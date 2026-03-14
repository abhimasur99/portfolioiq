"""pages/input.py

Screen 1 — Portfolio Input.

Responsibilities:
- Ticker entry with inline validation (before computation).
- Dollar amount input with automatic weight calculation and live recalculation.
- Benchmark selection from BENCHMARK_OPTIONS.
- Time period selection from PERIOD_OPTIONS.
- Full disclaimer display.
- Loading screen with seven-step progress bar on submit.
- On successful load, sets SK_PORTFOLIO_LOADED = True and routes to dashboard.

Does NOT compute any analytics — delegates to analytics/ modules via the
staged pipeline triggered on submit.

Implemented in: Session 9.
"""

import streamlit as st


def render() -> None:
    """Render the Portfolio Input screen."""
    st.title("Portfolio Input")
    st.info("Session 9 — not yet implemented.")
