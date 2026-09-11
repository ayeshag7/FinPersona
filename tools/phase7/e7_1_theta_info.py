"""
v2.1 Phase 7 -- E7.1a, theta_info: the |x| at which the level-free observables surrogate's sign accuracy of x_hat on
the steps with |x| >= theta reaches 0.80 (PREREG_PHASE_7.md 1.1).

    python -u -m tools.phase7.e7_1_theta_info --stages predict,sweep [--workers 4]

Stage `predict` refits the AUDIT's surrogate -- `evaluation.leakage_audit`'s GBT
(HistGradientBoostingRegressor(max_iter=200, learning_rate=0.08, max_depth=6, random_state=0)), out-of-sample from
GroupKFold(n_splits=5) with groups = scenario-seed, on `_prepare(panel, feature_keys, control="level_free")` -- and
STORES THE PER-ROW PREDICTIONS, which the stored audit does not carry.  Two feature sets: `full` (every rendered
field) and `price_only` (the level-free control set).  Nothing about the construction differs from the audit: the
same panel, the same n/m encoding, the same lag depth, the same folds, the same seed.  The stage VERIFIES that
against the published Phase-6 sign accuracies before anything downstream reads it (PREREG 1.1) -- if the four
numbers do not reproduce, the refit is a different construction and the phase stops here.

Stage `sweep` reads the stored predictions and computes, per population (all / calm) and per scenario, the sign
accuracy on |x| >= theta over the registered grid, with percentile cluster-bootstrap 95 % intervals over paths
(500 resamples, the audit's `_cluster_ci`), and locates theta_info by the registered rule: the smallest grid value
at which the accuracy is >= 0.80 and stays >= 0.80 at every larger grid value.  "Not reached" is a result.

Output: <out>/predictions.parquet, <out>/verify.json, <out>/theta_info.{json,csv,md}
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
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "2")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

from tools.phase5.common import GEN, PANELS, encode_nm, pin_state  # noqa: E402

OUT = os.path.join(GEN, "e7_1")
PANEL = os.path.join(PANELS, "sep_phase5_after.pkl")
SCRATCH = os.path.join(OUT, "_scratch")

# The registered grid (PREREG 1.1): the plan's five values plus the finer spacing needed to locate a crossing.
THETA_GRID = (0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30)
TARGET_ACC = 0.80
N_BOOT = 500

# The four published Phase-6 numbers the refit must reproduce (e6_after/audit_after_derived_L2.csv, gbt/target x,
# theta = 0.05).  Read from that file at run time; these are the values the report quotes.
VERIFY_FILE = os.path.join(GEN, "e6_after", "audit_after_derived_L2.csv")
VERIFY_TOL = 1e-12


# ------------------------------------------------------------------------------------------------ stage: predict
def _prepare_arrays():
    """The audit's own preparation, verbatim: encode_nm -> shown fields -> _prepare(control='level_free')."""
    from evaluation.leakage_audit import _prepare
    from agent.render import rendered_market_fields
    pan = encode_nm(pd.read_pickle(PANEL))
    shown = [f for f in rendered_market_fields("v2") if f in pan.columns] + (["reported_PE_nm"] if "reported_PE_nm" in pan else [])
    feature_keys = [k for k in shown if k in pan.columns and k != "date"]
    dfl, full_cols, ctrl_cols = _prepare(pan, feature_keys, "level_free")
    groups = (dfl["scenario"].astype(str) + "-" + dfl["seed"].astype(str)).to_numpy(dtype=object)
    return dfl, full_cols, ctrl_cols, groups, feature_keys


def _fold_job(args):
    """One (feature set, fold) fit.  Arrays come from the on-disk memmap so the workers share one copy."""
    import warnings
    warnings.filterwarnings("ignore")
    os.environ["OMP_NUM_THREADS"] = os.environ.get("E7_FIT_THREADS", "2")
    from sklearn.ensemble import HistGradientBoostingRegressor
    fs, k, tr, te, xpath, ypath, n, ncol = args
    X = np.load(xpath, mmap_mode="r"); y = np.load(ypath, mmap_mode="r")
    t0 = time.time()
    m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.08, max_depth=6, random_state=0)
    m.fit(np.asarray(X[tr]), np.asarray(y[tr]))
    p = m.predict(np.asarray(X[te]))
    return fs, k, te, p, round(time.time() - t0, 1)


def predict(workers: int, fit_threads: int):
    from sklearn.model_selection import GroupKFold
    from concurrent.futures import ProcessPoolExecutor
    os.makedirs(SCRATCH, exist_ok=True)
    t0 = time.time()
    print("[predict] preparing the audit's frame", flush=True)
    dfl, full_cols, ctrl_cols, groups, feature_keys = _prepare_arrays()
    y = dfl["x"].to_numpy(dtype=float)
    print(f"  rows {len(dfl)}  paths {len(np.unique(groups))}  full cols {len(full_cols)}  control cols {len(ctrl_cols)}", flush=True)

    paths = {}
    for fs, cols in (("full", full_cols), ("price_only", ctrl_cols)):
        p = os.path.join(SCRATCH, f"X_{fs}.npy")
        np.save(p, dfl[cols].to_numpy(dtype=float))
        paths[fs] = p
    ypath = os.path.join(SCRATCH, "y.npy"); np.save(ypath, y)

    folds = list(GroupKFold(n_splits=5).split(np.zeros((len(y), 1)), y, groups))
    jobs = [(fs, k, tr, te, paths[fs], ypath, len(y), 0) for fs in ("full", "price_only") for k, (tr, te) in enumerate(folds)]
    pred = {fs: np.full(len(y), np.nan) for fs in ("full", "price_only")}
    os.environ["E7_FIT_THREADS"] = str(fit_threads)
    print(f"[predict] {len(jobs)} fits on {workers} workers x {fit_threads} threads", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for fs, k, te, p, secs in ex.map(_fold_job, jobs):
            pred[fs][te] = p
            print(f"  {fs} fold {k}: {secs} s ({time.time() - t0:.0f} s elapsed)", flush=True)

    out = pd.DataFrame({
        "scenario": dfl["scenario"].astype(str).to_numpy(),
        "seed": dfl["seed"].to_numpy(),
        "day": dfl["day"].to_numpy() if "day" in dfl else np.arange(len(dfl)),
        "phase_group": pd.Series(dfl["macro"]).replace({"down-event": "event", "up-event": "event"}).astype(str).to_numpy(),
        "x": y,
        "pred_full": pred["full"],
        "pred_price_only": pred["price_only"],
    })
    os.makedirs(OUT, exist_ok=True)
    pp = os.path.join(OUT, "predictions.parquet")
    out.to_parquet(pp, index=False)
    for f in paths.values():
        os.remove(f)
    os.remove(ypath)
    print(f"[predict] -> {pp} ({time.time() - t0:.0f} s)", flush=True)
    verify(out)


def verify(pred: pd.DataFrame):
    """PREREG 1.1: the refit's sign accuracies at theta = 0.05 must reproduce the published Phase-6 numbers."""
    ref = pd.read_csv(VERIFY_FILE)
    ref = ref[(ref.model == "gbt") & (ref.target == "x")]
    rows, worst = [], 0.0
    for fs_ref, fs_new in (("full", "pred_full"), ("price_only", "pred_price_only")):
        for pg in ("calm", "event", "resolution", "all"):
            r = ref[(ref.feature_set == fs_ref) & (ref.phase_group == pg)]
            if r.empty:
                continue
            m = np.ones(len(pred), bool) if pg == "all" else (pred["phase_group"].to_numpy() == pg)
            sel = m & (np.abs(pred["x"].to_numpy()) >= 0.05) & np.isfinite(pred[fs_new].to_numpy())
            acc = float(np.mean(np.sign(pred[fs_new].to_numpy()[sel]) == np.sign(pred["x"].to_numpy()[sel])))
            pub = float(r["sign_acc_resolvable"].iloc[0]); d = abs(acc - pub)
            worst = max(worst, d)
            rows.append({"feature_set": fs_ref, "phase_group": pg, "n_resolvable": int(sel.sum()),
                         "published": pub, "refit": acc, "abs_diff": d,
                         "n_resolvable_published": int(r["n_resolvable"].iloc[0])})
    tab = pd.DataFrame(rows)
    ok = bool(worst <= VERIFY_TOL)
    doc = {"tolerance": VERIFY_TOL, "worst_abs_diff": worst, "reproduces": ok,
           "source": os.path.relpath(VERIFY_FILE, ROOT), "rows": rows,
           "rule": "PREREG_PHASE_7.md 1.1: the refit must reproduce the published Phase-6 sign accuracies at theta = 0.05 "
                   "to 1e-12; if it does not, the refit is a different construction and theta_info is not computed from it"}
    os.makedirs(OUT, exist_ok=True)
    json.dump(doc, open(os.path.join(OUT, "verify.json"), "w", encoding="utf-8"), indent=1)
    print(tab.to_string(index=False), flush=True)
    print(f"[verify] worst |refit - published| = {worst:.3e} -> {'REPRODUCES' if ok else 'DOES NOT REPRODUCE'}", flush=True)
    return ok


# -------------------------------------------------------------------------------------------------- stage: sweep
def _cluster_ci(stat_by_path, n_paths, n_boot=N_BOOT, seed=0):
    """The audit's percentile cluster bootstrap over paths (evaluation.leakage_audit._cluster_ci), verbatim."""
    if n_paths < 2 or n_boot <= 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    vals = np.empty(n_boot)
    for b in range(n_boot):
        vals[b] = stat_by_path(rng.integers(0, n_paths, n_paths))
    ok = np.isfinite(vals)
    if ok.sum() < 10:
        return (float("nan"), float("nan"))
    return (float(np.percentile(vals[ok], 2.5)), float(np.percentile(vals[ok], 97.5)))


def _acc_rows(sub: pd.DataFrame, label: str, population: str, col: str, feature_set: str):
    x = sub["x"].to_numpy(float); p = sub[col].to_numpy(float)
    path_of = pd.factorize(sub["scenario"].astype(str) + "-" + sub["seed"].astype(str))[0]
    n_paths = int(path_of.max()) + 1 if len(path_of) else 0
    out = []
    for th in THETA_GRID:
        res = (np.abs(x) >= th) & np.isfinite(p)
        n = int(res.sum())
        row = {"scope": label, "population": population, "feature_set": feature_set, "theta": th,
               "n_resolvable": n, "n_rows": int(len(sub)), "n_paths": n_paths,
               "coverage": float(np.mean(np.abs(x) >= th))}
        if n > 10:
            hit = (np.sign(p[res]) == np.sign(x[res])).astype(float)
            row["sign_acc"] = float(hit.mean())
            c_ok = np.bincount(path_of[res], weights=hit, minlength=n_paths)
            c_n = np.bincount(path_of[res], minlength=n_paths).astype(float)

            def boot(idx, c_ok=c_ok, c_n=c_n):
                nn = c_n[idx].sum()
                return float(c_ok[idx].sum() / nn) if nn > 10 else float("nan")
            row["sign_lo"], row["sign_hi"] = _cluster_ci(boot, n_paths)
        else:
            row["sign_acc"] = np.nan; row["sign_lo"] = np.nan; row["sign_hi"] = np.nan
        out.append(row)
    return out


def _sustained(theta, flag, measurable=None, skip_unmeasurable=True):
    """The smallest grid theta at which `flag` is True and stays True at every larger grid value.

    `measurable` marks the grid points where the accuracy could be computed at all (n_resolvable > 10).  The
    pre-registration's text -- "the smallest grid value at which the accuracy is >= 0.80 and stays >= 0.80 at every
    larger grid value" -- is SILENT on a larger grid value where there is no accuracy to compare, and the two
    readings differ on one cell (bull-trap calm; see PREREG_PHASE_7_ADDENDUM.md section 10):

      skip_unmeasurable=True   an unmeasurable point carries no evidence either way and is skipped  -> the PRIMARY
                               reading: a cell with 2 rows at theta = 0.30 must not decide the answer
      skip_unmeasurable=False  an unmeasurable point breaks the chain                               -> reported beside

    Both are computed and both are stored; neither is chosen after seeing which is more convenient, and the only
    two cells where they differ are named in the addendum.
    """
    n = len(flag)
    meas = np.ones(n, bool) if measurable is None else np.asarray(measurable, bool)
    for i in range(n):
        if not (meas[i] and flag[i]):
            continue
        tail = np.arange(i, n)
        if skip_unmeasurable:
            tail = tail[meas[tail]]
        if len(tail) and bool(np.all(flag[tail])) and (not skip_unmeasurable or bool(np.all(meas[tail] | flag[tail]))):
            return float(theta[i])
    return None


def _locate(g: pd.DataFrame):
    """The registered rule (PREREG 1.1): the smallest grid theta at which sign_acc >= 0.80 and stays >= 0.80 at
    every larger grid value.  Returns (theta_info or None, extras).

    `theta_info_ci_lower` beside it is an UNREGISTERED sensitivity added after the sweep was read and disclosed in
    PREREG_PHASE_7_ADDENDUM.md section 1: the same rule applied to the interval's lower end instead of the point
    estimate.  It exists because the registered locator is satisfied on the calm population at a theta where the
    resolvable count has fallen by three orders of magnitude, and a point estimate on 1,089 rows is not the same
    statement as one on 171,916.  It is a sensitivity; it does not replace the registered value anywhere.
    """
    g = g.sort_values("theta").reset_index(drop=True)
    th = g["theta"].to_numpy(float)
    acc = g["sign_acc"].to_numpy(float)
    lo = g["sign_lo"].to_numpy(float)
    meas = np.isfinite(acc)                       # n_resolvable > 10, i.e. an accuracy exists at all
    ok = np.where(meas, acc >= TARGET_ACC, False)
    ok_lo = np.where(np.isfinite(lo), lo >= TARGET_ACC, False)
    reached = _sustained(th, ok, meas, skip_unmeasurable=True)
    reached_strict = _sustained(th, ok, meas, skip_unmeasurable=False)
    reached_ci = _sustained(th, ok_lo, meas, skip_unmeasurable=True)
    j = int(np.nanargmax(acc)) if np.isfinite(acc).any() else -1
    note = ""
    if reached is None:
        note = "not reached"
    elif ok.any() and float(th[int(np.argmax(ok))]) < reached:
        note = f"first crossing at {th[int(np.argmax(ok))]:.2f} reverses; the rule takes the sustained one"
    return reached, {"max_acc": float(acc[j]) if j >= 0 else np.nan,
                     "theta_at_max": float(th[j]) if j >= 0 else np.nan,
                     "n_at_max": int(g["n_resolvable"].iloc[j]) if j >= 0 else 0,
                     "theta_info_ci_lower": reached_ci,
                     "theta_info_unmeasurable_breaks_chain": reached_strict,
                     "n_unmeasurable_grid_points": int((~meas).sum()),
                     "note": note}


def sweep():
    t0 = time.time()
    pred = pd.read_parquet(os.path.join(OUT, "predictions.parquet"))
    rows = []
    for fs_col, fs in (("pred_full", "full"), ("pred_price_only", "price_only")):
        rows += _acc_rows(pred, "pooled", "all", fs_col, fs)
        rows += _acc_rows(pred[pred.phase_group == "calm"], "pooled", "calm", fs_col, fs)
        for sc, g in pred.groupby("scenario"):
            rows += _acc_rows(g, str(sc), "all", fs_col, fs)
            gc = g[g.phase_group == "calm"]
            if len(gc) > 100:
                rows += _acc_rows(gc, str(sc), "calm", fs_col, fs)
    tab = pd.DataFrame(rows)
    tab.to_csv(os.path.join(OUT, "theta_info.csv"), index=False)

    loc = []
    for (scope, pop, fs), g in tab.groupby(["scope", "population", "feature_set"]):
        th, info = _locate(g)
        thc = info.get("theta_info_ci_lower")
        if info.get("theta_info_unmeasurable_breaks_chain") != th:
            info["note"] = (info.get("note") or "") + \
                (" | the two readings of an unmeasurable larger grid point differ here: "
                 f"{th} (skipped, primary) vs {info.get('theta_info_unmeasurable_breaks_chain')} (breaks the chain)")
        loc.append({"scope": scope, "population": pop, "feature_set": fs, "theta_info": th,
                    "reached": th is not None, **info,
                    "coverage_at_theta_info": float(g[g.theta == th]["coverage"].iloc[0]) if th is not None else np.nan,
                    "n_resolvable_at_theta_info": int(g[g.theta == th]["n_resolvable"].iloc[0]) if th is not None else 0,
                    "sign_acc_at_theta_info": float(g[g.theta == th]["sign_acc"].iloc[0]) if th is not None else np.nan,
                    "sign_lo_at_theta_info": float(g[g.theta == th]["sign_lo"].iloc[0]) if th is not None else np.nan,
                    "sign_hi_at_theta_info": float(g[g.theta == th]["sign_hi"].iloc[0]) if th is not None else np.nan,
                    "coverage_at_theta_info_ci": float(g[g.theta == thc]["coverage"].iloc[0]) if thc is not None else np.nan,
                    "n_resolvable_at_theta_info_ci": int(g[g.theta == thc]["n_resolvable"].iloc[0]) if thc is not None else 0})
    locd = pd.DataFrame(loc)
    doc = {"meta": {"grid": list(THETA_GRID), "target_accuracy": TARGET_ACC, "n_boot": N_BOOT,
                    "panel": os.path.relpath(PANEL, ROOT), "state": pin_state(),
                    "rule": "PREREG_PHASE_7.md 1.1: the smallest grid theta at which the level-free observables "
                            "surrogate's sign accuracy on |x| >= theta reaches 0.80 and stays there; 'not reached' is a result",
                    "sensitivity_ci_lower": "theta_info_ci_lower applies the same rule to the interval's lower end; "
                            "UNREGISTERED, added after the sweep was read, disclosed in PREREG_PHASE_7_ADDENDUM.md section 1",
                    "unmeasurable_grid_points": "the registered text is silent on a larger grid value with no "
                            "measurable accuracy (n_resolvable <= 10). PRIMARY reading: skip it, because a cell with "
                            "a handful of rows must not decide the answer. The other reading (it breaks the chain) is "
                            "stored per cell as theta_info_unmeasurable_breaks_chain; the two differ on bull-trap calm "
                            "only. PREREG_PHASE_7_ADDENDUM.md section 10",
                    "caveat": "the derived L2 gates fail (E6.6/E6.7: calm-trained +0.1088 against a registered margin of "
                              "-0.0313, of which Phase 5's ablation puts +0.051 in the wandering multiple). theta_info reads "
                              "the same surrogate, so 'what the agent can resolve' already includes that contribution.",
                    "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "seconds": round(time.time() - t0)},
           "located": loc}
    json.dump(doc, open(os.path.join(OUT, "theta_info.json"), "w", encoding="utf-8"), indent=1, default=float)
    locd.to_csv(os.path.join(OUT, "theta_info_located.csv"), index=False)
    print(locd.to_string(index=False), flush=True)
    print(f"[sweep] -> {OUT} ({time.time() - t0:.0f} s)", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="predict,sweep")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--fit-threads", type=int, default=2)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    for st in a.stages.split(","):
        st = st.strip()
        if st == "predict":
            predict(a.workers, a.fit_threads)
        elif st == "verify":
            verify(pd.read_parquet(os.path.join(OUT, "predictions.parquet")))
        elif st == "sweep":
            sweep()
        else:
            raise SystemExit(f"unknown stage {st!r}")


if __name__ == "__main__":
    main()
