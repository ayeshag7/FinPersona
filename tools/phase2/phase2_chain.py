"""
Resumable runner for the Phase-2 chain (PREREG_PHASE_2.md section 11).  Every stage is skipped when its output
already exists, so the chain survives a crash or a move to another machine.  Serial by design: one heavy job at a
time keeps memory bounded (Phase 1 hung the laptop twice by running two big jobs at once).

    python -m tools.phase2.phase2_chain [--list] [--from STAGE] [--only STAGE,...] [--workers 3]

Stages, in order:
    e2_1                 FW reproduction and the units convention (fixes price_scale for everything after it)
    e2_3_data            panel moments + block-bootstrap weight matrices (LOCAL ONLY: needs datasets/)
    power                PA1-PA5 decidability simulations
    smm_<engine>_<per>   the SMM fits (full and train decide; p1/p2/p3 are descriptive)
    refits_<engine>      bootstrap refits for the full-sample parameter intervals
    e2_4_ab              acceptance + held-out prediction -> the engine decision
    e2_2                 the persistence assembly and REG-5's rule
    e2_5                 the half-life estimator lookup table
    apply_e2             write params/mispricing.json (+ value.json's fitted sigma_V) and plumb the engine
    e2_6_<stage>         the persistence sweep (calibration, switches, checklist, level-free audits)
    e2_4_c               the checklist / level-free equivalence of the incumbent and the adopted engine
    after_state          checklist, level-free audits, path hashes and the freeze on the handed-over state
    tests                pytest
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
LOG = os.path.join(GEN, "e2_0", "chain.log")
ENGINES = ("ar1", "fw_v2", "fw_plus")
DECIDING = ("full", "train")
SUBS = ("p1", "p2", "p3")


def g(*p):
    return os.path.join(GEN, *p)


def smm_done(engine, period):
    return os.path.exists(g("e2_3", f"smm_{engine}_{period}.json"))


def refits_done(engine):
    p = g("e2_3", f"smm_{engine}_full.json")
    return os.path.exists(p) and "bootstrap_refits" in json.load(open(p, encoding="utf-8"))


def adopted_engine():
    p = g("e2_4", "decision.json")
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8")).get("decision", {}).get("adopted")


def stages(w):
    W = str(w)
    st = [
        ("e2_1", lambda: [PY, "-m", "tools.phase2.e2_1_fw_repro", "--n-runs", "200"],
         lambda: os.path.exists(g("e2_1", "fw_repro.json"))),
        ("e2_3_data", lambda: [PY, "-m", "tools.phase2.e2_3_data", "--n-boot", "500"],
         lambda: all(os.path.exists(g("e2_3", f"weight_{p}.npy")) for p in ("full", "p1", "p2", "p3", "train", "test"))),
        ("power", lambda: [PY, "-m", "tools.phase2.prereg_power"],
         lambda: os.path.exists(g("e2_0", "power.json"))
         and all(k in json.load(open(g("e2_0", "power.json"), encoding="utf-8")) for k in ("PA1", "PA2", "PA4", "PA5"))),
    ]
    for per in DECIDING + SUBS:
        for eng in ENGINES:
            # ADDENDUM section 2: train needs theta-hat only (no MC p); sub-periods are descriptive
            mi = "40" if per in DECIDING else "15"
            mc = "200" if per == "full" else ("0" if per == "train" else "50")
            st.append((f"smm_{eng}_{per}",
                       (lambda eng=eng, per=per, mi=mi, mc=mc: [PY, "-m", "tools.phase2.e2_3_smm", "--engine", eng,
                                                                "--period", per, "--n-paths", "200",
                                                                "--maxiter", mi, "--n-mc", mc]),
                       (lambda eng=eng, per=per: smm_done(eng, per))))
    for eng in ENGINES:
        st.append((f"refits_{eng}",
                   (lambda eng=eng: [PY, "-m", "tools.phase2.e2_3_smm", "--engine", eng, "--period", "full",
                                     "--refits-only", "--n-refits", "30"]),
                   (lambda eng=eng: refits_done(eng))))
    st += [
        ("e2_4_ab", lambda: [PY, "-m", "tools.phase2.e2_4_engine", "--stage", "ab"],
         lambda: os.path.exists(g("e2_4", "decision.json"))
         and "decision" in json.load(open(g("e2_4", "decision.json"), encoding="utf-8"))),
        ("e2_2", lambda: [PY, "-m", "tools.phase2.e2_2_persistence"],
         lambda: os.path.exists(g("e2_2", "persistence.json"))),
        ("e2_5", lambda: [PY, "-m", "tools.phase2.e2_5_hl_table", "--n-seeds", "200"],
         lambda: os.path.exists(g("e2_5", "hl_table.json"))),
        ("apply_e2", lambda: [PY, "-m", "tools.phase2.apply_e2"],
         lambda: os.path.exists(os.path.join(ROOT, "envs", "v2", "params", "mispricing.json"))),
        ("e2_6_calib", lambda: [PY, "-m", "tools.phase2.e2_6_sweep", "--stages", "calib", "--workers", W],
         lambda: os.path.exists(g("e2_6", "sweep.json"))
         and "calibration" in json.load(open(g("e2_6", "sweep.json"), encoding="utf-8"))),
        ("e2_6_switch", lambda: [PY, "-m", "tools.phase2.e2_6_sweep", "--stages", "switch", "--workers", W], lambda: False),
        ("e2_6_checklist", lambda: [PY, "-m", "tools.phase2.e2_6_sweep", "--stages", "checklist", "--workers", W], lambda: False),
        ("e2_6_audit", lambda: [PY, "-m", "tools.phase2.e2_6_sweep", "--stages", "audit", "--workers", W], lambda: False),
        ("e2_4_c", lambda: [PY, "-m", "tools.phase2.e2_4_engine", "--stage", "c"], lambda: False),
        ("after_state", lambda: [PY, "-m", "tools.phase2.after_state", "--workers", W], lambda: False),
        ("tests", lambda: [PY, "-m", "pytest", "-q", "tests"], lambda: False),
    ]
    return st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--from", dest="from_", default=None)
    ap.add_argument("--only", default=None)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    st = stages(a.workers)
    names = [s[0] for s in st]
    if a.list:
        for n, _, done in st:
            try:
                print(f"{n:24s} {'DONE' if done() else 'pending'}")
            except Exception as e:  # noqa: BLE001
                print(f"{n:24s} pending ({type(e).__name__})")
        return
    sel = names[names.index(a.from_):] if a.from_ else names
    if a.only:
        sel = [n for n in a.only.split(",") if n in names]
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    env = dict(os.environ, PYTHONUNBUFFERED="1", OMP_NUM_THREADS="2")
    for n, cmd, done in st:
        if n not in sel:
            continue
        try:
            if done():
                print(f"[chain] {n}: exists, skipped", flush=True)
                continue
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
            print(f"[chain] STOP at {n}", flush=True)
            sys.exit(r.returncode)
    print("[chain] all stages done", flush=True)


if __name__ == "__main__":
    main()
