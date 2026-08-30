"""
Apply the E1.4 decision to envs/v2/params/value.json (stage 2 of the Phase-1 parameter file; PREREG_PHASE_1.md section
5.3 and PREREG_PHASE_1_ADDENDUM.md section 2): the KS rule selects the placement exactly as pre-registered; the E[x] rule is
reported under the pre-registered form (old), the plan's two-condition reading (new-a) and, once the confirmatory run
exists, the powered TOST (new-b). The file's label states every outcome. Nothing else in value.json changes.

    python -m tools.phase1.apply_e1_4 [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e1_4")
PARAMS = os.path.join(ROOT, "envs", "v2", "params", "value.json")
PLACEMENT = {"current_x_negmean": "x_negmean", "B_x_zero": "x_zero", "A_V_announce": "V_announce", "C_both": "both"}


def select(split: dict) -> dict:
    v = split["variants"]
    passers = [k for k in v if k != "current_x_negmean" and v[k]["ks_pass"]]
    if passers:
        chosen = min(passers, key=lambda k: v[k]["ks_window"])
        why = "KS rule: both bootstrap upper limits < 0.10" + (", smallest window-day distance among passers" if len(passers) > 1 else "")
    else:
        chosen = "C_both"; why = "no variant meets the KS rule; C (the most flexible) carried forward with the shortfall stated (REG-3)"
    r = v[chosen]
    se = (r["E_x_ci95"][1] - r["E_x_ci95"][0]) / (2 * 1.96)
    ex = {"E_x": r["E_x"], "ci95_200": r["E_x_ci95"], "old_tost_200": r["E_x_pass"],
          "new_a_two_condition_200": bool(abs(r["E_x"]) <= 1.96 * se and abs(r["E_x"]) <= 0.02)}
    conf = os.path.join(GEN, f"confirm_{chosen}.json")
    if os.path.exists(conf):
        c = json.load(open(conf, encoding="utf-8"))["full"]
        ex.update({"n_confirm": c["n"], "E_x_confirm": c["E_x"], "ci95_confirm": c["ci95"], "new_b_tost_confirm": c["pass_tost"]})
    return {"chosen": chosen, "placement": PLACEMENT[chosen], "why": why, "passers": passers, "E_x": ex}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args()
    split = json.load(open(os.path.join(GEN, "generator_split.json"), encoding="utf-8"))
    d = select(split)
    ex = d["E_x"]
    status = ("confirmed (new-b)" if ex.get("new_b_tost_confirm") else "provisional (new-a passed; new-b " +
              ("failed -> team decision" if "new_b_tost_confirm" in ex else "pending") + ")") if ex["new_a_two_condition_200"] else "FAILS new-a -> team decision"
    label = (f"FIT/DESIGN E1.4 (29 Aug 2026): placement '{d['placement']}' by the pre-registered KS rule ({d['why']}); "
             f"E[x] on 200 flat paths {ex['E_x']:+.4f} [{ex['ci95_200'][0]:+.4f}, {ex['ci95_200'][1]:+.4f}]: pre-registered TOST "
             f"{'pass' if ex['old_tost_200'] else 'FAIL (undecidable at 200 seeds, PREREG_PHASE_1_ADDENDUM.md)'}; two-condition reading "
             f"{'pass' if ex['new_a_two_condition_200'] else 'FAIL'}"
             + (f"; 1,000-seed TOST {ex['E_x_confirm']:+.4f} [{ex['ci95_confirm'][0]:+.4f}, {ex['ci95_confirm'][1]:+.4f}] "
                f"{'pass' if ex['new_b_tost_confirm'] else 'FAIL'}" if "new_b_tost_confirm" in ex else "")
             + f" -> {status}. Total rate 0.010/day and size sd 0.03 CAL (v2 E1 calibration; Phase 3 re-fits); p_ann and lam_res FIT from the "
               f"panel's window share of jump days q (e1_4/panel_split.json)")
    print(json.dumps(d, indent=1)); print(label)
    if a.dry_run:
        return
    p = json.load(open(PARAMS, encoding="utf-8"))
    p["jump"]["value"]["placement"] = d["placement"]
    p["jump"]["label"] = label
    p["jump"]["source"] = "e1_4/generator_split.json (variants, KS rule), e1_4/confirm_*.json (E[x] at 1,000 seeds), e1_4/panel_split.json (q)"
    p["jump"]["decision"] = d
    with open(PARAMS, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(p, fh, indent=1)
    print("value.json updated: jump.placement =", d["placement"])


if __name__ == "__main__":
    main()
