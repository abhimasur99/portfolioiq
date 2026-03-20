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
    BENCHMARK_OPTIONS,
    COLOR_BLUE, COLOR_GREEN, COLOR_AMBER, COLOR_RED, COLOR_TEXT_MUTED,
    DEFAULT_MC_HORIZON, DEFAULT_MC_PATHS, DEFAULT_VAR_CONFIDENCE,
    DEFAULT_WEIGHT_MIN, DEFAULT_WEIGHT_MAX,
    SK_ANALYSIS_END, SK_ANALYSIS_START,
    SK_ANALYTICS, SK_BENCH_RETURNS, SK_BENCHMARK,
    SK_MARKET_SIGNALS, SK_MC_HORIZON, SK_MC_PATHS,
    SK_OPTIMIZATION, SK_PERFORMANCE, SK_PERIOD,
    SK_PORTFOLIO_LOADED, SK_PORTFOLIO_NAME, SK_PORT_RETURNS,
    SK_PRICE_DATA, SK_PRICE_DATA_FULL, SK_RETURNS_DF,
    SK_RISK_FACTORS, SK_RISK_FREE_RATE, SK_RISK_OUTLOOK,
    SK_TICKERS, SK_VAR_CONFIDENCE, SK_WEIGHT_MAX, SK_WEIGHT_MIN, SK_WEIGHTS,
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

    # 1. Market Stress — VIX level from live signals (external context first)
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

    # 2. Return Quality — Sharpe ratio
    sharpe = perf.get("sharpe", None)
    if sharpe is None:
        indicators.append({"label": "Return Quality", "status": "amber", "value": "n/a"})
    elif sharpe > 0.5:
        indicators.append({"label": "Return Quality", "status": "green", "value": f"{sharpe:.2f} Sharpe"})
    elif sharpe > 0:
        indicators.append({"label": "Return Quality", "status": "amber", "value": f"{sharpe:.2f} Sharpe"})
    else:
        indicators.append({"label": "Return Quality", "status": "red", "value": f"{sharpe:.2f} Sharpe"})

    # 3. Volatility — historical vol
    hvol = ro.get("hist_vol", None)
    if hvol is None:
        indicators.append({"label": "Volatility", "status": "amber", "value": "n/a"})
    elif hvol < 0.15:
        indicators.append({"label": "Volatility", "status": "green", "value": f"{hvol*100:.1f}% ann."})
    elif hvol < 0.25:
        indicators.append({"label": "Volatility", "status": "amber", "value": f"{hvol*100:.1f}% ann."})
    else:
        indicators.append({"label": "Volatility", "status": "red", "value": f"{hvol*100:.1f}% ann."})

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

    # 5. Diversification — Effective N relative to n holdings
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
        {"label": "CAGR",     "value": _pct(cagr),
         "help": "Compound Annual Growth Rate — the constant yearly return that matches total portfolio growth over the period. Accounts for compounding."},
        {"label": "Sharpe",   "value": _fmt(sharpe),
         "help": "Excess return per unit of total risk. Above 0.5 is acceptable; above 1.0 is strong; below 0 means underperforming cash on a risk-adjusted basis."},
        {"label": "Max DD",   "value": _pct(mdd),
         "help": "Largest peak-to-trough decline over the period. Worst loss a buy-and-hold investor would have experienced."},
        {"label": "Ann. Vol", "value": _pct(vol, sign=False),
         "help": "Annualised standard deviation of daily returns. Higher = wider daily swings in both directions."},
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
        {"label": "Beta",        "value": _fmt(beta),
         "help": "Sensitivity to benchmark. β > 1 amplifies market moves; β < 1 dampens them."},
        {"label": "Effective N", "value": _fmt(eff_n, 1),
         "help": "Number of truly independent positions after accounting for correlations. Lower than your actual holding count means the portfolio is concentrated."},
        {"label": "HHI",         "value": _fmt(hhi, 3),
         "help": "Sum of squared weights — equals 1/N for equal weight, 1.0 for a single asset. Lower = more diversified."},
        {"label": "Div. Ratio",  "value": _fmt(dr),
         "help": "Weighted-average individual volatility divided by portfolio volatility. Above 1.0 confirms diversification is reducing risk."},
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
    horizon  = st.session_state.get(SK_MC_HORIZON, DEFAULT_MC_HORIZON)

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
        {"label": "VaR 95%",   "value": _pct(var95),
         "help": "Worst daily loss in 95% of trading days (historical). On roughly 1 in 20 days, losses exceeded this threshold."},
        {"label": "CVaR 95%",  "value": _pct(cvar95),
         "help": "Average loss on the worst 5% of days (Expected Shortfall). More severe than VaR and better captures tail risk."},
        {"label": "Hist. Vol", "value": _pct(hvol, sign=False),
         "help": "Full-period annualised volatility from historical daily returns. Constant-weight estimate over the selected period."},
        {"label": "GARCH Vol", "value": _pct(gvol, sign=False),
         "help": "Forward-looking volatility estimate from a GARCH(1,1) model, which weights recent moves more heavily than older ones."},
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
        {"label": "Max Sharpe",     "value": _fmt(ms_ratio),
         "help": "Highest achievable Sharpe ratio along the efficient frontier under the weight constraints. Subject to estimation error in expected returns."},
        {"label": "Max Shrp Ret",   "value": _pct(ms_ret),
         "help": "Expected annualised return at the maximum Sharpe (tangency) portfolio, estimated from historical data."},
        {"label": "Min Var Vol",    "value": _pct(mv_vol, sign=False),
         "help": "Lowest achievable portfolio volatility along the efficient frontier under the weight constraints."},
        {"label": "Current Sharpe", "value": _fmt(cur_s),
         "help": "Your portfolio's Sharpe ratio at the current weights. Compare to Max Sharpe to see how far from optimal the allocation is."},
    ]

    converged = opt.get("optimizer_converged", False)
    if not converged:
        flag = {"status": "amber", "message": "Optimizer did not fully converge"}
    elif ms_ratio is not None and cur_s is not None and (ms_ratio - cur_s) > 0.5:
        flag = {"status": "amber", "message": "Significant improvement available"}
    else:
        flag = {"status": "green", "message": "Portfolio near efficient frontier"}

    return chart, kpis, flag


# ── Window labels and date offsets ─────────────────────────────────────────────

_WINDOW_OPTIONS = ["1Y", "3Y", "5Y", "All", "Custom"]
_WINDOW_OFFSETS = {"1Y": 1, "3Y": 3, "5Y": 5}  # years; "All" and "Custom" handled separately


def _window_start(label: str, end: pd.Timestamp, full_start: pd.Timestamp) -> pd.Timestamp:
    """Compute the start date for a given window label."""
    if label == "All":
        return full_start
    if label in _WINDOW_OFFSETS:
        candidate = end - pd.DateOffset(years=_WINDOW_OFFSETS[label])
        return max(candidate, full_start)
    return full_start


def _recompute_for_window(label: str, start: pd.Timestamp, end: pd.Timestamp) -> bool:
    """Slice the stored 5y prices to (start, end) and recompute all analytics layers.

    Updates SK_ANALYTICS, SK_PRICE_DATA, SK_RETURNS_DF, SK_PORT_RETURNS,
    SK_BENCH_RETURNS, SK_ANALYSIS_START, SK_ANALYSIS_END, SK_PERIOD in session state.

    Returns True on success, False on failure.
    """
    from analytics.returns import compute_log_returns, compute_portfolio_returns
    from analytics.performance import compute_all_performance
    from analytics.risk_factors import compute_all_risk_factors
    from analytics.risk_outlook import compute_all_risk_outlook
    from analytics.optimization import compute_all_optimization

    full_prices = st.session_state.get(SK_PRICE_DATA_FULL)
    tickers     = st.session_state.get(SK_TICKERS, [])
    weights     = st.session_state.get(SK_WEIGHTS)
    benchmark   = st.session_state.get(SK_BENCHMARK, "SPY")
    rf          = st.session_state.get(SK_RISK_FREE_RATE, 0.0)
    weight_min  = st.session_state.get(SK_WEIGHT_MIN, DEFAULT_WEIGHT_MIN)
    weight_max  = st.session_state.get(SK_WEIGHT_MAX, DEFAULT_WEIGHT_MAX)

    if full_prices is None or weights is None:
        return False

    prices_window = full_prices.loc[start:end]
    if len(prices_window) < 60:
        st.warning("Selected window has too few trading days. Expand the date range.")
        return False

    settings = {
        "var_confidence": st.session_state.get(SK_VAR_CONFIDENCE, DEFAULT_VAR_CONFIDENCE),
        "mc_horizon":     st.session_state.get(SK_MC_HORIZON, DEFAULT_MC_HORIZON),
        "mc_paths":       st.session_state.get(SK_MC_PATHS, DEFAULT_MC_PATHS),
    }

    try:
        returns_df        = compute_log_returns(prices_window)
        available         = [t for t in tickers if t in returns_df.columns]
        weights_aligned   = weights.reindex(available).dropna()
        weights_aligned   = weights_aligned / weights_aligned.sum()
        portfolio_returns = compute_portfolio_returns(returns_df[available], weights_aligned)
        benchmark_returns = (
            returns_df[benchmark] if benchmark in returns_df.columns
            else portfolio_returns.copy()
        )
        performance  = compute_all_performance(portfolio_returns, benchmark_returns, rf)
        risk_factors = compute_all_risk_factors(returns_df[available], weights_aligned, portfolio_returns)
        risk_outlook = compute_all_risk_outlook(portfolio_returns, benchmark_returns, weights_aligned, performance, settings)
        optimization = compute_all_optimization(returns_df[available], weights_aligned, rf, weight_min, weight_max)

        # Update session state — preserve market_signals (time-independent)
        analytics = st.session_state.get(SK_ANALYTICS, {})
        analytics[SK_PERFORMANCE]  = performance
        analytics[SK_RISK_FACTORS] = risk_factors
        analytics[SK_RISK_OUTLOOK] = risk_outlook
        analytics[SK_OPTIMIZATION] = optimization
        st.session_state[SK_ANALYTICS]       = analytics
        st.session_state[SK_PRICE_DATA]      = prices_window
        st.session_state[SK_RETURNS_DF]      = returns_df
        st.session_state[SK_PORT_RETURNS]    = portfolio_returns
        st.session_state[SK_BENCH_RETURNS]   = benchmark_returns
        st.session_state[SK_ANALYSIS_START]  = str(start.date())
        st.session_state[SK_ANALYSIS_END]    = str(end.date())
        st.session_state[SK_PERIOD]          = label
        return True
    except Exception as exc:
        st.error(f"Window recompute failed: {exc}")
        return False


def _render_time_selector() -> None:
    """Render the analysis window selector bar and handle window changes."""
    full_prices = st.session_state.get(SK_PRICE_DATA_FULL)
    if full_prices is None or full_prices.empty:
        return

    full_start = full_prices.index[0]
    full_end   = full_prices.index[-1]
    current_label = st.session_state.get(SK_PERIOD, "3Y")
    if current_label not in _WINDOW_OPTIONS:
        current_label = "3Y"
    current_idx = _WINDOW_OPTIONS.index(current_label)

    selected = st.radio(
        "Analysis window",
        options=_WINDOW_OPTIONS,
        index=current_idx,
        horizontal=True,
        label_visibility="collapsed",
    )

    # Custom date pickers (shown only when Custom is selected)
    if selected == "Custom":
        col_s, col_e = st.columns(2)
        with col_s:
            default_start = (full_end - pd.DateOffset(years=3)).date()
            custom_start  = st.date_input(
                "From",
                value=default_start,
                min_value=full_start.date(),
                max_value=full_end.date(),
                key="_custom_start",
            )
        with col_e:
            custom_end = st.date_input(
                "To",
                value=full_end.date(),
                min_value=full_start.date(),
                max_value=full_end.date(),
                key="_custom_end",
            )
        if custom_start >= custom_end:
            st.warning("Start date must be before end date.")
            return
        new_start = pd.Timestamp(custom_start)
        new_end   = pd.Timestamp(custom_end)
    else:
        new_start = _window_start(selected, full_end, full_start)
        new_end   = full_end

    # Recompute only when the selection has actually changed
    if selected != current_label or selected == "Custom":
        # For Custom, also check if dates changed
        prev_start = st.session_state.get(SK_ANALYSIS_START, "")
        prev_end   = st.session_state.get(SK_ANALYSIS_END, "")
        new_start_str = str(new_start.date())
        new_end_str   = str(new_end.date())
        if selected != current_label or new_start_str != prev_start or new_end_str != prev_end:
            with st.spinner(f"Computing {selected} analysis…"):
                success = _recompute_for_window(selected, new_start, new_end)
            if success:
                st.rerun()


# ── Details page routing ───────────────────────────────────────────────────────

def _route_details(details_key: str) -> None:
    """Render the requested details page within the DASHBOARD nav context."""
    _ORDER  = ["q1", "q2", "q3", "q4"]
    _LABELS = {
        "q1": "Performance",
        "q2": "Risk Factors",
        "q3": "Risk Outlook",
        "q4": "Optimization",
    }

    idx = _ORDER.index(details_key)
    back_col, _, nav_col = st.columns([2, 3, 3])

    with back_col:
        if st.button("← Dashboard", key="_btn_back_dash"):
            del st.session_state[_SK_DETAILS]
            st.rerun()

    with nav_col:
        l_col, r_col = st.columns(2)
        with l_col:
            if idx > 0:
                prev = _ORDER[idx - 1]
                if st.button(f"← {_LABELS[prev]}", key="_btn_nav_prev", use_container_width=True):
                    st.session_state[_SK_DETAILS] = prev
                    st.rerun()
        with r_col:
            if idx < len(_ORDER) - 1:
                nxt = _ORDER[idx + 1]
                if st.button(f"{_LABELS[nxt]} →", key="_btn_nav_next", use_container_width=True):
                    st.session_state[_SK_DETAILS] = nxt
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

    # Context badge + time frame selector (before health bar)
    port_ret = st.session_state.get(SK_PORT_RETURNS)
    window_label = st.session_state.get(SK_PERIOD, "3Y")
    benchmark = st.session_state.get(SK_BENCHMARK, "SPY")
    bench_label = next((k for k, v in BENCHMARK_OPTIONS.items() if v == benchmark), benchmark)
    if port_ret is not None and not port_ret.empty:
        last_date = port_ret.index[-1].strftime("%b %d, %Y")
        st.caption(
            f"**{window_label} Analysis** | Benchmark: {bench_label} | "
            f"Data as of {last_date} — reflects previous market close"
        )

    _render_time_selector()

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
