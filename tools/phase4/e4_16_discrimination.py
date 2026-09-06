"""
E4.16 -- the discrimination table re-run on the Phase-4 hand-over state.

    python -m tools.phase4.e4_16_discrimination [--n-boot 2000] [--out DIR]

The brief's instruction, and the reason it exists: "the phase that changes the environment is the phase that
should measure what the change did".  Phase 4 changed the schedule, the hazard, the blow-off label, the
post-top leg and the calendar, and all of those move coverage and the policy spread, so E3.7's table is
re-measured here beside Phase 3's and Phase 2's.

**This tool takes an explicit `--out`.**  `tools/phase3/e3_7_discrimination.py` and
`tools/phase3/after_state.py` hardcode Phase-3 output names, which is how this phase overwrote
`e3_after_checklist.*` (PHASE_4_REPORT section 7).  Nothing here writes into a previous phase's directory.

Input: the L5 csv for the Phase-4 state, produced by
    python -m tools.l5_report --train 40 --eval 50 --out docs/env_v2/generated/v2_1/e4_16/l5_phase4_after

No pass/fail: G1 is Phase 6's gate.  A collapse in any scenario is a finding for the team.

Output: <out>/discrimination.{json,md}
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tools.phase2.e2_7_discrimination import summarise  # noqa: E402

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--out", default=os.path.join(GEN, "e4_16"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    res = {"what": "E4.16: the policy-spread table (16A G1's shape) on the Phase-4 hand-over, beside Phase 3's "
                   "and Phase 2's, same design (40 training seeds, 50 scored seeds, three personas x four "
                   "scenarios).",
           "rule": "no pass/fail -- G1 is Phase 6's gate; a collapse in any scenario is a finding for the team.",
           "phase4_changes_that_could_move_it": [
               "the schedule's ranges are FIT (det_len median 8 d against v2's 27; depth from the panel)",
               "the hazard is E4.3's mapping A (h0 6.7e-4, b 5.42) rather than v2's CAL",
               "the blow-off label reaches the driver and its multiplier is calibrated (2.0764)",
               "the post-top leg is an exponential decay (half-life 40) rather than a linear ramp",
               "the eps quarter grid is randomised per seed"],
           "states": {}}
    sources = [
        ("phase4_after", os.path.join(a.out, "l5_phase4_after.csv"), "Phase 4 hand-over (event block in force)"),
        ("phase3_after", os.path.join(GEN, "e3_7", "l5_phase3_after.csv"), "Phase 3 hand-over (volatility block)"),
        ("phase2_after", os.path.join(GEN, "e2_7", "l5_phase2_after.csv"), "Phase 2 hand-over"),
    ]
    for key, csv, label in sources:
        if os.path.exists(csv):
            res["states"][key] = summarise(csv, label, a.n_boot)
        else:
            print(f"  (missing: {csv})", flush=True)
    with open(os.path.join(a.out, "discrimination.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)

    L = ["# E4.16 the discrimination table on the Phase-4 hand-over", "",
         res["what"], "", f"**Rule:** {res['rule']}", "",
         "What Phase 4 changed that could move this table:", ""]
    L += [f"- {x}" for x in res["phase4_changes_that_could_move_it"]]
    L.append("")
    for key, st in res["states"].items():
        L += [f"## {st['label']}", "",
              "| scenario | coverage | runs with NO resolvable step | mandate oracle | best L5 | best trivial "
              "| gap oracle->L5 | gap L5->trivial | ordering | both gaps > 0 |",
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
                f"{r.get('ordering', '')} | {r.get('both_gaps_positive', '')} |")
        L.append("")
    # the comparison the team actually needs: did coverage move between hand-overs?
    if "phase4_after" in res["states"] and "phase3_after" in res["states"]:
        L += ["## What moved between the Phase-3 and Phase-4 hand-overs", "",
              "| scenario | coverage P3 | coverage P4 | undefined-MCR share P3 | P4 |", "|---|---|---|---|---|"]
        p3 = res["states"]["phase3_after"]["scenarios"]
        p4 = res["states"]["phase4_after"]["scenarios"]
        for sc in p4:
            if sc in p3:
                L.append(f"| {sc} | {p3[sc]['coverage_0.05']:.3f} | {p4[sc]['coverage_0.05']:.3f} | "
                         f"{p3[sc]['share_runs_with_no_resolvable_step']:.0%} | "
                         f"{p4[sc]['share_runs_with_no_resolvable_step']:.0%} |")
        L.append("")
    with open(os.path.join(a.out, "discrimination.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"wrote {a.out}/discrimination.json ({len(res['states'])} states)", flush=True)


if __name__ == "__main__":
    main()
