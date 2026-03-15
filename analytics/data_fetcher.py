"""analytics/data_fetcher.py

Data fetching layer — yfinance wrapper with caching and error handling.

Responsibilities:
- Multi-ticker download via yfinance.download (single batched call, not per-ticker).
- Explicit handling of yfinance MultiIndex column structure: (price_type, ticker).
- Adjusted Close extraction (never raw Close).
- NaN dropping after every fetch.
- Ticker validation before computation — surfaces inline error on invalid ticker.
- Exponential backoff on rate limiting: 1s -> 2s -> 4s.
- ^IRX fetch and conversion: annualized % / 100 / 252 = daily decimal rate.
- 1-hour TTL cache for price data via @st.cache_data.
- Market signals fetched fresh each session — NOT cached with price data TTL.

Does NOT compute returns or any derived analytics.

Dependencies: yfinance, pandas, numpy, streamlit (for cache decorator).
Assumptions:
- yfinance returns MultiIndex DataFrame for multi-ticker downloads:
    columns level 0 = price type ("Adj Close", "Close", ...)
    columns level 1 = ticker symbol
- Adjusted Close accounts for dividends and splits (total return basis).
- ^IRX may return NaN rows; use last valid value.

Architecture note:
  Public functions (fetch_price_data, fetch_risk_free_rate) are thin cached
  wrappers around private _impl functions. Tests call the _impl functions
  directly after mocking yfinance.download, avoiding Streamlit context issues
  with @st.cache_data in the test environment.
"""

import time
import logging

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

from assets.config import RISK_FREE_TICKER

logger = logging.getLogger(__name__)

# Fallback risk-free rate if ^IRX is unavailable (4% annualized)
_FALLBACK_ANNUAL_RATE = 0.04
_FALLBACK_DAILY_RATE = _FALLBACK_ANNUAL_RATE / 252.0

# Exponential backoff delays in seconds
_BACKOFF_DELAYS = [1, 2, 4]


# ── Private implementation functions (testable, not cached) ───────────────────

def _download_with_backoff(
    tickers: list[str],
    period: str,
    max_retries: int = 3,
) -> pd.DataFrame:
    """Download price data from yfinance with exponential backoff.

    Args:
        tickers: List of ticker symbols. Joined into a space-separated string
                 for a single batched yfinance.download call.
        period: yfinance period string (e.g. "1y", "3y", "5y").
        max_retries: Maximum download attempts before raising.

    Returns:
        Raw pd.DataFrame from yfinance.download (MultiIndex for multiple tickers).

    Raises:
        ValueError: If yfinance returns an empty DataFrame.
        RuntimeError: If all retry attempts fail.
    """
    ticker_str = " ".join(tickers)
    last_exc: Exception | None = None

    for attempt, delay in enumerate([0] + _BACKOFF_DELAYS[:max_retries - 1]):
        if delay:
            logger.warning("Rate limit hit — retrying in %ds (attempt %d)", delay, attempt + 1)
            time.sleep(delay)
        try:
            raw = yf.download(
                ticker_str,
                period=period,
                auto_adjust=False,
                progress=False,
                threads=True,
            )
            if raw.empty:
                raise ValueError(
                    f"yfinance returned no data for tickers: {tickers}. "
                    "Check ticker symbols and try a shorter period."
                )
            return raw
        except ValueError:
            raise  # Don't retry on validation errors
        except Exception as exc:
            last_exc = exc
            if attempt == max_retries - 1:
                break
            # Only retry on plausible transient errors
            exc_str = str(exc).lower()
            if not any(k in exc_str for k in ("rate", "timeout", "connect", "http")):
                raise

    raise RuntimeError(
        f"Failed to fetch data for {tickers} after {max_retries} attempts. "
        f"Last error: {last_exc}"
    )


def _extract_adj_close(raw: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """Extract Adj Close columns from a yfinance download result.

    Handles both MultiIndex (multi-ticker) and flat (single-ticker) column
    structures returned by yfinance.

    Args:
        raw: Raw DataFrame from yfinance.download.
        tickers: Expected ticker symbols (used for column naming).

    Returns:
        pd.DataFrame with tickers as columns and dates as index.
        NaN rows dropped. Columns ordered to match input tickers.

    Raises:
        ValueError: If Adj Close data is missing or all-NaN for any ticker.
    """
    if isinstance(raw.columns, pd.MultiIndex):
        # Multi-ticker: columns are (price_type, ticker)
        try:
            prices = raw["Adj Close"].copy()
        except KeyError:
            raise ValueError(
                "yfinance output missing 'Adj Close' column. "
                "Ensure auto_adjust=False is set."
            )
    else:
        # Single ticker: flat columns ["Open", "High", ..., "Adj Close"]
        if "Adj Close" not in raw.columns:
            raise ValueError(
                "yfinance output missing 'Adj Close' column. "
                "Ensure auto_adjust=False is set."
            )
        prices = raw[["Adj Close"]].copy()
        prices.columns = tickers  # rename to the ticker symbol

    prices = prices.dropna(how="all")

    # Validate each expected ticker has data
    missing = []
    for ticker in tickers:
        if ticker not in prices.columns:
            missing.append(ticker)
        elif prices[ticker].isna().all():
            missing.append(ticker)

    if missing:
        raise ValueError(
            f"No data returned for ticker(s): {missing}. "
            "Verify the symbols are valid and have data for the selected period."
        )

    # Drop rows where any ticker has NaN, then reorder to match input
    prices = prices[tickers].dropna()
    return prices


def _fetch_price_data_impl(tickers: list[str], period: str) -> pd.DataFrame:
    """Pure implementation of price data fetching (no cache, testable).

    Args:
        tickers: List of ticker symbols.
        period: yfinance period string.

    Returns:
        pd.DataFrame: adjusted close prices, dates x tickers. No NaN rows.

    Raises:
        ValueError: On invalid tickers or empty data.
        RuntimeError: On persistent network failure.
    """
    raw = _download_with_backoff(tickers, period)
    return _extract_adj_close(raw, tickers)


def _fetch_risk_free_rate_impl() -> float:
    """Pure implementation of risk-free rate fetch (no cache, testable).

    Fetches ^IRX (13-week T-bill yield), extracts the last valid value,
    and converts from annualized percentage to daily decimal rate.

    Conversion: annualized_pct / 100 / 252

    Returns:
        float: daily decimal risk-free rate. Falls back to
               _FALLBACK_DAILY_RATE (0.04 / 252) if fetch fails.
    """
    try:
        raw = yf.download(
            RISK_FREE_TICKER,
            period="5d",
            auto_adjust=False,
            progress=False,
        )
        if raw.empty:
            logger.warning("^IRX returned empty data — using fallback rate %.4f", _FALLBACK_ANNUAL_RATE)
            return _FALLBACK_DAILY_RATE

        # Handle both MultiIndex and flat column structures
        if isinstance(raw.columns, pd.MultiIndex):
            series = raw["Adj Close"].iloc[:, 0]
        else:
            col = "Adj Close" if "Adj Close" in raw.columns else "Close"
            series = raw[col]

        valid = series.dropna()
        if valid.empty:
            logger.warning("^IRX all-NaN — using fallback rate %.4f%%", _FALLBACK_ANNUAL_RATE)
            return _FALLBACK_DAILY_RATE

        last_val = float(valid.iloc[-1])
        daily_rate = last_val / 100.0 / 252.0
        logger.info("Risk-free rate: %.4f%% annualized -> %.6f daily", last_val, daily_rate)
        return daily_rate

    except Exception as exc:
        logger.warning("Failed to fetch ^IRX (%s) — using fallback %.4f%%", exc, _FALLBACK_ANNUAL_RATE)
        return _FALLBACK_DAILY_RATE


def validate_tickers(tickers: list[str]) -> tuple[list[str], list[str]]:
    """Pre-validate ticker symbols before triggering the full data pipeline.

    Uses a short 5-day download to confirm each ticker has live data.
    Batches all tickers in a single call to minimise API usage.

    Args:
        tickers: List of ticker symbols to validate.

    Returns:
        Tuple of (valid_tickers, invalid_tickers).
        A ticker is "invalid" if it returns no data or all-NaN Adj Close.
    """
    if not tickers:
        return [], []

    try:
        raw = _download_with_backoff(tickers, period="5d")
        if isinstance(raw.columns, pd.MultiIndex):
            adj = raw["Adj Close"] if "Adj Close" in raw.columns.get_level_values(0) else pd.DataFrame()
        else:
            adj = raw[["Adj Close"]] if "Adj Close" in raw.columns else pd.DataFrame()
            if not adj.empty and len(tickers) == 1:
                adj.columns = tickers

        valid, invalid = [], []
        for ticker in tickers:
            if ticker in adj.columns and not adj[ticker].dropna().empty:
                valid.append(ticker)
            else:
                invalid.append(ticker)
        return valid, invalid

    except Exception as exc:
        logger.warning("Ticker validation skipped (network/API error: %s) — proceeding to main fetch", exc)
        return tickers, []  # skip validation; let the main pipeline surface the real error


# ── Public cached API ─────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def fetch_price_data(tickers: tuple[str, ...], period: str) -> pd.DataFrame:
    """Fetch adjusted close prices for a portfolio of tickers.

    Cached with a 1-hour TTL. Takes a tuple (not list) so Streamlit can
    hash the argument for cache keying.

    Args:
        tickers: Tuple of ticker symbols (e.g. ("AAPL", "MSFT", "SPY")).
                 Use tuple not list — lists are not hashable for cache keys.
        period: yfinance period string (e.g. "1y", "3y", "5y").

    Returns:
        pd.DataFrame with dates as index and tickers as columns.
        Adjusted close prices (total return). No NaN rows.

    Raises:
        ValueError: If any ticker is invalid or returns no data.
        RuntimeError: On persistent network failure after backoff retries.
    """
    return _fetch_price_data_impl(list(tickers), period)


def fetch_risk_free_rate() -> float:
    """Fetch the current risk-free rate from ^IRX (13-week T-bill yield).

    NOT cached — called once per session load and stored in session state.

    Returns:
        float: Daily decimal risk-free rate = annualized_pct / 100 / 252.
               Falls back to 0.04 / 252 if ^IRX is unavailable.
    """
    return _fetch_risk_free_rate_impl()


def fetch_market_signals() -> dict:
    """Fetch all 11 live market preparedness signals.

    NOT cached — fetched fresh on each session load per architecture spec.
    Implemented in Session 6 (market_signals.py).

    Returns:
        dict keyed by signal name with value, status, and interpretation.

    Raises:
        NotImplementedError until Session 6.
    """
    raise NotImplementedError("Implemented in Session 6 (analytics/market_signals.py).")
