"""
v2.1 Phase 6 -- E6.6 / E6.7: the target-permutation nulls of the L2 selectivity and the L2b phase-clock
selectivity, simulated with the real estimator on the real panel at the intended n (rule 11; P5-16).

Plan Section 10.2: "the gate = selectivity of the non-price fields over the level-free control <= the 95th
percentile of a label-permutation null (paths' targets permuted across seeds) plus the sampling half-width";
E6.7: "the 10 pp margin replaced by the same null-derived margin".

The null.  Each path's TARGET series (x for L2; the macro label vector for L2b) is swapped, whole, with
another path's (the construction `leakage_audit.l2_surrogate` already uses for its shuffled-V control): every
feature keeps its own within-path structure, every target keeps its own shape, and the link between them is
broken for BOTH feature sets.  Under this null neither the level-free control nor the full set carries
information about the target, so the selectivity (full minus control) is pure fitting noise -- its 95th
percentile is the margin a real selectivity has to clear before it can be called information.  Located before
the rule is written: Phase 5's column-permutation null sat at the COST of noise columns (negative), and a rule
written around a proxy was on the wrong side of zero (PREREG_PHASE_5_ADDENDUM section 6).

Both feature sets are refitted per draw (the control's fit under a permuted target is not the same as under the
real one), so one draw of the L2 null is two GBT regressions per population and one draw of the L2b null is two
GBT classifications.  With `--n-perm 20` the 95th percentile lies between the 19th and 20th order statistic,
and the resolution is stated in the output (the e5_7a convention).

The measured selectivities and their paired cluster-bootstrap half-widths come from the UNPERMUTED fits, which
are reused from an `e5_7a`-style ablation.json when its `base_hash` matches (the FULL and BASE fits of
`e5_7a/final/ablation.json` are the Phase-5 state's), and fitted here otherwise.

Everything is written after every fit, so the run is resumable (rule 14) and can be split across machines
(a `--perm-range a:b` on the box, the rest here; the JSONs merge by key).

Usage:
    python -u tools/phase6/e6_6_null.py --panel docs/env_v2/generated/v2_1/_panels/sep_phase5_after.pkl \
        --out docs/env_v2/generated/v2_1/e6_6/null --n-perm 20 --workers 3 [--stages l2,l2b] [--pops all,calm]
        [--reuse-fits docs/env_v2/generated/v2_1/e5_7a/final/ablation.json] [--perm-range 0:20]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

from tools.phase5.common import GEN, encode_nm, pin_state, shown_fields_of  # noqa: E402
from tools.phase5.e5_7a_ablation import (  # noqa: E402  -- the same bootstrap draws and sufficient statistics
    BOOT_SEED, N_BOOT, _boot_idx, acc_draws, ci, feature_sets, r2_draws,
)

THETA = 0.05
PERM_SEED = 660001


# ------------------------------------------------------------------------------------------ one job
def _job(args):
    """One (feature set, target, population, permutation) fit -> per-path sufficient statistics."""
    import warnings
    warnings.filterwarnings("ignore")
    os.environ["OMP_NUM_THREADS"] = "2"
    from evaluation.leakage_audit import _models, _oos_predictions
    prep_path, name, fcols, target, pop, perm = args
    d = pd.read_pickle(prep_path)
    if pop == "calm":
        d = d.loc[d["macro"].to_numpy() == "calm"].reset_index(drop=True)
    groups = d["_path"].to_numpy()
    path_of = d["_path_idx"].to_numpy()
    n_paths = int(d["_path_idx"].max()) + 1
    X = d[fcols].to_numpy(float)
    out = {"name": name, "target": target, "pop": pop, "n_rows": int(len(d)), "n_paths": n_paths,
           "n_cols": len(fcols), "perm": (perm["k"] if perm else None)}
    t0 = time.time()

    def permute_target(y):
        # path p receives path perm[p]'s target series (whole); lengths differ only by the calm mask, in which
        # case the shorter one is padded with its last value -- l2_surrogate's construction, unchanged
        order = np.argsort(path_of, kind="stable")
        rows_by_path = np.split(order, np.cumsum(np.bincount(path_of, minlength=n_paths))[:-1])
        src = np.asarray(perm["perm"])
        yp = y.copy()
        for p in range(n_paths):
            a_, b_ = rows_by_path[p], rows_by_path[src[p]]
            if len(b_) == 0:
                continue
            n = min(len(a_), len(b_))
            yp[a_[:n]] = y[b_[:n]]
            if len(a_) > n:
                yp[a_[n:]] = y[b_[-1]]
        return yp

    if target == "macro":
        from sklearn.ensemble import HistGradientBoostingClassifier
        from sklearn.model_selection import GroupKFold, cross_val_predict
        y = d["macro"].to_numpy(dtype=object)
        if perm is not None:
            codes, uniq = pd.factorize(pd.Series(y))
            # pandas 3 returns an Arrow-backed Index here, which pyarrow will not index with an array: materialise it
            y = np.asarray(uniq, dtype=object)[permute_target(codes.astype(int))]
        cv = GroupKFold(n_splits=min(5, len(np.unique(groups))))
        pred = cross_val_predict(HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, max_depth=4,
                                                                random_state=0), X, y, cv=cv, groups=groups)
        hit = (pred == y).astype(float)
        out["stats"] = {"hit": np.bincount(path_of, weights=hit, minlength=n_paths).tolist(),
                        "cnt": np.bincount(path_of, minlength=n_paths).astype(float).tolist()}
        out["acc"] = float(hit.mean())
    else:
        y = d["x"].to_numpy(float)
        if perm is not None:
            y = permute_target(y)
        p = _oos_predictions(X, y, groups, _models()["gbt"])
        ok = np.isfinite(p)
        out["stats"] = {"cnt": np.bincount(path_of[ok], minlength=n_paths).astype(float).tolist(),
                        "sy": np.bincount(path_of[ok], weights=y[ok], minlength=n_paths).tolist(),
                        "syy": np.bincount(path_of[ok], weights=y[ok] ** 2, minlength=n_paths).tolist(),
                        "sres": np.bincount(path_of[ok], weights=(y[ok] - p[ok]) ** 2, minlength=n_paths).tolist()}
        ss = ((y[ok] - y[ok].mean()) ** 2).sum()
        out["R2"] = float(1 - ((y[ok] - p[ok]) ** 2).sum() / ss)
    out["seconds"] = round(time.time() - t0, 1)
    return out


def key(name, target, pop, perm=None):
    return f"{name}|{target}|{pop}" + (f"|perm{perm}" if perm is not None else "")


# ------------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    ap.add_argument("--stages", default="l2,l2b")
    ap.add_argument("--pops", default="all,calm")
    ap.add_argument("--n-perm", type=int, default=20)
    ap.add_argument("--perm-range", default=None, help="a:b -- only draws a..b-1 (to split a run across machines)")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--reuse-fits", default=os.path.join(GEN, "e5_7a", "final", "ablation.json"))
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(a.out, exist_ok=True)
    state = pin_state()
    stages = [s.strip() for s in a.stages.split(",")]
    pops = [s.strip() for s in a.pops.split(",")]

    from evaluation.leakage_audit import _prepare
    panel = encode_nm(pd.read_pickle(a.panel))
    shown = shown_fields_of(panel)
    dfl, full_cols, ctrl_cols = _prepare(panel, shown, "level_free")
    dfl["_path"] = (dfl["scenario"].astype(str) + "-" + dfl["seed"].astype(str)).to_numpy(dtype=object)
    dfl["_path_idx"] = pd.factorize(pd.Series(dfl["_path"]))[0]
    all_cols = sorted(set(full_cols) | set(ctrl_cols), key=lambda c: (c.split("_lag")[0], c))
    sets, groups = feature_sets(all_cols, ctrl_cols)
    prep = os.path.join(a.out, "_prepared.pkl")
    keep = sorted(set(sets["BASE"]) | set(sets["FULL"])) + ["x", "V", "macro", "_path", "_path_idx"]
    dfl[keep].to_pickle(prep)
    n_paths = int(dfl["_path_idx"].max()) + 1
    base_hash = hashlib.sha256(np.ascontiguousarray(dfl[sorted(sets["BASE"])].to_numpy(float)).tobytes()
                               + dfl["x"].to_numpy(float).tobytes() + dfl["V"].to_numpy(float).tobytes()).hexdigest()[:16]
    print(f"[panel] {os.path.relpath(a.panel, ROOT)}: {len(panel)} rows -> {len(dfl)} modelled, {n_paths} paths; "
          f"BASE {len(sets['BASE'])} cols, FULL {len(sets['FULL'])}; base_hash {base_hash}", flush=True)

    jp = os.path.join(a.out, "null.json")
    res = json.load(open(jp, encoding="utf-8")) if os.path.exists(jp) else {}
    res.setdefault("fits", {})
    res.update({"what": "E6.6/E6.7: target-permutation nulls of the L2 selectivity and the L2b phase-clock selectivity",
                "label": a.label, "panel": os.path.relpath(a.panel, ROOT), "state": state, "base_hash": base_hash,
                "n_paths": n_paths, "n_rows_modelled": int(len(dfl)), "shown_fields": shown,
                "estimator": "leakage_audit._models()['gbt'] (HistGradientBoosting), 5-fold GroupKFold by path; "
                             "L2b: HistGradientBoostingClassifier 200/0.1/4", "n_boot": N_BOOT, "boot_seed": BOOT_SEED,
                "perm_seed": PERM_SEED, "n_perm": a.n_perm})

    # unpermuted fits: reuse when the state is the same (hash), else fit
    if a.reuse_fits and os.path.exists(a.reuse_fits):
        src = json.load(open(a.reuse_fits, encoding="utf-8"))
        if src.get("base_hash") == base_hash:
            n_re = 0
            for k, v in src.get("fits", {}).items():
                nm, tg, pp = k.split("|")[:3]
                if nm in ("BASE", "FULL") and "|perm" not in k and tg in ("x", "macro") and k not in res["fits"]:
                    res["fits"][k] = dict(v); res["fits"][k]["reused_from"] = os.path.relpath(a.reuse_fits, ROOT); n_re += 1
            print(f"[reuse] {n_re} unpermuted fits reused from {os.path.relpath(a.reuse_fits, ROOT)}", flush=True)
        else:
            print(f"[reuse] base hash differs ({base_hash} vs {src.get('base_hash')}): unpermuted fits refitted", flush=True)

    rng = np.random.default_rng(PERM_SEED)
    perms = [rng.permutation(n_paths).tolist() for _ in range(a.n_perm)]   # the same draws whatever the range
    lo, hi = (0, a.n_perm) if not a.perm_range else tuple(int(v) for v in a.perm_range.split(":"))
    jobs = []
    if "l2" in stages:
        for pop in pops:
            for nm in ("BASE", "FULL"):
                if key(nm, "x", pop) not in res["fits"]:
                    jobs.append((prep, nm, sets[nm], "x", pop, None))
                for k in range(lo, hi):
                    if key(nm, "x", pop, k) not in res["fits"]:
                        jobs.append((prep, nm, sets[nm], "x", pop, {"k": k, "perm": perms[k]}))
    if "l2b" in stages:
        for nm in ("BASE", "FULL"):
            if key(nm, "macro", "all") not in res["fits"]:
                jobs.append((prep, nm, sets[nm], "macro", "all", None))
            for k in range(lo, hi):
                if key(nm, "macro", "all", k) not in res["fits"]:
                    jobs.append((prep, nm, sets[nm], "macro", "all", {"k": k, "perm": perms[k]}))
    jobs.sort(key=lambda j: -len(j[2]))
    print(f"[fits] {len(jobs)} jobs on {a.workers} workers", flush=True)

    def save():
        json.dump(res, open(jp, "w", encoding="utf-8"), indent=1, default=str)

    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for r in ex.map(_job, jobs, chunksize=1):
            res["fits"][key(r["name"], r["target"], r["pop"], r["perm"])] = r
            print(f"    {r['name']:5s} {r['target']:5s} {r['pop']:4s}" + (f" perm{r['perm']:>3}" if r["perm"] is not None else "     ")
                  + f"  {'R2' if 'R2' in r else 'acc'} {r.get('R2', r.get('acc', float('nan'))):+.4f}  ({r['seconds']} s)", flush=True)
            save()

    # ------------------------------------------------------------------ the nulls and the derived margins
    idx = _boot_idx(n_paths)
    summary = {}
    for tg, pops_t in (("x", pops), ("macro", ["all"])):
        if (tg == "x" and "l2" not in stages) or (tg == "macro" and "l2b" not in stages):
            continue
        for pop in pops_t:
            kb, kf = key("BASE", tg, pop), key("FULL", tg, pop)
            if kb not in res["fits"] or kf not in res["fits"]:
                continue
            fb, ff = res["fits"][kb], res["fits"][kf]
            val = (lambda r: r.get("R2", r.get("acc")))
            draws_b = r2_draws(fb["stats"], idx) if tg == "x" else acc_draws(fb["stats"], idx)
            draws_f = r2_draws(ff["stats"], idx) if tg == "x" else acc_draws(ff["stats"], idx)
            d = draws_f - draws_b
            sel = float(val(ff) - val(fb))
            sel_ci = ci(d)
            half = float((sel_ci[1] - sel_ci[0]) / 2.0) if sel_ci[0] is not None else None
            nulls = []
            for k in range(a.n_perm):
                a_, b_ = key("FULL", tg, pop, k), key("BASE", tg, pop, k)
                if a_ in res["fits"] and b_ in res["fits"]:
                    nulls.append(float(val(res["fits"][a_]) - val(res["fits"][b_])))
            nulls_sorted = sorted(nulls)
            blk = {"measured_selectivity": sel, "selectivity_ci95_paired": sel_ci, "sampling_halfwidth": half,
                   "base_value": val(fb), "full_value": val(ff),
                   "null": {"n_draws": len(nulls), "draws": nulls_sorted,
                            "median": float(np.median(nulls)) if nulls else None,
                            "p95": (float(np.percentile(nulls_sorted, 95)) if len(nulls) >= 20 else (nulls_sorted[-1] if nulls else None)),
                            "max": nulls_sorted[-1] if nulls else None,
                            "resolution": "with n < 20 draws the 95th percentile is the maximum; with 20 it lies between "
                                          "the 19th and 20th order statistic",
                            "base_under_null": [float(val(res["fits"][key("BASE", tg, pop, k)])) for k in range(a.n_perm) if key("BASE", tg, pop, k) in res["fits"]],
                            "full_under_null": [float(val(res["fits"][key("FULL", tg, pop, k)])) for k in range(a.n_perm) if key("FULL", tg, pop, k) in res["fits"]]}}
            if blk["null"]["p95"] is not None and half is not None:
                blk["derived_margin"] = float(blk["null"]["p95"] + half)
                blk["verdict_under_derived_margin"] = bool(sel <= blk["derived_margin"])
                blk["rule"] = "selectivity <= null p95 + sampling half-width (plan 10.2, E6.6/E6.7)"
            summary[f"{tg}|{pop}"] = blk
    res["summary"] = summary
    res["seconds"] = round(time.time() - t0, 1)
    save()

    # ------------------------------------------------------------------ markdown
    L = [f"# E6.6 / E6.7 — target-permutation nulls of the L2 and L2b selectivities — {a.label or os.path.basename(a.out)}", "",
         f"Panel `{res['panel']}`: {n_paths} paths, {res['n_rows_modelled']} modelled rows; {res['estimator']}; "
         f"{a.n_perm} target permutations (seed {PERM_SEED}); {N_BOOT}-resample paired cluster bootstrap over paths for the "
         f"measured selectivity. State: " + ", ".join(f"{k}={v}" for k, v in state.items() if k != "observables") + ".", "",
         "| statistic | population | control | full | measured selectivity [paired CI] | half-width | null median | null p95 | draws | derived margin | verdict |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, b in summary.items():
        tg, pop = k.split("|")
        nm = "L2 R²(x) selectivity" if tg == "x" else "L2b macro-class accuracy selectivity"
        n = b["null"]
        L.append(f"| {nm} | {pop} | {b['base_value']:+.4f} | {b['full_value']:+.4f} | {b['measured_selectivity']:+.4f} "
                 f"[{b['selectivity_ci95_paired'][0]:+.4f}, {b['selectivity_ci95_paired'][1]:+.4f}] | {b['sampling_halfwidth']:.4f} | "
                 f"{n['median']:+.4f} | {n['p95']:+.4f} | {n['n_draws']} | "
                 + (f"{b['derived_margin']:+.4f}" if "derived_margin" in b else "—") + " | "
                 + (("**PASS**" if b["verdict_under_derived_margin"] else "**FAIL**") if "derived_margin" in b else "—") + " |")
    L += ["", "The null's location is reported before the rule that uses it is final (rule 11): a null median far from zero "
              "means the selectivity statistic is biased under no information, and the margin absorbs that bias only if it "
              "is derived from this null rather than stated.", ""]
    with open(os.path.join(a.out, "null.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "null"} | {"null_p95": v["null"]["p95"], "null_median": v["null"]["median"], "n_draws": v["null"]["n_draws"]}
                      for k, v in summary.items()}, indent=1))
    print(f"-> {a.out} ({res['seconds']} s)")


if __name__ == "__main__":
    main()
