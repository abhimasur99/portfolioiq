"""screens/input.py

Screen 1 — Portfolio Input.

Responsibilities:
- Ticker entry with inline validation (before computation).
- Dollar amount input with automatic weight calculation and live recalculation.
- Benchmark selection from BENCHMARK_OPTIONS.
- Full disclaimer display.
- Loading screen with seven-step progress bar on submit.
- On successful load, sets SK_PORTFOLIO_LOADED = True and routes to dashboard.

Note: Time period is NOT selected here. The app always fetches 5 years of
price data. The analysis window (1Y/3Y/5Y/custom) is selected on the dashboard
via the time frame selector bar, allowing instant window switching.

7-step pipeline:
  1. Validate tickers (live yfinance check)
  2. Fetch 5y price data + risk-free rate (stores full history in SK_PRICE_DATA_FULL)
  3. Compute log returns + portfolio returns (on default 3Y window)
  4. Compute performance metrics (Layer 1)
  5. Compute risk factors (Layer 2)
  6. Compute risk outlook — GARCH, VaR, Monte Carlo (Layer 3)
  7. Compute optimization + fetch market signals (Layer 4)

Implemented in: Session 9.
"""

import pandas as pd
import streamlit as st

from assets.config import (
    BENCHMARK_OPTIONS,
    DEFAULT_BENCHMARK,
    DEFAULT_WEIGHT_MIN,
    DEFAULT_WEIGHT_MAX,
    DISCLAIMER_FULL,
    SK_ANALYSIS_END,
    SK_ANALYSIS_START,
    SK_ANALYTICS,
    SK_BENCH_RETURNS,
    SK_BENCHMARK,
    SK_MARKET_SIGNALS,
    SK_MC_HORIZON,
    SK_MC_PATHS,
    SK_OPTIMIZATION,
    SK_PERIOD,
    SK_PERFORMANCE,
    SK_PORTFOLIO_LOADED,
    SK_PORTFOLIO_NAME,
    SK_PORT_RETURNS,
    SK_PRICE_DATA,
    SK_PRICE_DATA_FULL,
    SK_RETURNS_DF,
    SK_RISK_FACTORS,
    SK_RISK_FREE_RATE,
    SK_RISK_OUTLOOK,
    SK_TICKERS,
    SK_VAR_CONFIDENCE,
    SK_TOTAL_VALUE,
    SK_WEIGHT_MAX,
    SK_WEIGHT_MIN,
    SK_WEIGHTS,
)

# Deferred analytics imports (inside _run_pipeline to avoid top-level import
# costs on every page load; modules are already bytecode-cached after first import)

_MAX_TICKERS = 10
_MIN_TICKERS = 2

# Session-local keys for the input form state.
# _KEY_PORTFOLIO_BASE is the fixed initial DataFrame — never overwritten after
# init. _KEY_TICKER_EDITOR is the data_editor widget key that Streamlit uses to
# accumulate row-level diffs (edited_rows / added_rows / deleted_rows). Keeping
# the base fixed and letting the key own the diffs avoids the double-apply bug
# that occurs when edited_df is written back as the new base on every rerun.
_KEY_PORTFOLIO_BASE = "_input_portfolio_base"
_KEY_TICKER_EDITOR  = "_ticker_editor"
_KEY_LAST_SUBMITTED = "_input_last_submitted"


# ── Form helpers ───────────────────────────────────────────────────────────────

def _init_input_state() -> None:
    """Initialise the fixed-base holdings DataFrame in session state.

    On first load: 4 empty rows.
    After a successful pipeline run: seed base from the last submitted DataFrame
    so navigating back to INPUT shows the previously entered portfolio.
    Clears any stale _KEY_TICKER_EDITOR diffs so they don't double-apply.
    """
    if _KEY_PORTFOLIO_BASE not in st.session_state:
        if _KEY_LAST_SUBMITTED in st.session_state:
            st.session_state[_KEY_PORTFOLIO_BASE] = st.session_state[_KEY_LAST_SUBMITTED].copy()
            st.session_state.pop(_KEY_TICKER_EDITOR, None)  # stale diffs would double-apply
        else:
            st.session_state[_KEY_PORTFOLIO_BASE] = pd.DataFrame({
                "Ticker":        ["", "", "", ""],
                "USD Amount ($)": [0.0, 0.0, 0.0, 0.0],
            })


def _parse_portfolio_df(df: pd.DataFrame) -> tuple:
    """Extract non-empty, non-zero rows from the editor DataFrame.

    Returns:
        (tickers, amounts) — parallel lists of str and float.
    """
    tickers, amounts = [], []
    for _, row in df.iterrows():
        ticker = str(row["Ticker"]).strip().upper()
        try:
            amount = float(row["USD Amount ($)"])
        except (ValueError, TypeError):
            amount = 0.0
        if ticker and amount > 0:
            tickers.append(ticker)
            amounts.append(amount)
    return tickers, amounts


def _compute_weights(tickers: list, amounts: list) -> pd.Series:
    """Dollar amounts → normalised weight Series."""
    total = sum(amounts)
    if total <= 0:
        return pd.Series(dtype=float)
    return pd.Series([a / total for a in amounts], index=tickers)


def _weight_bound_errors(
    weights: pd.Series,
    weight_min: float,
    weight_max: float,
) -> list:
    """Return list of human-readable bound violation strings (empty = all OK)."""
    errors = []
    for ticker, w in weights.items():
        if w < weight_min - 1e-6:
            errors.append(
                f"**{ticker}** weight {w*100:.1f}% is below minimum {weight_min*100:.0f}%."
            )
        if w > weight_max + 1e-6:
            errors.append(
                f"**{ticker}** weight {w*100:.1f}% exceeds maximum {weight_max*100:.0f}%."
            )
    return errors


# ── 7-step analytics pipeline ──────────────────────────────────────────────────

def _run_pipeline(
    tickers: list,
    benchmark: str,
    weights: pd.Series,
    portfolio_name: str,
) -> bool:
    """Execute all seven analytics pipeline steps with progress display.

    Fetches 5 years of price data (stored in SK_PRICE_DATA_FULL). Analytics
    are computed on the default 3-year window, which can be changed via the
    dashboard time frame selector without re-fetching.

    Stores all results in st.session_state on success and sets
    SK_PORTFOLIO_LOADED = True.

    Returns:
        True on full success, False if any step raised an exception or
        returned invalid data.
    """
    from analytics.data_fetcher import validate_tickers, fetch_price_data, fetch_risk_free_rate
    from analytics.returns import compute_log_returns, compute_portfolio_returns
    from analytics.performance import compute_all_performance
    from analytics.risk_factors import compute_all_risk_factors
    from analytics.risk_outlook import compute_all_risk_outlook
    from analytics.optimization import compute_all_optimization
    from analytics.market_signals import fetch_all_signals

    settings = {
        "var_confidence": st.session_state.get(SK_VAR_CONFIDENCE, 0.95),
        "mc_horizon":     st.session_state.get(SK_MC_HORIZON, 10),
        "mc_paths":       st.session_state.get(SK_MC_PATHS, 1_000),
    }
    weight_min = st.session_state.get(SK_WEIGHT_MIN, DEFAULT_WEIGHT_MIN)
    weight_max = st.session_state.get(SK_WEIGHT_MAX, DEFAULT_WEIGHT_MAX)

    all_tickers = tickers + ([benchmark] if benchmark not in tickers else [])

    progress_bar = st.progress(0)
    status_text  = st.empty()

    def _step(n: int, msg: str) -> None:
        progress_bar.progress(n / 7)
        status_text.markdown(f"**Step {n} / 7 —** {msg}")

    try:
        # ── Step 1: Validate tickers ──────────────────────────────────────────
        _step(1, "Validating tickers…")
        valid, invalid = validate_tickers(all_tickers)
        if invalid:
            progress_bar.empty()
            status_text.empty()
            st.error(
                f"Unrecognised tickers: **{', '.join(invalid)}**. "
                "Please correct and resubmit."
            )
            return False

        # ── Step 2: Fetch 5y price data + risk-free rate ──────────────────────
        _step(2, "Fetching 5-year price history from yfinance…")
        full_prices    = fetch_price_data(tuple(all_tickers))
        risk_free_rate = fetch_risk_free_rate()

        # Default analysis window: last 3 years (or max available if < 3y)
        end_date      = full_prices.index[-1]
        start_target  = end_date - pd.DateOffset(years=3)
        prices        = full_prices[full_prices.index >= start_target]
        if len(prices) < 60:  # fallback to full data if window is unexpectedly short
            prices = full_prices

        # ── Step 3: Log returns + portfolio / benchmark series ────────────────
        _step(3, "Computing log returns…")
        returns_df = compute_log_returns(prices)

        # Align weights to tickers that actually appear in the price data
        available = [t for t in tickers if t in returns_df.columns]
        if len(available) < _MIN_TICKERS:
            raise ValueError(
                f"Only {len(available)} tickers have price data. Need at least {_MIN_TICKERS}."
            )
        weights_aligned = weights.reindex(available).dropna()
        weights_aligned = weights_aligned / weights_aligned.sum()  # renormalize

        portfolio_returns = compute_portfolio_returns(
            returns_df[available], weights_aligned
        )
        benchmark_returns = (
            returns_df[benchmark]
            if benchmark in returns_df.columns
            else portfolio_returns.copy()
        )

        # ── Step 4: Performance (Layer 1) ─────────────────────────────────────
        _step(4, "Computing performance metrics…")
        performance = compute_all_performance(
            portfolio_returns, benchmark_returns, risk_free_rate
        )

        # ── Step 5: Risk factors (Layer 2) ────────────────────────────────────
        _step(5, "Computing risk factors…")
        risk_factors = compute_all_risk_factors(
            returns_df[available], weights_aligned, portfolio_returns
        )

        # ── Step 6: Risk outlook (Layer 3) ────────────────────────────────────
        _step(6, "Computing risk outlook (GARCH · VaR · Monte Carlo)…")
        risk_outlook = compute_all_risk_outlook(
            portfolio_returns, benchmark_returns,
            weights_aligned, performance, settings
        )

        # ── Step 7: Optimization + market signals (Layer 4) ───────────────────
        _step(7, "Running optimizer and fetching market signals…")
        optimization = compute_all_optimization(
            returns_df[available], weights_aligned,
            risk_free_rate, weight_min, weight_max
        )
        market_signals = fetch_all_signals(portfolio_returns)

        # ── Persist all results in session state ──────────────────────────────
        st.session_state[SK_TICKERS]         = available
        st.session_state[SK_WEIGHTS]         = weights_aligned
        st.session_state[SK_BENCHMARK]       = benchmark
        st.session_state[SK_PERIOD]          = "3Y"   # initial window label
        st.session_state[SK_ANALYSIS_START]  = str(prices.index[0].date())
        st.session_state[SK_ANALYSIS_END]    = str(prices.index[-1].date())
        st.session_state[SK_PORTFOLIO_NAME]  = portfolio_name
        st.session_state[SK_PRICE_DATA_FULL] = full_prices   # full 5y, for window switching
        st.session_state[SK_PRICE_DATA]      = prices        # active window prices
        st.session_state[SK_RETURNS_DF]      = returns_df
        st.session_state[SK_PORT_RETURNS]    = portfolio_returns
        st.session_state[SK_BENCH_RETURNS]   = benchmark_returns
        st.session_state[SK_RISK_FREE_RATE]  = risk_free_rate
        st.session_state[SK_ANALYTICS] = {
            SK_PERFORMANCE:    performance,
            SK_RISK_FACTORS:   risk_factors,
            SK_RISK_OUTLOOK:   risk_outlook,
            SK_OPTIMIZATION:   optimization,
            SK_MARKET_SIGNALS: market_signals,
        }
        st.session_state[SK_PORTFOLIO_LOADED] = True

        progress_bar.progress(1.0)
        status_text.markdown("✓ **Analysis complete.** Redirecting to dashboard…")
        return True

    except Exception as exc:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Analysis failed: {exc}")
        return False


# ── Page render ────────────────────────────────────────────────────────────────

def render() -> None:
    """Render the Portfolio Input screen."""
    _init_input_state()

    st.title("Portfolio Input")
    st.caption(
        "Enter your holdings below. Dollar amounts are automatically converted "
        "to portfolio weights."
    )

    # ── Demo portfolio shortcut ────────────────────────────────────────────────
    if st.button("⚡ Try Demo Portfolio", type="secondary", help="Pre-fills a diversified 5-stock US large-cap portfolio so you can explore the app immediately."):
        st.session_state[_KEY_PORTFOLIO_BASE] = pd.DataFrame({
            "Ticker":         ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
            "USD Amount ($)": [30000.0, 25000.0, 20000.0, 15000.0, 10000.0],
        })
        st.session_state.pop(_KEY_TICKER_EDITOR, None)
        st.rerun()

    col_form, col_preview = st.columns([3, 2], gap="large")

    # ── Left column: form ──────────────────────────────────────────────────────
    # All inputs are wrapped in st.form so that widget interactions (selectbox,
    # checkbox) do not trigger reruns mid-entry. Data is committed atomically
    # when the submit button is clicked.
    with col_form:
        with st.form("portfolio_form"):
            portfolio_name = st.text_input(
                "Portfolio name (optional)",
                value=st.session_state.get(SK_PORTFOLIO_NAME, ""),
                placeholder="e.g. Tech Growth Portfolio",
            )

            st.markdown("##### Holdings")
            st.caption(
                f"Enter {_MIN_TICKERS}–{_MAX_TICKERS} tickers with USD dollar amounts. "
                "Use the **+** icon to add rows."
            )

            edited_df = st.data_editor(
                st.session_state[_KEY_PORTFOLIO_BASE],
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "Ticker": st.column_config.TextColumn(
                        "Ticker",
                        help="Stock ticker symbol (e.g. AAPL, MSFT)",
                        max_chars=10,
                    ),
                    "USD Amount ($)": st.column_config.NumberColumn(
                        "USD Amount ($)",
                        help="Current market value of this position in USD",
                        min_value=0.0,
                        format="$%g",
                    ),
                },
                hide_index=True,
                key=_KEY_TICKER_EDITOR,
            )

            bench_keys   = list(BENCHMARK_OPTIONS.keys())
            bench_vals   = list(BENCHMARK_OPTIONS.values())
            stored_bench = st.session_state.get(SK_BENCHMARK, DEFAULT_BENCHMARK)
            bench_idx    = bench_vals.index(stored_bench) if stored_bench in bench_vals else 0
            benchmark_label = st.selectbox(
                "Benchmark",
                options=bench_keys,
                index=bench_idx,
                help="Used for alpha, beta, Sharpe, and Information Ratio calculations. "
                     "Analysis window (1Y/3Y/5Y/Custom) is set on the Dashboard.",
            )
            benchmark = BENCHMARK_OPTIONS[benchmark_label]

            with st.expander("Full disclaimer"):
                st.markdown(DISCLAIMER_FULL)

            agree = st.checkbox("I understand this analysis is not financial advice.")

            submit_clicked = st.form_submit_button(
                "Analyse Portfolio →",
                type="primary",
                use_container_width=True,
            )

    # ── Right column: weight preview (reflects last submitted state) ───────────
    with col_preview:
        tickers, amounts = _parse_portfolio_df(edited_df)
        weight_min = st.session_state.get(SK_WEIGHT_MIN, DEFAULT_WEIGHT_MIN)
        weight_max = st.session_state.get(SK_WEIGHT_MAX, DEFAULT_WEIGHT_MAX)

        st.markdown("##### Weight Preview")

        if len(tickers) < _MIN_TICKERS:
            st.info(f"Enter at least {_MIN_TICKERS} tickers with non-zero amounts, then click Analyse to see preview.")
        elif len(tickers) > _MAX_TICKERS:
            st.warning(
                f"Maximum {_MAX_TICKERS} tickers allowed. "
                f"Remove {len(tickers) - _MAX_TICKERS} row(s) to continue."
            )
        else:
            weights = _compute_weights(tickers, amounts)
            total_usd = sum(amounts)

            preview_rows = []
            for ticker, amount, weight in zip(tickers, amounts, weights.values):
                in_bounds = weight_min - 1e-6 <= weight <= weight_max + 1e-6
                preview_rows.append({
                    "Ticker": ticker,
                    "Amount": f"${amount:,.0f}",
                    "Weight": f"{weight * 100:.1f}%",
                    "OK": "✓" if in_bounds else "⚠",
                })

            st.dataframe(
                pd.DataFrame(preview_rows),
                hide_index=True,
                use_container_width=True,
            )
            st.caption(
                f"Total: **${total_usd:,.0f}**  ·  "
                f"Bounds: {weight_min*100:.0f}%–{weight_max*100:.0f}% "
                f"(change in Settings)"
            )

            bound_errors = _weight_bound_errors(weights, weight_min, weight_max)
            for err in bound_errors:
                st.warning(err)

    # ── Submission handling ────────────────────────────────────────────────────
    if submit_clicked:
        if not agree:
            st.error("Please tick the disclaimer checkbox before submitting.")
        else:
            tickers, amounts = _parse_portfolio_df(edited_df)
            weight_min = st.session_state.get(SK_WEIGHT_MIN, DEFAULT_WEIGHT_MIN)
            weight_max = st.session_state.get(SK_WEIGHT_MAX, DEFAULT_WEIGHT_MAX)

            if len(tickers) < _MIN_TICKERS:
                st.error(f"Enter at least {_MIN_TICKERS} holdings with non-zero amounts.")
            elif len(tickers) > _MAX_TICKERS:
                st.error(
                    f"Maximum {_MAX_TICKERS} tickers. "
                    f"Remove {len(tickers) - _MAX_TICKERS} row(s) and resubmit."
                )
            else:
                weights = _compute_weights(tickers, amounts)
                bound_errors = _weight_bound_errors(weights, weight_min, weight_max)
                if bound_errors:
                    st.error(
                        "Weight constraints not met. Adjust dollar amounts or update "
                        "weight bounds in **Settings**."
                    )
                    for err in bound_errors:
                        st.warning(err)
                else:
                    # Persist the submitted DataFrame so navigating back to
                    # INPUT pre-populates the form with the last portfolio.
                    st.session_state[_KEY_LAST_SUBMITTED] = edited_df.copy()
                    # Reset the base so _init_input_state picks it up fresh
                    # on the next INPUT render (after navigation back).
                    st.session_state.pop(_KEY_PORTFOLIO_BASE, None)
                    st.session_state[SK_TOTAL_VALUE] = float(sum(amounts))
                    st.markdown("---")
                    success = _run_pipeline(
                        tickers, benchmark, weights, portfolio_name
                    )
                    if success:
                        st.session_state["_nav_pending"] = "DASHBOARD"
                        st.rerun()
