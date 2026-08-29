"""
Regenerate the Markdown of every Section-9 checklist file from its CSV (v2.1 Phase 0, item 0.2, weakness item 39).

The `.md` footers of five of the six sensitivity files were written by an earlier version of
`evaluation.stylized_facts.to_markdown` and disagreed with their own tables (fw_index 7/6 for 8/7, pruna 6/7 for 7/8,
omega 6/7 for 7/8, panic3 8/5 for 9/6, panic6 7/6 for 8/7). The CSV written by the same run is the record; this tool
rewrites the table and the footer from the CSV with the current `to_markdown`, keeping the original title and preamble.
`tests/test_v2_1_phase_0.py::test_footer_counts_match_csv` locks the agreement.

Usage: python -m tools.regen_checklist_md [--check]
"""
from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from evaluation.stylized_facts import to_markdown  # noqa: E402

GEN = os.path.join(ROOT, "docs", "env_v2", "generated")
FILES = ["checklist_v2"] + [f"checklist_v2_sens_{k}" for k in ("fw_index", "pruna", "hl60", "omega_mode", "panic3", "panic6")]


def regen(name: str, check: bool = False) -> bool:
    csv = os.path.join(GEN, name + ".csv"); md = os.path.join(GEN, name + ".md")
    df = pd.read_csv(csv)
    df["pass"] = df["pass"].map(lambda v: None if pd.isna(v) else (str(v) == "True"))
    old = open(md, encoding="utf-8").read().splitlines()
    title = old[0].lstrip("# ").strip()
    preamble = old[2] if len(old) > 2 else ""
    new = to_markdown(df, title, preamble)
    same = new.strip() == "\n".join(old).strip()
    if not check and not same:
        with open(md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(new)
    return same


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true"); a = ap.parse_args()
    for f in FILES:
        same = regen(f, a.check)
        print(f"{f}: {'unchanged' if same else ('DIFFERS' if a.check else 'rewritten from CSV')}")
