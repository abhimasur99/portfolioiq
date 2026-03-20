"""tests/test_performance.py

Unit tests for analytics/performance.py.

Test coverage:
- test_cagr_manual: verify CAGR against manually computed value for known returns.
- test_sharpe_manual: verify Sharpe = (mean(rp) - rf) * sqrt(252) / std(rp).
- test_sortino_downside_only: downside sigma uses only negative returns.
- test_treynor_manual: verify Treynor = (mean(rp) - rf)*252 / beta.
- test_beta_ols: beta via Cov(Rp,Rb)/Var(Rb) matches scipy linregress slope.
- test_r_squared_correlation: R² = squared Pearson correlation(Rp, Rb).
- test_sharpe_zero_vol_protected: zero volatility input returns 0.0 (not div/0 error).
- test_sortino_zero_downside_protected: no negative returns returns 0.0.
- test_treynor_zero_beta_protected: zero beta returns 0.0.
- test_rolling_sharpe_length: rolling Sharpe has correct length and leading NaN.
- test_rolling_beta_length: rolling beta has correct length and leading NaN.

No real API calls. All tests use fixtures from conftest.py.
"""

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from analytics.performance import (
    compute_cagr,
    compute_sharpe,
    compute_sortino,
    compute_treynor,
    compute_info_ratio,
    compute_alpha_beta,
    compute_rolling_sharpe,
    compute_rolling_beta,
    compute_all_performance,
)


class TestCAGR:
    def test_cagr_manual(self, mock_portfolio_returns):
        """CAGR matches exp(mean * 252) - 1 computed manually."""
        expected = float(np.exp(mock_portfolio_returns.mean() * 252) - 1.0)
        result = compute_cagr(mock_portfolio_returns)
        assert abs(result - expected) < 1e-12

    def test_cagr_known_value(self):
        """CAGR on constant daily return of ln(1.1)/252 gives exactly 10% per year."""
        daily_r = np.log(1.10) / 252.0
        returns = pd.Series([daily_r] * 252)
        cagr = compute_cagr(returns)
        assert abs(cagr - 0.10) < 1e-10

    def test_cagr_returns_float(self, mock_portfolio_returns):
        assert isinstance(compute_cagr(mock_portfolio_returns), float)


class TestRatios:
    def test_sharpe_manual(self, mock_portfolio_returns, mock_risk_free_rate):
        """Sharpe = (mean(rp) - rf_daily) * sqrt(252) / std(rp)."""
        rp = mock_portfolio_returns
        rf = mock_risk_free_rate
        expected = float((rp.mean() - rf) * np.sqrt(252) / rp.std())
        result = compute_sharpe(rp, rf)
        assert abs(result - expected) < 1e-12

    def test_sortino_downside_only(self, mock_portfolio_returns, mock_risk_free_rate):
        """Sortino denominator uses only negative returns, not all returns."""
        rp = mock_portfolio_returns
        rf = mock_risk_free_rate
        neg = rp[rp < 0]
        downside_std = float(neg.std()) * np.sqrt(252)
        ann_excess = (rp.mean() - rf) * 252
        expected = float(ann_excess / downside_std)
        result = compute_sortino(rp, rf)
        assert abs(result - expected) < 1e-12

    def test_treynor_manual(
        self, mock_portfolio_returns, mock_benchmark_returns, mock_risk_free_rate
    ):
        """Treynor = (mean(rp) - rf)*252 / beta."""
        rp = mock_portfolio_returns
        rb = mock_benchmark_returns
        rf = mock_risk_free_rate
        beta = float(np.cov(rp.values, rb.values, ddof=1)[0, 1] / rb.var())
        ann_excess = (rp.mean() - rf) * 252
        expected = float(ann_excess / beta)
        result = compute_treynor(rp, rb, rf)
        assert abs(result - expected) < 1e-12

    def test_info_ratio_manual(self, mock_portfolio_returns, mock_benchmark_returns):
        """IR = mean(active) * sqrt(252) / std(active)."""
        rp = mock_portfolio_returns
        rb = mock_benchmark_returns
        active = rp - rb
        expected = float(active.mean() * np.sqrt(252) / active.std())
        result = compute_info_ratio(rp, rb)
        assert abs(result - expected) < 1e-12

    def test_sharpe_zero_vol_protected(self):
        """Constant returns (zero vol) returns Sharpe of 0.0, not inf or error."""
        constant_returns = pd.Series([0.001] * 252)
        result = compute_sharpe(constant_returns, risk_free_rate=0.0001)
        assert result == 0.0

    def test_sortino_zero_downside_protected(self):
        """All-positive returns (no negative) returns Sortino of 0.0."""
        all_positive = pd.Series([0.005] * 252)
        result = compute_sortino(all_positive, risk_free_rate=0.0001)
        assert result == 0.0

    def test_treynor_zero_beta_protected(self):
        """Constant portfolio with varying benchmark gives beta=0, Treynor=0.0.

        With rp constant: (rp[i] - mean(rp)) = 0 exactly, so Cov(rp, rb) = 0.
        With rb varying: Var(rb) > 0. Beta = 0 / Var(rb) = 0.0 exactly.
        """
        n = 252
        rp = pd.Series([0.001] * n)                           # constant → cov = 0
        rb = pd.Series([0.01 if i % 2 == 0 else -0.01 for i in range(n)])  # varying
        result = compute_treynor(rp, rb, risk_free_rate=0.0001)
        assert result == 0.0


class TestBetaAlpha:
    def test_beta_ols(self, mock_portfolio_returns, mock_benchmark_returns):
        """Beta Cov(Rp,Rb)/Var(Rb) matches scipy.stats.linregress slope."""
        rp = mock_portfolio_returns
        rb = mock_benchmark_returns
        slope, _, _, _, _ = stats.linregress(rb.values, rp.values)
        _, beta, _ = compute_alpha_beta(rp, rb, risk_free_rate=0.0001)
        assert abs(beta - slope) < 1e-10

    def test_r_squared_correlation(self, mock_portfolio_returns, mock_benchmark_returns):
        """R² equals squared Pearson correlation of Rp and Rb."""
        rp = mock_portfolio_returns
        rb = mock_benchmark_returns
        expected_r2 = float(rp.corr(rb) ** 2)
        _, _, r_squared = compute_alpha_beta(rp, rb, risk_free_rate=0.0001)
        assert abs(r_squared - expected_r2) < 1e-12

    def test_alpha_beta_returns_floats(
        self, mock_portfolio_returns, mock_benchmark_returns
    ):
        """alpha, beta, r_squared are all Python floats."""
        alpha, beta, r2 = compute_alpha_beta(
            mock_portfolio_returns, mock_benchmark_returns, risk_free_rate=0.0001
        )
        assert isinstance(alpha, float)
        assert isinstance(beta, float)
        assert isinstance(r2, float)

    def test_r_squared_in_unit_interval(
        self, mock_portfolio_returns, mock_benchmark_returns
    ):
        """R² is in [0, 1]."""
        _, _, r2 = compute_alpha_beta(
            mock_portfolio_returns, mock_benchmark_returns, risk_free_rate=0.0001
        )
        assert 0.0 <= r2 <= 1.0


class TestRollingMetrics:
    def test_rolling_sharpe_length(self, mock_portfolio_returns, mock_risk_free_rate):
        """Rolling Sharpe has same length as input."""
        result = compute_rolling_sharpe(mock_portfolio_returns, mock_risk_free_rate)
        assert len(result) == len(mock_portfolio_returns)

    def test_rolling_sharpe_leading_nan(self, mock_portfolio_returns, mock_risk_free_rate):
        """First 251 values are NaN (window=252 requires 252 observations)."""
        result = compute_rolling_sharpe(mock_portfolio_returns, mock_risk_free_rate, window=252)
        assert result.iloc[:251].isna().all()
        assert pd.notna(result.iloc[251])

    def test_rolling_beta_length(self, mock_portfolio_returns, mock_benchmark_returns):
        """Rolling beta has same length as input."""
        result = compute_rolling_beta(mock_portfolio_returns, mock_benchmark_returns)
        assert len(result) == len(mock_portfolio_returns)

    def test_rolling_beta_leading_nan(
        self, mock_portfolio_returns, mock_benchmark_returns
    ):
        """First 251 values are NaN (window=252 requires 252 observations)."""
        result = compute_rolling_beta(
            mock_portfolio_returns, mock_benchmark_returns, window=252
        )
        assert result.iloc[:251].isna().all()
        assert pd.notna(result.iloc[251])


class TestComputeAllPerformance:
    def test_all_keys_present(
        self, mock_portfolio_returns, mock_benchmark_returns, mock_risk_free_rate
    ):
        """compute_all_performance returns all expected keys."""
        result = compute_all_performance(
            mock_portfolio_returns, mock_benchmark_returns, mock_risk_free_rate
        )
        expected_keys = {
            "cagr", "volatility", "sharpe", "sortino", "treynor",
            "information_ratio", "alpha", "beta", "r_squared",
            "rolling_sharpe", "rolling_beta",
            "rolling_sharpe_window", "rolling_beta_window",
            "best_month", "worst_month", "best_year", "worst_year",
        }
        assert expected_keys == set(result.keys())

    def test_rolling_series_in_output(
        self, mock_portfolio_returns, mock_benchmark_returns, mock_risk_free_rate
    ):
        """rolling_sharpe and rolling_beta are pd.Series objects."""
        result = compute_all_performance(
            mock_portfolio_returns, mock_benchmark_returns, mock_risk_free_rate
        )
        assert isinstance(result["rolling_sharpe"], pd.Series)
        assert isinstance(result["rolling_beta"], pd.Series)

    def test_scalar_metrics_are_floats(
        self, mock_portfolio_returns, mock_benchmark_returns, mock_risk_free_rate
    ):
        """All scalar metrics are Python floats."""
        result = compute_all_performance(
            mock_portfolio_returns, mock_benchmark_returns, mock_risk_free_rate
        )
        scalar_keys = [
            "cagr", "volatility", "sharpe", "sortino", "treynor",
            "information_ratio", "alpha", "beta", "r_squared",
            "best_month", "worst_month", "best_year", "worst_year",
        ]
        for key in scalar_keys:
            assert isinstance(result[key], float), f"{key} is not a float"

    def test_best_month_gte_worst_month(
        self, mock_portfolio_returns, mock_benchmark_returns, mock_risk_free_rate
    ):
        """best_month >= worst_month (sanity check)."""
        result = compute_all_performance(
            mock_portfolio_returns, mock_benchmark_returns, mock_risk_free_rate
        )
        assert result["best_month"] >= result["worst_month"]

    def test_volatility_positive(
        self, mock_portfolio_returns, mock_benchmark_returns, mock_risk_free_rate
    ):
        """Annualized volatility is strictly positive for real data."""
        result = compute_all_performance(
            mock_portfolio_returns, mock_benchmark_returns, mock_risk_free_rate
        )
        assert result["volatility"] > 0.0
