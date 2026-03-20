"""analytics/risk_factors.py

Layer 2 — Diagnostic analytics: risk factor decomposition.

Responsibilities:
- Pearson correlation matrix (full period).
- Rolling 60-day correlation matrix.
- Covariance matrix with positive-definite check and 1e-6 diagonal regularization.
- Diversification ratio: weighted sum of individual vols / portfolio vol.
- HHI (Herfindahl-Hirschman Index): sum of squared weights.
- Effective N: 1 / HHI.
- Sector weights via yfinance GICS classification.
- Drawdown series, max drawdown, Calmar ratio, recovery time, Ulcer Index.

Mathematical spec:
- Pearson corr: Cov(i,j) / (sigma_i * sigma_j).
- HHI: sum(w_i^2).
- Effective N: 1 / HHI.
- Diversification ratio: (w^T * sigma_vec) / sigma_portfolio,
  where sigma_vec are individual annualized vols and sigma_portfolio
  = sqrt(w^T * AnnualizedCov * w).
- Drawdown at t: (V_t - max(V_0..V_t)) / max(V_0..V_t).
- Max drawdown: min of drawdown series.
- Calmar: CAGR / abs(max_drawdown). Protected against zero max_drawdown.
- Ulcer Index: sqrt(mean(DD_t^2)).
- Recovery time: trading days from trough to prior peak.

Covariance matrix condition check: numpy.linalg.cond > 1e10 triggers
diagonal regularization of +1e-6. Logged when regularization applied.

Dependencies: pandas, numpy, yfinance (sector weights only).
Assumptions:
- Input returns_df contains log returns (not multiplied by 100).
- Weights are a pd.Series indexed by ticker, summing to 1.

Naming conventions (locked):
- corr_matrix: pd.DataFrame — Pearson correlation matrix.
- cov_matrix: pd.DataFrame — covariance matrix (annualized).
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ── Correlation ───────────────────────────────────────────────────────────────

def compute_correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    """Compute full-period Pearson correlation matrix.

    Args:
        returns_df: pd.DataFrame of log returns, dates × tickers.

    Returns:
        pd.DataFrame: correlation matrix, tickers × tickers. Diagonal = 1.0.
    """
    return returns_df.corr()


def compute_rolling_correlation(
    returns_df: pd.DataFrame,
    window: int = 60,
) -> pd.DataFrame:
    """Compute rolling Pearson correlation matrix (60-day default).

    Uses pandas rolling().corr() which returns a MultiIndex DataFrame:
        index level 0 = date, index level 1 = ticker_i
        columns = ticker_j

    Args:
        returns_df: pd.DataFrame of log returns.
        window: Rolling window in trading days (default 60).

    Returns:
        pd.DataFrame with MultiIndex (date, ticker_i) and ticker columns.
        First (window-1) dates will have NaN correlation values.
    """
    return returns_df.rolling(window).corr()


# ── Covariance ────────────────────────────────────────────────────────────────

def compute_covariance_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    """Compute annualized covariance matrix with positive-definite regularization.

    Annualization: daily_cov * 252.
    Regularization: if condition number > 1e10, add 1e-6 to diagonal.

    Args:
        returns_df: pd.DataFrame of daily log returns.

    Returns:
        pd.DataFrame: annualized covariance matrix, tickers × tickers.
        Guaranteed positive-definite after regularization if needed.
    """
    daily_cov = returns_df.cov()
    cov_values = daily_cov.values * 252.0

    cond = np.linalg.cond(cov_values)
    if cond > 1e10:
        logger.warning(
            "Covariance matrix condition number %.2e > 1e10 — applying "
            "1e-6 diagonal regularization.",
            cond,
        )
        cov_values += np.eye(cov_values.shape[0]) * 1e-6

    return pd.DataFrame(cov_values, index=daily_cov.index, columns=daily_cov.columns)


# ── Concentration ─────────────────────────────────────────────────────────────

def compute_hhi(weights: pd.Series) -> float:
    """Compute Herfindahl-Hirschman Index: sum of squared weights.

    HHI = 1 for full concentration (single asset).
    HHI = 1/N for equal weights across N assets.

    Args:
        weights: pd.Series of portfolio weights summing to 1.

    Returns:
        float: HHI in (0, 1].
    """
    return float((weights ** 2).sum())


def compute_effective_n(weights: pd.Series) -> float:
    """Compute Effective N (diversification count): 1 / HHI.

    Effective N = N for equal-weight portfolio.
    Effective N = 1 for single-asset portfolio.

    Args:
        weights: pd.Series of portfolio weights summing to 1.

    Returns:
        float: Effective N >= 1.
    """
    hhi = compute_hhi(weights)
    if hhi < 1e-10:
        return float("inf")
    return float(1.0 / hhi)


def compute_diversification_ratio(
    returns_df: pd.DataFrame,
    weights: pd.Series,
) -> float:
    """Compute portfolio diversification ratio.

    DR = (w^T * sigma_vec) / sigma_portfolio
    where sigma_vec are annualized individual vols and
    sigma_portfolio = sqrt(w^T * AnnualizedCov * w).

    DR = 1.0 for a single-asset portfolio.
    DR > 1.0 indicates diversification benefit.

    Args:
        returns_df: pd.DataFrame of log returns (can contain more tickers than weights).
        weights: pd.Series indexed by ticker.

    Returns:
        float: diversification ratio >= 1.0 for long-only portfolios.
        Returns 0.0 if portfolio volatility is effectively zero.
    """
    tickers = weights.index.tolist()
    sub_returns = returns_df[tickers]

    ann_cov = sub_returns.cov() * 252.0
    individual_vols = np.sqrt(np.diag(ann_cov.values))   # annualized vol vector
    w = weights.values

    weighted_avg_vol = float(w @ individual_vols)
    portfolio_var = float(w @ ann_cov.values @ w)
    portfolio_vol = float(np.sqrt(max(portfolio_var, 0.0)))

    if portfolio_vol < 1e-10:
        return 0.0
    return float(weighted_avg_vol / portfolio_vol)


# ── Drawdown ──────────────────────────────────────────────────────────────────

def compute_drawdown_series(portfolio_returns: pd.Series) -> pd.Series:
    """Compute drawdown series from portfolio log returns.

    Builds a price index (exp of cumulative log returns), then computes
    (price - running_max) / running_max at each point.

    All values are <= 0 by construction.

    Args:
        portfolio_returns: pd.Series of daily portfolio log returns.

    Returns:
        pd.Series of drawdown values (same index), all <= 0.
    """
    price_index = np.exp(portfolio_returns.cumsum())
    running_max = price_index.cummax()
    return (price_index - running_max) / running_max


def compute_max_drawdown(drawdown_series: pd.Series) -> float:
    """Compute maximum drawdown (most negative drawdown value).

    Args:
        drawdown_series: pd.Series of drawdown values, all <= 0.

    Returns:
        float: max drawdown, a negative value (or 0.0 if no drawdown).
    """
    return float(drawdown_series.min())


def compute_calmar(
    portfolio_returns: pd.Series,
    max_drawdown: float,
) -> float:
    """Compute annualized Calmar ratio: CAGR / abs(max_drawdown).

    Args:
        portfolio_returns: pd.Series of daily portfolio log returns.
        max_drawdown: float, typically negative. Uses abs() internally.

    Returns:
        float: Calmar ratio. Returns 0.0 if max_drawdown is effectively zero.
    """
    if abs(max_drawdown) < 1e-10:
        return 0.0
    cagr = float(np.exp(portfolio_returns.mean() * 252) - 1.0)
    return float(cagr / abs(max_drawdown))


def compute_recovery_time(drawdown_series: pd.Series) -> int | None:
    """Compute recovery time in trading days from trough to prior peak.

    Args:
        drawdown_series: pd.Series of drawdown values (all <= 0).

    Returns:
        int: trading days from trough to recovery (drawdown reaching 0).
        None: if the portfolio has not yet recovered by end of series.
        0: if there was no drawdown (trough = 0).
    """
    if drawdown_series.min() >= 0.0:
        return 0  # no drawdown ever

    trough_pos = int(drawdown_series.values.argmin())
    post_trough = drawdown_series.iloc[trough_pos:]
    recovered = np.where(post_trough.values >= 0.0)[0]

    if len(recovered) == 0:
        return None  # not yet recovered
    return int(recovered[0])  # trading days from trough to recovery


def compute_ulcer_index(drawdown_series: pd.Series) -> float:
    """Compute Ulcer Index: sqrt(mean(DD_t^2)).

    Measures the depth and duration of drawdowns. Returns 0.0 for
    a series with no drawdown.

    Args:
        drawdown_series: pd.Series of drawdown values (all <= 0).

    Returns:
        float: Ulcer Index >= 0.
    """
    return float(np.sqrt(np.mean(drawdown_series.values ** 2)))


# ── Sector weights ────────────────────────────────────────────────────────────

def fetch_sector_weights(weights: pd.Series) -> dict:
    """Fetch GICS sector classification and compute sector-level weight aggregates.

    Uses yfinance Ticker.info["sector"] for each holding. Best-effort:
    tickers where sector is unavailable are grouped under "Unknown".

    NOT cached — called once per session as part of the risk factor pipeline.

    Args:
        weights: pd.Series of portfolio weights indexed by ticker.

    Returns:
        dict mapping sector name (str) → aggregate weight (float).
        Returns {} if all sector fetches fail.
    """
    try:
        import yfinance as yf
    except ImportError:
        logger.warning("yfinance not available — sector weights skipped.")
        return {}

    import requests
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    })

    _ETF_QUOTE_TYPES = {"etf", "mutualfund"}

    sector_weights: dict[str, float] = {}
    for ticker, weight in weights.items():
        try:
            info = yf.Ticker(ticker, session=session).info
            sector = info.get("sector") or ""
            if not sector:
                quote_type = (info.get("quoteType") or "").lower()
                sector = "ETF / Fund" if quote_type in _ETF_QUOTE_TYPES else "Unknown"
        except Exception as exc:
            logger.warning("Sector fetch failed for %s: %s", ticker, exc)
            sector = "Unknown"
        sector_weights[sector] = sector_weights.get(sector, 0.0) + float(weight)

    if set(sector_weights.keys()) == {"Unknown"}:
        return {}

    return sector_weights


# ── Master aggregator ─────────────────────────────────────────────────────────

def compute_all_risk_factors(
    returns_df: pd.DataFrame,
    weights: pd.Series,
    portfolio_returns: pd.Series,
) -> dict:
    """Compute all Layer 2 diagnostic risk factor metrics.

    Args:
        returns_df: pd.DataFrame of per-ticker log returns (all holdings + benchmark).
        weights: pd.Series indexed by ticker (holdings only), summing to 1.
        portfolio_returns: pd.Series of weighted portfolio log returns.

    Returns:
        dict with keys:
            corr_matrix        — pd.DataFrame, Pearson correlation (tickers × tickers)
            rolling_corr       — pd.DataFrame, MultiIndex rolling 60-day correlation
            cov_matrix         — pd.DataFrame, annualized covariance matrix
            hhi                — float, Herfindahl-Hirschman Index
            effective_n        — float, Effective N = 1/HHI
            diversification_ratio — float, weighted avg vol / portfolio vol
            sector_weights     — dict, sector → aggregate weight
            drawdown_series    — pd.Series, drawdown at each point (all <= 0)
            max_drawdown       — float, most negative drawdown value
            calmar             — float, CAGR / abs(max_drawdown)
            recovery_days      — int or None, trading days trough → recovery
            ulcer_index        — float, sqrt(mean(DD^2))
    """
    # Subset returns to holdings only for concentration/correlation metrics
    holding_returns = returns_df[weights.index]

    drawdown_series = compute_drawdown_series(portfolio_returns)
    max_dd = compute_max_drawdown(drawdown_series)

    return {
        "corr_matrix": compute_correlation_matrix(holding_returns),
        "rolling_corr": compute_rolling_correlation(holding_returns, window=60),
        "cov_matrix": compute_covariance_matrix(holding_returns),
        "hhi": compute_hhi(weights),
        "effective_n": compute_effective_n(weights),
        "diversification_ratio": compute_diversification_ratio(returns_df, weights),
        "sector_weights": fetch_sector_weights(weights),
        "drawdown_series": drawdown_series,
        "max_drawdown": max_dd,
        "calmar": compute_calmar(portfolio_returns, max_dd),
        "recovery_days": compute_recovery_time(drawdown_series),
        "ulcer_index": compute_ulcer_index(drawdown_series),
    }
