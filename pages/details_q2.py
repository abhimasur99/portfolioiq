"""pages/details_q2.py

Screen 3b — Q2 More Details: Risk Factors (Diagnostic).

Responsibilities:
- Back to Dashboard button (always first element).
- Plain-language insight block at top.
- Extended charts: rolling 60-day correlation, full correlation heatmap,
  drawdown chart, sector weight bar chart, diversification metrics.
- Complete metric table with every number explained.
- Explain Numbers panel available.

Accessed exclusively via the More Details button on Q2 of the dashboard.
Never appears in the nav bar.

Implemented in: Session 11.
"""

import streamlit as st


def render() -> None:
    """Render the Q2 (Risk Factors) More Details screen."""
    if st.button("← Back to Dashboard"):
        st.session_state["_page_override"] = "DASHBOARD"
        st.rerun()
    st.title("Risk Factors — More Details")
    st.info("Session 11 — not yet implemented.")
