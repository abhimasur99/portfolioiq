"""screens/details_q4.py

Screen 3d — Q4 More Details: Optimization (Prescriptive).

Responsibilities:
- Back to Dashboard button (always first element).
- Estimation error warning prominently displayed at top.
- Plain-language insight block.
- Extended charts: efficient frontier with all three optimizer portfolios
  marked, CML, current portfolio dot; weight delta bar chart.
- Interactive weight delta table for all three optimizers.
- Complete metric table.
- Explain Numbers panel available.
- Language throughout: conditional ("the optimizer identifies..."),
  never prescriptive ("you should...").

Accessed exclusively via the More Details button on Q4 of the dashboard.
Never appears in the nav bar.

Implemented in: Session 13.
"""

import numpy as np
import pandas as pd
import streamlit as st

from assets.config import (
    SK_ANALYTICS,
    SK_OPTIMIZATION,
    SK_PERFORMANCE,
    SK_PORT_RETURNS,
    SK_RISK_FREE_RATE,
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
    """Render the Q4 (Optimization) More Details screen."""
    analytics    = st.session_state.get(SK_ANALYTICS, {})
    opt          = analytics.get(SK_OPTIMIZATION, {})
    perf         = analytics.get(SK_PERFORMANCE, {})
    port_ret     = st.session_state.get(SK_PORT_RETURNS, pd.Series(dtype=float))
    risk_free    = st.session_state.get(SK_RISK_FREE_RATE, 0.0)
    tickers      = st.session_state.get(SK_TICKERS, [])

    # Pull optimizer outputs
    frontier_vols       = opt.get("frontier_vols", [])
    frontier_returns    = opt.get("frontier_returns", [])
    ms_weights          = opt.get("max_sharpe_weights")
    ms_return           = opt.get("max_sharpe_return")
    ms_vol              = opt.get("max_sharpe_vol")
    ms_ratio            = opt.get("max_sharpe_ratio")
    mv_weights          = opt.get("min_var_weights")
    mv_return           = opt.get("min_var_return")
    mv_vol              = opt.get("min_var_vol")
    mv_ratio            = (float(mv_return) - risk_free * 252) / float(mv_vol) if (
        mv_return is not None and mv_vol is not None and mv_vol > 1e-10
    ) else None
    rp_weights          = opt.get("risk_parity_weights")
    rp_return           = opt.get("risk_parity_return")
    rp_vol              = opt.get("risk_parity_vol")
    rp_ratio            = (float(rp_return) - risk_free * 252) / float(rp_vol) if (
        rp_return is not None and rp_vol is not None and rp_vol > 1e-10
    ) else None
    cml_slope           = opt.get("cml_slope")
    weight_delta_table  = opt.get("weight_delta_table", pd.DataFrame())
    converged           = opt.get("optimizer_converged", True)

    # Current portfolio position for frontier chart
    current_vol    = perf.get("volatility")
    current_return = perf.get("cagr")
    current_sharpe = perf.get("sharpe")
    rf_ann         = float(risk_free) * 252

    # ── Title ──────────────────────────────────────────────────────────────────
    st.title("Optimization — Deep Dive")
    st.caption("Prescriptive analytics: efficient frontier, optimizer portfolios, and weight deltas.")

    # ── Optimizer assumptions notice ───────────────────────────────────────────
    st.warning(
        "**Optimizer Assumptions — Read Before Interpreting.**  \n"
        "Mean-variance optimization is highly sensitive to the expected return inputs, "
        "which are estimated from historical data and carry substantial uncertainty. "
        "Small changes in return estimates can produce very different frontier shapes and "
        "optimizer weights. The portfolios identified below are historically optimal under "
        "the assumptions of the model — they are **not investment recommendations**.  \n"
        "Use these outputs to understand the *structure* of the opportunity set (risk-return "
        "trade-offs, diversification potential, weight concentrations) rather than as a "
        "rebalancing prescription. Consult a qualified financial adviser before making "
        "investment decisions."
    )

    # ── Insight block ──────────────────────────────────────────────────────────
    with st.container():
        left_col, right_col = st.columns([3, 2], gap="large")
        with left_col:
            st.markdown("##### At a Glance")
            insight_lines = []

            if not converged:
                insight_lines.append(
                    "**One or more optimizers did not fully converge.** Results are the best "
                    "feasible solution found but may not be globally optimal. "
                    "Treat weight outputs with extra caution."
                )

            if current_sharpe is not None and ms_ratio is not None:
                gap = ms_ratio - current_sharpe
                if gap > 0.3:
                    insight_lines.append(
                        f"The current portfolio's Sharpe ratio ({_fmt(current_sharpe)}) is "
                        f"**{_fmt(gap)} below** the Max Sharpe frontier portfolio "
                        f"({_fmt(ms_ratio)}), suggesting meaningful room to improve "
                        "risk-adjusted return within these tickers and constraints — "
                        "subject to estimation uncertainty."
                    )
                elif gap > 0:
                    insight_lines.append(
                        f"The current portfolio's Sharpe ({_fmt(current_sharpe)}) is close to "
                        f"the Max Sharpe portfolio ({_fmt(ms_ratio)}) — the current allocation "
                        "is near-efficient given these tickers."
                    )
                else:
                    insight_lines.append(
                        f"The current portfolio's Sharpe ({_fmt(current_sharpe)}) exceeds the "
                        f"Max Sharpe output ({_fmt(ms_ratio)}). This can occur when the "
                        "optimizer's expected return estimates differ from realised returns, "
                        "or when the current portfolio lies outside the constrained frontier."
                    )

            if mv_vol is not None and current_vol is not None:
                vol_saving = current_vol - mv_vol
                if vol_saving > 0.02:
                    insight_lines.append(
                        f"The Min Variance portfolio ({_pct(mv_vol, sign=False)} vol) could "
                        f"theoretically reduce annualised volatility by ~{_pct(vol_saving, sign=False)} "
                        "vs the current allocation — if the historical covariance structure persists."
                    )

            if rp_vol is not None:
                insight_lines.append(
                    f"The Risk Parity portfolio ({_pct(rp_vol, sign=False)} vol, "
                    f"Sharpe {_fmt(rp_ratio)}) targets equal risk contribution from each holding, "
                    "typically overweighting lower-volatility assets."
                )

            for line in insight_lines:
                st.markdown(f"- {line}")

            st.caption(
                "_All optimizer outputs use annualised expected returns and covariance estimated "
                "from the historical period. Estimation error in expected returns is the "
                "dominant source of optimizer instability. See the Guide for details._"
            )

        with right_col:
            st.markdown("##### Optimizer Comparison")
            comp = {
                "Portfolio":  ["Current", "Max Sharpe", "Min Variance", "Risk Parity"],
                "Ann. Return": [_pct(current_return), _pct(ms_return),
                                _pct(mv_return), _pct(rp_return)],
                "Ann. Vol":   [_pct(current_vol, sign=False), _pct(ms_vol, sign=False),
                                _pct(mv_vol, sign=False), _pct(rp_vol, sign=False)],
                "Sharpe":     [_fmt(current_sharpe), _fmt(ms_ratio),
                               _fmt(mv_ratio), _fmt(rp_ratio)],
            }
            st.dataframe(pd.DataFrame(comp), hide_index=True, use_container_width=True)

    st.markdown("---")

    # ── Charts ─────────────────────────────────────────────────────────────────
    st.markdown("##### Charts")

    from components.charts import efficient_frontier_chart, current_vs_optimal_chart

    # Efficient frontier (full width) — requires all frontier + optimizer data
    if frontier_vols and frontier_returns and ms_vol is not None and mv_vol is not None:
        st.plotly_chart(
            efficient_frontier_chart(
                frontier_vols=frontier_vols,
                frontier_returns=frontier_returns,
                current_vol=current_vol if current_vol is not None else 0.0,
                current_return=current_return if current_return is not None else 0.0,
                max_sharpe_vol=ms_vol,
                max_sharpe_return=ms_return,
                min_var_vol=mv_vol,
                min_var_return=mv_return,
                risk_parity_vol=rp_vol if rp_vol is not None else mv_vol,
                risk_parity_return=rp_return if rp_return is not None else mv_return,
                risk_free_rate=rf_ann,
            ),
            use_container_width=True,
            key="_det_q4_frontier",
        )
    else:
        st.info("Efficient frontier data not available.")

    # Current vs optimal bar chart (full width)
    if not weight_delta_table.empty:
        st.plotly_chart(
            current_vs_optimal_chart(weight_delta_table),
            use_container_width=True,
            key="_det_q4_delta",
        )
    else:
        st.info("Weight delta data not available.")

    st.markdown("---")

    # ── Weight delta table ─────────────────────────────────────────────────────
    st.markdown("##### Weight Comparison by Ticker")
    st.caption(
        "Δ columns show the change from current weights the optimizer identifies as optimal. "
        "Positive Δ means the optimizer would overweight relative to your current allocation; "
        "negative means underweight. These are model outputs, not trade instructions."
    )

    if not weight_delta_table.empty:
        # Format for display
        display_rows = []
        for ticker, row in weight_delta_table.iterrows():
            display_rows.append({
                "Ticker":          ticker,
                "Current":         f"{row['current'] * 100:.1f}%",
                "Max Sharpe":      f"{row['max_sharpe'] * 100:.1f}%",
                "Δ Max Sharpe":    f"{row['max_sharpe_delta'] * 100:+.1f}%",
                "Min Variance":    f"{row['min_var'] * 100:.1f}%",
                "Δ Min Var":       f"{row['min_var_delta'] * 100:+.1f}%",
                "Risk Parity":     f"{row['risk_parity'] * 100:.1f}%",
                "Δ Risk Parity":   f"{row['risk_parity_delta'] * 100:+.1f}%",
            })
        st.dataframe(
            pd.DataFrame(display_rows),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Weight delta table not available.")

