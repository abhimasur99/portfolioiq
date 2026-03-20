"""pages/details_q2.py

Screen 3b — Q2 More Details: Risk Factors (Diagnostic).

Responsibilities:
- Back to Dashboard button (always first element).
- Plain-language insight block at top.
- Full metrics table with every number explained.
- Four charts: correlation heatmap, rolling 60-day correlation,
  drawdown chart, sector weights bar chart.
- Inline Explain Numbers panel.

Accessed exclusively via the More Details button on Q2 of the dashboard.
Never appears in the nav bar.

Implemented in: Session 11.
"""

import pandas as pd
import streamlit as st

from analytics.risk_factors import compute_drawdown_series
from assets.config import (
    SK_ANALYTICS,
    SK_BENCH_RETURNS,
    SK_BENCHMARK,
    SK_RISK_FACTORS,
    SK_TICKERS,
    SK_WEIGHTS,
)


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


# ── Page render ─────────────────────────────────────────────────────────────────

def render() -> None:
    """Render the Q2 (Risk Factors) More Details screen."""
    analytics  = st.session_state.get(SK_ANALYTICS, {})
    rf         = analytics.get(SK_RISK_FACTORS, {})
    tickers    = st.session_state.get(SK_TICKERS, [])
    bench_ret  = st.session_state.get(SK_BENCH_RETURNS, pd.Series(dtype=float))
    benchmark  = st.session_state.get(SK_BENCHMARK, "Benchmark")

    # Pull values used throughout
    corr_matrix    = rf.get("corr_matrix")
    rolling_corr   = rf.get("rolling_corr", pd.DataFrame())
    drawdown_series = rf.get("drawdown_series", pd.Series(dtype=float))
    sector_weights = rf.get("sector_weights", {})
    hhi            = rf.get("hhi")
    eff_n          = rf.get("effective_n")
    div_ratio      = rf.get("diversification_ratio")
    max_dd         = rf.get("max_drawdown")
    calmar         = rf.get("calmar")
    recovery_days  = rf.get("recovery_days")
    ulcer_index    = rf.get("ulcer_index")

    # ── Title ──────────────────────────────────────────────────────────────────
    st.title("Risk Factors — Deep Dive")
    st.caption("Diagnostic analytics: portfolio construction quality and risk concentration.")

    # ── Insight block ──────────────────────────────────────────────────────────
    with st.container():
        left_col, right_col = st.columns([3, 2], gap="large")
        with left_col:
            st.markdown("##### At a Glance")
            insight_lines = []
            n_assets = max(len(tickers), 1)

            if eff_n is not None:
                ratio = eff_n / n_assets
                if ratio < 0.4:
                    insight_lines.append(
                        f"**High concentration:** with {n_assets} holdings, the effective number "
                        f"of independent positions is only **{_fmt(eff_n, 1)}** — correlations "
                        "are reducing diversification significantly."
                    )
                elif ratio < 0.7:
                    insight_lines.append(
                        f"**Moderate concentration:** Effective N of **{_fmt(eff_n, 1)}** out of "
                        f"{n_assets} holdings indicates some correlation clustering."
                    )
                else:
                    insight_lines.append(
                        f"**Well diversified:** Effective N of **{_fmt(eff_n, 1)}** out of "
                        f"{n_assets} holdings — positions are relatively independent."
                    )

            if div_ratio is not None:
                if div_ratio > 1.2:
                    insight_lines.append(
                        f"**Diversification Ratio of {_fmt(div_ratio)}** confirms that combining "
                        "these assets meaningfully reduces total portfolio volatility below the "
                        "weighted average of individual vols."
                    )
                elif div_ratio >= 1.0:
                    insight_lines.append(
                        f"**Diversification Ratio of {_fmt(div_ratio)}** shows modest risk "
                        "reduction from combining assets — positions have material correlation."
                    )
                else:
                    insight_lines.append(
                        f"**Diversification Ratio of {_fmt(div_ratio)}** below 1.0 is unusual "
                        "and may indicate estimation issues with the covariance matrix."
                    )

            if max_dd is not None:
                insight_lines.append(
                    f"The portfolio experienced a maximum drawdown of **{_pct(max_dd)}**."
                    + (f" Recovery took **{recovery_days} trading days**." if recovery_days else "")
                )

            for line in insight_lines:
                st.markdown(f"- {line}")

            st.caption(
                "_Correlation and covariance estimates are based on the full historical period "
                "selected. In market stress, correlations typically spike — this is precisely "
                "when diversification benefits disappear._"
            )

        with right_col:
            st.markdown("##### Key Metrics")
            _kms = [
                ("Effective N",  _fmt(eff_n, 1),
                 "Number of truly independent positions after accounting for correlations. Lower than your actual holding count = concentrated."),
                ("HHI",          _fmt(hhi, 3),
                 "Sum of squared weights — equals 1/N for equal weight, 1.0 for a single asset. Lower = more diversified."),
                ("Div. Ratio",   _fmt(div_ratio),
                 "Weighted-average individual volatility ÷ portfolio volatility. Above 1.0 confirms diversification is actively reducing risk."),
                ("Max Drawdown", _pct(max_dd),
                 "Largest peak-to-trough portfolio decline. Worst loss a buy-and-hold investor would have experienced."),
                ("Calmar Ratio", _fmt(calmar),
                 "CAGR ÷ |Max Drawdown|. Higher = better return per unit of drawdown risk absorbed."),
                ("Ulcer Index",  _fmt(ulcer_index),
                 "Root mean square of all drawdown values — penalises both depth and duration of underwater periods. Lower is better."),
            ]
            for i in range(0, len(_kms), 2):
                _row = _kms[i:i + 2]
                _cols = st.columns(len(_row))
                for _col, (_lbl, _val, _hlp) in zip(_cols, _row):
                    with _col:
                        st.metric(label=_lbl, value=_val, help=_hlp)

    st.markdown("---")

    # ── Charts ─────────────────────────────────────────────────────────────────
    st.markdown("##### Charts")

    from components.charts import (
        correlation_heatmap,
        rolling_correlation_chart,
        drawdown_chart,
        sector_weights_chart,
    )

    # Row 1: correlation heatmap | rolling correlation
    ch_left, ch_right = st.columns(2)
    with ch_left:
        if corr_matrix is not None:
            st.plotly_chart(
                correlation_heatmap(corr_matrix),
                use_container_width=True,
                key="_det_q2_heatmap",
            )
        else:
            st.info("Correlation matrix not available.")
    with ch_right:
        if not rolling_corr.empty:
            st.plotly_chart(
                rolling_correlation_chart(rolling_corr),
                use_container_width=True,
                key="_det_q2_rollingcorr",
            )
        else:
            st.info("Rolling correlation data not available.")

    # Row 2: drawdown | sector weights
    bench_drawdown = (
        compute_drawdown_series(bench_ret)
        if not bench_ret.empty
        else None
    )
    ch_left2, ch_right2 = st.columns(2)
    with ch_left2:
        if not drawdown_series.empty:
            st.plotly_chart(
                drawdown_chart(
                    drawdown_series,
                    benchmark_drawdown=bench_drawdown,
                    benchmark_label=benchmark,
                ),
                use_container_width=True,
                key="_det_q2_drawdown",
            )
        else:
            st.info("Drawdown series not available.")
    with ch_right2:
        st.plotly_chart(
            sector_weights_chart(sector_weights),
            use_container_width=True,
            key="_det_q2_sectors",
        )

