# PortfolioIQ — Testing Log

## How to use this file

- Add new issues as they are found during testing. Never delete rows — update status instead.
- Update status and commit hash when a fix is made.
- Append session notes at the bottom after each testing session.

## Severity scale

| Level | Meaning |
|-------|---------|
| P0 | Blocker — crashes the app or makes a screen unusable |
| P1 | Major — core feature broken or significantly degraded UX |
| P2 | Minor — visual issue, redundant element, or degraded-but-functional UX |
| P3 | Polish — nice-to-have improvement, low urgency |

## Status values

`OPEN` → `IN-PROGRESS` → `FIXED (commit hash)` | `DEFERRED (reason)` | `WONTFIX (reason)`

---

## Issue Tracker

| ID | P | Screen | Description | Status | Commit |
|----|---|--------|-------------|--------|--------|
| TL-001 | P0 | Details Q1–Q4 | DuplicateWidgetID crashes all More Details screens — Back button rendered twice (once in dashboard._route_details, once in each details page) | FIXED (beba3ef) | beba3ef |
| TL-002 | P1 | Input | Portfolio entries lost when navigating back from dashboard — st.form submission clears _KEY_TICKER_EDITOR widget state | FIXED (beba3ef) | beba3ef |
| TL-003 | P1 | Dashboard | Ticker tape CSS class mismatch — HTML used ticker-tape/ticker-tape-content but CSS animation targets ticker-tape-container/ticker-tape-track | FIXED | — |
| TL-004 | P1 | Terminal | VXMT 404 warning on every load — VXMT is delisted; signal already degrades gracefully to "unavailable" | WONTFIX/EXPECTED | — |
| TL-005 | P2 | Dashboard | Holdings strip shows price already visible in ticker tape above it — replaced with horizontal weight bar | FIXED | — |
| TL-006 | P2 | Input | Weight preview only updates after clicking Analyse — live update removed when st.form was added | OPEN | — |
| TL-007 | P3 | Guide | Tables unreadable — cell text too long, columns overflow and are unreadable | FIXED | — |

| TL-008 | P2 | Details Q2 | Correlation matrix: some numbers invisible — text color not contrasting against cell background color | FIXED | — |
| TL-009 | P2 | Details Q2 | ETFs (e.g. GLD) show as "Unknown" sector — yfinance doesn't classify ETFs under GICS sectors | FIXED | — |
| TL-010 | P2 | Details Q3 | Tech Concentration signal shows "unavailable" — no reliable sector feed in yfinance; known limitation | DEFERRED/v2 | — |
| TL-011 | P2 | Details Q4 | Stress test scenarios not in chronological order — should be 2000, 2008, 2020, 2022 | FIXED | — |
| TL-012 | P3 | Details Q4 | "Estimation Error Warning" label — changed to "Optimizer Assumptions" | FIXED | — |
| TL-013 | P3 | All | Page transitions — abrupt; evaluate whether Streamlit allows smoother transitions | OPEN | — |
| TL-014 | P1 | Input | Auto-redirect to dashboard fails on re-analyse — nav_radio widget retained INPUT state after user navigated back | FIXED | — |
| TL-015 | P2 | Settings | Weight bounds and drift threshold sliders show wrong values — format="%.0f%%" doesn't scale decimals to % | FIXED | — |
| TL-016 | P2 | Dashboard | Holdings strip redesigned — stacked breakdown bar replacing individual column bars | FIXED | — |

---

## Session Notes

**2026-03-14 — Smoke test session 1**
Tester: Abhi (manual, browser)
Portfolio tested: JPM + AAPL, $25k each, SPY benchmark, 3y period
Found: TL-001, TL-002, TL-003, TL-004, TL-005, TL-006, TL-007
Fixed this session: yfinance upgraded 0.2.36 → 0.2.66 (validation now works); validate_tickers fallback improved (network error no longer marks all tickers invalid); input form changed to st.form (prevents mid-entry reruns); app launch command corrected to use venv explicitly.
Status at session end: TL-001 through TL-007 all OPEN except TL-004 WONTFIX.

**2026-03-14 — Fix session 2**
Fixed: TL-001 (P0, duplicate Back button — FIXED beba3ef), TL-002 (P1, input state lost on back-navigate — FIXED beba3ef), TL-003 partial (P1, * 3 → * 2 but CSS class mismatch remained).
Logged new issues: TL-008 through TL-013.

**2026-03-14 — Fix session 3**
Fixed: TL-003 (CSS class mismatch: ticker-tape → ticker-tape-container, ticker-tape-content → ticker-tape-track), TL-005 (holdings strip: price removed, horizontal weight bar added), TL-008 (heatmap text: light text on dark cells, dark text on white cells), TL-009 (ETF sector: quoteType check labels ETFs as "ETF / Fund" not "Unknown"), TL-011 (stress test order: 2000 → 2008 → 2020 → 2022), TL-012 ("Estimation Error Warning" → "Optimizer Assumptions").
Remaining open: TL-006 (weight preview liveness — deferred for discussion), TL-007 (guide table readability — deferred), TL-010 (tech concentration — deferred/v2), TL-013 (page transitions — open).

**2026-03-14 — Fix session 4**
New issues found: TL-014 (auto-redirect on re-analyse), TL-015 (settings slider format), TL-016 (holdings strip redesign to stacked bar). Also: ticker scroll speed halved (60s → 30s).
Fixed: TL-014 (nav_radio key added to radio widget in app.py; st.session_state["nav_radio"]="DASHBOARD" set before rerun in input.py), TL-015 (sliders now use 0–100 int scale with format="%d%%", convert to decimal on save), TL-016 (holdings strip → full-width stacked segmented bar with color-coded per-ticker segments).
Stage B planned: ? icon tooltips on all KPI metrics, remove Explain Numbers + All Metrics tables from details pages. Stage C: Guide page redesign.

**2026-03-19 — Stage D**
Items implemented: (1) Cross-quadrant navigation in More Details — prev/next buttons in _route_details() in dashboard.py; (3) Tech Concentration shows "Coming Soon" instead of n/a — market_signals.py interpretation updated, details_q3.py special-case display added; (4) Historical stress tests (GFC/Dot-Com/COVID/Rate Shock) removed from UI — replaced with Signal-Based Sensitivity Analysis using GARCH vol × signal environment multipliers; signal_scenario_chart() added to charts.py; _compute_signal_scenarios() added to details_q3.py; environment badge (Calm/Elevated/Stressed/Severe) added to At a Glance; (5) DEFAULT_WEIGHT_MAX 0.50→0.90 in config.py; (6) Guide wording: "non-stationary"→"constantly evolving", "characterised"→"described", Q3 paragraph updated; (7) Data freshness caption added to dashboard; all user-facing "live" language removed (details_q3.py, guide.py, input.py). CHANGELOG [0.21.0].
TL-010 status update: still DEFERRED/v2 for full implementation, but "Coming Soon" label added to panel.

**2026-03-15 — Fix session 5 (Stage B + C)**
New issue found: Two-click navigation lag introduced by TL-014 fix — without key= on radio, passing index= on every rerun caused Streamlit to reset widget position, requiring two clicks.
Fixed: Two-click nav lag (app.py: index= now only passed when _nav_pending fires or on first load; omitted on normal reruns so radio tracks its own state).
Fixed: More Details state persistence — _dashboard_details session key persisted when navigating away from Dashboard. Fixed by clearing it in INPUT/GUIDE/SETTINGS routing blocks in app.py.
Stage B implemented (commit 33ab9a4): ? icon tooltips via st.metric(help=) on all 16 KPI tiles in dashboard quadrants (_build_q1/q2/q3/q4 in dashboard.py); removed Explain Numbers toggle button + explain panel from dashboard_quad.py; health bar reordered to: Market Stress → Return Quality → Volatility → Drawdown Risk → Diversification → Efficiency.
Details Key Metrics + Q3 signals panel (commit 5de925f): Added st.metric(help=) grids to Key Metrics sections in details_q1/q2/q3 (replacing dataframe tables). Converted Q3 Risk Preparedness Panel from HTML card grid to st.metric() tiles with signal interpretation in help= tooltip.
Stage C Guide redesign — TL-007 FIXED (commit a9fa5c9): guide.py completely rewritten — removed all 5 wide metric-table expanders (unreadable in st.dataframe), pivoted to 3-section how-to-use layout: Section 1 (4-step how-to-use flow), Section 2 (what each quadrant tells you — 4 paragraphs), Section 3 (key limitations — 4 points). Metric definitions now live in ? tooltips on each KPI tile. Version bumped to v1.1 — 2026-03.
Commits this session: 3dc0dcc (T1 bug fixes), 33ab9a4 (Stage B), 5de925f (nav + details tooltips), a9fa5c9 (Stage C + TL-007).
Remaining open: TL-006 (weight preview liveness — deferred), TL-013 (page transitions — open low priority), TL-010 (tech concentration — deferred/v2).
