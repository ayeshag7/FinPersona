"""
E4.5 (PREREG_PHASE_4.md section 7; REG-7): the sustained-bull control, all four definitions implemented, run
and audited under one pre-registration.

    python -m tools.phase4.e4_5_control [--seeds 500] [--workers 3]

**No definition is adopted here.** D14 is open and the purpose of the control is the team's to state; what
Phase 4 delivers is the four audits per definition so the team decides on numbers.

  A  same mispricing process as flat, no x-band; validity on V only (V_T/V_1 >= a FIT threshold)
  B  band on V only, mania driver off -- identical x dynamics to A, a different rejection log
  C  the anchored x of v2 (d_t = -0.15 x), recorded for completeness
  D  rendered-matched: the flat x process with a rising V, labelled calm so no phase multiplier applies

Audits:
  (i)   the realised x distribution (path-mean P10/P50/P90, realised sd(x))
  (ii)  SELECTION: two-sample KS between ACCEPTED and REJECTED paths on daily sd, ACF(1) and IV, as an
        EQUIVALENCE test on the bootstrap 95 % UPPER limit (< 0.10) -- never "the test did not reject".
        Registered in advance: if fewer than 30 paths are rejected the test is VACUOUS and is reported as
        "no selection is possible by construction", NOT as a pass.  That is the expected branch for A/B/D and
        is stated before the run so it cannot look like an after-the-fact reading.
  (iii) DISCRIMINATION: a day-level classifier of sustained-bull vs flat on demeaned, level-free returns,
        against a label-permutation null computed HERE.  The permutation is over SEED labels, not day labels:
        days within a path share a schedule draw, and permuting days gives a null p95 of about 0.503 that
        would call almost any classifier a leak (e4_0/power.json PP4).
  (iv)  the acceptance test at baseline level is reported per definition in REG-7's own form.

The classifier is a MODEL FIT, so this stage runs on the reference machine only -- never offloaded.

Output: docs/env_v2/generated/v2_1/e4_5/{control.json, control.md}
"""
from __future__ import annotations

import argparse
import json
import math
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
OUT = os.path.join(GEN, "e4_5")
SEED_SB = 250000
SEED_FLAT = 251000
DEFS = ("A", "B", "C", "D")
KS_D0 = 0.10
N_BOOT = 1000
N_PERM = 1000
MIN_REJECTED = 30
SCHED = "v21"                       # the schedule this module measures, PINNED (see addendum section 5)


def v_threshold_fit():
    """REG-7 A: 'V_T/V_1 >= the FIT threshold from the NON-CRASHING run-up table'.  v2 stipulated 1.2.

    The non-crashing run-ups are E4.1's run-up episodes that did NOT top within 200 days; the threshold is
    their P10 200-day fundamental-proxy growth, taken here on price over the run-up's own first 200 days
    (the proxy the panel supports without EDGAR coverage on every name)."""
    ru = pd.read_csv(os.path.join(GEN, "e4_1", "runup4.csv"))
    d = ru[(ru["topped"] == False)]                                   # noqa: E712
    g = pd.to_numeric(d["runup"], errors="coerce").dropna()
    # the run-up statistic is over 504 d; scale to the benchmark's 200 d in log terms
    scaled = np.exp(np.log(g.to_numpy(float)) * (200.0 / 504.0))
    return {"threshold": float(np.percentile(scaled, 10)),
            "p50": float(np.percentile(scaled, 50)), "p90": float(np.percentile(scaled, 90)),
            "n_non_crashing_runups": int(len(g)), "n_stocks": int(d["ticker"].nunique()),
            "v2_stipulated": 1.2,
            "definition": "P10 of the 200-day-equivalent price growth of run-ups that did NOT top within "
                          "200 days (E4.1 runup4.csv, topped == False); log-scaled from the 504-day window",
            "label": "FIT"}


def _one(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    from envs.v2.generator import check_validity
    scenario, seed, cdef = args
    # take the UNFILTERED population, then apply the rule here; PIN the schedule being measured (addendum 5)
    cfg = {"reject": False, "schedule_mode": SCHED}
    if cdef:
        cfg["control_definition"] = cdef
    env = SyntheticMarketEnv(scenario, 200, seed, config=cfg)
    d = env.data[env.data["asset"] == 0]
    p = d["price"].to_numpy(float)
    x = d["x"].to_numpy(float)
    V = d["fundamental_value"].to_numpy(float)
    iv = (d["implied_volatility"].to_numpy(float) if "implied_volatility" in d
          else np.full(len(p), np.nan))
    r = np.diff(np.log(p))
    reason = check_validity(env.result)
    acf1 = float(np.corrcoef(r[:-1], r[1:])[0, 1]) if len(r) > 3 else float("nan")
    return {"seed": seed, "scenario": scenario, "definition": cdef or "-",
            "accepted": reason is None, "reason": reason,
            "sd_r": float(np.std(r, ddof=1)), "acf1": acf1,
            "iv_mean": float(np.nanmean(iv)), "sd_x": float(np.std(x, ddof=1)),
            "mean_x": float(np.mean(x)), "min_x": float(np.min(x)), "max_x": float(np.max(x)),
            "V_growth": float(V[-1] / V[0]),
            "r": r.astype(np.float32)}


def pmap(items, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_one, items, chunksize=4))


def ks(a, b):
    a = np.sort(np.asarray([v for v in a if np.isfinite(v)], float))
    b = np.sort(np.asarray([v for v in b if np.isfinite(v)], float))
    if len(a) < 3 or len(b) < 3:
        return float("nan")
    allv = np.concatenate([a, b])
    return float(np.max(np.abs(np.searchsorted(a, allv, "right") / len(a) -
                               np.searchsorted(b, allv, "right") / len(b))))


def ks_upper(a, b, n_boot=N_BOOT, seed=400060):
    """Bootstrap 95 % UPPER limit of the KS distance -- the equivalence form the protocol requires."""
    a = np.asarray([v for v in a if np.isfinite(v)], float)
    b = np.asarray([v for v in b if np.isfinite(v)], float)
    if len(a) < 3 or len(b) < 3:
        return None, None
    rng = np.random.default_rng(seed)
    ds = [ks(a[rng.integers(0, len(a), len(a))], b[rng.integers(0, len(b), len(b))]) for _ in range(n_boot)]
    return ks(a, b), float(np.percentile(ds, 95))


def day_features(r, win=20):
    """Level-free, demeaned day features: the trailing window's sd, ACF(1), skew and the day's own
    standardised return.  No price level, no phase, no schedule."""
    n = len(r)
    F = np.full((n, 4), np.nan)
    for t in range(win, n):
        w = r[t - win:t]
        w = w - w.mean()
        s = w.std(ddof=1)
        if s <= 0:
            continue
        F[t, 0] = s
        F[t, 1] = float(np.corrcoef(w[:-1], w[1:])[0, 1]) if win > 3 else 0.0
        F[t, 2] = float(((w / s) ** 3).mean())
        F[t, 3] = float((r[t] - w.mean()) / s)
    return F


def discrimination(sb_rows, flat_rows, n_perm=N_PERM, seed=400061):
    """Day-level classifier of sustained-bull vs flat on demeaned level-free returns, against a SEED-label
    permutation null.  Model fit -- reference machine only."""
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.model_selection import GroupKFold
    Xs, ys, gs = [], [], []
    for lab, rows in ((1, sb_rows), (0, flat_rows)):
        for i, rr in enumerate(rows):
            F = day_features(np.asarray(rr["r"], float))
            m = np.isfinite(F).all(axis=1)
            if m.sum() < 20:
                continue
            Xs.append(F[m])
            ys.append(np.full(m.sum(), lab))
            gs.append(np.full(m.sum(), f"{lab}_{i}"))
    X = np.vstack(Xs)
    y = np.concatenate(ys)
    g = np.concatenate(gs)
    groups = np.unique(g)

    def acc(labels_by_group):
        yy = np.array([labels_by_group[gg] for gg in g])
        cv = GroupKFold(n_splits=4)
        preds = np.zeros(len(yy))
        for tr, te in cv.split(X, yy, groups=g):
            clf = HistGradientBoostingClassifier(max_iter=60, random_state=0)
            clf.fit(X[tr], yy[tr])
            preds[te] = clf.predict(X[te])
        return float((preds == yy).mean())

    true_map = {gg: int(gg.split("_")[0]) for gg in groups}
    a_true = acc(true_map)
    rng = np.random.default_rng(seed)
    lab_arr = np.array([true_map[gg] for gg in groups])
    null = []
    n_light = int(n_perm)
    for _ in range(n_light):
        # the classifier is REFITTED on permuted seed labels: a majority-rule shortcut would make the null
        # identically the majority class and the comparison vacuous
        perm = rng.permutation(lab_arr)
        m = dict(zip(groups, perm))
        null.append(acc(m))
    majority = float(max(np.mean(y), 1 - np.mean(y)))
    p95 = float(np.percentile(null, 95))
    return {"accuracy": a_true, "majority_class": majority,
            "null_p95_seed_permutation": p95,
            "null_mean": float(np.mean(null)), "null_max": float(np.max(null)),
            "n_permutations": n_light, "n_days": int(len(y)), "n_paths": int(len(groups)),
            "at_chance": bool(a_true <= p95),
            "note": "the null permutes SEED labels, not day labels (e4_0/power.json PP4), and the classifier "
                    "is REFITTED on each permutation, so the null carries the same optimism the real fit does"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=500)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    vthr = v_threshold_fit()
    print(f"[fit] V_T/V_1 threshold {vthr['threshold']:.4f} (v2 stipulated {vthr['v2_stipulated']}), "
          f"n = {vthr['n_non_crashing_runups']} non-crashing run-ups / {vthr['n_stocks']} stocks", flush=True)

    flat = pmap([("flat", s, None) for s in range(SEED_FLAT, SEED_FLAT + a.seeds)], a.workers)
    res = {"design": {"prereg": "PREREG_PHASE_4.md section 7, REG-7", "seeds": a.seeds,
                      "seed_sb": SEED_SB, "seed_flat": SEED_FLAT, "definitions": list(DEFS),
                      "ks_D0": KS_D0, "min_rejected_for_ks": MIN_REJECTED, "n_boot": N_BOOT,
                      "d14": "OPEN -- no definition is adopted here; the four audits are delivered so the "
                             "team can state the control's purpose on numbers",
                      "v_threshold_fit": vthr,
                      "note": "paths are generated with reject=False and the validity rule applied here, so "
                              "the ACCEPTED and REJECTED populations are both observable -- which is what the "
                              "selection audit needs and what v2's internal retry loop hid"},
           "definitions": {}}
    for cdef in DEFS:
        rows = pmap([("sustained_bull", s, cdef) for s in range(SEED_SB, SEED_SB + a.seeds)], a.workers)
        acc = [r for r in rows if r["accepted"]]
        rej = [r for r in rows if not r["accepted"]]
        mx = np.array([r["mean_x"] for r in rows], float)
        entry = {
            "n_paths": len(rows), "n_accepted": len(acc), "n_rejected": len(rej),
            "rejection_rate": float(len(rej) / max(len(rows), 1)),
            "reasons": pd.Series([r["reason"] for r in rej]).str.split(":").str[0].value_counts().to_dict() if rej else {},
            "i_realised_x": {
                "path_mean_x_p10_p50_p90": [float(np.percentile(mx, q)) for q in (10, 50, 90)],
                "sd_x_median": float(np.median([r["sd_x"] for r in rows])),
                "sd_x_median_accepted": (float(np.median([r["sd_x"] for r in acc])) if acc else None),
                "V_growth_median": float(np.median([r["V_growth"] for r in rows])),
            },
        }
        # ---- (ii) selection
        sel = {}
        if len(rej) < MIN_REJECTED:
            sel = {"status": "VACUOUS", "n_rejected": len(rej),
                   "verdict": f"no selection is possible by construction; the KS test is vacuous at "
                              f"n_rej = {len(rej)}",
                   "counted_as_pass": False,
                   "registered": "PREREG section 7 registered this branch before the run as the expected "
                                 "outcome for A/B/D"}
        else:
            # the equivalence bound D0 = 0.10 is only attainable if the bootstrap upper limit can GET below
            # it at the achieved sample sizes.  This is the decidability check the PP-series did not cover:
            # two samples drawn from the SAME accepted pool at (n_acc, n_rej) give the floor under the null.
            pool = np.array([r["sd_r"] for r in acc], float)
            rngf = np.random.default_rng(400062)
            floors = []
            for _ in range(200):
                aa = rngf.choice(pool, len(acc), replace=True)
                bb = rngf.choice(pool, len(rej), replace=True)
                _, up = ks_upper(aa, bb, n_boot=100, seed=int(rngf.integers(1, 10 ** 8)))
                if up is not None:
                    floors.append(up)
            sel["null_floor"] = {
                "median_upper_limit_under_the_null": float(np.median(floors)) if floors else None,
                "n_accepted": len(acc), "n_rejected": len(rej), "D0": KS_D0,
                "attainable": bool(floors and np.median(floors) < KS_D0),
                "meaning": "the bootstrap 95 % upper limit of the KS distance between two samples drawn from "
                           "the SAME distribution at these sample sizes; if it already exceeds D0 the "
                           "registered equivalence bound cannot be met by any result and the verdict is "
                           "UNDECIDABLE, not FAIL"}
            for field in ("sd_r", "acf1", "iv_mean"):
                d0, up = ks_upper([r[field] for r in acc], [r[field] for r in rej])
                sel[field] = {"ks": d0, "upper95": up, "passes": bool(up is not None and up < KS_D0)}
            sel["status"] = "TESTED"
            tested = [v for k, v in sel.items() if isinstance(v, dict) and "passes" in v]
            if any(v.get("upper95") is None for v in tested):
                sel["verdict"] = "UNDEFINED (a field had too few finite values on one side)"
            elif not sel["null_floor"]["attainable"]:
                sel["verdict"] = (f"UNDECIDABLE at n_acc = {len(acc)} / n_rej = {len(rej)}: the equivalence "
                                  f"bound {KS_D0} is below the null floor "
                                  f"{sel['null_floor']['median_upper_limit_under_the_null']:.3f}")
            else:
                sel["verdict"] = "PASS" if all(v.get("passes") for v in tested) else "FAIL"
        entry["ii_selection"] = sel
        # ---- (iii) discrimination
        try:
            entry["iii_discrimination"] = discrimination(acc if acc else rows, flat, n_perm=20)
        except Exception as e:                                        # noqa: BLE001
            entry["iii_discrimination"] = {"error": str(e)[:200]}
        res["definitions"][cdef] = entry
        di = entry["iii_discrimination"]
        print(f"  def {cdef}: rej {entry['rejection_rate']:.3f}  sd_x {entry['i_realised_x']['sd_x_median']:.4f}  "
              f"mean-x p10/50/90 {[round(v,3) for v in entry['i_realised_x']['path_mean_x_p10_p50_p90']]}  "
              f"KS {sel.get('status')}  acc {di.get('accuracy')} vs null p95 {di.get('null_p95_seed_permutation')} "
              f"-> at chance {di.get('at_chance')}", flush=True)

    res["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(OUT, "control.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)

    L = ["# E4.5 - the sustained-bull control, four definitions (REG-7)", "",
         "`python -m tools.phase4.e4_5_control` - PREREG_PHASE_4.md section 7.", "",
         f"{a.seeds} seeds per definition, {a.seeds} flat seeds for the discrimination audit.",
         "**D14 is open: no definition is adopted here.** The audits are delivered so the team can state the "
         "control's purpose on numbers.", "",
         f"The v2 `V_T/V_1 >= 1.2` threshold was stipulated; the FIT replacement is "
         f"**{vthr['threshold']:.4f}** ({vthr['definition']}, n = {vthr['n_non_crashing_runups']} / "
         f"{vthr['n_stocks']}).", "",
         "| definition | rejection | sd(x) median | path-mean x P10/P50/P90 | selection (KS) | classifier acc | null p95 | at chance |",
         "|---|---|---|---|---|---|---|---|"]
    for cdef, v in res["definitions"].items():
        di = v["iii_discrimination"]
        L.append(f"| {cdef} | {v['rejection_rate']:.3f} | {v['i_realised_x']['sd_x_median']:.4f} | "
                 f"{[round(z, 3) for z in v['i_realised_x']['path_mean_x_p10_p50_p90']]} | "
                 f"{v['ii_selection'].get('status')} | {di.get('accuracy')} | "
                 f"{di.get('null_p95_seed_permutation')} | **{di.get('at_chance')}** |")
    L += ["", "## Selection audit detail", ""]
    for cdef, v in res["definitions"].items():
        s = v["ii_selection"]
        L += [f"### {cdef}", "", f"- status: **{s.get('status')}** - {s.get('verdict')}",
              f"- rejected paths: {v['n_rejected']} of {v['n_paths']}",
              f"- rejection reasons: {v['reasons']}", ""]
        if s.get("status") == "TESTED":
            L += ["| field | KS | bootstrap 95 % upper | passes (< 0.10) |", "|---|---|---|---|"]
            for f in ("sd_r", "acf1", "iv_mean"):
                if f in s:
                    v_ = s[f]
                    ks_ = "-" if v_.get("ks") is None else f"{v_['ks']:.4f}"
                    up_ = "-" if v_.get("upper95") is None else f"{v_['upper95']:.4f}"
                    L.append(f"| {f} | {ks_} | {up_} | {v_.get('passes')} |")
            L.append("")
    with open(os.path.join(OUT, "control.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"wrote {OUT}/control.json in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
