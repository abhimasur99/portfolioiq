# Changelog

All notable changes to PortfolioIQ are documented here.
Format: [Semantic Version] — Date, with Added / Changed / Fixed / Removed sections.

---

## [0.24.0] — 2026-03-20

### Added
- `components/charts.py` `drawdown_chart()`: Optional `benchmark_drawdown` + `benchmark_label` params — renders portfolio drawdown (red/filled) and benchmark drawdown (gray dotted) on the same chart when benchmark data is provided.
- `pages/details_q2.py`: Benchmark drawdown overlay — reads `SK_BENCH_RETURNS`, computes benchmark drawdown series, passes to `drawdown_chart()`.
- `analytics/risk_outlook.py`: `_compute_ewma_series_pct()` — computes rolling EWMA conditional vol series (pct units) for use as a fallback trace in the GARCH chart. Stored as `ewma_series` in the risk outlook output dict.
- `components/charts.py` `garch_volatility_chart()`: Optional `ewma_series` param — when GARCH falls back due to insufficient data (`garch_result = None`), plots EWMA rolling series in `COLOR_PURPLE` labeled "EWMA Cond. Vol (fallback)", distinguishing it from the blue GARCH trace shown on 3Y/5Y.
- `components/charts.py` `signal_scenario_chart()`: `total_value` param — bars show combined "% / −$" labels when portfolio dollar value is available. `use_monthly` param — toggles between 1-Day and 1-Month VaR display.
- `pages/details_q3.py`: Daily/Monthly horizon toggle (radio) above the Signal Sensitivity chart.

### Changed
- `pages/details_q3.py` `_compute_signal_scenarios()`: Upgraded from normal-distribution VaR (`-1.645 × σ`) to **Filtered Historical Simulation (FHS)** — scales the actual empirical 5th-percentile daily return by the vol ratio (`σ_stressed / σ_hist_daily`). Preserves portfolio fat-tail and skew properties without distribution assumptions. Falls back to normal VaR if `hist_vol` or `var_95_hist` are unavailable.
- `pages/dashboard.py` `_build_q3()`: Reads `SK_VAR_METHOD` — shows `var_95_garch` when GARCH method selected, else `var_95_hist` (historical).
- `pages/details_q3.py` Key Metrics panel: VaR 95% label switches between Historical and GARCH based on `SK_VAR_METHOD`. CVaR always uses historical (noted in help text).
- `pages/details_q1.py` Return Distribution chart: VaR marker line uses `var_95_garch` when GARCH method selected, else `var_95_hist`.
- `pages/settings.py` VaR method selector: Expanded help text explaining the practical difference between historical and GARCH VaR, noting CVaR always uses historical.

---

## [0.23.0] — 2026-03-20

### Fixed
- `components/charts.py` `rolling_sharpe_chart()`: `IndexError` crash when 1Y window selected — all-NaN rolling series after dropna produced empty Series; `s.iloc[-1]` raised `IndexError`. Fixed with empty-Series guard returning a placeholder figure.
- `components/charts.py` `rolling_beta_chart()`: Same empty-Series guard added for consistency.
- `pages/dashboard.py` `_render_holdings_strip()`: Holdings with weight < 8% showed no label — replaced threshold-based inline label with a persistent color-coded label row below the bar; all holdings always visible.

### Added
- `assets/config.py`: `SK_TOTAL_VALUE` session state key — total portfolio USD value entered by user.
- `analytics/performance.py` `compute_all_performance()`: Adaptive rolling window — uses 252-day window when data ≥ 253 rows; falls back to `max(21, n // 3)` for shorter windows (e.g. ~83-day for 1Y). Stores `rolling_sharpe_window` and `rolling_beta_window` in output dict.
- `pages/details_q1.py`: Disclosure caption shown below rolling charts when window < 252 days.

### Changed
- `assets/config.py` `BENCHMARK_OPTIONS`: Removed `"US Agg Bond (AGG)"` — equities-only app; bond benchmark produces conceptually meaningless alpha and beta. See D-12.
- `pages/dashboard.py` `_WINDOW_OPTIONS`: Removed "All" and "Custom" — time frame selector now shows 1Y / 3Y / 5Y only. Custom deferred to v2.
- `components/charts.py` `rolling_sharpe_chart()` and `rolling_beta_chart()`: Added `window` parameter (default 252); chart title reflects actual window used.
- `components/charts.py` `monte_carlo_fan_chart()`: `yaxis_title` changed from verbose `"Portfolio Value (base = X)"` to `"Portfolio Value ($)"`. `initial_value` now passed from actual portfolio dollar value.
- `components/charts.py` `signal_scenario_chart()`: Added `margin=dict(t=70)` to increase space between subtitle and bars.
- `pages/input.py`: Stores `SK_TOTAL_VALUE` (total portfolio USD) in session state after pipeline completes.
- `pages/dashboard.py` `_build_q3()`: Passes `SK_TOTAL_VALUE` as `initial_value` to `monte_carlo_fan_chart()`.
- `pages/details_q3.py`: Swapped chart order — Signal-Based Sensitivity Analysis now appears before Monte Carlo fan. Passes `SK_TOTAL_VALUE` to `monte_carlo_fan_chart()`.
- `DECISIONS.md`: Added D-12 — AGG removed from benchmark options.

---

## [0.22.0] — 2026-03-20

### Added
- `pages/dashboard.py` `_recompute_for_window()`: Full analytics recompute when user changes analysis window. Slices the stored 5-year price data to the selected window and re-runs all four analytics layers.
- `pages/dashboard.py` `_render_time_selector()`: Analysis window selector bar — 1Y / 3Y / 5Y / All / Custom. Custom selection shows inline date pickers. Triggers `_recompute_for_window()` on change. Replaces period selection in Input and Settings.
- `assets/config.py`: Three new session state keys — `SK_ANALYSIS_START`, `SK_ANALYSIS_END` (active window boundaries as date strings), `SK_PRICE_DATA_FULL` (full 5y prices stored at analysis time).

### Changed
- `analytics/data_fetcher.py` `fetch_price_data()`: Removed `period` parameter. Always fetches `period="5y"`. Cache key is tickers only.
- `pages/input.py`: Removed period selectbox. Pipeline stores full 5y prices in `SK_PRICE_DATA_FULL`, computes analytics on 3y default window, sets `SK_ANALYSIS_START`/`SK_ANALYSIS_END`.
- `pages/dashboard.py` `render()`: Added context badge above health bar — "3-Year Analysis | Benchmark: SPY | Data as of [date]". Replaces Stage D data freshness caption. Added time frame selector bar below context badge.
- `pages/settings.py`: Removed Period section (period now controlled on dashboard). Removed Rebalancing section (drift threshold deferred to v2). Settings now has 4 sections: Portfolio (benchmark only), Risk, Monte Carlo, Weight Bounds. MC horizon options updated to `[1, 2, 3, 5]` years.
- `assets/config.py`: `DEFAULT_MC_HORIZON` changed from 10 to 1. Removed `"60/40 Blend (SPY+AGG)"` from `BENCHMARK_OPTIONS` (misleading fallback — deferred to v2, see D-11). Removed `PERIOD_OPTIONS` (no longer used in UI).
- `pages/details_q2.py`: Removed Beta insight block from At a Glance — Beta is a Q1 performance metric, not a Q2 structural diagnostic.
- `pages/details_q3.py`: Stacked GARCH vol, Monte Carlo fan, and Signal Sensitivity charts full-width vertically (was side-by-side 50/50 columns). Updated MC caption to reflect 1-year default. Charts are now visually balanced.
- `components/charts.py` `signal_scenario_chart()`: Bars now show losses as downward from zero. Y-axis inverted (losses go below zero), consistent with loss convention. Bar annotations show multiplier labels and exact monthly VaR % on each bar.
- `DECISIONS.md`: Added D-11 — 60/40 composite benchmark deferred to v2.

### Removed
- `pages/settings.py`: Period section and Rebalancing (drift threshold) section removed.
- `assets/config.py`: `PERIOD_OPTIONS` removed.

---

## [0.21.0] — 2026-03-19

### Added
- `pages/dashboard.py` `_route_details()`: Cross-quadrant navigation — prev/next buttons alongside "← Dashboard" so users can move directly between Q1→Q2→Q3→Q4 More Details without returning to the dashboard.
- `pages/dashboard.py` `render()`: Data freshness caption — "Market data as of [date] — reflects previous market close. Analytics do not update during trading hours."
- `components/charts.py` `signal_scenario_chart()`: New chart replacing historical stress tests. Shows three GARCH-volatility-scaled scenarios (Moderate 1.5×, Significant 2.0×, Severe 3.0×) with the current-environment scenario highlighted based on live signal statuses.
- `pages/details_q3.py` `_compute_signal_scenarios()`: Private helper computing signal-driven scenarios from GARCH vol + signal red/amber counts → environment level (Calm/Elevated/Stressed/Severe).

### Changed
- `pages/details_q3.py`: Replaced historical crisis stress test chart (GFC, Dot-Com, COVID, Rate Shock) with Signal-Based Sensitivity Analysis. Environment assessment badge added to At a Glance block.
- `pages/details_q3.py` `_render_preparedness_panel()`: Tech Concentration now shows "⚪ Coming Soon" instead of "⚪ n/a". Panel caption updated — removed "live" language, now says "fetched fresh at portfolio analysis time using end-of-day data."
- `analytics/market_signals.py` `_sig_tech_concentration()`: Updated interpretation to "Coming in v2 — tech sector concentration requires an enhanced sector data feed not available from yfinance."
- `assets/config.py`: `DEFAULT_WEIGHT_MAX` raised from 0.50 to 0.90 — allows concentrated portfolios to express up to 90% single-position weight in optimizer output.
- `pages/guide.py`: Minor wording improvements — "non-stationary" → "constantly evolving", "characterised" → "described", "11 live market signals" → "11 market environment signals fetched fresh at each session from end-of-day data."

---

## [0.20.0] — 2026-03-15

### Changed
- `pages/guide.py`: Complete redesign (Stage C / TL-007). Replaced 5 wide 4-column methodology tables with a readable 3-section layout: (1) How to Use — 4-step walkthrough, (2) What Each Quadrant Tells You — one paragraph per quadrant, (3) Key Limitations — 4 concise bullets. Version bumped to v1.1. `pandas` import removed.

### Removed
- All metric-by-metric formula/limitation tables from guide.py (`_PERF_ROWS`, `_RISK_FACTORS_ROWS`, `_RISK_OUTLOOK_ROWS`, `_OPTIMIZATION_ROWS`, `_SIGNALS_ROWS`, `_render_table`). Metric definitions now live in ? tooltips on every KPI tile.

---

## [0.19.0] — 2026-03-15

### Fixed
- `app.py`: Navigating away from Dashboard (to INPUT, GUIDE, or SETTINGS) now clears `_dashboard_details`, so returning to Dashboard always shows the main dashboard, not a More Details sub-page.

### Changed
- `pages/details_q1.py`, `details_q2.py`, `details_q3.py`: Replaced Key Metrics `st.dataframe` summary tables with `st.metric()` grids (2 per row) carrying `help=` tooltip text on every metric.
- `pages/details_q3.py` `_render_preparedness_panel()`: Converted 11-signal HTML card grid to `st.metric()` tiles; interpretation text moved into the `help=` tooltip. Unused color imports removed.

---

## [0.18.0] — 2026-03-15

### Changed
- `components/dashboard_quad.py`: Added `help=kpi.get("help")` to `st.metric()` calls — renders inline `?` tooltip on hover for every KPI tile. Removed "Explain Numbers" toggle button and explain panel block. "More Details →" is now the only action button per quadrant.
- `pages/dashboard.py` `_build_q1/q2/q3/q4()`: Added `"help"` key to all 16 KPI dicts with concise 1–2 sentence tooltip text per metric.
- `pages/dashboard.py` `_health_indicators()`: Reordered health signals — Market Stress → Return Quality → Volatility → Drawdown Risk → Diversification → Efficiency.
- `pages/details_q1.py`, `details_q2.py`, `details_q3.py`, `details_q4.py`: Removed "All Metrics" dataframe table and "Explain Numbers" toggle + explain panel from all four details screens.

### Removed
- `components/explain_panel.py` is now unreferenced — no longer called from any page.

---

## [0.17.0] — 2026-03-15

### Fixed
- `assets/style.css`: Ticker tape animation class mismatch — HTML used `ticker-tape`/`ticker-tape-content`; CSS targets `ticker-tape-container`/`ticker-tape-track`. Fixed HTML class names in `_render_ticker_tape()`. (TL-003)
- `assets/style.css`: Ticker scroll speed reduced from 60s to 30s for better readability.
- `pages/dashboard.py` `_render_holdings_strip()`: Replaced per-ticker price columns with a single full-width stacked segmented breakdown bar; each ticker gets a color-coded segment proportional to weight, labelled with symbol and percentage. (TL-005 / TL-016)
- `pages/dashboard.py` `_check_loaded()`: "Go to Input →" button did nothing — now sets `_nav_pending` + reruns correctly. (TL-014 related)
- `components/charts.py` `correlation_heatmap()`: Text on near-zero (white background) cells was invisible — changed to `#000000` for abs(val) < 0.6, `COLOR_TEXT` for abs(val) >= 0.6. (TL-008)
- `analytics/risk_factors.py` `fetch_sector_weights()`: ETFs labeled "Unknown" sector — added `quoteType` check; ETF/MUTUALFUND quote types now labeled "ETF / Fund". (TL-009)
- `assets/config.py` `STRESS_SCENARIOS`: Reordered to chronological — 2000 Dot-Com → 2008 GFC → 2020 COVID → 2022 Rate Shock. (TL-011)
- `pages/details_q4.py`: Warning title changed from "Estimation Error Warning" to "Optimizer Assumptions". (TL-012)
- `pages/settings.py`: Weight bounds and drift threshold sliders showed "0 to 0" / "1 to 1" — switched from float (0.0–1.0) + `format="%.0f%%"` to integer (0–100) + `format="%d%%"`, converting back to decimal on save. (TL-015)
- `app.py` + `pages/input.py`: Auto-redirect to Dashboard after re-analyse failed on second run — replaced `key="nav_radio"` approach (blocked by Streamlit widget-state restriction) with `_nav_pending` / `_current_nav` plain-key pattern; `index=` only passed to radio when programmatic override is needed, eliminating two-click lag. (TL-014)

---

## [0.16.0] — 2026-03-13

### Fixed
- `pages/dashboard.py` `_health_indicators()`: Drawdown Risk indicator read `perf.get("max_drawdown")` — key lives in `risk_factors`. Fixed to `rf.get("max_drawdown")`.
- `pages/dashboard.py` `_build_q1()`: Max DD KPI tile read `perf.get("max_drawdown")` — same wrong dict. Fixed to `analytics.get(SK_RISK_FACTORS, {}).get("max_drawdown")`.
- `pages/dashboard.py` `_build_q2()`: Correlation heatmap read `rf.get("correlation_matrix")` — correct key is `"corr_matrix"`. Fixed. Was always rendering the empty fallback figure.
- `components/explain_panel.py` Q1 panel: Max Drawdown display read `perf.get("max_drawdown")`. Fixed to `rf.get("max_drawdown")`.

### Added
- `README.md`: full project README — quickstart, project structure, analytics methodology summary (all 4 layers), test instructions, configuration table, navigation guide, tech stack table, disclaimer.

---

## [0.15.0] — 2026-03-13

### Added
- `pages/settings.py` (Session 15): full Settings screen — five grouped sections (Portfolio, Risk, Monte Carlo, Weight Bounds, Rebalancing); granular Save and Recompute button that detects which settings changed and recomputes only affected analytics layers (VaR/method/GARCH → risk_outlook; MC horizon/paths → risk_outlook; weight bounds → optimization; benchmark/period → informational redirect to Input since price re-fetch required); Restore Defaults button; current-values summary card when portfolio is loaded; all SK_ constants used, no raw string literals.

---

## [0.14.0] — 2026-03-13

### Added
- `pages/guide.py` (Session 14): full Guide screen — introductory framing paragraph (conditional characterisation, not prediction), five 4-column methodology tables (Metric / Formula-Method / What it tells you / Key assumption-limitation) covering Performance, Risk Factors, Risk Outlook, Optimization, and Leading Indicators; closing signal limitations statement; version date footer.

---

## [0.13.0] — 2026-03-13

### Added
- `pages/details_q4.py` (Session 13): Q4 Optimization Deep Dive — back button, prominent estimation error warning (conditional language throughout; never prescriptive), insight block (Sharpe gap, convergence status, weight concentration of each optimizer output), efficient frontier chart (full width, all 3 optimizer portfolios + current portfolio + CML), current-vs-optimal bar chart, interactive weight delta table (current / max-sharpe / min-var / risk-parity weights + deltas per ticker), full 9-row metrics table (returns/vols/ratios for all 3 portfolios + CML slope + convergence flag), inline Explain Numbers panel.

---

## [0.12.0] — 2026-03-13

### Added
- `pages/details_q3.py` (Session 12): Q3 Risk Outlook Deep Dive — back button, plain-language insight block (VaR/vol tier language), Risk Preparedness Panel (all 11 live signals in a 3-column badge grid with status colour, value, and one-line interpretation; "unavailable" signals shown greyed out; signal disclaimer), three charts (GARCH volatility, Monte Carlo fan, stress test bar), full 11-row metrics table (hist/EWMA/GARCH vol, VaR 95/99, CVaR 95/99, monthly VaR, skewness, excess kurtosis, GARCH fallback flag), inline Explain Numbers panel.

---

## [0.11.0] — 2026-03-13

### Added
- `pages/details_q1.py` (Session 11): Q1 Performance Deep Dive — back button (clears `_dashboard_details` routing key), plain-language insight block, full 12-metric table (CAGR, Sharpe, Sortino, Treynor, Info Ratio, Alpha, Beta, R², Vol, Best/Worst Month, Best/Worst Year, Max DD, Calmar), four charts (cumulative return, return distribution with VaR/CVaR lines, rolling Sharpe, rolling Beta), inline Explain Numbers panel.
- `pages/details_q2.py` (Session 11): Q2 Risk Factors Deep Dive — back button, insight block, full metrics table (HHI, Effective N, Diversification Ratio, Max Drawdown, Calmar, Recovery Days, Ulcer Index, Beta), four charts (correlation heatmap, rolling 60-day correlation, drawdown chart, sector weights), inline Explain Numbers panel.


---

## [0.10.0] — 2026-03-13

### Added
- `components/dashboard_quad.py` (Session 10): `render_quadrant()` — quadrant header with flag badge, compact 260px Plotly chart, 3–4 st.metric KPI tiles, Explain Numbers toggle button + inline explain panel, More Details routing button.
- `components/explain_panel.py` (Session 10): `render_explain_panel()` — contextual plain-language metric explanations per quadrant (Q1 performance, Q2 risk factors, Q3 risk outlook, Q4 optimization), populated from live analytics values, limitation disclosure + Guide link at bottom.
- `pages/dashboard.py` (Session 10): full Dashboard screen — guard redirect if portfolio not loaded; CSS ticker tape (latest prices + 1-day change); holdings strip (ticker, weight, latest price per asset); 6-indicator health bar (return quality, volatility, diversification, drawdown, market stress, portfolio efficiency); 2×2 quadrant grid calling render_quadrant for Q1–Q4 with pre-built charts, KPIs, and flags from session state analytics; More Details routing via `_dashboard_details` session key.

---

## [0.9.0] — 2026-03-13

### Added
- `pages/input.py` (Session 9): full Portfolio Input screen — `st.data_editor` ticker/amount table (2–10 rows, dynamic), live weight preview with bound-violation highlighting, benchmark + period selectors, disclaimer accordion + checkbox gate, 7-step analytics pipeline (`_run_pipeline`) with `st.progress` bar and per-step status text. On success: all session state keys populated (SK_TICKERS, SK_WEIGHTS, SK_PRICE_DATA, SK_RETURNS_DF, SK_PORT_RETURNS, SK_BENCH_RETURNS, SK_RISK_FREE_RATE, SK_ANALYTICS dict with performance/risk_factors/risk_outlook/optimization/market_signals), SK_PORTFOLIO_LOADED = True, `st.rerun()` to dashboard.

---

## [0.8.0] — 2026-03-13

### Added
- `components/charts.py` (Session 8): all 13 Plotly figure builders — `cumulative_return_chart`, `return_distribution_chart`, `rolling_sharpe_chart`, `rolling_beta_chart`, `correlation_heatmap`, `rolling_correlation_chart`, `drawdown_chart`, `sector_weights_chart`, `garch_volatility_chart`, `monte_carlo_fan_chart`, `stress_test_chart`, `efficient_frontier_chart`, `current_vs_optimal_chart`. All use PLOTLY_TEMPLATE_NAME; all colors from config.py constants. No hardcoded color strings.

---

## [0.7.0] — 2026-03-13

### Added
- `analytics/optimization.py` (Session 7): `_optimize_min_variance`, `_optimize_max_sharpe`, `_optimize_risk_parity` (equal risk contribution via unnormalized squared-difference objective), `_compute_frontier` (50 points, feasible-max upper bound, warm-start), `compute_all_optimization` (master aggregator — frontier_vols, frontier_returns, frontier_weights, max_sharpe_weights/return/vol/ratio, min_var_weights/return/vol, risk_parity_weights/return/vol, cml_slope, weight_delta_table, optimizer_converged).
- `tests/test_optimization.py` (Session 7): 12 previously skipped tests now passing — weight sum-to-one, non-negative, bounds check for max Sharpe / min var / risk parity; frontier length (50), frontier returns monotonically increasing, frontier vols U-shaped (min at left end). 0 skipped in optimization tests.

---

## [0.6.0] — 2026-03-13

### Added
- `analytics/risk_outlook.py` (Session 6): `_run_garch_monte_carlo` (vectorized GARCH-MC, loop over steps only, numpy vectorized over paths), `_run_stress_tests` (alpha + beta × scenario_return for all 4 STRESS_SCENARIOS), `compute_all_risk_outlook` (master aggregator, complete).
- `analytics/market_signals.py`: `fetch_all_signals` with all 11 signals — VIX level, VIX trend, VIX term structure, MOVE index, yield curve, credit spreads, copper-to-gold ratio, dollar index, oil sensitivity, rate sensitivity, tech concentration. Graceful fallback to "unavailable" per signal on fetch failure.
- `tests/test_risk_outlook.py` (Session 6): MC shape, MC positive values, stress test keys — all previously skipped tests now passing. 0 skipped in risk_outlook tests.
- `tests/test_market_signals.py`: all 6 tests — signal keys structure, status validity, oil/rate sensitivity range, VIX level positive, yield curve finite.

---

## [0.5.0] — 2026-03-13

### Added
- `analytics/risk_outlook.py` (Session 5 functions): `compute_historical_vol`, `compute_ewma_vol` (λ=0.94 RiskMetrics), `fit_garch` (GARCH(1,1) via arch 6.3.0, stationarity check α+β<1, EWMA fallback if <252 obs or non-stationary), `compute_var_cvar_historical` (5th/1st percentile, tail mean), `compute_garch_var` (normal distribution VaR), `compute_var_monthly` (×√21 i.i.d. scaling), `compute_skewness_kurtosis`.
- `tests/test_risk_outlook.py` (Session 5 tests): 9 tests covering historical VaR at 95th/99th percentile, CVaR < VaR, GARCH stationarity (α+β<1), EWMA fallback trigger, EWMA vol positive. Session 6 tests (MC, stress) remain skipped.

---

## [0.4.0] — 2026-03-13

### Added
- `analytics/risk_factors.py`: `compute_correlation_matrix`, `compute_rolling_correlation` (60-day), `compute_covariance_matrix` (annualized, PD-checked with 1e-6 regularization), `compute_hhi`, `compute_effective_n`, `compute_diversification_ratio`, `compute_drawdown_series`, `compute_max_drawdown`, `compute_calmar`, `compute_recovery_time`, `compute_ulcer_index`, `fetch_sector_weights` (live yfinance, best-effort), `compute_all_risk_factors`.
- `tests/test_risk_factors.py`: 14 unit tests covering Pearson correlation identity and range, HHI/Effective N for equal weights, diversification ratio (single asset = 1.0), drawdown non-positivity, max drawdown on known path, Calmar zero-guard, Ulcer Index on flat series, and covariance positive-definiteness.

---

## [0.3.0] — 2026-03-13

### Added
- `analytics/returns.py`: `compute_log_returns` (rt = ln(Pt/Pt-1)), `compute_portfolio_returns` (dot product with weight-sum validation).
- `analytics/performance.py`: `compute_cagr`, `compute_sharpe`, `compute_sortino`, `compute_treynor`, `compute_info_ratio`, `compute_alpha_beta` (Jensen's alpha, beta, R²), `compute_rolling_sharpe`, `compute_rolling_beta`, `compute_best_worst_periods`, `compute_all_performance`. All zero-denominator protected.
- `tests/test_returns.py`: 7 unit tests covering log return formula, shape, NaN-free output, portfolio weighting, weight normalization error, and single-asset edge case.
- `tests/test_performance.py`: 10 unit tests covering CAGR manual verification, Sharpe, Sortino (downside-only), Treynor, beta vs OLS, R² vs correlation, all three zero-denominator guards, and rolling metric lengths.

### Changed
- `CLAUDE.md`: added Reading Protocol section (3 situations), fixed stale "Git commit pending" checkpoint from Session 2.

---

## [0.2.0] — 2026-03-13

### Added
- `tests/conftest.py`: complete mock data fixtures — 800 trading days, 4 tickers (AAPL/MSFT/GOOGL/SPY), correlated log-normal prices with stress period (2× vol, days 200–299), drawdown (days 300–379), and recovery (days 380–449). Seed 42. All fixtures implemented.
- `analytics/data_fetcher.py`: full yfinance data layer — batched multi-ticker download, explicit MultiIndex column handling, Adj Close extraction, NaN dropping, ticker validation, exponential backoff (1s/2s/4s) on rate limit, `^IRX` fetch with /100/252 conversion and fallback, 1-hour Streamlit cache on price data, fresh fetch for market signals.
- `tests/test_data_fetcher.py`: unit tests for data fetcher — MultiIndex handling, NaN dropping, invalid ticker error, `^IRX` conversion, fallback rate, and mock fixture structure.

---

## [0.1.0] — 2026-03-13

### Added
- Complete project scaffolding (Session 1)
- `requirements.txt`: 9 dependencies pinned exactly (Streamlit, yfinance, pandas, numpy, scipy, arch, Plotly, pytest, pytest-mock)
- `.gitignore`: Python artifacts, virtual environments, Streamlit secrets, test artifacts
- `.streamlit/config.toml`: dark theme base, background colors, text color, font
- `assets/config.py`: full color palette, typography constants, Plotly "portfolioiq" dark template registered at import, all SK_ session state key constants, all DEFAULT_ constants, BENCHMARK_OPTIONS, PERIOD_OPTIONS, STRESS_SCENARIOS, DISCLAIMER_SHORT, DISCLAIMER_FULL, all market signal tickers
- `assets/style.css`: cockpit dark theme CSS — Google Fonts import, dark backgrounds, metric tiles, buttons, inputs, ticker tape animation, disclaimer footer, signal badges
- `app.py`: entry point with CSS injection, session state initialization, 4-item nav bar (INPUT / DASHBOARD / GUIDE / SETTINGS), page routing, footer disclaimer
- `pages/`: 8 page stubs — input, dashboard, details_q1–q4, guide, settings — each with full docstrings and `render()` function signatures
- `analytics/`: 7 module stubs — data_fetcher, returns, performance, risk_factors, risk_outlook, optimization, market_signals — each with full docstrings, function signatures, and mathematical specifications
- `components/`: 3 component stubs — charts, dashboard_quad, explain_panel — with full docstrings and function signatures
- `tests/`: `conftest.py` + 6 test files — test_returns, test_performance, test_risk_factors, test_risk_outlook, test_optimization, test_market_signals — with complete test plans (all tests skipped pending implementation)
- `CLAUDE.md`: project memory file with module responsibilities, naming conventions, 15 locked architectural decisions, known issues, current state, session continuity protocol
- `DECISIONS.md`: 10 architectural decision log entries (D-01 through D-10)
