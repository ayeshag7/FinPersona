"""
E3.9a (PREREG_PHASE_3_ADDENDUM.md section 4.1): the level-free surrogate TRAINED ON CALM ROWS ONLY.

The published audit (`evaluation/leakage_audit.py::l2_surrogate`) fits `_oos_predictions` on ALL rows and only
then masks by phase group, so its "calm R2" is a CROSS-PHASE-trained model scored against calm-only variance --
a large negative value there is substantially a train/eval regime artefact, not a measure of what a calm-day
reader can extract.  This module restricts the panel to calm rows BEFORE fitting and otherwise changes nothing:
same level-free feature construction, same three estimators, same GroupKFold-by-path cross-validation (held-out
seeds), same 500-resample cluster bootstrap over paths.

Run on the STORED hand-over panels (no regeneration), Phase 3 and Phase 2, so the before/after comparison is
like-for-like under the corrected estimator.  Reports R2(x) AND sign accuracy on resolvable steps -- the pair
the addendum registered, because the direction is the statistic a mandate-conformity benchmark turns on.

    python -m tools.phase3.e3_9_calm_trained [--n-boot 500]

Output: docs/env_v2/generated/v2_1/e3_9/calm_trained.{json,md}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e3_9")
THETA = 0.05
PANELS = {
    "phase3": (os.path.join(GEN, "_panels", "sep_phase3_after.pkl"),
               os.path.join(GEN, "e3_after", "audit_after_levelfree.pkl")),
    "phase2": (os.path.join(GEN, "_panels", "sep_phase2_after.pkl"),
               os.path.join(GEN, "e2_6_after", "audit_after_levelfree.pkl")),
}


def calm_trained(panel: pd.DataFrame, shown, n_boot: int):
    """The audit's own machinery, restricted to calm rows BEFORE the fit."""
    from evaluation.leakage_audit import _prepare, _models, _oos_predictions, _r2, _cluster_ci
    dfl, full_cols, ctrl_cols = _prepare(panel, shown, "level_free")
    calm = (dfl["macro"] == "calm").to_numpy()
    dfl = dfl.loc[calm].reset_index(drop=True)
    groups = (dfl["scenario"].astype(str) + "-" + dfl["seed"].astype(str)).to_numpy(dtype=object)
    y = dfl["x"].to_numpy(dtype=float)
    path_of = pd.factorize(pd.Series(groups))[0]
    n_paths = int(path_of.max()) + 1
    rows = []
    for fs_name, fcols in (("full", full_cols), ("price_only", ctrl_cols)):
        X = dfl[fcols].to_numpy(dtype=float)
        for mname, model in _models().items():
            p = _oos_predictions(X, y, groups, model)
            ok = np.isfinite(p)
            row = {"feature_set": fs_name, "model": mname, "n_rows": int(len(y)), "n_paths": n_paths,
                   "R2": _r2(y, p)}
            cnt = np.bincount(path_of[ok], minlength=n_paths).astype(float)
            sy = np.bincount(path_of[ok], weights=y[ok], minlength=n_paths)
            syy = np.bincount(path_of[ok], weights=y[ok] ** 2, minlength=n_paths)
            sres = np.bincount(path_of[ok], weights=(y[ok] - p[ok]) ** 2, minlength=n_paths)

            def r2_boot(idx, cnt=cnt, sy=sy, syy=syy, sres=sres):
                n = cnt[idx].sum()
                if n < 30:
                    return float("nan")
                ss = syy[idx].sum() - sy[idx].sum() ** 2 / n
                return float(1 - sres[idx].sum() / ss) if ss > 0 else float("nan")
            row["R2_lo"], row["R2_hi"] = _cluster_ci(r2_boot, n_paths, n_boot)
            res = (np.abs(y) >= THETA) & ok
            row["sign_acc_resolvable"] = float(np.mean(np.sign(p[res]) == np.sign(y[res]))) if res.sum() > 10 else np.nan
            row["n_resolvable"] = int(res.sum())
            c_ok = np.bincount(path_of[res], weights=(np.sign(p[res]) == np.sign(y[res])).astype(float),
                               minlength=n_paths)
            c_n = np.bincount(path_of[res], minlength=n_paths).astype(float)

            def sg_boot(idx, c_ok=c_ok, c_n=c_n):
                n = c_n[idx].sum()
                return float(c_ok[idx].sum() / n) if n > 10 else float("nan")
            row["sign_lo"], row["sign_hi"] = _cluster_ci(sg_boot, n_paths, n_boot)
            rows.append(row)
            print(f"    {fs_name:10s} {mname:5s} R2 {row['R2']:+.3f} [{row['R2_lo']:+.3f}, {row['R2_hi']:+.3f}]"
                  f"  sign {row['sign_acc_resolvable']:.3f} [{row['sign_lo']:.3f}, {row['sign_hi']:.3f}]",
                  flush=True)
    return rows


def published_rows(audit_pkl):
    """The as-published (cross-phase-trained) calm rows from the stored audit, for the side-by-side."""
    d = pd.read_pickle(audit_pkl)
    l2 = d["L2"]
    r = l2[(l2.target == "x") & (l2.phase_group == "calm")]
    return [{"feature_set": row.feature_set, "model": row.model, "R2": float(row.R2),
             "R2_lo": float(row.R2_lo), "R2_hi": float(row.R2_hi),
             "sign_acc_resolvable": float(row.sign_acc_resolvable),
             "sign_lo": float(row.sign_lo), "sign_hi": float(row.sign_hi),
             "n_resolvable": int(row.n_resolvable)} for row in r.itertuples()], d["shown_fields"]


def best(rows, fs):
    cand = [r for r in rows if r["feature_set"] == fs and np.isfinite(r["R2"])]
    return max(cand, key=lambda r: r["R2"]) if cand else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-boot", type=int, default=500)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    res = {"what": "the level-free surrogate trained on CALM ROWS ONLY, beside the published cross-phase-trained "
                   "calm rows, on the stored hand-over panels of Phases 2 and 3",
           "design": {"panels": {k: os.path.relpath(v[0], ROOT) for k, v in PANELS.items()},
                      "estimator_difference": "the published audit fits on all rows (GroupKFold by path) and "
                                              "masks by phase group afterwards; here the panel is restricted to "
                                              "calm rows BEFORE the fit, everything else identical",
                      "theta": THETA, "n_boot": a.n_boot,
                      "L2_sign_threshold_plan": 0.70},
           "states": {}}
    for state, (panel_p, audit_p) in PANELS.items():
        print(f"[{state}]", flush=True)
        pub, shown = published_rows(audit_p)
        panel = pd.read_pickle(panel_p)
        ct = calm_trained(panel, shown, a.n_boot)
        res["states"][state] = {"published_cross_phase_trained": pub, "calm_trained": ct,
                                "n_rows_panel": int(len(panel))}
    # headline pairs
    hl = {}
    for state in PANELS:
        s = res["states"][state]
        hl[state] = {
            "published_levelfree": best(s["published_cross_phase_trained"], "price_only"),
            "calm_trained_levelfree": best(s["calm_trained"], "price_only"),
            "published_full": best(s["published_cross_phase_trained"], "full"),
            "calm_trained_full": best(s["calm_trained"], "full"),
        }
    res["headline"] = hl
    res["seconds"] = round(time.time() - t0)
    with open(os.path.join(OUT, "calm_trained.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)

    def fmt(r):
        if r is None:
            return "n/a"
        return (f"{r['R2']:+.3f} [{r['R2_lo']:+.3f}, {r['R2_hi']:+.3f}] / sign {r['sign_acc_resolvable']:.3f} "
                f"[{r['sign_lo']:.3f}, {r['sign_hi']:.3f}]")
    L = ["# E3.9a the level-free calm channel under a CALM-TRAINED surrogate "
         "(PREREG_PHASE_3_ADDENDUM.md section 4.1)", "",
         res["design"]["estimator_difference"] + ". Best model per cell; R2(x) / sign accuracy on resolvable "
         f"steps (|x| >= {THETA}), {a.n_boot}-resample cluster bootstrap over paths. The plan's own L2 sign "
         "threshold is 0.70.", "",
         "| state | feature set | published (cross-phase-trained) | calm-trained |", "|---|---|---|---|"]
    for state in ("phase2", "phase3"):
        for fs, lab in (("price_only", "level-free"), ("full", "full field set")):
            L.append(f"| {state} | {lab} | {fmt(hl[state]['published_' + ('levelfree' if fs == 'price_only' else 'full')])} "
                     f"| {fmt(hl[state]['calm_trained_' + ('levelfree' if fs == 'price_only' else 'full')])} |")
    with open(os.path.join(OUT, "calm_trained.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
