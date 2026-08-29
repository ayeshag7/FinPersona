"""
v2 generator freeze (v2.1 plan, Phase 0, item 0.3): write or check the SHA-256 manifest of every file that
defines a path or an audit statistic. The manifest lives at tests/v2_freeze_manifest.json and is checked by
tests/test_v2_freeze.py; simulation/provenance.py hashes the same file set at runtime so that Env_Code_Hash
changes when any generator module changes.

Regenerating the manifest is a logged decision (the phase report records it):
    python -m tools.freeze_manifest --write --label "Phase 0 freeze"
    python -m tools.freeze_manifest --check
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from simulation.provenance import code_manifest, manifest_hash, MANIFEST_PATH, V2_FREEZE_PATTERNS  # noqa: E402


def write(label: str) -> dict:
    files = code_manifest(ROOT)
    doc = {"label": label, "written": _dt.date.today().isoformat(), "patterns": list(V2_FREEZE_PATTERNS),
           "line_endings": "CRLF normalised to LF before hashing", "manifest_hash": manifest_hash(files), "files": files}
    with open(MANIFEST_PATH, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1)
    return doc


def check() -> list:
    stored = json.load(open(MANIFEST_PATH, encoding="utf-8"))
    now = code_manifest(ROOT)
    diffs = []
    for k in sorted(set(stored["files"]) | set(now)):
        if stored["files"].get(k) != now.get(k):
            diffs.append((k, stored["files"].get(k), now.get(k)))
    return diffs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--label", default="v2.1 freeze")
    a = ap.parse_args()
    if a.write:
        d = write(a.label)
        print(f"manifest written: {len(d['files'])} files, hash {d['manifest_hash']} -> {MANIFEST_PATH}")
    if a.check or not a.write:
        diffs = check()
        for k, s, n in diffs:
            print(f"CHANGED {k}: stored {s} now {n}")
        print("manifest OK" if not diffs else f"{len(diffs)} file(s) differ from the manifest")
        sys.exit(1 if diffs else 0)
