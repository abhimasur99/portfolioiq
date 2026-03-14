"""analytics/market_signals.py

Live market preparedness signals — the Risk Preparedness Panel.

Responsibilities:
Fetch and interpret all 11 live forward-looking signals. Each signal returns
a current value, status (green/amber/red), and one-sentence interpretation.

Signals (fetched fresh each session, NOT cached with price data TTL):
1.  VIX level — market 30-day implied volatility. ^VIX.
    >20 = elevated stress (amber). >30 = acute fear (red).
2.  VIX 30-day trend — rising vs falling. Computed from 30-day window.
3.  VIX term structure — VIX vs VIX3M vs VIX6M (VXMT fallback for VIX3M).
    Backwardation = near-term fear elevated (amber/red).
4.  MOVE index — bond market implied volatility. ^MOVE.
5.  Yield curve — ^TNX minus ^TYX spread (per spec; see DECISIONS.md for note
    on ^TYX being 30yr not 2yr). Inversion = caution signal.
6.  Credit spreads — HYG yield proxy minus IEF yield proxy. Widening = risk-off.
7.  Copper-to-gold ratio — CPER / GLD. Rising = growth optimism.
8.  Dollar index — DX-Y.NYB. Rising DXY = headwind for global-revenue tech.
9.  Oil sensitivity — rolling 60-day correlation between portfolio and USO.
10. Rate sensitivity — rolling 60-day correlation between portfolio and TLT.
11. Tech concentration — sum of GICS technology sector weights.

Graceful fallbacks:
- VIX3M unavailable → use VXMT.
- MOVE unavailable → surface warning, omit signal.
- Any signal fetch failure → return status "unavailable" without crashing.

Dependencies: yfinance, pandas, numpy.
Assumptions:
- Portfolio returns available in session state for rolling correlation signals.
- ^TNX and ^TYX return annualized percentages; divide by 100 for spread in pct pts.

Implemented in: Session 6.
"""

import numpy as np
import pandas as pd
import yfinance

from assets.config import (
    SIGNAL_VIX, SIGNAL_VIX3M, SIGNAL_VXMT, SIGNAL_MOVE,
    SIGNAL_TNX, SIGNAL_TYX, SIGNAL_HYG, SIGNAL_IEF,
    SIGNAL_GLD, SIGNAL_CPER, SIGNAL_USO, SIGNAL_TLT, SIGNAL_DXY,
)

_WINDOW_TREND = 30
_WINDOW_CORR = 60

_ALL_SIGNAL_TICKERS = [
    SIGNAL_VIX, SIGNAL_VIX3M, SIGNAL_VXMT, SIGNAL_MOVE,
    SIGNAL_TNX, SIGNAL_TYX, SIGNAL_HYG, SIGNAL_IEF,
    SIGNAL_GLD, SIGNAL_CPER, SIGNAL_USO, SIGNAL_TLT, SIGNAL_DXY,
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _unavailable(msg: str = "Signal data unavailable.") -> dict:
    return {"value": None, "status": "unavailable", "interpretation": msg, "raw": None}


def _fetch_prices(period: str = "6mo") -> dict:
    """Batch-download all signal tickers. Returns {ticker: pd.Series of close prices}.

    Uses yfinance.download with MultiIndex column structure (standard for
    multi-ticker requests). Per-ticker errors are silently dropped — caller
    handles missing tickers via _unavailable().
    """
    out = {}
    try:
        df = yfinance.download(
            _ALL_SIGNAL_TICKERS,
            period=period,
            auto_adjust=False,
            progress=False,
            threads=False,
        )
    except Exception:
        return out

    if df is None or df.empty:
        return out

    price_level = None
    if isinstance(df.columns, pd.MultiIndex):
        levels = df.columns.get_level_values(0).unique().tolist()
        if "Adj Close" in levels:
            price_level = "Adj Close"
        elif "Close" in levels:
            price_level = "Close"
        if price_level is None:
            return out
        for ticker in _ALL_SIGNAL_TICKERS:
            try:
                s = df[price_level][ticker].dropna()
                if len(s) > 0:
                    out[ticker] = s
            except Exception:
                continue
    else:
        # Flat DataFrame (single ticker returned — unlikely in batch, but safe)
        for col in ("Adj Close", "Close"):
            if col in df.columns:
                s = df[col].dropna()
                if len(s) > 0 and len(_ALL_SIGNAL_TICKERS) == 1:
                    out[_ALL_SIGNAL_TICKERS[0]] = s
                break

    return out


# ── Signal computations ────────────────────────────────────────────────────────

def _sig_vix_level(prices: dict) -> dict:
    try:
        s = prices.get(SIGNAL_VIX)
        if s is None or len(s) == 0:
            return _unavailable("^VIX data unavailable.")
        val = float(s.iloc[-1])
        if val <= 0 or not np.isfinite(val):
            return _unavailable("^VIX value is non-positive or non-finite.")
        if val < 20:
            status = "green"
            interp = f"VIX at {val:.1f} — market calm, low implied volatility."
        elif val < 30:
            status = "amber"
            interp = f"VIX at {val:.1f} — elevated stress, above-normal implied volatility."
        else:
            status = "red"
            interp = f"VIX at {val:.1f} — acute fear, extreme implied volatility."
        return {"value": val, "status": status, "interpretation": interp, "raw": s}
    except Exception:
        return _unavailable()


def _sig_vix_trend(prices: dict) -> dict:
    try:
        s = prices.get(SIGNAL_VIX)
        if s is None or len(s) < _WINDOW_TREND:
            return _unavailable("Insufficient VIX history for 30-day trend.")
        recent = s.iloc[-_WINDOW_TREND:].values.astype(float)
        slope = float(np.polyfit(np.arange(len(recent)), recent, 1)[0])
        if slope > 0.05:
            status = "amber"
            interp = "VIX trending higher — rising market fear over the last 30 days."
        elif slope < -0.05:
            status = "green"
            interp = "VIX trending lower — market fear subsiding over the last 30 days."
        else:
            status = "green"
            interp = "VIX trend flat — market volatility expectations stable over 30 days."
        return {"value": slope, "status": status, "interpretation": interp, "raw": s.iloc[-_WINDOW_TREND:]}
    except Exception:
        return _unavailable()


def _sig_vix_term_structure(prices: dict) -> dict:
    try:
        vix = prices.get(SIGNAL_VIX)
        # Prefer VIX3M; fall back to VXMT
        vix3m = prices.get(SIGNAL_VIX3M)
        if vix3m is None or len(vix3m) == 0:
            vix3m = prices.get(SIGNAL_VXMT)
        if vix is None or vix3m is None or len(vix) == 0 or len(vix3m) == 0:
            return _unavailable("VIX or VIX3M/VXMT data unavailable for term structure.")
        spot = float(vix.iloc[-1])
        term = float(vix3m.iloc[-1])
        spread = spot - term  # positive = backwardation (near > long)
        if spread > 2.0:
            status = "red"
            interp = f"VIX term structure in strong backwardation (VIX−VIX3M={spread:+.1f}) — acute near-term fear."
        elif spread > 0.0:
            status = "amber"
            interp = f"VIX term structure mildly inverted (VIX−VIX3M={spread:+.1f}) — modest near-term stress."
        else:
            status = "green"
            interp = f"VIX term structure in contango (VIX−VIX3M={spread:+.1f}) — normal, long-term vol above spot."
        return {"value": spread, "status": status, "interpretation": interp,
                "raw": {"vix": spot, "vix3m": term}}
    except Exception:
        return _unavailable()


def _sig_move_index(prices: dict) -> dict:
    try:
        s = prices.get(SIGNAL_MOVE)
        if s is None or len(s) == 0:
            return _unavailable("MOVE index data unavailable.")
        val = float(s.iloc[-1])
        if not np.isfinite(val) or val <= 0:
            return _unavailable("MOVE index value invalid.")
        if val < 80:
            status = "green"
            interp = f"MOVE at {val:.0f} — bond market volatility calm."
        elif val < 120:
            status = "amber"
            interp = f"MOVE at {val:.0f} — elevated bond market volatility."
        else:
            status = "red"
            interp = f"MOVE at {val:.0f} — acute bond market volatility stress."
        return {"value": val, "status": status, "interpretation": interp, "raw": s}
    except Exception:
        return _unavailable()


def _sig_yield_curve(prices: dict) -> dict:
    try:
        tnx = prices.get(SIGNAL_TNX)
        tyx = prices.get(SIGNAL_TYX)
        if tnx is None or tyx is None or len(tnx) == 0 or len(tyx) == 0:
            return _unavailable("Treasury yield data unavailable.")
        tnx_val = float(tnx.iloc[-1])  # 10-yr, annualized %
        tyx_val = float(tyx.iloc[-1])  # 30-yr, annualized %
        # Convert to decimal pct points for the spread value
        spread = (tnx_val - tyx_val) / 100.0
        if not np.isfinite(spread):
            return _unavailable("Yield curve spread is not finite.")
        if spread > 0.0:
            # 10yr > 30yr = inverted long end
            status = "amber"
            interp = f"Yield curve: 10yr ({tnx_val:.2f}%) > 30yr ({tyx_val:.2f}%) — atypical long-end inversion."
        elif spread > -0.005:
            status = "amber"
            interp = f"Yield curve flat ({spread*100:+.1f} bps) — historically associated with slowing growth."
        else:
            status = "green"
            interp = f"Yield curve normal ({spread*100:+.1f} bps, 30yr > 10yr) — typical upward slope."
        return {"value": spread, "status": status, "interpretation": interp,
                "raw": {"tnx": tnx_val, "tyx": tyx_val}}
    except Exception:
        return _unavailable()


def _sig_credit_spreads(prices: dict) -> dict:
    try:
        hyg = prices.get(SIGNAL_HYG)
        ief = prices.get(SIGNAL_IEF)
        if hyg is None or ief is None or len(hyg) < 2 or len(ief) < 2:
            return _unavailable("HYG or IEF data unavailable for credit spread proxy.")
        window = min(30, len(hyg) - 1, len(ief) - 1)
        hyg_ret = float(hyg.iloc[-1] / hyg.iloc[-(window + 1)] - 1.0)
        ief_ret = float(ief.iloc[-1] / ief.iloc[-(window + 1)] - 1.0)
        spread_proxy = hyg_ret - ief_ret  # negative = HY underperforms = spreads widening
        if spread_proxy < -0.05:
            status = "red"
            interp = f"Credit spreads significantly widened ({spread_proxy*100:+.1f}% HY vs IG over 30d) — risk-off signal."
        elif spread_proxy < -0.01:
            status = "amber"
            interp = f"Credit spreads mildly widened ({spread_proxy*100:+.1f}% HY vs IG over 30d) — monitor for deterioration."
        else:
            status = "green"
            interp = f"Credit spreads stable/tightening ({spread_proxy*100:+.1f}% HY vs IG over 30d) — risk appetite intact."
        return {"value": spread_proxy, "status": status, "interpretation": interp,
                "raw": {"hyg": float(hyg.iloc[-1]), "ief": float(ief.iloc[-1])}}
    except Exception:
        return _unavailable()


def _sig_copper_gold_ratio(prices: dict) -> dict:
    try:
        cper = prices.get(SIGNAL_CPER)
        gld = prices.get(SIGNAL_GLD)
        if cper is None or gld is None or len(cper) < _WINDOW_TREND or len(gld) < _WINDOW_TREND:
            return _unavailable("CPER or GLD data unavailable for copper-to-gold ratio.")
        ratio_now = float(cper.iloc[-1]) / float(gld.iloc[-1])
        ratio_prev = float(cper.iloc[-_WINDOW_TREND]) / float(gld.iloc[-_WINDOW_TREND])
        denom = abs(ratio_prev)
        pct_change = (ratio_now - ratio_prev) / denom if denom > 1e-10 else 0.0
        if pct_change > 0.02:
            status = "green"
            interp = f"Copper/gold ratio rising ({pct_change*100:+.1f}% over 30d) — growth optimism increasing."
        elif pct_change < -0.02:
            status = "amber"
            interp = f"Copper/gold ratio falling ({pct_change*100:+.1f}% over 30d) — growth concerns emerging."
        else:
            status = "green"
            interp = f"Copper/gold ratio stable ({pct_change*100:+.1f}% over 30d) — neutral growth signal."
        return {"value": ratio_now, "status": status, "interpretation": interp,
                "raw": {"copper": float(cper.iloc[-1]), "gold": float(gld.iloc[-1])}}
    except Exception:
        return _unavailable()


def _sig_dollar_index(prices: dict) -> dict:
    try:
        s = prices.get(SIGNAL_DXY)
        if s is None or len(s) < _WINDOW_TREND:
            return _unavailable("Dollar index (DXY) data unavailable.")
        val = float(s.iloc[-1])
        prev = float(s.iloc[-_WINDOW_TREND])
        denom = abs(prev)
        pct_change = (val - prev) / denom if denom > 1e-10 else 0.0
        if pct_change > 0.02:
            status = "amber"
            interp = f"Dollar index rising ({pct_change*100:+.1f}% over 30d) — headwind for global-revenue equities."
        elif pct_change < -0.02:
            status = "green"
            interp = f"Dollar index falling ({pct_change*100:+.1f}% over 30d) — tailwind for global-revenue equities."
        else:
            status = "green"
            interp = f"Dollar index stable ({pct_change*100:+.1f}% over 30d) — neutral currency environment."
        return {"value": val, "status": status, "interpretation": interp, "raw": s}
    except Exception:
        return _unavailable()


def _sig_oil_sensitivity(portfolio_returns: pd.Series, prices: dict) -> dict:
    try:
        uso = prices.get(SIGNAL_USO)
        if uso is None or len(uso) < _WINDOW_CORR + 1:
            return _unavailable("Insufficient USO data for oil sensitivity computation.")
        uso_returns = np.log(uso / uso.shift(1)).dropna()
        common = portfolio_returns.index.intersection(uso_returns.index)
        if len(common) < _WINDOW_CORR:
            return _unavailable("Insufficient date overlap for oil sensitivity (need 60 days).")
        port_aligned = portfolio_returns.loc[common]
        uso_aligned = uso_returns.loc[common]
        rolling_corr = port_aligned.rolling(_WINDOW_CORR).corr(uso_aligned)
        corr_val = float(rolling_corr.iloc[-1])
        if not np.isfinite(corr_val):
            return _unavailable("Oil sensitivity correlation is undefined (insufficient variance).")
        corr_val = float(np.clip(corr_val, -1.0, 1.0))
        if abs(corr_val) > 0.5:
            status = "amber"
            interp = f"Portfolio has significant oil sensitivity (ρ={corr_val:.2f}) — exposed to energy price moves."
        else:
            status = "green"
            interp = f"Portfolio has low oil sensitivity (ρ={corr_val:.2f}) — limited energy price exposure."
        return {"value": corr_val, "status": status, "interpretation": interp, "raw": rolling_corr}
    except Exception:
        return _unavailable()


def _sig_rate_sensitivity(portfolio_returns: pd.Series, prices: dict) -> dict:
    try:
        tlt = prices.get(SIGNAL_TLT)
        if tlt is None or len(tlt) < _WINDOW_CORR + 1:
            return _unavailable("Insufficient TLT data for rate sensitivity computation.")
        tlt_returns = np.log(tlt / tlt.shift(1)).dropna()
        common = portfolio_returns.index.intersection(tlt_returns.index)
        if len(common) < _WINDOW_CORR:
            return _unavailable("Insufficient date overlap for rate sensitivity (need 60 days).")
        port_aligned = portfolio_returns.loc[common]
        tlt_aligned = tlt_returns.loc[common]
        rolling_corr = port_aligned.rolling(_WINDOW_CORR).corr(tlt_aligned)
        corr_val = float(rolling_corr.iloc[-1])
        if not np.isfinite(corr_val):
            return _unavailable("Rate sensitivity correlation is undefined (insufficient variance).")
        corr_val = float(np.clip(corr_val, -1.0, 1.0))
        if corr_val < -0.4:
            status = "red"
            interp = f"Portfolio strongly negatively correlated with bonds (ρ={corr_val:.2f}) — high rate risk."
        elif abs(corr_val) > 0.3:
            status = "amber"
            interp = f"Portfolio moderately rate-sensitive (ρ={corr_val:.2f}) — monitor interest rate moves."
        else:
            status = "green"
            interp = f"Portfolio has low rate sensitivity (ρ={corr_val:.2f}) — limited bond market exposure."
        return {"value": corr_val, "status": status, "interpretation": interp, "raw": rolling_corr}
    except Exception:
        return _unavailable()


def _sig_tech_concentration() -> dict:
    # Requires sector_weights which are not passed into fetch_all_signals.
    # Surface as unavailable; caller can inject sector data if needed.
    return _unavailable(
        "Tech concentration unavailable — sector weights not provided to signal layer."
    )


# ── Public API ─────────────────────────────────────────────────────────────────

def fetch_all_signals(portfolio_returns: "pd.Series") -> dict:
    """Fetch and interpret all 11 live market preparedness signals.

    Args:
        portfolio_returns: pd.Series of daily portfolio log returns,
                           used for oil and rate sensitivity correlations.

    Returns:
        dict keyed by signal name, each value is a dict with:
        - value: float or None — current signal value.
        - status: str — "green" | "amber" | "red" | "unavailable".
        - interpretation: str — one-sentence plain-language reading.
        - raw: any — raw fetched data for chart use if applicable.
    """
    prices = _fetch_prices(period="6mo")

    return {
        "vix_level":          _sig_vix_level(prices),
        "vix_trend":          _sig_vix_trend(prices),
        "vix_term_structure": _sig_vix_term_structure(prices),
        "move_index":         _sig_move_index(prices),
        "yield_curve":        _sig_yield_curve(prices),
        "credit_spreads":     _sig_credit_spreads(prices),
        "copper_gold_ratio":  _sig_copper_gold_ratio(prices),
        "dollar_index":       _sig_dollar_index(prices),
        "oil_sensitivity":    _sig_oil_sensitivity(portfolio_returns, prices),
        "rate_sensitivity":   _sig_rate_sensitivity(portfolio_returns, prices),
        "tech_concentration": _sig_tech_concentration(),
    }
