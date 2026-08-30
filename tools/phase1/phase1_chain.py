"""
Resumable runner for the Phase-1 chain after the E1.4 generator variants and the E1.2 recovery study exist
(PREREG_PHASE_1.md; execution-order rule: the handed-over state is what gets audited). Every stage is skipped when its
output already exists, so the chain can be relaunched after a crash or moved to another machine.

    python -m tools.phase1.phase1_chain [--workers 3] [--from STAGE] [--only STAGE,...] [--list]
Stages (in order): apply_e1_2, confirm_e1_4, apply_e1_4, e1_5, apply_e1_5, s11_fixed, s11_A, s11_B, s11_C, e1_1, e1_3,
sep_after, audit_after_levelfree, audit_after_level, l5_after, checklist_after, s15_after, hashes_after,
audit_before_levelfree, audit_before_level, l5_before, tests. Serial by design: one heavy job at a time keeps memory bounded.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
PY = sys.executable
LOG = os.path.join(GEN, "_panels", "chain.log")


def g(*p):
    return os.path.join(GEN, *p)


from tools.phase1.before_state import FROZEN_CFG  # noqa: E402


def chosen_variant():
    from tools.phase1.apply_e1_4 import select
    return select(json.load(open(g("e1_4", "generator_split.json"), encoding="utf-8")))["chosen"]


def stages(w):
    W = str(w)
    return [
        ("apply_e1_2", lambda: [PY, "-m", "tools.phase1.apply_e1_2"], lambda: os.path.exists(g("e1_2", "decision.json"))),
        ("confirm_e1_4", lambda: [PY, "-m", "tools.phase1.e1_4_confirm", "--variant", chosen_variant(), "--workers", W],
         lambda: os.path.exists(g("e1_4", f"confirm_{chosen_variant()}.json"))),
        ("apply_e1_4", lambda: [PY, "-m", "tools.phase1.apply_e1_4"],
         lambda: "decision" in json.load(open(os.path.join(ROOT, "envs", "v2", "params", "value.json"), encoding="utf-8"))["jump"]),
        ("e1_5", lambda: [PY, "-m", "tools.phase1.e1_5_burn_in", "--write-states", "--n", "2000", "--workers", W], lambda: os.path.exists(g("e1_5", "burn_in.json"))),
        ("apply_e1_5", lambda: [PY, "-m", "tools.phase1.apply_e1_5"],
         lambda: json.load(open(os.path.join(ROOT, "envs", "v2", "params", "value.json"), encoding="utf-8"))["burn_in"].get("source") == "e1_5/burn_in.json"),
    ] + [
        (f"s11_{m}", (lambda m=m, mode=mode: [PY, "-m", "tools.phase1.before_state", "s11", "--tag", m, "--workers", W, "--config", json.dumps({"start_price_mode": mode})]),
         (lambda m=m: os.path.exists(g("_panels", f"s11_{m}_panel.pkl"))))
        for m, mode in (("fixed", "fixed"), ("A", "randomise"), ("B", "normalise"), ("C", "both"))
    ] + [
        ("e1_1", lambda: [PY, "-m", "tools.phase1.e1_1_start_price"], lambda: os.path.exists(g("e1_1", "start_price.json"))),
        ("e1_3", lambda: [PY, "-m", "tools.phase1.e1_3_sweep", "--workers", W], lambda: os.path.exists(g("e1_3", "sweep.json"))),
        ("sep_after", lambda: [PY, "-m", "tools.phase1.before_state", "sep", "--tag", "after"], lambda: os.path.exists(g("_panels", "sep_after.pkl"))),
        ("audit_after_levelfree", lambda: [PY, "-m", "evaluation.leakage_audit", "--env", "v2", "--panel-pickle", g("_panels", "sep_after.pkl"), "--control", "level_free",
                                           "--no-subsample", "--out", g("e1_6", "audit_after_levelfree.md")], lambda: os.path.exists(g("e1_6", "audit_after_levelfree.md"))),
        ("audit_after_level", lambda: [PY, "-m", "evaluation.leakage_audit", "--env", "v2", "--panel-pickle", g("_panels", "sep_after.pkl"), "--control", "level",
                                       "--no-subsample", "--out", g("e1_6", "audit_after_level.md")], lambda: os.path.exists(g("e1_6", "audit_after_level.md"))),
        ("l5_after", lambda: [PY, os.path.join(ROOT, "tools", "l5_report.py"), "--train", "40", "--eval", "50", "--T", "200", "--feature-sets", "full,price_only,level_free",
                              "--out", g("e1_6", "l5_after")], lambda: os.path.exists(g("e1_6", "l5_after.csv"))),
        ("checklist_after", lambda: [PY, "-m", "tools.phase1.before_state", "checklist", "--tag", "after"], lambda: os.path.exists(g("e1_6_checklist_after.md"))),
        ("s15_after", lambda: [PY, "-m", "tools.phase1.before_state", "s15", "--tag", "after", "--workers", W], lambda: os.path.exists(g("e1_5", "day1_states_after.npz"))),
        ("hashes_after", lambda: [PY, "-m", "tools.phase1.before_state", "hashes", "--tag", "after"], lambda: os.path.exists(g("path_hashes_phase1_after.json"))),
        ("audit_before_levelfree", lambda: [PY, "-m", "evaluation.leakage_audit", "--env", "v2", "--panel-pickle", g("_panels", "sep_before.pkl"), "--control", "level_free",
                                            "--no-subsample", "--out", g("e1_6", "audit_before_levelfree.md")], lambda: os.path.exists(g("e1_6", "audit_before_levelfree.md"))),
        ("audit_before_level", lambda: [PY, "-m", "evaluation.leakage_audit", "--env", "v2", "--panel-pickle", g("_panels", "sep_before.pkl"), "--control", "level",
                                        "--no-subsample", "--out", g("e1_6", "audit_before_level.md")], lambda: os.path.exists(g("e1_6", "audit_before_level.md"))),
        ("l5_before", lambda: [PY, os.path.join(ROOT, "tools", "l5_report.py"), "--train", "40", "--eval", "50", "--T", "200", "--feature-sets", "full,price_only,level_free",
                               "--out", g("e1_6", "l5_before"), "--config", json.dumps(FROZEN_CFG)], lambda: os.path.exists(g("e1_6", "l5_before.csv"))),
        ("numbers", lambda: [PY, "-m", "tools.phase1.phase1_numbers"], lambda: False),
        ("tests", lambda: [PY, "-m", "pytest", "-q", "-x", "tests"], lambda: False),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--from", dest="from_", default=None)
    ap.add_argument("--only", default=None)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    sys.path.insert(0, ROOT)
    st = stages(a.workers)
    names = [s[0] for s in st]
    if a.list:
        for n, _, done in st:
            try:
                print(n, "DONE" if done() else "pending")
            except Exception as e:  # noqa: BLE001
                print(n, f"pending ({type(e).__name__})")
        return
    sel = names[names.index(a.from_):] if a.from_ else names
    if a.only:
        sel = [n for n in a.only.split(",") if n in names]
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    for n, cmd, done in st:
        if n not in sel:
            continue
        try:
            if done():
                print(f"[chain] {n}: exists, skipped", flush=True); continue
        except Exception:
            pass
        t0 = time.time()
        c = cmd()
        print(f"[chain] {n}: {' '.join(c)}", flush=True)
        with open(LOG, "a", encoding="utf-8") as lf:
            lf.write(f"{time.strftime('%H:%M:%S')} start {n}\n")
        r = subprocess.run(c, cwd=ROOT, env=env)
        with open(LOG, "a", encoding="utf-8") as lf:
            lf.write(f"{time.strftime('%H:%M:%S')} end {n} rc={r.returncode} {time.time() - t0:.0f} s\n")
        print(f"[chain] {n}: rc={r.returncode} {time.time() - t0:.0f} s", flush=True)
        if r.returncode != 0:
            print(f"[chain] STOP at {n}", flush=True); sys.exit(r.returncode)
    print("[chain] all stages done", flush=True)


if __name__ == "__main__":
    main()
