"""analytics/risk_outlook.py

Layer 3 — Predictive analytics: risk outlook and forward characterization.

Responsibilities:
- Historical volatility: std(log_returns) * sqrt(252).
- EWMA volatility: sigma^2_t = lambda * sigma^2_{t-1} + (1-lambda) * r^2_{t-1}. Lambda=0.94.
- GARCH(1,1) via arch library:
    - Fitted on percentage log returns (multiply by 100 before fit).
    - disp=False to suppress optimization output.
    - Stationarity check: alpha + beta < 1. EWMA fallback if violated.
    - Minimum 252 observations required; EWMA fallback if shorter.
    - Output sigma divided by 100 when converting back to decimal.
- Historical VaR at 95% and 99%: percentile of realized returns.
- Historical CVaR at 95% and 99%: mean of returns below VaR threshold.
- GARCH-conditional VaR: mu - z * sigma_garch_t.
- VaR scaling to monthly: daily_VaR * sqrt(21). Assumes i.i.d.
- Monte Carlo (GARCH-MC):
    - Pre-generate (steps, paths) innovation matrix — NO Python loops over paths.
    - Running GARCH variance updated each step.
    - Returns (steps+1, paths) portfolio value matrix.
    - Extract p10, p50, p90 at each step.
- Stress tests: beta * scenario_index_return + alpha for each scenario.
- Skewness and excess kurtosis of portfolio returns.

Dependencies: pandas, numpy, scipy.stats, arch.
Assumptions:
- Input portfolio_returns are log returns (not multiplied by 100).
- GARCH is fitted on returns * 100; output sigma divided by 100 for use.
- Monte Carlo initializes from GARCH one-step-ahead conditional volatility.

Implemented in: Sessions 5 and 6.
"""


def compute_all_risk_outlook(
    portfolio_returns: "pd.Series",
    benchmark_returns: "pd.Series",
    weights: "pd.Series",
    performance: dict,
    settings: dict,
) -> dict:
    """Compute all Layer 3 risk outlook metrics.

    Args:
        portfolio_returns: pd.Series of daily portfolio log returns.
        benchmark_returns: pd.Series of daily benchmark log returns.
        weights: pd.Series indexed by ticker.
        performance: dict output from performance.compute_all_performance().
        settings: dict with keys: var_confidence, mc_horizon, mc_paths.

    Returns:
        dict with keys: hist_vol, ewma_vol, garch_vol, garch_model,
        var_95_hist, cvar_95_hist, var_99_hist, cvar_99_hist,
        var_95_garch, cvar_95_garch, var_monthly,
        mc_paths_matrix, mc_p10, mc_p50, mc_p90,
        stress_results, skewness, excess_kurtosis,
        garch_fallback (bool, True if EWMA used instead of GARCH).
    """
    raise NotImplementedError("Implemented in Sessions 5 and 6.")
