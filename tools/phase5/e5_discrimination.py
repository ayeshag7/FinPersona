"""
The discrimination table on the Phase-5 hand-over state, beside Phases 4, 3 and 2 (PREREG_PHASE_5.md section 10d).

    python -m tools.phase5.e5_discrimination [--n-boot 2000] [--out docs/env_v2/generated/v2_1/e5_l5]

Input: the L5 csv of the Phase-5 state, produced by
    python -m tools.phase5.e5_l5 --train 40 --eval 50 --out docs/env_v2/generated/v2_1/e5_l5/l5_phase5_after
(the oracle subclass that encodes "n/m" as the audit does; the frozen ObservablesOracle otherwise unchanged).

The summariser is tools/phase2/e2_7_discrimination.summarise, unchanged, as in E4.16.  This tool takes an explicit --out
and writes nothing into a previous phase's directory (PHASE_4_REPORT section 7's lesson).  No pass/fail: G1 is Phase 6's
gate; a collapse in any scenario is a finding for the team.

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
    ap.add_argument("--out", default=os.path.join(GEN, "e5_l5"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    res = {"what": ("the policy-spread table (16A G1's shape) on the Phase-5 hand-over, beside Phase 4's, Phase 3's and "
                    "Phase 2's, same design (40 training seeds, 50 scored seeds, three personas x four scenarios); the "
                    "Phase-5 oracle encodes a rendered 'n/m' P/E as the cap plus an indicator, as the audit does"),
           "rule": "no pass/fail -- G1 is Phase 6's gate; a collapse in any scenario is a finding for the team.",
           "phase5_changes_that_could_move_it": [
               "the multiple is FIT and wanders (design B): P/E no longer reads x through a constant k",
               "trailing EPS can be non-positive (the loss chain) and P/E renders 'n/m' on those days",
               "the analyst field is a price proxy (design C), not V e^u",
               "sentiment is a returns-only FIT process (design A) with no term in x",
               "volume has no |x| loading (design A)",
               "the announcement lags are FIT (P50 19 trading days) and dividends follow a FIT Lintner chain with a payer draw"],
           "states": {}}
    sources = [
        ("phase5_after", os.path.join(a.out, "l5_phase5_after.csv"), "Phase 5 hand-over (observables block in force)"),
        ("phase4_after", os.path.join(GEN, "e4_16", "l5_phase4_after.csv"), "Phase 4 hand-over (event block in force)"),
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

    L = ["# The discrimination table on the Phase-5 hand-over", "",
         res["what"], "", f"**Rule:** {res['rule']}", "",
         "What Phase 5 changed that could move this table:", ""]
    L += [f"- {x}" for x in res["phase5_changes_that_could_move_it"]]
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
    if "phase5_after" in res["states"] and "phase4_after" in res["states"]:
        L += ["## What moved between the Phase-4 and Phase-5 hand-overs", "",
              "| scenario | coverage P4 | coverage P5 | undefined-MCR share P4 | P5 | gap oracle->L5 P4 | P5 |",
              "|---|---|---|---|---|---|---|"]
        p4 = res["states"]["phase4_after"]["scenarios"]
        p5 = res["states"]["phase5_after"]["scenarios"]
        for sc in p5:
            if sc in p4:
                L.append(f"| {sc} | {p4[sc]['coverage_0.05']:.3f} | {p5[sc]['coverage_0.05']:.3f} | "
                         f"{p4[sc]['share_runs_with_no_resolvable_step']:.0%} | "
                         f"{p5[sc]['share_runs_with_no_resolvable_step']:.0%} | "
                         f"{p4[sc]['gap_oracle_to_L5']['mean']:.4f} | {p5[sc]['gap_oracle_to_L5']['mean']:.4f} |")
        L.append("")
    with open(os.path.join(a.out, "discrimination.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"wrote {a.out}/discrimination.json ({len(res['states'])} states)", flush=True)


if __name__ == "__main__":
    main()
