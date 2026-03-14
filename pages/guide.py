"""pages/guide.py

Screen 4 — Guide.

Responsibilities:
- Introductory paragraph: conditional characterization framing (not prediction).
- Five sections with four-column tables:
    Section 1: Performance (Descriptive) — CAGR, Sharpe, Sortino, etc.
    Section 2: Risk Factors (Diagnostic) — correlation, drawdown, HHI, etc.
    Section 3: Risk Outlook (Predictive) — VaR, CVaR, GARCH, Monte Carlo.
    Section 4: Optimization (Prescriptive) — frontier, max Sharpe, estimation error.
    Section 5: Leading Indicators & Preparedness Signals — all 11 signals.
- Closing statement on signal limitations.
- Version date displayed.
- Four columns per row: Metric, Formula/Method, What it tells you, Key assumption/limitation.

This is a living document. Version date updated whenever content changes.
Implemented in: Session 14.
"""

import streamlit as st

GUIDE_VERSION = "v1.0 — 2026-03"


def render() -> None:
    """Render the Guide screen."""
    st.title("Guide")
    st.caption(GUIDE_VERSION)
    st.info("Session 14 — not yet implemented.")
