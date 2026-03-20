"""tests/test_data_fetcher.py

Unit tests for analytics/data_fetcher.py.

Tests call the private _impl functions directly to avoid Streamlit cache
context issues. yfinance.download is mocked via fixtures in conftest.py.

Test coverage:
- MultiIndex column extraction (real yfinance output format)
- NaN row dropping
- Invalid ticker detection and ValueError
- Single-ticker flat column handling
- ^IRX conversion: annualized % / 100 / 252
- ^IRX NaN handling: last valid value used
- ^IRX fetch failure: fallback rate returned
- validate_tickers: separates valid from invalid
- _download_with_backoff: ValueError on empty result (not retried)
"""

import numpy as np
import pandas as pd
import pytest

from analytics.data_fetcher import (
    _extract_adj_close,
    _fetch_price_data_impl,
    _fetch_risk_free_rate_impl,
    _FALLBACK_DAILY_RATE,
    validate_tickers,
)


# ── _extract_adj_close ────────────────────────────────────────────────────────

class TestExtractAdjClose:
    def test_multiindex_extracts_adj_close(self, mock_yfinance_download, mock_prices):
        """MultiIndex DataFrame: Adj Close extracted correctly for all tickers."""
        import yfinance as yf
        raw = yf.download("AAPL MSFT GOOGL SPY", period="3y")
        tickers = ["AAPL", "MSFT", "GOOGL", "SPY"]

        prices = _extract_adj_close(raw, tickers)

        assert list(prices.columns) == tickers
        assert not prices.isnull().any().any()
        assert len(prices) > 0

    def test_multiindex_values_match_mock(self, mock_yfinance_download, mock_prices):
        """Extracted prices match the mock source data exactly."""
        import yfinance as yf
        raw = yf.download("AAPL MSFT GOOGL SPY", period="3y")
        prices = _extract_adj_close(raw, ["AAPL", "MSFT", "GOOGL", "SPY"])

        pd.testing.assert_frame_equal(
            prices.reset_index(drop=True),
            mock_prices.reset_index(drop=True),
            check_names=False,
        )

    def test_column_order_matches_input(self, mock_yfinance_download, mock_prices):
        """Output columns are ordered to match the input tickers list."""
        import yfinance as yf
        raw = yf.download("AAPL MSFT GOOGL SPY", period="3y")
        ordered = ["SPY", "AAPL", "GOOGL", "MSFT"]
        prices = _extract_adj_close(raw, ordered)
        assert list(prices.columns) == ordered

    def test_nan_rows_dropped(self, mocker, mock_prices):
        """Rows with any NaN in Adj Close are dropped from output."""
        # Build a MultiIndex df with a NaN row injected
        tickers = ["AAPL", "MSFT"]
        price_types = ["Adj Close", "Close"]
        cols = pd.MultiIndex.from_product([price_types, tickers])
        raw = pd.DataFrame(index=mock_prices.index[:10], columns=cols, dtype=float)
        for t in tickers:
            raw[("Adj Close", t)] = mock_prices[t].iloc[:10].values
            raw[("Close", t)] = mock_prices[t].iloc[:10].values

        # Inject NaN at row 3
        raw.loc[raw.index[3], ("Adj Close", "AAPL")] = np.nan

        prices = _extract_adj_close(raw, tickers)
        assert not prices.isnull().any().any()
        assert len(prices) == 9  # 10 rows minus the NaN row

    def test_invalid_ticker_raises_value_error(self, mocker, mock_prices):
        """Ticker with all-NaN Adj Close raises ValueError with ticker name."""
        tickers = ["AAPL", "FAKEX"]
        price_types = ["Adj Close", "Close"]
        cols = pd.MultiIndex.from_product([price_types, tickers])
        raw = pd.DataFrame(index=mock_prices.index[:5], columns=cols, dtype=float)

        raw[("Adj Close", "AAPL")] = 130.0
        raw[("Close", "AAPL")] = 130.0
        raw[("Adj Close", "FAKEX")] = np.nan   # invalid ticker — all NaN
        raw[("Close", "FAKEX")] = np.nan

        with pytest.raises(ValueError, match="FAKEX"):
            _extract_adj_close(raw, tickers)

    def test_flat_single_ticker_columns(self, mocker, mock_prices):
        """Single-ticker yfinance output (flat columns) handled correctly."""
        flat_df = pd.DataFrame(
            {
                "Open":      mock_prices["AAPL"].iloc[:20].values,
                "High":      mock_prices["AAPL"].iloc[:20].values,
                "Low":       mock_prices["AAPL"].iloc[:20].values,
                "Close":     mock_prices["AAPL"].iloc[:20].values,
                "Adj Close": mock_prices["AAPL"].iloc[:20].values,
                "Volume":    [1_000_000] * 20,
            },
            index=mock_prices.index[:20],
        )
        prices = _extract_adj_close(flat_df, ["AAPL"])
        assert list(prices.columns) == ["AAPL"]
        assert len(prices) == 20

    def test_missing_adj_close_column_raises(self):
        """DataFrame without Adj Close column raises ValueError."""
        raw = pd.DataFrame({"Close": [100, 101, 102]})
        with pytest.raises(ValueError, match="Adj Close"):
            _extract_adj_close(raw, ["AAPL"])


# ── _fetch_price_data_impl ────────────────────────────────────────────────────

class TestFetchPriceDataImpl:
    def test_returns_dataframe(self, mock_yfinance_download, mock_prices):
        """Full pipeline returns a DataFrame with expected shape."""
        prices = _fetch_price_data_impl(["AAPL", "MSFT", "GOOGL", "SPY"], "3y")
        assert isinstance(prices, pd.DataFrame)
        assert set(prices.columns) == {"AAPL", "MSFT", "GOOGL", "SPY"}

    def test_no_nan_in_output(self, mock_yfinance_download, mock_prices):
        """Output DataFrame contains no NaN values."""
        prices = _fetch_price_data_impl(["AAPL", "MSFT"], "3y")
        assert not prices.isnull().any().any()

    def test_all_prices_positive(self, mock_yfinance_download, mock_prices):
        """All returned prices are strictly positive."""
        prices = _fetch_price_data_impl(["AAPL", "MSFT", "GOOGL", "SPY"], "3y")
        assert (prices > 0).all().all()

    def test_raises_on_empty_download(self, mocker):
        """ValueError raised when yfinance returns an empty DataFrame."""
        mocker.patch("yfinance.download", return_value=pd.DataFrame())
        with pytest.raises(ValueError):
            _fetch_price_data_impl(["AAPL"], "3y")


# ── _fetch_risk_free_rate_impl ────────────────────────────────────────────────

class TestFetchRiskFreeRateImpl:
    def test_correct_conversion(self, mock_irx_download):
        """^IRX value of 5.0 converts correctly to 5.0 / 100 / 252."""
        rate = _fetch_risk_free_rate_impl()
        expected = 5.0 / 100.0 / 252.0
        assert abs(rate - expected) < 1e-10

    def test_returns_float(self, mock_irx_download):
        """Return type is float."""
        rate = _fetch_risk_free_rate_impl()
        assert isinstance(rate, float)

    def test_rate_positive(self, mock_irx_download):
        """Returned rate is strictly positive."""
        rate = _fetch_risk_free_rate_impl()
        assert rate > 0.0

    def test_last_valid_value_used_with_nan(self, mock_irx_download_with_nan):
        """When ^IRX has leading NaN rows, the last valid value (5.0) is used."""
        rate = _fetch_risk_free_rate_impl()
        expected = 5.0 / 100.0 / 252.0
        assert abs(rate - expected) < 1e-10

    def test_fallback_on_fetch_failure(self, mocker):
        """Returns fallback rate when yfinance raises an exception."""
        mocker.patch("yfinance.download", side_effect=Exception("network error"))
        rate = _fetch_risk_free_rate_impl()
        assert abs(rate - _FALLBACK_DAILY_RATE) < 1e-12

    def test_fallback_on_empty_result(self, mocker):
        """Returns fallback rate when yfinance returns empty DataFrame."""
        mocker.patch("yfinance.download", return_value=pd.DataFrame())
        rate = _fetch_risk_free_rate_impl()
        assert abs(rate - _FALLBACK_DAILY_RATE) < 1e-12

    def test_daily_rate_magnitude(self, mock_irx_download):
        """Daily rate is in a plausible range (0.5% to 15% annualized)."""
        rate = _fetch_risk_free_rate_impl()
        # rate is daily decimal: plausible annualized range is 0.5%-15%
        assert 0.005 / 252 < rate < 0.15 / 252


# ── validate_tickers ─────────────────────────────────────────────────────────

class TestValidateTickers:
    def test_all_valid(self, mock_yfinance_download):
        """All tickers with data are returned as valid."""
        valid, invalid = validate_tickers(["AAPL", "MSFT", "GOOGL", "SPY"])
        assert set(valid) == {"AAPL", "MSFT", "GOOGL", "SPY"}
        assert invalid == []

    def test_empty_input(self):
        """Empty ticker list returns empty valid and invalid lists."""
        valid, invalid = validate_tickers([])
        assert valid == []
        assert invalid == []

    def test_network_failure_passes_through(self, mocker):
        """On network failure, all tickers are passed through as valid — let the main fetch surface the real error."""
        mocker.patch("yfinance.download", side_effect=Exception("network error"))
        valid, invalid = validate_tickers(["AAPL", "MSFT"])
        assert set(valid) == {"AAPL", "MSFT"}
        assert invalid == []
