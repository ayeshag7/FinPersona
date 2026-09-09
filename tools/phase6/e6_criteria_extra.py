"""
v2.1 Phase 6 -- the blocks of `evaluation/params/phase6_criteria.json` that come from files other than E6.1/E6.2:

  item9     PREREG_PHASE_6.md 5.4: item 9's reference bands from E6.9's AR(1) known answer at the FIT half-life
            (the T = 200 P10/P90 of the sample ACF(1), and of the sample sd scaled to the engine's s_x)
  l1_floor  E6.5's derived ceiling on the within-5 % share (e6_5/floor.json)
  gates     E6.6/E6.7: the L2 (all, calm) and L2b margins from the target-permutation nulls (e6_6/null/null.json):
            margin = null p95 + the paired sampling half-width; the centred sensitivity beside; the verdicts
  n_min     criterion B's minimum n_gen for size (the n at which its D = 0 pass rate first exceeds 0.90 in
            e6_2/criteria.json's size/power table)

Every block carries provenance (label, source, date, interval, n) and the status DERIVED; the loud loader
(`evaluation/criteria.py`) validates the file after the write.  Nothing here is stated: every number is read from
the file named in its `source`.

    python -m tools.phase6.e6_criteria_extra --stages item9,l1_floor,n_min[,gates]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
CRIT = os.path.join(ROOT, "evaluation", "params", "phase6_criteria.json")
TODAY = time.strftime("%Y-%m-%d")


def _j(p):
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def block_item9(doc):
    ka = _j(os.path.join(GEN, "e6_9", "known_answers.json"))
    cases = {c["name"]: c for c in ka["cases"]}
    a = cases["acf_ar1_engine_persistence_lag1"]["horizons"]["200"]
    s = cases["sd_ar1_engine"]["horizons"]["200"]
    h = ka["meta"]["engine_half_life_days"]
    rho = 2.0 ** (-1.0 / h)
    stationary_unit = 1.0 / math.sqrt(1.0 - rho ** 2)          # sd of the unit-innovation AR(1) the case simulated
    b = _j(os.path.join(GEN, "e6_6", "bound.json"))["bound"]["adopted"]
    s_x = float(b["s_x"])
    doc["item9_reference"] = {
        "value": {"acf1_p10": a["p10"], "acf1_p50": a["median"], "acf1_p90": a["p90"], "half_life_days": h,
                  "sd_lo": s_x * s["p10"] / stationary_unit, "sd_hi": s_x * s["p90"] / stationary_unit,
                  "sd_p50_scaled": s_x * s["median"] / stationary_unit, "s_x": s_x, "n_reps": a["n_reps"]},
        "status": "DERIVED",
        "label": "item 9 judged as fidelity to the FIT process measured with the same 200-day ruler: the cross-seed median "
                 "ACF(1) of x on flat paths inside the [P10, P90] of the sample ACF(1) of an AR(1) at the FIT half-life "
                 "(E6.9, T = 200), and the median 200-day sd(x) inside the AR(1) reference's [P10, P90] scaled to s_x",
        "source": "docs/env_v2/generated/v2_1/e6_9/known_answers.json (acf_ar1_engine_persistence_lag1, sd_ar1_engine); "
                  "e6_6/bound.json adopted.s_x", "date": TODAY,
        "interval": "the [P10, P90] bands are the intervals", "n": {"reps": a["n_reps"], "T": 200}}
    print(f"item9: ACF(1) [{a['p10']:.4f}, {a['p90']:.4f}]; sd(x) [{doc['item9_reference']['value']['sd_lo']:.4f}, {doc['item9_reference']['value']['sd_hi']:.4f}]")


def block_l1_floor(doc):
    f = _j(os.path.join(GEN, "e6_5", "floor.json"))
    r = f["rule"]
    doc.setdefault("gates", {})["l1_floor"] = {
        "value": {"ceiling_5pct": r["ceiling_5pct"], "halfwidth_5pct": r["halfwidth_5pct"], "margin_5pct": r["margin_5pct"],
                  "trivial_empirical_5pct": f["empirical_trivial"]["tau_0.05"]["share"],
                  "s_x": f["inputs"]["s_x"], "bound_day_T": f["inputs"]["bound_day_T"]},
        "status": "DERIVED",
        "label": "E6.5: no candidate's within-5 % share may exceed 2*Phi(0.05/(s_x*sqrt(1-B)))-1 plus the share's cluster-bootstrap "
                 "half-width at 1,600 paths; replaces the hard-coded 1 % floor (weakness 32)",
        "source": _rel(os.path.join(GEN, "e6_5", "floor.json")), "date": TODAY,
        "interval": "the half-width is the interval", "n": {"paths": f["empirical_trivial"]["n_paths"]}}
    print(f"l1_floor: margin {r['margin_5pct']:.4f}")


def block_n_min(doc):
    c = _j(os.path.join(GEN, "e6_2", "criteria.json"))
    by_n = {}
    for r in c["rows"]:
        if r.get("population") == "size_power":
            for n, sp in r["size_power"].items():
                by_n.setdefault(int(n), []).append(sp["D0.00"]["pass_rate_B"])
    table = {n: float(np.median(v)) for n, v in sorted(by_n.items())}
    n_min = next((n for n, m in sorted(table.items()) if m >= 0.90), None)
    doc["criterion_B"]["value"]["n_min_size"] = n_min
    doc["criterion_B"]["value"]["size_pass_rate_at_D0_by_n"] = table
    doc["criterion_B"]["label"] += (f"; decisive only at n_gen >= {n_min} (the smallest n at which its median pass rate under "
                                    f"a true D = 0 is >= 0.90: {table})")
    print(f"n_min for B: {n_min}; median pass rate at D = 0 by n: {table}")


def block_gates(doc):
    n = _j(os.path.join(GEN, "e6_6", "null", "null.json"))
    s = n["summary"]
    gates = doc.setdefault("gates", {})
    for key, name in (("x|all", "l2_all"), ("x|calm", "l2_calm"), ("macro|all", "l2b")):
        if key not in s or "derived_margin" not in s[key]:
            print(f"{name}: not in the null summary yet -- skipped")
            continue
        b = s[key]; nl = b["null"]
        centred = float(nl["p95"] - nl["median"] + b["sampling_halfwidth"])
        gates[name] = {
            "value": {"measured_selectivity": b["measured_selectivity"], "selectivity_ci95": b["selectivity_ci95_paired"],
                      "sampling_halfwidth": b["sampling_halfwidth"], "null_median": nl["median"], "null_p95": nl["p95"],
                      "null_n_draws": nl["n_draws"], "margin": b["derived_margin"], "pass": b["verdict_under_derived_margin"],
                      "centred_margin": centred, "pass_centred": bool(b["measured_selectivity"] <= centred),
                      "base_value": b["base_value"], "full_value": b["full_value"]},
            "status": "DERIVED",
            "label": f"{name}: selectivity (FULL - BASE, the audit's GBT, {'macro-class accuracy' if name == 'l2b' else 'R2(x)'}) <= "
                     f"null p95 + the paired sampling half-width, the null = paths' targets permuted across seeds with both feature "
                     f"sets refitted ({nl['n_draws']} draws; the 95th percentile of 20 draws lies between the 19th and 20th order "
                     f"statistic); the centred margin (p95 - median + half-width) is the registered sensitivity",
            "source": _rel(os.path.join(GEN, "e6_6", "null", "null.json")), "date": TODAY,
            "interval": "the null's draws and the paired CI are the intervals", "n": {"paths": n["n_paths"], "draws": nl["n_draws"]}}
        print(f"{name}: measured {b['measured_selectivity']:+.4f}, null median {nl['median']:+.4f}, p95 {nl['p95']:+.4f}, "
              f"margin {b['derived_margin']:+.4f} -> {'PASS' if b['verdict_under_derived_margin'] else 'FAIL'} "
              f"(centred margin {centred:+.4f} -> {'PASS' if gates[name]['value']['pass_centred'] else 'FAIL'})")


def block_items(doc):
    """The registered item -> statistics mapping WITH its per-statistic population and reference overrides and the
    descriptive flag (PREREG_PHASE_6.md 5.1): the first writer of the criteria file dropped `per_stat_pop` /
    `per_stat_reference` (item 20's calm sigma is judged on the flat paths against every window) and carried no
    descriptive flag for item 4 -- a defect of the file writer, corrected here from the E6.2 tool's registered dict."""
    from tools.phase6.e6_2_criteria import ITEMS
    doc["items"] = {str(k): {"statistics": v["stats"], "population": v["pop"], "reference": v.get("reference", "all"),
                             "property": v["property"], "per_stat_population": v.get("per_stat_pop", {}),
                             "per_stat_reference": v.get("per_stat_reference", {}),
                             "descriptive": bool(k == 4)} for k, v in ITEMS.items()}
    doc["_items_note"] = ("item 4 is descriptive (plan 10.2: 'never as the pass criterion'); item 20's daily_sigma is judged on the flat "
                          "paths against every real window, its mdd and worst_day on the crash paths against the crash windows")
    print("items block rewritten with the per-statistic overrides and item 4 descriptive")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="item9,l1_floor,n_min")
    a = ap.parse_args(argv)
    doc = _j(CRIT)
    doc["_status_key"].setdefault("DERIVED", "computed from a null, a bound or a known-answer reference by a registered rule")
    for st in [s.strip() for s in a.stages.split(",")]:
        {"item9": block_item9, "l1_floor": block_l1_floor, "n_min": block_n_min, "gates": block_gates, "items": block_items}[st](doc)
    tmp = CRIT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    from evaluation import criteria as CR
    CR.load(tmp)                                   # the loud loader validates before the file is replaced
    os.replace(tmp, CRIT)
    print(f"written and validated: {_rel(CRIT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
