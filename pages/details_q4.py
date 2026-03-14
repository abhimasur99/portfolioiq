"""pages/details_q4.py

Screen 3d — Q4 More Details: Optimization (Prescriptive).

Responsibilities:
- Back to Dashboard button (always first element).
- Estimation error warning prominently displayed at top.
- Plain-language insight block.
- Extended charts: efficient frontier with all three optimizer portfolios
  marked, CML, current portfolio dot; weight delta table for all three.
- Complete metric table.
- Explain Numbers panel available.
- Language throughout: conditional ("the optimizer identifies..."),
  never prescriptive ("you should...").

Accessed exclusively via the More Details button on Q4 of the dashboard.
Never appears in the nav bar.

Implemented in: Session 13.
"""

import streamlit as st


def render() -> None:
    """Render the Q4 (Optimization) More Details screen."""
    if st.button("← Back to Dashboard"):
        st.session_state["_page_override"] = "DASHBOARD"
        st.rerun()
    st.title("Optimization — More Details")
    st.info("Session 13 — not yet implemented.")
