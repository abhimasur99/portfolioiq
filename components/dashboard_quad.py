"""components/dashboard_quad.py

Reusable dashboard quadrant component.

Renders one of the four analytical quadrants on the main dashboard.
Each quadrant has a consistent layout:
- Quadrant header (title, subtitle).
- Primary chart (compact height, use_container_width=True).
- Row of 3-4 KPI metric tiles.
- Contextual flag (amber/red/green badge with one-line message).
- Two action buttons: "Explain Numbers" and "More Details".

The Explain Numbers button opens the explain_panel overlay without navigating.
The More Details button sets a session state key to route to the correct
details page and calls st.rerun().

Implemented in: Session 10.
"""

import streamlit as st
import plotly.graph_objects as go

from assets.config import COLOR_GREEN, COLOR_AMBER, COLOR_RED, COLOR_TEXT_MUTED

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
    from components.explain_panel import render_explain_panel

    hdr_col, badge_col = st.columns([5, 2])
    with hdr_col:
        st.markdown(f"##### {title}")
    with badge_col:
        if flag:
            status = flag.get("status", "green")
            emoji = _FLAG_EMOJI.get(status, "⚪")
            color = _FLAG_COLOR.get(status, COLOR_TEXT_MUTED)
            msg = flag.get("message", "")
            st.markdown(
                f'<div style="text-align:right;font-size:0.8rem;color:{color};">'
                f'{emoji}&nbsp;{msg}</div>',
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
                )

    toggle_key = f"_explain_open_{quadrant_id}"
    btn_l, btn_r = st.columns(2)
    with btn_l:
        if st.button("Explain Numbers", key=f"_btn_exp_{quadrant_id}", use_container_width=True):
            st.session_state[toggle_key] = not st.session_state.get(toggle_key, False)
    with btn_r:
        if st.button("More Details →", key=f"_btn_det_{quadrant_id}", type="primary", use_container_width=True):
            st.session_state[_SK_DETAILS] = details_page
            st.rerun()

    if st.session_state.get(toggle_key, False):
        st.markdown("---")
        analytics = st.session_state.get("analytics", {})
        render_explain_panel(quadrant_id, analytics)
        if st.button("Close explanation", key=f"_close_exp_{quadrant_id}"):
            st.session_state[toggle_key] = False
            st.rerun()

    st.markdown("---")
