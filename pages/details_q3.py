"""pages/details_q3.py

Screen 3c — Q3 More Details: Risk Outlook (Predictive).

Responsibilities:
- Back to Dashboard button (always first element).
- Plain-language insight block at top.
- Live Risk Preparedness Panel: all 11 forward-looking signals, each with
  label, current value, status badge, and one-sentence interpretation.
  Disclaimer: signals are awareness tools, not predictions.
- Extended charts: GARCH volatility vs historical, VaR comparison chart,
  Monte Carlo fan chart, stress test bar chart.
- Complete metric table.
- Explain Numbers panel available.

Accessed exclusively via the More Details button on Q3 of the dashboard.
Never appears in the nav bar.

Implemented in: Session 12.
"""

import streamlit as st


def render() -> None:
    """Render the Q3 (Risk Outlook) More Details screen."""
    if st.button("← Back to Dashboard"):
        st.session_state["_page_override"] = "DASHBOARD"
        st.rerun()
    st.title("Risk Outlook — More Details")
    st.info("Session 12 — not yet implemented.")
