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

import numpy as np
import pytest

from assets.config import DEFAULT_FRONTIER_POINTS, DEFAULT_WEIGHT_MIN, DEFAULT_WEIGHT_MAX
from analytics.optimization import compute_all_optimization


# ── Shared fixture ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def opt_result(mock_returns, mock_weights, mock_risk_free_rate):
    """Run compute_all_optimization once for all Session 7 tests."""
    return compute_all_optimization(
        returns_df=mock_returns,
        weights=mock_weights,
        risk_free_rate=mock_risk_free_rate,
        weight_min=DEFAULT_WEIGHT_MIN,
        weight_max=DEFAULT_WEIGHT_MAX,
    )


# ── Max Sharpe ─────────────────────────────────────────────────────────────────

class TestMaxSharpe:
    def test_max_sharpe_weights_sum_to_one(self, opt_result):
        """Max Sharpe weights sum to 1 within floating-point tolerance."""
        w = opt_result["max_sharpe_weights"]
        assert abs(w.sum() - 1.0) < 1e-6, f"Max Sharpe weights sum = {w.sum():.8f}"

    def test_max_sharpe_weights_non_negative(self, opt_result):
        """All Max Sharpe weights are >= 0 (long-only enforced)."""
        w = opt_result["max_sharpe_weights"]
        assert (w >= 0).all(), f"Negative weights found: {w[w < 0].to_dict()}"

    def test_max_sharpe_weights_within_bounds(self, opt_result):
        """All Max Sharpe weights are within [weight_min, weight_max]."""
        w = opt_result["max_sharpe_weights"]
        assert (w >= DEFAULT_WEIGHT_MIN - 1e-6).all(), (
            f"Weights below min: {w[w < DEFAULT_WEIGHT_MIN].to_dict()}"
        )
        assert (w <= DEFAULT_WEIGHT_MAX + 1e-6).all(), (
            f"Weights above max: {w[w > DEFAULT_WEIGHT_MAX].to_dict()}"
        )

    def test_max_sharpe_ratio_is_finite(self, opt_result):
        """Max Sharpe ratio is a finite float (sign depends on market regime)."""
        ratio = opt_result["max_sharpe_ratio"]
        assert isinstance(ratio, float)
        assert np.isfinite(ratio)

    def test_max_sharpe_vol_positive(self, opt_result):
        """Max Sharpe portfolio volatility is strictly positive."""
        assert opt_result["max_sharpe_vol"] > 0.0

    def test_max_sharpe_return_is_float(self, opt_result):
        """Max Sharpe return is a Python float."""
        assert isinstance(opt_result["max_sharpe_return"], float)


# ── Min Variance ───────────────────────────────────────────────────────────────

class TestMinVariance:
    def test_min_var_weights_sum_to_one(self, opt_result):
        """Min variance weights sum to 1 within floating-point tolerance."""
        w = opt_result["min_var_weights"]
        assert abs(w.sum() - 1.0) < 1e-6, f"Min var weights sum = {w.sum():.8f}"

    def test_min_var_weights_non_negative(self, opt_result):
        """All min variance weights are >= 0 (long-only enforced)."""
        w = opt_result["min_var_weights"]
        assert (w >= 0).all(), f"Negative weights found: {w[w < 0].to_dict()}"

    def test_min_var_weights_within_bounds(self, opt_result):
        """All min variance weights are within [weight_min, weight_max]."""
        w = opt_result["min_var_weights"]
        assert (w >= DEFAULT_WEIGHT_MIN - 1e-6).all(), (
            f"Weights below min: {w[w < DEFAULT_WEIGHT_MIN].to_dict()}"
        )
        assert (w <= DEFAULT_WEIGHT_MAX + 1e-6).all(), (
            f"Weights above max: {w[w > DEFAULT_WEIGHT_MAX].to_dict()}"
        )

    def test_min_var_vol_positive(self, opt_result):
        """Min var portfolio volatility is strictly positive."""
        assert opt_result["min_var_vol"] > 0.0

    def test_min_var_vol_le_max_sharpe_vol(self, opt_result):
        """Min var vol <= max Sharpe vol (min var is on the left of the frontier)."""
        assert opt_result["min_var_vol"] <= opt_result["max_sharpe_vol"] + 1e-6


# ── Risk Parity ────────────────────────────────────────────────────────────────

class TestRiskParity:
    def test_risk_parity_weights_sum_to_one(self, opt_result):
        """Risk parity weights sum to 1 within floating-point tolerance."""
        w = opt_result["risk_parity_weights"]
        assert abs(w.sum() - 1.0) < 1e-6, f"Risk parity weights sum = {w.sum():.8f}"

    def test_risk_parity_weights_non_negative(self, opt_result):
        """All risk parity weights are >= 0 (long-only enforced)."""
        w = opt_result["risk_parity_weights"]
        assert (w >= 0).all(), f"Negative weights found: {w[w < 0].to_dict()}"

    def test_risk_parity_weights_within_bounds(self, opt_result):
        """All risk parity weights are within [weight_min, weight_max]."""
        w = opt_result["risk_parity_weights"]
        assert (w >= DEFAULT_WEIGHT_MIN - 1e-6).all(), (
            f"Weights below min: {w[w < DEFAULT_WEIGHT_MIN].to_dict()}"
        )
        assert (w <= DEFAULT_WEIGHT_MAX + 1e-6).all(), (
            f"Weights above max: {w[w > DEFAULT_WEIGHT_MAX].to_dict()}"
        )

    def test_risk_parity_vol_positive(self, opt_result):
        """Risk parity portfolio volatility is strictly positive."""
        assert opt_result["risk_parity_vol"] > 0.0


# ── Efficient Frontier ─────────────────────────────────────────────────────────

class TestEfficientFrontier:
    def test_frontier_length(self, opt_result):
        """Efficient frontier has exactly DEFAULT_FRONTIER_POINTS (50) points."""
        assert len(opt_result["frontier_returns"]) == DEFAULT_FRONTIER_POINTS, (
            f"Expected {DEFAULT_FRONTIER_POINTS} frontier points, "
            f"got {len(opt_result['frontier_returns'])}"
        )
        assert len(opt_result["frontier_vols"]) == DEFAULT_FRONTIER_POINTS
        assert len(opt_result["frontier_weights"]) == DEFAULT_FRONTIER_POINTS

    def test_frontier_returns_increasing(self, opt_result):
        """Frontier returns are monotonically non-decreasing."""
        returns = opt_result["frontier_returns"]
        for i in range(1, len(returns)):
            assert returns[i] >= returns[i - 1] - 1e-8, (
                f"Frontier returns not increasing at index {i}: "
                f"{returns[i-1]:.6f} -> {returns[i]:.6f}"
            )

    def test_frontier_vols_u_shaped(self, opt_result):
        """Minimum variance is at the left end: frontier_vols[0] is the minimum."""
        vols = opt_result["frontier_vols"]
        min_vol = min(vols)
        # The min-var portfolio anchors the left end; its vol should be the smallest
        assert vols[0] <= min_vol + 1e-6, (
            f"Minimum vol {min_vol:.6f} not at left end (got {vols[0]:.6f})"
        )

    def test_frontier_vols_all_positive(self, opt_result):
        """All frontier portfolio volatilities are strictly positive."""
        for i, vol in enumerate(opt_result["frontier_vols"]):
            assert vol > 0.0, f"Non-positive vol at frontier index {i}: {vol}"

    def test_frontier_weights_sum_to_one(self, opt_result):
        """Each frontier portfolio's weights sum to 1."""
        for i, w in enumerate(opt_result["frontier_weights"]):
            w_arr = np.array(w)
            assert abs(w_arr.sum() - 1.0) < 1e-5, (
                f"Frontier point {i} weights sum = {w_arr.sum():.8f}"
            )


# ── Output structure ───────────────────────────────────────────────────────────

class TestOutputStructure:
    def test_all_keys_present(self, opt_result):
        """compute_all_optimization returns all required keys."""
        required = {
            "frontier_vols", "frontier_returns", "frontier_weights",
            "max_sharpe_weights", "max_sharpe_return", "max_sharpe_vol", "max_sharpe_ratio",
            "min_var_weights", "min_var_return", "min_var_vol",
            "risk_parity_weights", "risk_parity_return", "risk_parity_vol",
            "cml_slope", "weight_delta_table", "optimizer_converged",
        }
        assert required.issubset(opt_result.keys()), (
            f"Missing keys: {required - opt_result.keys()}"
        )

    def test_optimizer_converged_is_bool(self, opt_result):
        """optimizer_converged is a Python bool."""
        assert isinstance(opt_result["optimizer_converged"], bool)

    def test_optimizer_converged_true(self, opt_result):
        """All three optimizers converge on mock data."""
        assert opt_result["optimizer_converged"] is True

    def test_weight_delta_table_shape(self, opt_result, mock_weights):
        """weight_delta_table has one row per ticker and expected columns."""
        table = opt_result["weight_delta_table"]
        assert len(table) == len(mock_weights)
        expected_cols = {
            "current", "max_sharpe", "max_sharpe_delta",
            "min_var", "min_var_delta", "risk_parity", "risk_parity_delta",
        }
        assert expected_cols.issubset(set(table.columns))

    def test_cml_slope_equals_max_sharpe_ratio(self, opt_result):
        """CML slope equals the Max Sharpe ratio (both measure tangency portfolio Sharpe)."""
        assert abs(opt_result["cml_slope"] - opt_result["max_sharpe_ratio"]) < 1e-10
