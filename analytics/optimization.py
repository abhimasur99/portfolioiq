"""analytics/optimization.py

Layer 4 — Prescriptive analytics: portfolio optimization.

Responsibilities:
- Efficient frontier at DEFAULT_FRONTIER_POINTS (50) target return levels.
- Maximum Sharpe portfolio (tangency portfolio) via scipy SLSQP.
- Minimum variance portfolio via scipy SLSQP.
- Risk parity portfolio (equal risk contribution) via scipy SLSQP.
- Capital Market Line (CML) from risk-free rate through tangency point.
- Weight delta table: current weights vs all three optimizer weights.
- Covariance matrix condition check before optimization.

Mathematical spec:
- Portfolio variance: w^T * Sigma * w.
- Efficient frontier: 50 evenly spaced target returns from min-var return
  to max feasible return under constraints. Each solve minimizes variance
  subject to target return equality, sum-to-one, long-only, weight bounds.
- Max Sharpe: minimizes negative Sharpe. Objective: -(Rp - Rf) / sqrt(w^T Sigma w).
- Min variance: minimizes w^T Sigma w directly.
- Risk parity: minimizes sum of squared differences between each asset's
  unnormalized risk contribution (w_i * (Sigma w)_i) and equal target
  (portfolio_var / N). Tolerance 1e-10, max_iter 1000.
- Initial weights: ALWAYS equal-weighted (1/N) for all three optimizers.
- Single covariance matrix shared across all 50 frontier solves.
- Covariance matrix regularized (+1e-6 diagonal) if cond > 1e10.

All quantities annualized:
- mu = daily_mean * 252 (arithmetic annualization).
- cov = daily_cov * 252.
- rf_ann = daily_rf * 252.

Constraints (locked):
- Long-only: all weights >= weight_min.
- Sum-to-one: sum(weights) = 1.
- Weight bounds: [weight_min, weight_max] per asset.

Language note: results described as "identified by the optimizer as
historically optimal under specific assumptions" — never as recommendations.

Dependencies: numpy, scipy.optimize, pandas.
Assumptions:
- Returns and covariance matrix estimated from historical data.
- Optimizer treats these estimates as exact (estimation error documented in Guide).

Implemented in: Session 7.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from assets.config import (
    DEFAULT_FRONTIER_POINTS,
    DEFAULT_COV_COND_THRESH,
    DEFAULT_COV_REGULARIZE,
)

_EPS = 1e-12
_SLSQP_OPTIONS = {"ftol": 1e-10, "maxiter": 1000}


# ── Internal helpers ───────────────────────────────────────────────────────────

def _build_mu_cov(returns_df: pd.DataFrame, tickers: list) -> tuple:
    """Annualized mean return vector and covariance matrix for given tickers.

    Returns:
        (mu, cov) — both numpy arrays in annualized units.
        cov is regularized if condition number > DEFAULT_COV_COND_THRESH.
    """
    sub = returns_df[tickers]
    mu = sub.mean().values * 252.0
    cov = sub.cov().values * 252.0
    if np.linalg.cond(cov) > DEFAULT_COV_COND_THRESH:
        cov += np.eye(cov.shape[0]) * DEFAULT_COV_REGULARIZE
    return mu, cov


def _port_vol(w: np.ndarray, cov: np.ndarray) -> float:
    return float(np.sqrt(max(float(w @ cov @ w), 0.0)))


def _port_return(w: np.ndarray, mu: np.ndarray) -> float:
    return float(w @ mu)


def _sum_to_one_constraint() -> dict:
    return {"type": "eq", "fun": lambda w: float(w.sum()) - 1.0}


def _return_constraint(mu: np.ndarray, target: float) -> dict:
    return {"type": "eq", "fun": lambda w, t=target: float(w @ mu) - t}


# ── Three core optimizers ──────────────────────────────────────────────────────

def _optimize_min_variance(
    mu: np.ndarray,
    cov: np.ndarray,
    n: int,
    weight_min: float,
    weight_max: float,
) -> tuple:
    """Minimize portfolio variance. Returns (weights, success)."""
    w0 = np.ones(n) / n
    bounds = [(weight_min, weight_max)] * n
    result = minimize(
        fun=lambda w: float(w @ cov @ w),
        x0=w0,
        method="SLSQP",
        bounds=bounds,
        constraints=[_sum_to_one_constraint()],
        options=_SLSQP_OPTIONS,
    )
    return result.x, bool(result.success)


def _optimize_max_sharpe(
    mu: np.ndarray,
    cov: np.ndarray,
    rf_ann: float,
    n: int,
    weight_min: float,
    weight_max: float,
) -> tuple:
    """Maximize Sharpe ratio (minimize negative Sharpe). Returns (weights, success)."""
    w0 = np.ones(n) / n
    bounds = [(weight_min, weight_max)] * n

    def neg_sharpe(w: np.ndarray) -> float:
        vol = _port_vol(w, cov)
        if vol < _EPS:
            return 0.0
        return -(_port_return(w, mu) - rf_ann) / vol

    result = minimize(
        fun=neg_sharpe,
        x0=w0,
        method="SLSQP",
        bounds=bounds,
        constraints=[_sum_to_one_constraint()],
        options=_SLSQP_OPTIONS,
    )
    return result.x, bool(result.success)


def _optimize_risk_parity(
    cov: np.ndarray,
    n: int,
    weight_min: float,
    weight_max: float,
) -> tuple:
    """Equal risk contribution portfolio. Returns (weights, success).

    Minimizes sum_i (w_i * (Sigma @ w)_i - portfolio_var / N)^2.
    This unnormalized form avoids division by portfolio volatility and is
    numerically stable when variance is small.
    """
    w0 = np.ones(n) / n
    bounds = [(weight_min, weight_max)] * n

    def objective(w: np.ndarray) -> float:
        sigma_w = cov @ w
        port_var = float(w @ sigma_w)
        target = port_var / n
        risk_contribs = w * sigma_w
        return float(np.sum((risk_contribs - target) ** 2))

    result = minimize(
        fun=objective,
        x0=w0,
        method="SLSQP",
        bounds=bounds,
        constraints=[_sum_to_one_constraint()],
        options=_SLSQP_OPTIONS,
    )
    return result.x, bool(result.success)


# ── Efficient frontier ─────────────────────────────────────────────────────────

def _max_feasible_return(
    mu: np.ndarray,
    n: int,
    weight_min: float,
    weight_max: float,
) -> float:
    """Maximum achievable portfolio return under weight constraints."""
    result = minimize(
        fun=lambda w: -float(w @ mu),
        x0=np.ones(n) / n,
        method="SLSQP",
        bounds=[(weight_min, weight_max)] * n,
        constraints=[_sum_to_one_constraint()],
        options=_SLSQP_OPTIONS,
    )
    return float(-result.fun) if result.success else float(mu.max())


def _compute_frontier(
    mu: np.ndarray,
    cov: np.ndarray,
    min_var_weights: np.ndarray,
    n: int,
    weight_min: float,
    weight_max: float,
    n_points: int = DEFAULT_FRONTIER_POINTS,
) -> tuple:
    """Compute the efficient frontier.

    Upper bound uses the feasible maximum return (constrained LP) rather than
    the theoretical single-asset max, ensuring all n_points targets are feasible.

    Returns:
        (frontier_vols, frontier_returns, frontier_weights) — all lists of length n_points.
        Points that fail to converge are filled with the nearest successful value.
    """
    lower = _port_return(min_var_weights, mu)
    upper = _max_feasible_return(mu, n, weight_min, weight_max)

    # Clamp to avoid degenerate range
    if upper <= lower + _EPS:
        upper = lower + abs(lower) * 0.01 + _EPS

    targets = np.linspace(lower, upper, n_points)
    bounds = [(weight_min, weight_max)] * n

    frontier_vols: list = []
    frontier_returns: list = []
    frontier_weights: list = []

    # Warm-start: begin from min-var weights, step forward through targets
    w0 = min_var_weights.copy()

    for target in targets:
        constraints = [_sum_to_one_constraint(), _return_constraint(mu, target)]
        result = minimize(
            fun=lambda w: float(w @ cov @ w),
            x0=w0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options=_SLSQP_OPTIONS,
        )
        if result.success:
            w = result.x
            w0 = w  # warm-start next solve
            frontier_vols.append(_port_vol(w, cov))
            frontier_returns.append(_port_return(w, mu))
            frontier_weights.append(w.tolist())
        else:
            # Fill with previous point if available, otherwise skip
            if frontier_vols:
                frontier_vols.append(frontier_vols[-1])
                frontier_returns.append(frontier_returns[-1])
                frontier_weights.append(frontier_weights[-1])

    # Pad to exactly n_points if any solves were skipped entirely
    while len(frontier_vols) < n_points and frontier_vols:
        frontier_vols.append(frontier_vols[-1])
        frontier_returns.append(frontier_returns[-1])
        frontier_weights.append(frontier_weights[-1])

    return frontier_vols, frontier_returns, frontier_weights


# ── Weight delta table ─────────────────────────────────────────────────────────

def _build_weight_delta_table(
    tickers: list,
    current_weights: pd.Series,
    max_sharpe_weights: np.ndarray,
    min_var_weights: np.ndarray,
    risk_parity_weights: np.ndarray,
) -> pd.DataFrame:
    """Build a DataFrame showing current vs optimized weights and deltas.

    Columns: current, max_sharpe, max_sharpe_delta, min_var, min_var_delta,
             risk_parity, risk_parity_delta.
    Index: ticker symbols.
    """
    cw = current_weights.reindex(tickers).values
    rows = []
    for i, ticker in enumerate(tickers):
        rows.append({
            "ticker":            ticker,
            "current":           float(cw[i]),
            "max_sharpe":        float(max_sharpe_weights[i]),
            "max_sharpe_delta":  float(max_sharpe_weights[i] - cw[i]),
            "min_var":           float(min_var_weights[i]),
            "min_var_delta":     float(min_var_weights[i] - cw[i]),
            "risk_parity":       float(risk_parity_weights[i]),
            "risk_parity_delta": float(risk_parity_weights[i] - cw[i]),
        })
    return pd.DataFrame(rows).set_index("ticker")


# ── Public API ─────────────────────────────────────────────────────────────────

def compute_all_optimization(
    returns_df: pd.DataFrame,
    weights: pd.Series,
    risk_free_rate: float,
    weight_min: float,
    weight_max: float,
) -> dict:
    """Compute all Layer 4 optimization outputs.

    Args:
        returns_df: pd.DataFrame of per-ticker log returns.
        weights: pd.Series of current portfolio weights (indexed by ticker).
        risk_free_rate: Daily decimal risk-free rate.
        weight_min: Minimum weight per asset (e.g. 0.05).
        weight_max: Maximum weight per asset (e.g. 0.50).

    Returns:
        dict with keys: frontier_vols, frontier_returns, frontier_weights,
        max_sharpe_weights, max_sharpe_return, max_sharpe_vol, max_sharpe_ratio,
        min_var_weights, min_var_return, min_var_vol,
        risk_parity_weights, risk_parity_return, risk_parity_vol,
        cml_slope, weight_delta_table, optimizer_converged (bool).
    """
    tickers = weights.index.tolist()
    n = len(tickers)
    rf_ann = risk_free_rate * 252.0

    mu, cov = _build_mu_cov(returns_df, tickers)

    # ── Min variance (reference point for frontier lower bound) ────────────────
    mv_w, mv_ok = _optimize_min_variance(mu, cov, n, weight_min, weight_max)
    min_var_return = _port_return(mv_w, mu)
    min_var_vol = _port_vol(mv_w, cov)
    min_var_weights = pd.Series(mv_w, index=tickers)

    # ── Max Sharpe ─────────────────────────────────────────────────────────────
    ms_w, ms_ok = _optimize_max_sharpe(mu, cov, rf_ann, n, weight_min, weight_max)
    max_sharpe_return = _port_return(ms_w, mu)
    max_sharpe_vol = _port_vol(ms_w, cov)
    max_sharpe_ratio = (
        (max_sharpe_return - rf_ann) / max_sharpe_vol
        if max_sharpe_vol > _EPS
        else 0.0
    )
    max_sharpe_weights = pd.Series(ms_w, index=tickers)

    # ── Risk parity ────────────────────────────────────────────────────────────
    rp_w, rp_ok = _optimize_risk_parity(cov, n, weight_min, weight_max)
    risk_parity_return = _port_return(rp_w, mu)
    risk_parity_vol = _port_vol(rp_w, cov)
    risk_parity_weights = pd.Series(rp_w, index=tickers)

    # ── Efficient frontier ─────────────────────────────────────────────────────
    frontier_vols, frontier_returns, frontier_weights = _compute_frontier(
        mu=mu,
        cov=cov,
        min_var_weights=mv_w,
        n=n,
        weight_min=weight_min,
        weight_max=weight_max,
        n_points=DEFAULT_FRONTIER_POINTS,
    )

    # ── CML ────────────────────────────────────────────────────────────────────
    cml_slope = max_sharpe_ratio  # Sharpe ratio of tangency portfolio = CML slope

    # ── Weight delta table ─────────────────────────────────────────────────────
    weight_delta_table = _build_weight_delta_table(
        tickers=tickers,
        current_weights=weights,
        max_sharpe_weights=ms_w,
        min_var_weights=mv_w,
        risk_parity_weights=rp_w,
    )

    optimizer_converged = bool(mv_ok and ms_ok and rp_ok)

    return {
        "frontier_vols":        frontier_vols,
        "frontier_returns":     frontier_returns,
        "frontier_weights":     frontier_weights,
        "max_sharpe_weights":   max_sharpe_weights,
        "max_sharpe_return":    float(max_sharpe_return),
        "max_sharpe_vol":       float(max_sharpe_vol),
        "max_sharpe_ratio":     float(max_sharpe_ratio),
        "min_var_weights":      min_var_weights,
        "min_var_return":       float(min_var_return),
        "min_var_vol":          float(min_var_vol),
        "risk_parity_weights":  risk_parity_weights,
        "risk_parity_return":   float(risk_parity_return),
        "risk_parity_vol":      float(risk_parity_vol),
        "cml_slope":            float(cml_slope),
        "weight_delta_table":   weight_delta_table,
        "optimizer_converged":  optimizer_converged,
    }
