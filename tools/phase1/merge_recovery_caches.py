"""
Merge the recovery-study cell caches produced by several runs (local and Kaggle kernels) into the local cache, keeping
for each cell the file with the most replications, then rebuild e1_2/recovery.{json,md} from the merged caches
(PREREG_PHASE_1_ADDENDUM.md section 6.1). Every cell's achieved replication count is stated in the table.

    python -m tools.phase1.merge_recovery_caches --from <dir> [<dir> ...] [--dry-run]
Each <dir> is searched recursively for AB_*.json / C_*.json cache files.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
CACHE = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e1_2", "cache")


def n_reps(path: str) -> int:
    try:
        return len(json.load(open(path, encoding="utf-8")))
    except Exception:
        return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="dirs", nargs="+", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    os.makedirs(CACHE, exist_ok=True)
    best: dict[str, tuple[int, str]] = {}
    for name in os.listdir(CACHE):
        if name.endswith(".json"):
            p = os.path.join(CACHE, name)
            best[name] = (n_reps(p), p)
    for d in a.dirs:
        for p in glob.glob(os.path.join(d, "**", "cache", "*.json"), recursive=True):
            name = os.path.basename(p)
            n = n_reps(p)
            if n > best.get(name, (-1, ""))[0]:
                best[name] = (n, p)
    moved = 0
    for name, (n, p) in sorted(best.items()):
        dst = os.path.join(CACHE, name)
        if os.path.abspath(p) != os.path.abspath(dst):
            print(f"  {name}: taking {n} reps from {p}")
            if not a.dry_run:
                shutil.copy2(p, dst)
            moved += 1
    print(f"{len(best)} cells; {moved} updated" + (" (dry run)" if a.dry_run else ""))
    counts = {name: n for name, (n, _) in sorted(best.items())}
    print(json.dumps(counts, indent=1))


if __name__ == "__main__":
    main()
