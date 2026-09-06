"""
E4.18 -- the CALM-TRAINED level-free surrogate on the Phase-4 hand-over state.

    python -m tools.phase4.e4_18_calm_trained [--n-boot 500] [--out DIR]

**Why this exists and E4.17 is not enough.**  `evaluation/leakage_audit.py::l2_surrogate` fits one model on
ALL rows (GroupKFold by path) and only then masks by phase group -- `leakage_audit.py` lines 297-300.  Its
"calm R2" is therefore a CROSS-PHASE-trained model scored against calm-only variance, which is not the
quantity the Phase-4 brief singles out.  That quantity is Phase 3's **calm-TRAINED** level-free
R2(x) = +0.349 [0.322, 0.374], of which E3.8 attributed about 0.20 to the process + GJR + jump stack,
leaving **about +0.15 for the events and the sentiment feedback** -- the part a Phase-4 event redesign could
have moved.  Only `tools/phase3/e3_9_calm_trained.py` computes it, and it hardcodes the Phase-2 and Phase-3
panels.

This module imports that module's estimator unchanged -- no reimplementation, so the comparison cannot drift
on the estimator -- and points it at the Phase-4 panel.  Phase 3 is RE-RUN here rather than quoted from
`e3_9/calm_trained.json`, so both states pass through one code path and one library version in one process;
reproducing Phase 3's stored +0.349 is itself the check that the comparison is sound.

Writes to its own directory (P4-19: Phase-3 tools hardcode Phase-3 output names and one of them overwrote
`e3_after_checklist.*` earlier in this phase).  Model fits stay on the reference machine by the
reproducibility guard -- never offloaded.

Output: <out>/calm_trained_phase4.{json,md}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

from tools.phase3.e3_9_calm_trained import calm_trained, published_rows, best  # noqa: E402

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")

# (state, panel pickle, the stored audit pickle that carries `shown_fields` for that state)
STATES = [
    ("phase3", os.path.join(GEN, "_panels", "sep_phase3_after.pkl"),
     os.path.join(GEN, "e3_after", "audit_after_levelfree.pkl")),
    ("phase4", os.path.join(GEN, "_panels", "sep_phase4_after.pkl"),
     os.path.join(GEN, "e4_16", "audit_after_levelfree.pkl")),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-boot", type=int, default=500)
    ap.add_argument("--out", default=os.path.join(GEN, "e4_18"))
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(a.out, exist_ok=True)

    from envs.v2 import events_params as EP
    if not EP.PRESENT:
        raise SystemExit("events.json is absent: this measures the DEPLOYED state and there is none")
    print(f"[state] blowoff {EP.BLOWOFF_MODE} mult {EP.BLOWOFF_MULT} | "
          f"post_top {EP.POST_TOP_MODE}/{EP.POST_TOP_HALF_LIFE}", flush=True)

    res = {"what": "E4.18: the level-free surrogate TRAINED ON CALM ROWS ONLY, on the Phase-3 and Phase-4 "
                   "hand-over panels, under one code path in one process.",
           "why": "the published audit is cross-phase-trained (leakage_audit.py:297-300); the brief's quantity "
                  "is the calm-TRAINED level-free R2(x), Phase 3 = +0.349 [0.322, 0.374], of which E3.8 "
                  "attributed ~0.20 to the process+GJR+jump stack, leaving ~+0.15 for events and sentiment.",
           "estimator": "tools.phase3.e3_9_calm_trained.calm_trained, imported unchanged",
           "n_boot": a.n_boot, "states": {}}

    for state, panel_p, audit_p in STATES:
        if not (os.path.exists(panel_p) and os.path.exists(audit_p)):
            print(f"  (missing for {state}: {panel_p} / {audit_p})", flush=True)
            continue
        print(f"[{state}] {os.path.relpath(panel_p, ROOT)}", flush=True)
        pub, shown = published_rows(audit_p)
        panel = pd.read_pickle(panel_p)
        ct = calm_trained(panel, shown, a.n_boot)
        res["states"][state] = {"panel": os.path.relpath(panel_p, ROOT),
                                "published_cross_phase_trained": pub, "calm_trained": ct,
                                "n_rows_panel": int(len(panel))}

    hl = {s: {"published_levelfree": best(v["published_cross_phase_trained"], "price_only"),
              "calm_trained_levelfree": best(v["calm_trained"], "price_only"),
              "published_full": best(v["published_cross_phase_trained"], "full"),
              "calm_trained_full": best(v["calm_trained"], "full")}
          for s, v in res["states"].items()}
    res["headline"] = hl
    res["seconds"] = round(time.time() - t0)
    with open(os.path.join(a.out, "calm_trained_phase4.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)

    def fmt(r):
        if r is None:
            return "n/a"
        return (f"{r['R2']:+.4f} [{r['R2_lo']:+.4f}, {r['R2_hi']:+.4f}] / sign {r['sign_acc_resolvable']:.3f} "
                f"[{r['sign_lo']:.3f}, {r['sign_hi']:.3f}] ({r['model']})")

    L = ["# E4.18 the calm-trained level-free channel, Phase 3 vs Phase 4", "",
         res["why"], "",
         f"Best model per cell; R2(x) / sign accuracy on resolvable steps, {a.n_boot}-resample cluster "
         "bootstrap over paths. CIs that overlap are not a detected change.", "",
         "| state | feature set | published (cross-phase-trained) | calm-trained |", "|---|---|---|---|"]
    for s in ("phase3", "phase4"):
        if s not in hl:
            continue
        for key, lab in (("levelfree", "level-free"), ("full", "full field set")):
            L.append(f"| {s} | {lab} | {fmt(hl[s]['published_' + key])} | {fmt(hl[s]['calm_trained_' + key])} |")
    L.append("")
    if "phase3" in hl and "phase4" in hl:
        L += ["## The brief's quantity", ""]
        for key, lab in (("levelfree", "level-free"), ("full", "full field set")):
            p3, p4 = hl["phase3"]["calm_trained_" + key], hl["phase4"]["calm_trained_" + key]
            overlap = not (p4["R2_hi"] < p3["R2_lo"] or p3["R2_hi"] < p4["R2_lo"])
            L.append(f"- calm-trained {lab} R2(x): {p3['R2']:+.4f} [{p3['R2_lo']:+.4f}, {p3['R2_hi']:+.4f}] -> "
                     f"{p4['R2']:+.4f} [{p4['R2_lo']:+.4f}, {p4['R2_hi']:+.4f}], delta {p4['R2'] - p3['R2']:+.4f}"
                     f" -- CIs {'OVERLAP: no detected change' if overlap else 'DISJOINT: a detected change'}")
    with open(os.path.join(a.out, "calm_trained_phase4.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L), flush=True)
    print(f"\nwrote {a.out}/calm_trained_phase4.json in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
