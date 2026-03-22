"""components/dashboard_quad.py

Reusable dashboard quadrant component.

Renders one of the four analytical quadrants on the main dashboard.
Each quadrant has a consistent layout:
- Quadrant header (title, subtitle).
- Primary chart (compact height, use_container_width=True).
- Row of KPI metric tiles with inline ? tooltips (help= parameter).
- Contextual flag (emoji badge).
- One action button: "More Details".

The More Details button sets a session state key to route to the correct
details page and calls st.rerun().

Implemented in: Session 10. Updated Stage B: ? tooltips, removed Explain Numbers.
"""

import streamlit as st
import plotly.graph_objects as go

from assets.config import COLOR_GREEN, COLOR_AMBER, COLOR_RED

_SK_DETAILS = "_dashboard_details"
_CHART_HEIGHT = 260
_FLAG_COLOR = {"green": COLOR_GREEN, "amber": COLOR_AMBER, "red": COLOR_RED}
_FLAG_EMOJI = {"green": "🟢", "amber": "🟡", "red": "🔴"}


def render_quadrant(
    quadrant_id: str,
    title: str,
    chart_fig: go.Figure,
    kpis: list,
    flag: dict | None,
    details_page: str,
) -> None:
    hdr_col, badge_col = st.columns([5, 2])
    with hdr_col:
        st.markdown(f"##### {title}")
    with badge_col:
        if flag:
            status = flag.get("status", "green")
            emoji = _FLAG_EMOJI.get(status, "⚪")
            color = _FLAG_COLOR.get(status, COLOR_GREEN)
            st.markdown(
                f'<div style="text-align:right;font-size:0.8rem;color:{color};">'
                f'{emoji}</div>',
                unsafe_allow_html=True,
            )

    chart_fig.update_layout(height=_CHART_HEIGHT, margin=dict(l=40, r=20, t=30, b=30))
    st.plotly_chart(chart_fig, use_container_width=True, key=f"_chart_{quadrant_id}")

    if kpis:
        kpi_cols = st.columns(len(kpis))
        for col, kpi in zip(kpi_cols, kpis):
            with col:
                st.metric(
                    label=kpi.get("label", ""),
                    value=kpi.get("value", "---"),
                    delta=kpi.get("delta"),
                    delta_color=kpi.get("delta_color", "normal"),
                    help=kpi.get("help"),
                )

    if st.button("More Details →", key=f"_btn_det_{quadrant_id}", type="primary", use_container_width=True):
        st.session_state[_SK_DETAILS] = details_page
        st.rerun()

    st.markdown("---")
