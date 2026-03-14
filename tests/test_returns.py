"""tests/test_returns.py

Unit tests for analytics/returns.py.

Test plan (Session 3):
- test_log_return_formula: manually verify rt = ln(Pt/Pt-1) for known prices.
- test_log_returns_shape: output has one fewer row than input prices.
- test_log_returns_no_nan: output contains no NaN values.
- test_portfolio_returns_shape: same length as returns_df.
- test_portfolio_returns_weighted: verify dot product with known weights and returns.
- test_weights_normalization_error: ValueError if weights don't sum to 1 ± 1e-6.
- test_single_asset_portfolio: portfolio returns equal single ticker returns when w=1.

No real API calls. All tests use fixtures from conftest.py.
"""

import pytest


class TestLogReturns:
    def test_log_return_formula(self):
        pytest.skip("Implemented in Session 3.")

    def test_log_returns_shape(self, mock_prices, mock_returns):
        pytest.skip("Implemented in Session 3.")

    def test_log_returns_no_nan(self, mock_returns):
        pytest.skip("Implemented in Session 3.")


class TestPortfolioReturns:
    def test_portfolio_returns_shape(self, mock_returns, mock_weights, mock_portfolio_returns):
        pytest.skip("Implemented in Session 3.")

    def test_portfolio_returns_weighted(self):
        pytest.skip("Implemented in Session 3.")

    def test_weights_normalization_error(self, mock_returns):
        pytest.skip("Implemented in Session 3.")

    def test_single_asset_portfolio(self, mock_returns):
        pytest.skip("Implemented in Session 3.")
