"""tests/test_returns.py

Unit tests for analytics/returns.py.

Test coverage:
- test_log_return_formula: manually verify rt = ln(Pt/Pt-1) for known prices.
- test_log_returns_shape: output has one fewer row than input prices.
- test_log_returns_no_nan: output contains no NaN values.
- test_portfolio_returns_shape: same length as returns_df.
- test_portfolio_returns_weighted: verify dot product with known weights and returns.
- test_weights_normalization_error: ValueError if weights don't sum to 1 ± 1e-6.
- test_single_asset_portfolio: portfolio returns equal single ticker returns when w=1.

No real API calls. All tests use fixtures from conftest.py.
"""

import numpy as np
import pandas as pd
import pytest

from analytics.returns import compute_log_returns, compute_portfolio_returns


class TestLogReturns:
    def test_log_return_formula(self):
        """rt = ln(Pt / Pt-1) verified on known prices."""
        prices = pd.DataFrame(
            {"A": [100.0, 110.0, 99.0], "B": [200.0, 180.0, 216.0]},
            index=pd.bdate_range("2024-01-02", periods=3),
        )
        result = compute_log_returns(prices)

        # Manually: ln(110/100), ln(99/110); ln(180/200), ln(216/180)
        assert abs(result["A"].iloc[0] - np.log(110.0 / 100.0)) < 1e-12
        assert abs(result["A"].iloc[1] - np.log(99.0 / 110.0)) < 1e-12
        assert abs(result["B"].iloc[0] - np.log(180.0 / 200.0)) < 1e-12
        assert abs(result["B"].iloc[1] - np.log(216.0 / 180.0)) < 1e-12

    def test_log_returns_shape(self, mock_prices, mock_returns):
        """Output has one fewer row than input prices (first difference dropped)."""
        result = compute_log_returns(mock_prices)
        assert len(result) == len(mock_prices) - 1
        assert list(result.columns) == list(mock_prices.columns)

    def test_log_returns_no_nan(self, mock_returns):
        """Output contains no NaN values."""
        assert not mock_returns.isnull().any().any()

    def test_log_returns_matches_fixture(self, mock_prices, mock_returns):
        """compute_log_returns output matches conftest mock_returns fixture exactly."""
        result = compute_log_returns(mock_prices)
        pd.testing.assert_frame_equal(result, mock_returns)


class TestPortfolioReturns:
    def test_portfolio_returns_shape(
        self, mock_returns, mock_weights, mock_portfolio_returns
    ):
        """Portfolio returns have the same length as returns_df."""
        result = compute_portfolio_returns(mock_returns, mock_weights)
        assert len(result) == len(mock_returns)

    def test_portfolio_returns_weighted(self):
        """Dot product with known weights produces the expected values."""
        dates = pd.bdate_range("2024-01-02", periods=3)
        returns_df = pd.DataFrame(
            {"A": [0.01, -0.02, 0.03], "B": [0.02, 0.01, -0.01]},
            index=dates,
        )
        weights = pd.Series({"A": 0.6, "B": 0.4})
        result = compute_portfolio_returns(returns_df, weights)

        expected = pd.Series(
            [0.01 * 0.6 + 0.02 * 0.4, -0.02 * 0.6 + 0.01 * 0.4, 0.03 * 0.6 + (-0.01) * 0.4],
            index=dates,
        )
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_portfolio_returns_matches_fixture(
        self, mock_returns, mock_weights, mock_portfolio_returns
    ):
        """compute_portfolio_returns output matches conftest mock_portfolio_returns fixture."""
        result = compute_portfolio_returns(mock_returns, mock_weights)
        pd.testing.assert_series_equal(result, mock_portfolio_returns, check_names=False)

    def test_weights_normalization_error(self, mock_returns):
        """ValueError if weights don't sum to 1 within 1e-6 tolerance."""
        bad_weights = pd.Series({"AAPL": 0.5, "MSFT": 0.3})  # sums to 0.8
        with pytest.raises(ValueError, match="sum to 1"):
            compute_portfolio_returns(mock_returns, bad_weights)

    def test_weights_sum_exactly_one_passes(self, mock_returns):
        """Weights summing to exactly 1.0 do not raise."""
        w = pd.Series({"AAPL": 0.5, "MSFT": 0.5})
        result = compute_portfolio_returns(mock_returns, w)
        assert len(result) == len(mock_returns)

    def test_single_asset_portfolio(self, mock_returns):
        """Single asset with weight=1.0 gives portfolio returns equal to that asset."""
        w = pd.Series({"SPY": 1.0})
        result = compute_portfolio_returns(mock_returns, w)
        pd.testing.assert_series_equal(
            result, mock_returns["SPY"], check_names=False
        )
