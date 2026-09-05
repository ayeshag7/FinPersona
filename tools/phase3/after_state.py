"""
Phase 3 hand-over (execution-order step-0 rule, paid in full): regenerate everything that describes the state
being handed over — path hashes, the Section-9 checklist (200 seeds, SCL), the SEP level-free audit (local
reference machine only), and the freeze manifest.

    python -m tools.phase3.after_state [--stages hashes,checklist,audit,freeze]
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
OUT = os.path.join(GEN, "e3_after")
PY = sys.executable
SEP_SEED0, SEP_N = 30000, 200
SCL_SEED0, SCL_N = 40000, 200


def hashes():
    from tools.path_hashes import build
    build(os.path.join(GEN, "path_hashes_phase3_after.json"))


def checklist():
    from envs.synthetic_market import checklist_paths
    from evaluation.stylized_facts import run_checklist, to_markdown
    t0 = time.time()
    paths = checklist_paths(SCL_N, 200, seed0=SCL_SEED0)
    df = run_checklist(paths)
    out = os.path.join(GEN, "e3_after_checklist.md")
    pre = (f"Generator v2.1 after Phase 3; {SCL_N} seeds per scenario (crash: per delta), T = 200, seeds from "
           f"{SCL_SEED0} (SCL, the standard checklist panel, like-for-like with `e2_after_checklist`). Items 14 "
           "and 16 come from the leakage audit; 18 and 19 are unit tests.")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(to_markdown(df, "Section 9 validation checklist, standard checklist panel (Phase 3 after)", pre))
    df.to_csv(out.replace(".md", ".csv"), index=False)
    print(df[["item", "property", "pass"]].to_string(index=False))
    print(f"checklist: {time.time() - t0:.0f} s -> {out}")


def sep_panel():
    from envs.synthetic_market import audit_panel
    p = os.path.join(GEN, "_panels", "sep_phase3_after.pkl")
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
    out = os.path.join(OUT, "audit_after_levelfree.md")
    cmd = [PY, "-m", "evaluation.leakage_audit", "--env", "v2", "--panel-pickle", p, "--control", "level_free",
           "--no-subsample", "--out", out]
    print(" ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def freeze():
    subprocess.run([PY, "-m", "tools.freeze_manifest", "--write", "--label", "v2.1 Phase 3 freeze"],
                   cwd=ROOT, check=False)


def main():
    ap = argparse.ArgumentParser()
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
