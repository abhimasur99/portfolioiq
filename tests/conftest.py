"""tests/conftest.py

Shared pytest fixtures for PortfolioIQ test suite.

IMPORTANT: All tests must use these fixtures. No test makes real API calls.
yfinance.download is mocked to return a fixed, known price series.

Mock data requirements (per spec):
- At least 756 trading days (3 years) for reliability.
- Four tickers: AAPL, MSFT, GOOGL, SPY (benchmark).
- Periods of elevated volatility (simulate GARCH clustering).
- A distinct drawdown period (at least -15% peak-to-trough).
- Both high-correlation and low-correlation periods.
- All prices > 0 (no zero prices — protects log return computation).

Fixtures provided:
- mock_prices: pd.DataFrame — adjusted close prices, 756+ rows, 4 tickers.
- mock_returns: pd.DataFrame — log returns computed from mock_prices.
- mock_weights: pd.Series — equal weights (0.25 each for 3 holdings).
- mock_portfolio_returns: pd.Series — weighted portfolio log returns.
- mock_benchmark_returns: pd.Series — SPY log returns from mock_prices.
- mock_risk_free_rate: float — fixed daily decimal rate (0.05 / 252).

Implemented in: Session 2 (before any analytics code).
"""

import pytest
import numpy as np
import pandas as pd


@pytest.fixture(scope="session")
def mock_prices() -> pd.DataFrame:
    """Fixed known price series for 4 tickers over 756+ trading days.

    Returns:
        pd.DataFrame with DatetimeIndex, columns = ["AAPL", "MSFT", "GOOGL", "SPY"].
        Prices constructed to include: elevated vol period, drawdown, correlation shifts.
    """
    raise NotImplementedError("Implemented in Session 2.")


@pytest.fixture(scope="session")
def mock_returns(mock_prices) -> pd.DataFrame:
    """Log returns computed from mock_prices.

    Returns:
        pd.DataFrame of log returns, same columns as mock_prices, length 755+.
    """
    raise NotImplementedError("Implemented in Session 2.")


@pytest.fixture(scope="session")
def mock_weights() -> pd.Series:
    """Equal-weight portfolio across AAPL, MSFT, GOOGL (not SPY).

    Returns:
        pd.Series with index ["AAPL", "MSFT", "GOOGL"], values [1/3, 1/3, 1/3].
    """
    tickers = ["AAPL", "MSFT", "GOOGL"]
    return pd.Series([1 / 3] * 3, index=tickers)


@pytest.fixture(scope="session")
def mock_portfolio_returns(mock_returns, mock_weights) -> pd.Series:
    """Weighted portfolio log returns from mock_returns and mock_weights."""
    raise NotImplementedError("Implemented in Session 2.")


@pytest.fixture(scope="session")
def mock_benchmark_returns(mock_returns) -> pd.Series:
    """SPY log returns from mock_returns."""
    raise NotImplementedError("Implemented in Session 2.")


@pytest.fixture(scope="session")
def mock_risk_free_rate() -> float:
    """Fixed daily decimal risk-free rate: 5% annualized / 252."""
    return 0.05 / 252
