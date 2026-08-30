"""
Reproduce E1.3 grid rows locally with the sweep's own run_point (ADDENDUM section 6.2): the Kaggle sweep reported calm
R2(x) 0.41 at (sigma_V 0.006, t5, s_x 0.165) while the same reader on the same point gives ~0.15 here.

    python -m tools.phase1.e1_3_repro_point [--workers 3] [--n-seeds 200]
Outputs: docs/env_v2/generated/v2_1/e1_3/repro_point.{json,md}
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")

POINTS = [(0.006, ("t5", 5.0), 0.165), (0.020, ("t5", 5.0), 0.165), (0.006, ("gaussian", None), 0.10)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--n-seeds", type=int, default=200)
    a = ap.parse_args()
    import numpy, pandas, sklearn, scipy
    from tools.phase1.e1_3_sweep import run_point, sbar_for
    stored = json.load(open(os.path.join(GEN, "e1_3", "sweep.json"), encoding="utf-8"))
    env = {"python": platform.python_version(), "numpy": numpy.__version__, "pandas": pandas.__version__, "sklearn": sklearn.__version__, "scipy": scipy.__version__}
    out = {"environment_local": env, "n_seeds": a.n_seeds, "rows": []}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for sv, (dname, dfv), sx in POINTS:
            over = {"sigma_V": sv, "df_V": dfv, "garch": {"sbar": sbar_for(sx)}}
            r = run_point(ex, over, a.n_seeds, f"sV {sv} {dname} sx {sx}", (sv, sx, 150.0))
            k = next(g for g in stored["grid"] if g["sigma_V"] == sv and g["df_V"] == dname and g["s_x"] == sx)
            out["rows"].append({"sigma_V": sv, "df_V": dname, "s_x": sx,
                                "local": {"calm": r["surrogate_level_free"]["calm"], "all_R2": r["surrogate_level_free"]["all"]["R2"], "cov_flat_0.05": r["coverage"]["flat"]["theta_0.05"],
                                          "item9_hl": r["item9_T800"]["hl_median"], "sd_x5000": r["realised_sd_x_T5000_jumps_off"]["mean"]},
                                "kaggle": {"calm": k["surrogate_level_free"]["calm"], "all_R2": k["surrogate_level_free"]["all"]["R2"], "cov_flat_0.05": k["coverage"]["flat"]["theta_0.05"],
                                           "item9_hl": k["item9_T800"]["hl_median"], "sd_x5000": k["realised_sd_x_T5000_jumps_off"]["mean"]}})
            print(out["rows"][-1], f"{time.time() - t0:.0f} s", flush=True)
    with open(os.path.join(GEN, "e1_3", "repro_point.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=float)
    L = ["# E1.3 grid rows reproduced locally (ADDENDUM section 6.2)", "", f"Local environment: {env}. Same seeds, same run_point, {a.n_seeds} seeds x 4 scenarios.", "",
         "| point | calm R2 local [CI] | calm R2 Kaggle [CI] | all R2 local / Kaggle | cov flat 0.05 local / Kaggle | item 9 hl local / Kaggle | sd_x5000 local / Kaggle |", "|---|---|---|---|---|---|---|"]
    for r in out["rows"]:
        l, k = r["local"], r["kaggle"]
        L.append(f"| sV {r['sigma_V']} {r['df_V']} sx {r['s_x']} | {l['calm']['R2']:.3f} [{l['calm']['ci95'][0]:.3f}, {l['calm']['ci95'][1]:.3f}] | {k['calm']['R2']:.3f} [{k['calm']['ci95'][0]:.3f}, {k['calm']['ci95'][1]:.3f}] | "
                 f"{l['all_R2']:.3f} / {k['all_R2']:.3f} | {l['cov_flat_0.05']:.2f} / {k['cov_flat_0.05']:.2f} | {l['item9_hl']:.0f} / {k['item9_hl']:.0f} | {l['sd_x5000']:.3f} / {k['sd_x5000']:.3f} |")
    with open(os.path.join(GEN, "e1_3", "repro_point.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
