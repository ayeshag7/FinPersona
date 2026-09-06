"""
E4.17 -- the SEP level-free leakage audit on the Phase-4 hand-over state.

    python -m tools.phase4.e4_17_sep_audit [--n 200] [--T 200] [--seed0 30000] [--out DIR]

This is the audit that can actually see what Phase 4 did.  E4.16's decomposition re-run reproduces Phase 3's
numbers to four decimals -- correctly, because its arms are synthetic AR(1)/GJR processes with no event block,
so the event redesign cannot enter it (`e3_8`'s own docstring: "the events and sentiment channels remain
Phase 6's, and the full generator's number is the after-state SEP audit's").  The full generator's level-free
calm R2(x) is what moves, and it is measured here.

Phase 3's hand-over numbers, for the comparison: level-free calm R2(x) **-0.58** as published
(cross-phase-trained) and **+0.349 [0.322, 0.374]** calm-trained; full-field calm 0.213; all-phase full-field
**0.843**.  E3.8 attributed about 0.20 of the calm-trained figure to the exact process + GJR + jump stack,
leaving **about +0.15 for the events and the sentiment feedback** -- which is the quantity Phase 4's event
redesign could have moved, and the reason the brief calls narrowing it "the single most useful thing your
event redesign could hand" Phase 6.

**Why this is not `tools/phase3/after_state.py --stages audit`.**  That function caches its panel at
`_panels/sep_phase3_after.pkl` and returns it if it exists -- which it does.  Running it now would audit
PHASE 3's stored paths and write the result under Phase 3's name, reporting a stale state as the new one.
That is the same hardcoded-path trap that overwrote `e3_after_checklist.*` earlier in this phase (P4-19).
This module builds its own panel under its own name and writes to its own directory.

Model fits stay on the reference machine by the reproducibility guard -- this is never offloaded.

Output: <out>/audit_after_levelfree.{md,json} and _panels/sep_phase4_after.pkl
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
PY = sys.executable


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--T", type=int, default=200)
    ap.add_argument("--seed0", type=int, default=30000)
    ap.add_argument("--out", default=os.path.join(GEN, "e4_16"))
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(a.out, exist_ok=True)

    from envs.v2 import events_params as EP
    if not EP.PRESENT:
        raise SystemExit("events.json is absent: this audit measures the DEPLOYED state and there is none")
    print(f"[state] schedule v21 | hazard {EP.HAZARD_MAPPING} | blowoff {EP.BLOWOFF_MODE} "
          f"mult {EP.BLOWOFF_MULT} | post_top {EP.POST_TOP_MODE}/{EP.POST_TOP_HALF_LIFE} | "
          f"eps_quarter_randomised {EP.RANDOMISE_EPS_QUARTER}", flush=True)

    panel_p = os.path.join(GEN, "_panels", "sep_phase4_after.pkl")
    if os.path.exists(panel_p):
        print(f"[panel] {panel_p} exists, reusing", flush=True)
    else:
        from envs.synthetic_market import audit_panel
        os.makedirs(os.path.dirname(panel_p), exist_ok=True)
        t = time.time()
        panel = audit_panel(a.n, a.T, seed0=a.seed0)
        panel.to_pickle(panel_p)
        print(f"[panel] {panel[['scenario', 'seed']].drop_duplicates().shape[0]} paths, {len(panel)} rows, "
              f"{time.time() - t:.0f} s -> {panel_p}", flush=True)

    out_md = os.path.join(a.out, "audit_after_levelfree.md")
    cmd = [PY, "-m", "evaluation.leakage_audit", "--env", "v2", "--panel-pickle", panel_p,
           "--control", "level_free", "--no-subsample", "--out", out_md]
    print("[audit] " + " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=ROOT)
    print(f"[audit] rc={r.returncode} in {time.time() - t0:.0f} s total", flush=True)
    if r.returncode == 0:
        print(f"wrote {out_md}", flush=True)


if __name__ == "__main__":
    main()
