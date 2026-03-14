"""tests/conftest.py

Shared pytest fixtures for PortfolioIQ test suite.

CRITICAL: No test in this suite makes real API calls. yfinance.download is
mocked via the mock_yfinance_download fixture wherever data fetching is tested.

Mock data construction (mock_prices):
- 800 trading business days starting 2021-01-04 (~3.2 years)
- 4 tickers: AAPL, MSFT, GOOGL, SPY
- Correlated log-normal price paths via Cholesky decomposition
- Correlation structure: AAPL-MSFT 0.75, tech-SPY ~0.55
- Days   0-199: normal period (~25% annualized vol for tech, ~18% for SPY)
- Days 200-299: stress period (2x normal volatility — tests GARCH clustering)
- Days 300-379: drawdown (~-18% cumulative drift — tests max drawdown, Calmar)
- Days 380-449: recovery (+drift)
- Days 450-799: return to normal
- Seed 42 for full reproducibility across all test runs
- All prices > 0 guaranteed by log-normal construction

Fixtures:
- mock_prices            — pd.DataFrame, adjusted close, 800 rows x 4 tickers
- mock_returns           — pd.DataFrame, log returns, 799 rows x 4 tickers
- mock_weights           — pd.Series, equal weights across AAPL/MSFT/GOOGL
- mock_portfolio_returns — pd.Series, weighted portfolio log returns, 799 rows
- mock_benchmark_returns — pd.Series, SPY log returns, 799 rows
- mock_risk_free_rate    — float, 0.05 / 252
- mock_yfinance_download — patches yfinance.download with MultiIndex DataFrame
- mock_irx_download      — patches yfinance.download with ^IRX single-ticker data
"""

import numpy as np
import pandas as pd
import pytest


# ── Price generation ───────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def mock_prices() -> pd.DataFrame:
    """800 trading days of synthetic adjusted close prices for 4 tickers.

    Constructed to satisfy all test requirements:
    - >756 days (GARCH minimum + buffer)
    - Stress period (volatility clustering for GARCH tests)
    - Drawdown >= -15% peak-to-trough (drawdown metric tests)
    - All prices strictly > 0

    Returns:
        pd.DataFrame with DatetimeIndex (business days from 2021-01-04),
        columns ["AAPL", "MSFT", "GOOGL", "SPY"]. All values > 0.
    """
    rng = np.random.default_rng(42)
    n = 800
    tickers = ["AAPL", "MSFT", "GOOGL", "SPY"]
    dates = pd.bdate_range(start="2021-01-04", periods=n)

    # Correlation and daily covariance via Cholesky
    corr = np.array([
        [1.00, 0.75, 0.60, 0.55],  # AAPL
        [0.75, 1.00, 0.65, 0.60],  # MSFT
        [0.60, 0.65, 1.00, 0.50],  # GOOGL
        [0.55, 0.60, 0.50, 1.00],  # SPY
    ])
    annual_vols = np.array([0.28, 0.26, 0.25, 0.18])
    daily_vols = annual_vols / np.sqrt(252)
    cov = np.outer(daily_vols, daily_vols) * corr
    L = np.linalg.cholesky(cov)

    # Base log returns
    z = rng.standard_normal((n, 4))
    log_returns = z @ L.T  # shape (n, 4)

    # Stress period: 2x volatility (days 200-299)
    z_stress = rng.standard_normal((100, 4))
    log_returns[200:300] = z_stress @ (L * 2.0).T

    # Drawdown: negative drift (days 300-379), ~-18% cumulative on portfolio
    log_returns[300:380] -= 0.0025

    # Recovery: positive drift (days 380-449)
    log_returns[380:450] += 0.0015

    # Build price paths via cumulative log returns (all prices stay > 0)
    # cum_log has shape (n+1, 4): row 0 = zeros (t=0 prior close),
    # rows 1..n = after each day's return. Slice [1:] to get n rows
    # aligned with the n trading dates.
    start_prices = np.array([130.0, 230.0, 2700.0, 370.0])
    cum_log = np.cumsum(log_returns, axis=0)          # shape (n, 4)
    prices = start_prices * np.exp(cum_log)            # shape (n, 4), all > 0

    return pd.DataFrame(prices, index=dates, columns=tickers)


# ── Return fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def mock_returns(mock_prices: pd.DataFrame) -> pd.DataFrame:
    """Log returns from mock_prices: rt = ln(Pt / Pt-1).

    Returns:
        pd.DataFrame, 799 rows x 4 columns. No NaN values.
    """
    return np.log(mock_prices / mock_prices.shift(1)).dropna()


@pytest.fixture(scope="session")
def mock_weights() -> pd.Series:
    """Equal-weight portfolio across AAPL, MSFT, GOOGL. SPY is the benchmark.

    Returns:
        pd.Series index=["AAPL","MSFT","GOOGL"], values=[1/3, 1/3, 1/3].
        Sums to 1.0 within floating-point tolerance.
    """
    tickers = ["AAPL", "MSFT", "GOOGL"]
    w = 1.0 / 3.0
    return pd.Series([w, w, w], index=tickers)


@pytest.fixture(scope="session")
def mock_portfolio_returns(
    mock_returns: pd.DataFrame,
    mock_weights: pd.Series,
) -> pd.Series:
    """Weighted portfolio log returns: returns_df[holdings] @ weights.

    Returns:
        pd.Series, 799 rows.
    """
    return mock_returns[mock_weights.index].dot(mock_weights)


@pytest.fixture(scope="session")
def mock_benchmark_returns(mock_returns: pd.DataFrame) -> pd.Series:
    """SPY log returns extracted from mock_returns.

    Returns:
        pd.Series, 799 rows.
    """
    return mock_returns["SPY"]


@pytest.fixture(scope="session")
def mock_risk_free_rate() -> float:
    """Fixed daily decimal risk-free rate: 5% annualized / 252.

    Returns:
        float ~= 0.0001984
    """
    return 0.05 / 252.0


# ── yfinance mocks ─────────────────────────────────────────────────────────────

@pytest.fixture
def mock_yfinance_download(mocker, mock_prices: pd.DataFrame):
    """Patch yfinance.download to return mock_prices as a real yfinance
    MultiIndex DataFrame.

    yfinance.download with multiple tickers returns a DataFrame with:
        columns level 0 = price type ("Adj Close", "Close", "Open", ...)
        columns level 1 = ticker symbol

    This fixture replicates that exact structure so data_fetcher.py's
    MultiIndex extraction logic is exercised against realistic mock data.

    Usage:
        def test_fetch(mock_yfinance_download, mock_prices):
            prices = _fetch_price_data_impl(["AAPL", "MSFT"], "3y")
            assert set(prices.columns) == {"AAPL", "MSFT"}

    Returns:
        MagicMock wrapping yfinance.download (supports call assertions).
    """
    price_types = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    tickers = mock_prices.columns.tolist()

    multi_cols = pd.MultiIndex.from_product(
        [price_types, tickers],
        names=["Price", "Ticker"],
    )
    multi_df = pd.DataFrame(
        index=mock_prices.index,
        columns=multi_cols,
        dtype=float,
    )

    for ticker in tickers:
        for pt in price_types:
            if pt in ("Adj Close", "Close"):
                multi_df[(pt, ticker)] = mock_prices[ticker].values
            elif pt == "Volume":
                multi_df[(pt, ticker)] = 1_000_000.0
            else:
                multi_df[(pt, ticker)] = mock_prices[ticker].values

    return mocker.patch("yfinance.download", return_value=multi_df)


@pytest.fixture
def mock_irx_download(mocker):
    """Patch yfinance.download to return a ^IRX single-ticker DataFrame.

    ^IRX in yfinance returns a plain (non-MultiIndex) DataFrame.
    Value set to 5.0 (5% annualized).
    Expected conversion: 5.0 / 100 / 252 = 0.0001984...

    Returns:
        MagicMock wrapping yfinance.download.
    """
    dates = pd.bdate_range(start="2026-03-10", periods=5)
    irx_df = pd.DataFrame(
        {
            "Close":     [5.0] * 5,
            "Adj Close": [5.0] * 5,
        },
        index=dates,
    )
    return mocker.patch("yfinance.download", return_value=irx_df)


@pytest.fixture
def mock_irx_download_with_nan(mocker):
    """Patch yfinance.download to return ^IRX data with leading NaN rows.

    Tests that fetch_risk_free_rate uses the last *valid* value, not the
    first row (which may be NaN when markets are closed or data is sparse).

    Returns:
        MagicMock wrapping yfinance.download.
    """
    dates = pd.bdate_range(start="2026-03-10", periods=5)
    irx_df = pd.DataFrame(
        {
            "Close":     [np.nan, np.nan, 4.5, 4.8, 5.0],
            "Adj Close": [np.nan, np.nan, 4.5, 4.8, 5.0],
        },
        index=dates,
    )
    return mocker.patch("yfinance.download", return_value=irx_df)
