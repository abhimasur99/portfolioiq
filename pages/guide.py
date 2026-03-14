"""pages/guide.py

Screen 4 — Guide.

Responsibilities:
- Introductory paragraph: conditional characterization framing (not prediction).
- Five sections with four-column tables:
    Section 1: Performance (Descriptive) — CAGR, Sharpe, Sortino, etc.
    Section 2: Risk Factors (Diagnostic) — correlation, drawdown, HHI, etc.
    Section 3: Risk Outlook (Predictive) — VaR, CVaR, GARCH, Monte Carlo.
    Section 4: Optimization (Prescriptive) — frontier, max Sharpe, estimation error.
    Section 5: Leading Indicators & Preparedness Signals — all 11 signals.
- Closing statement on signal limitations.
- Version date displayed.
- Four columns per row: Metric, Formula/Method, What it tells you, Key assumption/limitation.

Implemented in: Session 14.
"""

import pandas as pd
import streamlit as st

GUIDE_VERSION = "v1.0 — 2026-03"


# ── Section data ────────────────────────────────────────────────────────────────

_PERF_ROWS = [
    (
        "CAGR",
        "exp(sum(log returns) / years) − 1",
        "The smoothed annual growth rate if the portfolio grew at a constant rate. "
        "Accounts for compounding; comparable across portfolios of different lengths.",
        "Backwards-looking only. A high CAGR over a short or lucky period does not imply "
        "future outperformance. Sensitive to start/end date selection.",
    ),
    (
        "Annualised Volatility",
        "std(daily log returns) × √252",
        "Total price fluctuation per year. Higher volatility means wider swings in either "
        "direction. Does not distinguish between upside and downside moves.",
        "Assumes i.i.d. daily returns for the √252 scaling. True annual vol may differ "
        "if return autocorrelation is present (e.g. illiquid assets).",
    ),
    (
        "Sharpe Ratio",
        "(mean daily return − Rf_daily) / std(daily) × √252",
        "Excess return earned per unit of total risk. Above 1.0 is commonly considered "
        "strong; below 0 means the portfolio underperformed the risk-free rate on a "
        "risk-adjusted basis.",
        "Penalises upside and downside volatility equally. Misleading for assets with "
        "strong skew or fat tails. Depends on the choice of risk-free rate.",
    ),
    (
        "Sortino Ratio",
        "(mean daily return − Rf_daily) / semi-std(daily) × √252",
        "Like Sharpe, but the denominator uses only downside deviations below zero. "
        "A higher Sortino than Sharpe indicates losses were less severe than overall "
        "volatility suggests.",
        "Semi-deviation is less stable than standard deviation (computed on a smaller "
        "subset of returns). Less commonly reported, so peer comparison is harder.",
    ),
    (
        "Treynor Ratio",
        "(mean return − Rf) / Beta",
        "Excess return per unit of systematic (market) risk. Appropriate for comparing "
        "portfolios that will be combined into a broader diversified account.",
        "Meaningless for portfolios with near-zero or negative beta. Assumes CAPM — "
        "a single market factor explains all systematic risk.",
    ),
    (
        "Information Ratio",
        "mean(active return) / std(active return) × √252",
        "Active return (portfolio minus benchmark) per unit of tracking error. "
        "Above 0.5 is considered evidence of consistent active management skill.",
        "Requires a sensible benchmark. A high IR against an irrelevant benchmark is "
        "meaningless. Short track records inflate IR due to noise.",
    ),
    (
        "Jensen's Alpha",
        "mean portfolio return − [Rf + Beta × (mean benchmark − Rf)]",
        "Excess return not explained by market exposure (beta). Positive alpha "
        "indicates true outperformance beyond what market timing alone would deliver.",
        "Assumes the single-factor CAPM fully describes expected returns. Alpha "
        "shrinks when controlling for additional risk factors (size, value, momentum).",
    ),
    (
        "Beta",
        "cov(portfolio, benchmark) / var(benchmark)",
        "Sensitivity to benchmark moves. Beta = 1.2 means the portfolio tends to rise "
        "1.2× when the benchmark rises and fall 1.2× when it falls.",
        "Beta is estimated from historical data and may shift over time (beta drift). "
        "Assumes linear relationship between portfolio and benchmark returns.",
    ),
    (
        "R-Squared",
        "corr(portfolio, benchmark)²",
        "Proportion of portfolio variance explained by the benchmark. R² = 0.95 means "
        "95% of return variation is driven by market moves. Low R² = idiosyncratic.",
        "High R² does not imply good performance — it means the portfolio tracks the "
        "index. R² can be high even when alpha is negative.",
    ),
    (
        "Rolling Sharpe / Rolling Beta",
        "Computed over trailing 252-day (1-year) window",
        "Shows whether risk-adjusted return and market sensitivity have been stable "
        "or have drifted over time. Periods below zero on rolling Sharpe indicate "
        "underperformance of cash on a rolling basis.",
        "252-day window is short enough to detect regime changes but long enough to "
        "reduce noise. Edge effects near the start of the series are normal.",
    ),
    (
        "Best / Worst Month & Year",
        "Resample daily log returns to monthly / yearly; exp(sum) − 1",
        "Range of calendar-period outcomes. Shows the best-case and worst-case "
        "experiences a buy-and-hold investor would have faced.",
        "Calendar boundaries are arbitrary. The best year may immediately precede "
        "the worst. Not a guide to future outcomes.",
    ),
]

_RISK_FACTORS_ROWS = [
    (
        "Correlation Matrix",
        "Pearson corr(log returns_i, log returns_j) over full period",
        "Pairwise relationship between holdings. Values near +1 mean assets move "
        "together (less diversification); near −1 means they offset each other.",
        "Pearson correlation is linear — it misses tail dependence (assets that are "
        "uncorrelated on average but crash together). Correlations estimated from a "
        "calm period overstate true diversification.",
    ),
    (
        "Rolling 60-Day Correlation",
        "Trailing 60-trading-day Pearson correlation per pair",
        "Shows how correlations shift over time. During market stress, correlations "
        "typically spike toward 1.0 — diversification collapses when you need it most.",
        "60 days is short, so estimates are noisy. Interpret trends, not individual "
        "data points. Leading edge of series has fewer observations.",
    ),
    (
        "HHI (Herfindahl-Hirschman Index)",
        "sum(w_i²) for all holdings",
        "Weight concentration index. Ranges from 1/N (perfectly equal weight) to 1.0 "
        "(single holding). Lower HHI means more evenly spread capital.",
        "HHI only captures weight concentration, not correlation concentration. Two "
        "equal-weight holdings that move in lockstep have low HHI but high real concentration.",
    ),
    (
        "Effective N",
        "1 / HHI",
        "The number of equally-weighted, uncorrelated positions that would give the "
        "same level of diversification. Effective N < actual N when holdings are correlated.",
        "Computed only from weights (same as HHI). Does not account for cross-asset "
        "correlations directly — use alongside the correlation matrix.",
    ),
    (
        "Diversification Ratio",
        "sum(w_i × σ_i) / σ_portfolio",
        "Ratio of weighted-average individual volatilities to portfolio volatility. "
        "Values above 1.0 confirm that combining assets reduces total risk. Higher is better.",
        "Computed from historical covariance. If all assets become correlated in a stress "
        "event, the ratio collapses toward 1.0 regardless of its historical value.",
    ),
    (
        "Max Drawdown",
        "min(portfolio_value / running_max − 1)",
        "The largest peak-to-trough loss an investor would have experienced holding "
        "through the full period. Represents the worst realised loss before recovery.",
        "Highly sensitive to the period selected. A 3-year window may miss a severe "
        "drawdown that occurred 4 years ago. Does not indicate when the next drawdown will occur.",
    ),
    (
        "Calmar Ratio",
        "CAGR / |Max Drawdown|",
        "Return earned per unit of maximum drawdown absorbed. Higher is better. "
        "A portfolio with 10% CAGR and 20% max drawdown has Calmar = 0.5.",
        "Both numerator and denominator are backwards-looking. A single large drawdown "
        "can permanently reduce Calmar even if subsequent performance recovers.",
    ),
    (
        "Recovery Days",
        "Trading days from the trough of the deepest drawdown back to the prior peak",
        "How long it took to recover from the worst loss. Short recovery = resilient; "
        "long recovery = prolonged period of being underwater.",
        "Only measures recovery from the single deepest drawdown. The portfolio may "
        "have had other significant drawdowns with different recovery profiles. "
        "None = still in drawdown at the end of the period.",
    ),
    (
        "Ulcer Index",
        "sqrt(mean(drawdown_values²))",
        "Root mean square of all drawdown values over the period. Penalises both the "
        "depth and the duration of underwater periods. Lower is better.",
        "Less commonly reported than max drawdown; no universal benchmark for 'good' "
        "vs 'bad' values. Useful for comparing two portfolios against each other.",
    ),
]

_RISK_OUTLOOK_ROWS = [
    (
        "Historical Volatility (ann.)",
        "std(daily log returns) × √252 over full period",
        "Constant-weight estimate of return dispersion. The baseline volatility "
        "measure against which GARCH and EWMA estimates are compared.",
        "Treats all historical observations equally. Does not respond to recent "
        "volatility spikes. A calm 2-year period can mask elevated near-term risk.",
    ),
    (
        "EWMA Volatility",
        "σ²_t = λ × σ²_{t-1} + (1−λ) × r²_{t-1}, λ = 0.94 (RiskMetrics)",
        "Exponentially weighted moving average of variance. Gives more weight to "
        "recent returns. Responds faster to volatility spikes than historical vol.",
        "No mean-reversion: EWMA vol can drift upward or downward indefinitely without "
        "a pull-back force. Choice of λ = 0.94 is convention, not universal.",
    ),
    (
        "GARCH(1,1) Volatility",
        "σ²_t = ω + α × r²_{t-1} + β × σ²_{t-1}; fit by MLE on % log returns",
        "Conditional variance model with mean-reversion built in. α captures shock "
        "responsiveness; β captures volatility persistence. α+β < 1 ensures stationarity. "
        "Falls back to EWMA if α+β ≥ 1 or fewer than 252 observations.",
        "GARCH assumes return innovations are conditionally normal — fat tails are "
        "partially captured by time-varying σ² but not fully. Model parameters estimated "
        "from full historical period; may not reflect current regime.",
    ),
    (
        "VaR (Historical, 95% / 99%)",
        "5th / 1st percentile of the empirical daily log return distribution",
        "Threshold: on the worst 5% (or 1%) of days historically, the portfolio lost "
        "at least this much. VaR is a loss threshold, not an average loss.",
        "Non-parametric — directly from observed returns. Assumes the future return "
        "distribution resembles the past. Extreme events that did not occur in the "
        "sample period are invisible to historical VaR.",
    ),
    (
        "CVaR / Expected Shortfall (95% / 99%)",
        "mean(returns | return < VaR threshold)",
        "Average loss on the worst 5% (or 1%) of days. Always worse than VaR. "
        "Measures the severity of tail losses beyond the VaR threshold.",
        "Requires enough observations in the tail for a stable estimate. With fewer "
        "than 500 observations, 99th percentile CVaR has very high estimation error.",
    ),
    (
        "GARCH VaR (95%)",
        "−GARCH_vol_daily × Φ⁻¹(0.95), Φ = standard normal CDF",
        "Forward-looking VaR using today's GARCH-implied conditional volatility and "
        "a normal quantile multiplier. Responds faster to recent market conditions.",
        "Assumes normally distributed innovations — underestimates VaR when returns "
        "are fat-tailed (excess kurtosis). Acts as a complement to historical VaR, "
        "not a replacement.",
    ),
    (
        "Monthly VaR (95%)",
        "Daily VaR 95% × √21",
        "Approximate one-month loss threshold. Converts daily VaR to a monthly horizon "
        "using the square-root-of-time rule.",
        "√T scaling assumes i.i.d. returns. Volatility clustering (captured by GARCH "
        "at the daily level) is not preserved under this approximation. "
        "Use as a directional order-of-magnitude estimate only.",
    ),
    (
        "Skewness",
        "E[(r − μ)³] / σ³",
        "Asymmetry of the return distribution. Negative skew means the distribution "
        "has a longer left tail — large losses occur more frequently than large gains.",
        "Sample skewness is noisy, especially for short histories. A small number of "
        "extreme events can produce large skewness estimates that do not persist.",
    ),
    (
        "Excess Kurtosis",
        "E[(r − μ)⁴] / σ⁴ − 3",
        "Tail thickness relative to a normal distribution. Excess kurtosis > 0 (leptokurtic) "
        "means extreme returns occur more often than the normal distribution predicts. "
        "Most financial return series exhibit positive excess kurtosis.",
        "Like skewness, sensitive to outliers. Does not indicate the direction of extreme "
        "events — only their relative frequency. Does not update in real time.",
    ),
    (
        "Monte Carlo Fan (GARCH-MC)",
        "N=1,000 paths, GARCH(1,1) dynamics, horizon = user-selected years; "
        "10th / 50th / 90th percentiles displayed",
        "Distribution of plausible future portfolio values. The spread of the fan "
        "represents uncertainty. The 50th percentile path is the median scenario.",
        "Paths are simulated from GARCH-implied dynamics starting from current "
        "conditions. Normal innovations assumed — fat tails underrepresented. "
        "Not a forecast. The median path is not the most likely single outcome.",
    ),
    (
        "Stress Tests",
        "Portfolio return = α + β × scenario index return, for 4 historical scenarios",
        "Applies your portfolio's estimated alpha and beta to historical crisis index "
        "returns. Shows what your specific allocation would have experienced (not the index).",
        "Assumes alpha and beta estimated from the full period are stable during stress — "
        "they typically are not. Beta rises and alpha falls during market crises. "
        "Use as a lower-bound plausibility check, not a precise prediction.",
    ),
]

_OPTIMIZATION_ROWS = [
    (
        "Efficient Frontier",
        "Set of 50 portfolios minimising variance for target return levels from "
        "min-var return to feasible maximum, using SLSQP with weight bounds",
        "The curve of portfolios offering the highest return for each level of risk. "
        "Any portfolio below the frontier is inefficient — more return is achievable "
        "at the same risk by moving up to the frontier.",
        "Expected returns are estimated from historical means — the dominant source of "
        "estimation error. Small changes in return estimates shift the frontier dramatically. "
        "The frontier is computed under the selected period and weight constraints.",
    ),
    (
        "Max Sharpe Portfolio (Tangency)",
        "Minimise −(w⊤μ − Rf) / √(w⊤Σw) subject to sum=1, bounds",
        "The frontier portfolio with the highest Sharpe ratio. Geometrically, it is "
        "the point where the Capital Market Line (from Rf) is tangent to the frontier.",
        "Highly sensitive to expected return (μ) inputs. Small changes in μ can move "
        "the tangency point dramatically. Outputs should be treated as illustrative, "
        "not prescriptive.",
    ),
    (
        "Min Variance Portfolio",
        "Minimise w⊤Σw subject to sum=1, bounds",
        "The portfolio with the lowest achievable volatility under the weight constraints. "
        "Does not use expected returns — only the covariance matrix. More robust to "
        "estimation error than Max Sharpe.",
        "Covariance estimates are also noisy, especially for short histories or large N. "
        "The min variance portfolio tends to be highly concentrated in low-vol assets.",
    ),
    (
        "Risk Parity",
        "Minimise Σᵢ (wᵢ × (Σw)ᵢ − σ²_p / N)² subject to sum=1, bounds",
        "Equal Risk Contribution: each holding contributes the same amount to total "
        "portfolio variance. Typically overweights lower-volatility assets relative "
        "to their market-cap weight.",
        "Does not optimise for returns — only risk distribution. In a rising market, "
        "risk parity portfolios may underperform cap-weighted or max-Sharpe portfolios. "
        "Sensitive to covariance estimation errors for small N.",
    ),
    (
        "Capital Market Line (CML)",
        "From Rf through the Max Sharpe (tangency) portfolio",
        "All combinations of the risk-free asset and the tangency portfolio. Any "
        "point on the CML dominates portfolios below it at the same risk level. "
        "The slope of the CML equals the Max Sharpe ratio.",
        "The CML is theoretical — it assumes investors can borrow and lend at Rf, "
        "which is not realistic. In practice, borrowing costs are higher than Rf.",
    ),
    (
        "Estimation Error Warning",
        "N/A — a disclosure, not a calculation",
        "Mean-variance optimization amplifies errors in expected return inputs. "
        "Historical mean returns are poor predictors of future returns, especially "
        "for short histories. Optimizer outputs are model results, not recommendations.",
        "This is the most important limitation on this screen. The efficient frontier "
        "and optimal weights should be interpreted as illustrating the structure of the "
        "opportunity set — not as a rebalancing prescription.",
    ),
    (
        "Weight Delta Table",
        "Δᵢ = w_optimizer_i − w_current_i for each ticker",
        "Shows how much each optimizer would increase (+) or decrease (−) each position "
        "relative to the current allocation. Useful for understanding the direction "
        "and magnitude of implied rebalancing.",
        "Deltas are computed from model-optimal weights that assume the historical "
        "covariance and return structure persists. Transaction costs, taxes, and "
        "turnover are not considered.",
    ),
]

_SIGNALS_ROWS = [
    (
        "VIX Level",
        "CBOE VIX index (^VIX) current value, fetched via yfinance",
        "Equity market implied volatility — the market's expectation of S&P 500 "
        "volatility over the next 30 days. Above 20 = elevated concern; above 30 = "
        "crisis-level fear.",
        "VIX measures implied vol of S&P 500 options — not your portfolio's volatility. "
        "A high VIX raises correlations and may signal adverse conditions but does "
        "not predict direction.",
    ),
    (
        "VIX Trend",
        "Linear slope of VIX over trailing 10 trading days",
        "Whether market fear is rising or falling. Rising VIX (positive slope) "
        "indicates increasing concern; falling VIX signals improving sentiment.",
        "Short window (10 days) produces noisy signals. A single spike followed by "
        "reversion can flip the trend signal. Use alongside VIX Level, not in isolation.",
    ),
    (
        "VIX Term Structure",
        "^VIX (30-day) minus ^VIX3M (3-month) implied volatility spread",
        "Spot vs forward implied vol. Normally positive (contango). An inverted "
        "term structure (spot > 3-month) signals acute near-term fear — markets "
        "expect stress to resolve quickly.",
        "Inversion alone does not predict the severity or duration of market stress. "
        "Has historically been a coincident indicator, not a leading indicator.",
    ),
    (
        "MOVE Index",
        "ICE BofA MOVE Index (^MOVE) — bond market implied volatility",
        "The bond market's 'VIX'. High MOVE = high rate uncertainty. Elevated MOVE "
        "can spill into equity volatility through credit and duration channels.",
        "MOVE reflects Treasury option vol, not credit spreads. A rising MOVE driven "
        "by economic growth expectations differs from one driven by default fears.",
    ),
    (
        "Yield Curve",
        "^TNX (10-year) minus ^TYX (30-year) Treasury yield spread",
        "Measures the slope of the long end of the yield curve. An inverted "
        "spread (10yr < 30yr is normal; deeply negative = unusual long-end inversion) "
        "can signal rate expectations or growth concerns.",
        "Note: this uses 10yr−30yr, not the classic 10yr−2yr recession indicator "
        "(the 2-year Treasury lacks a reliable standard yfinance ticker). Interpret "
        "with awareness of this approximation. See DECISIONS.md D-10.",
    ),
    (
        "Credit Spreads",
        "HYG (high-yield ETF) / IEF (7-10yr Treasury ETF) price ratio as a proxy",
        "Measures high-yield credit risk appetite relative to investment-grade rates. "
        "Falling ratio = widening credit spreads = corporate stress or risk-off shift.",
        "Price-ratio proxy is an approximation. True credit spreads require OAS "
        "(option-adjusted spread) data from a Bloomberg or FRED feed. This signal "
        "provides directional awareness, not precision.",
    ),
    (
        "Copper / Gold Ratio",
        "Current price of copper futures (HG=F) divided by gold (GC=F)",
        "Copper is industrial (cyclical demand); gold is a safe haven. Rising ratio "
        "= risk-on / growth optimism. Falling ratio = risk-off / growth concern.",
        "Both commodity prices are affected by supply factors unrelated to global "
        "growth sentiment. The ratio can move on supply shocks even when macro "
        "conditions are stable.",
    ),
    (
        "Dollar Index",
        "DXY index (DX-Y.NYB) current value vs 3-month average",
        "A strong dollar is typically a headwind for international equities "
        "(reduces USD value of foreign returns) and for commodity prices. "
        "Rising dollar = tightening global financial conditions.",
        "Dollar strength reflects many factors: Fed policy, growth differentials, "
        "safe-haven demand. A strong dollar from strong US growth is different from "
        "a strong dollar from global risk aversion.",
    ),
    (
        "Oil Sensitivity",
        "Rolling 60-day Pearson correlation of portfolio vs USO (oil ETF) returns",
        "How much your portfolio has moved with oil prices recently. High positive "
        "correlation = energy-exposed; negative = potential hedge.",
        "60-day rolling window is short — signal is noisy and reflects recent market "
        "moves, which may not persist. Correlation ≠ causation.",
    ),
    (
        "Rate Sensitivity",
        "Rolling 60-day Pearson correlation of portfolio vs TLT (20yr Treasury ETF)",
        "How much your portfolio has moved with long-duration bonds. Positive "
        "correlation = rate-sensitive (rising rates hurt); negative = natural hedge.",
        "TLT prices move inversely to long-term yields. Correlation is computed over "
        "60 days and reflects recent conditions. Duration sensitivity can shift as "
        "portfolio composition changes.",
    ),
    (
        "Tech Concentration",
        "Currently unavailable — requires sector breakdown from an external data source",
        "Would measure the proportion of portfolio in technology-related sectors, "
        "flagging concentration risk in rate-sensitive growth names.",
        "Sector classifications require a reliable external feed (e.g. GICS from "
        "a data provider). yfinance sector data is incomplete and inconsistent across "
        "tickers. Planned for v2.",
    ),
]


# ── Page render ─────────────────────────────────────────────────────────────────

def _render_table(rows: list) -> None:
    """Render a four-column methodology table."""
    df = pd.DataFrame(
        rows,
        columns=["Metric", "Formula / Method", "What it tells you",
                 "Key assumption / limitation"],
    )
    st.dataframe(df, hide_index=True, use_container_width=True)


def render() -> None:
    """Render the Guide screen."""
    st.title("Methodology Guide")
    st.caption(GUIDE_VERSION)

    # ── Introduction ───────────────────────────────────────────────────────────
    st.markdown(
        "PortfolioIQ analyses your portfolio across four analytical layers. "
        "Every number is a characterisation of historical data — not a prediction, "
        "recommendation, or guarantee of future performance. "
        "The application describes what *has happened* and, where indicated, "
        "what *might happen* under specific model assumptions. "
        "All outputs are conditional on the data, the model, and the time period selected.\n\n"
        "This guide explains every metric: how it is computed, what it is intended to "
        "reveal, and where it can mislead. Understanding the limitations is as important "
        "as understanding the numbers."
    )

    st.markdown("---")

    # ── Section 1: Performance ─────────────────────────────────────────────────
    with st.expander("1 — Performance (Descriptive)", expanded=True):
        st.markdown(
            "Descriptive analytics characterise what the portfolio *has done*. "
            "These metrics are computed from log returns (rt = ln(Pt / Pt-1)) over the "
            "selected historical period. All ratios use the current ^IRX 13-week T-bill "
            "rate as the risk-free rate."
        )
        _render_table(_PERF_ROWS)

    # ── Section 2: Risk Factors ────────────────────────────────────────────────
    with st.expander("2 — Risk Factors (Diagnostic)", expanded=False):
        st.markdown(
            "Diagnostic analytics explain *why* the portfolio behaved as it did — "
            "through concentration, correlation structure, and drawdown characteristics. "
            "Covariance and correlation estimates use the full historical period selected."
        )
        _render_table(_RISK_FACTORS_ROWS)

    # ── Section 3: Risk Outlook ────────────────────────────────────────────────
    with st.expander("3 — Risk Outlook (Predictive)", expanded=False):
        st.markdown(
            "Predictive analytics model *what could happen* under specific statistical "
            "assumptions. GARCH(1,1) is fitted on percentage log returns; outputs are "
            "converted back to decimal. Monte Carlo uses 1,000 paths with GARCH-driven "
            "dynamics. All predictive outputs carry model uncertainty in addition to "
            "parameter estimation uncertainty."
        )
        _render_table(_RISK_OUTLOOK_ROWS)

    # ── Section 4: Optimization ────────────────────────────────────────────────
    with st.expander("4 — Optimization (Prescriptive)", expanded=False):
        st.markdown(
            "**Estimation error warning:** Mean-variance optimization is highly sensitive "
            "to expected return inputs estimated from historical data. Small changes in "
            "return estimates can produce very different frontier shapes and optimal weights. "
            "These outputs identify historically optimal portfolios under model assumptions — "
            "they are not investment recommendations. All optimizers use scipy SLSQP with "
            "the weight bounds configured in Settings."
        )
        _render_table(_OPTIMIZATION_ROWS)

    # ── Section 5: Leading Indicators ─────────────────────────────────────────
    with st.expander("5 — Leading Indicators & Preparedness Signals", expanded=False):
        st.markdown(
            "The Risk Preparedness Panel shows 11 forward-looking signals fetched fresh "
            "from yfinance each time a portfolio is loaded. These signals describe the "
            "current market *environment* — they are awareness tools, not buy/sell signals. "
            "Signal status thresholds (green / amber / red) are heuristic, not academically "
            "calibrated. A red signal does not mean 'sell'; it means the environment warrants "
            "heightened awareness."
        )
        _render_table(_SIGNALS_ROWS)

    st.markdown("---")

    # ── Closing statement ──────────────────────────────────────────────────────
    st.markdown(
        "#### A Note on Limitations\n\n"
        "Every quantitative metric in PortfolioIQ is computed from a finite historical "
        "sample. Financial markets are non-stationary: distributions, correlations, and "
        "volatility regimes change over time. A metric that characterised the portfolio "
        "accurately over the past 3 years may not characterise it accurately over the "
        "next 3 years.\n\n"
        "Specific limitations to keep in mind:\n"
        "- **Look-back period sensitivity:** all metrics are sensitive to the start and "
        "end dates selected on the Input screen. A 3-year window that includes 2022 will "
        "look very different from one that excludes it.\n"
        "- **Benchmark choice:** Sharpe, beta, alpha, Information Ratio, and R² all "
        "depend on the benchmark selected. An equity portfolio benchmarked to a bond "
        "index will show misleadingly high alpha.\n"
        "- **Correlation instability:** correlations that appear stable over a calm "
        "period spike during market stress — precisely when diversification is most needed.\n"
        "- **Optimizer sensitivity:** the efficient frontier and all optimizer outputs "
        "are highly sensitive to expected return inputs derived from the same historical "
        "period. The frontier is informative about the *structure* of the opportunity set, "
        "not the *direction* of rebalancing.\n\n"
        "_PortfolioIQ is an educational and analytical tool. It is not a regulated financial "
        "service and does not constitute investment advice. Always consult a qualified "
        "financial adviser before making investment decisions._"
    )

    st.caption(f"PortfolioIQ — {GUIDE_VERSION}")
