# Changelog

All notable changes to PortfolioIQ are documented here.
Format: [Semantic Version] — Date, with Added / Changed / Fixed / Removed sections.

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
