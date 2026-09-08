"""
v2.1 Phase 6 -- E6.5: the L1 pass rule derived from the noise floor implied by the x process, not the hard-coded 1 %.

Plan Section 10.2 (E6.5): "the pass rule derived from the noise floor implied by the x process (the share of steps
that any level-free estimate could hit given sd(x)), not a hard-coded 1 %"; weakness 32.

The derivation.  A candidate V_hat is an algebraic function of shown fields.  Because P = V e^x, a candidate that
carries no information about x beyond the price path can do no better than V_hat = P e^{-x_hat} with x_hat a
level-free estimate of x, so its absolute percentage error is |e^{x - x_hat} - 1| ~ |x - x_hat|.  Two ceilings
follow from the parameters in force, with nothing chosen:

  trivial     x_hat = 0 (V_hat = k P, "price itself"): the share of steps within a tolerance tau is
              P(|x| <= tau) -- from the stationary distribution of x (Gaussian at s_x for the analytic form) and,
              empirically, from the generator's own x on the panel
  informed    x_hat the best level-free reader: its residual sd is at least s_x sqrt(1 - B) with B the Appendix-B
              bound on R^2(x) (E6.6), so the share within tau is at most 2 Phi(tau / (s_x sqrt(1 - B))) - 1

A candidate whose within-tau share exceeds the informed ceiling (plus the sampling half-width of a share at the
panel's n of paths, cluster-bootstrapped) is reading V through something other than the price path -- that is
what L1 exists to find.  A candidate below the trivial line is worse than price itself.  The rule is stated for
tau in {1 %, 2 %, 5 %}; the 5 % share is the one the extended set (E5.7b) already reports with intervals.

The measured side is read from the stored L1 tables (the after-state audit's L1 and the extended-set run) so
that the derived rule is applied to numbers already on disk, and the verdict under BOTH rules (the 1 % floor as
registered in v2, and the derived ceiling) is reported.

Usage:
    python -u tools/phase6/e6_5_floor.py [--bound-json docs/env_v2/generated/v2_1/e6_6/bound.json]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from typing import Dict, List

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
try:                                              # the Windows console is cp1252; the markdown carries Greek letters
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e6_5")
PANEL = os.path.join(GEN, "_panels", "sep_phase5_after.pkl")
L1_CSV = os.path.join(GEN, "e5_after", "audit_after_levelfree_L1.csv")
L1EXT = os.path.join(GEN, "e5_7b", "final", "l1ext.json")
TAUS = (0.01, 0.02, 0.05)


def analytic_shares(s_x: float, B: float) -> Dict:
    out = {}
    for tau in TAUS:
        triv = 2 * stats.norm.cdf(tau / s_x) - 1
        sd_res = s_x * math.sqrt(max(1e-12, 1.0 - B))
        inf = 2 * stats.norm.cdf(tau / sd_res) - 1
        out[f"tau_{tau}"] = {"trivial_gaussian": float(triv), "informed_ceiling_gaussian": float(inf), "residual_sd": sd_res}
    return out


def empirical_shares(panel: pd.DataFrame, n_boot: int = 500, seed: int = 650001) -> Dict:
    """P(|x| <= tau) on the generator's own x, all rows, with a cluster bootstrap over paths (the trivial line
    as the generator actually realises it -- x is not Gaussian: jumps, events)."""
    x = panel["x"].to_numpy(float)
    path = pd.factorize(panel["scenario"].astype(str) + "-" + panel["seed"].astype(str))[0]
    n_paths = int(path.max()) + 1
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n_paths, (n_boot, n_paths))
    cnt = np.bincount(path, minlength=n_paths).astype(float)
    out = {}
    for tau in TAUS:
        hit = (np.abs(x) <= tau).astype(float)
        c = np.bincount(path, weights=hit, minlength=n_paths)
        draws = np.array([c[ix].sum() / cnt[ix].sum() for ix in idx])
        out[f"tau_{tau}"] = {"share": float(hit.mean()), "ci95": [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))],
                             "halfwidth": float((np.percentile(draws, 97.5) - np.percentile(draws, 2.5)) / 2)}
    out["n_rows"] = int(len(x)); out["n_paths"] = n_paths
    # by scenario, for the record
    out["by_scenario"] = {}
    for sc, g in panel.groupby("scenario"):
        out["by_scenario"][sc] = {f"tau_{tau}": float(np.mean(np.abs(g["x"].to_numpy(float)) <= tau)) for tau in TAUS}
    return out


def measured_candidates() -> List[Dict]:
    rows = []
    if os.path.exists(L1_CSV):
        d = pd.read_csv(L1_CSV)
        for _, r in d.iterrows():
            rows.append({"source": "e5_after L1", **{k: (r[k] if k in d.columns else None) for k in d.columns}})
    if os.path.exists(L1EXT):
        with open(L1EXT, "r", encoding="utf-8") as fh:
            e = json.load(fh)
        # the extended set (pairwise geometric means, least-squares combinations, the median of the valuation
        # candidates) keyed by formula, plus the run's own 'best' and 'price_itself' rows
        for name, v in (e.get("extended") or {}).items():
            if isinstance(v, dict) and "within_5pct" in v:
                rows.append({"source": "e5_7b/final l1ext", "candidate": name, **v})
        b = e.get("best")
        if isinstance(b, dict) and "within_5pct" in b:
            rows.append({"source": "e5_7b/final l1ext (best)", "candidate": f"best = {b.get('candidate')}", **{k: v for k, v in b.items() if k != "candidate"}})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--bound-json", default=os.path.join(GEN, "e6_6", "bound.json"))
    a = ap.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    b = json.load(open(a.bound_json, encoding="utf-8"))["bound"]
    s_x = float(b["adopted"]["s_x"]); B_day = float(b["adopted"]["day_T"]); B_avg = float(b["adopted"]["window_avg"])
    panel = pd.read_pickle(PANEL)
    emp = empirical_shares(panel)
    res = {"what": "E6.5: the L1 pass rule derived from the x process' noise floor (trivial and informed ceilings)",
           "inputs": {"s_x": s_x, "bound_day_T": B_day, "bound_window_avg": B_avg, "bound_source": os.path.relpath(a.bound_json, ROOT).replace("\\", "/"),
                      "panel": os.path.relpath(PANEL, ROOT).replace("\\", "/")},
           "analytic": {"at_bound_day_T": analytic_shares(s_x, B_day), "at_bound_window_avg": analytic_shares(s_x, B_avg)},
           "empirical_trivial": emp,
           "rule": {"statement": "for tau in {1 %, 2 %, 5 %}: a candidate's within-tau share may not exceed the informed ceiling "
                                 "2*Phi(tau / (s_x*sqrt(1 - B))) - 1 (B = the Appendix-B day-T bound) plus the share's sampling "
                                 "half-width at the panel's n of paths; the trivial line is the generator's own P(|x| <= tau) with "
                                 "its CI, reported beside price itself",
                    "replaces": "the hard-coded NOISE_FLOOR = 0.01 and the 'share of steps with APE above 1 %' rule (weakness 32)",
                    "derived_from": "the parameters in force (s_x by the volatility identity, h FIT) through Appendix B; nothing chosen"},
           "measured": measured_candidates(), "seconds": round(time.time() - t0, 1),
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    # verdicts of the measured candidates at tau = 5 % under the derived rule
    ceil5 = res["analytic"]["at_bound_day_T"]["tau_0.05"]["informed_ceiling_gaussian"]
    hw5 = emp["tau_0.05"]["halfwidth"]
    res["rule"]["ceiling_5pct"] = ceil5; res["rule"]["halfwidth_5pct"] = hw5; res["rule"]["margin_5pct"] = ceil5 + hw5
    verdicts = []
    for m in res["measured"]:
        w5 = m.get("within_5pct")
        if w5 is None and "share_within_5pct" in m:
            w5 = m["share_within_5pct"]
        if w5 is not None and np.isfinite(float(w5)):
            verdicts.append({"source": m["source"], "candidate": m.get("candidate") or m.get("formula") or m.get("name"),
                             "within_5pct": float(w5), "pass_derived": bool(float(w5) <= ceil5 + hw5),
                             "above_trivial_empirical": bool(float(w5) > emp["tau_0.05"]["share"])})
    res["verdicts_5pct"] = verdicts
    with open(os.path.join(OUT, "floor.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=float)
    L = ["# E6.5 — the L1 noise floor derived from the x process", "",
         f"s_x = {s_x:.4f} (the volatility identity, with the jumps), Appendix-B bound B = {B_day:.4f} (day 200) / {B_avg:.4f} (window average); "
         f"panel `{res['inputs']['panel']}` ({emp['n_paths']} paths, {emp['n_rows']:,} rows).", "",
         "| τ | trivial (Gaussian, x̂ = 0) | trivial (empirical P(\\|x\\| ≤ τ) [CI]) | informed ceiling at B(day 200) | at B(window avg) |",
         "|---|---|---|---|---|"]
    for tau in TAUS:
        k = f"tau_{tau}"
        ad, aa, e = res["analytic"]["at_bound_day_T"][k], res["analytic"]["at_bound_window_avg"][k], emp[k]
        L.append(f"| {tau:.0%} | {ad['trivial_gaussian']:.3f} | {e['share']:.3f} [{e['ci95'][0]:.3f}, {e['ci95'][1]:.3f}] | "
                 f"**{ad['informed_ceiling_gaussian']:.3f}** | {aa['informed_ceiling_gaussian']:.3f} |")
    L += ["", f"**Derived rule (τ = 5 %):** within-5 % share ≤ {ceil5:.3f} + {hw5:.3f} = **{ceil5 + hw5:.3f}**. {res['rule']['statement']}.", "",
          "| candidate (source) | within-5 % | above the trivial line | passes the derived ceiling |", "|---|---|---|---|"]
    for v in verdicts:
        L.append(f"| {v['candidate']} ({v['source']}) | {v['within_5pct']:.3f} | {'yes' if v['above_trivial_empirical'] else 'no'} | "
                 f"{'**PASS**' if v['pass_derived'] else '**FAIL**'} |")
    L.append("")
    with open(os.path.join(OUT, "floor.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print("\n".join(L[:12]))
    print(f"-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
