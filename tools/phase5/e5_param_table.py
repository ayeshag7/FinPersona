"""
The parameter table of PHASE_5_REPORT.md section 4, generated from envs/v2/params/observables.json so the report cannot
disagree with the deployed file (tests/test_v2_1_phase_5.py::test_phase5_report_parameter_table_matches_observables_json
reads the status from the second column of the row whose first column is the entry's key).

    python -m tools.phase5.e5_param_table [--path envs/v2/params/observables.json] [--write]

With --write the block between <!-- param-table --> and <!-- /param-table --> in the report is replaced.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORT = os.path.join(ROOT, "docs", "env_v2", "v2_1", "PHASE_5_REPORT.md")


def _num(v, nd=4):
    if isinstance(v, float):
        return f"{v:.{nd}g}" if abs(v) < 1e-3 or abs(v) >= 1e4 else f"{v:.{nd}f}".rstrip("0").rstrip(".")
    return str(v)


def _values(key, val):
    """A short rendering of the section's values (the file carries the full grids)."""
    if not isinstance(val, dict):
        return _num(val)
    skip = {"grid_A", "grid_B_log_between", "loss_size_grid", "lag_grid_td", "full_sample_fit", "bracket_phase9"}
    parts = []
    for k, v in val.items():
        if k in skip:
            if isinstance(v, dict):
                n_in = {len(x) if isinstance(x, (list, tuple)) else 1 for x in v.values()}
                parts.append(f"{k}: {len(v)} widths x {'/'.join(str(x) for x in sorted(n_in))} pts")
            elif isinstance(v, (list, tuple)):
                parts.append(f"{k}: {len(v)} pts")
            else:
                parts.append(f"{k}: {v}")
        elif isinstance(v, (list, tuple)):
            parts.append(f"{k}: [" + ", ".join(_num(x) for x in v) + "]")
        elif isinstance(v, dict):
            parts.append(f"{k}: {{" + ", ".join(f"{kk}: {_num(vv)}" for kk, vv in v.items()) + "}")
        else:
            parts.append(f"{k}: {_num(v)}")
    return "; ".join(parts)


def table(path):
    d = json.load(open(path, encoding="utf-8"))
    L = ["| entry | status | design and values in force | n | interval | label (the file's, abridged) |", "|---|---|---|---|---|---|"]
    for key, e in d.items():
        if not isinstance(e, dict) or "status" not in e:
            continue
        n = e.get("n"); iv = e.get("interval")
        n_txt = "; ".join(f"{k} {v}" for k, v in n.items()) if isinstance(n, dict) else str(n)
        iv_txt = "; ".join(f"{k} {_values(k, v) if isinstance(v, dict) else ('[' + ', '.join(_num(x) for x in v) + ']' if isinstance(v, list) else v)}"
                           for k, v in iv.items()) if isinstance(iv, dict) else str(iv)
        lab = e.get("label", "")
        lab = lab if len(lab) <= 420 else lab[:417] + "..."
        L.append(f"| `{key}` | **{e['status']}** | {_values(key, e.get('value'))} | {n_txt} | {iv_txt} | {lab} |")
    return "\n".join(L)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=os.path.join(ROOT, "envs", "v2", "params", "observables.json"))
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    md = table(a.path)
    print(md)
    if a.write:
        s = open(REPORT, encoding="utf-8").read()
        i, j = s.index("<!-- param-table -->"), s.index("<!-- /param-table -->")
        s = s[:i] + "<!-- param-table -->\n" + md + "\n" + s[j:]
        open(REPORT, "w", encoding="utf-8").write(s)
        print("\nreport block replaced")


if __name__ == "__main__":
    main()
