"""assets/config.py

Central configuration for PortfolioIQ.

Defines the color palette, typography constants, Plotly dark theme template,
all session state key constants, application-wide defaults, and static lookup
tables (benchmark options, stress scenarios, disclaimer text).

No analytics logic lives here. This module is imported by every page and chart
module. It is never modified at runtime — all values are read-only constants.

Dependencies: plotly (for template registration only).
Assumptions: Plotly template is registered at import time via pio.templates.
"""

import plotly.graph_objects as go
import plotly.io as pio

# ─── Color Palette ────────────────────────────────────────────────────────────

# Background hierarchy
COLOR_BG_PAGE      = "#010b14"  # outermost page / stApp background
COLOR_BG_PRIMARY   = "#030f1c"  # primary panel and card background
COLOR_BG_SECONDARY = "#051525"  # secondary panel / nested card
COLOR_BG_HOVER     = "#071a2e"  # hover state overlay

# Signal colors
COLOR_BLUE   = "#00d4ff"  # electric blue — neutral data / primary trace
COLOR_AMBER  = "#ef9f27"  # amber — warnings / caution flags
COLOR_RED    = "#e24b4a"  # red — risk flags / negative signals
COLOR_GREEN  = "#2aba6a"  # green — positive signals / improvements
COLOR_PURPLE = "#9f97ff"  # purple — diagnostic metrics

# Chart auxiliaries
COLOR_GRID       = "#0d2137"  # subtle grid lines
COLOR_AXIS       = "#1a3a5c"  # axis lines
COLOR_TEXT       = "#c8d8e8"  # primary text on dark background
COLOR_TEXT_MUTED = "#5a7a9a"  # muted / secondary text

# ─── Typography ───────────────────────────────────────────────────────────────

FONT_MONO    = "Share Tech Mono"  # data labels and numbers
FONT_HEADING = "Exo 2"           # headings and large KPI values
FONT_DISPLAY = "Rajdhani"        # supplementary display font

# ─── Plotly Dark Theme Template ───────────────────────────────────────────────

_template = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor=COLOR_BG_PRIMARY,
        plot_bgcolor=COLOR_BG_SECONDARY,
        font=dict(
            family=FONT_MONO,
            color=COLOR_TEXT,
            size=12,
        ),
        title=dict(
            font=dict(family=FONT_HEADING, color=COLOR_TEXT, size=16),
            x=0.01,
        ),
        xaxis=dict(
            gridcolor=COLOR_GRID,
            linecolor=COLOR_AXIS,
            zerolinecolor=COLOR_AXIS,
            tickfont=dict(family=FONT_MONO, color=COLOR_TEXT_MUTED, size=11),
        ),
        yaxis=dict(
            gridcolor=COLOR_GRID,
            linecolor=COLOR_AXIS,
            zerolinecolor=COLOR_AXIS,
            tickfont=dict(family=FONT_MONO, color=COLOR_TEXT_MUTED, size=11),
        ),
        legend=dict(
            bgcolor=COLOR_BG_PRIMARY,
            bordercolor=COLOR_AXIS,
            borderwidth=1,
            font=dict(family=FONT_MONO, color=COLOR_TEXT, size=11),
        ),
        colorway=[
            COLOR_BLUE,
            COLOR_GREEN,
            COLOR_AMBER,
            COLOR_PURPLE,
            COLOR_RED,
        ],
        margin=dict(l=50, r=30, t=50, b=50),
        hoverlabel=dict(
            bgcolor=COLOR_BG_SECONDARY,
            bordercolor=COLOR_AXIS,
            font=dict(family=FONT_MONO, color=COLOR_TEXT, size=11),
        ),
    )
)

PLOTLY_TEMPLATE_NAME = "portfolioiq"
pio.templates[PLOTLY_TEMPLATE_NAME] = _template
pio.templates.default = PLOTLY_TEMPLATE_NAME

# ─── Session State Keys ───────────────────────────────────────────────────────
# All keys defined here as constants. Page files NEVER use raw string literals
# as session state keys — always import and use these constants.

# Portfolio input
SK_TICKERS        = "tickers"           # list[str]
SK_WEIGHTS        = "weights"           # pd.Series, index=tickers
SK_BENCHMARK      = "benchmark"         # str, e.g. "SPY"
SK_PERIOD         = "period"            # str, e.g. "3y"
SK_PORTFOLIO_NAME = "portfolio_name"    # str (optional user label)

# Fetched market data
SK_PRICE_DATA     = "price_data"        # pd.DataFrame, MultiIndex cols
SK_RETURNS_DF     = "returns_df"        # pd.DataFrame, log returns per ticker
SK_PORT_RETURNS   = "portfolio_returns" # pd.Series, weighted portfolio log returns
SK_BENCH_RETURNS  = "benchmark_returns" # pd.Series, benchmark log returns
SK_RISK_FREE_RATE = "risk_free_rate"    # float, daily decimal rate from ^IRX

# Top-level analytics results dictionary
SK_ANALYTICS      = "analytics"         # dict — all computed results keyed below

# Sub-keys within analytics dict (used for targeted recompute on settings change)
SK_PERFORMANCE    = "performance"       # dict — Layer 1 results
SK_RISK_FACTORS   = "risk_factors"      # dict — Layer 2 results
SK_RISK_OUTLOOK   = "risk_outlook"      # dict — Layer 3 results
SK_OPTIMIZATION   = "optimization"      # dict — Layer 4 results
SK_MARKET_SIGNALS = "market_signals"    # dict — live preparedness signals

# Settings
SK_VAR_CONFIDENCE  = "var_confidence"   # float, e.g. 0.95
SK_VAR_METHOD      = "var_method"       # str, "historical" | "garch"
SK_MC_HORIZON      = "mc_horizon"       # int, years
SK_MC_PATHS        = "mc_paths"         # int, 1000 or 10000
SK_WEIGHT_MIN      = "weight_min"       # float, default 0.05
SK_WEIGHT_MAX      = "weight_max"       # float, default 0.50
SK_GARCH_REFIT     = "garch_refit"      # str, "each_load" | "daily"
SK_DRIFT_THRESHOLD = "drift_threshold"  # float, rebalancing drift threshold

# UI state
SK_PORTFOLIO_LOADED = "portfolio_loaded"  # bool

# ─── Application Defaults ─────────────────────────────────────────────────────

DEFAULT_BENCHMARK        = "SPY"
DEFAULT_PERIOD           = "3y"
DEFAULT_VAR_CONFIDENCE   = 0.95
DEFAULT_VAR_METHOD       = "historical"
DEFAULT_MC_HORIZON       = 10       # years
DEFAULT_MC_PATHS         = 1_000
DEFAULT_WEIGHT_MIN       = 0.05     # 5%
DEFAULT_WEIGHT_MAX       = 0.50     # 50%
DEFAULT_DRIFT_THRESHOLD  = 0.05     # 5% drift before rebalance flag
DEFAULT_EWMA_LAMBDA      = 0.94     # RiskMetrics standard
DEFAULT_ROLLING_CORR     = 60       # days for rolling correlation
DEFAULT_ROLLING_PERF     = 252      # days for rolling Sharpe / beta
DEFAULT_FRONTIER_POINTS  = 50       # target return levels for efficient frontier
DEFAULT_GARCH_MIN_OBS    = 252      # minimum observations before GARCH vs EWMA
DEFAULT_COV_REGULARIZE   = 1e-6     # diagonal regularization if cond > 1e10
DEFAULT_COV_COND_THRESH  = 1e10     # condition number threshold for regularization

# ─── Benchmark Options ────────────────────────────────────────────────────────

BENCHMARK_OPTIONS = {
    "S&P 500 (SPY)":          "SPY",
    "Nasdaq 100 (QQQ)":       "QQQ",
    "Russell 2000 (IWM)":     "IWM",
    "US Agg Bond (AGG)":      "AGG",
    "60/40 Blend (SPY+AGG)":  "60_40",
}

# ─── Period Options ───────────────────────────────────────────────────────────

PERIOD_OPTIONS = {
    "1 Year":  "1y",
    "3 Years": "3y",
    "5 Years": "5y",
    "Custom":  "custom",
}

# ─── Tickers for Data Fetching ────────────────────────────────────────────────

RISK_FREE_TICKER = "^IRX"   # 13-week T-bill yield; divide by 100, then /252

# ─── Market Signal Tickers ────────────────────────────────────────────────────

SIGNAL_VIX      = "^VIX"       # CBOE 30-day implied volatility
SIGNAL_VIX3M    = "^VIX3M"     # 3-month VIX; fallback to VXMT
SIGNAL_VXMT     = "VXMT"       # mid-term VIX fallback
SIGNAL_MOVE     = "^MOVE"      # bond market implied volatility index
SIGNAL_TNX      = "^TNX"       # 10-year Treasury yield (annualized %)
SIGNAL_TYX      = "^TYX"       # 30-year Treasury yield (annualized %)
# NOTE: spec uses ^TNX - ^TYX for yield curve. Standard recession indicator
# uses 10yr - 2yr. ^TYX is 30yr, not 2yr. This is implemented per spec.
# A DECISIONS.md entry captures this discrepancy. Revisit in v2.
SIGNAL_HYG      = "HYG"        # iShares iBoxx HY Corporate Bond ETF
SIGNAL_IEF      = "IEF"        # iShares 7-10yr Treasury ETF
SIGNAL_GLD      = "GLD"        # SPDR Gold Shares (gold proxy)
SIGNAL_CPER     = "CPER"       # United States Copper Index Fund (copper proxy)
SIGNAL_USO      = "USO"        # United States Oil Fund (oil proxy)
SIGNAL_TLT      = "TLT"        # iShares 20+yr Treasury ETF (rate sensitivity)
SIGNAL_DXY      = "DX-Y.NYB"   # US Dollar Index

# ─── Stress Test Scenarios ────────────────────────────────────────────────────

STRESS_SCENARIOS = {
    "2000 Dot-Com Bust": {
        "index_return": -0.78,
        "description":  "Nasdaq fell ~78% over 2.5 years (2000–2002).",
    },
    "2008 Global Financial Crisis": {
        "index_return": -0.37,
        "description":  "SPY fell ~37% in 2008.",
    },
    "2020 COVID Crash": {
        "index_return": -0.34,
        "description":  "SPY fell ~34% peak-to-trough (Feb–Mar 2020).",
    },
    "2022 Rate Shock": {
        "index_return": -0.18,
        "description":  "SPY fell ~18%, AGG fell ~13% in 2022.",
    },
}

# ─── Disclaimer Text ──────────────────────────────────────────────────────────

DISCLAIMER_SHORT = (
    "For educational purposes only. Not financial advice. "
    "Past performance does not guarantee future results."
)

DISCLAIMER_FULL = (
    "For educational purposes only. Not financial advice. "
    "All analysis is based on historical data. "
    "Past performance does not guarantee future results. "
    "All models assume historical statistical properties persist — "
    "this may not hold in future market conditions."
)
