"""pages/details_q1.py

Screen 3a — Q1 More Details: Performance (Descriptive).

Responsibilities:
- Back to Dashboard button (always first element).
- Plain-language insight block at top.
- Extended chart grid (rolling Sharpe, rolling beta, return distribution,
  calendar returns heatmap, cumulative return extended).
- Complete metric table with every number explained in context.
- Explain Numbers panel available.

Accessed exclusively via the More Details button on Q1 of the dashboard.
Never appears in the nav bar.

Implemented in: Session 11.
"""

import streamlit as st


def render() -> None:
    """Render the Q1 (Performance) More Details screen."""
    if st.button("← Back to Dashboard"):
        st.session_state["_page_override"] = "DASHBOARD"
        st.rerun()
    st.title("Performance — More Details")
    st.info("Session 11 — not yet implemented.")
