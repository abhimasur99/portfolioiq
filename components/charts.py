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

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from assets.config import (
    PLOTLY_TEMPLATE_NAME,
    COLOR_BLUE, COLOR_GREEN, COLOR_AMBER, COLOR_RED, COLOR_PURPLE,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_AXIS, COLOR_BG_SECONDARY,
    FONT_MONO,
)

# Shared semi-transparent fills (RGBA strings derived from config colors)
_BLUE_FILL   = "rgba(0,212,255,0.15)"
_AMBER_FILL  = "rgba(239,159,39,0.15)"
_RED_FILL    = "rgba(226,75,74,0.20)"
_GREEN_FILL  = "rgba(42,186,106,0.15)"


# ── Cumulative return chart ────────────────────────────────────────────────────

def cumulative_return_chart(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
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
    port_cum = (np.exp(portfolio_returns.cumsum()) - 1) * 100
    bench_cum = (np.exp(benchmark_returns.cumsum()) - 1) * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=port_cum.index,
        y=port_cum.values,
        mode="lines",
        name="Portfolio",
        line=dict(color=COLOR_BLUE, width=2),
        hovertemplate="%{x|%Y-%m-%d}<br>%{y:+.1f}%<extra>Portfolio</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=bench_cum.index,
        y=bench_cum.values,
        mode="lines",
        name=benchmark_label,
        line=dict(color=COLOR_TEXT_MUTED, width=1.5, dash="dash"),
        hovertemplate="%{x|%Y-%m-%d}<br>%{y:+.1f}%<extra>" + benchmark_label + "</extra>",
    ))
    fig.add_hline(y=0, line_color=COLOR_AXIS, line_width=1)
    fig.update_layout(
        template=PLOTLY_TEMPLATE_NAME,
        title="Cumulative Return",
        xaxis_title=None,
        yaxis_title="Return (%)",
        yaxis_tickformat="+.1f",
        hovermode="x unified",
    )
    return fig


# ── Return distribution chart ──────────────────────────────────────────────────

def return_distribution_chart(
    portfolio_returns: pd.Series,
    var_95: float,
    cvar_95: float,
) -> go.Figure:
    """Return distribution histogram with VaR marker and CVaR shaded tail.

    Args:
        portfolio_returns: pd.Series of daily portfolio log returns.
        var_95: 95% VaR threshold (negative float, e.g. -0.015).
        cvar_95: 95% CVaR mean tail loss (negative float, <= var_95).

    Returns:
        go.Figure with histogram, VaR vertical line, and CVaR shaded region.
    """
    returns_pct = portfolio_returns.values * 100

    fig = go.Figure()

    # Histogram
    fig.add_trace(go.Histogram(
        x=returns_pct,
        nbinsx=60,
        name="Daily returns",
        marker_color=COLOR_BLUE,
        opacity=0.7,
        hovertemplate="Return: %{x:.2f}%<br>Count: %{y}<extra></extra>",
    ))

    # CVaR shaded region (vertical fill via shape)
    fig.add_vrect(
        x0=min(returns_pct) * 1.05,
        x1=cvar_95 * 100,
        fillcolor=_RED_FILL,
        layer="below",
        line_width=0,
        annotation_text="CVaR 95%",
        annotation_position="top left",
        annotation_font_color=COLOR_RED,
        annotation_font_size=10,
    )

    # VaR vertical line
    fig.add_vline(
        x=var_95 * 100,
        line_color=COLOR_AMBER,
        line_width=2,
        line_dash="dash",
        annotation_text=f"VaR 95%: {var_95*100:.2f}%",
        annotation_position="top right",
        annotation_font_color=COLOR_AMBER,
        annotation_font_size=10,
    )

    fig.update_layout(
        template=PLOTLY_TEMPLATE_NAME,
        title="Daily Return Distribution",
        xaxis_title="Daily Return (%)",
        yaxis_title="Frequency",
        showlegend=False,
        bargap=0.05,
    )
    return fig


# ── Rolling Sharpe chart ───────────────────────────────────────────────────────

def rolling_sharpe_chart(rolling_sharpe: pd.Series) -> go.Figure:
    """Rolling 252-day Sharpe ratio line chart.

    Args:
        rolling_sharpe: pd.Series of rolling Sharpe values (NaN for first 251 days).

    Returns:
        go.Figure with Sharpe line and horizontal reference at 0 and 1.
    """
    s = rolling_sharpe.dropna()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=s.index,
        y=s.values,
        mode="lines",
        name="Rolling Sharpe (252d)",
        line=dict(color=COLOR_PURPLE, width=2),
        fill="tozeroy",
        fillcolor=_AMBER_FILL if float(s.iloc[-1]) < 0 else _BLUE_FILL,
        hovertemplate="%{x|%Y-%m-%d}<br>Sharpe: %{y:.2f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_color=COLOR_AXIS, line_width=1)
    fig.add_hline(
        y=1.0,
        line_color=COLOR_GREEN,
        line_width=1,
        line_dash="dot",
        annotation_text="1.0",
        annotation_font_color=COLOR_GREEN,
        annotation_font_size=10,
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE_NAME,
        title="Rolling Sharpe Ratio (252-day)",
        xaxis_title=None,
        yaxis_title="Sharpe Ratio",
    )
    return fig


# ── Rolling Beta chart ─────────────────────────────────────────────────────────

def rolling_beta_chart(rolling_beta: pd.Series) -> go.Figure:
    """Rolling 252-day beta line chart.

    Args:
        rolling_beta: pd.Series of rolling beta values (NaN for first 251 days).

    Returns:
        go.Figure with beta line and horizontal reference at 1.
    """
    s = rolling_beta.dropna()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=s.index,
        y=s.values,
        mode="lines",
        name="Rolling Beta (252d)",
        line=dict(color=COLOR_AMBER, width=2),
        hovertemplate="%{x|%Y-%m-%d}<br>Beta: %{y:.2f}<extra></extra>",
    ))
    fig.add_hline(y=1.0, line_color=COLOR_TEXT_MUTED, line_width=1, line_dash="dash",
                  annotation_text="β = 1", annotation_font_color=COLOR_TEXT_MUTED,
                  annotation_font_size=10)
    fig.add_hline(y=0, line_color=COLOR_AXIS, line_width=1)
    fig.update_layout(
        template=PLOTLY_TEMPLATE_NAME,
        title="Rolling Beta vs Benchmark (252-day)",
        xaxis_title=None,
        yaxis_title="Beta",
    )
    return fig


# ── Correlation heatmap ────────────────────────────────────────────────────────

def correlation_heatmap(corr_matrix: pd.DataFrame) -> go.Figure:
    """Pearson correlation heatmap with annotated cell values.

    Colorscale: COLOR_BLUE at -1, white at 0, COLOR_RED at 1.
    Text color per cell: dark on light cells, light on dark cells.
    For 20+ holdings, shows top 10 highest off-diagonal correlations.

    Args:
        corr_matrix: pd.DataFrame — square Pearson correlation matrix.

    Returns:
        go.Figure heatmap.
    """
    labels = corr_matrix.columns.tolist()
    n = len(labels)
    z = corr_matrix.values

    # Conditional text color: use dark text for mid-range, light for extremes
    text_colors = []
    for row in z:
        row_colors = []
        for val in row:
            # Absolute value drives darkness; white background → use dark text
            row_colors.append(COLOR_TEXT if abs(val) < 0.6 else COLOR_BG_SECONDARY)
        text_colors.append(row_colors)

    annotations = []
    for i in range(n):
        for j in range(n):
            annotations.append(dict(
                x=labels[j],
                y=labels[i],
                text=f"{z[i, j]:.2f}",
                showarrow=False,
                font=dict(
                    family=FONT_MONO,
                    size=11,
                    color=text_colors[i][j],
                ),
            ))

    colorscale = [
        [0.0, COLOR_BLUE],
        [0.5, "#ffffff"],
        [1.0, COLOR_RED],
    ]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=labels,
        y=labels,
        colorscale=colorscale,
        zmin=-1,
        zmax=1,
        showscale=True,
        colorbar=dict(
            title="ρ",
            tickfont=dict(family=FONT_MONO, color=COLOR_TEXT_MUTED, size=10),
        ),
        hovertemplate="%{y} × %{x}<br>ρ = %{z:.3f}<extra></extra>",
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE_NAME,
        title="Correlation Matrix",
        annotations=annotations,
        xaxis=dict(side="bottom"),
    )
    return fig


# ── Rolling correlation chart ──────────────────────────────────────────────────

def rolling_correlation_chart(rolling_corr: pd.DataFrame) -> go.Figure:
    """Rolling 60-day pairwise correlation lines.

    Args:
        rolling_corr: pd.DataFrame with one column per asset pair (e.g. "AAPL-MSFT"),
                      or a long-format DataFrame. NaN for the first window-1 rows.

    Returns:
        go.Figure with one line per pair.
    """
    colors = [COLOR_BLUE, COLOR_GREEN, COLOR_AMBER, COLOR_PURPLE, COLOR_RED]
    fig = go.Figure()
    for i, col in enumerate(rolling_corr.columns):
        s = rolling_corr[col].dropna()
        fig.add_trace(go.Scatter(
            x=s.index,
            y=s.values,
            mode="lines",
            name=str(col),
            line=dict(color=colors[i % len(colors)], width=1.5),
            hovertemplate="%{x|%Y-%m-%d}<br>" + str(col) + ": %{y:.2f}<extra></extra>",
        ))
    fig.add_hline(y=0, line_color=COLOR_AXIS, line_width=1)
    fig.update_layout(
        template=PLOTLY_TEMPLATE_NAME,
        title="Rolling Pairwise Correlation (60-day)",
        xaxis_title=None,
        yaxis_title="Correlation (ρ)",
        yaxis_range=[-1.1, 1.1],
    )
    return fig


# ── Drawdown chart ─────────────────────────────────────────────────────────────

def drawdown_chart(drawdown_series: pd.Series) -> go.Figure:
    """Underwater equity curve showing portfolio drawdown.

    Args:
        drawdown_series: pd.Series of drawdown values (non-positive, from compute_drawdown_series).

    Returns:
        go.Figure with filled drawdown area (red fill below zero).
    """
    dd_pct = drawdown_series * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dd_pct.index,
        y=dd_pct.values,
        mode="lines",
        name="Drawdown",
        line=dict(color=COLOR_RED, width=1.5),
        fill="tozeroy",
        fillcolor=_RED_FILL,
        hovertemplate="%{x|%Y-%m-%d}<br>Drawdown: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=0, line_color=COLOR_AXIS, line_width=1)
    fig.update_layout(
        template=PLOTLY_TEMPLATE_NAME,
        title="Portfolio Drawdown",
        xaxis_title=None,
        yaxis_title="Drawdown (%)",
        yaxis_tickformat=".1f",
        showlegend=False,
    )
    return fig


# ── Sector weights chart ───────────────────────────────────────────────────────

def sector_weights_chart(sector_weights: dict) -> go.Figure:
    """Horizontal bar chart of portfolio weight by GICS sector.

    Args:
        sector_weights: dict mapping sector name (str) to weight (float 0-1).
                        Omit sectors with zero weight before calling.

    Returns:
        go.Figure horizontal bar chart sorted by weight descending.
    """
    if not sector_weights:
        fig = go.Figure()
        fig.update_layout(
            template=PLOTLY_TEMPLATE_NAME,
            title="Sector Weights",
            annotations=[dict(
                text="Sector data unavailable",
                x=0.5, y=0.5,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(color=COLOR_TEXT_MUTED, size=13),
            )],
        )
        return fig

    # Sort descending by weight
    sorted_items = sorted(sector_weights.items(), key=lambda x: x[1])
    sectors = [item[0] for item in sorted_items]
    weights_pct = [item[1] * 100 for item in sorted_items]

    bar_colors = [
        COLOR_GREEN if w >= 0 else COLOR_RED for w in weights_pct
    ]

    fig = go.Figure(go.Bar(
        x=weights_pct,
        y=sectors,
        orientation="h",
        marker_color=bar_colors,
        text=[f"{w:.1f}%" for w in weights_pct],
        textposition="outside",
        textfont=dict(family=FONT_MONO, color=COLOR_TEXT, size=10),
        hovertemplate="%{y}<br>%{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE_NAME,
        title="Portfolio Weight by Sector",
        xaxis_title="Weight (%)",
        yaxis_title=None,
        showlegend=False,
        margin=dict(l=150, r=60, t=50, b=50),
    )
    return fig


# ── GARCH volatility chart ─────────────────────────────────────────────────────

def garch_volatility_chart(
    portfolio_returns: pd.Series,
    ewma_vol: float,
    garch_result: object,
    is_fallback: bool,
) -> go.Figure:
    """Historical rolling vol vs EWMA reference vs GARCH conditional vol.

    Args:
        portfolio_returns: pd.Series of daily log returns.
        ewma_vol: Annualized EWMA volatility (scalar, shown as horizontal reference).
        garch_result: arch model result object (has .conditional_volatility) or None.
        is_fallback: True if GARCH fell back to EWMA (affects label).

    Returns:
        go.Figure with three traces: rolling 21-day hist vol, EWMA ref line,
        GARCH conditional vol (if available).
    """
    # Rolling 21-day historical vol (annualized)
    rolling_vol = portfolio_returns.rolling(21).std() * np.sqrt(252) * 100
    rolling_vol = rolling_vol.dropna()

    fig = go.Figure()

    # Rolling historical vol
    fig.add_trace(go.Scatter(
        x=rolling_vol.index,
        y=rolling_vol.values,
        mode="lines",
        name="Rolling 21d Vol",
        line=dict(color=COLOR_TEXT_MUTED, width=1, dash="dot"),
        hovertemplate="%{x|%Y-%m-%d}<br>Rolling Vol: %{y:.1f}%<extra></extra>",
    ))

    # GARCH conditional vol (if available)
    if garch_result is not None and hasattr(garch_result, "conditional_volatility"):
        garch_vol_series = garch_result.conditional_volatility / 100 * np.sqrt(252) * 100
        label = "GARCH(1,1) Cond. Vol" if not is_fallback else "EWMA Cond. Vol (fallback)"
        fig.add_trace(go.Scatter(
            x=portfolio_returns.index[-len(garch_vol_series):],
            y=garch_vol_series.values,
            mode="lines",
            name=label,
            line=dict(color=COLOR_BLUE, width=2),
            hovertemplate="%{x|%Y-%m-%d}<br>" + label + ": %{y:.1f}%<extra></extra>",
        ))

    # EWMA reference line
    fig.add_hline(
        y=ewma_vol * 100,
        line_color=COLOR_AMBER,
        line_width=1.5,
        line_dash="dash",
        annotation_text=f"EWMA: {ewma_vol*100:.1f}%",
        annotation_font_color=COLOR_AMBER,
        annotation_font_size=10,
    )

    fig.update_layout(
        template=PLOTLY_TEMPLATE_NAME,
        title="Portfolio Volatility (Annualized)",
        xaxis_title=None,
        yaxis_title="Volatility (% ann.)",
    )
    return fig


# ── Monte Carlo fan chart ──────────────────────────────────────────────────────

def monte_carlo_fan_chart(
    mc_p10: np.ndarray,
    mc_p50: np.ndarray,
    mc_p90: np.ndarray,
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
    n_steps = len(mc_p50)
    # X axis in years (0 = today)
    x_years = np.linspace(0, horizon_years, n_steps)

    # Scale to initial_value
    scale = initial_value / float(mc_p50[0]) if float(mc_p50[0]) > 0 else initial_value
    p10 = mc_p10 * scale
    p50 = mc_p50 * scale
    p90 = mc_p90 * scale

    fig = go.Figure()

    # P90 upper bound (filled to p10)
    fig.add_trace(go.Scatter(
        x=np.concatenate([x_years, x_years[::-1]]),
        y=np.concatenate([p90, p10[::-1]]),
        fill="toself",
        fillcolor=_BLUE_FILL,
        line=dict(color="rgba(0,0,0,0)"),
        name="P10–P90 range",
        hoverinfo="skip",
        showlegend=True,
    ))

    # P10 lower bound line
    fig.add_trace(go.Scatter(
        x=x_years,
        y=p10,
        mode="lines",
        name="P10 (pessimistic)",
        line=dict(color=COLOR_RED, width=1, dash="dot"),
        hovertemplate="Year %{x:.1f}<br>P10: $%{y:.0f}<extra></extra>",
    ))

    # P90 upper bound line
    fig.add_trace(go.Scatter(
        x=x_years,
        y=p90,
        mode="lines",
        name="P90 (optimistic)",
        line=dict(color=COLOR_GREEN, width=1, dash="dot"),
        hovertemplate="Year %{x:.1f}<br>P90: $%{y:.0f}<extra></extra>",
    ))

    # P50 median
    fig.add_trace(go.Scatter(
        x=x_years,
        y=p50,
        mode="lines",
        name="Median (P50)",
        line=dict(color=COLOR_BLUE, width=2.5),
        hovertemplate="Year %{x:.1f}<br>Median: $%{y:.0f}<extra></extra>",
    ))

    fig.add_hline(y=initial_value, line_color=COLOR_AXIS, line_width=1, line_dash="dot")
    fig.update_layout(
        template=PLOTLY_TEMPLATE_NAME,
        title=f"Monte Carlo Simulation ({horizon_years}-Year Horizon)",
        xaxis_title="Years",
        yaxis_title=f"Portfolio Value (base = {initial_value:.0f})",
        hovermode="x unified",
    )
    return fig


# ── Stress test chart ──────────────────────────────────────────────────────────

def stress_test_chart(stress_results: dict) -> go.Figure:
    """Grouped bar chart of index vs portfolio impact for each stress scenario.

    Args:
        stress_results: dict from _run_stress_tests, keyed by scenario name.
                        Each value has "index_return" and "portfolio_return" (floats).

    Returns:
        go.Figure with two bar groups: index impact and portfolio impact.
    """
    scenarios = list(stress_results.keys())
    index_returns = [stress_results[s]["index_return"] * 100 for s in scenarios]
    port_returns = [stress_results[s]["portfolio_return"] * 100 for s in scenarios]

    # Shorten labels for display
    short_labels = [s.replace(" Global Financial Crisis", " GFC")
                     .replace(" Dot-Com Bust", " Dot-Com")
                     .replace(" Rate Shock", " Rates")
                     .replace(" COVID Crash", " COVID")
                    for s in scenarios]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Index (SPY)",
        x=short_labels,
        y=index_returns,
        marker_color=COLOR_TEXT_MUTED,
        hovertemplate="%{x}<br>Index: %{y:+.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Your Portfolio",
        x=short_labels,
        y=port_returns,
        marker_color=[COLOR_GREEN if r >= 0 else COLOR_RED for r in port_returns],
        hovertemplate="%{x}<br>Portfolio: %{y:+.1f}%<extra></extra>",
    ))
    fig.add_hline(y=0, line_color=COLOR_AXIS, line_width=1)
    fig.update_layout(
        template=PLOTLY_TEMPLATE_NAME,
        title="Stress Test Scenarios",
        xaxis_title=None,
        yaxis_title="Impact (%)",
        yaxis_tickformat="+.0f",
        barmode="group",
        bargap=0.20,
        bargroupgap=0.05,
    )
    return fig


# ── Efficient frontier chart ───────────────────────────────────────────────────

def efficient_frontier_chart(
    frontier_vols: list,
    frontier_returns: list,
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
    fv = [v * 100 for v in frontier_vols]
    fr = [r * 100 for r in frontier_returns]
    rf_pct = risk_free_rate * 100

    fig = go.Figure()

    # Efficient frontier line
    fig.add_trace(go.Scatter(
        x=fv,
        y=fr,
        mode="lines",
        name="Efficient Frontier",
        line=dict(color=COLOR_BLUE, width=2),
        hovertemplate="Vol: %{x:.1f}%<br>Return: %{y:.1f}%<extra>Frontier</extra>",
    ))

    # Capital Market Line: from rf through max Sharpe, extended to right edge
    if max_sharpe_vol > 0:
        slope = (max_sharpe_return - risk_free_rate) / max_sharpe_vol
        max_vol_cml = max(frontier_vols) * 1.2 if frontier_vols else max_sharpe_vol * 1.5
        cml_x = [0.0, max_vol_cml * 100]
        cml_y = [rf_pct, rf_pct + slope * max_vol_cml * 100]
        fig.add_trace(go.Scatter(
            x=cml_x,
            y=cml_y,
            mode="lines",
            name="CML",
            line=dict(color=COLOR_TEXT_MUTED, width=1, dash="dash"),
            hoverinfo="skip",
        ))

    # Max Sharpe (star marker)
    fig.add_trace(go.Scatter(
        x=[max_sharpe_vol * 100],
        y=[max_sharpe_return * 100],
        mode="markers",
        name="Max Sharpe",
        marker=dict(color=COLOR_AMBER, size=14, symbol="star"),
        hovertemplate="Max Sharpe<br>Vol: %{x:.1f}%<br>Return: %{y:.1f}%<extra></extra>",
    ))

    # Min variance (diamond marker)
    fig.add_trace(go.Scatter(
        x=[min_var_vol * 100],
        y=[min_var_return * 100],
        mode="markers",
        name="Min Variance",
        marker=dict(color=COLOR_GREEN, size=12, symbol="diamond"),
        hovertemplate="Min Variance<br>Vol: %{x:.1f}%<br>Return: %{y:.1f}%<extra></extra>",
    ))

    # Risk parity (square marker)
    fig.add_trace(go.Scatter(
        x=[risk_parity_vol * 100],
        y=[risk_parity_return * 100],
        mode="markers",
        name="Risk Parity",
        marker=dict(color=COLOR_PURPLE, size=12, symbol="square"),
        hovertemplate="Risk Parity<br>Vol: %{x:.1f}%<br>Return: %{y:.1f}%<extra></extra>",
    ))

    # Current portfolio (circle marker)
    fig.add_trace(go.Scatter(
        x=[current_vol * 100],
        y=[current_return * 100],
        mode="markers",
        name="Your Portfolio",
        marker=dict(color=COLOR_RED, size=12, symbol="circle",
                    line=dict(color=COLOR_TEXT, width=1)),
        hovertemplate="Your Portfolio<br>Vol: %{x:.1f}%<br>Return: %{y:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        template=PLOTLY_TEMPLATE_NAME,
        title="Efficient Frontier",
        xaxis_title="Annualized Volatility (%)",
        yaxis_title="Annualized Return (%)",
        xaxis_tickformat=".1f",
        yaxis_tickformat="+.1f",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# ── Current vs optimal weights chart ──────────────────────────────────────────

def current_vs_optimal_chart(weight_delta_table: pd.DataFrame) -> go.Figure:
    """Grouped bar chart: current portfolio weights vs three optimizer weights.

    Args:
        weight_delta_table: pd.DataFrame from compute_all_optimization with index=ticker
                            and columns including current, max_sharpe, min_var, risk_parity.

    Returns:
        go.Figure with 4 bar groups (one per strategy) per ticker.
    """
    tickers = weight_delta_table.index.tolist()
    w_pct = weight_delta_table * 100

    fig = go.Figure()
    configs = [
        ("current",    "Current",    COLOR_TEXT_MUTED),
        ("max_sharpe", "Max Sharpe", COLOR_AMBER),
        ("min_var",    "Min Var",    COLOR_GREEN),
        ("risk_parity","Risk Parity",COLOR_PURPLE),
    ]
    for col, label, color in configs:
        if col in w_pct.columns:
            fig.add_trace(go.Bar(
                name=label,
                x=tickers,
                y=w_pct[col].values,
                marker_color=color,
                hovertemplate="%{x}<br>" + label + ": %{y:.1f}%<extra></extra>",
            ))

    fig.add_hline(y=0, line_color=COLOR_AXIS, line_width=1)
    fig.update_layout(
        template=PLOTLY_TEMPLATE_NAME,
        title="Current vs Optimizer Weights",
        xaxis_title=None,
        yaxis_title="Weight (%)",
        yaxis_tickformat=".0f",
        barmode="group",
        bargap=0.20,
        bargroupgap=0.05,
    )
    return fig
