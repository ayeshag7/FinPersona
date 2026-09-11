"""
v2.1 Phase 8 -- E8.5's power analysis validated on data with a KNOWN answer before the pilot's data are read
(hard rule 2: every statistical method is validated on simulated data before it touches a real contrast).

    python -u -m tools.phase8.e8_5_validate [--datasets 200] [--boot 500] [--workers 2]

**Unregistered, disclosed** (PREREG_PHASE_8_ADDENDUM.md): PREREG 3.8 registered simulations for E8.3's estimators; the
plug-in quantities of 5.4 and the one-sided 90 % upper limit of 5.5 were not given one.  This check adds that evidence
and replaces no rule.

Data-generating process, E8.5's own shape (3 personas x 2 arms x 4 scenarios x 8 seeds x 3 replicates):
    y = mu[persona, scenario] + beta x memory + w[path] + x[path, arm] + e
with w ~ N(0, 0.05^2) (a path effect shared by both arms), x ~ N(0, s_int^2 / 2) per (path, arm) so that the seed-level
difference carries Var = s_int^2, and e ~ N(0, s_rep^2) per replicate.  The truth the plug-ins target is
sigma_d(R') = sqrt(s_int^2 + 2 s_rep^2 / R').

Reported per (s_int, s_rep): the median of estimate / truth for sigma_d(1) and sigma_d(3); the coverage of the
one-sided 90 % path-bootstrap upper limit (the share of datasets in which it is >= the truth, nominal 0.90) with a
Wilson interval; the share of datasets with sigma^2_int truncated at 0; and the seeds per cell D12's rule would ask for
at the truth against at the plug-in (median).

Output: docs/env_v2/generated/v2_1/e8_5/validate.{json,csv}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
warnings.filterwarnings("ignore")

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e8_5")
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
SCENARIOS = ("flat", "bull_trap", "crash", "sustained_bull")
SEEDS = tuple(range(8))
REPS = 3
CONDITIONS = [(0.03, 0.04), (0.0, 0.05), (0.05, 0.02)]      # (s_int, s_rep): mixed, replicate-only, seed-dominated
S_PATH = 0.05
BETA = 0.05


def simulate(rng, s_int, s_rep) -> pd.DataFrame:
    rows = []
    mu = {(p, c): rng.uniform(0.05, 0.4) for p in PERSONAS for c in SCENARIOS}
    for c in SCENARIOS:
        for s in SEEDS:
            w = rng.normal(0, S_PATH)
            for p in PERSONAS:
                for a, arm in enumerate(("static", "memory")):
                    x = rng.normal(0, s_int / np.sqrt(2)) if s_int > 0 else 0.0
                    for r in range(REPS):
                        rows.append({"Persona": p, "Arm": arm, "Scenario": c, "Seed": s, "Decode_Replicate": r,
                                     "y": mu[(p, c)] + BETA * a + w + x + rng.normal(0, s_rep)})
    return pd.DataFrame(rows)


def _task(args):
    s_int, s_rep, i, n_boot = args
    warnings.filterwarnings("ignore")
    from tools.phase8.e8_5_analyse import plug_ins, boot_plug_ins_fast, n_seeds, mls_ucl_sigma_d
    rng = np.random.default_rng([85, int(s_int * 1000), int(s_rep * 1000), i])
    t = simulate(rng, s_int, s_rep)
    p = plug_ins(t, "y")
    # the array form of the bootstrap the analysis uses, proven equal to the loop (test_boot_plug_ins_fast_equals_loop)
    b = boot_plug_ins_fast(t, "y", np.random.default_rng([86, i]), n_boot=n_boot)
    out = {"s_int": s_int, "s_rep": s_rep, "i": i, "sigma2_int": p["sigma2_int"], "sigma2_rep": p["sigma2_rep"]}
    alpha_b = 0.05 / 36
    for R in (1, 3):
        truth = np.sqrt(s_int ** 2 + 2 * s_rep ** 2 / R)
        out[f"truth_R{R}"] = truth
        out[f"est_R{R}"] = p[f"sigma_d_R{R}"]
        out[f"ucl90_R{R}"] = b[f"sigma_d_R{R}_ucl90"]
        out[f"covers_R{R}"] = bool(b[f"sigma_d_R{R}_ucl90"] >= truth)
        # the closed-form limit added after the bootstrap's under-coverage (addendum 16), measured on the same datasets
        mls = mls_ucl_sigma_d(p["sigma_d_R"] ** 2, p["df_d"], p["sigma2_rep"], p["df_rep"], p["R_harmonic"], R)
        out[f"mls90_R{R}"] = mls
        out[f"mls_covers_R{R}"] = bool(mls >= truth)
        out[f"n_seeds_mls_R{R}"] = n_seeds(mls, 0.05, alpha_b)
    out["n_seeds_truth_R1"] = n_seeds(out["truth_R1"], 0.05, alpha_b)
    out["n_seeds_plugin_R1"] = n_seeds(out["ucl90_R1"], 0.05, alpha_b)
    return out


def wilson(k, n, z=1.959963984540054):
    p = k / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, c - h, c + h


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", type=int, default=200)
    ap.add_argument("--boot", type=int, default=500)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args(argv)
    from concurrent.futures import ProcessPoolExecutor
    tasks = [(si, sr, i, a.boot) for si, sr in CONDITIONS for i in range(a.datasets)]
    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for k, r in enumerate(ex.map(_task, tasks, chunksize=4)):
            rows.append(r)
            if (k + 1) % 50 == 0:
                print(f"[{k + 1}/{len(tasks)}] {time.time() - t0:.0f}s", flush=True)
    t = pd.DataFrame(rows)
    os.makedirs(OUT, exist_ok=True)
    t.to_csv(os.path.join(OUT, "validate.csv"), index=False)
    summary = []
    for (si, sr), g in t.groupby(["s_int", "s_rep"]):
        row = {"s_int": si, "s_rep": sr, "n_datasets": int(len(g)),
               "share_sigma2_int_at_zero": float((g["sigma2_int"] <= 0).mean())}
        for R in (1, 3):
            row[f"median_est_over_truth_R{R}"] = float((g[f"est_R{R}"] / g[f"truth_R{R}"]).median())
            p, lo, hi = wilson(int(g[f"covers_R{R}"].sum()), len(g))
            row.update({f"ucl90_coverage_R{R}": p, f"ucl90_coverage_R{R}_lo": lo, f"ucl90_coverage_R{R}_hi": hi})
        row["median_n_seeds_truth_R1"] = float(g["n_seeds_truth_R1"].median())
        row["median_n_seeds_plugin_R1"] = float(g["n_seeds_plugin_R1"].median())
        row["share_plugin_n_below_truth_n"] = float((g["n_seeds_plugin_R1"] < g["n_seeds_truth_R1"]).mean())
        summary.append(row)
    s = pd.DataFrame(summary)
    json.dump({"registered": False, "reason": "PREREG 3.8 simulated E8.3's estimators, not E8.5's plug-ins; this adds that evidence",
               "design": {"personas": len(PERSONAS), "scenarios": len(SCENARIOS), "seeds": len(SEEDS), "reps": REPS,
                          "s_path": S_PATH, "beta": BETA, "boot": a.boot},
               "nominal_coverage": 0.90, "seconds": time.time() - t0, "table": json.loads(s.to_json(orient="records"))},
              open(os.path.join(OUT, "validate.json"), "w", encoding="utf-8"), indent=1)
    print(s.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
