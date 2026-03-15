"""pages/details_q3.py

Screen 3c — Q3 More Details: Risk Outlook (Predictive).

Responsibilities:
- Back to Dashboard button (always first element).
- Plain-language insight block at top.
- Live Risk Preparedness Panel: all 11 forward-looking signals, each with
  label, current value, status badge, and one-sentence interpretation.
  Disclaimer: signals are awareness tools, not predictions.
- Extended charts: GARCH volatility vs historical, Monte Carlo fan chart,
  stress test bar chart.
- Complete metric table.
- Explain Numbers panel available.

Accessed exclusively via the More Details button on Q3 of the dashboard.
Never appears in the nav bar.

Implemented in: Session 12.
"""

import pandas as pd
import streamlit as st

from assets.config import (
    COLOR_AMBER,
    COLOR_GREEN,
    COLOR_RED,
    COLOR_TEXT_MUTED,
    SK_ANALYTICS,
    SK_MARKET_SIGNALS,
    SK_MC_HORIZON,
    SK_PERFORMANCE,
    SK_PORT_RETURNS,
    SK_RISK_OUTLOOK,
)

_EXPLAIN_KEY = "_explain_open_q3_details"

# Signal display labels (key → human-readable name)
_SIGNAL_LABELS = {
    "vix_level":          "VIX Level",
    "vix_trend":          "VIX Trend",
    "vix_term_structure": "VIX Term Structure",
    "move_index":         "MOVE Index",
    "yield_curve":        "Yield Curve",
    "credit_spreads":     "Credit Spreads",
    "copper_gold_ratio":  "Copper / Gold Ratio",
    "dollar_index":       "Dollar Index (DXY)",
    "oil_sensitivity":    "Oil Sensitivity",
    "rate_sensitivity":   "Rate Sensitivity",
    "tech_concentration": "Tech Concentration",
}

_STATUS_COLOR = {
    "green":       COLOR_GREEN,
    "amber":       COLOR_AMBER,
    "red":         COLOR_RED,
    "unavailable": COLOR_TEXT_MUTED,
}
_STATUS_EMOJI = {
    "green":       "🟢",
    "amber":       "🟡",
    "red":         "🔴",
    "unavailable": "⚪",
}


# ── Formatting helpers ──────────────────────────────────────────────────────────

def _pct(val, decimals: int = 1, sign: bool = True) -> str:
    if val is None:
        return "n/a"
    try:
        fmt = f"{'+' if sign else ''}.{decimals}f"
        return f"{float(val) * 100:{fmt}}%"
    except (TypeError, ValueError):
        return "n/a"


def _fmt(val, decimals: int = 2) -> str:
    if val is None:
        return "n/a"
    try:
        return f"{float(val):.{decimals}f}"
    except (TypeError, ValueError):
        return "n/a"


def _fmt_signal_value(val) -> str:
    """Format a signal value for display — 2 decimals if numeric, dash otherwise."""
    if val is None:
        return "—"
    try:
        return f"{float(val):.2f}"
    except (TypeError, ValueError):
        return str(val)


# ── Risk Preparedness Panel ─────────────────────────────────────────────────────

def _render_preparedness_panel(signals: dict) -> None:
    """Render the 11-signal risk preparedness grid."""
    st.markdown("##### Live Risk Preparedness Panel")
    st.caption(
        "Forward-looking market environment signals fetched live at portfolio load time. "
        "These are awareness indicators, not predictions or investment advice."
    )

    signal_keys = list(_SIGNAL_LABELS.keys())
    # Render in rows of 3
    for row_start in range(0, len(signal_keys), 3):
        row_keys = signal_keys[row_start : row_start + 3]
        cols = st.columns(len(row_keys))
        for col, key in zip(cols, row_keys):
            sig   = signals.get(key, {})
            label = _SIGNAL_LABELS[key]
            val   = sig.get("value")
            status = sig.get("status", "unavailable")
            interp = sig.get("interpretation", "No data available.")
            color  = _STATUS_COLOR.get(status, COLOR_TEXT_MUTED)
            emoji  = _STATUS_EMOJI.get(status, "⚪")

            with col:
                st.markdown(
                    f'<div style="border:1px solid {color};border-radius:8px;'
                    f'padding:10px 12px;background:rgba(0,0,0,0.2);margin-bottom:8px;">'
                    f'<div style="font-size:0.72rem;color:{COLOR_TEXT_MUTED};'
                    f'margin-bottom:4px;">{label}</div>'
                    f'<div style="font-size:1.0rem;color:{color};font-weight:600;">'
                    f'{emoji} {_fmt_signal_value(val)}</div>'
                    f'<div style="font-size:0.72rem;color:{COLOR_TEXT_MUTED};'
                    f'margin-top:6px;line-height:1.3;">{interp}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    st.caption(
        "_Signals are updated each time you load a portfolio. Market data is sourced from "
        "yfinance and may lag by one trading day. Signal thresholds are heuristic — "
        "red does not mean 'sell'; it means the environment warrants heightened awareness._"
    )


# ── Page render ─────────────────────────────────────────────────────────────────

def render() -> None:
    """Render the Q3 (Risk Outlook) More Details screen."""
    analytics   = st.session_state.get(SK_ANALYTICS, {})
    ro          = analytics.get(SK_RISK_OUTLOOK, {})
    signals     = analytics.get(SK_MARKET_SIGNALS, {})
    port_ret    = st.session_state.get(SK_PORT_RETURNS, pd.Series(dtype=float))
    mc_horizon  = st.session_state.get(SK_MC_HORIZON, 10)

    # Pull values used throughout
    hist_vol      = ro.get("hist_vol")
    ewma_vol      = ro.get("ewma_vol")
    garch_vol     = ro.get("garch_vol")
    garch_result  = ro.get("garch_model")
    is_fallback   = ro.get("garch_fallback", False)
    var_95_hist   = ro.get("var_95_hist")
    cvar_95_hist  = ro.get("cvar_95_hist")
    var_99_hist   = ro.get("var_99_hist")
    cvar_99_hist  = ro.get("cvar_99_hist")
    var_95_garch  = ro.get("var_95_garch")
    var_monthly   = ro.get("var_monthly")
    mc_p10        = ro.get("mc_p10")
    mc_p50        = ro.get("mc_p50")
    mc_p90        = ro.get("mc_p90")
    stress_results = ro.get("stress_results", {})
    skewness      = ro.get("skewness")
    excess_kurt   = ro.get("excess_kurtosis")

    # ── Title ──────────────────────────────────────────────────────────────────
    st.title("Risk Outlook — Deep Dive")
    st.caption("Predictive analytics: volatility forecasts, tail risk, and scenario stress tests.")

    # ── Insight block ──────────────────────────────────────────────────────────
    with st.container():
        left_col, right_col = st.columns([3, 2], gap="large")
        with left_col:
            st.markdown("##### At a Glance")
            insight_lines = []

            if hist_vol is not None:
                if hist_vol > 0.30:
                    insight_lines.append(
                        f"**High volatility environment:** annualised historical volatility is "
                        f"**{_pct(hist_vol, sign=False)}** — well above the typical 15–20% range "
                        "for a diversified equity portfolio."
                    )
                elif hist_vol > 0.18:
                    insight_lines.append(
                        f"**Elevated volatility:** annualised historical vol of "
                        f"**{_pct(hist_vol, sign=False)}** is above the long-run average but "
                        "within normal range for an equity-heavy portfolio."
                    )
                else:
                    insight_lines.append(
                        f"**Low volatility environment:** annualised historical vol of "
                        f"**{_pct(hist_vol, sign=False)}** is in the calm range. "
                        "This may understate tail risk if current conditions are unusual."
                    )

            if garch_vol is not None and hist_vol is not None:
                spread = abs(garch_vol - hist_vol)
                if garch_vol > hist_vol * 1.15:
                    insight_lines.append(
                        f"GARCH model-implied vol (**{_pct(garch_vol, sign=False)}**) is "
                        f"materially above historical vol — the model detects recent volatility "
                        "clustering and is signalling rising near-term risk."
                    )
                elif garch_vol < hist_vol * 0.85:
                    insight_lines.append(
                        f"GARCH vol (**{_pct(garch_vol, sign=False)}**) is below historical vol, "
                        "suggesting a recent calm period after an earlier volatile stretch."
                    )
                if is_fallback:
                    insight_lines.append(
                        "_Note: GARCH model used EWMA fallback (insufficient data or "
                        "non-stationary fit). Volatility estimate is less precise._"
                    )

            if var_95_hist is not None:
                insight_lines.append(
                    f"On the worst 5% of trading days historically, the portfolio lost at least "
                    f"**{_pct(var_95_hist)}** (VaR 95%). The average loss on those days was "
                    f"**{_pct(cvar_95_hist)}** (CVaR 95%)."
                )

            if skewness is not None and excess_kurt is not None:
                tail_note = []
                if skewness < -0.5:
                    tail_note.append("negative skew (more frequent large losses than gains)")
                if excess_kurt > 1.0:
                    tail_note.append("fat tails (extreme events more likely than normal distribution predicts)")
                if tail_note:
                    insight_lines.append(
                        "The return distribution shows " + " and ".join(tail_note) + ". "
                        "Historical VaR may understate true tail risk."
                    )

            for line in insight_lines:
                st.markdown(f"- {line}")

            st.caption(
                "_Forward-looking estimates are based on historical data. The GARCH model "
                "assumes volatility clustering and mean reversion. Monte Carlo paths use "
                "GARCH-implied dynamics. Past tail behaviour may not reflect future tail risk._"
            )

        with right_col:
            st.markdown("##### Key Metrics")
            summary = {
                "Metric": ["Hist. Vol (ann.)", "GARCH Vol (ann.)", "VaR 95% (daily)",
                            "CVaR 95% (daily)", "VaR 95% (monthly)", "Skewness"],
                "Value":  [_pct(hist_vol, sign=False), _pct(garch_vol, sign=False),
                            _pct(var_95_hist), _pct(cvar_95_hist),
                            _pct(var_monthly), _fmt(skewness)],
            }
            st.dataframe(pd.DataFrame(summary), hide_index=True, use_container_width=True)

    st.markdown("---")

    # ── Risk Preparedness Panel ────────────────────────────────────────────────
    _render_preparedness_panel(signals)

    st.markdown("---")

    # ── Charts ─────────────────────────────────────────────────────────────────
    st.markdown("##### Charts")

    from components.charts import (
        garch_volatility_chart,
        monte_carlo_fan_chart,
        stress_test_chart,
    )

    # GARCH volatility vs historical (full width)
    st.plotly_chart(
        garch_volatility_chart(
            portfolio_returns=port_ret,
            ewma_vol=ewma_vol if ewma_vol is not None else pd.Series(dtype=float),
            garch_result=garch_result,
            is_fallback=is_fallback,
        ),
        use_container_width=True,
        key="_det_q3_garchvol",
    )

    # Monte Carlo fan | Stress test
    ch_left, ch_right = st.columns(2)
    with ch_left:
        if mc_p10 is not None and mc_p50 is not None and mc_p90 is not None:
            st.plotly_chart(
                monte_carlo_fan_chart(mc_p10, mc_p50, mc_p90, horizon_years=mc_horizon),
                use_container_width=True,
                key="_det_q3_mc",
            )
        else:
            st.info("Monte Carlo data not available.")
    with ch_right:
        if stress_results:
            st.plotly_chart(
                stress_test_chart(stress_results),
                use_container_width=True,
                key="_det_q3_stress",
            )
        else:
            st.info("Stress test data not available.")

    st.markdown("---")

    # ── Full metrics table ─────────────────────────────────────────────────────
    st.markdown("##### All Risk Outlook Metrics")

    garch_label = "EWMA (GARCH fallback)" if is_fallback else "GARCH(1,1)"

    metrics_data = {
        "Metric": [
            "Historical Volatility (ann.)",
            "EWMA Volatility (ann.)",
            f"{garch_label} Volatility (ann.)",
            "VaR 95% — Historical (daily)",
            "CVaR 95% — Historical (daily)",
            "VaR 99% — Historical (daily)",
            "CVaR 99% — Historical (daily)",
            "VaR 95% — GARCH (daily)",
            "VaR 95% — Monthly Scaled",
            "Return Skewness",
            "Excess Kurtosis",
        ],
        "Value": [
            _pct(hist_vol, sign=False),
            _pct(ewma_vol, sign=False),
            _pct(garch_vol, sign=False),
            _pct(var_95_hist),
            _pct(cvar_95_hist),
            _pct(var_99_hist),
            _pct(cvar_99_hist),
            _pct(var_95_garch),
            _pct(var_monthly),
            _fmt(skewness),
            _fmt(excess_kurt),
        ],
        "What it measures": [
            "Standard deviation of daily log returns × √252. Constant-weight estimate over full period.",
            "Exponentially-weighted moving average of variance (λ=0.94, RiskMetrics). More weight on recent days.",
            "Conditional variance from GARCH(1,1) fit — captures volatility clustering and mean reversion. "
            "Falls back to EWMA if insufficient data or non-stationary fit (α+β≥1).",
            "5th percentile of historical daily return distribution — threshold loss on worst 5% of days.",
            "Average loss on the worst 5% of days. Always worse than VaR; this is the expected shortfall.",
            "1st percentile threshold — loss exceeded only 1% of trading days historically.",
            "Average loss on the worst 1% of days. Extreme tail risk estimate.",
            "VaR using GARCH-implied conditional volatility × normal quantile (1.645σ). Forward-looking.",
            "Daily VaR 95% scaled to monthly horizon using i.i.d. approximation (×√21). Directional only.",
            "Asymmetry of the return distribution. Negative skew means more large losses than gains.",
            "Tail thickness beyond a normal distribution. Excess kurtosis > 0 means fatter tails — "
            "extreme events occur more often than the normal distribution predicts.",
        ],
    }

    st.dataframe(
        pd.DataFrame(metrics_data),
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("---")

    # ── Explain Numbers ────────────────────────────────────────────────────────
    if st.button("Explain Numbers", key="_det_q3_exp_btn", use_container_width=True):
        st.session_state[_EXPLAIN_KEY] = not st.session_state.get(_EXPLAIN_KEY, False)

    if st.session_state.get(_EXPLAIN_KEY, False):
        st.markdown("---")
        from components.explain_panel import render_explain_panel
        render_explain_panel("q3", analytics)
        if st.button("Close explanation", key="_det_q3_close_exp"):
            st.session_state[_EXPLAIN_KEY] = False
            st.rerun()
