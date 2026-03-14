"""analytics/returns.py

Log return computation and portfolio aggregation.

Responsibilities:
- Compute log returns for each ticker: rt = ln(Pt / Pt-1).
- Aggregate to portfolio-level returns using user weights.
- Align portfolio and benchmark return series to a common date index.
- Weight normalization (weights must sum to 1 before aggregation).

Naming conventions (locked):
- returns_df: pd.DataFrame of per-ticker log returns.
- weights: pd.Series indexed by ticker.
- portfolio_returns: pd.Series of weighted portfolio log returns.
- benchmark_returns: pd.Series of benchmark log returns.

Mathematical spec:
- rt = ln(Pt / Pt-1) using numpy.log.
- portfolio_returns = returns_df.dot(weights).
- Log returns used throughout — never simple returns.
- Returns multiplied by 100 only when passed to GARCH fitting (in risk_outlook.py).

Dependencies: pandas, numpy.
Assumptions:
- Input price DataFrame has no NaN values (caller's responsibility to dropna first).
- Weights sum to 1.0 within floating-point tolerance.

Implemented in: Session 3.
"""


def compute_log_returns(prices: "pd.DataFrame") -> "pd.DataFrame":
    """Compute log returns from adjusted close price DataFrame.

    Args:
        prices: pd.DataFrame with dates as index, tickers as columns.
                Must have no NaN values.

    Returns:
        pd.DataFrame of log returns (first row dropped). Same column structure.

    Formula: rt = ln(Pt / Pt-1)
    """
    raise NotImplementedError("Implemented in Session 3.")


def compute_portfolio_returns(
    returns_df: "pd.DataFrame",
    weights: "pd.Series",
) -> "pd.Series":
    """Compute weighted portfolio log returns.

    Args:
        returns_df: pd.DataFrame of per-ticker log returns.
        weights: pd.Series indexed by ticker, summing to 1.0.

    Returns:
        pd.Series of portfolio log returns, same date index as returns_df.

    Raises:
        ValueError: If weights do not sum to 1 within 1e-6 tolerance.
    """
    raise NotImplementedError("Implemented in Session 3.")
