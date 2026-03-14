# DECISIONS.md — Architectural Decision Log

Every significant design decision is recorded here with context, options considered,
the decision made, rationale, and consequences.
Never delete entries — mark superseded decisions as SUPERSEDED and add a new entry.

---

## D-01: Log Returns vs Simple Returns

**Date:** 2026-03-13
**Status:** LOCKED

**Context:** Every return computation in the application — CAGR, Sharpe, beta, VaR, GARCH,
Monte Carlo — requires a consistent return definition.

**Options considered:**
1. Simple returns: Rt = (Pt - Pt-1) / Pt-1
2. Log returns: rt = ln(Pt / Pt-1)

**Decision:** Log returns throughout.

**Rationale:**
- Time-additive: sum of daily log returns = total log return. Simple returns are not additive.
- Approximately symmetric (no lower bound of -1).
- Better statistical properties for MLE-based models (GARCH fitting).
- Industry standard in quantitative finance and FRM curriculum.
- Consistency is the primary concern — mixing return types is a common source of subtle bugs.

**Consequences:**
- GARCH library fitted on percentage log returns (multiply by 100 before fit, divide by 100 after).
- All VaR and CVaR computed on log returns and displayed as such.
- CAGR requires exponentiation: total_return = exp(sum(log_returns)) - 1.
- Small numerical difference vs simple returns for typical daily ranges (< 0.5%).

---

## D-02: Python 3.11 Specifically

**Date:** 2026-03-13
**Status:** LOCKED

**Context:** Python version selection affects the arch library for GARCH fitting.

**Options considered:**
1. Python 3.12 (latest stable)
2. Python 3.11

**Decision:** Python 3.11.

**Rationale:**
- arch library (GARCH) has documented dependency conflicts with Python 3.12 in some configurations.
- Streamlit 1.32 fully supports 3.11.
- All other dependencies (numpy 1.26, scipy 1.12, pandas 2.2) support 3.11.

**Consequences:**
- Virtual environment must be created with Python 3.11 explicitly.
- Deployment environment must specify Python 3.11.

---

## D-03: GARCH(1,1) via arch Library

**Date:** 2026-03-13
**Status:** LOCKED

**Context:** Volatility estimation requires a model that captures clustering (volatility
persistence). Multiple libraries and specifications were considered.

**Options considered:**
1. GARCH(1,1) via arch library
2. GARCH via statsmodels
3. Manual numpy GARCH implementation
4. EWMA only (simpler, no fitting required)

**Decision:** GARCH(1,1) via arch library, with EWMA fallback.

**Rationale:**
- arch library is the standard Python GARCH library with MLE fitting.
- GARCH(1,1) is sufficient for financial returns and is the FRM standard.
- EWMA fallback when: (a) stationarity condition alpha+beta >= 1, or (b) fewer than 252 obs.
- Demonstrates more technical depth than EWMA-only for the portfolio showcase purpose.

**Consequences:**
- arch library requires a C compiler (Visual Studio on Windows, Xcode CLI on Mac).
- GARCH must be fitted on percentage returns (multiply by 100); divide output by 100.
- disp=False required to suppress verbose optimization output in Streamlit.
- Stationarity check (alpha+beta < 1) must run after every fit — most important test in suite.
- Refitting on every portfolio load is the default behavior.

---

## D-04: scipy SLSQP for All Three Optimizers

**Date:** 2026-03-13
**Status:** LOCKED

**Context:** Portfolio optimization requires constrained minimization.

**Options considered:**
1. scipy.optimize.minimize with SLSQP method
2. cvxpy (convex optimization library)
3. PyPortfolioOpt library

**Decision:** scipy.optimize.minimize with method='SLSQP'.

**Rationale:**
- scipy is already a dependency. No additional library required.
- SLSQP handles equality and inequality constraints natively.
- Sufficient precision for all three portfolios (max Sharpe, min variance, risk parity).
- Demonstrates from-scratch implementation rather than hiding behind a high-level abstraction — more impressive for a portfolio project.

**Consequences:**
- Max Sharpe objective: minimize negative Sharpe (-(Rp - Rf) / portfolio_vol).
- Min variance: minimize portfolio variance directly.
- Risk parity: minimize sum of squared (risk contribution - equal target) differences.
- Risk parity tolerance 1e-10, max_iter 1000.
- Optimizer non-convergence surfaces message suggesting wider weight bounds; falls back to min variance.

---

## D-05: Equal-Weight Initialization for Optimization

**Date:** 2026-03-13
**Status:** LOCKED

**Context:** The starting point for constrained optimization affects whether the solver
finds the global optimum or a local minimum.

**Options considered:**
1. Initialize from user's current weights
2. Initialize from equal weights (1/N)
3. Random restarts

**Decision:** Always initialize from equal weights (1/N).

**Rationale:**
- Equal weights are the natural interior starting point within all weight bounds.
- Initializing from user weights creates a local minimum bias near the current allocation,
  defeating the purpose of showing the optimizer's independent recommendation.
- Random restarts add complexity and computation time without meaningful benefit for
  typical N < 30 portfolios.

**Consequences:**
- The optimizer always finds the true globally optimal solution (within SLSQP guarantees).
- Results are reproducible (not random).
- User's current weights are shown separately as a dot/marker, not as the optimizer input.

---

## D-06: Risk-Free Rate from ^IRX

**Date:** 2026-03-13
**Status:** LOCKED

**Context:** Every risk-adjusted ratio (Sharpe, Sortino, Treynor, Information ratio,
Jensen's alpha, CML) requires a risk-free rate.

**Options considered:**
1. ^IRX (13-week T-bill, CBOE) — fetched via yfinance
2. Hardcoded constant (e.g. 0.05)
3. Fed Funds rate from FRED API

**Decision:** ^IRX fetched once on portfolio load, held constant for the session.

**Rationale:**
- Current market risk-free rate is more accurate than a hardcoded constant.
- ^IRX is available via yfinance (no additional API key needed).
- Held constant for the session — consistent across all metrics.
- Simpler than FRED API (no key required, no additional dependency).

**Consequences:**
- ^IRX returns annualized percentage — must divide by 100 then by 252 for daily decimal rate.
- If ^IRX fetch fails, must have a reasonable fallback (e.g. last valid value or 0.05 constant).
- ^IRX may return NaN rows — use last valid value.

---

## D-07: GARCH-MC for Monte Carlo (Not Plain GBM)

**Date:** 2026-03-13
**Status:** LOCKED

**Context:** Monte Carlo simulation requires a volatility model for path generation.

**Options considered:**
1. Plain GBM with constant historical volatility
2. GARCH-MC: GBM with time-varying GARCH-driven volatility
3. Historical bootstrap

**Decision:** GARCH-MC — GBM with GARCH(1,1) updating volatility at each step.

**Rationale:**
- Plain GBM assumes constant volatility — inconsistent with GARCH model fitted elsewhere.
- GARCH-MC produces more realistic paths with volatility clustering.
- Initializing from GARCH one-step-ahead forecast provides a current-conditions starting point.
- Historical bootstrap would require much larger arrays and does not extend naturally to
  longer horizons.

**Consequences:**
- Monte Carlo must be fully vectorized (pre-generate (steps, paths) innovation matrix).
- Python loops over paths are forbidden — orders of magnitude too slow for 1,000+ paths.
- Running GARCH variance maintained per-path, updated at each step.
- If GARCH fallback (EWMA) is active, Monte Carlo uses constant EWMA volatility.

---

## D-08: Market Signals Fresh Fetch (Not Cached)

**Date:** 2026-03-13
**Status:** LOCKED

**Context:** The Risk Preparedness Panel shows 11 live signals. Caching behavior matters
for data freshness and load time.

**Options considered:**
1. Cache signals with same 1-hour TTL as price data
2. Fetch signals fresh on every session load (no cache)
3. Cache signals with shorter TTL (e.g. 15 minutes)

**Decision:** Fetch signals fresh on each session load. No cache TTL applied.

**Rationale:**
- Signals are explicitly described as "live" and "current-conditions" in the spec.
- Signal interpretation (VIX above 20 = elevated stress) depends on the current value, not a cached value.
- Sessions are typically user-initiated events (not background refreshes), so fresh fetch is appropriate.
- Separating signal cache from price data cache prevents stale signals appearing on a fresh session.

**Consequences:**
- market_signals.py fetch functions must NOT use @st.cache_data.
- price data fetch in data_fetcher.py DOES use @st.cache_data with 1-hour TTL.
- Signal fetch failures must be handled gracefully without crashing the session.

---

## D-09: Four-Item Nav Bar, More Details from Quadrant Buttons Only

**Date:** 2026-03-13
**Status:** LOCKED

**Context:** Navigation architecture determines cognitive complexity and information hierarchy.

**Options considered:**
1. Six-item nav bar with Q1–Q4 More Details accessible from nav
2. Four-item nav bar; More Details via sidebar or sub-tabs
3. Four-item nav bar; More Details exclusively via quadrant buttons on dashboard

**Decision:** Four-item nav bar (INPUT, DASHBOARD, GUIDE, SETTINGS). More Details accessed only via quadrant buttons.

**Rationale:**
- Keeps navigation simple for Maya (primary casual user persona).
- The dashboard is the application's home base — drilling down from it is the natural UX flow.
- A six-item nav bar exposes analytical depth before the user has seen the summary, reversing the progressive disclosure principle.
- "Deep Dive" never appearing in nav bar prevents confusion with "More Details" terminology.

**Consequences:**
- More Details pages are not directly accessible via URL or nav bar.
- Back to Dashboard button must be the first element on every More Details page.
- The nav bar remains visible on More Details pages for Guide and Settings access.

---

## D-10: Yield Curve Ticker Discrepancy

**Date:** 2026-03-13
**Status:** OPEN — revisit in v2

**Context:** The spec states: "Yield curve: 10-year minus 2-year Treasury spread. Fetched as ^TNX minus ^TYX."
However, ^TNX is the 10-year Treasury yield and ^TYX is the 30-year Treasury yield — not the 2-year.
The 2-year Treasury yield does not have a reliable standard yfinance ticker.

**Options considered:**
1. Implement per spec: ^TNX - ^TYX (10yr - 30yr). Inversion logic inverted from standard meaning.
2. Use ^TNX - ^IRX (10yr - 3mo T-bill) as a proxy for the slope.
3. Use ^FVX (5-year) as a middle ground.
4. Fetch 2yr yield from FRED API (requires API key).

**Decision:** Implement per spec using ^TNX - ^TYX, with a comment in code noting the discrepancy.
Display label in UI: "Yield Curve (10yr - 30yr spread)" to be transparent.

**Rationale:**
- Implementing per spec maintains consistency with the project document.
- The note in code and UI label prevents misleading the user.
- Revisiting in v2 with FRED integration for true 2yr yield is the clean long-term solution.

**Consequences:**
- The spread will typically be negative (10yr < 30yr) — this is normal term premium direction.
- Inversion signals are calibrated to this spread, not the classic 10yr-2yr recession indicator.
- Documented here so the discrepancy is not forgotten.
