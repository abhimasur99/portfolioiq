"""app.py

PortfolioIQ — entry point and application shell.

Responsibilities:
- Inject global CSS (assets/style.css) via st.markdown.
- Initialize session state defaults on first load.
- Render the four-item navigation bar (INPUT, DASHBOARD, GUIDE, SETTINGS).
- Route to the correct page module based on nav selection.
- Render the persistent footer disclaimer on every screen.

This file does NOT contain any analytics logic or chart rendering.
All page content is delegated to the pages/ modules.

Navigation rules (locked):
- Nav bar has exactly four items: INPUT, DASHBOARD, GUIDE, SETTINGS.
- "Deep Dive" never appears in the nav bar.
- More Details screens are accessed only via quadrant buttons on the dashboard.
"""

import streamlit as st
from pathlib import Path

from assets.config import (
    DISCLAIMER_SHORT,
    DEFAULT_BENCHMARK,
    DEFAULT_PERIOD,
    DEFAULT_VAR_CONFIDENCE,
    DEFAULT_VAR_METHOD,
    DEFAULT_MC_HORIZON,
    DEFAULT_MC_PATHS,
    DEFAULT_WEIGHT_MIN,
    DEFAULT_WEIGHT_MAX,
    DEFAULT_DRIFT_THRESHOLD,
    SK_BENCHMARK,
    SK_PERIOD,
    SK_VAR_CONFIDENCE,
    SK_VAR_METHOD,
    SK_MC_HORIZON,
    SK_MC_PATHS,
    SK_WEIGHT_MIN,
    SK_WEIGHT_MAX,
    SK_DRIFT_THRESHOLD,
    SK_PORTFOLIO_LOADED,
    SK_ANALYTICS,
)

# ── Page config (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="PortfolioIQ",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS injection ──────────────────────────────────────────────────────────────
_css_path = Path(__file__).parent / "assets" / "style.css"
with open(_css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Session state initialization ───────────────────────────────────────────────
_defaults = {
    SK_BENCHMARK:        DEFAULT_BENCHMARK,
    SK_PERIOD:           DEFAULT_PERIOD,
    SK_VAR_CONFIDENCE:   DEFAULT_VAR_CONFIDENCE,
    SK_VAR_METHOD:       DEFAULT_VAR_METHOD,
    SK_MC_HORIZON:       DEFAULT_MC_HORIZON,
    SK_MC_PATHS:         DEFAULT_MC_PATHS,
    SK_WEIGHT_MIN:       DEFAULT_WEIGHT_MIN,
    SK_WEIGHT_MAX:       DEFAULT_WEIGHT_MAX,
    SK_DRIFT_THRESHOLD:  DEFAULT_DRIFT_THRESHOLD,
    SK_PORTFOLIO_LOADED: False,
    SK_ANALYTICS:        {},
}
for key, value in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ── Navigation ─────────────────────────────────────────────────────────────────
# Four permanent items only. Order matters for display.
_NAV_ITEMS = ["INPUT", "DASHBOARD", "GUIDE", "SETTINGS"]

# Default to DASHBOARD if portfolio is loaded, otherwise INPUT.
_default_page = "DASHBOARD" if st.session_state[SK_PORTFOLIO_LOADED] else "INPUT"

selected_page = st.sidebar.radio(
    label="Navigation",
    options=_NAV_ITEMS,
    index=_NAV_ITEMS.index(_default_page),
    label_visibility="collapsed",
)

# ── Page routing ───────────────────────────────────────────────────────────────
if selected_page == "INPUT":
    from pages import input as _page
    _page.render()

elif selected_page == "DASHBOARD":
    from pages import dashboard as _page
    _page.render()

elif selected_page == "GUIDE":
    from pages import guide as _page
    _page.render()

elif selected_page == "SETTINGS":
    from pages import settings as _page
    _page.render()

# ── Footer disclaimer ──────────────────────────────────────────────────────────
st.markdown(
    f'<div class="disclaimer-footer">{DISCLAIMER_SHORT}</div>',
    unsafe_allow_html=True,
)
