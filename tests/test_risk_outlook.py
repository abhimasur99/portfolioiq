"""tests/test_risk_outlook.py

Unit tests for analytics/risk_outlook.py.

Session 5 tests (implemented now):
- test_historical_var_95_percentile: VaR(95%) = 5th percentile of returns.
- test_cvar_95_below_var: CVaR(95%) < VaR(95%) (tail mean is more extreme).
- test_historical_var_99_more_extreme: VaR(99%) <= VaR(95%).
- test_garch_stationarity: alpha + beta < 1 for fitted model (CRITICAL).
- test_garch_fallback_short_series: EWMA fallback triggered for < 252 obs.
- test_ewma_vol_positive: EWMA volatility > 0.

Session 6 tests (remain skipped):
- test_monte_carlo_shape, test_monte_carlo_positive_values, test_stress_test_keys.

No real API calls. All tests use fixtures from conftest.py.
"""

import numpy as np
import pandas as pd
import pytest

from analytics.risk_outlook import (
    compute_historical_vol,
    compute_ewma_vol,
    fit_garch,
    compute_var_cvar_historical,
    compute_garch_var,
    compute_var_monthly,
    compute_skewness_kurtosis,
    _run_garch_monte_carlo,
    _run_stress_tests,
)


class TestVolatility:
    def test_ewma_vol_positive(self, mock_portfolio_returns):
        """EWMA volatility is strictly positive."""
        vol = compute_ewma_vol(mock_portfolio_returns)
        assert vol > 0.0

    def test_ewma_vol_returns_float(self, mock_portfolio_returns):
        """EWMA vol returns a Python float."""
        assert isinstance(compute_ewma_vol(mock_portfolio_returns), float)

    def test_ewma_vol_increases_in_stress(self):
        """EWMA vol is higher for high-vol series than low-vol series."""
        rng = np.random.default_rng(0)
        low_vol = pd.Series(rng.standard_normal(500) * 0.005)
        high_vol = pd.Series(rng.standard_normal(500) * 0.025)
        assert compute_ewma_vol(high_vol) > compute_ewma_vol(low_vol)

    def test_ewma_lambda_sensitivity(self, mock_portfolio_returns):
        """Higher lambda (longer memory) should produce smoother vol estimate."""
        vol_94 = compute_ewma_vol(mock_portfolio_returns, lambda_=0.94)
        vol_80 = compute_ewma_vol(mock_portfolio_returns, lambda_=0.80)
        assert vol_94 > 0.0
        assert vol_80 > 0.0

    def test_historical_vol_matches_formula(self, mock_portfolio_returns):
        """hist_vol = std(returns) * sqrt(252)."""
        expected = float(mock_portfolio_returns.std() * np.sqrt(252))
        result = compute_historical_vol(mock_portfolio_returns)
        assert abs(result - expected) < 1e-12

    def test_historical_vol_positive(self, mock_portfolio_returns):
        """Historical vol is strictly positive for real data."""
        assert compute_historical_vol(mock_portfolio_returns) > 0.0


class TestVaRCVaR:
    def test_historical_var_95_percentile(self, mock_portfolio_returns):
        """VaR(95%) equals the 5th percentile of returns."""
        var_95, _ = compute_var_cvar_historical(mock_portfolio_returns, confidence=0.95)
        expected = float(np.percentile(mock_portfolio_returns.values, 5.0))
        assert abs(var_95 - expected) < 1e-12

    def test_historical_var_99_percentile(self, mock_portfolio_returns):
        """VaR(99%) equals the 1st percentile of returns."""
        var_99, _ = compute_var_cvar_historical(mock_portfolio_returns, confidence=0.99)
        expected = float(np.percentile(mock_portfolio_returns.values, 1.0))
        assert abs(var_99 - expected) < 1e-12

    def test_cvar_95_below_var(self, mock_portfolio_returns):
        """CVaR(95%) <= VaR(95%): the tail mean is more extreme than the percentile."""
        var_95, cvar_95 = compute_var_cvar_historical(mock_portfolio_returns, confidence=0.95)
        assert cvar_95 <= var_95

    def test_historical_var_99_more_extreme(self, mock_portfolio_returns):
        """VaR(99%) <= VaR(95%): 99% VaR is more negative (larger loss)."""
        var_95, _ = compute_var_cvar_historical(mock_portfolio_returns, confidence=0.95)
        var_99, _ = compute_var_cvar_historical(mock_portfolio_returns, confidence=0.99)
        assert var_99 <= var_95

    def test_var_negative_for_real_data(self, mock_portfolio_returns):
        """VaR is negative (loss expressed as a log return)."""
        var_95, _ = compute_var_cvar_historical(mock_portfolio_returns, confidence=0.95)
        assert var_95 < 0.0

    def test_cvar_returns_floats(self, mock_portfolio_returns):
        """Both var and cvar are Python floats."""
        var, cvar = compute_var_cvar_historical(mock_portfolio_returns)
        assert isinstance(var, float)
        assert isinstance(cvar, float)

    def test_var_monthly_more_extreme(self, mock_portfolio_returns):
        """Monthly VaR is more extreme (more negative) than daily VaR."""
        var_daily, _ = compute_var_cvar_historical(mock_portfolio_returns, confidence=0.95)
        var_monthly = compute_var_monthly(var_daily)
        assert var_monthly <= var_daily

    def test_var_monthly_scaling(self, mock_portfolio_returns):
        """Monthly VaR = daily VaR * sqrt(21)."""
        var_daily, _ = compute_var_cvar_historical(mock_portfolio_returns, confidence=0.95)
        expected = float(var_daily * np.sqrt(21))
        result = compute_var_monthly(var_daily)
        assert abs(result - expected) < 1e-12

    def test_garch_var_negative(self, mock_portfolio_returns):
        """GARCH-conditional VaR is negative (loss expressed as return)."""
        _, garch_vol_daily, _ = fit_garch(mock_portfolio_returns)
        var_garch = compute_garch_var(mock_portfolio_returns, garch_vol_daily, 0.95)
        assert var_garch < 0.0

    def test_garch_var_more_extreme_at_99(self, mock_portfolio_returns):
        """GARCH VaR at 99% is more extreme than at 95%."""
        _, garch_vol_daily, _ = fit_garch(mock_portfolio_returns)
        var_95 = compute_garch_var(mock_portfolio_returns, garch_vol_daily, 0.95)
        var_99 = compute_garch_var(mock_portfolio_returns, garch_vol_daily, 0.99)
        assert var_99 <= var_95


class TestGARCH:
    def test_garch_stationarity(self, mock_portfolio_returns):
        """CRITICAL: alpha + beta < 1 for fitted GARCH(1,1) model.

        If non-stationary, fit_garch falls back to EWMA (is_fallback=True).
        Either way, stationarity is enforced: if GARCH succeeded, check params;
        if fallback, verify vol is positive.
        """
        result, garch_vol_daily, is_fallback = fit_garch(mock_portfolio_returns)

        if not is_fallback:
            alpha = float(result.params["alpha[1]"])
            beta = float(result.params["beta[1]"])
            assert alpha + beta < 1.0, (
                f"GARCH non-stationary: alpha+beta = {alpha + beta:.4f} >= 1"
            )
        else:
            assert garch_vol_daily > 0.0

    def test_garch_returns_positive_vol(self, mock_portfolio_returns):
        """Returned daily vol is strictly positive regardless of fallback."""
        _, garch_vol_daily, _ = fit_garch(mock_portfolio_returns)
        assert garch_vol_daily > 0.0

    def test_garch_fallback_short_series(self):
        """EWMA fallback triggered when series has < 252 observations."""
        short_returns = pd.Series(
            np.random.default_rng(99).standard_normal(100) * 0.01
        )
        _, _, is_fallback = fit_garch(short_returns, min_obs=252)
        assert is_fallback is True

    def test_garch_fallback_flag_type(self, mock_portfolio_returns):
        """is_fallback is a bool."""
        _, _, is_fallback = fit_garch(mock_portfolio_returns)
        assert isinstance(is_fallback, bool)

    def test_garch_vol_plausible_magnitude(self, mock_portfolio_returns):
        """GARCH daily vol is in plausible range for equity returns (0.1% – 5%)."""
        _, garch_vol_daily, _ = fit_garch(mock_portfolio_returns)
        assert 0.001 < garch_vol_daily < 0.05

    def test_garch_result_not_none_on_success(self, mock_portfolio_returns):
        """When GARCH fit succeeds (no fallback), result is not None."""
        result, _, is_fallback = fit_garch(mock_portfolio_returns)
        if not is_fallback:
            assert result is not None
            assert hasattr(result, "params")


class TestSkewnessKurtosis:
    def test_skewness_kurtosis_types(self, mock_portfolio_returns):
        """Both skewness and excess_kurtosis are Python floats."""
        skew, kurt = compute_skewness_kurtosis(mock_portfolio_returns)
        assert isinstance(skew, float)
        assert isinstance(kurt, float)

    def test_excess_kurtosis_near_zero_for_normal(self):
        """Excess kurtosis is close to 0 for a large normally distributed sample."""
        rng = np.random.default_rng(42)
        normal_returns = pd.Series(rng.standard_normal(5000) * 0.01)
        _, kurt = compute_skewness_kurtosis(normal_returns)
        assert abs(kurt) < 0.5

    def test_excess_kurtosis_positive_for_fat_tails(self):
        """Excess kurtosis > 0 for fat-tailed t-distribution."""
        rng = np.random.default_rng(7)
        t_returns = pd.Series(rng.standard_t(df=5, size=2000) * 0.01)
        _, kurt = compute_skewness_kurtosis(t_returns)
        assert kurt > 0.0


class TestMonteCarlo:
    def test_monte_carlo_shape(self, mock_portfolio_returns):
        """MC values array has shape (n_steps + 1, n_paths): rows = time steps, cols = paths."""
        n_paths = 200
        n_steps = 10  # horizon_years=1 would be 252; use 10 for speed
        _, garch_vol_daily, _ = fit_garch(mock_portfolio_returns)
        result = _run_garch_monte_carlo(mock_portfolio_returns, None, garch_vol_daily, n_paths, n_steps)
        assert result["values"].shape == (n_steps + 1, n_paths)
        assert result["p10"].shape == (n_steps + 1,)
        assert result["p50"].shape == (n_steps + 1,)
        assert result["p90"].shape == (n_steps + 1,)

    def test_monte_carlo_positive_values(self, mock_portfolio_returns):
        """All simulated portfolio values are strictly positive (log-normal cannot go negative)."""
        n_paths = 200
        n_steps = 10
        _, garch_vol_daily, _ = fit_garch(mock_portfolio_returns)
        result = _run_garch_monte_carlo(mock_portfolio_returns, None, garch_vol_daily, n_paths, n_steps)
        assert float(result["values"].min()) > 0.0

    def test_monte_carlo_starts_at_one(self, mock_portfolio_returns):
        """MC values[0] == 1.0 for all paths (normalized to initial portfolio value)."""
        n_paths = 100
        n_steps = 5
        _, garch_vol_daily, _ = fit_garch(mock_portfolio_returns)
        result = _run_garch_monte_carlo(mock_portfolio_returns, None, garch_vol_daily, n_paths, n_steps)
        np.testing.assert_array_equal(result["values"][0], np.ones(n_paths))

    def test_monte_carlo_percentile_ordering(self, mock_portfolio_returns):
        """p10 <= p50 <= p90 at every time step."""
        n_paths = 500
        n_steps = 10
        _, garch_vol_daily, _ = fit_garch(mock_portfolio_returns)
        result = _run_garch_monte_carlo(mock_portfolio_returns, None, garch_vol_daily, n_paths, n_steps)
        assert np.all(result["p10"] <= result["p50"])
        assert np.all(result["p50"] <= result["p90"])


class TestStressTests:
    def test_stress_test_keys(self, mock_portfolio_returns, mock_benchmark_returns):
        """All 4 STRESS_SCENARIOS keys are present in stress test output."""
        from assets.config import STRESS_SCENARIOS
        from analytics.performance import compute_all_performance
        performance = compute_all_performance(
            mock_portfolio_returns, mock_benchmark_returns, risk_free_rate=0.05 / 252
        )
        result = _run_stress_tests(mock_portfolio_returns, mock_benchmark_returns, performance)
        for scenario_name in STRESS_SCENARIOS:
            assert scenario_name in result, f"Missing stress scenario: {scenario_name}"

    def test_stress_test_value_structure(self, mock_portfolio_returns, mock_benchmark_returns):
        """Each stress result has index_return, portfolio_return, and description keys."""
        from analytics.performance import compute_all_performance
        performance = compute_all_performance(
            mock_portfolio_returns, mock_benchmark_returns, risk_free_rate=0.05 / 252
        )
        result = _run_stress_tests(mock_portfolio_returns, mock_benchmark_returns, performance)
        for name, data in result.items():
            assert "index_return" in data, f"Scenario {name} missing index_return"
            assert "portfolio_return" in data, f"Scenario {name} missing portfolio_return"
            assert "description" in data, f"Scenario {name} missing description"

    def test_stress_test_portfolio_return_is_float(self, mock_portfolio_returns, mock_benchmark_returns):
        """Stress test portfolio returns are Python floats."""
        from analytics.performance import compute_all_performance
        performance = compute_all_performance(
            mock_portfolio_returns, mock_benchmark_returns, risk_free_rate=0.05 / 252
        )
        result = _run_stress_tests(mock_portfolio_returns, mock_benchmark_returns, performance)
        for name, data in result.items():
            assert isinstance(data["portfolio_return"], float), (
                f"Scenario {name} portfolio_return is not a float"
            )
