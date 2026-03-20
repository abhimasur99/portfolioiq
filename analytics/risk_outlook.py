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


def _compute_ewma_series_pct(
    portfolio_returns: pd.Series,
    lambda_: float = 0.94,
) -> "np.ndarray":
    """Compute rolling EWMA conditional volatility as a series in percentage units.

    Matches the format of arch's .conditional_volatility (pct units) so the
    result can be plotted alongside the GARCH trace in garch_volatility_chart().
    Used as a fallback when GARCH cannot be fitted (< 252 obs).

    Args:
        portfolio_returns: pd.Series of daily log returns.
        lambda_: EWMA decay factor (default 0.94, RiskMetrics standard).

    Returns:
        np.ndarray of EWMA daily conditional vol in percentage units (same
        length as portfolio_returns).
    """
    r = portfolio_returns.values * 100.0   # pct units, matches arch convention
    var = float(np.var(r, ddof=1))
    out = []
    for ret in r:
        var = lambda_ * var + (1.0 - lambda_) * ret ** 2
        out.append(np.sqrt(var))
    return np.array(out)


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


# ── Monte Carlo ───────────────────────────────────────────────────────────────

def _run_garch_monte_carlo(
    portfolio_returns: pd.Series,
    garch_result,
    garch_vol_daily: float,
    n_paths: int,
    n_steps: int,
) -> dict:
    """Vectorized GARCH-MC portfolio simulation.

    Pre-generates all (n_steps, n_paths) innovations in one numpy call —
    no Python loops over paths. Only a sequential loop over steps is used
    (required because each step's variance depends on the prior step's variance).

    GARCH variance recursion (decimal units):
        sigma²_t = omega_dec + alpha * r²_{t-1} + beta * sigma²_{t-1}

    When garch_result is None (EWMA fallback), uses:
        omega=0, alpha=0.06 (1-lambda), beta=0.94 (lambda)

    Args:
        portfolio_returns: pd.Series of daily log returns (used for drift mu).
        garch_result: arch ResultsWrapper or None (EWMA fallback).
        garch_vol_daily: float, daily decimal conditional vol from fit_garch.
        n_paths: int, number of simulation paths.
        n_steps: int, number of trading days to simulate.

    Returns:
        dict with keys:
            values — np.ndarray of shape (n_steps+1, n_paths), portfolio values.
                     Row 0 = 1.0 (normalized initial value).
            p10, p50, p90 — np.ndarray of shape (n_steps+1,), percentile fans.
    """
    # Extract GARCH parameters in decimal units
    if garch_result is not None:
        omega_dec = float(garch_result.params["omega"]) / 1e4  # pct² → decimal²
        alpha_param = float(garch_result.params["alpha[1]"])
        beta_param = float(garch_result.params["beta[1]"])
    else:
        # EWMA: sigma²_t = 0.94*sigma²_{t-1} + 0.06*r²_{t-1}
        omega_dec = 0.0
        alpha_param = 0.06
        beta_param = 0.94

    mu = float(portfolio_returns.mean())      # daily drift
    sigma2_init = garch_vol_daily ** 2        # initial daily variance

    # Pre-generate all innovations at once: shape (n_steps, n_paths)
    rng = np.random.default_rng(42)
    Z = rng.standard_normal((n_steps, n_paths))

    # Initialize state
    sigma2 = np.full(n_paths, sigma2_init)    # current variance per path
    values = np.ones((n_steps + 1, n_paths))  # portfolio values, start at 1.0

    # Sequential step loop (vectorized over paths at each step)
    for t in range(n_steps):
        sigma = np.sqrt(np.maximum(sigma2, 0.0))
        r_t = mu + sigma * Z[t]                         # shape (n_paths,)
        values[t + 1] = values[t] * np.exp(r_t)
        sigma2 = omega_dec + alpha_param * r_t ** 2 + beta_param * sigma2

    p10 = np.percentile(values, 10, axis=1)
    p50 = np.percentile(values, 50, axis=1)
    p90 = np.percentile(values, 90, axis=1)

    return {"values": values, "p10": p10, "p50": p50, "p90": p90}


# ── Stress tests ──────────────────────────────────────────────────────────────

def _run_stress_tests(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    performance: dict,
) -> dict:
    """Apply historical stress scenarios to estimate portfolio impact.

    Formula: portfolio_return = alpha + beta * scenario_index_return
    Uses Jensen's alpha (annualized) and beta from the performance dict.

    Args:
        portfolio_returns: pd.Series (unused directly; reserved for future use).
        benchmark_returns: pd.Series (unused directly; reserved for future use).
        performance: dict from compute_all_performance(), must include 'alpha' and 'beta'.

    Returns:
        dict keyed by scenario name, each value is a dict with:
            index_return     — float, the market scenario return (e.g. -0.37)
            portfolio_return — float, estimated portfolio return in the scenario
            description      — str, scenario description from config
    """
    from assets.config import STRESS_SCENARIOS

    beta = float(performance["beta"])
    alpha = float(performance["alpha"])  # Jensen's alpha (annualized decimal)

    results = {}
    for scenario_name, scenario_data in STRESS_SCENARIOS.items():
        index_return = float(scenario_data["index_return"])
        portfolio_return = alpha + beta * index_return
        results[scenario_name] = {
            "index_return": index_return,
            "portfolio_return": float(portfolio_return),
            "description": scenario_data["description"],
        }
    return results


# ── Master aggregator ─────────────────────────────────────────────────────────

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
        dict with keys:
            hist_vol          — float, annualized historical volatility
            ewma_vol          — float, annualized EWMA volatility (lambda=0.94)
            garch_vol         — float, annualized GARCH conditional volatility
            garch_model       — arch ResultsWrapper or None (EWMA fallback)
            var_95_hist       — float, 95% historical VaR (negative = loss)
            cvar_95_hist      — float, 95% historical CVaR
            var_99_hist       — float, 99% historical VaR
            cvar_99_hist      — float, 99% historical CVaR
            var_95_garch      — float, GARCH-conditional 95% VaR (normal)
            var_monthly       — float, 95% historical VaR scaled to 21 days
            mc_paths_matrix   — np.ndarray (n_steps+1, n_paths) portfolio values
            mc_p10            — np.ndarray (n_steps+1,) 10th percentile fan
            mc_p50            — np.ndarray (n_steps+1,) median fan
            mc_p90            — np.ndarray (n_steps+1,) 90th percentile fan
            stress_results    — dict, scenario name → impact dict
            skewness          — float
            excess_kurtosis   — float
            garch_fallback    — bool, True if EWMA was used instead of GARCH
    """
    var_conf = float(settings.get("var_confidence", 0.95))
    mc_horizon = int(settings.get("mc_horizon", 10))
    mc_paths = int(settings.get("mc_paths", 1_000))
    mc_steps = mc_horizon * 252

    hist_vol = compute_historical_vol(portfolio_returns)
    ewma_vol = compute_ewma_vol(portfolio_returns)
    garch_result, garch_vol_daily, is_fallback = fit_garch(portfolio_returns)
    garch_vol = garch_vol_daily * np.sqrt(252)

    # EWMA series for the GARCH chart — only computed when GARCH falls back due to
    # insufficient data (result is None). Used as a purple fallback trace on 1Y window.
    ewma_series = (
        _compute_ewma_series_pct(portfolio_returns)
        if is_fallback and garch_result is None
        else None
    )

    var_95_hist, cvar_95_hist = compute_var_cvar_historical(portfolio_returns, 0.95)
    var_99_hist, cvar_99_hist = compute_var_cvar_historical(portfolio_returns, 0.99)
    var_95_garch = compute_garch_var(portfolio_returns, garch_vol_daily, 0.95)
    var_monthly = compute_var_monthly(var_95_hist)

    mc_results = _run_garch_monte_carlo(
        portfolio_returns, garch_result, garch_vol_daily, mc_paths, mc_steps
    )
    stress_results = _run_stress_tests(portfolio_returns, benchmark_returns, performance)
    skewness, excess_kurtosis = compute_skewness_kurtosis(portfolio_returns)

    return {
        "hist_vol": hist_vol,
        "ewma_vol": ewma_vol,
        "garch_vol": garch_vol,
        "garch_model": garch_result,
        "var_95_hist": var_95_hist,
        "cvar_95_hist": cvar_95_hist,
        "var_99_hist": var_99_hist,
        "cvar_99_hist": cvar_99_hist,
        "var_95_garch": var_95_garch,
        "var_monthly": var_monthly,
        "mc_paths_matrix": mc_results["values"],
        "mc_p10": mc_results["p10"],
        "mc_p50": mc_results["p50"],
        "mc_p90": mc_results["p90"],
        "stress_results": stress_results,
        "skewness": skewness,
        "excess_kurtosis": excess_kurtosis,
        "garch_fallback": is_fallback,
        "ewma_series":    ewma_series,
    }
