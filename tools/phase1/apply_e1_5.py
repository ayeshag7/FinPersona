"""
Apply the E1.5 burn-in decision (REG-17; PREREG_PHASE_1.md section 6) to envs/v2/params/value.json: per-engine burn-in
days and the mode. GenConfig carries one burn_in_mode, so when engines split between A (long burn-in) and B (stored
state) the mode of the default engine is written and the per-engine days follow each engine's own decision; the label
states the split. Nothing else in value.json changes.

    python -m tools.phase1.apply_e1_5 [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e1_5")
PARAMS = os.path.join(ROOT, "envs", "v2", "params", "value.json")
DEFAULT_ENGINE = "fw_fallback_hl150"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args()
    b = json.load(open(os.path.join(GEN, "burn_in.json"), encoding="utf-8"))
    dec = b["decision"]
    n_paths = b["design"].get("n_paths", 500)
    days = {eng: int(d["burn_in_days"]) for eng, d in dec.items()}
    modes = {eng: ("stored" if d["adopted"] == "B" else "long") for eng, d in dec.items()}
    mode = modes[DEFAULT_ENGINE]
    days["default"] = days[DEFAULT_ENGINE]
    label = (f"FIT/DESIGN E1.5 (29 Aug 2026; REG-17 rule: every variable's KS upper limit < 0.10 against the day-5000 reference of {n_paths} flat paths; PREREG_PHASE_1_ADDENDUM.md section 4): "
             + "; ".join(f"{e}: {d['adopted']} ({days[e]} d; {d['reason']}; current 260 d {'passes' if d['current_passes'] else 'FAILS'})" for e, d in dec.items())
             + f". GenConfig.burn_in_mode = '{mode}' (the default engine's choice); engines adopting the other option keep their own days here and the report states the split"
             if len(set(modes.values())) > 1 else
             f"FIT/DESIGN E1.5 (29 Aug 2026; REG-17 rule: every variable's KS upper limit < 0.10 against the day-5000 reference of {n_paths} flat paths; PREREG_PHASE_1_ADDENDUM.md section 4): "
             + "; ".join(f"{e}: {d['adopted']} ({days[e]} d; {d['reason']}; current 260 d {'passes' if d['current_passes'] else 'FAILS'})" for e, d in dec.items()))
    print(json.dumps({"mode": mode, "days": days, "modes": modes}, indent=1)); print(label)
    if a.dry_run:
        return
    p = json.load(open(PARAMS, encoding="utf-8"))
    p["burn_in"]["value"] = {"mode": mode, "days": days, "stored_days": 60, "modes_by_engine": modes}
    p["burn_in"]["label"] = label
    p["burn_in"]["source"] = "e1_5/burn_in.json"
    with open(PARAMS, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(p, fh, indent=1)
    print("value.json updated: burn_in")


if __name__ == "__main__":
    main()
