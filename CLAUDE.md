# CLAUDE.md — PortfolioIQ Project Memory

Read this file at the start of every session. Confirm understanding before writing any code.
Update the Current State section at the end of every session before closing.

---

## Project Identity

PortfolioIQ is a Python/Streamlit equity portfolio analytics web application delivering
institutional-grade quantitative analysis across four layers (Descriptive, Diagnostic,
Predictive, Prescriptive) in plain language, using a cockpit dark-theme dashboard.
Built for DIY investors and simultaneously as a portfolio project demonstrating FRM/CFA
methodology applied in code, targeting model risk and market risk analyst roles at NYC banks.

---

## Module Responsibilities

| File | Does | Does NOT |
|------|------|----------|
| `assets/config.py` | Colors, fonts, Plotly template, session state key constants, defaults | Any analytics or runtime logic |
| `assets/style.css` | CSS injection for cockpit dark theme | Anything Plotly-related (handled by template) |
| `app.py` | CSS injection, session state init, 4-item nav bar, routing, footer disclaimer | Analytics, charts |
| `analytics/data_fetcher.py` | yfinance download, MultiIndex handling, Adj Close, caching, validation, ^IRX conversion | Returns computation |
| `analytics/returns.py` | Log returns from prices, portfolio aggregation | Performance ratios |
| `analytics/performance.py` | CAGR, Sharpe, Sortino, Treynor, Info ratio, alpha, beta, R², rolling metrics | Risk or optimization |
| `analytics/risk_factors.py` | Correlation, drawdown, HHI, diversification ratio, sector weights | Forward-looking signals |
| `analytics/risk_outlook.py` | GARCH, EWMA, VaR, CVaR, Monte Carlo, stress tests | Market signals fetch |
| `analytics/optimization.py` | Efficient frontier, max Sharpe, min variance, risk parity, CML | Return forecasting |
| `analytics/market_signals.py` | 11 live forward-looking signals, fresh fetch each session | Cached analytics |
| `components/charts.py` | All Plotly figure builders | Session state, analytics |
| `components/dashboard_quad.py` | Reusable quadrant layout component | Chart logic |
| `components/explain_panel.py` | Explain Numbers overlay | Navigation |
| `pages/input.py` | Screen 1: ticker entry, weight calc, loading pipeline | Analytics computation |
| `pages/dashboard.py` | Screen 2: 2x2 quadrants, health bar, holdings strip, ticker tape | Analytics computation |
| `pages/details_q{1-4}.py` | Screen 3a-d: More Details for each quadrant | Nav bar appearance |
| `pages/guide.py` | Screen 4: 5-section methodology reference | Analytics |
| `pages/settings.py` | Screen 5: all user settings, granular recompute on save | Analytics computation |
| `tests/conftest.py` | Shared fixtures, mocked yfinance — 756+ days, 4 tickers | Real API calls |

---

## Naming Conventions (Locked)

- `returns_df` — pd.DataFrame of per-ticker log returns
- `weights` — pd.Series of portfolio weights indexed by ticker
- `benchmark_returns` — pd.Series of benchmark log returns
- `portfolio_returns` — pd.Series of weighted portfolio log returns
- `tickers` — list[str] of ticker symbols
- `analytics` — dict of all session analytics results (from SK_ANALYTICS)
- `cov_matrix` — pd.DataFrame covariance matrix
- `corr_matrix` — pd.DataFrame Pearson correlation matrix

---

## Locked Architectural Decisions

**Cannot be changed without explicit discussion and confirmation.**

1. **Log returns** — rt = ln(Pt/Pt-1). Never simple returns. Multiplied by 100 only for GARCH fitting.
2. **Python 3.11** — arch library has dependency conflicts with 3.12.
3. **GARCH(1,1) via arch library** — fitted on percentage returns. disp=False. Stationarity check: alpha+beta < 1. EWMA fallback if violated or < 252 obs.
4. **scipy SLSQP** — for all three optimizers (max Sharpe, min variance, risk parity).
5. **Equal-weight initialization** — optimizer always starts from 1/N, never from current user weights.
6. **Risk-free rate from ^IRX** — divide by 100, then by 252 for daily decimal rate.
7. **GARCH-MC for Monte Carlo** — full numpy vectorization. No Python loops over paths.
8. **Market signals fetched fresh** — each session. Not cached with price data 1-hour TTL.
9. **Four-item nav bar only** — INPUT, DASHBOARD, GUIDE, SETTINGS. Deep Dive never in nav bar.
10. **More Details from quadrant buttons only** — never from nav bar.
11. **All chart colors from config.py** — never hardcoded in chart functions.
12. **All session state keys from config.py constants** — never raw string literals in page files.
13. **Historical VaR and CVaR as primary risk metrics** — shown at 95% and 99%.
14. **All three optimizer portfolios shown simultaneously** — max Sharpe, min variance, risk parity.
15. **No chat feature in v1.**

---

## Known Issues

- **Yield curve ticker discrepancy:** spec uses ^TNX - ^TYX for yield curve spread, but ^TYX is the 30-year Treasury, not the 2-year. Implementing per spec. Documented in DECISIONS.md D-10. Revisit in v2.
- **^MOVE availability:** ^MOVE may not always be available from yfinance. Graceful fallback required in market_signals.py.
- **VIX3M availability:** use VXMT as fallback if ^VIX3M is unavailable.

---

## Current State

**Session 1 — COMPLETE (2026-03-13)**

Completed:
- Full directory structure created.
- requirements.txt: all 9 dependencies pinned exactly.
- .gitignore: Python, venv, Streamlit secrets, test artifacts.
- .streamlit/config.toml: dark theme base, backgroundColor, secondaryBackgroundColor, textColor.
- assets/config.py: complete color palette, FONT constants, Plotly dark template registered as "portfolioiq", all SK_ session state key constants, all DEFAULT_ constants, BENCHMARK_OPTIONS, PERIOD_OPTIONS, STRESS_SCENARIOS, DISCLAIMER_SHORT, DISCLAIMER_FULL, all signal tickers.
- assets/style.css: full cockpit CSS including Google Fonts import, dark background, metric tiles, buttons, inputs, ticker tape animation, disclaimer footer, signal badges.
- app.py: entry point with CSS injection, session state init, 4-item nav bar, page routing, footer disclaimer.
- pages/: all 8 page stubs with full docstrings and render() functions.
- analytics/: all 7 module stubs with full docstrings, function signatures, and mathematical specs.
- components/: all 3 component stubs with full docstrings and function signatures.
- tests/: conftest.py + 6 test files with full test plans (all skipped pending implementation).
- CLAUDE.md: this file (with Session Continuity Protocol added).
- DECISIONS.md: 10 architectural decisions (D-01 through D-10).
- CHANGELOG.md: initialized with [0.1.0] entry.
- Git repo initialized and first commit made: "feat: Session 1 — project scaffolding".

Next session: Session 2 — data_fetcher.py (yfinance layer) + complete conftest.py with mock data.

**Session state keys to watch:** All defined in assets/config.py. SK_PORTFOLIO_LOADED gates dashboard access.

---

## Session Continuity Protocol

These three rules prevent rate-limit interruptions from leaving the project in an ambiguous state.

**Rule 1 — Bookkeeping-first ordering within each session:**
1. CHANGELOG.md updated/initialized first (before any primary work).
2. All primary work (code, stubs, analytics).
3. CLAUDE.md Current State updated incrementally after each major batch.
4. Git commit last — CLAUDE.md records it only AFTER it actually runs, never before.

**Rule 2 — Incremental CLAUDE.md checkpoints:**
After every logical batch of files, append a checkpoint line to Current State immediately.
Format: `[Checkpoint — X complete]: files written. Remaining: Y, Z.`
Do not wait until session end to update Current State.

**Rule 3 — Proactive status output before large batches:**
Before writing 5+ files in sequence, output a STATUS CHECKPOINT to the chat:
```
STATUS CHECKPOINT
Completed so far: [list]
About to write: [next N files]
Remaining after this batch: [list]
If rate limit hits here, resume from: [specific file]
```
This is visible in the chat history even if tool calls don't complete.

---

## Standard Session Opening Prompt

"Please read CLAUDE.md first and confirm you understand the current project state.
Then read [specific files needed today]. Today's session goal is [one sentence].
Do not change any decisions in CLAUDE.md without flagging it and waiting for my confirmation.
Before writing any code, describe your implementation plan in a few sentences so I can confirm the approach."
