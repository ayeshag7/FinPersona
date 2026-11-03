"""E5's registered read: the robustness table (`PREREG_PHASE_9_STAGE2_E5.md` 3).

    python -u -m tools.phase9.e9_5_e5_analyse

One row per **conclusion** x **generator parameter**.  A conclusion is a stage-1 cell whose memory - static
contrast was significant under BH within its model's family of 36.

What this does, and why each step is the way it is:

*   **One frame per model per level, never a frame holding two settings.**  Section 3 is explicit that
    `seed_level_pairs` groups on (Model, Persona, Scenario_Cell, Seed, Arm) and **ignores `Setting`**, so a single
    call over the twelve `sens_*` settings would average the levels into one number with no error and run BH over
    12 x 36 rows in one family.  Each (model, level) therefore gets its own call, and the twelve results are put
    beside one another afterwards.  Unlike E3 and E4, E5 needs no family override: with `memory` and `static` the
    only arms present, the shared dict's Q1 fires exactly the registered contrast, one tier-C family of 36 under
    `bh_within`.

*   **The default level is read twice, and both are reported.**  Section 3 takes the conclusion set from stage 1,
    which ran 122 seeds, while every `sens_*` level ran 60.  A sign that differs between a 122-seed default and a
    60-seed level could be the seed set rather than the level, so the default is also computed on the **same 60
    seeds** the levels use, and the sign criterion is applied against that matched default.  The 122-seed figure
    is carried beside it, because the conclusion set itself is stage 1's as published.

*   **Both readings of the sign criterion, as P9-23 settled.**  *significant-only* (the headline): a conclusion is
    level-dependent only if some level is significant with the opposite sign.  *plain* (the plan's sentence):
    level-dependent if the sign differs at any level, significant or not.  Neither is collapsed into the other.

*   **R5** is `tools.phase9.e9_3_simulate.analytic`'s `p_R5` -- R4's two-way variance referred to t(M - 1),
    addendum 1's adopted candidate -- computed on the (model x path) matrix of memory - static at that level, then
    BH-adjusted within the stage-1 family the conclusion came from.

*   **The level x arm interaction** is (level effect - matched-default effect) per model and path, with a 90 %
    interval on t(M - 1), against the registered equivalence margin of 0.025 (half the minimum effect, D12).

Each criterion is reported in its own column and the verdict names which one fired; no criterion is collapsed
into another.
"""
from __future__ import annotations

import json
import os
import time

import numpy as np
import pandas as pd
from scipy import stats

from tools.phase9.e9_3_simulate import analytic
from tools.stats_v2 import TIER_C, run_stats_v21, scenario_cell

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
E94 = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e9_4")
OUT = os.path.join(E94, "stats_e5_sensitivity")

E5_MANIFEST = "e9_4_stage2_sens"
HEADLINE = ("e9_4_stage1_headline_open", "e9_4_stage1_headline_open_b2")
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
SEEDS = range(10001, 10061)
MARGIN = 0.025                      # addendum: half of D12's 0.05
PARAM_OF = lambda lv: lv.replace("sens_", "").rsplit("__", 1)[0]


def _slug(s: str) -> str:
    return s.replace("/", "_").replace("|", "_").replace(".", "_")


def contrasts_for(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """run_stats_v21's tier-C table for one frame, or empty."""
    if df.empty or len(set(df["Arm"]) & {"memory", "static"}) < 2:
        return pd.DataFrame()
    t = run_stats_v21(df, prefix)["contrasts"]
    return t[(t["tier"] == "C") & (t["contrast"] == "memory - static")].copy()


def paired(df: pd.DataFrame, persona: str, cell: str, metric: str) -> pd.DataFrame:
    """(Model x Path) matrix of memory - static for one cell and metric."""
    d = df.copy()
    d["Scenario_Cell"] = scenario_cell(d)
    d = d[(d["Persona"] == persona) & (d["Scenario_Cell"] == cell)]
    if d.empty:
        return pd.DataFrame()
    g = d.groupby(["Model", "Seed", "Arm"])[metric].mean().unstack("Arm")
    if "memory" not in g.columns or "static" not in g.columns:
        return pd.DataFrame()
    return (g["memory"] - g["static"]).dropna().unstack("Seed")


def r5_p(mat: pd.DataFrame) -> float:
    if mat.empty or mat.shape[0] < 2 or mat.shape[1] < 2:
        return float("nan")
    D = mat.to_numpy(float)[None, :, :]
    if not np.isfinite(D).all():
        return float("nan")
    return float(analytic(D)["p_R5"][0])


def interaction_ci(level_mat: pd.DataFrame, base_mat: pd.DataFrame):
    """(estimate, lo, hi) for the level x arm interaction on t(M - 1), 90 %."""
    if level_mat.empty or base_mat.empty:
        return (float("nan"),) * 3
    common_m = level_mat.index.intersection(base_mat.index)
    common_p = level_mat.columns.intersection(base_mat.columns)
    if len(common_m) < 2 or len(common_p) < 2:
        return (float("nan"),) * 3
    diff = level_mat.loc[common_m, common_p] - base_mat.loc[common_m, common_p]
    per_model = diff.mean(axis=1).to_numpy(float)
    M = len(per_model)
    est = float(per_model.mean())
    se = float(per_model.std(ddof=1) / np.sqrt(M))
    t = float(stats.t.ppf(0.95, M - 1))
    return est, est - t * se, est + t * se


def main() -> int:
    per_run = pd.read_csv(os.path.join(E94, "per_run.csv"))
    if E5_MANIFEST not in set(per_run["Manifest"]):
        raise SystemExit(f"{E5_MANIFEST} is not in per_run.csv -- score it first")
    os.makedirs(OUT, exist_ok=True)
    sens = per_run[(per_run["Manifest"] == E5_MANIFEST) & (per_run["Persona"].isin(PERSONAS))]
    levels = sorted(sens["Setting"].unique())
    models = sorted(sens["Model"].unique())
    print(f"E5: {len(models)} models x {len(levels)} levels", flush=True)

    head = per_run[(per_run["Manifest"].isin(HEADLINE)) & (per_run["Persona"].isin(PERSONAS))
                   & (per_run["Model"].isin(models))]
    head60 = head[head["Seed"].isin(SEEDS)]

    # ---- stage-1 conclusions, per model, family of 36, as published (122 seeds) ----
    print("stage-1 conclusions (the family of 36 per model, as published) ...", flush=True)
    concl, base60 = {}, {}
    for m in models:
        t = contrasts_for(head[head["Model"] == m], os.path.join(OUT, "_stage1_" + _slug(m)))
        if len(t):
            concl[m] = t.set_index(["Persona", "Scenario_Cell", "metric"])
            print(f"  {m.split('/')[-1][:38]:38s} {len(t)} tests, "
                  f"{int(t['claim'].sum())} significant -> conclusions", flush=True)
        t60 = contrasts_for(head60[head60["Model"] == m], os.path.join(OUT, "_stage1_60_" + _slug(m)))
        if len(t60):
            base60[m] = t60.set_index(["Persona", "Scenario_Cell", "metric"])

    # ---- every (model, level) on its own frame ----
    lvl = {}
    for m in models:
        for L in levels:
            f = sens[(sens["Model"] == m) & (sens["Setting"] == L)]
            t = contrasts_for(f, os.path.join(OUT, "_lvl_" + _slug(L) + "_" + _slug(m)))
            if len(t):
                lvl[(m, L)] = t.set_index(["Persona", "Scenario_Cell", "metric"])
        print(f"  levels done for {m.split('/')[-1][:38]}", flush=True)

    # ---- the table ----
    rows = []
    for m in models:
        if m not in concl:
            continue
        for key, c in concl[m].iterrows():
            if not bool(c["claim"]):
                continue                                   # a conclusion is a SIGNIFICANT stage-1 cell
            persona, cell, metric = key
            base = base60.get(m, pd.DataFrame())
            b_est = float(base.loc[key, "estimate"]) if (len(base) and key in base.index) else float("nan")
            sign_ref = np.sign(b_est if np.isfinite(b_est) else c["estimate"])
            bmat = paired(head60[head60["Model"] == m], persona, cell, metric)
            for param in sorted({PARAM_OF(L) for L in levels}):
                plv = [L for L in levels if PARAM_OF(L) == param]
                flips_plain, flips_sig, r5s, inter = [], [], [], []
                for L in plv:
                    t = lvl.get((m, L))
                    if t is None or key not in t.index:
                        continue
                    r = t.loc[key]
                    s = np.sign(float(r["estimate"]))
                    if s != 0 and sign_ref != 0 and s != sign_ref:
                        flips_plain.append(L)
                        if bool(r["claim"]):
                            flips_sig.append(L)
                    sub = sens[(sens["Model"] == m) & (sens["Setting"] == L)]
                    lmat = paired(sub, persona, cell, metric)
                    r5s.append((L, r5_p(lmat)))
                    inter.append((L,) + interaction_ci(lmat, bmat))
                worst = max((abs(e) for _, e, _, _ in inter if np.isfinite(e)), default=float("nan"))
                not_equiv = any(np.isfinite(lo) and np.isfinite(hi) and (lo > MARGIN or hi < -MARGIN)
                                for _, _, lo, hi in inter)
                verdict = ("level-dependent (significant-only)" if flips_sig else
                           "not equivalent" if not_equiv else "robust")
                rows.append({
                    "Model": m, "Persona": persona, "Scenario_Cell": cell, "metric": metric,
                    "parameter": param, "n_levels": len(plv),
                    "stage1_estimate_122seed": float(c["estimate"]),
                    "stage1_estimate_60seed": b_est,
                    "sign_reference": int(sign_ref),
                    "level_dependent_plain": bool(flips_plain),
                    "level_dependent_significant_only": bool(flips_sig),
                    "levels_flipping_plain": ";".join(PARAM_OF(x) + "/" + x.rsplit("__", 1)[-1] for x in flips_plain),
                    "levels_flipping_significant": ";".join(x.rsplit("__", 1)[-1] for x in flips_sig),
                    "max_abs_interaction": worst,
                    "equivalence_margin": MARGIN,
                    "not_equivalent": bool(not_equiv),
                    "r5_p_min": float(np.nanmin([p for _, p in r5s])) if r5s else float("nan"),
                    "verdict": verdict,
                })
    T = pd.DataFrame(rows)
    T.to_csv(os.path.join(OUT, "robustness_table.csv"), index=False)

    summary = {"n_models": len(models), "n_levels": len(levels),
               "n_conclusions": int(sum(int(c["claim"].sum()) for c in concl.values())),
               "n_rows": int(len(T)),
               "equivalence_margin": MARGIN,
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if len(T):
        summary["verdicts"] = {k: int(v) for k, v in T["verdict"].value_counts().items()}
        summary["level_dependent_plain"] = int(T["level_dependent_plain"].sum())
        summary["level_dependent_significant_only"] = int(T["level_dependent_significant_only"].sum())
        summary["by_parameter_significant_only"] = {
            k: int(v) for k, v in T.groupby("parameter")["level_dependent_significant_only"].sum().items()}
        summary["by_parameter_plain"] = {
            k: int(v) for k, v in T.groupby("parameter")["level_dependent_plain"].sum().items()}
        isfj = T[(T["Persona"] == "ISFJ") & (T["metric"] == "band_mas")]
        summary["P4_isfj_band_mas_rows"] = int(len(isfj))
        summary["P4_isfj_holding_sign_everywhere"] = int((~isfj["level_dependent_plain"]).sum())
    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8"), indent=1)
    print("\n" + json.dumps(summary, indent=1), flush=True)
    print(f"\nwritten -> {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
