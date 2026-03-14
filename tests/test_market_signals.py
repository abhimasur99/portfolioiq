"""tests/test_market_signals.py

Unit tests for analytics/market_signals.py.

Test plan (Session 6):
- test_all_signal_keys_present: output dict has all 11 expected signal keys.
- test_signal_status_valid: each signal's "status" is one of green/amber/red/unavailable.
- test_oil_sensitivity_range: oil sensitivity correlation in [-1, 1].
- test_rate_sensitivity_range: rate sensitivity correlation in [-1, 1].
- test_vix_level_positive: VIX level > 0.
- test_yield_curve_sign: yield curve spread is a finite float.

Market signal fetches are mocked in these tests — no real API calls.
Uses pytest-mock to patch yfinance.download in market_signals module.

No real API calls. All tests use fixtures from conftest.py.
"""

import numpy as np
import pandas as pd
import pytest

from analytics.market_signals import fetch_all_signals


EXPECTED_SIGNAL_KEYS = [
    "vix_level",
    "vix_trend",
    "vix_term_structure",
    "move_index",
    "yield_curve",
    "credit_spreads",
    "copper_gold_ratio",
    "dollar_index",
    "oil_sensitivity",
    "rate_sensitivity",
    "tech_concentration",
]

_SIGNAL_TICKERS = [
    "^VIX", "^VIX3M", "VXMT", "^MOVE", "^TNX", "^TYX",
    "HYG", "IEF", "GLD", "CPER", "USO", "TLT", "DX-Y.NYB",
]


def _build_mock_signal_df(portfolio_returns: pd.Series) -> pd.DataFrame:
    """Build a MultiIndex DataFrame mimicking yfinance.download for all signal tickers.

    Uses portfolio_returns.index as the date axis so that oil/rate sensitivity
    rolling-correlation lookups find overlapping dates. Values are designed to
    exercise non-unavailable code paths for every signal.
    """
    dates = portfolio_returns.index
    n = len(dates)
    rng = np.random.default_rng(123)

    # Per-ticker price series (all positive, reasonable magnitudes)
    raw = {
        "^VIX":     np.clip(np.linspace(18.0, 22.0, n) + rng.standard_normal(n) * 0.5, 10, 50),
        "^VIX3M":   np.clip(np.linspace(19.5, 23.5, n) + rng.standard_normal(n) * 0.5, 10, 50),
        "VXMT":     np.clip(np.linspace(19.0, 23.0, n) + rng.standard_normal(n) * 0.5, 10, 50),
        "^MOVE":    np.clip(np.full(n, 90.0) + rng.standard_normal(n), 50, 200),
        "^TNX":     np.clip(np.full(n, 4.5) + rng.standard_normal(n) * 0.05, 0.1, 10),
        "^TYX":     np.clip(np.full(n, 4.8) + rng.standard_normal(n) * 0.05, 0.1, 10),
        "HYG":      np.clip(np.full(n, 75.0) + rng.standard_normal(n) * 0.2, 50, 100),
        "IEF":      np.clip(np.full(n, 95.0) + rng.standard_normal(n) * 0.2, 70, 110),
        "GLD":      np.clip(np.full(n, 180.0) + rng.standard_normal(n) * 0.5, 100, 250),
        "CPER":     np.clip(np.full(n, 25.0) + rng.standard_normal(n) * 0.1, 10, 50),
        "USO":      np.clip(np.full(n, 70.0) + rng.standard_normal(n) * 2.0, 30, 120),
        "TLT":      np.clip(np.full(n, 95.0) + rng.standard_normal(n) * 1.0, 60, 130),
        "DX-Y.NYB": np.clip(np.full(n, 104.0) + rng.standard_normal(n) * 0.2, 80, 130),
    }

    price_types = ["Adj Close", "Close"]
    multi_cols = pd.MultiIndex.from_product(
        [price_types, _SIGNAL_TICKERS], names=["Price", "Ticker"]
    )
    df = pd.DataFrame(index=dates, columns=multi_cols, dtype=float)
    for ticker in _SIGNAL_TICKERS:
        for pt in price_types:
            df[(pt, ticker)] = raw[ticker]

    return df


class TestSignalStructure:
    def test_all_signal_keys_present(self, mock_portfolio_returns, mocker):
        """Output dict contains all 11 expected signal keys."""
        mock_df = _build_mock_signal_df(mock_portfolio_returns)
        mocker.patch("yfinance.download", return_value=mock_df)
        result = fetch_all_signals(mock_portfolio_returns)
        for key in EXPECTED_SIGNAL_KEYS:
            assert key in result, f"Missing signal key: {key}"

    def test_signal_status_valid(self, mock_portfolio_returns, mocker):
        """Every signal's status is one of the four valid values."""
        mock_df = _build_mock_signal_df(mock_portfolio_returns)
        mocker.patch("yfinance.download", return_value=mock_df)
        result = fetch_all_signals(mock_portfolio_returns)
        valid = {"green", "amber", "red", "unavailable"}
        for key in EXPECTED_SIGNAL_KEYS:
            status = result[key]["status"]
            assert status in valid, f"Signal '{key}' has invalid status: '{status}'"

    def test_signal_dict_has_required_fields(self, mock_portfolio_returns, mocker):
        """Every signal dict has value, status, interpretation, and raw fields."""
        mock_df = _build_mock_signal_df(mock_portfolio_returns)
        mocker.patch("yfinance.download", return_value=mock_df)
        result = fetch_all_signals(mock_portfolio_returns)
        required = {"value", "status", "interpretation", "raw"}
        for key in EXPECTED_SIGNAL_KEYS:
            assert required.issubset(result[key].keys()), (
                f"Signal '{key}' is missing fields. Got: {set(result[key].keys())}"
            )

    def test_signal_interpretation_is_string(self, mock_portfolio_returns, mocker):
        """Every signal's interpretation is a non-empty string."""
        mock_df = _build_mock_signal_df(mock_portfolio_returns)
        mocker.patch("yfinance.download", return_value=mock_df)
        result = fetch_all_signals(mock_portfolio_returns)
        for key in EXPECTED_SIGNAL_KEYS:
            interp = result[key]["interpretation"]
            assert isinstance(interp, str) and len(interp) > 0, (
                f"Signal '{key}' has empty or non-string interpretation"
            )


class TestSignalValues:
    def test_oil_sensitivity_range(self, mock_portfolio_returns, mocker):
        """Oil sensitivity correlation is in [-1, 1]."""
        mock_df = _build_mock_signal_df(mock_portfolio_returns)
        mocker.patch("yfinance.download", return_value=mock_df)
        result = fetch_all_signals(mock_portfolio_returns)
        sig = result["oil_sensitivity"]
        assert sig["status"] != "unavailable", (
            "Oil sensitivity should compute with mock data — got 'unavailable'. "
            f"Interpretation: {sig['interpretation']}"
        )
        assert -1.0 <= sig["value"] <= 1.0, (
            f"Oil sensitivity value {sig['value']!r} is outside [-1, 1]"
        )

    def test_rate_sensitivity_range(self, mock_portfolio_returns, mocker):
        """Rate sensitivity correlation is in [-1, 1]."""
        mock_df = _build_mock_signal_df(mock_portfolio_returns)
        mocker.patch("yfinance.download", return_value=mock_df)
        result = fetch_all_signals(mock_portfolio_returns)
        sig = result["rate_sensitivity"]
        assert sig["status"] != "unavailable", (
            "Rate sensitivity should compute with mock data — got 'unavailable'. "
            f"Interpretation: {sig['interpretation']}"
        )
        assert -1.0 <= sig["value"] <= 1.0, (
            f"Rate sensitivity value {sig['value']!r} is outside [-1, 1]"
        )

    def test_vix_level_positive(self, mock_portfolio_returns, mocker):
        """VIX level value is strictly positive."""
        mock_df = _build_mock_signal_df(mock_portfolio_returns)
        mocker.patch("yfinance.download", return_value=mock_df)
        result = fetch_all_signals(mock_portfolio_returns)
        sig = result["vix_level"]
        assert sig["status"] != "unavailable", "VIX level should compute with mock data."
        assert sig["value"] > 0.0, f"VIX level {sig['value']!r} is not positive"

    def test_yield_curve_sign(self, mock_portfolio_returns, mocker):
        """Yield curve spread is a finite float (sign not constrained by test)."""
        mock_df = _build_mock_signal_df(mock_portfolio_returns)
        mocker.patch("yfinance.download", return_value=mock_df)
        result = fetch_all_signals(mock_portfolio_returns)
        sig = result["yield_curve"]
        assert sig["status"] != "unavailable", "Yield curve should compute with mock data."
        assert isinstance(sig["value"], float), (
            f"Yield curve value is not a float: {type(sig['value'])}"
        )
        assert np.isfinite(sig["value"]), (
            f"Yield curve value is not finite: {sig['value']!r}"
        )

    def test_tech_concentration_unavailable_without_weights(self, mock_portfolio_returns, mocker):
        """Tech concentration returns 'unavailable' since sector_weights are not passed."""
        mock_df = _build_mock_signal_df(mock_portfolio_returns)
        mocker.patch("yfinance.download", return_value=mock_df)
        result = fetch_all_signals(mock_portfolio_returns)
        assert result["tech_concentration"]["status"] == "unavailable"

    def test_graceful_fallback_on_empty_download(self, mock_portfolio_returns, mocker):
        """All signals return 'unavailable' (not crash) when yfinance returns empty DataFrame."""
        empty_df = pd.DataFrame()
        mocker.patch("yfinance.download", return_value=empty_df)
        result = fetch_all_signals(mock_portfolio_returns)
        # 10 computed signals (all but tech_concentration, which is always unavailable) go unavailable
        for key in EXPECTED_SIGNAL_KEYS:
            assert result[key]["status"] == "unavailable", (
                f"Expected 'unavailable' for '{key}' on empty download, got '{result[key]['status']}'"
            )
