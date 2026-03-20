"""pages/guide.py

Screen 4 — Guide.

Responsibilities:
- Section 1: How to use the app (input → dashboard → more details flow).
- Section 2: What each quadrant tells you (4 brief explanatory paragraphs).
- Section 3: Key limitations — estimation error, historical data, not advice.
- Version date displayed.

Metric-level definitions are available via the ? icon on every KPI tile.
This guide covers the app flow and interpretive context, not formula detail.

Implemented in: Session 14. Redesigned Stage C: tables removed, how-to focus.
"""

import streamlit as st

GUIDE_VERSION = "v1.1 — 2026-03"


def render() -> None:
    """Render the Guide screen."""
    st.title("How to Use PortfolioIQ")
    st.caption(GUIDE_VERSION)

    st.markdown(
        "PortfolioIQ analyses your equity portfolio across four analytical layers — "
        "Descriptive, Diagnostic, Predictive, and Prescriptive. "
        "Every number describes **historical data** or **model output under stated assumptions**. "
        "Nothing here is a prediction or investment recommendation. "
        "Hover the **?** icon on any metric tile for a plain-language definition."
    )

    st.markdown("---")

    # ── Section 1: How to Use ──────────────────────────────────────────────────
    st.markdown("#### 1 — How to Use")

    st.markdown(
        "**Step 1 — Input your portfolio.**  \n"
        "Go to **INPUT** in the sidebar. Enter each holding as a ticker symbol and a "
        "dollar amount. Select a benchmark (default: SPY) and a lookback period "
        "(default: 3 years). Check the disclaimer, then click **Analyse Portfolio**. "
        "The app fetches price data, computes all analytics, and navigates you to the Dashboard."
    )
    st.markdown(
        "**Step 2 — Read the Dashboard.**  \n"
        "The Dashboard shows your portfolio across four quadrants arranged in a 2×2 grid. "
        "Each quadrant has a primary chart, key metric tiles with ? tooltips, and a "
        "colour-coded status flag. The Portfolio Health bar above the grid gives a "
        "one-line status for six dimensions of portfolio health."
    )
    st.markdown(
        "**Step 3 — Explore More Details.**  \n"
        "Click **More Details →** on any quadrant to open its deep-dive screen. "
        "Each details screen shows an At-a-Glance insight block, additional charts, "
        "and (for Q3) the full 11-signal Risk Preparedness Panel. "
        "Use the **← Back to Dashboard** button or click **DASHBOARD** in the sidebar to return."
    )
    st.markdown(
        "**Step 4 — Adjust Settings.**  \n"
        "Go to **SETTINGS** to change the VaR confidence level, Monte Carlo horizon, "
        "weight bounds, or drift threshold. Clicking **Save and Recompute** re-runs "
        "only the affected analytics layers — no need to re-fetch price data."
    )

    st.markdown("---")

    # ── Section 2: What Each Quadrant Tells You ────────────────────────────────
    st.markdown("#### 2 — What Each Quadrant Tells You")

    st.markdown("**Q1 — Performance (Descriptive)**")
    st.markdown(
        "Answers: *what has this portfolio actually done?* "
        "CAGR measures the smoothed annual growth rate. Sharpe ratio measures return "
        "earned per unit of total risk — above 1.0 is strong, below 0 means "
        "underperforming cash on a risk-adjusted basis. Max Drawdown shows the worst "
        "peak-to-trough loss experienced. The cumulative return chart compares the "
        "portfolio against the selected benchmark over the full period. "
        "All statistics are backward-looking and sensitive to the period chosen."
    )

    st.markdown("**Q2 — Risk Factors (Diagnostic)**")
    st.markdown(
        "Answers: *why did the portfolio behave that way?* "
        "The correlation heatmap shows how much holdings move together — high "
        "correlation reduces real diversification. Effective N measures the number of "
        "truly independent positions (lower than your actual count means concentration). "
        "The Diversification Ratio confirms whether combining assets is actually reducing "
        "portfolio volatility. The drawdown chart shows the full history of underwater "
        "periods. Correlations tend to spike toward 1.0 during market stress — "
        "precisely when diversification is most needed."
    )

    st.markdown("**Q3 — Risk Outlook (Predictive)**")
    st.markdown(
        "Answers: *what could happen from here?* "
        "Historical VaR and CVaR measure tail risk from past returns. GARCH volatility "
        "is a forward-looking estimate that weights recent market moves more heavily. "
        "The Monte Carlo fan shows the spread of 1,000 simulated portfolio paths — "
        "it is a range of possibilities, not a forecast. The Signal-Based Sensitivity "
        "Analysis shows estimated portfolio losses under three stress levels derived from "
        "current GARCH volatility, calibrated to the current market signal environment. "
        "The Market Environment Signals panel shows 11 indicators (VIX, credit spreads, "
        "yield curve, etc.) fetched fresh at each session from end-of-day data — "
        "these are awareness indicators, not buy or sell signals."
    )

    st.markdown("**Q4 — Optimization (Prescriptive)**")
    st.markdown(
        "Answers: *what does the model suggest as an alternative allocation?* "
        "The efficient frontier shows portfolios offering the highest return for each "
        "level of risk, given your tickers and weight constraints. Three optimizer "
        "portfolios are shown: Max Sharpe (best risk-adjusted return), Min Variance "
        "(lowest achievable volatility), and Risk Parity (equal risk contribution from "
        "each holding). The weight delta table shows how much each optimizer would shift "
        "each position relative to your current allocation. "
        "**Important:** optimizer outputs are highly sensitive to expected return estimates "
        "derived from historical data. Small estimation errors can produce very different "
        "frontier shapes. Treat these as illustrations of the opportunity structure, "
        "not rebalancing instructions."
    )

    st.markdown("---")

    # ── Section 3: Key Limitations ─────────────────────────────────────────────
    st.markdown("#### 3 — Key Limitations")

    st.markdown(
        "**All metrics are historical.** Every statistic is computed from a finite "
        "sample of past returns. Financial markets are constantly evolving — distributions, "
        "correlations, and volatility regimes shift over time. A metric that accurately "
        "described the portfolio over the past three years may not hold over the next three."
    )
    st.markdown(
        "**Period and benchmark sensitivity.** CAGR, Sharpe, drawdown, beta, alpha, "
        "and Information Ratio all change meaningfully depending on the start/end dates "
        "and benchmark selected. A 3-year window including 2022 looks very different "
        "from one that excludes it. An equity portfolio benchmarked to bonds will show "
        "misleadingly high alpha."
    )
    st.markdown(
        "**Optimizer estimation error.** Mean-variance optimization amplifies errors "
        "in expected return inputs. Small changes in return estimates can shift the "
        "efficient frontier dramatically and produce corner-weight solutions. "
        "The optimizer outputs on Q4 should be interpreted as structural insights "
        "(risk-return trade-offs, diversification potential) rather than prescriptions."
    )
    st.markdown(
        "**Correlation instability.** Pairwise correlations are estimated from the "
        "selected historical period. During market stress, correlations typically spike "
        "toward 1.0 — diversification benefits collapse when they are most needed. "
        "The rolling correlation chart on Q2 details shows how correlations have shifted "
        "over time."
    )

    st.markdown("---")
    st.caption(
        "_PortfolioIQ is an educational and analytical tool. It does not constitute "
        "investment advice or a regulated financial service. Always consult a qualified "
        "financial adviser before making investment decisions._"
    )
    st.caption(f"PortfolioIQ — {GUIDE_VERSION}")
