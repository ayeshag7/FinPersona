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


# ======================================================================================================================
# v2.1 Phase 8 (E8.3; PREREG_PHASE_8.md 3; weakness 59, 67).  NEW functions beside the v2 ones above, which are unchanged
# (the golden record, tests/phase8_golden.json).  Every one was validated on simulated data with a known answer before
# it touches a real contrast (tools/phase8/e8_3_simulate.py; docs/env_v2/generated/v2_1/e8_3/):
#   * the v2 `mixed_effects` (seeds nested in models, random intercepts only) rejects a TRUE null in 36-58 % of
#     simulated datasets once the arm effect varies by model;
#   * `crossed_mixed_model` (E1) and `pigeonhole_ci` (E2) hold size at 6 models and do NOT at 3 (0.08-0.12) --
#     their simulated size travels with every use;
#   * BH across the metrics of one contrast (v2) gives an FDR of 0.43-0.996; BH within a question family holds on a
#     one-family grid and not on a multi-family one; BY across families holds everywhere (addendum 5).
# ======================================================================================================================
TIER_C = ("band_mas", "v21_mcr_D_0.05", "v21_mcr_D_0.002")          # confirmatory (PREREG 3.4)
TIER_S = ("turnover", "mdd_pct", "return_pct")                      # secondary, their own families
NO_PERSONA = ("NONE", "TRADER", "O3_conservative", "O3_aggressive")


def question_families() -> Dict[str, List[tuple]]:
    """PREREG 3.4: each question's contrasts, (arm, reference), within persona x scenario cell."""
    from experiments.arms_v2 import CONTEXT_LEVELS
    q5 = []
    for level, (st, mem) in CONTEXT_LEVELS.items():
        q5 += [(mem, st), (mem, "memory")]
    return {"Q1": [("memory", "static"), ("path_b_memory", "path_b_static")],
            "Q2": [("memory", "placebo_directive"), ("swapped", "memory")],
            "Q3": [("placebo_directive", "static"), ("placebo_declarative", "static"), ("wrapper_only", "static")],
            "Q4": [("path_b_static", "static")],
            "Q5": q5}


def scenario_cell(df: pd.DataFrame) -> pd.Series:
    """A scenario cell: the scenario, with the crash discount when the scenario is crash."""
    sc = df["Scenario"].astype(str)
    if "Crash_Discount" in df.columns:
        return np.where(sc == "crash", sc + "_d" + df["Crash_Discount"].astype(str), sc)
    return sc


def seed_level_pairs(per_run: pd.DataFrame, metric: str, arm: str, reference: str) -> pd.DataFrame:
    """PREREG 3.1: the pair is (model, persona, path); replicates are averaged per arm BEFORE the difference, never
    paired by index.  Returns Model, Persona, Scenario_Cell, Seed, Path and d = mean(arm) - mean(reference)."""
    d = per_run[per_run["Arm"].isin([arm, reference])].dropna(subset=[metric]).copy()
    if d.empty:
        return pd.DataFrame(columns=["Model", "Persona", "Scenario_Cell", "Seed", "Path", "d"])
    d["Scenario_Cell"] = scenario_cell(d)
    m = d.groupby(["Model", "Persona", "Scenario_Cell", "Seed", "Arm"])[metric].mean().unstack("Arm")
    if arm not in m.columns or reference not in m.columns:
        return pd.DataFrame(columns=["Model", "Persona", "Scenario_Cell", "Seed", "Path", "d"])
    out = (m[arm] - m[reference]).dropna().rename("d").reset_index()
    out["Path"] = out["Scenario_Cell"].astype(str) + "|" + out["Seed"].astype(str)
    return out


def pigeonhole_ci(pairs: pd.DataFrame, n_boot: int = 1999, seed: int = 0, alpha: float = 0.05, rng=None) -> Dict[str, float]:
    """PREREG 3.3 (E2): two-way cluster bootstrap by model and path.  Each resample draws the models and, independently,
    the paths with replacement; every pair is weighted by (its model's draw count x its path's draw count); the
    statistic is the weighted mean difference; the interval is percentile.  With one model the model dimension is
    degenerate and the bootstrap is one-way by path (`one_way`).  The two-sided p is read from the same draws."""
    rng = rng if rng is not None else np.random.default_rng(seed)
    if pairs.empty:
        return {"n_models": 0, "n_paths": 0}
    tab = pairs.pivot_table(index="Model", columns="Path", values="d", aggfunc="mean")
    D = tab.to_numpy(float)
    mask = np.isfinite(D).astype(float)
    D0 = np.where(mask > 0, D, 0.0)
    M, S = D.shape
    wm = rng.multinomial(M, np.full(M, 1.0 / M), size=n_boot).astype(float)
    ws = rng.multinomial(S, np.full(S, 1.0 / S), size=n_boot).astype(float)
    num = np.einsum("bm,ms,bs->b", wm, D0, ws)
    den = np.einsum("bm,ms,bs->b", wm, mask, ws)
    stat = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)
    stat = stat[np.isfinite(stat)]
    est = float(D0.sum() / mask.sum())
    lo, hi = np.percentile(stat, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    p = float(min(1.0, 2 * min((stat <= 0).mean(), (stat >= 0).mean()) + 1.0 / (len(stat) + 1)))
    return {"estimate": est, "ci_lo": float(lo), "ci_hi": float(hi), "p_boot": p, "n_models": int(M), "n_paths": int(S),
            "n_pairs": int(mask.sum()), "one_way": bool(M == 1), "n_boot": int(len(stat))}


def path_sign_flip(pairs: pd.DataFrame, n_perm: int = 9999, seed: int = 0, exact_max: int = 16) -> Dict[str, float]:
    """PREREG 3.6 (N3): the sign of every pair in a path is flipped together (paths are the exchangeable units);
    exact over all 2^n sign vectors when n <= `exact_max`.  The smallest attainable two-sided p is 2 / 2^n, so a path
    count below the minimum cannot reject at all -- returned, never hidden."""
    if pairs.empty:
        return {"n_paths": 0}
    s = pairs.groupby("Path")["d"].agg(["sum", "size"])
    tot, n_units = s["sum"].to_numpy(float), float(s["size"].sum())
    n = len(tot)
    obs = tot.sum() / n_units
    if n <= exact_max:
        signs = ((np.arange(2 ** n)[:, None] >> np.arange(n)[None, :]) & 1) * 2.0 - 1.0
        null = signs @ tot / n_units
        p = float(np.mean(np.abs(null) >= abs(obs) - 1e-15))
        exact = True
    else:
        rng = np.random.default_rng(seed)
        null = rng.choice([-1.0, 1.0], size=(n_perm, n)) @ tot / n_units
        p = float((np.sum(np.abs(null) >= abs(obs)) + 1) / (n_perm + 1))
        exact = False
    return {"n_paths": int(n), "mean_d": float(obs), "p_signflip": p, "exact": exact,
            "min_attainable_p": float(2.0 / 2 ** n) if exact else float(1.0 / (n_perm + 1))}


def _reml_fit(model, optimizer: str):
    """REML by lbfgs (the estimator P8-9 validated), or `optimizer="best"`: lbfgs and Powell, the higher restricted
    likelihood kept.  lbfgs stops at a local optimum in 15-20 % of E1's fits, and in 34-61 % at a zero-variance boundary
    (PREREG_PHASE_8_ADDENDUM.md 17); "best" equals `tools/phase8/e8_3_simulate.fit_e1_best`."""
    if optimizer == "lbfgs":
        return model.fit(reml=True, method="lbfgs", maxiter=400)
    best = None
    for m in ("lbfgs", "powell"):
        try:
            r = model.fit(reml=True, method=m, maxiter=400 if m == "lbfgs" else 1600)
        except Exception:                                        # noqa: BLE001 -- the other method may still fit
            continue
        if best is None or (np.isfinite(r.llf) and r.llf > best.llf):
            best = r
    if best is None:
        raise RuntimeError("no REML fit returned")
    return best


def crossed_mixed_model(per_run: pd.DataFrame, metric: str, reference: str = "static", arms=None,
                        optimizer: str = "lbfgs") -> Dict[str, object]:
    """PREREG 3.2 (E1): y ~ C(Arm, Treatment(ref)) * C(Persona) * C(Scenario) with CROSSED variance components --
    model, model x arm (the random slope for arm by model, interaction-variance parameterisation), path, and path x arm
    where replicates exist -- via one group and `vc_formula`.  statsmodels estimates no intercept-slope correlation;
    the simulation planted one (rho = 0.5) and measured its effect on size.  Returns the fixed-effect table, the
    variance components, the residual, the components at the zero boundary, the convergence flag, the optimizer and
    the REML log-likelihood.  `optimizer="best"` fits at the better of the lbfgs and Powell optima (P8-17); the
    crossed model is DESCRIPTIVE on the main grid -- addendum 17's rule did not adopt E1-amended, and at six models
    with a model x arm sd of 0.03 neither E1 nor E2 holds size at the sized design."""
    if optimizer not in ("lbfgs", "best"):
        raise ValueError(f"optimizer must be 'lbfgs' or 'best', got {optimizer!r}")
    import statsmodels.formula.api as smf
    d = per_run.dropna(subset=[metric]).copy()
    if arms is not None:
        d = d[d["Arm"].isin(list(arms) + [reference])]
    d["y"] = d[metric].astype(float)
    d["Scenario"] = scenario_cell(d)
    d["Path"] = d["Scenario"].astype(str) + "|" + d["Seed"].astype(str)
    vc = {}                                     # the order the simulation validated (model, model_arm, path, path_arm)
    if d["Model"].nunique() > 1:
        vc.update({"model": "0 + C(Model)", "model_arm": "0 + C(Model):C(Arm)"})
    vc["path"] = "0 + C(Path)"
    if "Decode_Replicate" in d.columns and d["Decode_Replicate"].nunique() > 1:
        vc["path_arm"] = "0 + C(Path):C(Arm)"
    form = f"y ~ C(Arm, Treatment('{reference}'))" + (" * C(Persona)" if d["Persona"].nunique() > 1 else "") + \
           (" * C(Scenario)" if d["Scenario"].nunique() > 1 else "")
    try:
        r = _reml_fit(smf.mixedlm(form, d, groups=np.ones(len(d)), re_formula="0", vc_formula=vc), optimizer)
        comps = dict(zip(r.model.exog_vc.names, (float(v) for v in np.asarray(r.vcomp, float))))
        fixed = pd.DataFrame({"term": r.params.index, "coef": r.params.values, "se": r.bse.reindex(r.params.index).values,
                              "p": r.pvalues.reindex(r.params.index).values})
        fixed = fixed[~fixed["term"].isin(["Group Var"]) & ~fixed["term"].str.endswith(" Var")]
        return {"metric": metric, "formula": form, "vc_formula": vc, "fixed": fixed, "variance_components": comps,
                "residual": float(r.scale), "at_boundary": sorted(k for k, v in comps.items() if v < 1e-8),
                "converged": bool(r.converged), "n": int(len(d)), "optimizer": optimizer, "reml_llf": float(r.llf)}
    except Exception as exc:                                     # noqa: BLE001 -- reported, never replaced
        return {"metric": metric, "formula": form, "vc_formula": vc, "error": f"{type(exc).__name__}: {str(exc)[:160]}",
                "n": int(len(d)), "optimizer": optimizer}


def by_adjust(p: np.ndarray) -> np.ndarray:
    """Benjamini-Yekutieli q-values: BH on p x sum_{i<=m} 1/i."""
    p = np.asarray(p, float)
    if len(p) == 0:
        return p
    c = float(np.sum(1.0 / np.arange(1, len(p) + 1)))
    return bh_adjust(np.minimum(p * c, 1.0))


def v2_family_count(n_nonreference_arms: int, n_personas: int, n_scenario_cells: int, n_metrics: int = len(METRICS)) -> int:
    """The v2 construction's test count (`arm_contrasts` x METRICS): the number weakness 59 calls "roughly 840"."""
    return int(n_nonreference_arms * n_personas * n_scenario_cells * n_metrics)


def family_table(tests: pd.DataFrame) -> pd.DataFrame:
    """The size of every family, COUNTED from the tests actually computed (a family's m is its number of p-values)."""
    if tests.empty:
        return pd.DataFrame(columns=["family", "question", "tier", "m"])
    t = tests.groupby(["family", "question", "tier"]).size().rename("m").reset_index()
    return t


def run_stats_v21(per_run: pd.DataFrame, out_prefix: str, n_boot: int = 1999, seed: int = 0) -> Dict[str, pd.DataFrame]:
    """The v2.1 statistics track: every registered contrast present in the table, per persona x scenario cell x metric,
    with its two-way cluster-bootstrap interval and p, Cliff's delta beside, BH within its question family, BY across
    all confirmatory (tier C) families and separately across the secondary ones, and the decision rule the parameter
    file names for this grid's number of confirmatory families.  THE FAMILY SIZE IS WRITTEN BESIDE EVERY q-VALUE
    (`test_bh_family_size_logged`)."""
    rows = []
    personas = [p for p in sorted(per_run["Persona"].astype(str).unique()) if p not in NO_PERSONA]
    tiers = {"C": [m for m in TIER_C if m in per_run.columns], "S": [m for m in TIER_S if m in per_run.columns]}
    for q, pairs in question_families().items():
        for arm, ref in pairs:
            if arm not in set(per_run["Arm"]) or ref not in set(per_run["Arm"]):
                continue
            for tier, mets in tiers.items():
                for metric in mets:
                    allp = seed_level_pairs(per_run, metric, arm, ref)
                    for (persona, cell), g in allp.groupby(["Persona", "Scenario_Cell"]):
                        if persona in NO_PERSONA or g["Path"].nunique() < 2:
                            continue
                        b = pigeonhole_ci(g, n_boot=n_boot, seed=seed)
                        sub = per_run[(per_run["Persona"] == persona) & (scenario_cell(per_run) == cell)]
                        a_v = sub[sub["Arm"] == arm][metric].dropna().to_numpy(); r_v = sub[sub["Arm"] == ref][metric].dropna().to_numpy()
                        rows.append({"family": f"{q}|{tier}", "question": q, "tier": tier, "contrast": f"{arm} - {ref}",
                                     "Persona": persona, "Scenario_Cell": cell, "metric": metric, **b,
                                     "cliffs_delta": cliffs_delta(a_v, r_v)})
    tests = pd.DataFrame(rows)
    fam = family_table(tests)
    if len(tests):
        tests = tests.merge(fam[["family", "m"]].rename(columns={"m": "m_family"}), on="family")
        tests["q_bh_within_family"] = np.nan
        for f, idx in tests.groupby("family").groups.items():
            tests.loc[idx, "q_bh_within_family"] = bh_adjust(tests.loc[idx, "p_boot"].to_numpy())
        tests["q_by_across_families"] = np.nan
        for tier in ("C", "S"):
            idx = tests.index[tests["tier"] == tier]
            tests.loc[idx, "q_by_across_families"] = by_adjust(tests.loc[idx, "p_boot"].to_numpy())
            tests.loc[idx, "m_across_families"] = len(idx)
        n_conf = int(fam[fam["tier"] == "C"]["family"].nunique())
        rule = "no rule: experiments/params/inference.json absent"
        try:
            from experiments import inference_params as IP
            if IP.PRESENT:
                rule = IP.decision_rule(max(n_conf, 1))
        except Exception as exc:                                  # noqa: BLE001
            rule = f"no rule: {type(exc).__name__}"
        tests["n_confirmatory_families"] = n_conf
        tests["decision_rule"] = rule
        qcol = {"bh_within": "q_bh_within_family", "by_across": "q_by_across_families"}.get(rule)
        tests["claim"] = (tests[qcol] <= 0.05) & (tests["tier"] == "C") if qcol else False
    models = {}
    for metric in tiers["C"]:
        models[metric] = crossed_mixed_model(per_run, metric, optimizer="best")     # descriptive, at the better optimum (P8-17)
    os.makedirs(os.path.dirname(out_prefix) or ".", exist_ok=True)
    tests.to_csv(out_prefix + "_v21_contrasts.csv", index=False)
    fam.to_csv(out_prefix + "_v21_families.csv", index=False)
    vc_rows = [{"metric": m, **{f"vc_{k}": v for k, v in r.get("variance_components", {}).items()},
                "residual": r.get("residual"), "converged": r.get("converged"), "at_boundary": ",".join(r.get("at_boundary", [])),
                "optimizer": r.get("optimizer"), "reml_llf": r.get("reml_llf"), "role": "descriptive (P8-17)",
                "error": r.get("error", "")} for m, r in models.items()]
    pd.DataFrame(vc_rows).to_csv(out_prefix + "_v21_variance_components.csv", index=False)
    return {"contrasts": tests, "families": fam, "models": models}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--per_run", default=os.path.join(ROOT, "docs", "env_v2", "generated", "report_v2_per_run.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "env_v2", "generated", "stats_v2"))
    a = ap.parse_args()
    per_run = pd.read_csv(a.per_run)
    t = run_stats(per_run, a.out)
    print({k: len(v) for k, v in t.items()}, "written", a.out + ".md")
