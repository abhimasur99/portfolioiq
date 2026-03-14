# Changelog

All notable changes to PortfolioIQ are documented here.
Format: [Semantic Version] — Date, with Added / Changed / Fixed / Removed sections.

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
