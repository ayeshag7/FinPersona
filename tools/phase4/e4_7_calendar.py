"""
E4.7 (PREREG_PHASE_4.md section 9; REG-9, D6): orderings, the calendar, and the setup range.

    python -m tools.phase4.e4_7_calendar [--stages setup,ordering,render,eps] [--seeds 200] [--workers 3]

Four things, all measured on the DEPLOYED state with `schedule_mode` pinned:

  setup     the setup range swept, with BOTH quantities it trades off between measured at each setting:
            the crash rise time (E4.2's unmet criterion, whose binding lever P4-6 identified as `setup_len`)
            and the day-only macro-phase classifier (REG-9's constraint).  P4-6 established the correlation
            and the conditional; it did NOT establish that shortening the setup fixes the rise time, because
            conditioning on the onset lag selects on an outcome.  This is that experiment.
  ordering  setup_first / event_first / phase_free, same classifier per scenario.
  render    the three day-index renderings.  A rendering changes only what is SHOWN, not the path, so all
            three are evaluated on one generated path set.
  eps       whether `days_since_eps_announcement` carries an absolute clock, with the quarter grid fixed
            (v2) and randomised per seed (E4.7d), measured rather than assumed.

Statistic (REG-9): the accuracy of a classifier that sees ONLY the rendered day field, predicting the day's
macro phase, within each scenario.  The model is the best day-value -> phase lookup, fitted on half the seeds
and scored on the other half.  The null permutes SEED labels -- each seed's phase sequence is reassigned to
another seed's day axis, which destroys the day-phase alignment while preserving every path's own phase
structure.  Permuting DAY labels would give a null of about 0.503 and call almost any classifier a leak
(e4_0/power.json PP4).

Rule: a setting is acceptable iff accuracy <= the null's 95th percentile + 1 pp, in every scenario.

The rise-time calm reference is the BURN-IN's last 120 days, identical across arms, because the "30 days
before the event" reference used elsewhere is undefined for a short setup -- the first attempt at this sweep
returned n = 0 for exactly that reason.

Output: docs/env_v2/generated/v2_1/e4_7/{calendar.json, calendar.md}
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
OUT = os.path.join(GEN, "e4_7")
SCHED = "v21"
SEED_SETUP = 320000
SEED_ORD = 322000
SEED_REND = 324000
SEED_EPS = 326000
N_PERM = 200
PANEL_RISE_CI = [29.0, 35.0]
MARGIN_PP = 0.01          # REG-9's "+1 pp"


# --------------------------------------------------------------------------- generator jobs
def _path(args):
    """One path on the deployed state.  Returns the day axis, the macro phase, the rendered day field under
    all three renderings, the eps field, and the rise-time statistics."""
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    from tools.phase3.episodes import drawdown_episodes, rise_decay
    scenario, seed, cfg, renders = args
    kw = {"crash_discount": 0.70} if scenario == "crash" else {}
    base = dict(cfg or {})
    base["schedule_mode"] = SCHED
    out = {"seed": seed, "scenario": scenario}
    fields = {}
    for mode in renders:
        env = SyntheticMarketEnv(scenario, 200, seed, config=base, day_index_mode=mode, **kw)
        d = env.data[env.data["asset"] == 0]
        day = d["day"].to_numpy(int)
        m = day >= 1
        if mode == renders[0]:
            out["days"] = day[m].tolist()
            out["phases"] = [str(z) for z in d["phase"].to_numpy(object)[m]]
            out["eps_days"] = d["days_since_eps_announcement"].to_numpy(float)[m].tolist()
            out["setup_len"] = int(env.schedule.setup_len)
            out["ordering"] = env.schedule.ordering
            out["rejected"] = int(env.attempts > 1)
            if scenario == "crash":
                p = d["price"].to_numpy(float)
                r = np.diff(np.log(p))
                full = env.result
                rb = np.diff(np.log(full.P[0][full.day <= 0]))
                rv_calm = float(np.mean(rb[-120:] ** 2)) if len(rb) >= 120 else float("nan")
                eps = [e for e in drawdown_episodes(p, depth_thr=-0.30) if (e["trough"] - e["peak"]) <= 126]
                if eps and np.isfinite(rv_calm) and rv_calm > 0:
                    e0 = min(eps, key=lambda e: e["depth"])
                    rd = rise_decay(e0, p, r, rv_calm)
                    if rd:
                        out["rise"] = rd["rise"]
                        out["onset_lag_before_event"] = int(env.schedule.event_start - rd["onset"])
                    out["depth"] = float(e0["depth"])
                    out["duration"] = int(e0["trough"] - e0["peak"])
        # What a stateless agent can read off the rendered day field, as a number.  This calls the RENDERER
        # directly rather than building a full observation per day: `_render_date` is the function that
        # produces the field, so this is the same value the agent would see, at a fraction of the cost.
        import datetime as dt
        vals = []
        for dd in day[m]:
            v = env._render_date(int(dd))
            if v is None:
                vals.append(None)
            elif isinstance(v, str) and v.startswith("Day-"):
                vals.append(float(v.split("-")[1].split(" ")[0]))
            else:
                vals.append(float(dt.date.fromisoformat(str(v)).toordinal()))
        fields[mode] = vals
    out["rendered"] = fields
    return out


def pmap(items, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_path, items, chunksize=2))


# --------------------------------------------------------------------------- the audit
def day_only_classifier(rows, feature_key, n_perm=N_PERM, seed=4700):
    """Best feature-value -> phase lookup, fitted on half the seeds and scored on the other half, against a
    SEED-label permutation null."""
    F, P, G = [], [], []
    for i, r in enumerate(rows):
        f = r["rendered"][feature_key] if feature_key in r["rendered"] else None
        if f is None or all(v is None for v in f):
            F.append(None)
            P.append(np.asarray(r["phases"], object))
            G.append(i)
            continue
        F.append(np.asarray([np.nan if v is None else v for v in f], float))
        P.append(np.asarray(r["phases"], object))
        G.append(i)
    n = len(G)
    if n < 20:
        return {"error": "too few paths"}
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    tr, te = idx[: n // 2], idx[n // 2:]
    no_feature = all(f is None for f in F)

    def fit_predict(train, test, phase_src):
        if no_feature:
            # nothing is rendered: the best any classifier can do is the majority phase of the training half
            allp = [str(x) for i in train for x in phase_src[i]]
            maj = pd.Series(allp).value_counts().idxmax() if allp else None
            hit = tot = 0
            for i in test:
                for pp in phase_src[i]:
                    tot += 1
                    hit += (str(pp) == maj)
            return hit / max(tot, 1)
        table = {}
        for i in train:
            if F[i] is None:
                continue
            for v, pp in zip(F[i], phase_src[i]):
                if not np.isfinite(v):
                    continue
                table.setdefault(float(v), {}).setdefault(str(pp), 0)
                table[float(v)][str(pp)] += 1
        pred = {v: max(c, key=c.get) for v, c in table.items()}
        allp = [str(x) for i in train for x in phase_src[i]]
        fallback = pd.Series(allp).value_counts().idxmax() if allp else None
        hit = tot = 0
        for i in test:
            if F[i] is None:
                continue
            for v, pp in zip(F[i], phase_src[i]):
                if not np.isfinite(v):
                    continue
                tot += 1
                hit += (pred.get(float(v), fallback) == str(pp))
        return hit / max(tot, 1)

    acc = fit_predict(tr, te, P)
    allp = [str(x) for i in te for x in P[i]]
    maj = float(pd.Series(allp).value_counts(normalize=True).max()) if allp else float("nan")
    null = []
    for _ in range(n_perm):
        perm = rng.permutation(n)
        shuffled = []
        for i in range(n):
            src = P[perm[i]]
            if len(src) >= len(P[i]):
                shuffled.append(src[: len(P[i])])
            else:
                shuffled.append(np.concatenate([src, np.full(len(P[i]) - len(src), src[-1], dtype=object)]))
        null.append(fit_predict(tr, te, shuffled))
    p95 = float(np.percentile(null, 95))
    return {"accuracy": float(acc), "majority_class": maj, "null_p95": p95,
            "null_mean": float(np.mean(null)), "n_permutations": n_perm, "n_paths": n,
            "margin_pp": float(100 * (acc - p95)),
            "acceptable": bool(acc <= p95 + MARGIN_PP),
            "rule": "REG-9: acceptable iff accuracy <= the seed-permutation null's 95th percentile + 1 pp"}


def boot_median(v, n_boot=2000, seed=4701):
    v = np.asarray([x for x in v if x is not None and np.isfinite(x)], float)
    if len(v) < 20:
        return None, None, len(v)
    rng = np.random.default_rng(seed)
    b = [float(np.median(v[rng.integers(0, len(v), len(v))])) for _ in range(n_boot)]
    return float(np.median(v)), [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))], int(len(v))


def eps_clock(rows, n_perm=N_PERM, seed=4702):
    """Does `days_since_eps_announcement` locate the agent on the ABSOLUTE calendar shared by all seeds?

    The first version of this test asked whether the field predicts the raw day index, with a null that
    permuted SEED labels.  Both were wrong and the test was degenerate (R^2 equalled the null exactly):
    every path has the SAME day axis 1..200, so permuting seeds cannot break a day-field relation that is
    identical across seeds -- which is precisely the relation being tested for.

    The relation that matters is between the field and the POSITION IN THE QUARTER, pooled across seeds.
    Under the v2 fixed grid every seed's quarter ends fall on the same days, so a value of the field implies
    the same quarter position for every seed and therefore the same three candidate days in a 200-day
    horizon.  Under a per-seed grid shift it implies nothing shared.

    Statistic: accuracy of predicting which third of the quarter (day mod 63 in 0-20 / 21-41 / 42-62) the day
    falls in, from the field value alone, fitted on half the seeds and scored on the other half.
    Null: each path's field series is shuffled IN TIME, which preserves its marginal distribution and destroys
    the alignment.  Chance is 1/3 by construction."""
    X, Y = [], []
    for r in rows:
        X.append(np.asarray(r["eps_days"], float))
        Y.append((np.asarray(r["days"], int) % 63) // 21)
    n = len(rows)
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    tr, te = idx[: n // 2], idx[n // 2:]

    def fit_predict(train, test, xsrc):
        tab = {}
        for i in train:
            for v, y in zip(xsrc[i], Y[i]):
                if np.isfinite(v):
                    tab.setdefault(round(float(v)), {}).setdefault(int(y), 0)
                    tab[round(float(v))][int(y)] += 1
        pred = {k: max(c, key=c.get) for k, c in tab.items()}
        allc = [int(y) for i in train for y in Y[i]]
        fb = int(pd.Series(allc).value_counts().idxmax()) if allc else 0
        hit = tot = 0
        for i in test:
            for v, y in zip(xsrc[i], Y[i]):
                if not np.isfinite(v):
                    continue
                tot += 1
                hit += (pred.get(round(float(v)), fb) == int(y))
        return hit / max(tot, 1)

    acc = fit_predict(tr, te, X)
    null = []
    for _ in range(n_perm):
        shuffled = [rng.permutation(X[i]) for i in range(n)]
        null.append(fit_predict(tr, te, shuffled))
    p95 = float(np.percentile(null, 95))
    return {"accuracy_quarter_third_from_eps_field": float(acc), "null_p95": p95,
            "null_mean": float(np.mean(null)), "chance": 1.0 / 3.0,
            "n_paths": n, "n_permutations": n_perm,
            "carries_a_clock": bool(acc > p95),
            "excess_over_null": float(acc - p95),
            "null_construction": "each path's field series shuffled IN TIME (marginal preserved, alignment "
                                 "destroyed); a seed-label permutation is degenerate here because every path "
                                 "shares the same day axis"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="setup,ordering,render,eps")
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    jp = os.path.join(OUT, "calendar.json")
    res = json.load(open(jp, encoding="utf-8")) if os.path.exists(jp) else {}
    res["design"] = {"prereg": "PREREG_PHASE_4.md section 9; REG-9; D6", "seeds": a.seeds,
                     "schedule_mode": SCHED + " (pinned)", "n_permutations": N_PERM,
                     "margin_pp": MARGIN_PP,
                     "rule": "accuracy <= seed-permutation null p95 + 1 pp, within each scenario",
                     "rise_calm_reference": "the burn-in's last 120 days, identical across arms"}
    stages = [s.strip() for s in a.stages.split(",")]

    def save():
        json.dump(res, open(jp, "w", encoding="utf-8"), indent=1, default=str)

    # ---------------------------------------------------------------- setup sweep
    if "setup" in stages:
        print("[setup] sweeping the setup range: rise time AND the day-only classifier ...", flush=True)
        grid = [(0.025, 0.10), (0.05, 0.20), (0.10, 0.30), (0.175, 0.40), (0.25, 0.55)]
        res["setup_sweep"] = {"note": "P4-6 established corr(onset lag, rise) = 0.684 and that paths whose "
                                      "onset coincides with the event give rise 32 d, but conditioning on "
                                      "the onset lag SELECTS ON AN OUTCOME. This sweeps the cause directly.",
                              "arms": {}}
        for lo, hi in grid:
            cfg = {"schedule_ranges": {"setup_frac": [lo, hi]}}
            rows = pmap([("crash", s, cfg, ("day_n",)) for s in range(SEED_SETUP, SEED_SETUP + a.seeds)],
                        a.workers)
            rise, rise_ci, n = boot_median([r.get("rise") for r in rows])
            lag, lag_ci, _ = boot_median([r.get("onset_lag_before_event") for r in rows])
            clf = day_only_classifier(rows, "day_n")
            key = f"setup_frac_{lo}_{hi}"
            res["setup_sweep"]["arms"][key] = {
                "setup_len_median": float(np.median([r["setup_len"] for r in rows])),
                "rise_median": rise, "rise_ci95": rise_ci, "n_rise": n,
                "rise_ci_overlaps_panel": bool(rise_ci and not (rise_ci[1] < PANEL_RISE_CI[0]
                                                                or rise_ci[0] > PANEL_RISE_CI[1])),
                "onset_lag_median": lag, "onset_lag_ci95": lag_ci,
                "depth_median": boot_median([r.get("depth") for r in rows])[0],
                "duration_median": boot_median([r.get("duration") for r in rows])[0],
                "rejection": float(np.mean([r["rejected"] for r in rows])),
                "day_only_classifier": clf}
            v = res["setup_sweep"]["arms"][key]
            print(f"    setup U({lo},{hi})T (median {v['setup_len_median']:.0f} d): rise {rise} {rise_ci} "
                  f"{'MEETS' if v['rise_ci_overlaps_panel'] else 'not met'} | lag {lag} | classifier "
                  f"{clf['accuracy']:.4f} vs null {clf['null_p95']:.4f} -> "
                  f"{'ACCEPTABLE' if clf['acceptable'] else 'CLOCK'}", flush=True)
            save()
        arms = res["setup_sweep"]["arms"]
        both = [k for k, v in arms.items()
                if v["rise_ci_overlaps_panel"] and v["day_only_classifier"]["acceptable"]]
        res["setup_sweep"]["verdict"] = {
            "arms_meeting_the_rise_time": [k for k, v in arms.items() if v["rise_ci_overlaps_panel"]],
            "arms_acceptable_on_the_classifier": [k for k, v in arms.items()
                                                  if v["day_only_classifier"]["acceptable"]],
            "arms_meeting_both": both,
            "conclusion": ("a setup range exists that meets the rise time AND stays at chance on the "
                           f"day-only classifier: {both}" if both else
                           "NO setup range tested meets both; the rise time and REG-9's clock constraint "
                           "trade off against each other and the trade-off is now measured")}
        print(f"    VERDICT: {res['setup_sweep']['verdict']['conclusion']}", flush=True)
        save()

    # ---------------------------------------------------------------- orderings
    if "ordering" in stages:
        print("[ordering] the three orderings, classifier per scenario ...", flush=True)
        res.setdefault("ordering", {})
        for ordr in ("setup_first", "event_first", "phase_free"):
            if ordr in res["ordering"] and len(res["ordering"][ordr]) == 2:
                print(f"    {ordr}: cached, skipped", flush=True)
                continue
            res["ordering"][ordr] = {}
            for sc in ("crash", "bull_trap"):
                rows = pmap([(sc, s, {"ordering": ordr}, ("day_n",))
                             for s in range(SEED_ORD, SEED_ORD + a.seeds)], a.workers)
                clf = day_only_classifier(rows, "day_n")
                res["ordering"][ordr][sc] = clf
                print(f"    {ordr:12s} {sc:10s} acc {clf['accuracy']:.4f} null {clf['null_p95']:.4f} "
                      f"-> {'ACCEPTABLE' if clf['acceptable'] else 'CLOCK'}", flush=True)
            save()

    # ---------------------------------------------------------------- renderings
    if "render" in stages:
        print("[render] the three day-index renderings on ONE path set ...", flush=True)
        res.setdefault("renderings", {})
        for sc in ("crash", "bull_trap"):
            if sc in res["renderings"] and len(res["renderings"][sc]) == 3:
                print(f"    {sc}: cached, skipped", flush=True)
                continue
            rows = pmap([(sc, s, {}, ("day_n", "none", "date"))
                         for s in range(SEED_REND, SEED_REND + a.seeds)], a.workers)
            res["renderings"][sc] = {}
            for mode in ("day_n", "none", "date"):
                clf = day_only_classifier(rows, mode)
                res["renderings"][sc][mode] = clf
                print(f"    {sc:10s} {mode:6s} acc {clf['accuracy']:.4f} null {clf['null_p95']:.4f} "
                      f"margin {clf['margin_pp']:+.2f} pp -> "
                      f"{'ACCEPTABLE' if clf['acceptable'] else 'CLOCK'}", flush=True)
            save()

    # ---------------------------------------------------------------- eps quarter clock
    if "eps" in stages:
        print("[eps] does days_since_eps_announcement carry an absolute clock? ...", flush=True)
        res["eps_quarter_clock"] = {}
        for label, randomise in (("v2_fixed_quarter_grid", False), ("randomised_per_seed", True)):
            # forced through the GenConfig field, not a module global: the workers are separate processes
            # and would not see a global set in the parent
            rows = pmap([("flat", s, {"randomise_eps_quarter": randomise}, ("day_n",))
                         for s in range(SEED_EPS, SEED_EPS + a.seeds)], a.workers)
            res["eps_quarter_clock"][label] = eps_clock(rows)
            v = res["eps_quarter_clock"][label]
            print(f"    {label:24s} acc(quarter third | eps field) "
                  f"{v['accuracy_quarter_third_from_eps_field']:.4f} vs null {v['null_p95']:.4f} "
                  f"(chance {v['chance']:.3f}) -> carries a clock: {v['carries_a_clock']}", flush=True)
        a_, b_ = res["eps_quarter_clock"]["v2_fixed_quarter_grid"], res["eps_quarter_clock"]["randomised_per_seed"]
        res["eps_quarter_clock"]["verdict"] = (
            "RANDOMISATION IS NEEDED AND WORKS -- the fixed grid carries a clock and randomising removes it"
            if a_["carries_a_clock"] and not b_["carries_a_clock"] else
            "RANDOMISATION IS NEEDED BUT DOES NOT SUFFICE -- both carry a clock"
            if a_["carries_a_clock"] and b_["carries_a_clock"] else
            "NOT NEEDED -- the fixed grid does not carry a clock at this n, so REG-9(c)'s premise is not "
            "supported by measurement and the randomisation is a no-cost precaution rather than a fix")
        print(f"    VERDICT: {res['eps_quarter_clock']['verdict']}", flush=True)
        save()

    res["seconds"] = round(time.time() - t0, 1)
    save()
    print(f"wrote {jp} in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
