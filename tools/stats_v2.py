"""
Statistics track (plan Section 11.2) for v2 results: model-level inference.

Inputs: the per-run table written by tools/report_v2.py (report_v2_per_run.csv).
For every metric in METRICS and every (persona, scenario) cell:
  * arm contrasts vs the 'static' arm within persona: paired by (model, seed, replicate) where possible;
    Cliff's delta and Hedges g with bootstrap 95% CIs; sign counts at MODEL level
    (how many of the N models move in the contrast's direction) -- effective N is models;
  * mixed-effects model metric ~ C(arm) * C(persona) with random intercepts for model
    (and seed as a variance component) via statsmodels MixedLM; Wald p-values per
    arm coefficient;
  * Benjamini-Hochberg across the metric family within each contrast;
  * degeneracy audit next to every contrast: parse-fallback share, zero-trade share,
    fraction of runs whose RG normalisation is degenerate.
Usage: python -m tools.stats_v2 --per_run docs/env_v2/generated/report_v2_per_run.csv --out docs/env_v2/generated/stats_v2
"""
from __future__ import annotations

import argparse
import os
import sys
import warnings
from typing import Dict, List

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

METRICS = ["mcr_0.05", "band_mas", "point_mas_v2", "rg_theta_0.05", "return_pct", "mdd_pct", "turnover"]
KEYS = ["Model", "Seed", "Decode_Replicate", "Crash_Discount"]


def cliffs_delta(a, b) -> float:
    a = np.asarray(a, float); b = np.asarray(b, float)
    if len(a) == 0 or len(b) == 0:
        return np.nan
    return float((a[:, None] > b[None, :]).mean() - (a[:, None] < b[None, :]).mean())


def hedges_g(a, b) -> float:
    a = np.asarray(a, float); b = np.asarray(b, float)
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return np.nan
    sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    if sp == 0:
        return np.nan
    j = 1 - 3 / (4 * (na + nb) - 9)
    return float((a.mean() - b.mean()) / sp * j)


def bootstrap_ci(a, b, fn, n_boot=1000, seed=0):
    rng = np.random.default_rng(seed)
    a = np.asarray(a, float); b = np.asarray(b, float)
    vals = [fn(rng.choice(a, len(a)), rng.choice(b, len(b))) for _ in range(n_boot)]
    vals = [v for v in vals if not np.isnan(v)]
    if not vals:
        return (np.nan, np.nan)
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))


def bh_adjust(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, float)
    n = len(p)
    order = np.argsort(p)
    ranked = np.empty(n); ranked[order] = np.arange(1, n + 1)
    q = p * n / ranked
    # enforce monotonicity
    q_sorted = np.minimum.accumulate(q[order][::-1])[::-1]
    out = np.empty(n); out[order] = q_sorted
    return np.clip(out, 0, 1)


def arm_contrasts(per_run: pd.DataFrame, reference: str = "static", n_boot: int = 1000) -> pd.DataFrame:
    rows = []
    for (persona, scenario), d in per_run.groupby(["Persona", "Scenario"]):
        base = d[d["Arm"] == reference]
        if base.empty:
            continue
        for arm, da in d.groupby("Arm"):
            if arm == reference:
                continue
            merged = da.merge(base, on=[k for k in KEYS if k in d.columns], suffixes=("", "_ref"))
            for m in METRICS:
                if m not in d.columns:
                    continue
                a = da[m].dropna().to_numpy(); b = base[m].dropna().to_numpy()
                if len(a) < 2 or len(b) < 2:
                    continue
                lo, hi = bootstrap_ci(a, b, cliffs_delta, n_boot)
                # model-level sign count on paired differences
                sign = np.nan; n_models = 0
                if m in merged.columns and f"{m}_ref" in merged.columns and len(merged):
                    diff = (merged[m] - merged[f"{m}_ref"]).groupby(merged["Model"]).mean()
                    n_models = int(diff.notna().sum()); sign = int((diff < 0).sum()) if m in ("mcr_0.05", "band_mas", "point_mas_v2", "turnover", "mdd_pct") else int((diff > 0).sum())
                rows.append({"Persona": persona, "Scenario": scenario, "Arm": arm, "vs": reference, "metric": m,
                             "n_arm": len(a), "n_ref": len(b), "mean_arm": float(a.mean()), "mean_ref": float(b.mean()),
                             "cliffs_delta": cliffs_delta(a, b), "delta_ci_lo": lo, "delta_ci_hi": hi,
                             "hedges_g": hedges_g(a, b), "models_improving": sign, "n_models": n_models,
                             "fallback_share_arm": float(da["fallback_share"].mean()) if "fallback_share" in da else np.nan,
                             "zero_trade_share_arm": float(da["zero_trade"].mean()) if "zero_trade" in da else np.nan,
                             "degenerate_rg_share_arm": float(da["degenerate_rg_v1"].mean()) if "degenerate_rg_v1" in da else np.nan})
    return pd.DataFrame(rows)


def mixed_effects(per_run: pd.DataFrame, metric: str) -> pd.DataFrame:
    """metric ~ C(arm) * C(persona) + random intercept per model (+ seed variance component)."""
    import statsmodels.formula.api as smf
    d = per_run.dropna(subset=[metric]).copy()
    d["y"] = d[metric].astype(float)
    if d["Model"].nunique() < 2 or d["Arm"].nunique() < 2:
        return pd.DataFrame()
    try:
        ref = "static" if "static" in set(d["Arm"]) else sorted(d["Arm"].unique())[0]
        md = smf.mixedlm(f"y ~ C(Arm, Treatment(reference='{ref}')) * C(Persona)", d, groups=d["Model"],
                         re_formula="1", vc_formula={"seed": "0 + C(Seed)"} if d["Seed"].nunique() > 1 else None)
        r = md.fit(reml=True, method="lbfgs", maxiter=200)
        terms = [t.replace(f"C(Arm, Treatment(reference='{ref}'))", "Arm").replace("C(Persona)", "Persona") for t in r.params.index]
        out = pd.DataFrame({"term": terms, "coef": r.params.values, "se": r.bse.values, "p": r.pvalues.values})
        out["metric"] = metric
        return out
    except Exception as exc:
        return pd.DataFrame([{"term": "ERROR", "coef": np.nan, "se": np.nan, "p": np.nan, "metric": metric, "note": str(exc)[:120]}])


RUN_KEYS = ["Model", "Persona", "Arm", "Scenario", "Seed", "Decode_Replicate"]


def window_means(per_step: pd.DataFrame, metric: str, window: int = 25) -> pd.DataFrame:
    """Per-run x 25-day-window means (the unit for temporal claims; per-day series are near-unit-root)."""
    d = per_step.dropna(subset=[metric]).copy()
    d["w"] = (d["Day"] - 1) // window
    keys = [k for k in RUN_KEYS if k in d.columns]
    g = d.groupby(keys + ["w"], sort=False)
    out = g.agg(y=(metric, "mean"), day_c=("Day", "mean"), phase=("Phase", lambda s: s.mode().iloc[0] if len(s) else "calm"),
                ordering=("Ordering", "first") if "Ordering" in d.columns else ("Day", "size")).reset_index()
    out["day_c"] = out["day_c"] / 100.0
    out["run"] = out[keys].astype(str).agg("|".join, axis=1)
    return out


def phase_time_model(per_step: pd.DataFrame, metric: str = "band_mas_t", window: int = 25) -> pd.DataFrame:
    """Plan Section 6 (methods review): on WINDOW means, y ~ C(phase) + day_c + C(ordering) with a random
    intercept per RUN (and a random slope for phase by model when > 1 model via a variance component).
    Day and phase are only identified across schedule types, hence the ordering factor."""
    import statsmodels.formula.api as smf
    w = window_means(per_step, metric, window)
    if w["phase"].nunique() < 2 or len(w) < 20:
        return pd.DataFrame()
    form = "y ~ C(phase) + day_c" + (" + C(ordering)" if "ordering" in w.columns and w["ordering"].nunique() > 1 else "")
    try:
        vc = {"model_phase": "0 + C(Model):C(phase)"} if "Model" in w.columns and w["Model"].nunique() > 1 else None
        md = smf.mixedlm(form, w, groups=w["run"], re_formula="1", vc_formula=vc)
        r = md.fit(reml=True, method="lbfgs", maxiter=300)
        return pd.DataFrame({"term": r.params.index, "coef": r.params.values, "se": r.bse.values, "p": r.pvalues.values, "metric": metric})
    except Exception as exc:
        return pd.DataFrame([{"term": "ERROR", "coef": np.nan, "se": np.nan, "p": np.nan, "metric": metric, "note": str(exc)[:120]}])


def windowed_trend_vs_null(per_step: pd.DataFrame, metric: str = "band_mas_t", window: int = 25,
                           n_perm: int = 500, seed: int = 0, null: str = "circular") -> Dict[str, float]:
    """'Temporal claims use windowed statistics, not expanding minima.' Per run: mean metric per
    25-day window; trend = slope of window means on window index.  Null (methods review): a
    CIRCULAR SHIFT of the window sequence within each run (preserves autocorrelation and the
    within-run distribution; a constant-exposure run has zero slope under every shift) --
    appropriate for PHASE-FREE runs; for runs with phases use `paired_sign_flip` against the
    stateless arm on the same seeds instead. Returns the observed mean slope, the shift-null
    p-value and the expanding-minimum statistic (monotone by construction; shown for contrast)."""
    rng = np.random.default_rng(seed)
    d = per_step.dropna(subset=[metric]).copy()
    d["w"] = (d["Day"] - 1) // window
    keys = [k for k in RUN_KEYS if k in d.columns]
    runs = []
    for key, g in d.groupby(keys, sort=False):
        wm = g.groupby("w")[metric].mean().to_numpy(dtype=float)
        if len(wm) >= 3:
            runs.append(wm)
    if not runs:
        return {"n_runs": 0}
    def slope(wm):
        x = np.arange(len(wm)); return float(np.polyfit(x, wm, 1)[0])
    obs = float(np.mean([slope(w) for w in runs]))
    if null == "circular":
        null_s = np.array([np.mean([slope(np.roll(w, rng.integers(1, len(w)))) for w in runs]) for _ in range(n_perm)])
    else:
        null_s = np.array([np.mean([slope(rng.permutation(w)) for w in runs]) for _ in range(n_perm)])
    p = float((np.sum(np.abs(null_s) >= abs(obs)) + 1) / (n_perm + 1))
    expanding = float(np.mean([np.minimum.accumulate(w)[-1] - w[0] for w in runs]))
    return {"n_runs": len(runs), "mean_window_slope": obs, "null": null, "perm_p": p, "null_sd": float(null_s.std()),
            "expanding_min_change": expanding}


def paired_sign_flip(per_step: pd.DataFrame, metric: str = "band_mas_t", arm: str = "stateful_memory",
                     reference: str = "memory", window: int = 25, n_perm: int = 2000, seed: int = 0) -> Dict[str, float]:
    """Time-beyond-phase test: window-trend of `arm` minus window-trend of the stateless `reference`
    arm on the SAME (model, persona, scenario, seed) -- phases cancel in the pair; sign-flip
    permutation across pairs."""
    rng = np.random.default_rng(seed)
    d = per_step.dropna(subset=[metric]).copy(); d["w"] = (d["Day"] - 1) // window
    keys = [k for k in ("Model", "Persona", "Scenario", "Seed", "Decode_Replicate") if k in d.columns]
    def trend(g):
        wm = g.groupby("w")[metric].mean().to_numpy(dtype=float)
        return float(np.polyfit(np.arange(len(wm)), wm, 1)[0]) if len(wm) >= 3 else np.nan
    ta = d[d["Arm"] == arm].groupby(keys).apply(trend, include_groups=False)
    tr = d[d["Arm"] == reference].groupby(keys).apply(trend, include_groups=False)
    diff = (ta - tr).dropna().to_numpy(dtype=float)
    if len(diff) < 2:
        return {"n_pairs": int(len(diff))}
    obs = float(diff.mean())
    flips = np.array([np.mean(diff * rng.choice([-1, 1], len(diff))) for _ in range(n_perm)])
    return {"n_pairs": int(len(diff)), "mean_trend_diff": obs, "p_signflip": float((np.sum(np.abs(flips) >= abs(obs)) + 1) / (n_perm + 1))}


def run_stats(per_run: pd.DataFrame, out_prefix: str) -> Dict[str, pd.DataFrame]:
    con = arm_contrasts(per_run)
    if len(con):
        # BH across the metric family within each (persona, scenario, arm) contrast, on the bootstrap-CI-based
        # two-sided p approximation of Cliff's delta (normal approximation from the CI width)
        z = con["cliffs_delta"] / ((con["delta_ci_hi"] - con["delta_ci_lo"]) / (2 * 1.96)).replace(0, np.nan)
        from scipy import stats
        con["p_approx"] = 2 * (1 - stats.norm.cdf(np.abs(z.fillna(0))))
        con["q_bh"] = np.nan
        for key, idx in con.groupby(["Persona", "Scenario", "Arm"]).groups.items():
            con.loc[idx, "q_bh"] = bh_adjust(con.loc[idx, "p_approx"].to_numpy())
    me = pd.concat([mixed_effects(per_run, m) for m in METRICS if m in per_run.columns], ignore_index=True) if len(per_run) else pd.DataFrame()
    deg = per_run.groupby(["Model", "Arm"]).agg(n=("fallback_share", "size"), fallback=("fallback_share", "mean"),
                                                 zero_trade=("zero_trade", "mean"),
                                                 degenerate_rg=("degenerate_rg_v1", "mean") if "degenerate_rg_v1" in per_run else ("zero_trade", "size")).reset_index()
    os.makedirs(os.path.dirname(out_prefix) or ".", exist_ok=True)
    con.to_csv(out_prefix + "_contrasts.csv", index=False)
    me.to_csv(out_prefix + "_mixedlm.csv", index=False)
    deg.to_csv(out_prefix + "_degeneracy.csv", index=False)
    with open(out_prefix + ".md", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# Statistics track (v2)\n\nEffective N is models (sign counts and mixed-effects random intercepts by model); "
                 "Cliff's delta / Hedges g with bootstrap 95% CIs; BH-adjusted q across the metric family per contrast; "
                 "degeneracy audit beside every contrast.\n\n## Arm contrasts vs static\n\n" +
                 (con.round(3).to_string(index=False) if len(con) else "(none)") +
                 "\n\n## Mixed-effects (metric ~ arm x persona, random intercept by model)\n\n" +
                 (me.round(4).to_string(index=False) if len(me) else "(none)") +
                 "\n\n## Degeneracy audit\n\n" + deg.round(3).to_string(index=False) + "\n")
    return {"contrasts": con, "mixedlm": me, "degeneracy": deg}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--per_run", default=os.path.join(ROOT, "docs", "env_v2", "generated", "report_v2_per_run.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "env_v2", "generated", "stats_v2"))
    a = ap.parse_args()
    per_run = pd.read_csv(a.per_run)
    t = run_stats(per_run, a.out)
    print({k: len(v) for k, v in t.items()}, "written", a.out + ".md")
