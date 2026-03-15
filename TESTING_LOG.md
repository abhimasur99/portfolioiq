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
| TL-003 | P1 | Dashboard | Ticker tape repeats each ticker 3× — tape_inner * 3 with few tickers makes repetition obvious | FIXED (beba3ef) | beba3ef |
| TL-004 | P1 | Terminal | VXMT 404 warning on every load — VXMT is delisted; signal already degrades gracefully to "unavailable" | WONTFIX/EXPECTED | — |
| TL-005 | P2 | Dashboard | Holdings strip shows price already visible in ticker tape above it | OPEN | — |
| TL-006 | P2 | Input | Weight preview only updates after clicking Analyse — live update removed when st.form was added | OPEN | — |
| TL-007 | P3 | Guide | Tables unreadable — cell text too long, columns overflow and are unreadable | OPEN | — |

---

## Session Notes

**2026-03-14 — Smoke test session 1**
Tester: Abhi (manual, browser)
Portfolio tested: JPM + AAPL, $25k each, SPY benchmark, 3y period
Found: TL-001, TL-002, TL-003, TL-004, TL-005, TL-006, TL-007
Fixed this session: yfinance upgraded 0.2.36 → 0.2.66 (validation now works); validate_tickers fallback improved (network error no longer marks all tickers invalid); input form changed to st.form (prevents mid-entry reruns); app launch command corrected to use venv explicitly.
Status at session end: TL-001 through TL-007 all OPEN except TL-004 WONTFIX.
