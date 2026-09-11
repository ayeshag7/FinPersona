"""
v2.1 Phase 7 -- E7.7's measurements: the dividend switch's effect on every baseline, and the placebo directive's
length against the real one, TESTED rather than asserted (PREREG_PHASE_7.md 8; weakness 60).

    python -u -m tools.phase7.e7_7_small_items --seeds 100

`dividends`  Every baseline policy's metrics with `dividends=False` and `dividends=True` on the same paths, so the
             effect of D10 is reported per policy rather than claimed.  The switch's inertness when off is a test
             (`test_dividends_switch_inert_on_baselines`); this is the magnitude when on.

`placebo`    The placebo directive's token length against the real mandate's, from the pilot's own prompt records
             (`mandate_block_text` in each run's `meta.json`), as a two-sample test with its n -- the plan's
             weakness 60 says the matching is asserted, not tested.

Output: <out>/dividends.{csv,md,json}, <out>/placebo_length.{json,md}
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
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

OUT = os.path.join(GEN, "e7_7")
SCENARIOS = ("flat", "bull_trap", "crash", "sustained_bull")
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
METRICS = ("return_pct", "mdd_pct", "turnover", "cost_paid", "mcr_0.05", "band_mas", "mean_cash_share")


def _one(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    from evaluation.baselines_v2 import baseline_metrics
    from evaluation.targets import centre
    from simulation.dividends import dividend_schedule
    sc, seed, T = args
    env = SyntheticMarketEnv(sc, T, seed)
    sched = dividend_schedule(env, 1, T)
    payer = bool(sched.sum() > 0)
    out = []
    for persona in PERSONAS:
        c0 = centre(persona)
        off = baseline_metrics(env, persona, c0, random_seeds=3, dividends=False)
        on = baseline_metrics(env, persona, c0, random_seeds=3, dividends=True)
        for pol in sorted(set(off) & set(on)):
            row = {"scenario": sc, "seed": seed, "persona": persona, "policy": pol, "payer": payer,
                   "dps_total_per_share": float(sched.sum())}
            for m in METRICS:
                row[f"{m}_off"] = off[pol].get(m, np.nan)
                row[f"{m}_on"] = on[pol].get(m, np.nan)
            out.append(row)
    return out


def dividends(seeds: int, T: int, workers: int, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()
    jobs = [(sc, s, T) for sc in SCENARIOS for s in range(seeds)]
    rows = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for i, r in enumerate(ex.map(_one, jobs, chunksize=4), 1):
            rows.extend(r)
            if i % 100 == 0:
                print(f"  {i}/{len(jobs)} ({time.time() - t0:.0f} s)", flush=True)
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(out_dir, "dividends.csv"), index=False)
    summ = []
    for pol, g in t.groupby("policy"):
        row = {"policy": pol, "n_cells": int(len(g)), "payer_share": float(g["payer"].mean())}
        for m in METRICS:
            row[f"{m}_off"] = float(g[f"{m}_off"].mean())
            row[f"{m}_on"] = float(g[f"{m}_on"].mean())
            row[f"{m}_delta"] = float((g[f"{m}_on"] - g[f"{m}_off"]).mean())
        summ.append(row)
    s = pd.DataFrame(summ).sort_values("policy")
    s.to_csv(os.path.join(out_dir, "dividends_summary.csv"), index=False)
    doc = {"seeds_per_scenario": seeds, "T": T, "scenarios": list(SCENARIOS), "personas": list(PERSONAS),
           "payer_share": float(t["payer"].mean()), "n_cells": int(len(t)), "state": pin_state(),
           "construction": "dividends paid into cash on the generator's own announcement days; the price path is "
                           "NOT ex-dividend adjusted (envs/ is frozen), so a paying holder is a total-return holder "
                           "on a price-return path",
           "summary": s.to_dict("records"), "seconds": round(time.time() - t0),
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(doc, open(os.path.join(out_dir, "dividends.json"), "w", encoding="utf-8"), indent=1, default=float)
    L = [f"# E7.4 — the effect of paying dividends, per baseline policy", "",
         f"{seeds} seeds × {len(SCENARIOS)} scenarios × {len(PERSONAS)} personas, T = {T}; "
         f"{doc['payer_share']:.1%} of paths are payers (a per-seed draw at the FIT payer share, so a non-payer "
         f"path receives nothing even with the switch on). The price path is not ex-dividend adjusted.", "",
         "| policy | return % off → on (Δ) | MDD % off → on (Δ) | MCR(0.05) off → on (Δ) | band-MAS off → on (Δ) | "
         "turnover off → on (Δ) |", "|---|---|---|---|---|---|"]
    for _, r in s.iterrows():
        L.append(f"| {r['policy']} | {r['return_pct_off']:.3f} → {r['return_pct_on']:.3f} "
                 f"({r['return_pct_delta']:+.3f}) | {r['mdd_pct_off']:.3f} → {r['mdd_pct_on']:.3f} "
                 f"({r['mdd_pct_delta']:+.3f}) | {r['mcr_0.05_off']:.4f} → {r['mcr_0.05_on']:.4f} "
                 f"({r['mcr_0.05_delta']:+.4f}) | {r['band_mas_off']:.4f} → {r['band_mas_on']:.4f} "
                 f"({r['band_mas_delta']:+.4f}) | {r['turnover_off']:.3f} → {r['turnover_on']:.3f} "
                 f"({r['turnover_delta']:+.3f}) |")
    with open(os.path.join(out_dir, "dividends.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L), flush=True)


def placebo(results: str, out_dir: str):
    """Weakness 60: the placebo directive's length is ASSERTED to match the real one; here it is measured."""
    os.makedirs(out_dir, exist_ok=True)
    from scipy import stats
    rows = []
    for mp in sorted(glob.glob(os.path.join(results, "**", "*.meta.json"), recursive=True)):
        m = json.load(open(mp, encoding="utf-8"))
        txt = m.get("mandate_block_text") or ""
        arm = m["run_config"].get("arm")
        if not txt or arm is None:
            continue
        rows.append({"arm": arm, "persona": m["run_config"].get("persona"),
                     "chars": len(txt), "words": len(txt.split()),
                     "tokens_approx": len(re.findall(r"\w+|[^\w\s]", txt))})
    t = pd.DataFrame(rows)
    if t.empty:
        json.dump({"status": "NOT COMPUTABLE", "reason": "no run carries a mandate_block_text"},
                  open(os.path.join(out_dir, "placebo_length.json"), "w", encoding="utf-8"), indent=1)
        print("[placebo] NOT COMPUTABLE: no mandate_block_text in the run records"); return
    real = t[t.arm == "memory"]; plac = t[t.arm == "placebo_directive"]
    doc = {"n_by_arm": t.groupby("arm").size().to_dict(), "state": pin_state(),
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if len(real) >= 2 and len(plac) >= 2:
        for unit in ("chars", "words", "tokens_approx"):
            a, b = real[unit].to_numpy(float), plac[unit].to_numpy(float)
            u = stats.mannwhitneyu(a, b, alternative="two-sided")
            doc[unit] = {"real_mean": float(a.mean()), "real_sd": float(a.std(ddof=1)), "n_real": int(len(a)),
                         "placebo_mean": float(b.mean()), "placebo_sd": float(b.std(ddof=1)), "n_placebo": int(len(b)),
                         "ratio_placebo_over_real": float(b.mean() / a.mean()) if a.mean() else np.nan,
                         "mannwhitney_u": float(u.statistic), "p": float(u.pvalue)}
        doc["rule"] = ("weakness 60: the matching is TESTED, not asserted. n is small (one model, one seed), so a "
                       "non-significant p is not evidence of matching -- the ratio and its n are the statement.")
    else:
        doc["status"] = "NOT COMPUTABLE"
        doc["reason"] = f"needs >= 2 runs in each of the memory and placebo_directive arms; found {len(real)} and {len(plac)}"
    json.dump(doc, open(os.path.join(out_dir, "placebo_length.json"), "w", encoding="utf-8"), indent=1, default=float)
    L = ["# E7.7 — placebo directive length against the real directive's, measured", "",
         f"From the pilot's own prompt records (`mandate_block_text`); n by arm: {doc['n_by_arm']}.", ""]
    if "chars" in doc:
        L += ["| unit | real (mean ± sd, n) | placebo (mean ± sd, n) | ratio | Mann–Whitney p |",
              "|---|---|---|---|---|"]
        for unit in ("chars", "words", "tokens_approx"):
            d = doc[unit]
            L.append(f"| {unit} | {d['real_mean']:.1f} ± {d['real_sd']:.1f} (n = {d['n_real']}) | "
                     f"{d['placebo_mean']:.1f} ± {d['placebo_sd']:.1f} (n = {d['n_placebo']}) | "
                     f"{d['ratio_placebo_over_real']:.3f} | {d['p']:.3f} |")
        L += ["", doc["rule"]]
    else:
        L += [f"**{doc.get('status')}** — {doc.get('reason')}"]
    with open(os.path.join(out_dir, "placebo_length.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="dividends,placebo")
    ap.add_argument("--seeds", type=int, default=100)
    ap.add_argument("--T", type=int, default=200)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--results", default=os.path.join(ROOT, "results_v2_pilot"))
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    for st in a.stages.split(","):
        st = st.strip()
        if st == "dividends":
            dividends(a.seeds, a.T, a.workers, a.out)
        elif st == "placebo":
            placebo(a.results, a.out)
        else:
            raise SystemExit(f"unknown stage {st!r}")


if __name__ == "__main__":
    main()
