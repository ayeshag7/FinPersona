"""
Calm-reference reconciliation (PREREG_PHASE_1_ADDENDUM.md section 6.2): why E1.3's grid surrogate reports calm
R2(x) ~ 0.41 at the parameters in force while the SEP audit's level-free reader reports ~ 0.08. Both estimators are run
on both panels, crossed with both calm definitions:

  panels:    P_grid = E1.3's in-force point (seeds 60000-60199 x 4 scenarios, crash delta 0.70; hidden-path features)
             P_sep  = the SEP-after panel (1,600 rendered paths; docs/env_v2/generated/v2_1/_panels/sep_after.pkl)
  readers:   R_grid = tools.phase1.e1_3_sweep.surrogate (GBT, 7 level-free keys + lags/returns, GroupKFold by path)
             R_sep  = evaluation.leakage_audit.l2_surrogate(control="level_free") best-model calm row
  calm:      the generator's phase label == "calm" (E1.3) vs the audit's phase_group == "calm" (SEP)

    python -m tools.phase1.e1_3_calm_reconcile [--workers 3] [--n-seeds 200]
Outputs: docs/env_v2/generated/v2_1/e1_3/calm_reconcile.{json,md}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")


def grid_panel(n_seeds: int, workers: int) -> pd.DataFrame:
    from tools.phase1.e1_3_sweep import _path_job, SEED0, SCENARIOS4
    jobs = [(s, sc, {}) for sc in SCENARIOS4 for s in range(SEED0, SEED0 + n_seeds)]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        frames = [df for df, _ in ex.map(_path_job, jobs, chunksize=10)]
    return pd.concat(frames, ignore_index=True)


def audit_calm(panel: pd.DataFrame) -> dict:
    from evaluation.leakage_audit import l2_surrogate, _models
    from agent.render import rendered_market_fields
    panel = panel.copy()
    if "V" not in panel.columns:                       # the grid panel carries price and x only
        panel["V"] = panel["price"].to_numpy(float) * np.exp(-panel["x"].to_numpy(float))
    shown = [f for f in rendered_market_fields("v2") if f in panel.columns]
    l2 = l2_surrogate(panel, shown, theta=0.05, control="level_free", n_boot=300, models={"gbt": _models()["gbt"]})
    rows = l2[(l2["feature_set"] == "price_only") & (l2["target"] == "x")]
    out = {}
    for _, r in rows.iterrows():
        out[str(r["phase_group"])] = {"R2": float(r["R2"]), "ci95": [float(r["R2_lo"]), float(r["R2_hi"])], "n": int(r["n"])}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--n-seeds", type=int, default=200)
    a = ap.parse_args()
    from tools.phase1.e1_3_sweep import surrogate
    from envs.synthetic_market import MACRO_OF
    t0 = time.time()
    res = {"design": {"grid_seeds": [60000, 60000 + a.n_seeds - 1], "sep_panel": "_panels/sep_after.pkl", "n_boot": 300}}
    # panels
    pg = grid_panel(a.n_seeds, a.workers)
    ps = pd.read_pickle(os.path.join(GEN, "_panels", "sep_after.pkl"))
    if "macro" not in ps.columns:
        ps["macro"] = ps["phase"].map(MACRO_OF).fillna("calm")
    res["panels"] = {"grid": {"rows": int(len(pg)), "paths": int(pg.groupby(["scenario", "seed"]).ngroups), "calm_rows": int((pg["macro"] == "calm").sum())},
                     "sep": {"rows": int(len(ps)), "paths": int(ps.groupby(["scenario", "seed"]).ngroups), "calm_rows": int((ps["macro"] == "calm").sum())}}
    print("panels", res["panels"], flush=True)
    # E1.3's reader on both panels (calm = generator phase label)
    res["R_grid_on_grid"] = surrogate(pg, n_boot=300); print("R_grid on grid", res["R_grid_on_grid"]["calm"], flush=True)
    res["R_grid_on_sep"] = surrogate(ps, n_boot=300); print("R_grid on sep", res["R_grid_on_sep"]["calm"], flush=True)
    # the audit's reader on both panels (calm = the audit's phase group)
    res["R_sep_on_sep"] = audit_calm(ps); print("R_sep on sep", res["R_sep_on_sep"].get("calm"), flush=True)
    res["R_sep_on_grid"] = audit_calm(pg); print("R_sep on grid", res["R_sep_on_grid"].get("calm"), flush=True)
    # the grid reader on the flat scenario alone (the composition question)
    res["R_grid_on_grid_flat_only"] = surrogate(pg[pg["scenario"] == "flat"].reset_index(drop=True), n_boot=300)
    res["R_grid_on_sep_flat_only"] = surrogate(ps[ps["scenario"] == "flat"].reset_index(drop=True), n_boot=300)
    res["seconds"] = round(time.time() - t0)
    with open(os.path.join(GEN, "e1_3", "calm_reconcile.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=float)
    g = lambda d, k="calm": f"{d[k]['R2']:.3f} [{d[k]['ci95'][0]:.3f}, {d[k]['ci95'][1]:.3f}] (n {d[k]['n']})"
    L = ["# Calm-reference reconciliation (PREREG_PHASE_1_ADDENDUM.md section 6.2)", "",
         f"Grid panel: {res['panels']['grid']['paths']} paths, {res['panels']['grid']['rows']} rows, {res['panels']['grid']['calm_rows']} calm rows (generator phase label). "
         f"SEP-after panel: {res['panels']['sep']['paths']} paths, {res['panels']['sep']['rows']} rows, {res['panels']['sep']['calm_rows']} calm rows.", "",
         "| reader \\ panel | E1.3 grid panel (in-force point) | SEP-after panel |", "|---|---|---|",
         f"| E1.3 surrogate (calm = generator phase label) | {g(res['R_grid_on_grid'])} | {g(res['R_grid_on_sep'])} |",
         f"| audit l2_surrogate, level-free (calm = audit phase group) | {g(res['R_sep_on_grid'])} | {g(res['R_sep_on_sep'])} |",
         f"| E1.3 surrogate, flat scenario only | {g(res['R_grid_on_grid_flat_only'])} | {g(res['R_grid_on_sep_flat_only'])} |", "",
         "Reading: a row difference is the panel (composition, hidden vs rendered features); a column difference is the reader "
         "(feature construction, calm definition). The Phase-6 reference should be the cell that matches the published audit "
         "(audit reader on the SEP)."]
    with open(os.path.join(GEN, "e1_3", "calm_reconcile.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
