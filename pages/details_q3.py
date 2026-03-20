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
    SK_ANALYTICS,
    SK_MARKET_SIGNALS,
    SK_MC_HORIZON,
    SK_PERFORMANCE,
    SK_PORT_RETURNS,
    SK_RISK_OUTLOOK,
)

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


# ── Signal-driven scenario computation ──────────────────────────────────────────

_ENV_EMOJI = {"Calm": "🟢", "Elevated": "🟡", "Stressed": "🟠", "Severe": "🔴"}


def _compute_signal_scenarios(garch_vol: float, signals: dict) -> dict:
    """Derive three stress scenarios from GARCH vol and current signal statuses.

    Environment level is determined by counting red and amber signal statuses
    (unavailable signals are excluded from the count).

    Returns a dict with environment_level, n_red, n_amber, and three scenarios,
    each containing var_day, var_month (both negative, i.e. loss estimates),
    and a highlighted flag indicating which scenario matches the current environment.
    """
    n_red   = sum(1 for s in signals.values() if s.get("status") == "red")
    n_amber = sum(1 for s in signals.values() if s.get("status") == "amber")

    if n_red >= 4:
        env_level = "Severe"
    elif n_red >= 2:
        env_level = "Stressed"
    elif n_red == 1 or n_amber >= 3:
        env_level = "Elevated"
    else:
        env_level = "Calm"

    highlight_map = {
        "Calm":     "Moderate Stress",
        "Elevated": "Significant Stress",
        "Stressed": "Significant Stress",
        "Severe":   "Severe Stress",
    }
    highlighted = highlight_map[env_level]

    daily_vol = garch_vol / (252 ** 0.5)

    scenarios: dict = {}
    for name, mult in [
        ("Moderate Stress",    1.5),
        ("Significant Stress", 2.0),
        ("Severe Stress",      3.0),
    ]:
        s_daily_vol = daily_vol * mult
        var_day     = -1.645 * s_daily_vol
        var_month   = var_day * (21 ** 0.5)
        scenarios[name] = {
            "multiplier":  mult,
            "var_day":     var_day,
            "var_month":   var_month,
            "highlighted": (name == highlighted),
        }

    return {
        "environment_level": env_level,
        "n_red":   n_red,
        "n_amber": n_amber,
        "scenarios": scenarios,
    }


# ── Risk Preparedness Panel ─────────────────────────────────────────────────────

def _render_preparedness_panel(signals: dict) -> None:
    """Render the 11-signal risk preparedness grid using st.metric with ? tooltips."""
    st.markdown("##### Market Environment Signals")
    st.caption(
        "Market environment signals fetched fresh at portfolio analysis time using end-of-day data. "
        "Hover the ? icon on each signal for its interpretation. "
        "These are awareness indicators, not predictions or investment advice."
    )

    signal_keys = list(_SIGNAL_LABELS.keys())
    # Render in rows of 3
    for row_start in range(0, len(signal_keys), 3):
        row_keys = signal_keys[row_start : row_start + 3]
        cols = st.columns(3)
        for col, key in zip(cols, row_keys):
            sig    = signals.get(key, {})
            label  = _SIGNAL_LABELS[key]
            val    = sig.get("value")
            status = sig.get("status", "unavailable")
            interp = sig.get("interpretation", "No data available.")
            emoji  = _STATUS_EMOJI.get(status, "⚪")
            if key == "tech_concentration" and status == "unavailable":
                display_val = "⚪ Coming Soon"
            elif val is not None:
                display_val = f"{emoji} {_fmt_signal_value(val)}"
            else:
                display_val = f"{emoji} n/a"

            with col:
                st.metric(label=label, value=display_val, help=interp)

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

    # ── Compute signal scenarios (used in insight block and charts) ────────────
    scenario_data = None
    if garch_vol is not None:
        scenario_data = _compute_signal_scenarios(garch_vol, signals)

    # ── Insight block ──────────────────────────────────────────────────────────
    with st.container():
        left_col, right_col = st.columns([3, 2], gap="large")
        with left_col:
            st.markdown("##### At a Glance")
            insight_lines = []

            # Environment assessment from signals
            if scenario_data is not None:
                env_level = scenario_data["environment_level"]
                n_r = scenario_data["n_red"]
                n_a = scenario_data["n_amber"]
                emoji = _ENV_EMOJI.get(env_level, "⚪")
                insight_lines.append(
                    f"**Signal environment: {emoji} {env_level}** — "
                    f"{n_r} red signal{'s' if n_r != 1 else ''}, "
                    f"{n_a} amber signal{'s' if n_a != 1 else ''} across the 11 market indicators."
                )

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
            _kms = [
                ("Hist. Vol",      _pct(hist_vol, sign=False),
                 "Full-period annualised volatility from historical daily returns. Constant-weight estimate over the selected period."),
                ("GARCH Vol",      _pct(garch_vol, sign=False),
                 "Forward-looking volatility from GARCH(1,1) — weights recent moves more heavily. Falls back to EWMA if data is insufficient or fit is non-stationary."),
                ("VaR 95% (day)",  _pct(var_95_hist),
                 "Worst daily loss in 95% of trading days (historical). On roughly 1 in 20 days, losses exceeded this threshold."),
                ("CVaR 95% (day)", _pct(cvar_95_hist),
                 "Average loss on the worst 5% of days (Expected Shortfall). More severe than VaR and better captures tail risk."),
                ("VaR 95% (mo.)",  _pct(var_monthly),
                 "Daily VaR 95% scaled to a monthly horizon using the i.i.d. approximation (×√21). Directional estimate only."),
                ("Skewness",       _fmt(skewness),
                 "Asymmetry of the return distribution. Negative skew means more frequent large losses than gains."),
            ]
            for i in range(0, len(_kms), 2):
                _row = _kms[i:i + 2]
                _cols = st.columns(len(_row))
                for _col, (_lbl, _val, _hlp) in zip(_cols, _row):
                    with _col:
                        st.metric(label=_lbl, value=_val, help=_hlp)

    st.markdown("---")

    # ── Risk Preparedness Panel ────────────────────────────────────────────────
    _render_preparedness_panel(signals)

    st.markdown("---")

    # ── Charts ─────────────────────────────────────────────────────────────────
    st.markdown("##### Charts")

    from components.charts import (
        garch_volatility_chart,
        monte_carlo_fan_chart,
        signal_scenario_chart,
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

    # Monte Carlo fan | Signal-based sensitivity analysis
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
        if scenario_data is not None:
            st.markdown("##### Signal-Based Sensitivity Analysis")
            st.caption(
                "Estimated 1-month portfolio loss under three stress levels, derived from "
                "current GARCH-implied volatility scaled by signal environment severity. "
                "The highlighted bar reflects the current signal environment. "
                "These are model estimates, not forecasts."
            )
            st.plotly_chart(
                signal_scenario_chart(scenario_data),
                use_container_width=True,
                key="_det_q3_scenarios",
            )
        else:
            st.info("Signal scenario data not available — GARCH volatility required.")

