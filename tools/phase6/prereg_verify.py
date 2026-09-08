"""
PREREG_PHASE_6.md section 1: every inherited number verified against the file it cites, BEFORE any experiment
builds on it (P4-37, PHASE_5's `prereg_power.py --stages verify` pattern).

A row is a (label, cited value, file, accessor); the accessor reads the value from the file.  A figure that does
not reproduce is reported as a discrepancy and the FILE's value is the one the pre-registration uses.

    python -m tools.phase6.prereg_verify          -> docs/env_v2/generated/v2_1/e6_0/verify.{json,md}
"""
from __future__ import annotations

import json
import math
import os
import pickle
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
PARAMS = os.path.join(ROOT, "envs", "v2", "params")
OUT = os.path.join(GEN, "e6_0")


def _j(rel):
    with open(os.path.join(GEN, rel) if not rel.startswith("envs") else os.path.join(ROOT, rel), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _pkl(rel):
    with open(os.path.join(GEN, rel), "rb") as fh:
        return pickle.load(fh)


def rows():
    R = []
    # --- Phase-5 final state: the SEP audit
    aud = _pkl("e5_after/audit_after_levelfree.pkl")
    b = aud["L2b"]; v = aud["L2_verdict"]
    R += [("L2b full accuracy, Phase 5", 0.676, "e5_after/audit_after_levelfree.pkl L2b.acc_full", b["acc_full"], 3),
          ("L2b price-only accuracy", 0.658, "... L2b.acc_price_only", b["acc_price_only"], 3),
          ("L2b day-only accuracy", 0.508, "... L2b.acc_day_only", b["acc_day_only"], 3),
          ("L2b majority class", 0.414, "... L2b.majority_class", b["majority_class"], 3),
          ("L2b selectivity (+1.8 pp)", 0.018, "... L2b.selectivity", b["selectivity"], 3),
          ("L2 calm best R2(x)", -0.61, "... L2_verdict.calm_best_R2_x", v["calm_best_R2_x"], 2),
          ("L2 event best R2(x)", 0.45, "... L2_verdict.event_best_R2_x", v["event_best_R2_x"], 2),
          ("L2 event MAPE(V)", 0.128, "... L2_verdict.event_best_MAPE_V", v["event_best_MAPE_V"], 3),
          ("L2 max selectivity R2(x)", 0.028, "... L2_verdict.max_selectivity_R2_x", v["max_selectivity_R2_x"], 3),
          ("L2 max MAPE(V) gain", 0.017, "... L2_verdict.max_MAPE_gain_V", v["max_MAPE_gain_V"], 3),
          ("L2 shuffled-V R2", 0.001, "... L2_verdict.max_R2_shuffledV", v["max_R2_shuffledV"], 3),
          ("audit not subsampled", False, "... subsampled", aud["subsampled"], None),
          ("audit paths", 1600, "... n_paths", aud["n_paths"], None)]
    l1 = pd.read_csv(os.path.join(GEN, "e5_after", "audit_after_levelfree_L1.csv"))
    px = l1[l1["candidate"].str.contains("price itself")].iloc[0] if "candidate" in l1.columns else None
    if px is not None:
        R += [("L1 price itself median APE", 0.063, "e5_after/audit_after_levelfree_L1.csv", float(px["median_APE"]), 3),
              ("L1 price itself within-5 %", 0.426, "... within_5pct", float(px["within_5pct"]) if "within_5pct" in l1.columns else float("nan"), 3)]
    # --- calm-trained
    ct = _j("e5_after/calm_trained_phase5.json")["headline"]["phase5"]
    R += [("calm-trained level-free R2(x), Phase 5", 0.2912, "e5_after/calm_trained_phase5.json headline.phase5.calm_trained_levelfree.R2", ct["calm_trained_levelfree"]["R2"], 4),
          ("... CI lo", 0.2637, "... R2_lo", ct["calm_trained_levelfree"]["R2_lo"], 4),
          ("... CI hi", 0.3179, "... R2_hi", ct["calm_trained_levelfree"]["R2_hi"], 4),
          ("calm-trained full R2(x), Phase 5", 0.3950, "... calm_trained_full.R2", ct["calm_trained_full"]["R2"], 4)]
    # --- the final ablation
    ab = _j("e5_7a/final/ablation.json")
    f = ab["fits"]; t = ab["tables"]
    R += [("BASE|x|all R2 (the box's reference row)", 0.4059, "e5_7a/final/ablation.json fits.BASE|x|all.R2", f["BASE|x|all"]["R2"], 4),
          ("BASE|x|calm R2", 0.2912, "... fits.BASE|x|calm.R2", f["BASE|x|calm"]["R2"], 4),
          ("FULL|x|all R2", 0.432, "... fits.FULL|x|all.R2", f["FULL|x|all"]["R2"], 3),
          ("VAL add-one, all rows", 0.0090, "... tables.x|all.groups.VAL.add_one.delta", t["x|all"]["groups"]["VAL"]["add_one"]["delta"], 4),
          ("VAL add-one, calm-trained", 0.0509, "... tables.x|calm.groups.VAL.add_one.delta", t["x|calm"]["groups"]["VAL"]["add_one"]["delta"], 4),
          ("FULL - BASE, all rows (what 'the eighteen fields add' means)", 0.026, "... fits.FULL|x|all.R2 - fits.BASE|x|all.R2", f["FULL|x|all"]["R2"] - f["BASE|x|all"]["R2"], 3),
          ("sum of per-group add-ones, all rows (informational; differs from FULL - BASE by the groups' interaction)", 0.020,
           "... tables.x|all (sum over groups)", sum(g["add_one"]["delta"] for g in t["x|all"]["groups"].values() if "add_one" in g), 3),
          ("ANALYST column-permutation null p95", -0.0057, "e5_7a/baseline/ablation.json null_margins.ANALYST.p95_estimate", _j("e5_7a/baseline/ablation.json")["null_margins"]["ANALYST"]["p95_estimate"], 4),
          ("SENT column-permutation null p95", -0.0024, "... null_margins.SENT.p95_estimate", _j("e5_7a/baseline/ablation.json")["null_margins"]["SENT"]["p95_estimate"], 4)]
    # --- E3.8 and the block
    e38 = _j("e3_8/decomposition.json")
    arms = {a["label"].split(" ")[0]: a for a in e38["arms"]}
    ex, full = e38["arms"][0], e38["arms"][3]
    R += [("E3.8 exact-Gaussian level-free R2", 0.145, "e3_8/decomposition.json arms[0].levelfree_R2", ex["levelfree_R2"], 3),
          ("E3.8 exact arm's Gaussian bound", 0.163, "... arms[0].bound_window_avg_gaussian", ex["bound_window_avg_gaussian"], 3),
          ("E3.8 full stack level-free R2", 0.203, "... arms[3].levelfree_R2", full["levelfree_R2"], 3),
          ("E3.8 full stack CI lo", 0.141, "... arms[3].ci95[0]", full["ci95"][0], 3),
          ("E3.8 full stack CI hi", 0.262, "... arms[3].ci95[1]", full["ci95"][1], 3),
          ("E3.8 full stack bound (window avg)", 0.177, "... arms[3].bound_window_avg_gaussian", full["bound_window_avg_gaussian"], 3),
          ("E3.8 s_x implied (with jumps)", 0.0656, "... arms[3].s_x_implied", full["s_x_implied"], 4)]
    blk = _j("e3_4/block.json")
    R += [("sigma_V in force", 0.014573, "envs/v2/params/value.json sigma_V.value", _j("envs/v2/params/value.json")["sigma_V"]["value"], 6),
          ("h in force (d)", 22.381, "envs/v2/params/mispricing.json half_life.value", _j("envs/v2/params/mispricing.json")["half_life"]["value"], 3),
          ("h interval lo", 18.75, "... structural.interval.h[0]", _j("envs/v2/params/mispricing.json")["structural"]["interval"]["h"][0], 2),
          ("h interval hi", 32.64, "... structural.interval.h[1]", _j("envs/v2/params/mispricing.json")["structural"]["interval"]["h"][1], 2),
          ("sbar in force", 0.015088, "e3_4/block.json sbar", blk["sbar"], 6),
          ("GJR alpha", 0.027, "e3_4/block.json shape.alpha", blk["shape"]["alpha"], 3),
          ("GJR gamma", 0.058, "... shape.gamma", blk["shape"]["gamma"], 3),
          ("GJR beta", 0.932, "... shape.beta", blk["shape"]["beta"], 3),
          ("jump rate", 0.000583, "... jump_rate", blk["jump_rate"], 6),
          ("jump sd", 0.2303, "... jump_sd", blk["jump_sd"], 4)]
    kv = _j("kalman_bound_verification.json")
    R += [("Kalman bound verified against LOG section 3", True, "kalman_bound_verification.json passed", kv["passed"], None)]
    # --- onset, L5
    on = _j("e5_7c/final/onset.json")
    R += [("onset PASS under the non-price rule (all six transitions)", True, "e5_7c/final/onset.json verdict_nonprice.all_pass",
           bool(on["verdict_nonprice"]["all_pass"]), None),
          ("onset under the rule as registered: number of failing (transition, field) pairs", 9, "... verdict.failures (len)",
           len(on["verdict"]["failures"]), None)]
    dis = _j("e5_l5/discrimination.json")["states"]["phase5_after"]["scenarios"]
    for sc, want in (("flat", 0.362), ("crash", 0.543), ("bull_trap", 0.636), ("sustained_bull", 0.354)):
        R.append((f"L5 coverage {sc}, Phase 5", want, f"e5_l5/discrimination.json states.phase5_after.scenarios.{sc}.coverage_0.05",
                  dis[sc]["coverage_0.05"], 3))
    for sc in ("flat", "crash", "bull_trap", "sustained_bull"):
        s = dis[sc]
        R.append((f"L5 ordering oracle < L5 < trivial, {sc}", True, f"... scenarios.{sc} (oracle.mean < L5_best.mean < trivial_best.mean)",
                  bool(s["oracle"]["mean"] < s["L5_best"]["mean"] < s["trivial_best"]["mean"]), None))
    # --- the audit_bounds entry that names Phase 6
    ob = _j("envs/v2/params/observables.json")["audit_bounds"]
    R += [("audit_bounds.no_field_deterministic_R2 (PROVISIONAL)", 0.2, "envs/v2/params/observables.json audit_bounds.value", ob["value"]["no_field_deterministic_R2"], 3),
          ("audit_bounds.l2b_margin_phase6_owned (PROVISIONAL)", 0.1, "... l2b_margin_phase6_owned", ob["value"]["l2b_margin_phase6_owned"], 3),
          ("audit_bounds status", "PROVISIONAL", "... status", ob["status"], None)]
    return R


def main():
    os.makedirs(OUT, exist_ok=True)
    out = []
    n_bad = 0
    for label, cited, where, got, nd in rows():
        if got is None or (isinstance(got, float) and math.isnan(got)):
            ok = None
        elif nd is None:
            ok = (got == cited)
        else:
            ok = abs(float(got) - float(cited)) <= 0.5 * 10 ** (-nd) + 1e-12
        n_bad += (ok is False)
        out.append({"label": label, "cited": cited, "file": where, "file_value": got, "match": ok})
        print(f"{'OK ' if ok else ('?? ' if ok is None else 'MISMATCH')} {label:58s} cited {cited!s:>10}  file {got!s}")
    res = {"rows": out, "n_rows": len(out), "n_mismatch": n_bad, "n_unreadable": sum(1 for r in out if r["match"] is None),
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(os.path.join(OUT, "verify.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    L = ["# PREREG_PHASE_6 section 1 — inherited numbers verified against their files", "",
         f"{len(out)} rows; {n_bad} mismatches; {res['n_unreadable']} unreadable. Generated {res['generated_utc']}.", "",
         "| inherited figure | cited | file | file value | match |", "|---|---|---|---|---|"]
    for r in out:
        fv = r["file_value"]
        fv = f"{fv:.6g}" if isinstance(fv, float) else str(fv)
        L.append(f"| {r['label']} | {r['cited']} | `{r['file']}` | {fv} | {'OK' if r['match'] else ('unreadable' if r['match'] is None else '**MISMATCH**')} |")
    with open(os.path.join(OUT, "verify.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"{n_bad} mismatches -> {OUT}")
    return 0 if n_bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
