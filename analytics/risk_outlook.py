"""analytics/risk_outlook.py

Layer 3 — Predictive analytics: risk outlook and forward characterization.

Responsibilities:
- Historical volatility: std(log_returns) * sqrt(252).
- EWMA volatility: sigma^2_t = lambda * sigma^2_{t-1} + (1-lambda) * r^2_{t-1}. Lambda=0.94.
- GARCH(1,1) via arch library:
    - Fitted on percentage log returns (multiply by 100 before fit).
    - disp=False to suppress optimization output.
    - Stationarity check: alpha + beta < 1. EWMA fallback if violated.
    - Minimum 252 observations required; EWMA fallback if shorter.
    - Output sigma divided by 100 when converting back to decimal.
- Historical VaR at 95% and 99%: percentile of realized returns.
- Historical CVaR at 95% and 99%: mean of returns below VaR threshold.
- GARCH-conditional VaR: mu + z * sigma_garch_daily (normal distribution).
- VaR scaling to monthly: daily_VaR * sqrt(21). Assumes i.i.d.
- Monte Carlo (GARCH-MC): Session 6.
- Stress tests: Session 6.
- Skewness and excess kurtosis of portfolio returns.

VaR sign convention: all VaR and CVaR values are expressed as log returns
(negative numbers represent losses). For example, VaR(95%) = 5th percentile
of the return distribution ≈ -0.015 means a 1.5% daily loss at 95% confidence.

Dependencies: pandas, numpy, scipy.stats, arch.
Assumptions:
- Input portfolio_returns are log returns (not multiplied by 100).
- GARCH is fitted on returns * 100; output sigma divided by 100 for use.
- Monte Carlo initializes from GARCH one-step-ahead conditional volatility.
"""

import logging

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


# ── Historical volatility ─────────────────────────────────────────────────────

def compute_historical_vol(portfolio_returns: pd.Series) -> float:
    """Compute annualized historical volatility.

    Args:
        portfolio_returns: pd.Series of daily portfolio log returns.

    Returns:
        float: annualized volatility = std(returns) * sqrt(252).
    """
    return float(portfolio_returns.std() * np.sqrt(252))


# ── EWMA volatility ───────────────────────────────────────────────────────────

def compute_ewma_vol(portfolio_returns: pd.Series, lambda_: float = 0.94) -> float:
    """Compute current EWMA (RiskMetrics) annualized volatility estimate.

    Formula: sigma^2_t = lambda * sigma^2_{t-1} + (1 - lambda) * r^2_{t-1}
    Iterates through all observations; returns annualized sigma after the
    last observation (one-step-ahead conditional volatility estimate).

    Args:
        portfolio_returns: pd.Series of daily portfolio log returns.
        lambda_: Decay factor (default 0.94, RiskMetrics standard).

    Returns:
        float: annualized EWMA volatility.
    """
    r = portfolio_returns.values
    # Initialize with full-period variance for numerical stability
    var = float(np.var(r, ddof=1))
    for ret in r:
        var = lambda_ * var + (1.0 - lambda_) * ret ** 2
    return float(np.sqrt(var) * np.sqrt(252))


# ── GARCH(1,1) ────────────────────────────────────────────────────────────────

def fit_garch(
    portfolio_returns: pd.Series,
    min_obs: int = 252,
) -> tuple:
    """Fit GARCH(1,1) model on portfolio log returns.

    Fits on percentage returns (returns * 100) per arch convention.
    Enforces stationarity: alpha + beta < 1. Falls back to EWMA if:
      - Fewer than min_obs observations
      - Optimization fails
      - Fitted alpha + beta >= 1 (non-stationary)

    Args:
        portfolio_returns: pd.Series of daily log returns.
        min_obs: Minimum observations required to attempt GARCH fit (default 252).

    Returns:
        Tuple of (result, garch_vol_daily, is_fallback):
            result          — arch ResultsWrapper, or None if fallback triggered.
            garch_vol_daily — float, daily decimal conditional vol (annualize with *sqrt(252)).
            is_fallback     — bool, True if EWMA was used instead of GARCH.
    """
    if len(portfolio_returns) < min_obs:
        logger.warning(
            "GARCH requires >= %d observations (got %d) — using EWMA fallback.",
            min_obs,
            len(portfolio_returns),
        )
        ewma_daily = compute_ewma_vol(portfolio_returns) / np.sqrt(252)
        return None, float(ewma_daily), True

    pct_returns = portfolio_returns * 100.0

    try:
        from arch import arch_model
        model = arch_model(pct_returns, vol="Garch", p=1, q=1, dist="normal")
        result = model.fit(disp=False)

        alpha = float(result.params["alpha[1]"])
        beta = float(result.params["beta[1]"])

        if alpha + beta >= 1.0:
            logger.warning(
                "GARCH(1,1) non-stationary (alpha+beta=%.4f >= 1) — using EWMA fallback.",
                alpha + beta,
            )
            ewma_daily = compute_ewma_vol(portfolio_returns) / np.sqrt(252)
            return result, float(ewma_daily), True

        # Last conditional volatility in percentage units → convert to daily decimal
        garch_vol_pct = float(result.conditional_volatility.iloc[-1])
        garch_vol_daily = garch_vol_pct / 100.0

        logger.info(
            "GARCH(1,1) fit: omega=%.6f alpha=%.4f beta=%.4f (sum=%.4f) "
            "daily_vol=%.4f%%",
            float(result.params["omega"]),
            alpha,
            beta,
            alpha + beta,
            garch_vol_pct,
        )
        return result, garch_vol_daily, False

    except Exception as exc:
        logger.warning("GARCH fit failed (%s) — using EWMA fallback.", exc)
        ewma_daily = compute_ewma_vol(portfolio_returns) / np.sqrt(252)
        return None, float(ewma_daily), True


# ── VaR and CVaR ─────────────────────────────────────────────────────────────

def compute_var_cvar_historical(
    portfolio_returns: pd.Series,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Compute historical VaR and CVaR at the given confidence level.

    VaR is expressed as a log return (negative = loss).
    CVaR is the expected return given the return falls below VaR.

    Args:
        portfolio_returns: pd.Series of daily log returns.
        confidence: Confidence level (default 0.95 → 5th percentile).

    Returns:
        Tuple of (var, cvar):
            var  — float, the (1-confidence) percentile of returns (negative).
            cvar — float, mean of returns <= var (more negative than var).
    """
    tail_pct = (1.0 - confidence) * 100.0  # e.g., 5.0 for 95% confidence
    var = float(np.percentile(portfolio_returns.values, tail_pct))
    tail = portfolio_returns[portfolio_returns <= var]
    cvar = float(tail.mean()) if not tail.empty else var
    return var, cvar


def compute_garch_var(
    portfolio_returns: pd.Series,
    garch_vol_daily: float,
    confidence: float = 0.95,
) -> float:
    """Compute GARCH-conditional VaR assuming normally distributed innovations.

    Formula: VaR = mu + z * sigma_garch_daily
    where z = norm.ppf(1 - confidence) < 0 for confidence > 0.5.

    Args:
        portfolio_returns: pd.Series of daily log returns (used for mu estimate).
        garch_vol_daily: float, daily decimal conditional volatility from fit_garch.
        confidence: Confidence level (default 0.95).

    Returns:
        float: GARCH-conditional VaR as a log return (negative = loss).
    """
    mu = float(portfolio_returns.mean())
    z = float(stats.norm.ppf(1.0 - confidence))  # e.g., -1.6449 for 95%
    return float(mu + z * garch_vol_daily)


def compute_var_monthly(var_daily: float) -> float:
    """Scale daily VaR to monthly using square-root-of-time rule.

    Assumes i.i.d. returns. Monthly = 21 trading days.
    Since var_daily < 0 (loss), var_monthly will be more negative.

    Args:
        var_daily: float, daily VaR (negative number).

    Returns:
        float: monthly VaR = var_daily * sqrt(21).
    """
    return float(var_daily * np.sqrt(21))


# ── Moments ───────────────────────────────────────────────────────────────────

def compute_skewness_kurtosis(portfolio_returns: pd.Series) -> tuple[float, float]:
    """Compute skewness and excess kurtosis of portfolio returns.

    Args:
        portfolio_returns: pd.Series of daily log returns.

    Returns:
        Tuple of (skewness, excess_kurtosis):
            skewness        — float, third standardized moment. 0 for normal.
            excess_kurtosis — float, fourth standardized moment minus 3 (Fisher).
                              0 for normal, >0 for fat tails.
    """
    skewness = float(stats.skew(portfolio_returns.values))
    excess_kurtosis = float(stats.kurtosis(portfolio_returns.values, fisher=True))
    return skewness, excess_kurtosis


# ── Monte Carlo (Session 6) ───────────────────────────────────────────────────

def _run_garch_monte_carlo(
    portfolio_returns: pd.Series,
    garch_result,
    garch_vol_daily: float,
    n_paths: int,
    n_steps: int,
) -> dict:
    """GARCH-MC simulation. Implemented in Session 6."""
    raise NotImplementedError("Implemented in Session 6.")


# ── Stress tests (Session 6) ──────────────────────────────────────────────────

def _run_stress_tests(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    performance: dict,
) -> dict:
    """Scenario stress test results. Implemented in Session 6."""
    raise NotImplementedError("Implemented in Session 6.")


# ── Master aggregator (completed in Session 6) ────────────────────────────────

def compute_all_risk_outlook(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    weights: pd.Series,
    performance: dict,
    settings: dict,
) -> dict:
    """Compute all Layer 3 risk outlook metrics.

    Args:
        portfolio_returns: pd.Series of daily portfolio log returns.
        benchmark_returns: pd.Series of daily benchmark log returns.
        weights: pd.Series indexed by ticker.
        performance: dict output from performance.compute_all_performance().
        settings: dict with keys: var_confidence, mc_horizon, mc_paths.

    Returns:
        dict with keys: hist_vol, ewma_vol, garch_vol, garch_model,
        var_95_hist, cvar_95_hist, var_99_hist, cvar_99_hist,
        var_95_garch, var_monthly,
        mc_paths_matrix, mc_p10, mc_p50, mc_p90,
        stress_results, skewness, excess_kurtosis,
        garch_fallback (bool, True if EWMA used instead of GARCH).

    Raises:
        NotImplementedError: Until Session 6 (MC and stress tests pending).
    """
    raise NotImplementedError("Completed in Session 6 (MC and stress tests pending).")
