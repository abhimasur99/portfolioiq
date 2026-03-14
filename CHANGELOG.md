# Changelog

All notable changes to PortfolioIQ are documented here.
Format: [Semantic Version] — Date, with Added / Changed / Fixed / Removed sections.

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
