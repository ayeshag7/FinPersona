"""
Phase 2 hand-over: regenerate everything that describes the state being handed over (execution-order step-0 rule
of the plan: anything that changes the environment restarts from step 0 -- re-freeze, re-audit, new hashes).

    python -m tools.phase2.after_state [--workers 3] [--stages hashes,checklist,audit,freeze]

Stages
  hashes     `path_hashes_phase2_after.json` over the 95 manifest configurations
  checklist  the Section-9 checklist on the standard checklist panel (200 seeds, seed0 40000), as Phase 1's
             `e1_6_checklist_after` was produced, written to `e2_after_checklist.{md,csv}`
  audit      the LEVEL-FREE leakage audit on the standard evaluation panel (SEP: 1,600 paths, 320,000 rows,
             no subsampling), on the REFERENCE MACHINE -- the only environment a surrogate number may come from
             (PHASE_1_REPORT.md section 6.6)
  freeze     rewrite `tests/v2_freeze_manifest.json` with the label "v2.1 Phase 2 freeze"
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
OUT = os.path.join(GEN, "e2_6_after")
PY = sys.executable
SEP_SEED0, SEP_N = 30000, 200
SCL_SEED0, SCL_N = 40000, 200


def hashes():
    from tools.path_hashes import build
    build(os.path.join(GEN, "path_hashes_phase2_after.json"))


def checklist():
    from envs.synthetic_market import checklist_paths
    from evaluation.stylized_facts import run_checklist, to_markdown
    t0 = time.time()
    paths = checklist_paths(SCL_N, 200, seed0=SCL_SEED0)
    df = run_checklist(paths)
    os.makedirs(GEN, exist_ok=True)
    out = os.path.join(GEN, "e2_after_checklist.md")
    pre = (f"Generator v2.1 after Phase 2; {SCL_N} seeds per scenario (crash: per delta), T = 200, seeds from "
           f"{SCL_SEED0} (SCL, the standard checklist panel of PREREG_PHASE_1.md section 2, so the row is "
           "like-for-like with `e1_6_checklist_after`). Items 14 and 16 come from the leakage audit; 18 and 19 "
           "are unit tests.")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(to_markdown(df, "Section 9 validation checklist, standard checklist panel (Phase 2 after)", pre))
    df.to_csv(out.replace(".md", ".csv"), index=False)
    print(df[["item", "property", "pass"]].to_string(index=False))
    print(f"checklist: {time.time() - t0:.0f} s -> {out}")


def sep_panel():
    from envs.synthetic_market import audit_panel
    p = os.path.join(GEN, "_panels", "sep_phase2_after.pkl")
    if os.path.exists(p):
        print("SEP panel: exists")
        return p
    t0 = time.time()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    panel = audit_panel(SEP_N, 200, seed0=SEP_SEED0)
    panel.to_pickle(p)
    print(f"SEP: {panel[['scenario', 'seed']].drop_duplicates().shape[0]} paths, {len(panel)} rows, "
          f"{time.time() - t0:.0f} s")
    return p


def audit():
    p = sep_panel()
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(GEN, "e2_6_after", "audit_after_levelfree.md")
    cmd = [PY, "-m", "evaluation.leakage_audit", "--env", "v2", "--panel-pickle", p, "--control", "level_free",
           "--no-subsample", "--out", out]
    print(" ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def freeze():
    subprocess.run([PY, "-m", "tools.freeze_manifest", "--write", "--label", "v2.1 Phase 2 freeze"],
                   cwd=ROOT, check=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--stages", default="hashes,checklist,audit,freeze")
    a = ap.parse_args()
    fns = {"hashes": hashes, "checklist": checklist, "audit": audit, "freeze": freeze}
    for s in a.stages.split(","):
        t0 = time.time()
        print(f"[after_state] {s} ...", flush=True)
        fns[s]()
        print(f"[after_state] {s}: {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
