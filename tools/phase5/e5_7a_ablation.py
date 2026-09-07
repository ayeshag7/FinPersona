"""
E5.7(a) -- the per-field-group ablation (PREREG_PHASE_5.md section 3), on a STORED panel.

    python -m tools.phase5.e5_7a_ablation --panel <pkl> --out <dir> [--label NAME] [--stages add,drop,l2b,null]
                                          [--null-groups ANALYST,SENT] [--n-perm 20] [--workers 3]

For each field group G (common.GROUPS) and target y in {x, log V}:
  add-one   dR2_add(G)  = R2(BASE u G) - R2(BASE)      BASE = the audit's level-free control columns
  drop-one  dR2_drop(G) = R2(FULL)     - R2(FULL \\ G)  FULL = BASE u every group
on two populations: P-all (fit + score on all rows) and P-calm (fit + score on calm rows only -- the e3_9
calm-trained construction), with the audit's `gbt` estimator and 5-fold GroupKFold by path, unchanged.  The L2b
macro-phase classifier gets the same two differences in accuracy.  Every interval is a 500-resample percentile
cluster bootstrap over paths from per-path sufficient statistics, and the SAME resample indices are used for every
feature set, so differences carry paired intervals.

`--stages null` computes the permutation null margin of dR2_add(G) for the groups named: G's columns (field +
lags) are permuted ACROSS PATHS as whole blocks (within-path structure preserved, the link to the path's x broken),
N_PERM times; the margin is the maximum (the 19th-20th order statistic estimates the 95th percentile at 20 draws,
and its resolution is stated).

The panel must be the state it claims to be (P4-19): the caller passes `--label` and the tool records the deployed
configuration it ran under; a Phase-5 arm panel is built by tools/phase5/e5_panels.py, which pins its overrides.

Output: <out>/ablation.{json,md}, <out>/_prepared.pkl (the lagged frame, for the null stage and re-runs)
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

from tools.phase5.common import GEN, GROUPS, encode_nm, shown_fields_of, pin_state  # noqa: E402

THETA = 0.05
N_BOOT = 500
BOOT_SEED = 550001


# ------------------------------------------------------------------------------------------ feature sets
def feature_sets(cols, ctrl_cols):
    """{name: columns} for BASE, BASE+G, FULL, FULL-G, plus the raw group column lists."""
    def gcols(g):
        keys = set(GROUPS[g])
        return [c for c in cols if c.split("_lag")[0] in keys]
    groups = {g: gcols(g) for g in GROUPS}
    groups = {g: v for g, v in groups.items() if v}          # a group absent from the panel is skipped
    base = list(ctrl_cols)
    full = base + [c for g in groups for c in groups[g] if c not in base]
    sets = {"BASE": base, "FULL": full}
    for g, gc in groups.items():
        sets[f"BASE+{g}"] = base + [c for c in gc if c not in base]
        sets[f"FULL-{g}"] = [c for c in full if c not in set(gc)]
    return sets, groups


# ------------------------------------------------------------------------------------------ one job
def _job(args):
    """One (feature set, target, population) fit: returns per-path sufficient statistics for the bootstrap."""
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
    if perm is not None:
        # block permutation across paths of the permuted columns: path p receives path perm[p]'s block.  All
        # paths have the same row count after the audit's dropna (T - 20), so the swap is a clean re-index.
        pcols = [i for i, c in enumerate(fcols) if c in set(perm["cols"])]
        order = np.argsort(path_of, kind="stable")
        rows_by_path = np.split(order, np.cumsum(np.bincount(path_of, minlength=n_paths))[:-1])
        src = np.asarray(perm["perm"])
        Xp = X.copy()
        for p in range(n_paths):
            a, b = rows_by_path[p], rows_by_path[src[p]]
            n = min(len(a), len(b))
            Xp[np.ix_(a[:n], pcols)] = X[np.ix_(b[:n], pcols)]
            if len(a) > n:
                Xp[np.ix_(a[n:], pcols)] = X[np.ix_(np.repeat(b[-1], len(a) - n), pcols)]
        X = Xp
    out = {"name": name, "target": target, "pop": pop, "n_rows": int(len(d)), "n_paths": n_paths,
           "n_cols": len(fcols), "perm": (perm["k"] if perm else None)}
    t0 = time.time()
    if target == "macro":
        from sklearn.ensemble import HistGradientBoostingClassifier
        from sklearn.model_selection import GroupKFold, cross_val_predict
        y = d["macro"].to_numpy(dtype=object)
        cv = GroupKFold(n_splits=min(5, len(np.unique(groups))))
        pred = cross_val_predict(HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, max_depth=4,
                                                                random_state=0), X, y, cv=cv, groups=groups)
        hit = (pred == y).astype(float)
        out["stats"] = {"hit": np.bincount(path_of, weights=hit, minlength=n_paths).tolist(),
                        "cnt": np.bincount(path_of, minlength=n_paths).astype(float).tolist()}
        out["acc"] = float(hit.mean())
    else:
        y = d["x"].to_numpy(float) if target == "x" else np.log(d["V"].to_numpy(float))
        p = _oos_predictions(X, y, groups, _models()["gbt"])
        ok = np.isfinite(p)
        cnt = np.bincount(path_of[ok], minlength=n_paths).astype(float)
        out["stats"] = {"cnt": cnt.tolist(),
                        "sy": np.bincount(path_of[ok], weights=y[ok], minlength=n_paths).tolist(),
                        "syy": np.bincount(path_of[ok], weights=y[ok] ** 2, minlength=n_paths).tolist(),
                        "sres": np.bincount(path_of[ok], weights=(y[ok] - p[ok]) ** 2, minlength=n_paths).tolist()}
        ss = ((y[ok] - y[ok].mean()) ** 2).sum()
        out["R2"] = float(1 - ((y[ok] - p[ok]) ** 2).sum() / ss)
        if target == "x":
            res = ok & (np.abs(y) >= THETA)
            out["sign_acc"] = float(np.mean(np.sign(p[res]) == np.sign(y[res]))) if res.sum() > 10 else None
            out["stats"]["c_ok"] = np.bincount(path_of[res], weights=(np.sign(p[res]) == np.sign(y[res])).astype(float),
                                               minlength=n_paths).tolist()
            out["stats"]["c_n"] = np.bincount(path_of[res], minlength=n_paths).astype(float).tolist()
        else:
            ape = np.abs(np.exp(p[ok]) - np.exp(y[ok])) / np.exp(y[ok])
            out["MAPE_V"] = float(ape.mean())
            out["stats"]["s_ape"] = np.bincount(path_of[ok], weights=ape, minlength=n_paths).tolist()
    out["seconds"] = round(time.time() - t0, 1)
    return out


# ------------------------------------------------------------------------------------------ bootstrap
def _boot_idx(n_paths, n_boot=N_BOOT, seed=BOOT_SEED):
    rng = np.random.default_rng(seed)
    return rng.integers(0, n_paths, (n_boot, n_paths))


def r2_draws(st, idx):
    cnt, sy, syy, sres = (np.asarray(st[k]) for k in ("cnt", "sy", "syy", "sres"))
    out = np.empty(len(idx))
    for b, ix in enumerate(idx):
        n = cnt[ix].sum()
        ss = syy[ix].sum() - sy[ix].sum() ** 2 / n
        out[b] = 1 - sres[ix].sum() / ss if (n >= 30 and ss > 0) else np.nan
    return out


def acc_draws(st, idx):
    hit, cnt = np.asarray(st["hit"]), np.asarray(st["cnt"])
    return np.array([hit[ix].sum() / cnt[ix].sum() for ix in idx])


def mape_draws(st, idx):
    s, cnt = np.asarray(st["s_ape"]), np.asarray(st["cnt"])
    return np.array([s[ix].sum() / cnt[ix].sum() for ix in idx])


def ci(v):
    v = v[np.isfinite(v)]
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if len(v) >= 10 else [None, None]


# ------------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    ap.add_argument("--stages", default="add,drop,l2b")
    ap.add_argument("--null-groups", default="ANALYST,SENT")
    ap.add_argument("--n-perm", type=int, default=20)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--targets", default="x,logV")
    ap.add_argument("--pops", default="all,calm")
    ap.add_argument("--groups", default=None, help="comma list: restrict add-one/drop-one to these groups (arms)")
    ap.add_argument("--reuse-base", default=None, help="an ablation.json whose BASE fits are reused if this panel's BASE "
                                                        "feature matrix hashes identically (post-hoc arms share the hidden path)")
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(a.out, exist_ok=True)
    state = pin_state()
    stages = [s.strip() for s in a.stages.split(",")]
    targets = [s.strip() for s in a.targets.split(",")]
    pops = [s.strip() for s in a.pops.split(",")]

    from evaluation.leakage_audit import _prepare
    panel = encode_nm(pd.read_pickle(a.panel))
    shown = shown_fields_of(panel)
    dfl, full_cols, ctrl_cols = _prepare(panel, shown, "level_free")
    dfl["_path"] = (dfl["scenario"].astype(str) + "-" + dfl["seed"].astype(str)).to_numpy(dtype=object)
    dfl["_path_idx"] = pd.factorize(pd.Series(dfl["_path"]))[0]
    all_cols = sorted(set(full_cols) | set(ctrl_cols), key=lambda c: (c.split("_lag")[0], c))
    sets, groups = feature_sets(all_cols, ctrl_cols)
    if a.groups:
        keep = set(x.strip() for x in a.groups.split(","))
        groups = {g: v for g, v in groups.items() if g in keep}
    prep = os.path.join(a.out, "_prepared.pkl")
    keep = sorted(set(c for v in sets.values() for c in v)) + ["x", "V", "macro", "_path", "_path_idx"]
    dfl[keep].to_pickle(prep)
    n_paths = int(dfl["_path_idx"].max()) + 1
    print(f"[panel] {os.path.relpath(a.panel, ROOT)}: {len(panel)} rows -> {len(dfl)} modelled, {n_paths} paths; "
          f"shown {len(shown)} fields; groups {list(groups)}; BASE {len(sets['BASE'])} cols, FULL {len(sets['FULL'])}",
          flush=True)

    import hashlib
    base_hash = hashlib.sha256(np.ascontiguousarray(dfl[sorted(sets["BASE"])].to_numpy(float)).tobytes()
                               + dfl["x"].to_numpy(float).tobytes() + dfl["V"].to_numpy(float).tobytes()).hexdigest()[:16]
    jp = os.path.join(a.out, "ablation.json")
    res = json.load(open(jp, encoding="utf-8")) if os.path.exists(jp) else {}
    res["base_hash"] = base_hash
    if a.reuse_base and os.path.exists(a.reuse_base):
        src = json.load(open(a.reuse_base, encoding="utf-8"))
        if src.get("base_hash") == base_hash:
            n_re = 0
            for k, v in src.get("fits", {}).items():
                if k.startswith("BASE|") and "|perm" not in k and k not in res.setdefault("fits", {}):
                    res["fits"][k] = dict(v); res["fits"][k]["reused_from"] = os.path.relpath(a.reuse_base, ROOT); n_re += 1
            print(f"[reuse] BASE feature matrix identical to {os.path.relpath(a.reuse_base, ROOT)} (hash {base_hash}); "
                  f"{n_re} BASE fits reused", flush=True)
        else:
            print(f"[reuse] BASE hash differs ({base_hash} vs {src.get('base_hash')}); BASE refitted", flush=True)
    res.update({"what": "E5.7(a): per-field-group ablation (PREREG_PHASE_5.md section 3)", "label": a.label,
                "panel": os.path.relpath(a.panel, ROOT), "state": state, "shown_fields": shown,
                "groups": {g: GROUPS[g] for g in groups}, "n_rows_modelled": int(len(dfl)), "n_paths": n_paths,
                "estimator": "leakage_audit._models()['gbt'] (HistGradientBoosting 200/0.08/6), 5-fold GroupKFold by path; "
                             "L2b: HistGradientBoostingClassifier 200/0.1/4", "n_boot": N_BOOT, "boot_seed": BOOT_SEED})
    res.setdefault("fits", {})

    def key(name, target, pop, perm=None):
        return f"{name}|{target}|{pop}" + (f"|perm{perm}" if perm is not None else "")

    jobs = []
    if "add" in stages or "drop" in stages:
        # FULL is needed for drop-one only; a group-restricted add-one run (an arm) fits BASE and BASE+G alone
        names = ["BASE"] + (["FULL"] if ("drop" in stages or not a.groups) else [])
        if "add" in stages:
            names += [f"BASE+{g}" for g in groups]
        if "drop" in stages:
            names += [f"FULL-{g}" for g in groups]
        for name in names:
            for t in targets:
                for p in pops:
                    if key(name, t, p) not in res["fits"]:
                        jobs.append((prep, name, sets[name], t, p, None))
    if "l2b" in stages:
        for name in ["BASE", "FULL"] + [f"BASE+{g}" for g in groups] + [f"FULL-{g}" for g in groups]:
            if key(name, "macro", "all") not in res["fits"]:
                jobs.append((prep, name, sets[name], "macro", "all", None))
    if "null" in stages:
        rng = np.random.default_rng(560001)
        for g in [s.strip() for s in a.null_groups.split(",") if s.strip() in groups]:
            for k in range(a.n_perm):
                perm = {"k": k, "cols": groups[g], "perm": rng.permutation(n_paths).tolist()}
                if key(f"BASE+{g}", "x", "all", k) not in res["fits"]:
                    jobs.append((prep, f"BASE+{g}", sets[f"BASE+{g}"], "x", "all", perm))
    # heaviest first so the pool stays busy at the end
    jobs.sort(key=lambda j: -len(j[2]))
    print(f"[fits] {len(jobs)} jobs on {a.workers} workers", flush=True)

    def save():
        json.dump(res, open(jp, "w", encoding="utf-8"), indent=1, default=str)

    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for r in ex.map(_job, jobs, chunksize=1):
            res["fits"][key(r["name"], r["target"], r["pop"], r["perm"])] = r
            print(f"    {r['name']:14s} {r['target']:5s} {r['pop']:4s}" + (f" perm{r['perm']}" if r["perm"] is not None else "")
                  + f"  R2 {r.get('R2', r.get('acc', float('nan'))):+.4f}  ({r['seconds']} s)", flush=True)
            save()

    # ---------------------------------------------------------------- tables with paired intervals
    idx = _boot_idx(n_paths)
    draws = {}
    for k, r in res["fits"].items():
        if r["target"] == "macro":
            draws[k] = acc_draws(r["stats"], idx)
        else:
            draws[k] = r2_draws(r["stats"], idx)
    tables = {}
    for t in targets + (["macro"] if "l2b" in stages else []):
        for p in (pops if t != "macro" else ["all"]):
            kb, kf = key("BASE", t, p), key("FULL", t, p)
            if kb not in draws:
                continue
            # FULL exists only when drop-one ran (an arm's group-restricted add-one run fits BASE and BASE+G alone)
            tab = {"BASE": {"value": res["fits"][kb].get("R2", res["fits"][kb].get("acc")), "ci": ci(draws[kb])},
                   "FULL": ({"value": res["fits"][kf].get("R2", res["fits"][kf].get("acc")), "ci": ci(draws[kf])}
                            if kf in draws else None),
                   "groups": {}}
            for g in groups:
                row = {}
                ka, kd = key(f"BASE+{g}", t, p), key(f"FULL-{g}", t, p)
                if ka in draws:
                    d = draws[ka] - draws[kb]
                    row["add_one"] = {"delta": float(res["fits"][ka].get("R2", res["fits"][ka].get("acc")) - tab["BASE"]["value"]),
                                      "ci": ci(d), "value": res["fits"][ka].get("R2", res["fits"][ka].get("acc"))}
                if kd in draws and kf in draws:
                    d = draws[kf] - draws[kd]
                    row["drop_one"] = {"delta": float(tab["FULL"]["value"] - res["fits"][kd].get("R2", res["fits"][kd].get("acc"))),
                                       "ci": ci(d), "value": res["fits"][kd].get("R2", res["fits"][kd].get("acc"))}
                if t == "logV" and ka in res["fits"]:
                    row["add_one"]["MAPE_V"] = res["fits"][ka].get("MAPE_V")
                    row["add_one"]["MAPE_V_base"] = res["fits"][kb].get("MAPE_V")
                tab["groups"][g] = row
            tables[f"{t}|{p}"] = tab
    res["tables"] = tables
    nulls = {}
    for g in groups:
        ks = [k for k in res["fits"] if k.startswith(f"BASE+{g}|x|all|perm")]
        if ks:
            kb = key("BASE", "x", "all")
            vals = sorted(float(res["fits"][k]["R2"] - res["fits"][kb]["R2"]) for k in ks)
            nulls[g] = {"n_perm": len(vals), "draws": vals, "max": vals[-1],
                        "p95_estimate": float(np.percentile(vals, 95)) if len(vals) >= 20 else vals[-1],
                        "resolution": "the 95th percentile of n draws is the max for n < 20; with 20 draws it is "
                                      "between the 19th and 20th order statistic"}
    res["null_margins"] = nulls
    res["seconds"] = round(time.time() - t0, 1)
    save()

    # ---------------------------------------------------------------- markdown
    L = [f"# E5.7(a) per-field-group ablation -- {a.label or os.path.basename(a.out)}", "",
         f"Panel `{res['panel']}`: {res['n_paths']} paths, {res['n_rows_modelled']} modelled rows; estimator "
         f"{res['estimator']}; {N_BOOT}-resample paired cluster bootstrap over paths. State: "
         + ", ".join(f"{k}={v}" for k, v in state.items() if k != "observables") + ".", ""]
    for tk, tab in tables.items():
        t, p = tk.split("|")
        lab = {"x": "R2(x)", "logV": "R2(log V)", "macro": "L2b macro-class accuracy"}[t]
        L += [f"## {lab}, population {p.upper()}", "",
              f"BASE (level-free control) {tab['BASE']['value']:+.4f} [{tab['BASE']['ci'][0]:+.4f}, {tab['BASE']['ci'][1]:+.4f}]"
              + (f"; FULL {tab['FULL']['value']:+.4f} [{tab['FULL']['ci'][0]:+.4f}, {tab['FULL']['ci'][1]:+.4f}]." if tab["FULL"] else "."), "",
              "| group | add-one delta [paired CI] | drop-one delta [paired CI] |" + (" MAPE(V) base -> +G |" if t == "logV" else ""),
              "|---|---|---|" + ("---|" if t == "logV" else "")]
        for g, row in tab["groups"].items():
            def f(x):
                return "n/a" if not x else f"{x['delta']:+.4f} [{x['ci'][0]:+.4f}, {x['ci'][1]:+.4f}]"
            line = f"| {g} | {f(row.get('add_one'))} | {f(row.get('drop_one'))} |"
            if t == "logV" and row.get("add_one"):
                line += f" {row['add_one'].get('MAPE_V_base', float('nan')):.4f} -> {row['add_one'].get('MAPE_V', float('nan')):.4f} |"
            L.append(line)
        L.append("")
    if nulls:
        L += ["## Permutation null margins of dR2_add(x, P-all)", "", "| group | n perm | max | p95 estimate | draws |",
              "|---|---|---|---|---|"]
        for g, v in nulls.items():
            L.append(f"| {g} | {v['n_perm']} | {v['max']:+.5f} | {v['p95_estimate']:+.5f} | "
                     f"{', '.join(f'{d:+.5f}' for d in v['draws'])} |")
        L.append("")
    with open(os.path.join(a.out, "ablation.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"wrote {jp} in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
