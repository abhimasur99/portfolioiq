"""pages/dashboard.py

Screen 2 — Main Dashboard.

Responsibilities:
- Holdings strip (ticker, weight, current price).
- Health bar with six status indicators.
- Ticker tape with live prices across the top (CSS animation).
- Four quadrants in a 2x2 grid, each via dashboard_quad.py component:
    Q1 — Performance (Descriptive)
    Q2 — Risk Factors (Diagnostic)
    Q3 — Risk Outlook (Predictive)
    Q4 — Optimization (Prescriptive)
- Each quadrant: primary chart, 3–4 KPIs, Explain Numbers button,
  More Details button, one contextual flag.
- More Details buttons route to pages/details_q{n}.py.

Does NOT recompute analytics — reads from st.session_state[SK_ANALYTICS].

Implemented in: Session 10.
"""

import streamlit as st


def render() -> None:
    """Render the Main Dashboard screen."""
    st.title("Dashboard")
    st.info("Session 10 — not yet implemented.")
