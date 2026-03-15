"""pages/dashboard.py

Screen 2 — Main Dashboard.

Responsibilities:
- Holdings strip (ticker, weight, current price).
- Health bar with six status indicators.
- Ticker tape with live prices across the top (CSS animation).
- Four quadrants in a 2x2 grid, each via dashboard_quad.py component:
    Q1 -- Performance (Descriptive)
    Q2 -- Risk Factors (Diagnostic)
    Q3 -- Risk Outlook (Predictive)
    Q4 -- Optimization (Prescriptive)
- Each quadrant: primary chart, 3-4 KPIs, Explain Numbers button,
  More Details button, one contextual flag.
- More Details buttons route to pages/details_q{n}.py.

Does NOT recompute analytics -- reads from st.session_state[SK_ANALYTICS].

Implemented in: Session 10.
"""

import numpy as np
import pandas as pd
import streamlit as st

from assets.config import (
    COLOR_BLUE, COLOR_GREEN, COLOR_AMBER, COLOR_RED, COLOR_TEXT_MUTED,
    SK_ANALYTICS, SK_BENCH_RETURNS, SK_BENCHMARK, SK_PERFORMANCE,
    SK_PORTFOLIO_LOADED, SK_PORTFOLIO_NAME, SK_PORT_RETURNS,
    SK_PRICE_DATA, SK_RISK_FACTORS, SK_RISK_OUTLOOK,
    SK_OPTIMIZATION, SK_MARKET_SIGNALS, SK_TICKERS, SK_WEIGHTS,
    SK_RISK_FREE_RATE,
)

# Routing key set by render_quadrant More Details button
_SK_DETAILS = "_dashboard_details"

# Color palette for holdings segments (cycles if > 8 tickers)
_HOLDING_COLORS = [
    "#00d4ff",  # blue
    "#2aba6a",  # green
    "#ef9f27",  # amber
    "#a855f7",  # purple
    "#e24b4a",  # red
    "#06b6d4",  # teal
    "#f97316",  # orange
    "#ec4899",  # pink
]


# ── Guard ──────────────────────────────────────────────────────────────────────

def _check_loaded() -> bool:
    if not st.session_state.get(SK_PORTFOLIO_LOADED, False):
        st.warning("No portfolio loaded. Please go to **INPUT** and analyse your portfolio first.")
        if st.button("Go to Input →"):
            st.session_state["_nav_pending"] = "INPUT"
            st.rerun()
        return False
    return True


# ── Helpers ────────────────────────────────────────────────────────────────────

def _pct(val, decimals: int = 1, sign: bool = True) -> str:
    if val is None:
        return "n/a"
    try:
        fmt = f"{'+' if sign else ''}.{decimals}f"
        return f"{float(val)*100:{fmt}}%"
    except (TypeError, ValueError):
        return "n/a"


def _fmt(val, decimals: int = 2) -> str:
    if val is None:
        return "n/a"
    try:
        return f"{float(val):.{decimals}f}"
    except (TypeError, ValueError):
        return "n/a"


def _status_color(status: str) -> str:
    return {"green": COLOR_GREEN, "amber": COLOR_AMBER, "red": COLOR_RED}.get(
        status, COLOR_TEXT_MUTED
    )


# ── Ticker tape ────────────────────────────────────────────────────────────────

def _render_ticker_tape() -> None:
    """Render a CSS-animated scrolling ticker tape with latest prices."""
    prices: pd.DataFrame = st.session_state.get(SK_PRICE_DATA, pd.DataFrame())
    tickers: list = st.session_state.get(SK_TICKERS, [])
    benchmark: str = st.session_state.get(SK_BENCHMARK, "")

    if prices.empty:
        return

    all_tickers = list(dict.fromkeys(tickers + ([benchmark] if benchmark else [])))
    segments = []
    for ticker in all_tickers:
        if ticker not in prices.columns:
            continue
        col = prices[ticker].dropna()
        if len(col) < 2:
            continue
        latest = col.iloc[-1]
        prev   = col.iloc[-2]
        chg    = (latest - prev) / prev * 100 if prev > 0 else 0.0
        arrow  = "▲" if chg >= 0 else "▼"
        color  = COLOR_GREEN if chg >= 0 else COLOR_RED
        segments.append(
            f'<span style="margin:0 18px;">'
            f'<b>{ticker}</b>&nbsp;${latest:.2f}&nbsp;'
            f'<span style="color:{color};">{arrow}&nbsp;{chg:+.2f}%</span>'
            f'</span>'
        )

    if not segments:
        return

    tape_inner = " &nbsp;|&nbsp; ".join(segments)
    tape_html = (
        '<div class="ticker-tape-container">'
        '<div class="ticker-tape-track">'
        + tape_inner * 2  # repeat once for seamless CSS loop
        + "</div></div>"
    )
    st.markdown(tape_html, unsafe_allow_html=True)


# ── Holdings strip ─────────────────────────────────────────────────────────────

def _render_holdings_strip() -> None:
    """Render a full-width stacked segmented bar showing each ticker's portfolio weight."""
    tickers: list      = st.session_state.get(SK_TICKERS, [])
    weights: pd.Series = st.session_state.get(SK_WEIGHTS, pd.Series(dtype=float))

    if not tickers:
        return

    segments = []
    for i, ticker in enumerate(tickers):
        w_pct = float(weights.get(ticker, 0.0)) * 100
        color = _HOLDING_COLORS[i % len(_HOLDING_COLORS)]
        # Show label inside segment; skip text for very narrow segments (<8%)
        label = f"{ticker} {w_pct:.0f}%" if w_pct >= 12 else (ticker if w_pct >= 8 else "")
        segments.append(
            f'<div style="width:{w_pct:.2f}%;background:{color};display:flex;'
            f'align-items:center;justify-content:center;overflow:hidden;'
            f'white-space:nowrap;padding:0 4px;">'
            f'<span style="font-size:0.78rem;font-weight:700;color:#000;letter-spacing:0.03em;">'
            f'{label}</span>'
            f'</div>'
        )

    bar_html = (
        '<div style="display:flex;width:100%;height:34px;border-radius:5px;'
        'overflow:hidden;margin:4px 0 8px;">'
        + "".join(segments)
        + "</div>"
    )
    st.markdown(bar_html, unsafe_allow_html=True)


# ── Health bar ─────────────────────────────────────────────────────────────────

def _health_indicators(analytics: dict) -> list:
    """Build 6 health bar indicator dicts from analytics results.

    Each indicator: {"label": str, "status": green/amber/red, "value": str}.
    """
    perf = analytics.get(SK_PERFORMANCE, {})
    rf   = analytics.get(SK_RISK_FACTORS, {})
    ro   = analytics.get(SK_RISK_OUTLOOK, {})
    opt  = analytics.get(SK_OPTIMIZATION, {})
    sig  = analytics.get(SK_MARKET_SIGNALS, {})

    indicators = []

    # 1. Return Quality — Sharpe ratio
    sharpe = perf.get("sharpe", None)
    if sharpe is None:
        indicators.append({"label": "Return Quality", "status": "amber", "value": "n/a"})
    elif sharpe > 0.5:
        indicators.append({"label": "Return Quality", "status": "green", "value": f"{sharpe:.2f} Sharpe"})
    elif sharpe > 0:
        indicators.append({"label": "Return Quality", "status": "amber", "value": f"{sharpe:.2f} Sharpe"})
    else:
        indicators.append({"label": "Return Quality", "status": "red", "value": f"{sharpe:.2f} Sharpe"})

    # 2. Volatility Risk — historical vol
    hvol = ro.get("hist_vol", None)
    if hvol is None:
        indicators.append({"label": "Volatility", "status": "amber", "value": "n/a"})
    elif hvol < 0.15:
        indicators.append({"label": "Volatility", "status": "green", "value": f"{hvol*100:.1f}% ann."})
    elif hvol < 0.25:
        indicators.append({"label": "Volatility", "status": "amber", "value": f"{hvol*100:.1f}% ann."})
    else:
        indicators.append({"label": "Volatility", "status": "red", "value": f"{hvol*100:.1f}% ann."})

    # 3. Diversification — Effective N relative to n holdings
    eff_n = rf.get("effective_n", None)
    tickers = st.session_state.get(SK_TICKERS, [])
    n_assets = max(len(tickers), 1)
    if eff_n is None:
        indicators.append({"label": "Diversification", "status": "amber", "value": "n/a"})
    else:
        ratio = eff_n / n_assets
        val_str = f"Eff. N = {eff_n:.1f}"
        if ratio >= 0.7:
            indicators.append({"label": "Diversification", "status": "green", "value": val_str})
        elif ratio >= 0.4:
            indicators.append({"label": "Diversification", "status": "amber", "value": val_str})
        else:
            indicators.append({"label": "Diversification", "status": "red", "value": val_str})

    # 4. Drawdown Risk — max drawdown
    mdd = rf.get("max_drawdown", None)
    if mdd is None:
        indicators.append({"label": "Drawdown Risk", "status": "amber", "value": "n/a"})
    elif mdd > -0.10:
        indicators.append({"label": "Drawdown Risk", "status": "green", "value": f"{mdd*100:.1f}%"})
    elif mdd > -0.25:
        indicators.append({"label": "Drawdown Risk", "status": "amber", "value": f"{mdd*100:.1f}%"})
    else:
        indicators.append({"label": "Drawdown Risk", "status": "red", "value": f"{mdd*100:.1f}%"})

    # 5. Market Stress — VIX level from live signals
    vix_sig = sig.get("vix_level", {})
    vix_status = vix_sig.get("status", "unavailable")
    vix_val    = vix_sig.get("value", None)
    if vix_status == "unavailable" or vix_val is None:
        indicators.append({"label": "Market Stress", "status": "amber", "value": "VIX n/a"})
    else:
        indicators.append({
            "label": "Market Stress",
            "status": vix_status,
            "value": f"VIX {vix_val:.1f}",
        })

    # 6. Portfolio Efficiency — distance from efficient frontier
    converged = opt.get("optimizer_converged", False)
    ms_ratio  = opt.get("max_sharpe_ratio", None)
    cur_sharpe = perf.get("sharpe", None)
    if not converged or ms_ratio is None or cur_sharpe is None:
        indicators.append({"label": "Efficiency", "status": "amber", "value": "n/a"})
    else:
        gap = ms_ratio - cur_sharpe
        val_str = f"Gap {gap:+.2f}"
        if gap < 0.1:
            indicators.append({"label": "Efficiency", "status": "green", "value": val_str})
        elif gap < 0.5:
            indicators.append({"label": "Efficiency", "status": "amber", "value": val_str})
        else:
            indicators.append({"label": "Efficiency", "status": "red", "value": val_str})

    return indicators


def _render_health_bar(indicators: list) -> None:
    """Render 6 health indicators as a horizontal strip of colored tiles."""
    cols = st.columns(len(indicators))
    for col, ind in zip(cols, indicators):
        color  = _status_color(ind["status"])
        emoji  = {"green": "🟢", "amber": "🟡", "red": "🔴"}.get(ind["status"], "⚪")
        with col:
            st.markdown(
                f'<div style="border:1px solid {color};border-radius:6px;padding:6px 8px;'
                f'text-align:center;background:rgba(0,0,0,0.2);">'
                f'<div style="font-size:0.72rem;color:{COLOR_TEXT_MUTED};">{ind["label"]}</div>'
                f'<div style="font-size:0.85rem;color:{color};">{emoji} {ind["value"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── Quadrant builders ──────────────────────────────────────────────────────────

def _build_q1(analytics: dict) -> tuple:
    """Q1 — Performance (Descriptive). Returns (chart, kpis, flag)."""
    from components.charts import cumulative_return_chart

    port_ret  = st.session_state.get(SK_PORT_RETURNS, pd.Series(dtype=float))
    bench_ret = st.session_state.get(SK_BENCH_RETURNS, pd.Series(dtype=float))
    benchmark = st.session_state.get(SK_BENCHMARK, "Benchmark")
    perf      = analytics.get(SK_PERFORMANCE, {})

    chart = cumulative_return_chart(port_ret, bench_ret, benchmark_label=benchmark)

    cagr   = perf.get("cagr")
    sharpe = perf.get("sharpe")
    mdd    = analytics.get(SK_RISK_FACTORS, {}).get("max_drawdown")
    vol    = perf.get("volatility")

    kpis = [
        {"label": "CAGR",       "value": _pct(cagr)},
        {"label": "Sharpe",     "value": _fmt(sharpe)},
        {"label": "Max DD",     "value": _pct(mdd)},
        {"label": "Ann. Vol",   "value": _pct(vol, sign=False)},
    ]

    if sharpe is not None and sharpe < 0:
        flag = {"status": "red",   "message": "Negative risk-adjusted return"}
    elif sharpe is not None and sharpe < 0.5:
        flag = {"status": "amber", "message": "Sharpe below 0.5"}
    else:
        flag = {"status": "green", "message": "Healthy risk-adjusted return"}

    return chart, kpis, flag


def _build_q2(analytics: dict) -> tuple:
    """Q2 — Risk Factors (Diagnostic). Returns (chart, kpis, flag)."""
    from components.charts import correlation_heatmap

    rf   = analytics.get(SK_RISK_FACTORS, {})
    corr = rf.get("corr_matrix")

    if corr is not None:
        chart = correlation_heatmap(corr)
    else:
        import plotly.graph_objects as go
        chart = go.Figure().update_layout(title="Correlation Matrix (no data)")

    eff_n = rf.get("effective_n")
    hhi   = rf.get("hhi")
    dr    = rf.get("diversification_ratio")
    beta  = analytics.get(SK_PERFORMANCE, {}).get("beta")

    kpis = [
        {"label": "Beta",        "value": _fmt(beta)},
        {"label": "Effective N", "value": _fmt(eff_n, 1)},
        {"label": "HHI",         "value": _fmt(hhi, 3)},
        {"label": "Div. Ratio",  "value": _fmt(dr)},
    ]

    tickers = st.session_state.get(SK_TICKERS, [])
    n_assets = max(len(tickers), 1)
    if eff_n is not None and eff_n / n_assets < 0.4:
        flag = {"status": "red",   "message": "Highly concentrated portfolio"}
    elif eff_n is not None and eff_n / n_assets < 0.7:
        flag = {"status": "amber", "message": "Moderate concentration"}
    else:
        flag = {"status": "green", "message": "Well diversified"}

    return chart, kpis, flag


def _build_q3(analytics: dict) -> tuple:
    """Q3 — Risk Outlook (Predictive). Returns (chart, kpis, flag)."""
    from components.charts import monte_carlo_fan_chart

    ro       = analytics.get(SK_RISK_OUTLOOK, {})
    mc_p10   = ro.get("mc_p10")
    mc_p50   = ro.get("mc_p50")
    mc_p90   = ro.get("mc_p90")
    horizon  = st.session_state.get("mc_horizon", 10)

    if mc_p10 is not None and mc_p50 is not None and mc_p90 is not None:
        chart = monte_carlo_fan_chart(mc_p10, mc_p50, mc_p90, horizon_years=horizon)
    else:
        import plotly.graph_objects as go
        chart = go.Figure().update_layout(title="Monte Carlo (no data)")

    var95  = ro.get("var_95_hist")
    cvar95 = ro.get("cvar_95_hist")
    hvol   = ro.get("hist_vol")
    gvol   = ro.get("garch_vol")

    kpis = [
        {"label": "VaR 95%",    "value": _pct(var95)},
        {"label": "CVaR 95%",   "value": _pct(cvar95)},
        {"label": "Hist. Vol",  "value": _pct(hvol, sign=False)},
        {"label": "GARCH Vol",  "value": _pct(gvol, sign=False)},
    ]

    if var95 is not None and var95 < -0.03:
        flag = {"status": "red",   "message": f"Tail risk: VaR {var95*100:.1f}%/day"}
    elif var95 is not None and var95 < -0.015:
        flag = {"status": "amber", "message": "Elevated daily tail risk"}
    else:
        flag = {"status": "green", "message": "Tail risk within normal range"}

    return chart, kpis, flag


def _build_q4(analytics: dict) -> tuple:
    """Q4 — Optimization (Prescriptive). Returns (chart, kpis, flag)."""
    from components.charts import efficient_frontier_chart

    opt  = analytics.get(SK_OPTIMIZATION, {})
    perf = analytics.get(SK_PERFORMANCE, {})

    fv  = opt.get("frontier_vols", [])
    fr  = opt.get("frontier_returns", [])
    rf  = st.session_state.get(SK_RISK_FREE_RATE, 0.0) * 252

    hist_vol = analytics.get(SK_RISK_OUTLOOK, {}).get("hist_vol", 0.18)
    cur_ret  = perf.get("cagr", 0.0) or 0.0

    if fv and fr:
        chart = efficient_frontier_chart(
            frontier_vols=fv,
            frontier_returns=fr,
            current_vol=hist_vol,
            current_return=cur_ret,
            max_sharpe_vol=opt.get("max_sharpe_vol", 0.18),
            max_sharpe_return=opt.get("max_sharpe_return", 0.10),
            min_var_vol=opt.get("min_var_vol", 0.15),
            min_var_return=opt.get("min_var_return", 0.06),
            risk_parity_vol=opt.get("risk_parity_vol", 0.16),
            risk_parity_return=opt.get("risk_parity_return", 0.08),
            risk_free_rate=rf,
        )
    else:
        import plotly.graph_objects as go
        chart = go.Figure().update_layout(title="Efficient Frontier (no data)")

    ms_ratio = opt.get("max_sharpe_ratio")
    ms_ret   = opt.get("max_sharpe_return")
    mv_vol   = opt.get("min_var_vol")
    cur_s    = perf.get("sharpe")

    kpis = [
        {"label": "Max Sharpe",    "value": _fmt(ms_ratio)},
        {"label": "Max Shrp Ret",  "value": _pct(ms_ret)},
        {"label": "Min Var Vol",   "value": _pct(mv_vol, sign=False)},
        {"label": "Current Sharpe","value": _fmt(cur_s)},
    ]

    converged = opt.get("optimizer_converged", False)
    if not converged:
        flag = {"status": "amber", "message": "Optimizer did not fully converge"}
    elif ms_ratio is not None and cur_s is not None and (ms_ratio - cur_s) > 0.5:
        flag = {"status": "amber", "message": "Significant improvement available"}
    else:
        flag = {"status": "green", "message": "Portfolio near efficient frontier"}

    return chart, kpis, flag


# ── Details page routing ───────────────────────────────────────────────────────

def _route_details(details_key: str) -> None:
    """Render the requested details page within the DASHBOARD nav context."""
    back_col, _ = st.columns([1, 5])
    with back_col:
        if st.button("← Back to Dashboard"):
            del st.session_state[_SK_DETAILS]
            st.rerun()

    if details_key == "q1":
        from pages.details_q1 import render as render_details
    elif details_key == "q2":
        from pages.details_q2 import render as render_details
    elif details_key == "q3":
        from pages.details_q3 import render as render_details
    elif details_key == "q4":
        from pages.details_q4 import render as render_details
    else:
        st.error(f"Unknown details page: {details_key}")
        return

    render_details()


# ── Main render ────────────────────────────────────────────────────────────────

def render() -> None:
    """Render the Main Dashboard screen."""
    if not _check_loaded():
        return

    # Route to details if requested
    if _SK_DETAILS in st.session_state:
        _route_details(st.session_state[_SK_DETAILS])
        return

    analytics = st.session_state.get(SK_ANALYTICS, {})
    name = st.session_state.get(SK_PORTFOLIO_NAME, "")
    title = f"Dashboard — {name}" if name else "Dashboard"
    st.title(title)

    # Ticker tape
    _render_ticker_tape()

    # Holdings strip
    st.markdown("#### Holdings")
    _render_holdings_strip()
    st.markdown("")

    # Health bar
    st.markdown("#### Portfolio Health")
    indicators = _health_indicators(analytics)
    _render_health_bar(indicators)
    st.markdown("")

    # 2x2 quadrant grid
    from components.dashboard_quad import render_quadrant

    st.markdown("#### Analysis")
    top_left, top_right = st.columns(2, gap="medium")
    bot_left, bot_right = st.columns(2, gap="medium")

    with top_left:
        chart, kpis, flag = _build_q1(analytics)
        render_quadrant("q1", "Q1 — Performance", chart, kpis, flag, "q1")

    with top_right:
        chart, kpis, flag = _build_q2(analytics)
        render_quadrant("q2", "Q2 — Risk Factors", chart, kpis, flag, "q2")

    with bot_left:
        chart, kpis, flag = _build_q3(analytics)
        render_quadrant("q3", "Q3 — Risk Outlook", chart, kpis, flag, "q3")

    with bot_right:
        chart, kpis, flag = _build_q4(analytics)
        render_quadrant("q4", "Q4 — Optimization", chart, kpis, flag, "q4")
