"""components/explain_panel.py

Explain Numbers overlay panel.

Opens as an inline container on the dashboard and all More Details screens
without navigating away from the current page. Explains specific numbers in
plain language tied to the user's actual holdings.

Implemented in: Session 10.
"""

import streamlit as st


def render_explain_panel(quadrant_id: str, analytics: dict) -> None:
    """Render the Explain Numbers overlay for a given quadrant.

    Args:
        quadrant_id: One of "q1", "q2", "q3", "q4".
        analytics: The full analytics results dict from session state.
    """
    perf = analytics.get("performance", {})
    rf   = analytics.get("risk_factors", {})
    ro   = analytics.get("risk_outlook", {})
    opt  = analytics.get("optimization", {})

    st.markdown("**What do these numbers mean?**")

    if quadrant_id == "q1":
        cagr   = perf.get("cagr", None)
        sharpe = perf.get("sharpe", None)
        mdd    = perf.get("max_drawdown", None)
        st.markdown(
            f"**CAGR** ({_pct(cagr)}) is the compound annual growth rate — "
            "the smoothed annual return if the portfolio grew at a constant rate.\n\n"
            f"**Sharpe Ratio** ({_fmt(sharpe, 2)}) measures return earned per unit of risk "
            "(daily return minus risk-free rate, divided by volatility). "
            "Above 1.0 is considered good; below 0 means the portfolio underperformed "
            "the risk-free rate on a risk-adjusted basis.\n\n"
            f"**Max Drawdown** ({_pct(mdd)}) is the largest peak-to-trough decline in "
            "portfolio value. It captures the worst-case loss an investor would have experienced "
            "holding through the full period.\n\n"
            "_These are backward-looking statistics based on the selected historical period. "
            "Past performance does not predict future results._"
        )

    elif quadrant_id == "q2":
        eff_n  = rf.get("effective_n", None)
        hhi    = rf.get("hhi", None)
        dr     = rf.get("diversification_ratio", None)
        st.markdown(
            f"**Effective N** ({_fmt(eff_n, 1)}) estimates the number of truly independent "
            "positions in the portfolio. A portfolio with 10 holdings but concentrated in "
            "correlated assets may have an Effective N of only 3–4.\n\n"
            f"**HHI** ({_fmt(hhi, 3)}) (Herfindahl-Hirschman Index) ranges from 1/N (perfectly "
            "equal weights) to 1.0 (single holding). Lower is more diversified.\n\n"
            f"**Diversification Ratio** ({_fmt(dr, 2)}) is the ratio of weighted-average "
            "individual volatilities to portfolio volatility. Values above 1.0 confirm that "
            "diversification is reducing total risk; higher is better.\n\n"
            "_Correlation estimates shift over time, especially during market stress, when "
            "correlations tend to spike toward 1.0 (the wrong moment to be concentrated)._"
        )

    elif quadrant_id == "q3":
        var95  = ro.get("var_95_hist", None)
        cvar95 = ro.get("cvar_95_hist", None)
        hvol   = ro.get("hist_vol", None)
        gvol   = ro.get("garch_vol", None)
        st.markdown(
            f"**VaR 95%** ({_pct(var95)}) means that in the worst 5% of days historically, "
            "the portfolio lost at least this much. It is a threshold, not an average loss.\n\n"
            f"**CVaR 95%** ({_pct(cvar95)}) is the average loss on those worst 5% of days — "
            "the expected shortfall beyond the VaR threshold. It is always worse than VaR.\n\n"
            f"**Historical Vol** ({_pct(hvol)}) annualises the daily standard deviation "
            "of returns using sqrt(252). "
            f"**GARCH Vol** ({_pct(gvol)}) is the model-implied current conditional "
            "volatility — it updates faster than historical vol during stress periods.\n\n"
            "_VaR and CVaR assume the return distribution is stable. Tail events in real "
            "markets are more frequent and larger than historical data suggests._"
        )

    elif quadrant_id == "q4":
        ms_ret = opt.get("max_sharpe_return", None)
        ms_vol = opt.get("max_sharpe_vol", None)
        ms_r   = opt.get("max_sharpe_ratio", None)
        mv_vol = opt.get("min_var_vol", None)
        st.markdown(
            f"**Max Sharpe Portfolio** achieves the highest risk-adjusted return "
            f"({_pct(ms_ret)} ann. return, {_pct(ms_vol)} vol, Sharpe {_fmt(ms_r, 2)}) "
            "given your tickers and weight constraints. It sits on the efficient frontier "
            "at the tangency point with the Capital Market Line.\n\n"
            f"**Min Variance Portfolio** ({_pct(mv_vol)} vol) minimises total portfolio "
            "volatility regardless of return. Useful for capital preservation objectives.\n\n"
            "**Risk Parity** targets equal risk contribution from each asset, "
            "typically overweighting lower-volatility assets relative to their market cap.\n\n"
            "_Optimizer outputs are identified as historically optimal under specific "
            "assumptions. They are NOT recommendations. Estimation error in expected returns "
            "can significantly affect frontier shape — see the Guide for details._"
        )

    else:
        st.info("No explanation available for this quadrant.")

    st.caption("→ [Guide](/guide) for full methodology details.")


# ── Formatting helpers ─────────────────────────────────────────────────────────

def _pct(val, decimals: int = 1) -> str:
    if val is None:
        return "n/a"
    try:
        return f"{float(val)*100:+.{decimals}f}%"
    except (TypeError, ValueError):
        return "n/a"


def _fmt(val, decimals: int = 2) -> str:
    if val is None:
        return "n/a"
    try:
        return f"{float(val):.{decimals}f}"
    except (TypeError, ValueError):
        return "n/a"
