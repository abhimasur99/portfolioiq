"""components/explain_panel.py

Explain Numbers overlay panel.

Opens as an overlay on the dashboard and all More Details screens without
navigating away from the current page. Explains specific numbers in plain
language tied to the user's actual holdings.

Behavior:
- Triggered by "Explain Numbers" button on any quadrant or More Details screen.
- Displays in a Streamlit expander or modal-style container.
- Content is contextual to which quadrant triggered it.
- Limitation disclosed at bottom of every panel.
- Link to Guide section for deeper reading.
- Closes and returns focus to prior position without page navigation.

Implemented in: Session 10.
"""

import streamlit as st


def render_explain_panel(quadrant_id: str, analytics: dict) -> None:
    """Render the Explain Numbers overlay for a given quadrant.

    Args:
        quadrant_id: One of "q1", "q2", "q3", "q4".
        analytics: The full analytics results dict from session state.
    """
    raise NotImplementedError("Implemented in Session 10.")
