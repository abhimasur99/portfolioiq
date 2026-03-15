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
| TL-007 | P3 | Guide | Tables unreadable — cell text too long, columns overflow and are unreadable | OPEN | — |

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
