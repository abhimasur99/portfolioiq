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
- **Python 3.11 not installed:** only Python 3.12 available on this machine. Running on 3.12 with .venv. arch library installs and works on 3.12 for this setup — verify when arch is added in Session 5. If issues arise, install Python 3.11 via brew.

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

**Session 2 — COMPLETE (2026-03-13)**

Completed:
- tests/conftest.py: full mock data — 800 trading days, 4 tickers (AAPL/MSFT/GOOGL/SPY), Cholesky-correlated log-normal prices, stress period (2x vol days 200-299), drawdown (days 300-379), recovery (days 380-449), seed 42. All 6 fixtures implemented. mock_yfinance_download and mock_irx_download fixtures for patching yfinance in tests.
- analytics/data_fetcher.py: _download_with_backoff (exponential backoff 1s/2s/4s), _extract_adj_close (MultiIndex + flat column handling, NaN drop, invalid ticker ValueError), _fetch_price_data_impl, _fetch_risk_free_rate_impl (^IRX /100/252, fallback 0.04/252), validate_tickers, public cached fetch_price_data (@st.cache_data ttl=3600), fetch_risk_free_rate, fetch_market_signals stub.
- tests/test_data_fetcher.py: 21 tests, all passing. Covers MultiIndex extraction, NaN dropping, invalid ticker error, flat column handling, ^IRX conversion, NaN handling, fetch failure fallback, empty result fallback, validate_tickers.
- .venv: created with Python 3.12 (3.11 not installed — see Known Issues).

[Checkpoint — Session 2 complete]: All tests passing (21/21). Git commit 45e5537 made: "feat: Session 2 — data layer (data_fetcher.py, conftest.py, 21 tests)".

**Session 3 — COMPLETE (2026-03-13)**

Completed:
- analytics/returns.py: compute_log_returns (rt=ln(Pt/Pt-1)), compute_portfolio_returns (dot product, weight-sum validation with 1e-6 tolerance).
- analytics/performance.py: compute_cagr (exp(mean*252)-1), compute_sharpe, compute_sortino (negative-returns-only downside std), compute_treynor, compute_info_ratio, compute_alpha_beta (Jensen's alpha, beta via Cov/Var, R²=corr²), compute_rolling_sharpe (252-day), compute_rolling_beta (rolling Cov/Var), compute_best_worst_periods (resample ME/YE), compute_all_performance. All zero-denominator guards use 1e-10 tolerance (not == 0.0, which fails for FP-constant series).
- tests/test_returns.py: 10 tests, all passing.
- tests/test_performance.py: 23 tests, all passing.
- Full suite: 54 passed, 37 skipped.

[Checkpoint — Session 3 complete]: All 54 tests passing. FP lesson: use < 1e-10 threshold for zero-guards, not == 0.0. Git commit 862b3e0 made: "feat: Session 3 — returns and performance analytics".

**Session 4 — COMPLETE (2026-03-13)**

Completed:
- analytics/risk_factors.py: compute_correlation_matrix (Pearson), compute_rolling_correlation (60-day MultiIndex), compute_covariance_matrix (annualized *252, PD-check with 1e-6 diagonal regularization when cond>1e10), compute_hhi (sum w²), compute_effective_n (1/HHI), compute_diversification_ratio (weighted avg vol / portfolio vol from ann cov), compute_drawdown_series (exp(cumsum) price index), compute_max_drawdown, compute_calmar (CAGR/|max_dd|, 1e-10 guard), compute_recovery_time (trading days trough→recovery, None if unreachable), compute_ulcer_index (sqrt(mean(DD²))), fetch_sector_weights (live yfinance best-effort, grouped by GICS sector), compute_all_risk_factors.
- tests/test_risk_factors.py: 30 tests, all passing.
- Full suite: 84 passed, 27 skipped.

[Checkpoint — Session 4 complete]: All 84 tests passing. Git commit 7506041 made: "feat: Session 4 — risk factors analytics".

**Session 5 — COMPLETE (2026-03-13)**

Completed:
- arch 6.3.0 installed (works cleanly on Python 3.12 — no conflicts; known issue resolved).
- analytics/risk_outlook.py (Session 5 portion): compute_historical_vol (std*sqrt(252)), compute_ewma_vol (λ=0.94 RiskMetrics, initializes from full-period variance), fit_garch (GARCH(1,1) on pct returns, alpha+beta<1 stationarity check, EWMA fallback if <252 obs or non-stationary or fit failure; returns (result, daily_vol, is_fallback)), compute_var_cvar_historical (sign convention: negative = loss), compute_garch_var (normal VaR), compute_var_monthly (×sqrt(21)), compute_skewness_kurtosis (Fisher excess kurtosis). GARCH-MC and stress tests remain NotImplementedError for Session 6. compute_all_risk_outlook also NotImplementedError until Session 6.
- tests/test_risk_outlook.py: 25 passed, 3 skipped (MC/stress tests). First-run clean.
- Full suite: 109 passed, 21 skipped.

Key note: arch 6.3.0 installed successfully with Python 3.12 (statsmodels 0.14.6, patsy 1.0.2 added as dependencies). No version conflicts.

[Checkpoint — Session 5 complete]: All 109 tests passing. Git commit a893c87 made: "feat: Session 5 — risk outlook pt1".

[Checkpoint — Session 6 complete]: analytics/risk_outlook.py completed (_run_garch_monte_carlo vectorized GARCH-MC, _run_stress_tests alpha+beta×scenario_return, compute_all_risk_outlook master aggregator). analytics/market_signals.py implemented (all 11 signals, graceful per-signal fallback, yfinance batch download with MultiIndex extraction). tests/test_risk_outlook.py: 0 skipped (MC shape/positivity/percentile-ordering, stress keys/structure/types all passing). tests/test_market_signals.py: 11 new tests all passing. Full suite: 126 passed, 12 skipped (Session 7 optimization stubs only). pytest-mock installed (was missing from env; added to requirements). Git commit f4e52aa made: "feat: Session 6 — risk outlook pt2, market signals".

Next session: Session 7 — optimization.py (efficient frontier 50 targets, max Sharpe, min variance, risk parity, CML, weight delta table).

[Checkpoint — Session 7 complete]: analytics/optimization.py implemented (_optimize_min_variance, _optimize_max_sharpe, _optimize_risk_parity equal-RC via unnormalized squared-difference objective, _compute_frontier 50 points with feasible-max upper bound + warm-start, compute_all_optimization master aggregator with weight_delta_table). tests/test_optimization.py: 25 tests all passing, 0 skipped. Full suite: 151 passed, 0 skipped. Key note: max_sharpe_ratio test uses isfinite check (not >= 0) because mock data's drawdown period produces negative overall expected returns. Git commit 85b4648 made: "feat: Session 7 — portfolio optimization".

Next session: Session 8 — charts.py (all Plotly figure builders using config.py dark template).

[Checkpoint — Session 8 complete]: components/charts.py implemented — all 13 Plotly figure builders: cumulative_return_chart, return_distribution_chart, rolling_sharpe_chart, rolling_beta_chart, correlation_heatmap, rolling_correlation_chart, drawdown_chart, sector_weights_chart, garch_volatility_chart, monte_carlo_fan_chart, stress_test_chart, efficient_frontier_chart, current_vs_optimal_chart. All colors from config.py constants (no hardcoded hex). All 13 smoke-tested (produce go.Figure without error). Full test suite: 151 passed, 0 failed. No separate test file (charts tested visually in integration). Git commit a1df9fd made: "feat: Session 8 — all Plotly chart figure builders".

Next session: Session 9 — input.py (ticker validation, dollar-to-weight, 7-step loading pipeline with st.progress).

[Checkpoint — Session 9 complete]: pages/input.py implemented — st.data_editor holdings table (2–10 dynamic rows), live weight preview column with bound-violation indicators, benchmark + period selectors, disclaimer accordion + checkbox gate, 7-step _run_pipeline (validate tickers → fetch prices + rf rate → log returns → performance → risk factors → risk outlook → optimization + signals), st.progress + per-step st.empty status text, full session state population on success, st.rerun() to dashboard. Full suite: 151 passed. Git commit 31f2ad7 made: "feat: Session 9 — portfolio input screen".

Next session: Session 10 — dashboard.py (4-quadrant layout, health bar, holdings strip, ticker tape, Explain Numbers overlay).

[Checkpoint — Session 10 complete]: components/dashboard_quad.py (render_quadrant — header+flag badge, 260px chart, KPI tiles, Explain Numbers toggle + inline explain panel, More Details routing). components/explain_panel.py (render_explain_panel — Q1-Q4 contextual explanations with live values, limitation disclosure). pages/dashboard.py (full dashboard — guard redirect, CSS ticker tape, holdings strip, 6-indicator health bar, 2×2 quadrant grid via render_quadrant, _dashboard_details routing to details pages). CHANGELOG [0.10.0] added. Full suite: 151 passed, 0 failed. Git commit e92fc61 made: "feat: Session 10 — dashboard, quadrant component, explain panel".

Next session: Session 11 — details_q1.py (Q1 Performance Deep Dive) + details_q2.py (Q2 Risk Factors Deep Dive).

[Checkpoint — Session 11 complete]: pages/details_q1.py (Q1 Performance Deep Dive — back button via st.session_state.pop("_dashboard_details"), insight block, 15-row metrics table with descriptions, 4 charts: cumulative return / return distribution / rolling Sharpe / rolling Beta, Explain Numbers toggle). pages/details_q2.py (Q2 Risk Factors Deep Dive — same structure, 9-row metrics table, 4 charts: correlation heatmap / rolling corr / drawdown / sector weights). Both pages use correct _dashboard_details routing key (pop + rerun). Full suite: 151 passed. Git commit 8a808dd made: "feat: Session 11 — Q1 and Q2 More Details screens".

Next session: Session 12 — details_q3.py (Q3 Risk Outlook Deep Dive) + Risk Preparedness Panel (11 market signals).

[Checkpoint — Session 12 complete]: pages/details_q3.py (Q3 Risk Outlook Deep Dive — insight block with vol tier / GARCH vs hist comparison / tail shape language, Risk Preparedness Panel with all 11 signals in 3-col badge grid, 3 charts: GARCH vol / MC fan / stress test, 11-row metrics table with EWMA/GARCH/hist vol + VaR/CVaR at 95/99 + monthly VaR + skewness/kurtosis). Full suite: 151 passed. Git commit 4a27363 made: "feat: Session 12 — Q3 Risk Outlook Details + Risk Preparedness Panel".

Next session: Session 13 — details_q4.py (Q4 Optimization Deep Dive with estimation error warning).

[Checkpoint — Session 13 complete]: pages/details_q4.py (Q4 Optimization Deep Dive — prominent estimation error st.warning; conditional language throughout; insight block with Sharpe gap analysis / convergence status / vol-saving estimate; efficient frontier chart full width; current-vs-optimal bar chart; interactive weight delta table with formatted Δ columns; 11-row metrics table; Explain Numbers toggle). Full suite: 151 passed. Git commit pending.

Next session: Session 14 — guide.py (5-section methodology reference).

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

## Reading Protocol

Which files to read and in which order, depending on the situation.

**Situation 1 — Clean session start (no rate limit, normal continuation):**
1. Memory files (auto-loaded via MEMORY.md index): user_profile, project_overview, project_session_plan, feedback_general, project_locked_decisions
2. CLAUDE.md (this file) — confirm Current State, identify which session is next
3. Stub file(s) for today's session target — read Dependencies: and docstrings before writing
4. assets/config.py — confirm any constants needed for today's module (colors, SK_ keys, defaults)

**Situation 2 — Rate limit recovery (resuming a partially-completed session):**
1. CLAUDE.md — find last checkpoint line in Current State (this is the resume point)
2. `git diff HEAD` — shows exactly which files changed since last commit
3. Chat history STATUS CHECKPOINT — identifies which batch was in progress when rate limit hit
4. Stub for the in-progress file — resume from where the batch was interrupted

**Situation 3 — Mid-implementation (already in a session, writing a new module):**
1. Stub Dependencies: section for the target module — lists all imports needed
2. assets/config.py — look up any SK_ constants, colors, or defaults referenced
3. Related already-implemented module (e.g., read returns.py before performance.py)

**File authority hierarchy (most to least authoritative):**
- CLAUDE.md Current State — what's actually done
- git log / git diff — what files changed
- Memory files — session plan and preferences
- CHANGELOG.md — human-readable session summary

---

## Standard Session Opening Prompt

"Please read CLAUDE.md first and confirm you understand the current project state.
Then read [specific files needed today]. Today's session goal is [one sentence].
Do not change any decisions in CLAUDE.md without flagging it and waiting for my confirmation.
Before writing any code, describe your implementation plan in a few sentences so I can confirm the approach."
