"""
v2.1 Phase 7 -- E7.1b, part 2: theta_cost tested as a POLICY RULE, not only as a per-decision break-even.

    python -u -m tools.phase7.e7_1b_theta_cost_policy --seeds 100 --workers 6

WHY THIS EXISTS.  E7.1b derives theta_cost = 2c/f = 0.0020 as the mispricing at which ONE full reallocation's
expected profit over one half-life pays for ONE round trip, and `e7_1/theta_cost_var.json` verifies that closed
form numerically against the real `PortfolioV2`.  What neither establishes is the thing the number is used for:
that a POLICY which acts at theta = 0.0020 is better off than one which acts at 0.05.  The derivation charges the
round trip once; a policy acting at a low threshold pays it again every time x crosses back, and x crosses a low
threshold far more often than a high one.  Nothing in the phase had measured that, because every theta-dependent
policy in `e7_panel` ACTS at theta = 0.05 -- the theta sweep changes the yardstick, not the policy.

The experiment.  On the same paths and personas as the panel, run the mandate-conditional oracle **acting** at each
candidate theta, at the implemented 5 bp tier and again at 0 bp, and measure what each costs and earns:

    net return, gross return (0 bp), cost drag = gross - net, turnover, trade count, MCR against its own theta

The oracle knows x exactly, so this is the most favourable case for a low threshold -- exactly the case
theta_cost's derivation assumes (it presumes the sign of x is known).  If acting at theta_cost is not the best
net-return rule even here, the closed form is a per-decision break-even and not a policy rule, and the report says
so rather than leaving the reader to assume otherwise.

Output: <out>/theta_cost_policy.{csv,json,md}
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
os.environ.setdefault("OMP_NUM_THREADS", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

from tools.phase5.common import GEN, pin_state  # noqa: E402

OUT = os.path.join(GEN, "e7_1b")
SCENARIOS = ("flat", "bull_trap", "crash", "sustained_bull")
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
COST_BP = 5.0            # the implemented tier
INITIAL = 10000.0


def acting_thetas():
    """The candidate acting thresholds: the grid plus the derived values, read from E7.1's own files."""
    from tools.phase7.e7_rescore import derived_thetas, theta_set
    th, labels = theta_set(derived_thetas())
    return th, labels


def _one(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    from evaluation.baselines_v2 import baseline_policies, _run_policy
    from evaluation.targets import centre
    from evaluation.scoring import regret_terms
    sc, seed, T, thetas = args
    env = SyntheticMarketEnv(sc, T, seed)
    d = env.data[env.data["asset"] == 0].reset_index(drop=True)
    x = d["x"].to_numpy(float)
    rows = []
    for persona in PERSONAS:
        c0 = centre(persona)
        for th in thetas:
            pol = baseline_policies(persona, c0, theta=th, random_seeds=0)["mandate_conditional_oracle"][0]
            out = {}
            for tag, cbp in (("net", COST_BP), ("gross", 0.0)):
                f = _run_policy(env, c0, pol, cost_bp=cbp)
                pv = f["Portfolio_Value"].to_numpy(float)
                out[tag] = {"return_pct": (pv[-1] / INITIAL - 1) * 100.0,
                            "turnover": float(f["Traded_Value"].sum() / INITIAL),
                            "trade_count": int((f["Traded_Value"].to_numpy(float) > 0).sum()),
                            "cost_paid": float(f["Cost_Paid"].sum()),
                            "C": f["Cash_Share"].to_numpy(float)}
            t = regret_terms(out["net"]["C"], x, th, persona, prev_target=float(out["net"]["C"][0]))
            rows.append({"scenario": sc, "seed": int(seed), "persona": persona, "acting_theta": float(th),
                         "return_net_pct": out["net"]["return_pct"], "return_gross_pct": out["gross"]["return_pct"],
                         "cost_drag_pct": out["gross"]["return_pct"] - out["net"]["return_pct"],
                         "turnover": out["net"]["turnover"], "trade_count": out["net"]["trade_count"],
                         "cost_paid": out["net"]["cost_paid"],
                         "mcr_own_theta": t["mcr"], "coverage": t["coverage"],
                         "oracle_switches": t["oracle_switches"]})
    return rows


def _boot_ci(v, seeds, rng, n_boot=500):
    v = np.asarray(v, float); seeds = np.asarray(seeds)
    ok = np.isfinite(v); v, seeds = v[ok], seeds[ok]
    if len(v) < 3:
        return (float("nan"),) * 3
    us, inv = np.unique(seeds, return_inverse=True)
    sums = np.bincount(inv, weights=v, minlength=len(us))
    cnts = np.bincount(inv, minlength=len(us)).astype(float)
    pick = rng.integers(0, len(us), size=(n_boot, len(us)))
    draws = sums[pick].sum(axis=1) / cnts[pick].sum(axis=1)
    return float(np.mean(v)), float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=100)
    ap.add_argument("--T", type=int, default=200)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    thetas, labels = acting_thetas()
    print(f"[policy] {len(thetas)} acting thetas x {len(SCENARIOS)} scenarios x {a.seeds} seeds x "
          f"{len(PERSONAS)} personas, at {COST_BP} bp and at 0 bp", flush=True)
    jobs = [(sc, s, a.T, thetas) for sc in SCENARIOS for s in range(a.seeds)]
    rows = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for i, r in enumerate(ex.map(_one, jobs, chunksize=4), 1):
            rows.extend(r)
            if i % 100 == 0:
                print(f"  {i}/{len(jobs)} ({time.time() - t0:.0f} s)", flush=True)
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(a.out, "theta_cost_policy.csv"), index=False)

    rng = np.random.default_rng(717002)
    summ = []
    for th, g in t.groupby("acting_theta"):
        net = _boot_ci(g["return_net_pct"].to_numpy(), g["seed"].to_numpy(), rng)
        gross = _boot_ci(g["return_gross_pct"].to_numpy(), g["seed"].to_numpy(), rng)
        drag = _boot_ci(g["cost_drag_pct"].to_numpy(), g["seed"].to_numpy(), rng)
        summ.append({"acting_theta": float(th), "labels": "|".join(labels[round(float(th), 6)]),
                     "return_net_pct": net[0], "net_lo": net[1], "net_hi": net[2],
                     "return_gross_pct": gross[0], "cost_drag_pct": drag[0],
                     "trades_per_run": float(g["trade_count"].mean()),
                     "turnover": float(g["turnover"].mean()),
                     "cost_paid": float(g["cost_paid"].mean()),
                     "mcr_own_theta": float(g["mcr_own_theta"].mean()),
                     "n_cells": int(len(g)), "n_seeds": int(g["seed"].nunique())})
    s = pd.DataFrame(summ).sort_values("acting_theta")
    s.to_csv(os.path.join(a.out, "theta_cost_policy_summary.csv"), index=False)

    best_net = float(s.loc[s["return_net_pct"].idxmax(), "acting_theta"])
    best_gross = float(s.loc[s["return_gross_pct"].idxmax(), "acting_theta"])
    th_cost = json.load(open(os.path.join(GEN, "e7_1", "theta_cost_var.json"), encoding="utf-8"))["theta_cost"]["value"]
    at_cost = s[np.isclose(s["acting_theta"], th_cost)]
    at_best = s[np.isclose(s["acting_theta"], best_net)]
    gap = (float(at_best["return_net_pct"].iloc[0]) - float(at_cost["return_net_pct"].iloc[0])) if len(at_cost) else float("nan")
    doc = {"meta": {"seeds_per_scenario": a.seeds, "T": a.T, "cost_bp": COST_BP, "state": pin_state(),
                    "acting_thetas": thetas, "seconds": round(time.time() - t0),
                    "question": "theta_cost is a PER-DECISION break-even (one round trip). Is it also the best "
                                "acting threshold for a POLICY, which pays the round trip again on every crossing?",
                    "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
           "theta_cost_derived": th_cost,
           "best_acting_theta_by_net_return": best_net,
           "best_acting_theta_by_gross_return": best_gross,
           "net_return_gap_best_minus_theta_cost_pp": gap,
           "trades_at_theta_cost": float(at_cost["trades_per_run"].iloc[0]) if len(at_cost) else float("nan"),
           "trades_at_best": float(at_best["trades_per_run"].iloc[0]),
           "cost_drag_at_theta_cost_pp": float(at_cost["cost_drag_pct"].iloc[0]) if len(at_cost) else float("nan"),
           "summary": s.to_dict("records")}
    json.dump(doc, open(os.path.join(a.out, "theta_cost_policy.json"), "w", encoding="utf-8"), indent=1, default=float)

    L = ["# E7.1b part 2 — theta_cost tested as a policy rule", "",
         f"The mandate-conditional oracle **acting** at each candidate theta, on {a.seeds} seeds x "
         f"{len(SCENARIOS)} scenarios x {len(PERSONAS)} personas, at {COST_BP} bp per trade and again at 0 bp. "
         f"The oracle knows x exactly, so this is the most favourable case for a low threshold — which is the case "
         f"theta_cost's derivation assumes. Cluster-bootstrap 95 % intervals over seeds.", "",
         "| acting theta | label | net return % | gross return % (0 bp) | cost drag pp | trades per run | "
         "turnover | MCR at its own theta |", "|---|---|---|---|---|---|---|---|"]
    for _, r in s.iterrows():
        L.append(f"| {r['acting_theta']:.6g} | {r['labels']} | **{r['return_net_pct']:.3f}** "
                 f"[{r['net_lo']:.3f}, {r['net_hi']:.3f}] | {r['return_gross_pct']:.3f} | "
                 f"{r['cost_drag_pct']:.3f} | {r['trades_per_run']:.1f} | {r['turnover']:.2f} | "
                 f"{r['mcr_own_theta']:.4f} |")
    L += ["", f"**Derived theta_cost = {th_cost:.4f}. Best acting theta by net return = {best_net:.6g}"
              f"** (by gross return {best_gross:.6g}). Acting at theta_cost costs "
              f"{doc['trades_at_theta_cost']:.0f} trades a run against {doc['trades_at_best']:.0f} at the best, a "
              f"cost drag of {doc['cost_drag_at_theta_cost_pp']:.3f} pp, and gives up "
              f"{gap:.3f} pp of net return against the best acting threshold.", ""]
    with open(os.path.join(a.out, "theta_cost_policy.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L), flush=True)


if __name__ == "__main__":
    main()
