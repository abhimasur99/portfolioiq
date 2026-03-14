"""tests/test_risk_outlook.py

Unit tests for analytics/risk_outlook.py.

Test plan (Sessions 5–6):
- test_historical_var_95_percentile: VaR(95%) = 5th percentile of returns.
- test_cvar_95_below_var: CVaR(95%) < VaR(95%) (more extreme).
- test_historical_var_99_more_extreme: VaR(99%) <= VaR(95%).
- test_garch_stationarity: MOST IMPORTANT TEST — alpha + beta < 1 for fitted model.
- test_garch_fallback_short_series: EWMA fallback triggered for < 252 obs.
- test_monte_carlo_shape: output matrix shape = (steps+1, n_paths).
- test_monte_carlo_positive_values: all simulated portfolio values > 0.
- test_stress_test_keys: all four scenarios present in output.
- test_ewma_vol_positive: EWMA volatility > 0.

No real API calls. All tests use fixtures from conftest.py.
"""

import pytest


class TestVaRCVaR:
    def test_historical_var_95_percentile(self, mock_portfolio_returns):
        pytest.skip("Implemented in Session 5.")

    def test_cvar_95_below_var(self, mock_portfolio_returns):
        pytest.skip("Implemented in Session 5.")

    def test_historical_var_99_more_extreme(self, mock_portfolio_returns):
        pytest.skip("Implemented in Session 5.")


class TestGARCH:
    def test_garch_stationarity(self, mock_portfolio_returns):
        """CRITICAL: alpha + beta < 1 for fitted GARCH(1,1) model."""
        pytest.skip("Implemented in Session 5.")

    def test_garch_fallback_short_series(self):
        pytest.skip("Implemented in Session 5.")


class TestMonteCarlo:
    def test_monte_carlo_shape(self, mock_portfolio_returns):
        pytest.skip("Implemented in Session 6.")

    def test_monte_carlo_positive_values(self, mock_portfolio_returns):
        pytest.skip("Implemented in Session 6.")


class TestStressTests:
    def test_stress_test_keys(self, mock_portfolio_returns):
        pytest.skip("Implemented in Session 6.")


class TestVolatility:
    def test_ewma_vol_positive(self, mock_portfolio_returns):
        pytest.skip("Implemented in Session 5.")
