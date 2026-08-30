"""
Why does E1.3's surrogate not reproduce across machines while the SEP audit does? (ADDENDUM section 6.2.)
Hypothesis: `HistGradientBoostingRegressor` is constructed with `early_stopping='auto'`, which turns early stopping ON
for n > 10,000 rows; the iteration count then depends on floating-point summation order in the OpenMP histogram build,
so it varies with thread count and library build. The audit's larger panel may saturate `max_iter` and hide it.

Test: one panel, the same seeds, refit under thread counts {1, 4} and with early stopping on / off.
A spread across thread counts is proof of non-determinism inside one environment.

    python -m tools.phase1.e1_3_determinism_check [--n-seeds 40]
Outputs: docs/env_v2/generated/v2_1/e1_3/determinism_check.{json,md}
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
PANEL = os.path.join(GEN, "e1_3", "_determinism_panel.pkl")

WORKER = r"""
import json, os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, r"{root}")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from evaluation.leakage_audit import add_level_free_columns, add_lags_and_returns, _oos_predictions, LEVEL_FREE_KEYS
panel = pd.read_pickle(r"{panel}")
d = add_level_free_columns(panel)
keys = [k for k in ("RSI14", "trend_strength", "trend_regime", "lp_sma20", "lp_sma50", "macd_p", "macds_p") if k in d]
dfl, cols = add_lags_and_returns(d, keys)
dfl = dfl.dropna(subset=cols).reset_index(drop=True)
cols = [c for c in cols if c.split("_lag")[0] in LEVEL_FREE_KEYS]
groups = (dfl["scenario"].astype(str) + "-" + dfl["seed"].astype(str)).to_numpy(dtype=object)
y = dfl["x"].to_numpy(float)
calm = dfl["macro"].to_numpy(dtype=object) == "calm"
es = {es_flag}
m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.08, max_depth=6, random_state=0, early_stopping=es)
p = _oos_predictions(dfl[cols].to_numpy(float), y, groups, m)
def r2(mask):
    yy, pp = y[mask], p[mask]
    ss = ((yy - yy.mean()) ** 2).sum()
    return float(1 - ((yy - pp) ** 2).sum() / ss)
print(json.dumps({{"calm_R2": r2(calm), "all_R2": r2(np.ones(len(y), bool)), "n_rows": int(len(y)), "n_features": len(cols)}}))
"""


def run(threads: int, es_flag: str) -> dict:
    src = WORKER.format(root=ROOT, panel=PANEL, es_flag=es_flag)
    env = dict(os.environ, OMP_NUM_THREADS=str(threads), OPENBLAS_NUM_THREADS=str(threads), MKL_NUM_THREADS=str(threads))
    r = subprocess.run([sys.executable, "-c", src], capture_output=True, text=True, env=env, cwd=ROOT)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2000:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-seeds", type=int, default=40)
    a = ap.parse_args()
    from concurrent.futures import ProcessPoolExecutor
    from tools.phase1.e1_3_sweep import _path_job, SEED0, SCENARIOS4, sbar_for
    import pandas as pd
    if not os.path.exists(PANEL):
        over = {"sigma_V": 0.006, "df_V": 5.0, "garch": {"sbar": sbar_for(0.165)}}
        jobs = [(s, sc, over) for sc in SCENARIOS4 for s in range(SEED0, SEED0 + a.n_seeds)]
        with ProcessPoolExecutor(max_workers=2) as ex:
            frames = [df for df, _ in ex.map(_path_job, jobs, chunksize=8)]
        pd.concat(frames, ignore_index=True).to_pickle(PANEL)
    out = {"panel": {"n_seeds": a.n_seeds, "point": "sigma_V 0.006, t5, s_x 0.165 (the in-force grid row)"}, "runs": {}}
    import sklearn, numpy, platform
    out["environment"] = {"python": platform.python_version(), "sklearn": sklearn.__version__, "numpy": numpy.__version__}
    for es_flag, es_name in (("'auto'", "early_stopping='auto' (as _models() builds it)"), ("False", "early_stopping=False")):
        for threads in (1, 4):
            r = run(threads, es_flag)
            out["runs"][f"{es_name} | OMP={threads}"] = r
            print(f"{es_name:<46} OMP={threads}  calm R2 {r['calm_R2']:.4f}  all R2 {r['all_R2']:.4f}", flush=True)
    with open(os.path.join(GEN, "e1_3", "determinism_check.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    auto = [v["calm_R2"] for k, v in out["runs"].items() if "auto" in k]
    off = [v["calm_R2"] for k, v in out["runs"].items() if "False" in k]
    L = ["# E1.3 surrogate determinism check (ADDENDUM section 6.2)", "",
         f"One panel ({a.n_seeds} seeds x 4 scenarios at the in-force grid point), identical seeds and features; only the thread count and "
         f"the early-stopping flag differ. Environment: {out['environment']}.", "",
         "| estimator setting | OMP threads | calm R2(x) | all R2 |", "|---|---|---|---|"]
    for k, v in out["runs"].items():
        name, thr = k.split(" | OMP=")
        L.append(f"| {name} | {thr} | {v['calm_R2']:.4f} | {v['all_R2']:.4f} |")
    L += ["", f"Spread across thread counts: early_stopping='auto' {max(auto) - min(auto):.4f}; early_stopping=False {max(off) - min(off):.4f}.",
          "", "A non-zero spread with 'auto' and a zero spread with False identifies the defect: early stopping picks its iteration count "
          "from a validation score computed over OpenMP-parallel histogram sums, so the fitted model -- and every R2 derived from it -- "
          "depends on the thread count and the library build. The fix for any gate is to construct the estimator with early_stopping=False "
          "(or a fixed n_iter) and to pin the library versions."]
    with open(os.path.join(GEN, "e1_3", "determinism_check.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L[-3:]))


if __name__ == "__main__":
    main()
