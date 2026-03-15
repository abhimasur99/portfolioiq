"""pages/details_q1.py

Screen 3a — Q1 More Details: Performance (Descriptive).

Responsibilities:
- Back to Dashboard button (always first element).
- Plain-language insight block at top.
- Full 12-metric table with every number explained in context.
- Four charts: cumulative return, return distribution (with VaR/CVaR),
  rolling Sharpe, rolling Beta.
- Inline Explain Numbers panel.

Accessed exclusively via the More Details button on Q1 of the dashboard.
Never appears in the nav bar.

Implemented in: Session 11.
"""

import pandas as pd
import streamlit as st

from assets.config import (
    SK_ANALYTICS,
    SK_BENCH_RETURNS,
    SK_BENCHMARK,
    SK_PERFORMANCE,
    SK_PORT_RETURNS,
    SK_RISK_FACTORS,
    SK_RISK_OUTLOOK,
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
    """Render the Q1 (Performance) More Details screen."""
    analytics   = st.session_state.get(SK_ANALYTICS, {})
    perf        = analytics.get(SK_PERFORMANCE, {})
    rf          = analytics.get(SK_RISK_FACTORS, {})
    ro          = analytics.get(SK_RISK_OUTLOOK, {})
    port_ret    = st.session_state.get(SK_PORT_RETURNS, pd.Series(dtype=float))
    bench_ret   = st.session_state.get(SK_BENCH_RETURNS, pd.Series(dtype=float))
    benchmark   = st.session_state.get(SK_BENCHMARK, "Benchmark")

    # Pull values used throughout
    cagr      = perf.get("cagr")
    sharpe    = perf.get("sharpe")
    sortino   = perf.get("sortino")
    treynor   = perf.get("treynor")
    info_r    = perf.get("information_ratio")
    alpha     = perf.get("alpha")
    beta      = perf.get("beta")
    r_sq      = perf.get("r_squared")
    vol       = perf.get("volatility")
    best_mo   = perf.get("best_month")
    worst_mo  = perf.get("worst_month")
    best_yr   = perf.get("best_year")
    worst_yr  = perf.get("worst_year")
    max_dd    = rf.get("max_drawdown")
    calmar    = rf.get("calmar")
    var_95    = ro.get("var_95_hist")
    cvar_95   = ro.get("cvar_95_hist")
    rolling_sharpe = perf.get("rolling_sharpe", pd.Series(dtype=float))
    rolling_beta   = perf.get("rolling_beta", pd.Series(dtype=float))

    # ── Title ──────────────────────────────────────────────────────────────────
    st.title("Performance — Deep Dive")
    st.caption("Descriptive analytics: backward-looking performance attribution.")

    # ── Insight block ──────────────────────────────────────────────────────────
    with st.container():
        left_col, right_col = st.columns([3, 2], gap="large")
        with left_col:
            st.markdown("##### At a Glance")
            insight_lines = []

            if cagr is not None:
                cagr_str = _pct(cagr)
                if cagr > 0:
                    insight_lines.append(
                        f"The portfolio compounded at **{cagr_str} per year** over the "
                        "selected period."
                    )
                else:
                    insight_lines.append(
                        f"The portfolio **lost value** at a rate of **{cagr_str} per year** "
                        "over the selected period."
                    )

            if sharpe is not None:
                if sharpe >= 1.0:
                    insight_lines.append(
                        f"A **Sharpe ratio of {_fmt(sharpe)}** indicates strong risk-adjusted "
                        "returns — for each unit of risk, the portfolio earned meaningful excess "
                        "return above the risk-free rate."
                    )
                elif sharpe >= 0:
                    insight_lines.append(
                        f"A **Sharpe ratio of {_fmt(sharpe)}** is below 1.0, meaning the "
                        "return-per-unit-of-risk is modest. Returns exceeded the risk-free rate "
                        "but may not compensate for volatility."
                    )
                else:
                    insight_lines.append(
                        f"A **negative Sharpe ratio ({_fmt(sharpe)})** means the portfolio "
                        "underperformed the risk-free rate on a volatility-adjusted basis."
                    )

            if max_dd is not None:
                insight_lines.append(
                    f"The deepest drawdown was **{_pct(max_dd)}** — the worst peak-to-trough "
                    "decline an investor would have experienced holding through the full period."
                )

            if best_yr is not None and worst_yr is not None:
                insight_lines.append(
                    f"Best calendar year: **{_pct(best_yr)}**. "
                    f"Worst calendar year: **{_pct(worst_yr)}**."
                )

            for line in insight_lines:
                st.markdown(f"- {line}")

            st.caption(
                "_All statistics are calculated from historical price data over the selected "
                "period. Past performance does not predict future results._"
            )

        with right_col:
            st.markdown("##### Key Metrics")
            summary = {
                "Metric": ["CAGR", "Ann. Volatility", "Sharpe Ratio", "Max Drawdown",
                            "Calmar Ratio", "Beta"],
                "Value":  [_pct(cagr), _pct(vol, sign=False), _fmt(sharpe),
                            _pct(max_dd), _fmt(calmar), _fmt(beta)],
            }
            st.dataframe(pd.DataFrame(summary), hide_index=True, use_container_width=True)

    st.markdown("---")

    # ── Charts ─────────────────────────────────────────────────────────────────
    st.markdown("##### Charts")

    from components.charts import (
        cumulative_return_chart,
        return_distribution_chart,
        rolling_sharpe_chart,
        rolling_beta_chart,
    )

    # Row 1: cumulative return (full width)
    st.plotly_chart(
        cumulative_return_chart(port_ret, bench_ret, benchmark_label=benchmark),
        use_container_width=True,
        key="_det_q1_cumret",
    )

    # Row 2: distribution | rolling Sharpe
    ch_left, ch_right = st.columns(2)
    with ch_left:
        st.plotly_chart(
            return_distribution_chart(
                port_ret,
                var_95=var_95 if var_95 is not None else 0.0,
                cvar_95=cvar_95 if cvar_95 is not None else 0.0,
            ),
            use_container_width=True,
            key="_det_q1_dist",
        )
    with ch_right:
        st.plotly_chart(
            rolling_sharpe_chart(rolling_sharpe),
            use_container_width=True,
            key="_det_q1_rsharpe",
        )

    # Row 3: rolling beta (full width)
    st.plotly_chart(
        rolling_beta_chart(rolling_beta),
        use_container_width=True,
        key="_det_q1_rbeta",
    )

