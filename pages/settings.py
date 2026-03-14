"""pages/settings.py

Screen 5 — Settings.

Responsibilities:
- Benchmark selection (BENCHMARK_OPTIONS).
- Time period selection (PERIOD_OPTIONS).
- VaR confidence level (slider).
- VaR method (historical | garch).
- GARCH refit frequency.
- Optimization weight bounds (min/max sliders).
- Monte Carlo horizon (5, 10, 20, 30 years).
- Monte Carlo paths (1,000 or 10,000).
- Rebalancing drift threshold.
- Save and Recompute button: triggers granular recomputation of only the
  analytics affected by the changed setting.
  - Benchmark change → recompute performance + optimization (not price fetch).
  - VaR confidence change → recompute risk_outlook only.
  - Weight bounds change → recompute optimization only.
  - MC horizon/paths change → recompute MC only.

Writes all changed settings to st.session_state using SK_ constants.
Does NOT use raw string literals.

Implemented in: Session 15.
"""

import streamlit as st


def render() -> None:
    """Render the Settings screen."""
    st.title("Settings")
    st.info("Session 15 — not yet implemented.")
