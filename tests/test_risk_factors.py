"""tests/test_risk_factors.py

Unit tests for analytics/risk_factors.py.

Test coverage:
- test_pearson_correlation_identity: diagonal of corr_matrix = 1.0.
- test_pearson_correlation_range: all values in [-1, 1].
- test_pearson_correlation_symmetric: corr[i,j] == corr[j,i].
- test_hhi_equal_weights: N equal weights → HHI = 1/N.
- test_effective_n_equal_weights: N equal weights → Effective N = N.
- test_hhi_single_asset: single asset → HHI = 1.0.
- test_diversification_ratio_single_asset: DR = 1.0 for single asset.
- test_diversification_ratio_gt_one: DR > 1.0 for diversified portfolio.
- test_drawdown_no_positive: all drawdown values <= 0.
- test_drawdown_zero_at_peak: drawdown is 0 at all-time high.
- test_max_drawdown_known_path: verify max DD on a constructed price path.
- test_calmar_zero_drawdown_protected: zero max DD returns 0.0 (not div/0).
- test_ulcer_index_flat: Ulcer Index = 0 for non-declining price series.
- test_covariance_positive_definite: all eigenvalues > 0 after regularization.
- test_covariance_symmetric: cov_matrix is symmetric.
- test_covariance_annualized: diag entries ≈ (daily std * sqrt(252))^2.

No real API calls. All tests use fixtures from conftest.py.
"""

import numpy as np
import pandas as pd
import pytest

from analytics.risk_factors import (
    compute_correlation_matrix,
    compute_covariance_matrix,
    compute_hhi,
    compute_effective_n,
    compute_diversification_ratio,
    compute_drawdown_series,
    compute_max_drawdown,
    compute_calmar,
    compute_ulcer_index,
    compute_recovery_time,
)


class TestCorrelation:
    def test_pearson_correlation_identity(self, mock_returns):
        """Diagonal of correlation matrix is 1.0 for all tickers."""
        corr = compute_correlation_matrix(mock_returns)
        diag = np.diag(corr.values)
        np.testing.assert_allclose(diag, np.ones(len(diag)), atol=1e-12)

    def test_pearson_correlation_range(self, mock_returns):
        """All correlation values are in [-1, 1]."""
        corr = compute_correlation_matrix(mock_returns)
        assert (corr.values >= -1.0 - 1e-10).all()
        assert (corr.values <= 1.0 + 1e-10).all()

    def test_pearson_correlation_symmetric(self, mock_returns):
        """Correlation matrix is symmetric: corr[i,j] == corr[j,i]."""
        corr = compute_correlation_matrix(mock_returns)
        np.testing.assert_allclose(corr.values, corr.values.T, atol=1e-12)

    def test_pearson_correlation_shape(self, mock_returns):
        """Correlation matrix is square with shape (n_tickers, n_tickers)."""
        corr = compute_correlation_matrix(mock_returns)
        n = len(mock_returns.columns)
        assert corr.shape == (n, n)

    def test_pearson_correlation_columns_match(self, mock_returns):
        """Correlation matrix index and columns match returns_df columns."""
        corr = compute_correlation_matrix(mock_returns)
        assert list(corr.columns) == list(mock_returns.columns)
        assert list(corr.index) == list(mock_returns.columns)


class TestConcentration:
    def test_hhi_equal_weights(self):
        """HHI for N equal weights = 1/N."""
        for n in [2, 3, 4, 5]:
            weights = pd.Series([1.0 / n] * n, index=[f"T{i}" for i in range(n)])
            result = compute_hhi(weights)
            assert abs(result - 1.0 / n) < 1e-12, f"Failed for N={n}"

    def test_hhi_single_asset(self):
        """Single asset → HHI = 1.0."""
        w = pd.Series({"A": 1.0})
        assert abs(compute_hhi(w) - 1.0) < 1e-12

    def test_hhi_concentrated_portfolio(self):
        """HHI increases with concentration (80/20 > 50/50)."""
        w_equal = pd.Series({"A": 0.5, "B": 0.5})
        w_concentrated = pd.Series({"A": 0.8, "B": 0.2})
        assert compute_hhi(w_concentrated) > compute_hhi(w_equal)

    def test_effective_n_equal_weights(self):
        """Effective N for N equal weights = N."""
        for n in [2, 3, 4]:
            weights = pd.Series([1.0 / n] * n, index=[f"T{i}" for i in range(n)])
            result = compute_effective_n(weights)
            assert abs(result - float(n)) < 1e-10, f"Failed for N={n}"

    def test_effective_n_single_asset(self):
        """Single asset → Effective N = 1.0."""
        w = pd.Series({"A": 1.0})
        assert abs(compute_effective_n(w) - 1.0) < 1e-12

    def test_diversification_ratio_single_asset(self, mock_returns):
        """DR = 1.0 for single-asset portfolio (no diversification)."""
        w = pd.Series({"AAPL": 1.0})
        dr = compute_diversification_ratio(mock_returns, w)
        assert abs(dr - 1.0) < 1e-10

    def test_diversification_ratio_gt_one(self, mock_returns, mock_weights):
        """DR > 1.0 for a diversified multi-asset portfolio."""
        dr = compute_diversification_ratio(mock_returns, mock_weights)
        assert dr > 1.0


class TestDrawdown:
    def test_drawdown_no_positive(self, mock_portfolio_returns):
        """All drawdown values are <= 0 by construction."""
        dd = compute_drawdown_series(mock_portfolio_returns)
        assert (dd.values <= 1e-12).all()

    def test_drawdown_zero_at_alltime_high(self):
        """Drawdown is 0 at every new all-time high."""
        # Monotonically increasing price → always at a new high → DD = 0
        rising_returns = pd.Series([0.005] * 100)
        dd = compute_drawdown_series(rising_returns)
        np.testing.assert_allclose(dd.values, 0.0, atol=1e-12)

    def test_drawdown_same_length_as_input(self, mock_portfolio_returns):
        """Drawdown series has the same length as portfolio_returns."""
        dd = compute_drawdown_series(mock_portfolio_returns)
        assert len(dd) == len(mock_portfolio_returns)

    def test_max_drawdown_known_path(self):
        """Max drawdown on a known price path: prices drop from 100 to 80.

        Returns: [0, ln(0.8), 0] → prices [1, 0.8, 0.8]
        Running max: [1, 1, 1] → drawdown: [0, -0.2, -0.2]
        Max drawdown = -0.2 exactly.
        """
        returns = pd.Series([0.0, np.log(0.8), 0.0])
        dd = compute_drawdown_series(returns)
        max_dd = compute_max_drawdown(dd)
        assert abs(max_dd - (-0.2)) < 1e-12

    def test_max_drawdown_negative_or_zero(self, mock_portfolio_returns):
        """Max drawdown is <= 0."""
        dd = compute_drawdown_series(mock_portfolio_returns)
        assert compute_max_drawdown(dd) <= 0.0

    def test_max_drawdown_mock_stress_period(self, mock_portfolio_returns):
        """Mock data has a significant drawdown (stress + drift period)."""
        dd = compute_drawdown_series(mock_portfolio_returns)
        max_dd = compute_max_drawdown(dd)
        # Mock data has ~-18% drawdown designed in — should be at least -5%
        assert max_dd < -0.05

    def test_calmar_zero_drawdown_protected(self):
        """Zero max drawdown returns Calmar of 0.0 (not div/0 error)."""
        rising_returns = pd.Series([0.001] * 252)
        dd = compute_drawdown_series(rising_returns)
        max_dd = compute_max_drawdown(dd)  # 0.0 — no drawdown
        result = compute_calmar(rising_returns, max_dd)
        assert result == 0.0

    def test_calmar_positive_cagr_positive_dd(self, mock_portfolio_returns):
        """Calmar ratio has correct sign relative to CAGR."""
        dd = compute_drawdown_series(mock_portfolio_returns)
        max_dd = compute_max_drawdown(dd)
        calmar = compute_calmar(mock_portfolio_returns, max_dd)
        # CAGR sign and calmar sign should match (both positive or both negative)
        cagr = float(np.exp(mock_portfolio_returns.mean() * 252) - 1.0)
        if cagr > 0 and abs(max_dd) > 1e-10:
            assert calmar > 0.0

    def test_ulcer_index_flat(self):
        """Ulcer Index = 0.0 for monotonically rising (no drawdown) series."""
        rising_returns = pd.Series([0.005] * 100)
        dd = compute_drawdown_series(rising_returns)
        ui = compute_ulcer_index(dd)
        assert abs(ui) < 1e-12

    def test_ulcer_index_non_negative(self, mock_portfolio_returns):
        """Ulcer Index is always >= 0."""
        dd = compute_drawdown_series(mock_portfolio_returns)
        assert compute_ulcer_index(dd) >= 0.0

    def test_ulcer_index_positive_for_drawn_down(self, mock_portfolio_returns):
        """Ulcer Index > 0 for data with actual drawdowns."""
        dd = compute_drawdown_series(mock_portfolio_returns)
        assert compute_ulcer_index(dd) > 0.0

    def test_recovery_time_returns_int_or_none(self, mock_portfolio_returns):
        """Recovery time is an int (days recovered) or None (not yet recovered)."""
        dd = compute_drawdown_series(mock_portfolio_returns)
        result = compute_recovery_time(dd)
        assert isinstance(result, (int, type(None)))

    def test_recovery_time_zero_for_no_drawdown(self):
        """Recovery time = 0 when there is no drawdown."""
        rising_returns = pd.Series([0.005] * 100)
        dd = compute_drawdown_series(rising_returns)
        assert compute_recovery_time(dd) == 0


class TestCovariance:
    def test_covariance_positive_definite(self, mock_returns):
        """All eigenvalues of cov_matrix are > 0 after regularization."""
        cov = compute_covariance_matrix(mock_returns)
        eigenvalues = np.linalg.eigvalsh(cov.values)
        assert (eigenvalues > 0).all(), f"Non-positive eigenvalue: {eigenvalues.min()}"

    def test_covariance_symmetric(self, mock_returns):
        """Covariance matrix is symmetric."""
        cov = compute_covariance_matrix(mock_returns)
        np.testing.assert_allclose(cov.values, cov.values.T, atol=1e-10)

    def test_covariance_annualized(self, mock_returns):
        """Diagonal entries equal (annualized individual vol)^2."""
        cov = compute_covariance_matrix(mock_returns)
        for ticker in mock_returns.columns:
            daily_std = mock_returns[ticker].std()
            expected_ann_var = (daily_std * np.sqrt(252)) ** 2
            actual_ann_var = cov.loc[ticker, ticker]
            assert abs(actual_ann_var - expected_ann_var) < 1e-10

    def test_covariance_shape(self, mock_returns):
        """Covariance matrix is square with shape (n_tickers, n_tickers)."""
        cov = compute_covariance_matrix(mock_returns)
        n = len(mock_returns.columns)
        assert cov.shape == (n, n)

    def test_covariance_columns_match(self, mock_returns):
        """Covariance matrix columns and index match returns_df columns."""
        cov = compute_covariance_matrix(mock_returns)
        assert list(cov.columns) == list(mock_returns.columns)
        assert list(cov.index) == list(mock_returns.columns)
