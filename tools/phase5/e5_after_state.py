"""
Phase-5 hand-over (the execution-order step-0 rule, paid in full), with every output under Phase-5 names -- the
Phase-3 chain hardcodes Phase-3 names and overwrote e3_after_checklist.* once (PHASE_4_REPORT section 7).

    python -m tools.phase5.e5_after_state --stages panel,audit,calm,checklist,hashes,freeze [--workers 3]

  panel      the SEP panel of the deployed Phase-5 state (`_panels/sep_phase5_after.pkl`), built with the fast renderer
             (verified bit for bit against panel_from_env on the first seed) and encoded for "n/m"
  audit      evaluation.leakage_audit.run_audit on that panel, level-free control, no subsampling, the n/m indicator
             passed as a shown field -> e5_after/audit_after_levelfree.{md,pkl,_L1.csv,_L2.csv,_L4.csv,_checklist_rows.csv}
  calm       the calm-TRAINED level-free surrogate (tools/phase3/e3_9_calm_trained.calm_trained, imported unchanged) on
             the Phase-3, Phase-4 (post-D14) and Phase-5 panels in ONE process -> e5_after/calm_trained_phase5.{json,md}
  checklist  the Section-9 checklist at 200 seeds (SCL, seeds 40000+) -> e5_after_checklist.{md,csv}
  hashes     the 95-configuration path hashes -> path_hashes_phase5_after.json (+ the comparison with the HEAD fixture)
  freeze     the manifest rewrite (a logged decision)
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import subprocess
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

from tools.phase5.common import GEN, PANELS, pin_state, encode_nm, shown_fields_of  # noqa: E402

OUT = os.path.join(GEN, "e5_after")
PY = sys.executable
SEP_SEED0, SEP_N = 30000, 200
SCL_SEED0, SCL_N = 40000, 200


def panel(workers):
    from tools.phase5.e5_panels import build
    p = os.path.join(PANELS, "sep_phase5_after.pkl")
    if os.path.exists(p):
        print("SEP panel: exists"); return p
    from envs.v2 import observables_params as OP
    assert OP.PRESENT, "observables.json is absent: this measures the DEPLOYED state and there is none"
    paths = build({"after": {"obs_overrides": {}, "config": {}}}, workers=workers, verify=True)
    os.replace(paths["after"], p)
    return p


def audit():
    from evaluation.leakage_audit import run_audit, to_markdown, checklist_rows
    from agent.render import rendered_market_fields
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(PANELS, "sep_phase5_after.pkl")
    pan = encode_nm(pd.read_pickle(p))
    shown = [f for f in rendered_market_fields("v2") if f in pan.columns] + (["reported_PE_nm"] if "reported_PE_nm" in pan else [])
    t0 = time.time()
    res = run_audit(pan, shown, max_rows=None, control="level_free")
    out = os.path.join(OUT, "audit_after_levelfree.md")
    with open(out.replace(".md", ".pkl"), "wb") as fh:
        pickle.dump(res, fh)
    res["L1"].to_csv(out.replace(".md", "_L1.csv"), index=False)
    res["L2"].to_csv(out.replace(".md", "_L2.csv"), index=False)
    res["L4"].to_csv(out.replace(".md", "_L4.csv"), index=False)
    pd.DataFrame(checklist_rows(res)).to_csv(out.replace(".md", "_checklist_rows.csv"), index=False)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(to_markdown(res, f"Section 5 leakage / phase-clock / resolvability audit (v2.1 Phase 5 hand-over, stored panel "
                                  f"sep_phase5_after.pkl, {res['n_paths']} paths, T=200; 'n/m' encoded as cap + indicator)"))
    print(res["L2_verdict"]); print(res["L2b"]); print(f"audit: {time.time() - t0:.0f} s -> {out}")


def calm(n_boot=500):
    from tools.phase3.e3_9_calm_trained import calm_trained, published_rows, best
    os.makedirs(OUT, exist_ok=True)
    states = [("phase3", os.path.join(PANELS, "sep_phase3_after.pkl"), os.path.join(GEN, "e3_after", "audit_after_levelfree.pkl")),
              ("phase4_postD14", os.path.join(PANELS, "sep_phase4_after.pkl"), os.path.join(GEN, "e4_21", "audit_after_levelfree.pkl")),
              ("phase5", os.path.join(PANELS, "sep_phase5_after.pkl"), os.path.join(OUT, "audit_after_levelfree.pkl"))]
    res = {"what": "the calm-TRAINED level-free surrogate (e3_9 estimator unchanged) on the Phase-3, post-D14 Phase-4 and Phase-5 panels in one process",
           "n_boot": n_boot, "states": {}}
    for state, pp, ap in states:
        if not (os.path.exists(pp) and os.path.exists(ap)):
            print(f"  (missing for {state})"); continue
        pub, shown = published_rows(ap)
        pan = encode_nm(pd.read_pickle(pp))
        if "reported_PE_nm" in pan and "reported_PE_nm" not in shown:
            shown = list(shown) + ["reported_PE_nm"]
        print(f"[{state}]", flush=True)
        ct = calm_trained(pan, shown, n_boot)
        res["states"][state] = {"published_cross_phase_trained": pub, "calm_trained": ct, "n_rows_panel": int(len(pan))}
    hl = {s: {"calm_trained_levelfree": best(v["calm_trained"], "price_only"), "calm_trained_full": best(v["calm_trained"], "full")}
          for s, v in res["states"].items()}
    res["headline"] = hl
    json.dump(res, open(os.path.join(OUT, "calm_trained_phase5.json"), "w", encoding="utf-8"), indent=1)
    L = ["# the calm-trained level-free channel, Phases 3 / 4 (post-D14) / 5", "",
         "| state | level-free R2(x) [CI] | full-field R2(x) [CI] |", "|---|---|---|"]
    for s, v in hl.items():
        lf, fu = v["calm_trained_levelfree"], v["calm_trained_full"]
        L.append(f"| {s} | {lf['R2']:+.4f} [{lf['R2_lo']:+.4f}, {lf['R2_hi']:+.4f}] | {fu['R2']:+.4f} [{fu['R2_lo']:+.4f}, {fu['R2_hi']:+.4f}] |")
    with open(os.path.join(OUT, "calm_trained_phase5.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


def checklist():
    from envs.synthetic_market import checklist_paths
    from evaluation.stylized_facts import run_checklist, to_markdown
    t0 = time.time()
    paths = checklist_paths(SCL_N, 200, seed0=SCL_SEED0)
    df = run_checklist(paths)
    out = os.path.join(GEN, "e5_after_checklist.md")
    pre = (f"Generator v2.1 after Phase 5; {SCL_N} seeds per scenario (crash: per delta), T = 200, seeds from {SCL_SEED0} (SCL). "
           "Items 14 and 16 come from the leakage audit; 18 and 19 are unit tests.")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(to_markdown(df, "Section 9 validation checklist, standard checklist panel (Phase 5 after)", pre))
    df.to_csv(out.replace(".md", ".csv"), index=False)
    print(df[["item", "property", "pass"]].to_string(index=False)); print(f"checklist: {time.time() - t0:.0f} s")


def hashes():
    from tools.path_hashes import build, compare
    out = os.path.join(GEN, "path_hashes_phase5_after.json")
    build(out)
    before = os.path.join(GEN, "path_hashes_phase5_before.json")
    if os.path.exists(before):
        r = compare(before, out)
        json.dump({k: (v if not isinstance(v, list) else v[:50]) for k, v in r.items()},
                  open(os.path.join(GEN, "path_hashes_phase5_compare.json"), "w", encoding="utf-8"), indent=1, default=str)
        print("NON-ANALYST CHANGES vs HEAD:", len(r["changed_non_analyst"]))


def freeze():
    subprocess.run([PY, "-m", "tools.freeze_manifest", "--write", "--label", "v2.1 Phase 5 freeze"], cwd=ROOT, check=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="panel,audit,calm,checklist,hashes,freeze")
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    pin_state()
    fns = {"panel": lambda: panel(a.workers), "audit": audit, "calm": calm, "checklist": checklist, "hashes": hashes, "freeze": freeze}
    for s in a.stages.split(","):
        t0 = time.time(); print(f"[after_state] {s} ...", flush=True)
        fns[s.strip()]()
        print(f"[after_state] {s}: {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
