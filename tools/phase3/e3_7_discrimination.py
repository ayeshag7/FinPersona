"""
E3.7 (PREREG_PHASE_3.md section 11): E2.7's discrimination table re-run on the Phase-3 hand-over state -- the
panic multiplier and the jump block move sd(x) and coverage, so the policy spread and the MCR-undefined shares
are re-measured. No pass/fail: G1 is Phase 6's gate.

    python -m tools.l5_report --train 40 --eval 50 --out docs/env_v2/generated/v2_1/e3_7/l5_phase3_after
    python -m tools.phase3.e3_7_discrimination [--n-boot 2000]

Output: docs/env_v2/generated/v2_1/e3_7/discrimination.{json,md}
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tools.phase2.e2_7_discrimination import summarise, SCEN  # noqa: E402

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e3_7")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-boot", type=int, default=2000)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    res = {"what": "E3.7: E2.7's policy-spread table (16A G1's shape) on the Phase-3 hand-over, beside Phase 2's, "
                   "same design (40 training seeds, 50 scored seeds, three personas x four scenarios).",
           "rule": "no pass/fail -- G1 is Phase 6's gate; a collapse in any scenario is a finding for the team.",
           "states": {}}
    for key, csv, label in (("phase3_after", os.path.join(OUT, "l5_phase3_after.csv"),
                             "Phase 3 hand-over (volatility block in force)"),
                            ("phase2_after", os.path.join(GEN, "e2_7", "l5_phase2_after.csv"),
                             "Phase 2 hand-over (old GARCH shape, CAL jumps, v2 IV)")):
        if os.path.exists(csv):
            res["states"][key] = summarise(csv, label, a.n_boot)
    with open(os.path.join(OUT, "discrimination.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    L = ["# E3.7 the discrimination table on the Phase-3 hand-over (PREREG_PHASE_3.md section 11)", "",
         res["what"], "", f"**Rule:** {res['rule']}", ""]
    for key, st in res["states"].items():
        L += [f"## {st['label']}", "",
              "| scenario | coverage | runs with NO resolvable step | mandate oracle | best L5 | best trivial | gap oracle->L5 | gap L5->trivial | ordering | both gaps > 0 |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for sc, r in st["scenarios"].items():
            L.append(
                f"| {sc} | {r['coverage_0.05']:.3f} | "
                f"{r['n_cells_undefined_mcr']}/{r['n_cells']} ({r['share_runs_with_no_resolvable_step']:.0%}) | "
                f"{r['oracle']['mean']:.4f} | "
                f"{r['L5_best']['mean']:.4f} ({r['L5_best_policy'].replace('L5_', '')}) | "
                f"{r['trivial_best']['mean']:.4f} ({r['trivial_best_policy']}) | "
                f"{r['gap_oracle_to_L5']['mean']:.4f} [{r['gap_oracle_to_L5']['ci95'][0]:.4f}, "
                f"{r['gap_oracle_to_L5']['ci95'][1]:.4f}] | "
                f"{r['gap_L5_to_trivial']['mean']:.4f} [{r['gap_L5_to_trivial']['ci95'][0]:.4f}, "
                f"{r['gap_L5_to_trivial']['ci95'][1]:.4f}] | "
                f"{'yes' if r['ordering_holds'] else '**no**'} | "
                f"{'yes' if r['gaps_both_positive_at_95'] else '**no**'} |")
        L.append("")
    if len(res["states"]) == 2:
        a3, a2 = res["states"]["phase3_after"], res["states"]["phase2_after"]
        L += ["## The change, scenario by scenario (Phase 2 -> Phase 3)", "",
              "| scenario | coverage | runs with no resolvable step | gap L5->trivial |", "|---|---|---|---|"]
        for sc in SCEN:
            if sc in a2["scenarios"] and sc in a3["scenarios"]:
                L.append(f"| {sc} | {a2['scenarios'][sc]['coverage_0.05']:.3f} -> "
                         f"{a3['scenarios'][sc]['coverage_0.05']:.3f} | "
                         f"{a2['scenarios'][sc]['share_runs_with_no_resolvable_step']:.0%} -> "
                         f"{a3['scenarios'][sc]['share_runs_with_no_resolvable_step']:.0%} | "
                         f"{a2['scenarios'][sc]['gap_L5_to_trivial']['mean']:.4f} -> "
                         f"{a3['scenarios'][sc]['gap_L5_to_trivial']['mean']:.4f} |")
    with open(os.path.join(OUT, "discrimination.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L[6:]))


if __name__ == "__main__":
    main()
