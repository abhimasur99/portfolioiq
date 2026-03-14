"""tests/test_performance.py

Unit tests for analytics/performance.py.

Test plan (Session 3):
- test_cagr_manual: verify CAGR against manually computed value for known returns.
- test_sharpe_manual: verify Sharpe = (Rp - Rf) / sigma against known values.
- test_sortino_downside_only: downside sigma uses only negative returns.
- test_beta_ols: beta via Cov(Rp,Rb)/Var(Rb) matches scipy OLS coefficient.
- test_r_squared_correlation: R² = squared Pearson correlation(Rp, Rb).
- test_sharpe_zero_vol_protected: zero volatility input returns 0.0 (not div/0 error).
- test_sortino_zero_downside_protected: zero downside vol returns 0.0.
- test_treynor_zero_beta_protected: zero beta returns 0.0.
- test_rolling_sharpe_length: rolling Sharpe has correct length.
- test_rolling_beta_length: rolling beta has correct length.

No real API calls. All tests use fixtures from conftest.py.
"""

import pytest


class TestCAGR:
    def test_cagr_manual(self, mock_portfolio_returns):
        pytest.skip("Implemented in Session 3.")


class TestRatios:
    def test_sharpe_manual(self, mock_portfolio_returns, mock_risk_free_rate):
        pytest.skip("Implemented in Session 3.")

    def test_sortino_downside_only(self, mock_portfolio_returns, mock_risk_free_rate):
        pytest.skip("Implemented in Session 3.")

    def test_treynor_manual(self, mock_portfolio_returns, mock_benchmark_returns, mock_risk_free_rate):
        pytest.skip("Implemented in Session 3.")

    def test_sharpe_zero_vol_protected(self):
        pytest.skip("Implemented in Session 3.")

    def test_sortino_zero_downside_protected(self):
        pytest.skip("Implemented in Session 3.")

    def test_treynor_zero_beta_protected(self):
        pytest.skip("Implemented in Session 3.")


class TestBetaAlpha:
    def test_beta_ols(self, mock_portfolio_returns, mock_benchmark_returns):
        pytest.skip("Implemented in Session 3.")

    def test_r_squared_correlation(self, mock_portfolio_returns, mock_benchmark_returns):
        pytest.skip("Implemented in Session 3.")


class TestRollingMetrics:
    def test_rolling_sharpe_length(self, mock_portfolio_returns, mock_risk_free_rate):
        pytest.skip("Implemented in Session 3.")

    def test_rolling_beta_length(self, mock_portfolio_returns, mock_benchmark_returns):
        pytest.skip("Implemented in Session 3.")
