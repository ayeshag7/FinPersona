"""
The arms table of PHASE_5_REPORT.md section 3.8(d), generated from the arm files so no number is transcribed by hand.

    python -m tools.phase5.e5_arms_table [--write]

Prints the markdown; with --write replaces the block between <!-- arms-table --> and <!-- /arms-table --> in the report.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from tools.phase5.e5_decide import ablation, add_one, onset, _fmt, GEN  # noqa: E402

REPORT = os.path.join(ROOT, "docs", "env_v2", "v2_1", "PHASE_5_REPORT.md")
BLOCKS = {"multiple": "VAL", "epsdiv": "VAL", "analyst": "ANALYST", "sentiment": "SENT", "volume": "VOL"}
# the arms whose decision rule (or the D10 record) needs an onset audit; the rest are ablation-only sensitivities
NEEDS_ONSET = {"analyst_A_sd0.300", "analyst_A_sd0.450", "analyst_A_sd0.564", "analyst_A_sd0.600", "analyst_C", "volume_A", "volume_B",
               "sentiment_A", "sentiment_B_full", "sentiment_B_half", "sentiment_C", "epsdiv_v21_shown", "multiple_A_P10-P90", "multiple_B_P10-P90"}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    arms = json.load(open(os.path.join(GEN, "e5_arms", "arms.json"), encoding="utf-8"))
    base = json.load(open(os.path.join(GEN, "e5_7a", "baseline", "ablation.json"), encoding="utf-8"))
    L = ["| arm | group | ΔR²_add(x) all rows [paired CI] | ΔR²_add(x) calm-trained | ΔR²_add(log V) all | onset, the arm's fields (non-price rule) | worst excess (transition; null p95) |",
         "|---|---|---|---|---|---|---|"]
    for g in ("VAL", "ANALYST", "SENT", "VOL"):
        t = base["tables"]
        L.append(f"| v2 baseline | {g} | {_fmt(t['x|all']['groups'][g]['add_one'])} | {_fmt(t['x|calm']['groups'][g]['add_one'])} | "
                 f"{_fmt(t['logV|all']['groups'][g]['add_one'])} | see 3.8(c) | |")
    for name, spec in arms.items():
        g = spec["group"]; ab = ablation(name); on = onset(name, g)
        if ab is None and on is None:
            L.append(f"| `{name}` | {g} | *running* | | | | |"); continue
        if on is None:
            otxt, wtxt = "*running*" if name in NEEDS_ONSET else "not run (no rule needs it)", ""
        else:
            otxt = "PASS" if on["group_pass_nonprice"] else "FAIL " + ", ".join(on["group_failures_nonprice"])
            w = on["worst_group_excess"]; wtxt = f"{w['excess']:+.3f} ({w['transition']}; {w['null_p95']:+.3f})" if w else ""
        L.append(f"| `{name}` | {g} | {_fmt(add_one(ab, g))} | {_fmt(add_one(ab, g, 'x', 'calm'))} | {_fmt(add_one(ab, g, 'logV', 'all'))} | {otxt} | {wtxt} |")
    md = "\n".join(L)
    print(md)
    if a.write:
        s = open(REPORT, encoding="utf-8").read()
        i, j = s.index("<!-- arms-table -->"), s.index("<!-- /arms-table -->")
        s = s[:i] + "<!-- arms-table -->\n" + md + "\n" + s[j:]
        open(REPORT, "w", encoding="utf-8").write(s)
        print("\nreport block replaced")


if __name__ == "__main__":
    main()
