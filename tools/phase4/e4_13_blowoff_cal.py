"""
E4.13 -- the blow-off variance multiplier's closed loop (P4-11's outstanding half).

    python -m tools.phase4.e4_13_blowoff_cal [--iters 3] [--cal-seeds 400] [--verify-seeds 1200]

P4-11 revived the blow-off LABEL: v2 assigned it ex post in `events.relabel_blowoff`, so the driver never saw
it and its variance multiplier was dead code.  `volatility.json` records blow-off at MANIA's value (1.345)
precisely because of that, and Phase 3's own label discloses it as a documented shortfall.  With the label
alive the multiplier is no longer inert and needs a value of its own, which this module calibrates.

The value is written to `events.json` (Phase 4's file), NOT to `volatility.json`: Phase 3's parameter file is
frozen and this is a Phase-4 decision about Phase-4 machinery.  The generator applies it as an override on
`GJRParams.mult["blow-off"]`.

Target: the panel's blow-off/mania realised-variance ratio on the CORRECTED run-up calm reference (E4.1's
120 days AFTER the run-up start; E3.3's window sits at a post-crash trough).  Its CI is computed here by a
stock bootstrap of the ratio itself rather than combined from the two separate CIs.

Method: the same first-order closed loop `e3_4_mechanism.py` uses -- m <- m x (target / realised), iterated,
then verified at a larger seed count with a path-cluster bootstrap.  `schedule_mode` is pinned throughout.

Output: docs/env_v2/generated/v2_1/e4_13/blowoff_cal.{json,md}
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
OUT = os.path.join(GEN, "e4_13")
SCHED = "v21"
SEED_CAL = 330000
SEED_VER = 332000
N_BOOT = 2000


def panel_target():
    """The panel's blow-off/mania variance ratio on the corrected reference, with a stock bootstrap of the
    RATIO (not of the two multipliers separately)."""
    ru = pd.read_csv(os.path.join(GEN, "e4_1", "runup4.csv"))
    d = ru[pd.to_numeric(ru.get("rv_mania"), errors="coerce").notna()
           & pd.to_numeric(ru.get("rv_blow-off"), errors="coerce").notna()].copy()
    bo = pd.to_numeric(d["rv_blow-off"], errors="coerce").to_numpy(float)
    ma = pd.to_numeric(d["rv_mania"], errors="coerce").to_numpy(float)
    tick = d["ticker"].to_numpy()
    stocks = np.array(sorted(set(tick.tolist())))
    idx_by = {t: np.where(tick == t)[0] for t in stocks}
    rng = np.random.default_rng(4130)
    bs = []
    for _ in range(N_BOOT):
        ii = np.concatenate([idx_by[t] for t in rng.choice(stocks, len(stocks), replace=True)])
        bs.append(float(np.nanmean(bo[ii]) / np.nanmean(ma[ii])))
    return {"ratio": float(np.nanmean(bo) / np.nanmean(ma)),
            "ci95": [float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))],
            "n_episodes": int(len(d)), "n_stocks": int(len(stocks)),
            "reference": "E4.1's corrected run-up calm window (120 d AFTER the start)"}


def _one(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    seed, mult = args
    env = SyntheticMarketEnv("bull_trap", 200, seed,
                             config={"schedule_mode": SCHED, "blowoff_mult": float(mult)})
    d = env.data[env.data["asset"] == 0]
    ph = d["phase"].to_numpy(object)[1:]
    r = np.diff(np.log(d["price"].to_numpy(float)))
    out = {"seed": seed}
    for k in ("mania", "blow-off"):
        m = ph == k
        if m.sum() >= 10:
            out["rv_" + k] = float(np.mean(r[m] ** 2))
            out["n_" + k] = int(m.sum())
    return out


def pmap(items, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_one, items, chunksize=4))


def ratio_ci(rows, n_boot=N_BOOT, seed=4131):
    pairs = [(r.get("rv_blow-off"), r.get("n_blow-off"), r.get("rv_mania"), r.get("n_mania")) for r in rows]
    pairs = [(a, b, c, d) for a, b, c, d in pairs if a is not None and c is not None]
    if len(pairs) < 20:
        return None, None, len(pairs)
    A = np.array([[a * b, b, c * d, d] for a, b, c, d in pairs], float)
    pt = (A[:, 0].sum() / A[:, 1].sum()) / (A[:, 2].sum() / A[:, 3].sum())
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(n_boot):
        S = A[rng.integers(0, len(A), len(A))]
        bs.append((S[:, 0].sum() / S[:, 1].sum()) / (S[:, 2].sum() / S[:, 3].sum()))
    return float(pt), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], len(pairs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=3)
    ap.add_argument("--cal-seeds", type=int, default=400)
    ap.add_argument("--verify-seeds", type=int, default=1200)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    from envs.v2.volatility_params import MULT
    tgt = panel_target()
    m0 = float(MULT["mania"])
    print(f"[target] panel blow-off/mania {tgt['ratio']:.4f} {[round(v,4) for v in tgt['ci95']]} "
          f"n={tgt['n_episodes']}/{tgt['n_stocks']}", flush=True)
    print(f"[start ] volatility.json records blow-off at mania's value {m0:.4f} "
          f"(a placeholder, because the v2 label was dead)", flush=True)

    hist = []
    m = m0
    for it in range(a.iters):
        rows = pmap([(s, m) for s in range(SEED_CAL, SEED_CAL + a.cal_seeds)], a.workers)
        got, ci, n = ratio_ci(rows, n_boot=400)
        hist.append({"iteration": it, "mult": float(m), "realised": got, "n": n})
        print(f"    iter {it}: mult {m:.4f} -> realised {got:.4f} (target {tgt['ratio']:.4f}, n={n})",
              flush=True)
        if got is None or got <= 0:
            break
        m = m * (tgt["ratio"] / got)

    rows = pmap([(s, m) for s in range(SEED_VER, SEED_VER + a.verify_seeds)], a.workers)
    got, ci, n = ratio_ci(rows)
    inside = bool(ci and tgt["ci95"][0] <= got <= tgt["ci95"][1])
    # the incumbent, for the before column
    rows0 = pmap([(s, m0) for s in range(SEED_VER, SEED_VER + a.verify_seeds)], a.workers)
    got0, ci0, _ = ratio_ci(rows0)

    res = {"design": {"schedule_mode": SCHED + " (pinned)", "iterations": a.iters,
                      "cal_seeds": a.cal_seeds, "verify_seeds": a.verify_seeds, "n_boot": N_BOOT,
                      "method": "first-order closed loop m <- m x (target / realised), as e3_4_mechanism.py "
                                "uses, then verified at a larger seed count",
                      "why": "P4-11 revived the blow-off label; volatility.json records the multiplier at "
                             "mania's value because the v2 label was dead. The calibrated value is written "
                             "to events.json, not to Phase 3's frozen volatility.json."},
           "panel_target": tgt,
           "incumbent": {"mult": m0, "realised": got0, "ci95": ci0,
                         "inside_panel_ci": bool(ci0 and tgt["ci95"][0] <= got0 <= tgt["ci95"][1])},
           "calibration_history": hist,
           "adopted": {"mult": float(m), "realised": got, "ci95": ci, "n_paths": n,
                       "inside_panel_ci": inside,
                       "verdict": "CALIBRATED" if inside else "NOT REACHED"},
           }
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(os.path.join(OUT, "blowoff_cal.json"), "w", encoding="utf-8"), indent=1, default=str)
    L = ["# E4.13 - the blow-off multiplier's closed loop", "",
         "`python -m tools.phase4.e4_13_blowoff_cal` - P4-11's outstanding half.", "",
         f"Panel target (corrected reference): **{tgt['ratio']:.4f} "
         f"[{tgt['ci95'][0]:.4f}, {tgt['ci95'][1]:.4f}]**, n = {tgt['n_episodes']} run-ups / "
         f"{tgt['n_stocks']} stocks.", "",
         "| | multiplier | realised blow-off/mania | 95 % CI | inside the panel CI |", "|---|---|---|---|---|",
         f"| incumbent (mania's value) | {m0:.4f} | {got0:.4f} | [{ci0[0]:.4f}, {ci0[1]:.4f}] | "
         f"**{res['incumbent']['inside_panel_ci']}** |",
         f"| **calibrated** | **{m:.4f}** | **{got:.4f}** | [{ci[0]:.4f}, {ci[1]:.4f}] | **{inside}** |", "",
         "## Closed loop", "", "| iteration | multiplier | realised |", "|---|---|---|"]
    for h in hist:
        L.append(f"| {h['iteration']} | {h['mult']:.4f} | {h['realised']:.4f} |")
    L += ["", f"Verified at {a.verify_seeds} seeds. Verdict: **{res['adopted']['verdict']}**.", ""]
    open(os.path.join(OUT, "blowoff_cal.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"\nadopted mult {m:.4f} -> realised {got:.4f} {['%.4f' % v for v in ci]} "
          f"({res['adopted']['verdict']})")
    print(f"wrote {OUT}/blowoff_cal.json in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
