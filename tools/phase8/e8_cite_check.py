"""
P4-37's guard for Phase 8: every generated-file and code path a Phase-8 document cites must exist on disk.

    python -m tools.phase8.e8_cite_check [doc ...]

Default documents: PREREG_PHASE_8.md, PREREG_PHASE_8_ADDENDUM.md, PHASE_8_REPORT.md, PHASE_8_CHANGED_FILES.md,
IO_CONTRACT.md, PILOT_NOTES.md and the P8-* rows of DECISION_LOG.md.  The resolution rules are Phase 7's
(`tools/phase7/e7_cite_check.py`), with `e8_` and `results_v2/` added to the recognised prefixes.  Exit code 1 if any
cited path is missing.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.phase7 import e7_cite_check as C7   # noqa: E402

C7.PREFIXES = tuple(sorted(set(C7.PREFIXES + ("e8_", "results_v2/")), key=len, reverse=True))


def _module_forms(tok: str):
    """Phase 7's resolution, plus a module with a PRIVATE symbol (`evaluation/salience._design`): Phase 7's resolver
    only accepted a symbol starting with a letter, so a citation of a real private function read as missing."""
    out = []
    if "/" in tok and not tok.endswith((".py", ".json", ".md", ".csv", ".pkl", ".parquet", ".sh", ".log", "/")):
        out.append(tok + ".py")
        head, _, tail = tok.rpartition(".")
        if head and "/" in head and tail and (tail[:1].isalpha() or tail[:1] == "_"):
            out.append(head + ".py")
    return out


C7._module_forms = _module_forms
DEFAULT_DOCS = [os.path.join(ROOT, "docs", "env_v2", "v2_1", f) for f in
                ("PREREG_PHASE_8.md", "PREREG_PHASE_8_ADDENDUM.md", "PHASE_8_REPORT.md", "PHASE_8_CHANGED_FILES.md")] + \
               [os.path.join(ROOT, "docs", "env_v2", "spec", "IO_CONTRACT.md"),
                os.path.join(ROOT, "docs", "env_v2", "status", "PILOT_NOTES.md")]
LOG = os.path.join(ROOT, "docs", "env_v2", "decisions", "DECISION_LOG.md")


def main(argv=None):
    args = argv if argv is not None else sys.argv[1:]
    docs = [os.path.abspath(a) for a in args] or [d for d in DEFAULT_DOCS if os.path.exists(d)]
    total, bad = 0, 0
    for d in docs:
        with open(d, "r", encoding="utf-8") as fh:
            n, miss = C7.check(d, fh.read())
        total += n; bad += len(miss)
        print(f"{os.path.relpath(d, ROOT)}: {n} cited paths, {len(miss)} missing")
        for m in miss:
            print(f"   MISSING {m}")
    if os.path.exists(LOG) and not args:
        rows = [l for l in open(LOG, encoding="utf-8").read().splitlines() if l.startswith("| P8-")]
        n, miss = C7.check(LOG, "\n".join(rows))
        total += n; bad += len(miss)
        print(f"DECISION_LOG.md P8 rows: {n} cited paths, {len(miss)} missing")
        for m in miss:
            print(f"   MISSING {m}")
    print(f"checked {total} cited paths; {bad} missing")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
