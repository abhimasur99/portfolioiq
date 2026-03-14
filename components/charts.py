"""components/charts.py

All Plotly figure builders for PortfolioIQ.

Every function returns a go.Figure using the "portfolioiq" Plotly template
defined in assets/config.py. Colors are NEVER hardcoded here — always
imported from assets/config.py color constants.

All figures pass use_container_width=True when rendered via st.plotly_chart.
Dashboard quadrant charts have compact explicit height (set by dashboard_quad.py).

Chart inventory:
- cumulative_return_chart: portfolio vs benchmark dual-line chart.
- return_distribution_chart: histogram with VaR line and CVaR shaded region.
- rolling_sharpe_chart: rolling 252-day Sharpe ratio line.
- rolling_beta_chart: rolling 252-day beta line.
- correlation_heatmap: Pearson correlation matrix with annotated cell values.
  Conditional text color for readability. Colorscale: blue(-1) → white(0) → red(1).
- rolling_correlation_chart: rolling 60-day pairwise correlation lines.
- drawdown_chart: underwater equity curve.
- sector_weights_chart: horizontal bar chart by GICS sector.
- garch_volatility_chart: historical vs EWMA vs GARCH conditional vol.
- monte_carlo_fan_chart: p10/p50/p90 fan with shaded region.
- stress_test_chart: grouped bar chart of scenario impacts.
- efficient_frontier_chart: scatter with current portfolio dot, max Sharpe star, CML.
- current_vs_optimal_chart: grouped bar chart, current vs three optimizer weights.

Dependencies: plotly.graph_objects, assets.config.
Assumptions:
- PLOTLY_TEMPLATE_NAME registered in pio.templates before any chart function is called.
  This is guaranteed by importing assets.config before any chart function.

Implemented in: Session 8.
"""

import plotly.graph_objects as go
from assets.config import PLOTLY_TEMPLATE_NAME


def cumulative_return_chart(
    portfolio_returns: "pd.Series",
    benchmark_returns: "pd.Series",
    benchmark_label: str = "Benchmark",
) -> go.Figure:
    """Cumulative return chart: portfolio vs benchmark, both starting at 0.

    Args:
        portfolio_returns: pd.Series of daily portfolio log returns.
        benchmark_returns: pd.Series of daily benchmark log returns.
        benchmark_label: Display label for the benchmark trace.

    Returns:
        go.Figure with two traces: portfolio (solid blue) and benchmark (dashed).
    """
    raise NotImplementedError("Implemented in Session 8.")


def correlation_heatmap(corr_matrix: "pd.DataFrame") -> go.Figure:
    """Pearson correlation heatmap with annotated cell values.

    Colorscale: COLOR_BLUE at -1, white at 0, COLOR_RED at 1.
    Text color per cell: dark on light cells, light on dark cells.
    For 20+ holdings, shows top 10 highest correlations with explanatory note.

    Args:
        corr_matrix: pd.DataFrame — square Pearson correlation matrix.

    Returns:
        go.Figure heatmap.
    """
    raise NotImplementedError("Implemented in Session 8.")


def monte_carlo_fan_chart(
    mc_p10: "np.ndarray",
    mc_p50: "np.ndarray",
    mc_p90: "np.ndarray",
    horizon_years: int,
    initial_value: float = 100.0,
) -> go.Figure:
    """Monte Carlo fan chart: p50 solid line, p10-p90 shaded region.

    Args:
        mc_p10: np.ndarray of p10 portfolio values at each time step.
        mc_p50: np.ndarray of p50 portfolio values at each time step.
        mc_p90: np.ndarray of p90 portfolio values at each time step.
        horizon_years: Simulation horizon in years (for x-axis label).
        initial_value: Starting portfolio value (default 100 for normalization).

    Returns:
        go.Figure with p50 solid trace and p10-p90 fill-between shading.
    """
    raise NotImplementedError("Implemented in Session 8.")


def efficient_frontier_chart(
    frontier_vols: "np.ndarray",
    frontier_returns: "np.ndarray",
    current_vol: float,
    current_return: float,
    max_sharpe_vol: float,
    max_sharpe_return: float,
    min_var_vol: float,
    min_var_return: float,
    risk_parity_vol: float,
    risk_parity_return: float,
    risk_free_rate: float,
) -> go.Figure:
    """Efficient frontier scatter with optimizer portfolio markers and CML.

    Args:
        frontier_vols: Annualized volatilities along the frontier.
        frontier_returns: Annualized returns along the frontier.
        current_vol / current_return: Current portfolio position.
        max_sharpe_vol / max_sharpe_return: Max Sharpe portfolio.
        min_var_vol / min_var_return: Min variance portfolio.
        risk_parity_vol / risk_parity_return: Risk parity portfolio.
        risk_free_rate: Annualized risk-free rate for CML.

    Returns:
        go.Figure with frontier line, three optimizer markers,
        current portfolio dot, and CML.
    """
    raise NotImplementedError("Implemented in Session 8.")
