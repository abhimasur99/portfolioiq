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
- Diversification ratio: (w^T * sigma_vec) / sigma_portfolio.
- Drawdown at t: (V_t - max(V_0..V_t)) / max(V_0..V_t).
- Max drawdown: min of drawdown series.
- Calmar: CAGR / abs(max_drawdown). Protected against zero max_drawdown.
- Ulcer Index: sqrt(mean(DD_t^2)).
- Recovery time: trading days from trough to prior peak.

Covariance matrix condition check: numpy.linalg.cond > 1e10 triggers
diagonal regularization of +1e-6. Logged when regularization applied.

Dependencies: pandas, numpy.
Assumptions:
- Input returns_df contains log returns (not multiplied by 100).
- Weights are a pd.Series indexed by ticker, summing to 1.

Naming conventions (locked):
- corr_matrix: pd.DataFrame — Pearson correlation matrix.
- cov_matrix: pd.DataFrame — covariance matrix.

Implemented in: Session 4.
"""


def compute_all_risk_factors(
    returns_df: "pd.DataFrame",
    weights: "pd.Series",
    portfolio_returns: "pd.Series",
) -> dict:
    """Compute all Layer 2 diagnostic risk factor metrics.

    Args:
        returns_df: pd.DataFrame of per-ticker log returns.
        weights: pd.Series indexed by ticker, summing to 1.
        portfolio_returns: pd.Series of weighted portfolio log returns.

    Returns:
        dict with keys: corr_matrix, rolling_corr, cov_matrix,
        diversification_ratio, hhi, effective_n, sector_weights,
        drawdown_series, max_drawdown, calmar, recovery_days, ulcer_index.
    """
    raise NotImplementedError("Implemented in Session 4.")
