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
    DEFAULT_VAR_CONFIDENCE,
    DEFAULT_VAR_METHOD,
    DEFAULT_MC_HORIZON,
    DEFAULT_MC_PATHS,
    DEFAULT_WEIGHT_MIN,
    DEFAULT_WEIGHT_MAX,
    SK_BENCHMARK,
    SK_PERIOD,
    SK_VAR_CONFIDENCE,
    SK_VAR_METHOD,
    SK_MC_HORIZON,
    SK_MC_PATHS,
    SK_WEIGHT_MIN,
    SK_WEIGHT_MAX,
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
    SK_PERIOD:           "3Y",   # default window label; overwritten by input.py after load
    SK_VAR_CONFIDENCE:   DEFAULT_VAR_CONFIDENCE,
    SK_VAR_METHOD:       DEFAULT_VAR_METHOD,
    SK_MC_HORIZON:       DEFAULT_MC_HORIZON,
    SK_MC_PATHS:         DEFAULT_MC_PATHS,
    SK_WEIGHT_MIN:       DEFAULT_WEIGHT_MIN,
    SK_WEIGHT_MAX:       DEFAULT_WEIGHT_MAX,
    SK_PORTFOLIO_LOADED: False,
    SK_ANALYTICS:        {},
}
for key, value in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ── Navigation ─────────────────────────────────────────────────────────────────
# Four permanent items only. Order matters for display.
_NAV_ITEMS = ["INPUT", "DASHBOARD", "GUIDE", "SETTINGS"]

# Navigation state is tracked in _current_nav (a plain session state key, not
# widget-bound). Pages request navigation by setting _nav_pending; this block
# resolves it before the radio is rendered, avoiding widget-state restrictions.
#
# index= is only passed when a programmatic override is needed (_nav_pending fired
# or first load). On normal reruns it is omitted so Streamlit tracks the radio's
# own state by position — passing index= every run causes a two-click lag.
_nav_target = st.session_state.pop("_nav_pending", None)
if _nav_target and _nav_target in _NAV_ITEMS:
    _nav_index = _NAV_ITEMS.index(_nav_target)
elif "_current_nav" not in st.session_state:
    _nav_index = 1 if st.session_state[SK_PORTFOLIO_LOADED] else 0
else:
    _nav_index = None  # normal rerun — let radio track its own state

_radio_kwargs: dict = dict(label="Navigation", options=_NAV_ITEMS, label_visibility="collapsed")
if _nav_index is not None:
    _radio_kwargs["index"] = _nav_index

selected_page = st.sidebar.radio(**_radio_kwargs)
# Sync user's manual nav click back to our state variable
st.session_state["_current_nav"] = selected_page

# ── Page routing ───────────────────────────────────────────────────────────────
# Navigating away from DASHBOARD clears any active More Details sub-page so that
# returning to DASHBOARD always lands on the main dashboard, not a details screen.
if selected_page == "INPUT":
    st.session_state.pop("_dashboard_details", None)
    from screens import input as _page
    _page.render()

elif selected_page == "DASHBOARD":
    from screens import dashboard as _page
    _page.render()

elif selected_page == "GUIDE":
    st.session_state.pop("_dashboard_details", None)
    from screens import guide as _page
    _page.render()

elif selected_page == "SETTINGS":
    st.session_state.pop("_dashboard_details", None)
    from screens import settings as _page
    _page.render()

# ── Footer disclaimer ──────────────────────────────────────────────────────────
st.markdown(
    f'<div class="disclaimer-footer">{DISCLAIMER_SHORT}</div>',
    unsafe_allow_html=True,
)
