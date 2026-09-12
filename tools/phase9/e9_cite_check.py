"""
P4-37's guard for Phase 9: every generated-file and code path a Phase-9 document cites must exist on disk.

    python -m tools.phase9.e9_cite_check [doc ...]

Default documents: PREREG_PHASE_9.md, PREREG_PHASE_9_ADDENDUM.md, PHASE_9_REPORT.md, PHASE_9_CHANGED_FILES.md,
IO_CONTRACT.md, and the P9-* rows of DECISION_LOG.md.  The resolution rules are Phase 8's (`tools/phase8/e8_cite_check.py`,
itself Phase 7's with private-symbol modules added), with `e9_` added to the recognised prefixes.  Exit code 1 if any
cited path is missing.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.phase7 import e7_cite_check as C7   # noqa: E402
from tools.phase8 import e8_cite_check as C8   # noqa: E402  -- imported for its `_module_forms` patch

C7.PREFIXES = tuple(sorted(set(C7.PREFIXES + ("e9_",)), key=len, reverse=True))

DEFAULT_DOCS = [os.path.join(ROOT, "docs", "env_v2", "v2_1", f) for f in
                ("PREREG_PHASE_9.md", "PREREG_PHASE_9_ADDENDUM.md", "PHASE_9_REPORT.md", "PHASE_9_CHANGED_FILES.md")] + \
               [os.path.join(ROOT, "docs", "env_v2", "spec", "IO_CONTRACT.md")]
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
        rows = [l for l in open(LOG, encoding="utf-8").read().splitlines() if l.startswith("| P9-")]
        n, miss = C7.check(LOG, "\n".join(rows))
        total += n; bad += len(miss)
        print(f"DECISION_LOG.md P9 rows: {n} cited paths, {len(miss)} missing")
        for m in miss:
            print(f"   MISSING {m}")
    print(f"checked {total} cited paths; {bad} missing")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
