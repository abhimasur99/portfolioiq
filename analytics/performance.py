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
- CAGR: (1 + total_return)^(1/n_years) - 1, where total_return = exp(sum(log_returns)) - 1.
- Sharpe: (Rp - Rf) / sigma_annualized, where sigma = std(log_returns) * sqrt(252).
- Sortino: (Rp - Rf) / downside_sigma, where downside_sigma uses only negative returns.
- Treynor: (Rp - Rf) / beta.
- Information ratio: (Rp - Rb) / tracking_error.
- Jensen's alpha: Rp - (Rf + beta * (Rb - Rf)).
- Beta: Cov(Rp, Rb) / Var(Rb) via OLS.
- R-squared: squared Pearson correlation between Rp and Rb.

Zero-denominator protection required on: Sharpe (zero vol), Sortino (zero downside vol),
Treynor (zero beta), Information ratio (zero tracking error), Calmar (zero max DD).

Dependencies: pandas, numpy, scipy.stats.
Assumptions:
- Risk-free rate is daily decimal (from data_fetcher.fetch_risk_free_rate()).
- Input returns are log returns (not multiplied by 100).

Implemented in: Session 3.
"""


def compute_all_performance(
    portfolio_returns: "pd.Series",
    benchmark_returns: "pd.Series",
    risk_free_rate: float,
) -> dict:
    """Compute all Layer 1 performance metrics.

    Args:
        portfolio_returns: pd.Series of daily portfolio log returns.
        benchmark_returns: pd.Series of daily benchmark log returns.
        risk_free_rate: Daily decimal risk-free rate (^IRX / 100 / 252).

    Returns:
        dict with keys: cagr, volatility, sharpe, sortino, treynor,
        information_ratio, alpha, beta, r_squared, rolling_sharpe,
        rolling_beta, rolling_12m_returns, best_month, worst_month,
        best_year, worst_year.
    """
    raise NotImplementedError("Implemented in Session 3.")
