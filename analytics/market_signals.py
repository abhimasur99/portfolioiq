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


def fetch_all_signals(portfolio_returns: "pd.Series") -> dict:
    """Fetch and interpret all 11 live market preparedness signals.

    Args:
        portfolio_returns: pd.Series of daily portfolio log returns,
                           used for oil and rate sensitivity correlations.

    Returns:
        dict keyed by signal name, each value is a dict with:
        - value: float or str — current signal value.
        - status: str — "green" | "amber" | "red" | "unavailable".
        - interpretation: str — one-sentence plain-language reading.
        - raw: any — raw fetched data for chart use if applicable.
    """
    raise NotImplementedError("Implemented in Session 6.")
