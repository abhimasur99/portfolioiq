"""app.py

PortfolioIQ — entry point and application shell.

Responsibilities:
- Inject global CSS (assets/style.css) via st.markdown.
- Initialize session state defaults on first load.
- Render the four-item navigation bar (INPUT, DASHBOARD, GUIDE, SETTINGS).
- Route to the correct page module based on nav selection.
- Render the persistent footer disclaimer on every screen.

This file does NOT contain any analytics logic or chart rendering.
All page content is delegated to the screens/ modules.

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
    SK_COMPACT_MODE,
)

# ── Page config (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="PortfolioIQ",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
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
    SK_COMPACT_MODE:     False,
}
for key, value in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ── Navigation ─────────────────────────────────────────────────────────────────
# Programmatic navigation: pages set st.session_state["_nav_pending"] = "<PAGE>"
# and call st.rerun(). On the next run we pop it and write to _nav_radio before
# the sidebar renders so the correct page is selected.
_NAV_ITEMS = ["INPUT", "DASHBOARD", "GUIDE", "SETTINGS"]

_nav_pending = st.session_state.pop("_nav_pending", None)
if _nav_pending and _nav_pending in _NAV_ITEMS:
    st.session_state["_nav_radio"] = _nav_pending
elif "_nav_radio" not in st.session_state:
    st.session_state["_nav_radio"] = (
        "DASHBOARD" if st.session_state[SK_PORTFOLIO_LOADED] else "INPUT"
    )

selected_page = st.session_state["_nav_radio"]

# ── Sidebar buttons (replaces radio for visual consistency) ────────────────────
_DETAIL_ITEMS = [
    ("q1", "Performance"),
    ("q2", "Risk Factors"),
    ("q3", "Risk Outlook"),
    ("q4", "Optimization"),
]

for _page in _NAV_ITEMS:
    if st.sidebar.button(_page, key=f"_mainav_{_page}", use_container_width=True):
        st.session_state["_nav_radio"] = _page
        st.session_state.pop("_dashboard_details", None)
        st.rerun()

    # Sub-navigation: indented detail-page shortcuts, only when portfolio loaded
    if _page == "DASHBOARD" and st.session_state.get(SK_PORTFOLIO_LOADED):
        st.sidebar.markdown(
            '<p style="font-size:9px; color:#5a7a9a; text-transform:uppercase; '
            'letter-spacing:0.12em; font-family:\'Share Tech Mono\',monospace; '
            'margin:4px 0 2px 4px;">Details</p>',
            unsafe_allow_html=True,
        )
        for _dk, _dlabel in _DETAIL_ITEMS:
            _, _dcol = st.sidebar.columns([0.08, 0.92])
            if _dcol.button(_dlabel, key=f"_subnav_{_dk}", use_container_width=True):
                st.session_state["_dashboard_details"] = _dk
                st.session_state["_nav_radio"] = "DASHBOARD"
                st.rerun()

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
