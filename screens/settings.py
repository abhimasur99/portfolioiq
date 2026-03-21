"""screens/settings.py

Screen 5 — Settings.

Responsibilities:
- Benchmark selection (BENCHMARK_OPTIONS).
- VaR confidence level (slider).
- VaR method (historical | garch).
- GARCH refit frequency.
- Optimization weight bounds (min/max sliders).
- Monte Carlo horizon (1, 2, 3, 5 years).
- Monte Carlo paths (1,000 or 10,000).
- Save and Recompute button: triggers granular recomputation of only the
  analytics affected by the changed setting.
  - Benchmark change → informs user that a price re-fetch is required
    and prompts them to return to Input.
  - VaR confidence / method / GARCH refit → recompute risk_outlook only.
  - Weight bounds change → recompute optimization only.
  - MC horizon / paths change → recompute risk_outlook (MC paths) only.

Writes all changed settings to st.session_state using SK_ constants.
Does NOT use raw string literals for session state keys.

Implemented in: Session 15.
"""

import streamlit as st

from assets.config import (
    BENCHMARK_OPTIONS,
    DEFAULT_BENCHMARK,
    DEFAULT_MC_HORIZON,
    DEFAULT_MC_PATHS,
    DEFAULT_VAR_CONFIDENCE,
    DEFAULT_VAR_METHOD,
    DEFAULT_WEIGHT_MAX,
    DEFAULT_WEIGHT_MIN,
    SK_ANALYTICS,
    SK_BENCH_RETURNS,
    SK_BENCHMARK,
    SK_GARCH_REFIT,
    SK_MC_HORIZON,
    SK_MC_PATHS,
    SK_OPTIMIZATION,
    SK_PERFORMANCE,
    SK_PORTFOLIO_LOADED,
    SK_PORT_RETURNS,
    SK_RETURNS_DF,
    SK_RISK_FREE_RATE,
    SK_RISK_OUTLOOK,
    SK_VAR_CONFIDENCE,
    SK_VAR_METHOD,
    SK_WEIGHT_MAX,
    SK_WEIGHT_MIN,
    SK_WEIGHTS,
    SK_COMPACT_MODE,
)

# ── Helpers ─────────────────────────────────────────────────────────────────────

def _snapshot() -> dict:
    """Capture the current values of all configurable settings."""
    return {
        SK_BENCHMARK:      st.session_state.get(SK_BENCHMARK,      DEFAULT_BENCHMARK),
        SK_VAR_CONFIDENCE: st.session_state.get(SK_VAR_CONFIDENCE, DEFAULT_VAR_CONFIDENCE),
        SK_VAR_METHOD:     st.session_state.get(SK_VAR_METHOD,     DEFAULT_VAR_METHOD),
        SK_GARCH_REFIT:    st.session_state.get(SK_GARCH_REFIT,    "each_load"),
        SK_MC_HORIZON:     st.session_state.get(SK_MC_HORIZON,     DEFAULT_MC_HORIZON),
        SK_MC_PATHS:       st.session_state.get(SK_MC_PATHS,       DEFAULT_MC_PATHS),
        SK_WEIGHT_MIN:     st.session_state.get(SK_WEIGHT_MIN,     DEFAULT_WEIGHT_MIN),
        SK_WEIGHT_MAX:     st.session_state.get(SK_WEIGHT_MAX,     DEFAULT_WEIGHT_MAX),
    }


def _restore_defaults() -> None:
    """Reset all settings to their default values."""
    st.session_state[SK_BENCHMARK]      = DEFAULT_BENCHMARK
    st.session_state[SK_VAR_CONFIDENCE] = DEFAULT_VAR_CONFIDENCE
    st.session_state[SK_VAR_METHOD]     = DEFAULT_VAR_METHOD
    st.session_state[SK_GARCH_REFIT]    = "each_load"
    st.session_state[SK_MC_HORIZON]     = DEFAULT_MC_HORIZON
    st.session_state[SK_MC_PATHS]       = DEFAULT_MC_PATHS
    st.session_state[SK_WEIGHT_MIN]     = DEFAULT_WEIGHT_MIN
    st.session_state[SK_WEIGHT_MAX]     = DEFAULT_WEIGHT_MAX


# ── Granular recompute ──────────────────────────────────────────────────────────

def _recompute_risk_outlook() -> bool:
    """Recompute only risk_outlook (VaR, GARCH, MC). Updates analytics dict in place."""
    from analytics.risk_outlook import compute_all_risk_outlook

    port_ret   = st.session_state.get(SK_PORT_RETURNS)
    bench_ret  = st.session_state.get(SK_BENCH_RETURNS)
    weights    = st.session_state.get(SK_WEIGHTS)
    perf       = st.session_state.get(SK_ANALYTICS, {}).get(SK_PERFORMANCE, {})
    rf         = st.session_state.get(SK_RISK_FREE_RATE, 0.0)

    if port_ret is None or bench_ret is None or weights is None:
        return False

    settings = {
        "var_confidence": st.session_state.get(SK_VAR_CONFIDENCE, DEFAULT_VAR_CONFIDENCE),
        "mc_horizon":     st.session_state.get(SK_MC_HORIZON,     DEFAULT_MC_HORIZON),
        "mc_paths":       st.session_state.get(SK_MC_PATHS,       DEFAULT_MC_PATHS),
    }

    try:
        new_ro = compute_all_risk_outlook(
            port_ret, bench_ret, weights, perf, settings
        )
        analytics = st.session_state.get(SK_ANALYTICS, {})
        analytics[SK_RISK_OUTLOOK] = new_ro
        st.session_state[SK_ANALYTICS] = analytics
        return True
    except Exception as exc:
        st.error(f"Risk outlook recompute failed: {exc}")
        return False


def _recompute_optimization() -> bool:
    """Recompute only optimization layer. Updates analytics dict in place."""
    from analytics.optimization import compute_all_optimization

    returns_df = st.session_state.get(SK_RETURNS_DF)
    weights    = st.session_state.get(SK_WEIGHTS)
    rf         = st.session_state.get(SK_RISK_FREE_RATE, 0.0)
    weight_min = st.session_state.get(SK_WEIGHT_MIN, DEFAULT_WEIGHT_MIN)
    weight_max = st.session_state.get(SK_WEIGHT_MAX, DEFAULT_WEIGHT_MAX)

    if returns_df is None or weights is None:
        return False

    # Align returns to current weights
    available = [t for t in weights.index if t in returns_df.columns]
    if len(available) < 2:
        return False

    try:
        new_opt = compute_all_optimization(
            returns_df[available], weights.reindex(available).dropna(),
            rf, weight_min, weight_max
        )
        analytics = st.session_state.get(SK_ANALYTICS, {})
        analytics[SK_OPTIMIZATION] = new_opt
        st.session_state[SK_ANALYTICS] = analytics
        return True
    except Exception as exc:
        st.error(f"Optimization recompute failed: {exc}")
        return False


# ── Page render ─────────────────────────────────────────────────────────────────

def render() -> None:
    """Render the Settings screen."""
    st.title("Settings")
    st.caption(
        "Changes take effect when you click **Save and Recompute**. "
        "Settings that require a price re-fetch will prompt you to return to Input."
    )

    portfolio_loaded = st.session_state.get(SK_PORTFOLIO_LOADED, False)
    before = _snapshot()

    # ── Current state summary (if portfolio loaded) ────────────────────────────
    if portfolio_loaded:
        with st.expander("Current portfolio settings", expanded=False):
            bench_label = next(
                (k for k, v in BENCHMARK_OPTIONS.items()
                 if v == before[SK_BENCHMARK]), before[SK_BENCHMARK]
            )
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Benchmark", bench_label)
            col2.metric("VaR Conf.", f"{before[SK_VAR_CONFIDENCE]*100:.0f}%")
            col3.metric("MC Horizon", f"{before[SK_MC_HORIZON]}y")
            col4.metric("Paths", f"{before[SK_MC_PATHS]:,}")

    st.markdown("---")

    # ── Section 1: Portfolio ───────────────────────────────────────────────────
    st.markdown("#### Portfolio")
    st.caption(
        "Changing benchmark requires re-analysing your portfolio. "
        "After saving, return to **Input** and click **Analyse Portfolio →**."
    )

    bench_keys = list(BENCHMARK_OPTIONS.keys())
    bench_vals = list(BENCHMARK_OPTIONS.values())
    current_bench = st.session_state.get(SK_BENCHMARK, DEFAULT_BENCHMARK)
    bench_idx = bench_vals.index(current_bench) if current_bench in bench_vals else 0
    new_bench_label = st.selectbox(
        "Benchmark",
        options=bench_keys,
        index=bench_idx,
        help="The benchmark used for alpha, beta, Sharpe, and Information Ratio calculations.",
    )
    new_benchmark = BENCHMARK_OPTIONS[new_bench_label]

    st.markdown("---")

    # ── Section 2: Risk ────────────────────────────────────────────────────────
    st.markdown("#### Risk")
    st.caption("Changes here trigger a risk outlook recomputation only (GARCH, VaR, CVaR).")

    col_v, col_m = st.columns(2)
    with col_v:
        new_var_confidence = st.slider(
            "VaR confidence level",
            min_value=0.90,
            max_value=0.99,
            value=float(st.session_state.get(SK_VAR_CONFIDENCE, DEFAULT_VAR_CONFIDENCE)),
            step=0.01,
            format="%.2f",
            help="Percentile used for Value at Risk. 0.95 = worst 5% of days threshold.",
        )

    with col_m:
        var_method_options = ["historical", "garch"]
        current_var_method = st.session_state.get(SK_VAR_METHOD, DEFAULT_VAR_METHOD)
        var_method_idx = var_method_options.index(current_var_method) if current_var_method in var_method_options else 0
        new_var_method = st.selectbox(
            "VaR method",
            options=var_method_options,
            index=var_method_idx,
            help=(
                "Historical: 5th-percentile of realized returns — stable, backward-looking, "
                "captures actual fat tails and skew. "
                "GARCH: −1.645 × GARCH-implied daily vol — more reactive to current market "
                "conditions; assumes normal distribution and may diverge from historical in "
                "volatile periods. CVaR always uses the historical method regardless of this setting."
            ),
        )

    garch_refit_options = ["each_load", "daily"]
    garch_refit_labels  = {"each_load": "Each portfolio load", "daily": "Daily (on app open)"}
    current_garch_refit = st.session_state.get(SK_GARCH_REFIT, "each_load")
    garch_refit_idx     = garch_refit_options.index(current_garch_refit) if current_garch_refit in garch_refit_options else 0
    new_garch_refit = st.selectbox(
        "GARCH refit frequency",
        options=garch_refit_options,
        format_func=lambda x: garch_refit_labels[x],
        index=garch_refit_idx,
        help="How often the GARCH(1,1) model is re-fitted. 'Each load' is recommended.",
    )

    st.markdown("---")

    # ── Section 3: Monte Carlo ─────────────────────────────────────────────────
    st.markdown("#### Monte Carlo")
    st.caption("Changes here trigger a Monte Carlo recomputation within the risk outlook.")

    col_h, col_np = st.columns(2)
    with col_h:
        mc_horizon_options = [1, 2, 3, 5]
        current_mc_horizon = st.session_state.get(SK_MC_HORIZON, DEFAULT_MC_HORIZON)
        mc_horizon_idx = mc_horizon_options.index(current_mc_horizon) if current_mc_horizon in mc_horizon_options else 0
        new_mc_horizon = st.selectbox(
            "Simulation horizon (years)",
            options=mc_horizon_options,
            index=mc_horizon_idx,
            format_func=lambda x: f"{x} years",
            help="How far into the future the Monte Carlo paths are projected.",
        )

    with col_np:
        mc_paths_options = [1_000, 10_000]
        current_mc_paths = st.session_state.get(SK_MC_PATHS, DEFAULT_MC_PATHS)
        mc_paths_idx = mc_paths_options.index(current_mc_paths) if current_mc_paths in mc_paths_options else 0
        new_mc_paths = st.selectbox(
            "Number of paths",
            options=mc_paths_options,
            index=mc_paths_idx,
            format_func=lambda x: f"{x:,}",
            help="More paths = smoother percentile bands but slower computation (~10s for 10,000).",
        )

    st.markdown("---")

    # ── Section 4: Weight Bounds ───────────────────────────────────────────────
    st.markdown("#### Optimization Weight Bounds")
    st.caption(
        "These bounds are applied to all three optimizers (Max Sharpe, Min Variance, Risk Parity). "
        "Changes trigger an optimization recomputation only."
    )

    col_wl, col_wh = st.columns(2)
    with col_wl:
        new_weight_min_pct = st.slider(
            "Minimum position weight",
            min_value=0,
            max_value=30,
            value=int(round(float(st.session_state.get(SK_WEIGHT_MIN, DEFAULT_WEIGHT_MIN)) * 100)),
            step=1,
            format="%d%%",
            help="No position can fall below this weight in any optimizer output.",
        )
    new_weight_min = new_weight_min_pct / 100

    with col_wh:
        new_weight_max_pct = st.slider(
            "Maximum position weight",
            min_value=20,
            max_value=100,
            value=int(round(float(st.session_state.get(SK_WEIGHT_MAX, DEFAULT_WEIGHT_MAX)) * 100)),
            step=5,
            format="%d%%",
            help="No position can exceed this weight in any optimizer output.",
        )
    new_weight_max = new_weight_max_pct / 100

    if new_weight_min >= new_weight_max:
        st.warning("Minimum weight must be less than maximum weight.")

    st.markdown("---")

    # ── Section 5: Display ─────────────────────────────────────────────────────
    st.subheader("Display")
    new_compact = st.checkbox(
        "Compact layout",
        value=st.session_state.get(SK_COMPACT_MODE, False),
        help=(
            "Reduces dashboard chart heights (260px → 180px). "
            "Useful on smaller laptop screens (~900–1100px). "
            "Takes effect immediately on save."
        ),
    )

    st.markdown("---")

    # ── Action buttons ─────────────────────────────────────────────────────────
    btn_save, btn_reset = st.columns([3, 1])

    with btn_reset:
        if st.button("Restore Defaults", use_container_width=True):
            _restore_defaults()
            st.success("Settings restored to defaults.")
            st.rerun()

    with btn_save:
        save_disabled = new_weight_min >= new_weight_max
        if st.button(
            "Save and Recompute →",
            type="primary",
            use_container_width=True,
            disabled=save_disabled,
        ):
            # Collect new values
            new_settings = {
                SK_BENCHMARK:      new_benchmark,
                SK_VAR_CONFIDENCE: new_var_confidence,
                SK_VAR_METHOD:     new_var_method,
                SK_GARCH_REFIT:    new_garch_refit,
                SK_MC_HORIZON:     new_mc_horizon,
                SK_MC_PATHS:       new_mc_paths,
                SK_WEIGHT_MIN:     new_weight_min,
                SK_WEIGHT_MAX:     new_weight_max,
            }

            # Detect what changed
            portfolio_changed = (
                new_settings[SK_BENCHMARK] != before[SK_BENCHMARK]
            )
            risk_outlook_changed = (
                new_settings[SK_VAR_CONFIDENCE] != before[SK_VAR_CONFIDENCE]
                or new_settings[SK_VAR_METHOD]    != before[SK_VAR_METHOD]
                or new_settings[SK_GARCH_REFIT]   != before[SK_GARCH_REFIT]
                or new_settings[SK_MC_HORIZON]     != before[SK_MC_HORIZON]
                or new_settings[SK_MC_PATHS]       != before[SK_MC_PATHS]
            )
            optimization_changed = (
                new_settings[SK_WEIGHT_MIN] != before[SK_WEIGHT_MIN]
                or new_settings[SK_WEIGHT_MAX] != before[SK_WEIGHT_MAX]
            )

            # Always save all settings
            for key, val in new_settings.items():
                st.session_state[key] = val
            st.session_state[SK_COMPACT_MODE] = new_compact

            # Granular recompute
            if not portfolio_loaded:
                st.info("No portfolio loaded — settings saved. Load a portfolio from Input to apply them.")

            elif portfolio_changed:
                st.info(
                    "**Benchmark changed.** This setting requires a full data re-fetch to take "
                    "effect. Please go to **Input**, confirm your holdings, and click "
                    "**Analyse Portfolio →** to apply the new benchmark."
                )

            else:
                recomputed = []
                with st.spinner("Recomputing…"):
                    if risk_outlook_changed:
                        if _recompute_risk_outlook():
                            recomputed.append("risk outlook (VaR, GARCH, Monte Carlo)")
                    if optimization_changed:
                        if _recompute_optimization():
                            recomputed.append("optimization (frontier, Max Sharpe, Min Var, Risk Parity)")

                if recomputed:
                    st.success(
                        "Settings saved. Recomputed: " + " and ".join(recomputed) + ". "
                        "Dashboard will reflect updated numbers."
                    )
                else:
                    st.success("Settings saved. No analytics required recomputation.")
