"""components/dashboard_quad.py

Reusable dashboard quadrant component.

Renders one of the four analytical quadrants on the main dashboard.
Each quadrant has a consistent layout:
- Quadrant header (title, subtitle).
- Primary chart (compact height, use_container_width=True).
- Row of 3–4 KPI metric tiles.
- Contextual flag (amber/red/green badge with one-line message).
- Two action buttons: "Explain Numbers" and "More Details".

The Explain Numbers button opens the explain_panel overlay without navigating.
The More Details button sets a session state key to route to the correct
details page and calls st.rerun().

Args to render_quadrant():
- quadrant_id: str — "q1" | "q2" | "q3" | "q4".
- title: str — quadrant heading.
- chart_fig: go.Figure — primary Plotly figure (compact height set here).
- kpis: list[dict] — each dict has "label", "value", "delta" (optional).
- flag: dict | None — "status" (green/amber/red), "message" str.
- details_page: str — session state routing key for More Details.

Implemented in: Session 10.
"""

import streamlit as st
import plotly.graph_objects as go


def render_quadrant(
    quadrant_id: str,
    title: str,
    chart_fig: go.Figure,
    kpis: list,
    flag: dict | None,
    details_page: str,
) -> None:
    """Render a single dashboard quadrant.

    Args:
        quadrant_id: One of "q1", "q2", "q3", "q4".
        title: Quadrant display title.
        chart_fig: Plotly figure for the primary chart.
        kpis: List of dicts with keys "label", "value", and optional "delta".
        flag: Dict with "status" and "message", or None.
        details_page: Routing identifier for the More Details button.
    """
    raise NotImplementedError("Implemented in Session 10.")
