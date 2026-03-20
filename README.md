# PortfolioIQ

Institutional-grade equity portfolio analytics in a Streamlit web application.
Enter your holdings, get a full four-layer quantitative analysis in plain language.

---

## What it does

PortfolioIQ analyses an equity portfolio across four analytical layers:

| Layer | Quadrant | What it answers |
|-------|----------|-----------------|
| Descriptive | Q1 — Performance | What has this portfolio returned, and at what risk? |
| Diagnostic | Q2 — Risk Factors | Why did it behave this way? Concentration, correlation, drawdown. |
| Predictive | Q3 — Risk Outlook | What could happen? GARCH volatility, VaR, Monte Carlo, stress tests. |
| Prescriptive | Q4 — Optimization | What would a model-optimal allocation look like? |

Everything is displayed in plain language with inline explanations — no finance background required to read the dashboard, but the methodology is rigorous enough to demonstrate FRM/CFA-level quantitative implementation.

---

## Screenshots

_Run locally to see the full interface (dark cockpit theme, Plotly charts, animated ticker tape)._

---

## Quickstart

**Requirements:** Python 3.12, internet access for yfinance data.

```bash
# 1. Clone the repo
git clone <repo-url>
cd portfolio-risk-v3

# 2. Create and activate a virtual environment (Python 3.12 required)
python3.12 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

Open `http://localhost:8501` in your browser. Navigate to **INPUT**, enter 2–10 ticker symbols with dollar amounts, select a benchmark, and click **Analyse Portfolio →**. The analysis window (1Y/3Y/5Y/All/Custom) is selectable on the Dashboard after loading.

---

## Project structure

```
portfolio-risk-v3/
├── app.py                      # Entry point: nav bar, routing, CSS injection
├── requirements.txt
├── assets/
│   ├── config.py               # Colors, constants, SK_ session state keys, defaults
│   └── style.css               # Cockpit dark theme CSS
├── analytics/                  # Pure computation — no Streamlit calls
│   ├── data_fetcher.py         # yfinance download, caching, ticker validation
│   ├── returns.py              # Log returns, portfolio aggregation
│   ├── performance.py          # CAGR, Sharpe, Sortino, Treynor, alpha/beta, rolling
│   ├── risk_factors.py         # Correlation, drawdown, HHI, Effective N, sector weights
│   ├── risk_outlook.py         # GARCH(1,1), EWMA, VaR/CVaR, Monte Carlo, stress tests
│   ├── optimization.py         # Efficient frontier, Max Sharpe, Min Var, Risk Parity
│   └── market_signals.py       # 11 live forward-looking signals via yfinance
├── components/
│   ├── charts.py               # 13 Plotly figure builders (no session state)
│   ├── dashboard_quad.py       # Reusable quadrant layout component
│   └── explain_panel.py        # Explain Numbers overlay (deprecated — superseded by st.metric help= tooltips)
├── pages/
│   ├── input.py                # Screen 1: holdings entry, 7-step pipeline
│   ├── dashboard.py            # Screen 2: 2×2 dashboard, health bar, ticker tape
│   ├── details_q1.py           # Q1 Performance Deep Dive
│   ├── details_q2.py           # Q2 Risk Factors Deep Dive
│   ├── details_q3.py           # Q3 Risk Outlook Deep Dive + Preparedness Panel
│   ├── details_q4.py           # Q4 Optimization Deep Dive
│   ├── guide.py                # How-to-use guide: app flow, quadrant explanations, key limitations
│   └── settings.py             # All configurable parameters, granular recompute
└── tests/
    ├── conftest.py             # 800-day mock data fixtures (seed 42, 4 tickers)
    ├── test_data_fetcher.py
    ├── test_returns.py
    ├── test_performance.py
    ├── test_risk_factors.py
    ├── test_risk_outlook.py
    ├── test_optimization.py
    └── test_market_signals.py
```

---

## Analytics — methodology summary

### Returns
Log returns throughout: `rt = ln(Pt / Pt-1)`. Time-additive, consistent with GARCH fitting and Monte Carlo path generation. All ratios annualised with ×√252.

### Performance (Layer 1)
CAGR, annualised volatility, Sharpe, Sortino, Treynor, Information Ratio, Jensen's alpha, beta, R-squared, rolling 252-day Sharpe and beta, best/worst month and year. Risk-free rate fetched live from `^IRX` (13-week T-bill).

### Risk Factors (Layer 2)
Full and rolling 60-day correlation matrices, annualised covariance (PD-checked, 1e-6 regularisation), HHI, Effective N (1/HHI), Diversification Ratio, drawdown series, max drawdown, Calmar, recovery days, Ulcer Index, sector weights (yfinance, best-effort).

### Risk Outlook (Layer 3)
- **Volatility:** Historical (√252), EWMA (λ=0.94 RiskMetrics), GARCH(1,1) via `arch` 6.3.0 (MLE on percentage log returns; stationarity check α+β<1; EWMA fallback if non-stationary or <252 obs)
- **VaR/CVaR:** Historical at 95% and 99%; GARCH-VaR (normal quantile); monthly scaling (×√21)
- **Distribution:** skewness, excess kurtosis
- **Monte Carlo:** 1,000 paths (configurable to 10,000), GARCH-driven dynamics, vectorised over paths, sequential loop over steps; 10th/50th/90th percentile fan
- **Stress tests:** portfolio return = α + β × scenario index return for 4 historical crises (2008 GFC, 2020 COVID, 2000 Dot-Com, 2022 Rate Shock)

### Optimization (Layer 4)
All three optimizers use `scipy.optimize.minimize` with SLSQP, equal-weight initialisation, configurable weight bounds:
- **Max Sharpe:** minimise −(w⊤μ − Rf) / √(w⊤Σw)
- **Min Variance:** minimise w⊤Σw
- **Risk Parity:** minimise Σ(wᵢ·(Σw)ᵢ − σ²_p/N)² (unnormalized ERC objective)
- **Efficient frontier:** 50 points from min-variance return to feasible maximum (LP upper bound), warm-started
- Expected returns and covariance annualised from daily log returns (μ×252, Σ×252)

### Market Signals (Layer 4)
11 live signals fetched fresh on each portfolio load (no cache): VIX level/trend/term structure, MOVE index, yield curve (10yr−30yr), credit spreads (HYG/IEF proxy), copper/gold ratio, dollar index, oil sensitivity, rate sensitivity, tech concentration (unavailable — no reliable sector feed in yfinance).

---

## Running tests

```bash
pytest tests/ -v
```

151 tests (150 passing, 1 known pre-existing test/implementation mismatch in validate_tickers network-failure behavior), 0 skipped. Coverage includes: log return formula, portfolio weighting, all performance ratio zero-guards, correlation identity/range, drawdown non-positivity, GARCH stationarity (α+β<1), EWMA fallback trigger, VaR ordering (CVaR < VaR), Monte Carlo shape and positivity, stress test structure, optimizer weight constraints (sum-to-one, non-negative, within bounds), frontier length and shape.

---

## Configuration

All settings are adjustable at runtime via the **Settings** screen without restarting:

| Setting | Default | Effect |
|---------|---------|--------|
| Benchmark | SPY | Alpha, beta, Info Ratio, Treynor benchmark |
| VaR confidence | 95% | VaR and CVaR threshold |
| VaR method | Historical | Historical empirical vs GARCH-normal |
| MC horizon | 1 year | Monte Carlo projection length (options: 1, 2, 3, 5 years) |
| MC paths | 1,000 | Simulation paths (10,000 for smoother bands) |
| Weight min | 5% | Lower bound for all three optimizers |
| Weight max | 90% | Upper bound for all three optimizers |

Changing VaR/MC/GARCH settings triggers targeted recomputation of the risk outlook layer only. Changing weight bounds triggers optimization only. Changing benchmark requires a full data re-fetch from the Input screen. The analysis window (1Y/3Y/5Y/All/Custom) is selected on the Dashboard and does not require re-fetching data.

---

## Navigation

```
INPUT → DASHBOARD → [More Details Q1–Q4 via quadrant buttons] → GUIDE / SETTINGS
```

The nav bar has exactly four items: INPUT, DASHBOARD, GUIDE, SETTINGS. More Details screens are accessed only via the "More Details →" button on each quadrant — never from the nav bar directly.

---

## Disclaimer

PortfolioIQ is an educational and analytical tool. It is not a registered investment adviser and does not provide investment advice. All outputs are based on historical data and model assumptions. Past performance does not predict future results. Optimizer outputs are historically optimal under specific model assumptions — they are not investment recommendations. Always consult a qualified financial adviser before making investment decisions.

---

## Tech stack

| Library | Version | Purpose |
|---------|---------|---------|
| Streamlit | 1.32.0 | Web UI framework |
| yfinance | 0.2.66 | Market data |
| pandas | 2.2.0 | DataFrames |
| numpy | 1.26.0 | Numerical computation |
| scipy | 1.12.0 | SLSQP optimization |
| arch | 6.3.0 | GARCH(1,1) MLE fitting |
| plotly | 5.20.0 | Interactive charts |
| pytest | 8.0.0 | Test framework |
| pytest-mock | 3.12.0 | Mock fixtures |

Python 3.12 (arch 6.3.0 confirmed working on 3.12).
