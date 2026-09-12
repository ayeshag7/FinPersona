"""
v2.1 Phase 9 -- E9.2: the roster variance pilots and the stage-1 seed count they give (PREREG_PHASE_9.md 2).

    python -u -m tools.phase9.e9_2_pilot --stages shape,manifest
    python -u -m tools.phase9.e9_runner run --manifest docs/env_v2/generated/v2_1/e9_2/manifest.json --config <key> --workers 15
    python -u -m tools.phase9.e9_2_pilot --stages score,analyse

`shape`     For pilot seeds S_p per cell at R = 1 on E8.5's 12 persona x scenario cells, compute:
            * the pilot's runs (24 S_p), pairs (12 S_p) and df_d (12 S_p - 12);
            * the one-sided 90 % chi-square limit's inflation f^2 = df / chi2_{0.10}(df);
            * the expected total runs per model = pilot runs + f^2 x G_ref.
            G_ref is stage 1's run count per model at the reference seeds (e8_5/transfer.json's 93), divided by the
            inflation E8.5's own sizing carried (f^2 at E8.5's df_d, 84).  The pilot takes the S_p with the smallest
            expected total (ties -> the smaller); E8.5's shape is shown beside.
`manifest`  Every roster configuration not measured in the grid's configuration (e9_roster.MEASURED_IN_GRID_CONFIG) is
            piloted. Flash is not, but its static / memory prompt hashes under the grid's harness must equal E8.5's
            launch manifest; if they differ, Flash is piloted too.
            Cells: 3 personas x (static, memory) x 4 scenarios x pilot seeds 3001.. x rep 0.  The pilot's seeds are
            disjoint from E8.5's (2001-2008) and from the grid's (10001..).
`score`     every checkpointed pilot run -> `metrics_v2.score_run(scoring="v2_1")` -> e9_2/per_run.csv.
`analyse`   per model and metric: the seed-level pairs, sigma_d(R = 1) and its chi-square 90 % limit on df_d (the
            closed-form limit at R' = R, P8-15).  Flash's R = 1 limit is E8.5's closed form (e8_5/components.csv).
            The plug-in is the MAXIMUM of the band-MAS limit over the roster (P8-16, applied to measured models), and
            stage 1's seeds follow Appendix A as written at alpha' = 0.05 / 36, with the paired-correct count beside.

Outputs: docs/env_v2/generated/v2_1/e9_2/{shape.json, manifest.json, per_run.csv, sigma.csv, sizing.json}
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e9_2")
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
ARMS = ("static", "memory")
SCENARIOS = ("flat", "bull_trap", "crash", "sustained_bull")
N_CELLS = len(PERSONAS) * len(SCENARIOS)
PILOT_SEED0 = 3001
SP_CANDIDATES = (4, 8, 12, 16, 24, 32)
E85_DF_D = 84
Q = 0.90
# PREREG_PHASE_9_ADDENDUM.md 5 (TEAM, 12 Sep 2026): the only pilots allowed to be short of their planned cells, stopped
# on a clock two hours from 06:30 UTC and not on any measured sigma_d.  Every other model must finish, or the sizing
# refuses to call itself complete and stage 1 does not start.
TRUNCATED = frozenset({"gemini-2.5-pro|default", "gpt-5-nano|default"})


def f2(df: int) -> float:
    return df / stats.chi2.ppf(1 - Q, df)


def stage1_runs_per_model(seeds: int) -> int:
    """Stage 1's run count per model at `seeds` (PREREG_PHASE_9.md 4): the 12 headline cells x 2 arms, plus the D11
    common-start slice (3 personas x {static, memory, swapped} + the NONE trader, x 4 scenarios)."""
    return N_CELLS * len(ARMS) * seeds + (len(PERSONAS) * 3 + 1) * len(SCENARIOS) * seeds


def stage_shape():
    ref = int(json.load(open(os.path.join(GEN, "e8_5", "transfer.json"), encoding="utf-8"))["band_mas_plugin"]["seeds_appA_bonf_main_grid"])
    g_ref = stage1_runs_per_model(ref) / f2(E85_DF_D)
    rows = []
    for sp in SP_CANDIDATES:
        runs, pairs = N_CELLS * len(ARMS) * sp, N_CELLS * sp
        df = pairs - N_CELLS
        rows.append({"seeds_per_cell": sp, "runs": runs, "pairs": pairs, "df_d": df, "f2": f2(df), "f": math.sqrt(f2(df)),
                     "expected_total_runs_per_model": runs + f2(df) * g_ref})
    t = pd.DataFrame(rows)
    best = t.sort_values(["expected_total_runs_per_model", "seeds_per_cell"]).iloc[0]
    doc = {"registered": "PREREG_PHASE_9.md 2", "reference_seeds": ref, "stage1_runs_at_reference": stage1_runs_per_model(ref),
           "G_ref": g_ref, "e8_5_shape": {"runs": 576, "pairs": 96, "df_d": E85_DF_D, "df_rep": 384, "f2_at_df_d": f2(E85_DF_D)},
           "table": json.loads(t.to_json(orient="records")), "chosen_seeds_per_cell": int(best["seeds_per_cell"]),
           "chosen_runs_per_model": int(best["runs"]), "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    os.makedirs(OUT, exist_ok=True)
    json.dump(doc, open(os.path.join(OUT, "shape.json"), "w", encoding="utf-8"), indent=1)
    print(t.round(3).to_string(index=False))
    print("chosen:", doc["chosen_seeds_per_cell"], "seeds per cell,", doc["chosen_runs_per_model"], "runs per model")


def stage_manifest():
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    shape = json.load(open(os.path.join(OUT, "shape.json"), encoding="utf-8"))
    seeds = list(range(PILOT_SEED0, PILOT_SEED0 + int(shape["chosen_seeds_per_cell"])))
    cells = [{"persona": p, "arm": a, "scenario": sc, "seed": s, "rep": 0} for p in PERSONAS for a in ARMS for sc in SCENARIOS for s in seeds]
    configs = [k for k in RO.ROSTER if k not in RO.MEASURED_IN_GRID_CONFIG]
    # Flash's exemption: its E8.5 prompts must be the grid harness's prompts
    e85 = json.load(open(os.path.join(GEN, "e8_5", "manifest.json"), encoding="utf-8"))["fingerprint"]["prompt_hash"]
    probe = {"name": "flash-check", "subdir": "pilot", "configs": sorted(RO.MEASURED_IN_GRID_CONFIG),
             "cells": [{"persona": p, "arm": a, "scenario": "flat", "seed": 1} for p in PERSONAS for a in ARMS]}
    fp_flash = R.fingerprint(probe)["prompt_hash"]
    flash_same = all(fp_flash[f"gemini-2.5-flash|thinking0|{p}|{a}"] == e85[f"gemini-2.5-flash|{p}|{a}"] for p in PERSONAS for a in ARMS)
    if not flash_same:
        configs = list(RO.ROSTER)
    m = {"name": "e9_2_pilot", "kind": "pilot", "subdir": "pilot", "ledger_dir": "e9_2", "T": 200, "configs": configs,
         "cells": cells, "seeds": seeds, "flash_prompts_equal_e8_5": bool(flash_same),
         "registered": "PREREG_PHASE_9.md 2; DECISION_LOG P9-2, P9-5", "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    m["fingerprint"] = R.fingerprint(m)
    path = os.path.join(OUT, "manifest.json")
    if os.path.exists(path):
        R.verify_fingerprint(json.load(open(path, encoding="utf-8")))
        print("manifest exists and its fingerprint matches; not rewritten")
        return
    json.dump(m, open(path, "w", encoding="utf-8", newline="\n"), indent=1)
    print(f"manifest: {len(configs)} configurations x {len(cells)} runs; Flash's prompts equal E8.5's: {flash_same}")


# PREREG_PHASE_9_ADDENDUM.md 10 and 10a: the OpenRouter configurations run TRUNCATED seed lists, each in its own
# manifest, so "planned" is per configuration and not one number for the phase.  These two are not piloted at all --
# Qwen3.7 Flash on a measured 4,973 s per run, GLM 4.7 Flash under item 8's stopping rule -- so they cannot reach the
# plug-in, and the report must say the maximum was taken over 12 of 14.
NOT_PILOTED = frozenset({"openrouter/qwen/qwen3.7-flash|default", "openrouter/z-ai/glm-4.7-flash|default"})


def pilot_manifests() -> list:
    """Every registered pilot manifest: section 2's 16-seed one and the truncated OpenRouter ones (addendum 10)."""
    return sorted(glob.glob(os.path.join(OUT, "manifest*.json")))


def stage_score():
    from evaluation import scoring_params as SP
    SP.load()
    from evaluation.metrics_v2 import score_run
    from tools.phase8.e8_5_analyse import metric_names
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    rows = []
    for mpath in pilot_manifests():
        m = R.load_manifest(mpath)
        for key in m["configs"]:
            mc = RO.by_key(key)
            done = R.done_keys(m["subdir"], mc, m["cells"])
            for c in m["cells"]:
                cfg = R.cfg_for(mc, c, m["subdir"])
                if R.run_key(c, cfg) not in done:
                    continue
                df = pd.read_csv(R.run_paths(cfg)["csv"])
                sc = score_run(df, cfg.persona, scoring="v2_1")
                rows.append({"Model": key, "Persona": cfg.persona, "Arm": cfg.arm, "Scenario": cfg.scenario,
                             "Seed": cfg.seed, "Decode_Replicate": 0,
                             **{k: sc.get(k) for k in metric_names() + ["mdd_pct", "return_pct", "fallback_share", "trade_count"]}})
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(OUT, "per_run.csv"), index=False)
    json.dump({"scoring_json_sha256": SP.SHA256, "n_runs": int(len(t)), "by_model": t.groupby("Model").size().to_dict() if len(t) else {},
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "per_run.meta.json"), "w", encoding="utf-8"), indent=1)
    print("scored", len(t), t.groupby("Model").size().to_dict() if len(t) else {})


def sigma_r1(t: pd.DataFrame, metric: str) -> dict:
    """R = 1 pilot: d = memory - static per (persona, scenario, seed); sigma_d on df_d = pairs - cells; chi-square
    one-sided 90 % limit (the closed-form limit at R' = R, `test_mls_limit_reduces_to_chi_square`)."""
    g = t.groupby(["Persona", "Scenario", "Seed", "Arm"])[metric].mean().unstack("Arm")
    d = (g["memory"] - g["static"]).dropna()
    grp = d.groupby(level=["Persona", "Scenario"])
    df_d = int(len(d) - grp.ngroups)
    s2 = float(((d - grp.transform("mean")) ** 2).sum() / df_d) if df_d > 0 else float("nan")
    lim = math.sqrt(df_d * s2 / stats.chi2.ppf(1 - Q, df_d)) if df_d > 0 else float("nan")
    return {"n_pairs": int(len(d)), "df_d": df_d, "sigma_d_R1": math.sqrt(s2) if np.isfinite(s2) else float("nan"),
            "sigma_d_R1_limit90": lim, "mean_d": float(d.mean())}


def stage_analyse():
    from experiments import inference_params as IP
    from tools.phase8.e8_5_analyse import metric_names, n_seeds, mdd
    t = pd.read_csv(os.path.join(OUT, "per_run.csv"))
    rows = []
    for model, tm in t.groupby("Model"):
        for metric in metric_names():
            rows.append({"Model": model, "metric": metric, "source": "e9_2 pilot (R = 1)", **sigma_r1(tm.dropna(subset=[metric]), metric)})
    c85 = pd.read_csv(os.path.join(GEN, "e8_5", "components.csv"))
    for _, r in c85[c85.Model == "gemini-2.5-flash"].iterrows():
        rows.append({"Model": "gemini-2.5-flash|thinking0", "metric": r["metric"], "source": "E8.5 closed form at R' = 1 (P8-15)",
                     "n_pairs": int(r["n_pairs"]), "df_d": int(r["df_d"]), "sigma_d_R1": float(r["sigma_d_R1"]),
                     "sigma_d_R1_limit90": float(r["sigma_d_R1_mls90"]), "mean_d": float(r["mean_d"])})
    s = pd.DataFrame(rows)
    s.to_csv(os.path.join(OUT, "sigma.csv"), index=False)
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    bm = s[s.metric == "band_mas"].set_index("Model")
    missing = [k for k in RO.ROSTER if k not in bm.index]
    # a pilot that is merely UNFINISHED must never size the grid: compare each model's completed runs with its planned
    # cells, and allow only the models the team truncated on the clock (PREREG_PHASE_9_ADDENDUM.md 5) to be short
    planned, done = {}, {}
    for mpath in pilot_manifests():
        man = R.load_manifest(mpath)
        for k in man["configs"]:
            planned[k] = planned.get(k, 0) + len(man["cells"])
            done[k] = done.get(k, 0) + len(R.done_keys(man["subdir"], RO.by_key(k), man["cells"]))
    # A configuration the team DROPPED (P9-7, P9-8) cannot be "unfinished": it was abandoned by decision, it sizes
    # nothing, and leaving it in `short` would hold `complete` false for ever and hide whether the ROSTER finished.
    # It is reported separately instead, so nothing disappears.
    short = sorted(k for k, v in done.items() if v < planned[k] and k not in TRUNCATED and k in RO.ROSTER)
    dropped_short = sorted(k for k, v in done.items() if v < planned[k] and k not in RO.ROSTER)
    alpha_b = float(IP.block("main_grid_sizing")["value"]["alpha_bonferroni"])
    delta = float(IP.block("min_effect")["value"]["band_mas"])
    # the maximum is over the ROSTER only: a model measured but excluded from the phase (P9-7) is reported and sizes
    # nothing, so its rows must not reach the plug-in
    bm = bm.loc[[k for k in RO.ROSTER if k in bm.index]]
    plug = float(bm["sigma_d_R1_limit90"].max())
    seeds = n_seeds(plug, delta, alpha_b)
    doc = {"registered": "PREREG_PHASE_9.md 2 (P8-16's rule on measured models); truncation: addendum 5",
           "roster": list(RO.ROSTER), "missing_models": missing,
           "runs_done_vs_planned": {k: [v, planned[k]] for k, v in sorted(done.items())},
           "truncated_by_the_clock": sorted(TRUNCATED),
           "truncated_seed_lists_addendum_10": [os.path.basename(p) for p in pilot_manifests() if "openrouter" in p],
           "not_piloted_registered": sorted(k for k in missing if k in NOT_PILOTED),
           "missing_unregistered": sorted(k for k in missing if k not in NOT_PILOTED),
           "plugin_over_n_of_roster": [int(len([k for k in RO.ROSTER if k in bm.index])), len(RO.ROSTER)],
           "unfinished_models": short,
           "dropped_and_unfinished": dropped_short,
           "complete": (not [k for k in missing if k not in NOT_PILOTED]) and not short, "plugin_sigma_d_band_mas": plug, "plugin_model": str(bm["sigma_d_R1_limit90"].idxmax()),
           "alpha_bonferroni": alpha_b, "delta": delta, "stage1_seeds_appA": seeds,
           "stage1_seeds_paired_correct": n_seeds(plug, delta, alpha_b, factor2=False),
           "per_model_band_mas": json.loads(bm[["sigma_d_R1", "sigma_d_R1_limit90", "df_d", "source"]].to_json(orient="index")),
           "mdd_at_stage1_seeds": {mt: {mod: mdd(float(r["sigma_d_R1_limit90"]), seeds, alpha_b) for mod, r in g.set_index("Model").iterrows()}
                                   for mt, g in s.groupby("metric")},
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(doc, open(os.path.join(OUT, "sizing.json"), "w", encoding="utf-8"), indent=1)
    print(bm[["sigma_d_R1", "sigma_d_R1_limit90", "df_d"]].sort_values("sigma_d_R1_limit90").round(4).to_string())
    print({k: doc[k] for k in ("complete", "missing_models", "plugin_sigma_d_band_mas", "plugin_model", "stage1_seeds_appA", "stage1_seeds_paired_correct")})


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="shape,manifest")
    a = ap.parse_args(argv)
    for st in [x.strip() for x in a.stages.split(",") if x.strip()]:
        {"shape": stage_shape, "manifest": stage_manifest, "score": stage_score, "analyse": stage_analyse}[st]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
