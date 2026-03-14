"""tests/test_optimization.py

Unit tests for analytics/optimization.py.

Test plan (Session 7):
- test_max_sharpe_weights_sum_to_one: sum(weights) = 1 within 1e-6.
- test_max_sharpe_weights_non_negative: all weights >= 0.
- test_max_sharpe_weights_within_bounds: all weights in [weight_min, weight_max].
- test_min_var_weights_sum_to_one: same constraint check.
- test_min_var_weights_non_negative: same constraint check.
- test_min_var_weights_within_bounds: same constraint check.
- test_risk_parity_weights_sum_to_one: same constraint check.
- test_risk_parity_weights_non_negative: same constraint check.
- test_risk_parity_weights_within_bounds: same constraint check.
- test_frontier_length: frontier has DEFAULT_FRONTIER_POINTS (50) points.
- test_frontier_returns_increasing: frontier returns are monotonically increasing.
- test_frontier_vols_u_shaped: min variance is at left of frontier.

All three optimizer portfolios tested for constraint satisfaction.
No real API calls. All tests use fixtures from conftest.py.
"""

import pytest
from assets.config import DEFAULT_FRONTIER_POINTS, DEFAULT_WEIGHT_MIN, DEFAULT_WEIGHT_MAX


class TestMaxSharpe:
    def test_max_sharpe_weights_sum_to_one(self, mock_returns, mock_weights, mock_risk_free_rate):
        pytest.skip("Implemented in Session 7.")

    def test_max_sharpe_weights_non_negative(self, mock_returns, mock_weights, mock_risk_free_rate):
        pytest.skip("Implemented in Session 7.")

    def test_max_sharpe_weights_within_bounds(self, mock_returns, mock_weights, mock_risk_free_rate):
        pytest.skip("Implemented in Session 7.")


class TestMinVariance:
    def test_min_var_weights_sum_to_one(self, mock_returns, mock_weights, mock_risk_free_rate):
        pytest.skip("Implemented in Session 7.")

    def test_min_var_weights_non_negative(self, mock_returns, mock_weights, mock_risk_free_rate):
        pytest.skip("Implemented in Session 7.")

    def test_min_var_weights_within_bounds(self, mock_returns, mock_weights, mock_risk_free_rate):
        pytest.skip("Implemented in Session 7.")


class TestRiskParity:
    def test_risk_parity_weights_sum_to_one(self, mock_returns, mock_weights, mock_risk_free_rate):
        pytest.skip("Implemented in Session 7.")

    def test_risk_parity_weights_non_negative(self, mock_returns, mock_weights, mock_risk_free_rate):
        pytest.skip("Implemented in Session 7.")

    def test_risk_parity_weights_within_bounds(self, mock_returns, mock_weights, mock_risk_free_rate):
        pytest.skip("Implemented in Session 7.")


class TestEfficientFrontier:
    def test_frontier_length(self, mock_returns, mock_weights, mock_risk_free_rate):
        pytest.skip("Implemented in Session 7.")

    def test_frontier_returns_increasing(self, mock_returns, mock_weights, mock_risk_free_rate):
        pytest.skip("Implemented in Session 7.")

    def test_frontier_vols_u_shaped(self, mock_returns, mock_weights, mock_risk_free_rate):
        pytest.skip("Implemented in Session 7.")
