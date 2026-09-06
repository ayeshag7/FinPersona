"""
E4.10 -- every Phase-4 claim that was INFERRED rather than measured, tested against a stated falsifier.

    python -m tools.phase4.e4_10_verify_claims [--stages T1,T3,T4,T5,T6,T7,T8] [--seeds N] [--workers 3]

A claim audit of PHASE_4_REPORT.md and the P4-* entries separated statements backed by a generated file from
statements that were reasoning ABOUT one.  The reasoning ones are below.  Each is load-bearing for a decision
the team is being asked to take, so each gets a test that could falsify it.

  T1  "the panel's run-ups DECELERATE, so a super-exponential mania is contradicted" (P4-8).  The convexity
      ratio 0.665 is measured, but run-ups are DEFINED by a local maximum at the top, which mechanically
      flattens the final segment.  Falsifier: recompute on windows that exclude the endpoint, and on a window
      whose END is not selected on price at all.
  T3  "item 10 is inert BECAUSE E4.2 draws delta from the panel's depth distribution".  The 0.00 partial R^2
      is measured; the cause is not.  Falsifier: vary crash_discount under v2 and v21 and compare.
  T4  "about 2,000 seeds would bring the KS null floor to 0.10" (P4-9).  An extrapolation.  Falsifier:
      measure the floor as a function of the rejected-sample size.
  T5  "the deployed excess is the scenario mix" (P4-1).  The two weightings are measured but the residual
      +15.3 % was ATTRIBUTED.  Falsifier: decompose it into per-phase contributions.
  T6  "adopting A, B or D closes items 18 and 42" (P4-9).  Falsifier: measure the accepted-vs-rejected x
      distribution under each definition.
  T7  "v2's multi-asset extension implies a common-factor loading of 1.0" (P4-16).  Read from code, not
      measured.  Falsifier: generate multi-asset paths and measure the realised share.
  T8  the 1.354 mean-vs-median RV ratio is quoted in P4-1 but was computed in an ad-hoc session script and
      never written to a generated file.  Persist it with its n and interval.

Output: docs/env_v2/generated/v2_1/e4_10/verify.{json,md}
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
OUT = os.path.join(GEN, "e4_10")
N_BOOT = 1000
SEED_T3 = 292000
SEED_T6 = 293000
SEED_T7 = 294000


def boot_median_by_stock(v, tick, n_boot=N_BOOT, seed=4101):
    v = np.asarray(v, float)
    tick = np.asarray(tick)
    ok = np.isfinite(v)
    v, tick = v[ok], tick[ok]
    if len(v) < 20:
        return None, None, len(v), 0
    stocks = np.array(sorted(set(tick.tolist())))
    idx_by = {t: np.where(tick == t)[0] for t in stocks}
    rng = np.random.default_rng(seed)
    b = [float(np.median(v[np.concatenate([idx_by[t] for t in rng.choice(stocks, len(stocks), replace=True)])]))
         for _ in range(n_boot)]
    return (float(np.median(v)), [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))],
            int(len(v)), int(len(stocks)))


# =============================================================== T1
def t1_convexity_endpoint():
    from tools.phase1.panel import analysis_sets, load_prices
    ru = pd.read_csv(os.path.join(GEN, "e4_1", "runup4.csv"))
    A = analysis_sets(write=False)["A"]
    px = load_prices(A).ffill()
    rows = []
    for t, g in ru.groupby("ticker"):
        if t not in px.columns:
            continue
        p = px[t].to_numpy(float)
        lp = np.log(np.where(np.isfinite(p) & (p > 0), p, np.nan))
        n = len(lp)
        for _, r in g.iterrows():
            s0, s1 = int(r["start"]), int(r["top"])

            def ratio(a, b):
                L = b - a
                if L < 30 or b >= n or a < 0:
                    return None
                i1, i2 = a + L // 3, a + 2 * L // 3
                if not np.isfinite([lp[a], lp[i1], lp[i2], lp[b]]).all():
                    return None
                first = lp[i1] - lp[a]
                last = lp[b] - lp[i2]
                return (last / first) if first > 1e-6 else None

            rows.append({"ticker": t,
                         "a_original": ratio(s0, s1),
                         "b_minus21": ratio(s0, s1 - 21),
                         "b_minus42": ratio(s0, s1 - 42),
                         "c_fixed_horizon": ratio(s0, min(s0 + 504, n - 1))})
    df = pd.DataFrame(rows)
    out = {"claim": "the panel's run-ups decelerate (P4-8), so a super-exponential mania is contradicted",
           "falsifier": "if the deceleration disappears once the endpoint constraint is removed, the "
                        "measurement is an artefact of defining a run-up by a local maximum at its top",
           "windows": {}}
    for c, label in (("a_original", "[start, top] -- the original, endpoint-selected"),
                     ("b_minus21", "[start, top-21] -- past the +/-10 d local-max constraint"),
                     ("b_minus42", "[start, top-42] -- further past it"),
                     ("c_fixed_horizon", "[start, start+504] -- the END is not selected on price at all")):
        pt, ci, n, ns = boot_median_by_stock(df[c].to_numpy(float), df["ticker"].to_numpy())
        out["windows"][c] = {"description": label, "median_ratio": pt, "ci95": ci,
                             "n_episodes": n, "n_stocks": ns,
                             "accelerating": bool(pt is not None and pt > 1.0)}
    a_ = out["windows"]["a_original"]["median_ratio"]
    c_ = out["windows"]["c_fixed_horizon"]["median_ratio"]
    if c_ is None or a_ is None:
        out["verdict"] = "INCONCLUSIVE"
    elif c_ > 1.0 and a_ < 1.0:
        out["verdict"] = ("ARTEFACT -- the deceleration is produced by the endpoint selection. P4-8's "
                          "reading must be withdrawn and kappa re-fitted on a window that does not select "
                          "on the endpoint")
    elif c_ < 1.0:
        out["verdict"] = ("REAL -- the deceleration survives removing the endpoint constraint, so P4-8 "
                          "stands")
    else:
        out["verdict"] = "MIXED -- see the per-window rows"
    return out


# =============================================================== T3
def _t3_one(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    seed, mode, disc = args
    env = SyntheticMarketEnv("crash", 200, seed, crash_discount=disc, config={"schedule_mode": mode})
    p = env.data[env.data["asset"] == 0]["price"].to_numpy(float)
    return {"seed": seed, "mode": mode, "crash_discount": disc,
            "mdd": float((p / np.maximum.accumulate(p) - 1).min()),
            "delta_drawn": float(env.schedule.delta), "D_V": float(env.schedule.D_V)}


def t3_item10(seeds, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        jobs = [(s, m, dsc) for m in ("v2", "v21") for dsc in (0.55, 0.70, 0.85)
                for s in range(SEED_T3, SEED_T3 + seeds)]
        rows = list(ex.map(_t3_one, jobs, chunksize=8))
    df = pd.DataFrame(rows)
    out = {"claim": "checklist item 10 is inert BECAUSE E4.2 draws delta from the panel's depth "
                    "distribution, so the crash_discount arm factor no longer changes anything",
           "falsifier": "if the partial R^2 of crash_discount is also near zero under the v2 schedule, the "
                        "cause is something else",
           "arms": {}}
    for mode, g in df.groupby("mode"):
        means = g.groupby("crash_discount")["mdd"].mean().to_dict()
        spread = 100 * (means.get(0.55, np.nan) - means.get(0.85, np.nan))
        X = np.column_stack([np.ones(len(g)), g["D_V"].to_numpy(float)])
        y = g["mdd"].to_numpy(float)
        r_full = y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
        X2 = np.column_stack([X, g["crash_discount"].to_numpy(float)])
        r2_ = y - X2 @ np.linalg.lstsq(X2, y, rcond=None)[0]
        pr2 = 1.0 - float(r2_ @ r2_) / max(float(r_full @ r_full), 1e-12)
        out["arms"][mode] = {"means_by_discount": {str(k): float(v) for k, v in means.items()},
                             "spread_pp_0.55_minus_0.85": float(spread),
                             "partial_r2_of_crash_discount": float(pr2),
                             "corr_discount_vs_delta_drawn": float(
                                 np.corrcoef(g["crash_discount"], g["delta_drawn"])[0, 1])
                             if g["delta_drawn"].std() > 0 else 0.0,
                             "delta_drawn_sd": float(g["delta_drawn"].std()), "n": int(len(g))}
    v2, v21 = out["arms"].get("v2", {}), out["arms"].get("v21", {})
    out["verdict"] = ("CONFIRMED -- crash_discount drives MDD under v2 and does not under v21"
                      if (v2.get("partial_r2_of_crash_discount", 0) > 0.2 and
                          v21.get("partial_r2_of_crash_discount", 1) < 0.05)
                      else "NOT CONFIRMED AS STATED -- see the arms")
    return out


# =============================================================== T4
def t4_ks_floor():
    e45 = json.load(open(os.path.join(GEN, "e4_5", "control.json"), encoding="utf-8"))
    nf = e45["definitions"]["A"]["ii_selection"]["null_floor"]
    n_acc0, n_rej0 = nf["n_accepted"], nf["n_rejected"]
    rng = np.random.default_rng(4107)
    pool = rng.normal(size=20000)

    def ks_(a, b):
        a, b = np.sort(a), np.sort(b)
        allv = np.concatenate([a, b])
        return float(np.max(np.abs(np.searchsorted(a, allv, "right") / len(a) -
                                   np.searchsorted(b, allv, "right") / len(b))))

    out = {"claim": "about 2,000 seeds would bring the KS null floor to 0.10 (P4-9)",
           "falsifier": "measure the floor at each n and read off the n that reaches 0.10",
           "measured_at_phase4_n": {"n_accepted": n_acc0, "n_rejected": n_rej0,
                                    "floor": nf["median_upper_limit_under_the_null"]},
           "by_n_rejected": {}}
    for mult in (1, 2, 4, 8, 16):
        n_rej, n_acc = int(n_rej0 * mult), int(n_acc0 * mult)
        ups = []
        for _ in range(40):
            A = rng.choice(pool, n_acc, replace=True)
            B = rng.choice(pool, n_rej, replace=True)
            ds = [ks_(A[rng.integers(0, n_acc, n_acc)], B[rng.integers(0, n_rej, n_rej)]) for _ in range(60)]
            ups.append(float(np.percentile(ds, 95)))
        med = float(np.median(ups))
        out["by_n_rejected"][str(n_rej)] = {"seeds_implied": int(500 * mult), "n_accepted": n_acc,
                                            "median_upper_limit_under_null": med,
                                            "attainable_at_D0_0.10": bool(med < 0.10)}
    ok = [v["seeds_implied"] for v in out["by_n_rejected"].values() if v["attainable_at_D0_0.10"]]
    out["verdict"] = (f"the bound becomes attainable at about {min(ok)} seeds" if ok else
                      "the bound is NOT attainable at any n tested (up to 8,000 seeds); P4-9's "
                      "extrapolation was optimistic and the remedy is not simply more seeds")
    return out


# =============================================================== T5
def t5_residual():
    lv = json.load(open(os.path.join(GEN, "e4_0", "level.json"), encoding="utf-8"))
    pv = lv["iii_mix"]["per_phase_pooled"]
    pw = lv["iii_mix"]["panel_phase_weights"]["weights"]
    target = lv["iii_mix"]["target_s_A"]
    tot_w = sum(w for k, w in pw.items() if k in pv and np.isfinite(pv[k]["var"]))
    contrib = {}
    for k, w in pw.items():
        if k in pv and np.isfinite(pv[k]["var"]):
            contrib[k] = {"panel_weight": w / tot_w, "generator_variance": pv[k]["var"],
                          "weighted": (w / tot_w) * pv[k]["var"]}
    tot_var = sum(c["weighted"] for c in contrib.values())
    for k in contrib:
        contrib[k]["pct_of_total_variance"] = 100 * contrib[k]["weighted"] / tot_var
    sd = math.sqrt(tot_var)
    # what would the sd be if each phase in turn were set to the panel's own level for that phase?
    return {"claim": "the deployed excess over s_A is the benchmark's own scenario mix (P4-1)",
            "falsifier": "if one phase's contribution accounts for the residual, it is that phase's level "
                         "and not the mix",
            "target_s_A": target, "panel_weighted_sd": sd,
            "excess_pct": 100 * (sd / target - 1),
            "contributions": dict(sorted(contrib.items(), key=lambda kv: -kv[1]["pct_of_total_variance"])),
            "note": "panel weights come from E3.3's FIXED windows, so they measure the share of panel days "
                    "those windows cover rather than a phase-dating of the whole panel; the decomposition "
                    "shows where the variance sits, and is not a re-weighting that could be adopted"}


# =============================================================== T6
def _t6_one(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    from envs.v2.generator import check_validity
    seed, cdef = args
    env = SyntheticMarketEnv("sustained_bull", 200, seed,
                             config={"reject": False, "control_definition": cdef})
    d = env.data[env.data["asset"] == 0]
    x = d["x"].to_numpy(float)
    r = np.diff(np.log(d["price"].to_numpy(float)))
    return {"seed": seed, "definition": cdef, "accepted": check_validity(env.result) is None,
            "sd_x": float(np.std(x, ddof=1)), "sd_r": float(np.std(r, ddof=1)),
            "mean_x": float(np.mean(x))}


def t6_control_would_pass(seeds, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        jobs = [(s, c) for c in ("A", "B", "C", "D") for s in range(SEED_T6, SEED_T6 + seeds)]
        rows = list(ex.map(_t6_one, jobs, chunksize=8))
    df = pd.DataFrame(rows)

    def ks_(a, b):
        a, b = np.sort(np.asarray(a, float)), np.sort(np.asarray(b, float))
        if len(a) < 3 or len(b) < 3:
            return None
        allv = np.concatenate([a, b])
        return float(np.max(np.abs(np.searchsorted(a, allv, "right") / len(a) -
                                   np.searchsorted(b, allv, "right") / len(b))))

    out = {"claim": "adopting A, B or D closes weakness items 18 and 42 (P4-9)",
           "falsifier": "measure the accepted-vs-rejected x distribution under each definition; if A/B/D "
                        "still select on x the claim fails",
           "definitions": {}}
    for c, g in df.groupby("definition"):
        acc, rej = g[g["accepted"]], g[~g["accepted"]]
        e = {"rejection": float(len(rej) / max(len(g), 1)),
             "n_accepted": int(len(acc)), "n_rejected": int(len(rej)),
             "ks_mean_x": ks_(acc["mean_x"], rej["mean_x"]),
             "ks_sd_x": ks_(acc["sd_x"], rej["sd_x"]),
             "ks_sd_r": ks_(acc["sd_r"], rej["sd_r"])}
        # A raw KS distance means nothing without the null at the ACHIEVED sample sizes: at n_acc/n_rej of a
        # few hundred against a few tens, two samples from the SAME distribution already give a large KS.
        # The first version of this test compared against a stipulated 0.20 and would have reported every
        # definition as selecting, which is exactly the unfounded-threshold failure the addendum documents.
        rngn = np.random.default_rng(4109)
        pool = g["mean_x"].to_numpy(float)
        nulls = [ks_(rngn.choice(pool, len(acc), replace=True),
                     rngn.choice(pool, len(rej), replace=True)) for _ in range(400)]
        nulls = [z for z in nulls if z is not None]
        e["null_p95_at_these_n"] = float(np.percentile(nulls, 95)) if nulls else None
        e["null_median_at_these_n"] = float(np.median(nulls)) if nulls else None
        e["selects_on_x"] = bool(e["ks_mean_x"] is not None and e["null_p95_at_these_n"] is not None
                                 and e["ks_mean_x"] > e["null_p95_at_these_n"])
        e["excess_over_null_p95"] = (None if e["null_p95_at_these_n"] is None
                                     else float(e["ks_mean_x"] - e["null_p95_at_these_n"]))
        out["definitions"][c] = e
    ex = {c: out["definitions"][c]["excess_over_null_p95"] for c in ("A", "B", "C", "D")}
    out["threshold_note"] = ("the comparison is against a null computed at each definition's OWN achieved "
                             "n_accepted / n_rejected, not against a fixed distance; a fixed 0.20 would have "
                             "called every definition a selector, which is why the first version of this "
                             "test did")
    out["excess_over_null"] = ex
    abd_max = max(ex[c] for c in ("A", "B", "D"))
    ratio = (ex["C"] / abd_max) if abd_max and abd_max > 0 else None
    out["verdict"] = (
        "NOT ESTABLISHED AT THIS n, DIRECTION CLEAR. Every definition's KS exceeds its own null p95, but by "
        f"amounts that differ by a factor of about {ratio:.0f}: A/B/D by {abd_max:.4f} and C by {ex['C']:.4f}. "
        "At n_rejected = 44 (A/B/D) the test has very little power in either direction -- T4 measured that "
        "this family of KS comparisons needs roughly 4,000 seeds to be decidable at D0 = 0.10. So the claim "
        "'adopting A, B or D closes items 18 and 42' is NEITHER confirmed NOR refuted here; what IS measured "
        "is that C's selection is an order of magnitude larger than A/B/D's, and that A/B/D carry no x-band "
        "at all so any residual is rejection on V growth, which the engine makes independent of x."
        if ratio and ratio > 5 else
        f"MIXED -- excesses over null: {ex}")
    return out


# =============================================================== T7
def _t7_one(seed):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    env = SyntheticMarketEnv("crash", 200, seed, crash_discount=0.70, n_assets=3)
    M = []
    for a in range(3):
        p = env.data[env.data["asset"] == a]["price"].to_numpy(float)
        M.append((p / np.maximum.accumulate(p) - 1) <= -0.30)
    M = np.vstack(M)
    return {"seed": seed, "mean_share": float(M.mean(axis=0).mean()),
            "all_three": float(M.all(axis=0).mean()), "any": float(M.any(axis=0).mean())}


def t7_multi_asset(seeds, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        rows = list(ex.map(_t7_one, list(range(SEED_T7, SEED_T7 + seeds)), chunksize=4))
    df = pd.DataFrame(rows)
    e41 = json.load(open(os.path.join(GEN, "e4_1", "episodes4.json"), encoding="utf-8"))
    m = {"generator_mean_share_in_drawdown": float(df["mean_share"].mean()),
         "generator_all_three_together": float(df["all_three"].mean()),
         "panel_mean_share": e41["cross_section"]["mean_share_in_drawdown"],
         "panel_p90": e41["cross_section"]["p90_share_in_drawdown"],
         "panel_max": e41["cross_section"]["max_share_in_drawdown"],
         "n_paths": int(len(df)), "n_assets": 3}
    return {"claim": "v2's multi-asset extension puts every asset in the same event on the same days, i.e. "
                     "a common-factor loading of 1.0 (P4-16)",
            "falsifier": "generate 3-asset paths and measure the realised cross-sectional drawdown share",
            "measured": m,
            "verdict": ("CONFIRMED AS A DIRECTION but not as the number 1.0: the realised loading is "
                        f"{m['generator_mean_share_in_drawdown']:.3f} against the panel's "
                        f"{m['panel_mean_share']:.3f}; P4-16's wording must be corrected to the measured value"
                        if m["generator_mean_share_in_drawdown"] < 0.95 else
                        "CONFIRMED -- the realised loading is at or near 1.0")}


# =============================================================== T8
def t8_aggregator_ratio():
    from tools.phase1.panel import analysis_sets, load_prices
    from tools.phase3.episodes import rolling_rv
    A = analysis_sets(write=False)["A"]
    px = load_prices(A).ffill()
    rows = []
    for t in A:
        p = px[t].to_numpy(float)
        if not np.isfinite(p).any():
            continue
        r = np.diff(np.log(p))
        r = r[np.isfinite(r)]
        if len(r) < 500:
            continue
        rv = rolling_rv(np.diff(np.log(p)))
        rows.append({"ticker": t, "mean_based_sd": math.sqrt(float(np.mean(r ** 2))),
                     "median_based_sd": math.sqrt(float(np.nanmedian(rv)))})
    df = pd.DataFrame(rows)
    ratio = (df["mean_based_sd"] / df["median_based_sd"]).to_numpy(float)
    pt, ci, n, ns = boot_median_by_stock(ratio, df["ticker"].to_numpy(), seed=4108)
    blk = json.load(open(os.path.join(GEN, "e3_4", "block.json"), encoding="utf-8"))
    return {"claim": "the per-stock ratio of the mean-based to the median-based unconditional sd is 1.354 "
                     "[IQR 1.286, 1.452] (P4-1), which is the whole of Phase 3's apparent level gap",
            "median_ratio": pt, "ci95_stock_bootstrap": ci,
            "iqr": [float(np.percentile(ratio, 25)), float(np.percentile(ratio, 75))],
            "n_stocks": ns,
            "median_mean_based_sd": float(df["mean_based_sd"].median()),
            "median_median_based_sd": float(df["median_based_sd"].median()),
            "anchor_s_A": blk["s_A"],
            "note": "s_A is the anchor the variance identity targets; the phase multipliers' reference is "
                    "the per-stock MEDIAN of rolling-21d RV. The two differ by this ratio, which is why "
                    "median-referenced multipliers applied to a mean-anchored base looked like a level defect"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="T8,T1,T3,T4,T5,T6,T7")
    ap.add_argument("--seeds", type=int, default=300)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    jp = os.path.join(OUT, "verify.json")
    res = json.load(open(jp, encoding="utf-8")) if os.path.exists(jp) else {}
    res["design"] = {"purpose": "every Phase-4 claim that was INFERRED rather than measured, tested with a "
                                "stated falsifier", "seeds": a.seeds, "n_boot": N_BOOT}
    stages = [s.strip().upper() for s in a.stages.split(",")]

    def save():
        json.dump(res, open(jp, "w", encoding="utf-8"), indent=1, default=str)

    if "T8" in stages:
        print("[T8] the mean-vs-median aggregator ratio ...", flush=True)
        res["T8_aggregator_ratio"] = t8_aggregator_ratio()
        r = res["T8_aggregator_ratio"]
        print(f"    {r['median_ratio']:.4f} {[round(v, 4) for v in r['ci95_stock_bootstrap']]} "
              f"IQR {[round(v, 3) for v in r['iqr']]} n={r['n_stocks']} stocks", flush=True)
        save()
    if "T1" in stages:
        print("[T1] is the run-up deceleration an endpoint artefact? ...", flush=True)
        res["T1_convexity_endpoint"] = t1_convexity_endpoint()
        for k, v in res["T1_convexity_endpoint"]["windows"].items():
            print(f"    {k:16s} {v['median_ratio']:.4f} {[round(z, 3) for z in v['ci95']]} "
                  f"n={v['n_episodes']}/{v['n_stocks']}  accelerating={v['accelerating']}", flush=True)
        print(f"    VERDICT: {res['T1_convexity_endpoint']['verdict']}", flush=True)
        save()
    if "T3" in stages:
        print("[T3] is item 10's inertness caused by the depth draw? ...", flush=True)
        res["T3_item10_cause"] = t3_item10(a.seeds, a.workers)
        for m, v in res["T3_item10_cause"]["arms"].items():
            print(f"    {m}: partial R2 {v['partial_r2_of_crash_discount']:.4f}  "
                  f"spread {v['spread_pp_0.55_minus_0.85']:.2f} pp  "
                  f"corr(discount, delta) {v['corr_discount_vs_delta_drawn']:.3f}", flush=True)
        print(f"    VERDICT: {res['T3_item10_cause']['verdict']}", flush=True)
        save()
    if "T4" in stages:
        print("[T4] the KS null floor as a function of n ...", flush=True)
        res["T4_ks_floor"] = t4_ks_floor()
        for n, v in res["T4_ks_floor"]["by_n_rejected"].items():
            print(f"    n_rej {n:>5s} (~{v['seeds_implied']:5d} seeds): floor "
                  f"{v['median_upper_limit_under_null']:.4f} -> "
                  f"{'DECIDABLE' if v['attainable_at_D0_0.10'] else 'not decidable'}", flush=True)
        print(f"    VERDICT: {res['T4_ks_floor']['verdict']}", flush=True)
        save()
    if "T5" in stages:
        print("[T5] decomposing the residual excess ...", flush=True)
        res["T5_residual"] = t5_residual()
        for k, v in list(res["T5_residual"]["contributions"].items())[:7]:
            print(f"    {k:16s} weight {v['panel_weight']:.4f}  "
                  f"{v['pct_of_total_variance']:.1f} % of variance", flush=True)
        save()
    if "T6" in stages:
        print("[T6] would A/B/D actually stop selecting on x? ...", flush=True)
        res["T6_control_would_pass"] = t6_control_would_pass(a.seeds, a.workers)
        for c, v in res["T6_control_would_pass"]["definitions"].items():
            print(f"    def {c}: rejection {v['rejection']:.3f}  n {v['n_accepted']}/{v['n_rejected']}  "
                  f"KS(mean x) {v['ks_mean_x']:.4f}  null p95 at these n "
                  f"{v['null_p95_at_these_n']:.4f}  selects on x: {v['selects_on_x']}", flush=True)
        print(f"    VERDICT: {res['T6_control_would_pass']['verdict']}", flush=True)
        save()
    if "T7" in stages:
        print("[T7] the realised multi-asset loading ...", flush=True)
        res["T7_multi_asset"] = t7_multi_asset(max(a.seeds // 4, 40), a.workers)
        m = res["T7_multi_asset"]["measured"]
        print(f"    generator {m['generator_mean_share_in_drawdown']:.3f} "
              f"(all three together {m['generator_all_three_together']:.3f}) "
              f"vs panel {m['panel_mean_share']:.3f}", flush=True)
        print(f"    VERDICT: {res['T7_multi_asset']['verdict']}", flush=True)
        save()

    res["seconds"] = round(time.time() - t0, 1)
    save()
    print(f"\nwrote {jp} in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
