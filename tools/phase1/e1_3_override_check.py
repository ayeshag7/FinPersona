"""
Diagnostic for the E1.3 discrepancy (PREREG_PHASE_1_ADDENDUM.md section 6.2): the sweep's grid rows pass explicit
overrides {sigma_V, df_V, garch.sbar} while its mu_V rows and the reconciliation pass none, and the level-free calm R2(x)
differs (0.41 vs 0.16) at nominally the same point. Which override moves it? Each variant: 100 seeds x 4 scenarios,
E1.3's own reader.

    python -m tools.phase1.e1_3_override_check [--workers 3] [--n-seeds 100]
Outputs: docs/env_v2/generated/v2_1/e1_3/override_check.{json,md}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")

VARIANTS = {
    "none (in force)": {},
    "garch.sbar 0.017 (the default value, passed explicitly)": {"garch": {"sbar": 0.017}},
    "garch.sbar 0.0160 (the grid's s_x = 0.165 row)": {"garch": {"sbar": 0.0160}},
    "sigma_V 0.006 + df_V 5 (explicit, = in force)": {"sigma_V": 0.006, "df_V": 5.0},
    "all three as the grid row": {"sigma_V": 0.006, "df_V": 5.0, "garch": {"sbar": 0.0160}},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--n-seeds", type=int, default=100)
    a = ap.parse_args()
    from tools.phase1.e1_3_sweep import _path_job, surrogate, SEED0, SCENARIOS4
    from envs.v2.generator import GenConfig
    t0 = time.time()
    out = {"design": {"seeds": [SEED0, SEED0 + a.n_seeds - 1], "scenarios": SCENARIOS4, "n_boot": 300}, "variants": {}}
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for name, over in VARIANTS.items():
            cfg = GenConfig(scenario="flat", seed=1, **over)
            gp = getattr(cfg, "garch", None)
            jobs = [(s, sc, over) for sc in SCENARIOS4 for s in range(SEED0, SEED0 + a.n_seeds)]
            frames = [df for df, _ in ex.map(_path_job, jobs, chunksize=8)]
            panel = pd.concat(frames, ignore_index=True)
            sur = surrogate(panel, n_boot=300)
            sd_x = float(panel.groupby(["scenario", "seed"])["x"].std().median())
            out["variants"][name] = {"override": over, "garch_override_seen_by_config": gp, "calm": sur["calm"], "all": sur["all"],
                                     "median_path_sd_x": sd_x, "calm_daily_sd": float(panel.loc[panel["macro"] == "calm"].groupby(["scenario", "seed"])["price"]
                                                                                      .apply(lambda p: pd.Series(p.to_numpy()).pct_change().std()).median())}
            print(name, {k: round(v, 3) if isinstance(v, float) else v for k, v in sur["calm"].items()}, "sd_x", round(sd_x, 3), f"{time.time() - t0:.0f} s", flush=True)
    with open(os.path.join(GEN, "e1_3", "override_check.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=float)
    L = ["# E1.3 override check (ADDENDUM section 6.2)", "", f"{a.n_seeds} seeds x 4 scenarios per variant; E1.3's reader; 300-resample cluster CI.", "",
         "| variant | calm R2(x) [CI] | all R2 | median path sd(x) | calm daily sd |", "|---|---|---|---|---|"]
    for k, v in out["variants"].items():
        L.append(f"| {k} | {v['calm']['R2']:.3f} [{v['calm']['ci95'][0]:.3f}, {v['calm']['ci95'][1]:.3f}] | {v['all']['R2']:.3f} | {v['median_path_sd_x']:.3f} | {v['calm_daily_sd']:.4f} |")
    with open(os.path.join(GEN, "e1_3", "override_check.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
