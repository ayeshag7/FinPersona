"""
E3.6 (PREREG_PHASE_3.md section 8; weakness item 73): checklist item 5's statistic (fitted alpha + beta on path
returns) computed on CALM WINDOWS ONLY and on the WHOLE PATH, both reported. Runs on the applied Phase-3 state,
on the standard checklist panel (SCL seeds 40000+, the same panel as the after-state checklist row).

    python -m tools.phase3.e3_6_item73 [--seeds 200]

Output: docs/env_v2/generated/v2_1/e3_6/item73.{json,md}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e3_6")
CALM = {"calm", "sustained-bull"}
MIN_CALM_RUN = 100
SEED0 = 40000


def calm_runs(phases):
    runs, start = [], None
    for i, p in enumerate(list(phases) + ["_end"]):
        if p in CALM and start is None:
            start = i
        elif p not in CALM and start is not None:
            if i - start >= MIN_CALM_RUN:
                runs.append((start, i))
            start = None
    return runs


def main():
    from envs.synthetic_market import checklist_paths
    from evaluation.stylized_facts import garch_fit
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()
    paths = checklist_paths(a.seeds, 200, seed0=SEED0)
    whole, calm_only = [], []
    n_runs = 0
    for sc, plist in paths.items():
        for p in plist:
            r = p.df["r"].dropna().to_numpy()
            al, _, be = garch_fit(r)
            if np.isfinite(al) and np.isfinite(be):
                whole.append(al + be)
            ph = p.df["phase"].to_numpy(dtype=object)
            rr = p.df["r"].to_numpy()
            for lo, hi in calm_runs(ph):
                seg = rr[lo:hi]
                seg = seg[np.isfinite(seg)]
                if len(seg) >= MIN_CALM_RUN:
                    al, _, be = garch_fit(seg)
                    if np.isfinite(al) and np.isfinite(be):
                        calm_only.append(al + be)
                        n_runs += 1

    def summ(v):
        v = np.asarray(v, float)
        return {"median": float(np.median(v)), "p25_75": [float(np.percentile(v, 25)), float(np.percentile(v, 75))],
                "n": int(len(v))}
    out = {"design": {"panel": f"SCL checklist panel, {a.seeds} seeds per scenario (crash per delta), T = 200, "
                               f"seed0 {SEED0}", "calm_windows": f"maximal contiguous calm/sustained-bull runs "
                               f">= {MIN_CALM_RUN} d, fitted per run", "estimator": "item 5's garch_fit "
                               "(GARCH(1,1), zero mean, percent returns)"},
           "whole_path": summ(whole), "calm_windows_only": summ(calm_only),
           "item5_band": [0.90, 0.995],
           "in_band": {"whole": bool(0.90 <= float(np.median(whole)) <= 0.995),
                       "calm": bool(0.90 <= float(np.median(calm_only)) <= 0.995)},
           "seconds": round(time.time() - t0)}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "item73.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    L = ["# E3.6 / item 73: GARCH persistence on regime paths vs calm windows (PREREG_PHASE_3.md section 8)", "",
         out["design"]["panel"] + ".", "",
         "| computed on | median alpha+beta | IQR | n fits | inside item 5's [0.90, 0.995] |", "|---|---|---|---|---|",
         f"| whole path (the checklist's item 5) | {out['whole_path']['median']:.3f} | "
         f"{out['whole_path']['p25_75'][0]:.3f}-{out['whole_path']['p25_75'][1]:.3f} | {out['whole_path']['n']} | "
         f"{out['in_band']['whole']} |",
         f"| calm windows only (>= {MIN_CALM_RUN} d) | {out['calm_windows_only']['median']:.3f} | "
         f"{out['calm_windows_only']['p25_75'][0]:.3f}-{out['calm_windows_only']['p25_75'][1]:.3f} | "
         f"{out['calm_windows_only']['n']} | {out['in_band']['calm']} |"]
    with open(os.path.join(OUT, "item73.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
