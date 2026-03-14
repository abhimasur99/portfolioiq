"""analytics/performance.py

Layer 1 — Descriptive analytics: performance metrics.

Responsibilities:
- CAGR, annualized volatility, Sharpe, Sortino, Treynor, Information ratio,
  Jensen's alpha, beta, R-squared.
- Rolling 252-day Sharpe and beta.
- Rolling 12-month returns.
- Best and worst calendar months and years.

All metrics use log returns and the risk-free rate from ^IRX.

Mathematical spec:
- CAGR: exp(mean(log_returns) * 252) - 1
  Derivation: (1 + total_return)^(1/n_years) - 1,
  where total_return = exp(sum(log_returns)) - 1 and n_years = n / 252.
- Annualized vol: std(log_returns) * sqrt(252).
- Sharpe: (mean(rp) - rf_daily) * sqrt(252) / std(rp).
- Sortino: (mean(rp) - rf_daily) * 252 / downside_sigma,
  where downside_sigma = std(rp[rp < 0]) * sqrt(252).
- Treynor: (mean(rp) - rf_daily) * 252 / beta.
- Information ratio: mean(active) * sqrt(252) / std(active),
  where active = portfolio_returns - benchmark_returns.
- Jensen's alpha: (mean(rp) - rf_daily)*252 - beta*(mean(rb) - rf_daily)*252.
- Beta: Cov(rp, rb) / Var(rb), both with ddof=1.
- R-squared: corr(rp, rb)^2.

Zero-denominator protection required on: Sharpe (zero vol), Sortino (zero downside vol),
Treynor (zero beta), Information ratio (zero tracking error), Calmar (zero max DD).

Dependencies: pandas, numpy, scipy.stats.
Assumptions:
- Risk-free rate is daily decimal (from data_fetcher.fetch_risk_free_rate()).
- Input returns are log returns (not multiplied by 100).
"""

import numpy as np
import pandas as pd


# ── Beta helper ───────────────────────────────────────────────────────────────

def _compute_beta(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Compute beta via Cov(Rp, Rb) / Var(Rb), ddof=1.

    Returns 0.0 if benchmark variance is effectively zero (degenerate case).
    Uses 1e-10 threshold — well below any real daily return variance (~1e-4).
    """
    var_b = float(benchmark_returns.var())
    if var_b < 1e-10:
        return 0.0
    cov = float(np.cov(portfolio_returns.values, benchmark_returns.values, ddof=1)[0, 1])
    return cov / var_b


# ── Individual metric functions ───────────────────────────────────────────────

def compute_cagr(portfolio_returns: pd.Series) -> float:
    """Compute Compound Annual Growth Rate.

    Formula: exp(mean(log_returns) * 252) - 1

    Args:
        portfolio_returns: pd.Series of daily portfolio log returns.

    Returns:
        float: annualized CAGR as a decimal (e.g. 0.12 = 12%).
    """
    return float(np.exp(portfolio_returns.mean() * 252) - 1.0)


def compute_sharpe(portfolio_returns: pd.Series, risk_free_rate: float) -> float:
    """Compute annualized Sharpe ratio.

    Formula: (mean(rp) - rf_daily) * sqrt(252) / std(rp)

    Returns 0.0 if annualized volatility is effectively zero.
    Uses 1e-10 threshold — well below any real daily return std (~0.01).
    """
    std = float(portfolio_returns.std())
    if std < 1e-10:
        return 0.0
    return float((portfolio_returns.mean() - risk_free_rate) * np.sqrt(252) / std)


def compute_sortino(portfolio_returns: pd.Series, risk_free_rate: float) -> float:
    """Compute annualized Sortino ratio.

    Downside sigma: std of negative returns only, annualized.
    Formula: (mean(rp) - rf_daily) * 252 / downside_sigma

    Returns 0.0 if there are no negative returns or downside sigma is zero.
    """
    negative = portfolio_returns[portfolio_returns < 0]
    if negative.empty:
        return 0.0
    downside_std = float(negative.std()) * np.sqrt(252)
    if downside_std == 0.0:
        return 0.0
    ann_excess = (portfolio_returns.mean() - risk_free_rate) * 252
    return float(ann_excess / downside_std)


def compute_treynor(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float,
) -> float:
    """Compute annualized Treynor ratio.

    Formula: (mean(rp) - rf_daily) * 252 / beta

    Returns 0.0 if beta is zero.
    """
    beta = _compute_beta(portfolio_returns, benchmark_returns)
    if beta == 0.0:
        return 0.0
    ann_excess = (portfolio_returns.mean() - risk_free_rate) * 252
    return float(ann_excess / beta)


def compute_info_ratio(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> float:
    """Compute Information ratio.

    Formula: mean(active) * sqrt(252) / std(active)
    where active = portfolio_returns - benchmark_returns.

    Returns 0.0 if tracking error is zero.
    """
    active = portfolio_returns - benchmark_returns
    tracking_error = float(active.std())
    if tracking_error == 0.0:
        return 0.0
    return float(active.mean() * np.sqrt(252) / tracking_error)


def compute_alpha_beta(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float,
) -> tuple[float, float, float]:
    """Compute Jensen's alpha, beta, and R-squared.

    Alpha formula: (mean(rp) - rf)*252 - beta*(mean(rb) - rf)*252
    Beta formula:  Cov(rp, rb) / Var(rb)
    R²  formula:   corr(rp, rb)^2

    Args:
        portfolio_returns: pd.Series of daily portfolio log returns.
        benchmark_returns: pd.Series of daily benchmark log returns.
        risk_free_rate: Daily decimal risk-free rate.

    Returns:
        Tuple of (alpha, beta, r_squared), all floats.
    """
    beta = _compute_beta(portfolio_returns, benchmark_returns)
    rp_ann = portfolio_returns.mean() * 252
    rb_ann = benchmark_returns.mean() * 252
    rf_ann = risk_free_rate * 252
    alpha = float(rp_ann - (rf_ann + beta * (rb_ann - rf_ann)))
    r_squared = float(portfolio_returns.corr(benchmark_returns) ** 2)
    return alpha, beta, r_squared


def compute_rolling_sharpe(
    portfolio_returns: pd.Series,
    risk_free_rate: float,
    window: int = 252,
) -> pd.Series:
    """Compute rolling annualized Sharpe ratio.

    Args:
        portfolio_returns: pd.Series of daily portfolio log returns.
        risk_free_rate: Daily decimal risk-free rate.
        window: Rolling window in trading days (default 252).

    Returns:
        pd.Series of rolling Sharpe values. First (window-1) values are NaN.
        NaN where rolling std is zero.
    """
    roll_mean = portfolio_returns.rolling(window).mean()
    roll_std = portfolio_returns.rolling(window).std()
    sharpe = (roll_mean - risk_free_rate) * np.sqrt(252) / roll_std
    return sharpe.where(roll_std > 0, other=np.nan)


def compute_rolling_beta(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    window: int = 252,
) -> pd.Series:
    """Compute rolling beta via rolling covariance / rolling variance.

    Args:
        portfolio_returns: pd.Series of daily portfolio log returns.
        benchmark_returns: pd.Series of daily benchmark log returns.
        window: Rolling window in trading days (default 252).

    Returns:
        pd.Series of rolling beta values. First (window-1) values are NaN.
        NaN where rolling benchmark variance is zero.
    """
    roll_cov = portfolio_returns.rolling(window).cov(benchmark_returns)
    roll_var = benchmark_returns.rolling(window).var()
    beta = roll_cov / roll_var
    return beta.where(roll_var > 0, other=np.nan)


def compute_best_worst_periods(portfolio_returns: pd.Series) -> dict:
    """Compute best and worst calendar months and years.

    Resamples log returns to month-end and year-end, converts to
    total return = exp(sum(log_returns)) - 1 for each period.

    Returns:
        dict with keys: best_month, worst_month, best_year, worst_year.
        All values are decimal returns (e.g. 0.05 = 5%).
    """
    def _total_return(log_r: pd.Series) -> float:
        return float(np.exp(log_r.sum()) - 1.0)

    monthly = portfolio_returns.resample("ME").apply(_total_return)
    yearly = portfolio_returns.resample("YE").apply(_total_return)

    return {
        "best_month": float(monthly.max()),
        "worst_month": float(monthly.min()),
        "best_year": float(yearly.max()),
        "worst_year": float(yearly.min()),
    }


# ── Master aggregator ─────────────────────────────────────────────────────────

def compute_all_performance(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float,
) -> dict:
    """Compute all Layer 1 performance metrics.

    Args:
        portfolio_returns: pd.Series of daily portfolio log returns.
        benchmark_returns: pd.Series of daily benchmark log returns.
        risk_free_rate: Daily decimal risk-free rate (^IRX / 100 / 252).

    Returns:
        dict with keys:
            cagr              — annualized CAGR (decimal)
            volatility        — annualized vol (decimal)
            sharpe            — annualized Sharpe ratio
            sortino           — annualized Sortino ratio
            treynor           — annualized Treynor ratio
            information_ratio — annualized Information ratio
            alpha             — Jensen's alpha (annualized, decimal)
            beta              — market beta
            r_squared         — R² vs benchmark
            rolling_sharpe    — pd.Series, 252-day rolling Sharpe
            rolling_beta      — pd.Series, 252-day rolling beta
            best_month        — best calendar month total return
            worst_month       — worst calendar month total return
            best_year         — best calendar year total return
            worst_year        — worst calendar year total return
    """
    alpha, beta, r_squared = compute_alpha_beta(
        portfolio_returns, benchmark_returns, risk_free_rate
    )
    periods = compute_best_worst_periods(portfolio_returns)

    return {
        "cagr": compute_cagr(portfolio_returns),
        "volatility": float(portfolio_returns.std() * np.sqrt(252)),
        "sharpe": compute_sharpe(portfolio_returns, risk_free_rate),
        "sortino": compute_sortino(portfolio_returns, risk_free_rate),
        "treynor": compute_treynor(portfolio_returns, benchmark_returns, risk_free_rate),
        "information_ratio": compute_info_ratio(portfolio_returns, benchmark_returns),
        "alpha": alpha,
        "beta": beta,
        "r_squared": r_squared,
        "rolling_sharpe": compute_rolling_sharpe(portfolio_returns, risk_free_rate),
        "rolling_beta": compute_rolling_beta(portfolio_returns, benchmark_returns),
        **periods,
    }
