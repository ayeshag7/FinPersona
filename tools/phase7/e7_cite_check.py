"""
P4-37's guard for Phase 7: every generated-file path a Phase-6 document cites must exist on disk.

    python -m tools.phase7.e7_cite_check [doc ...]

Default documents: PREREG_PHASE_7.md, PREREG_PHASE_7_ADDENDUM.md, PHASE_7_REPORT.md, PHASE_7_CHANGED_FILES.md and the
P7-* rows of DECISION_LOG.md.  Backticked tokens that look like paths (`e7_*/...`, `e5_*/...`, `e3_*/...`, `_panels/...`,
`path_hashes_*`, `tools/...`, `envs/...`, `tests/...`, `evaluation/...`, `docs/...`, `spec/...`) are resolved against the
repository root and against `docs/env_v2/generated/v2_1/` and `docs/env_v2/`; `{a,b}` brace sets are expanded.  A token
that is a pattern (contains `*`) is checked with glob.  Exit code 1 if any cited path is missing.
"""
from __future__ import annotations

import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
ENV = os.path.join(ROOT, "docs", "env_v2")
DEFAULT_DOCS = [os.path.join(ROOT, "docs", "env_v2", "v2_1", f) for f in
                ("PREREG_PHASE_7.md", "PREREG_PHASE_7_ADDENDUM.md", "PHASE_7_REPORT.md",
                 "PHASE_7_CHANGED_FILES.md")] +                [os.path.join(ROOT, "docs", "env_v2", "spec", "IO_CONTRACT.md"),
                os.path.join(ROOT, "docs", "env_v2", "status", "PILOT_NOTES.md")]
LOG = os.path.join(ROOT, "docs", "env_v2", "decisions", "DECISION_LOG.md")
PAT = re.compile(r"`([A-Za-z0-9_./\-\*]+(?:\{[A-Za-z0-9_,.\-]+\})?[A-Za-z0-9_./\-\*]*)`")
PREFIXES = ("e7_", "e6_", "e5_", "e4_", "e3_", "e2_", "e1_", "_panels/", "path_hashes_", "tools/", "envs/", "tests/", "evaluation/", "simulation/", "agent/", "docs/", "spec/", "v2_1/", "results_v2_pilot/")


def expand(tok: str):
    m = re.search(r"\{([^}]*)\}", tok)
    if not m:
        return [tok]
    return [tok[:m.start()] + alt + tok[m.end():] for alt in m.group(1).split(",")]


def _module_forms(tok: str):
    """v2.1 Phase 7: a citation is often a module plus a symbol -- `evaluation/targets.BANDS`,
    `tools/report_v2.cell_baselines` -- or a module without its extension. Both name a real file; the checker
    resolves them so that the documents can cite a symbol without the check reporting a missing path."""
    out = []
    if "/" in tok and not tok.endswith((".py", ".json", ".md", ".csv", ".pkl", ".parquet", ".sh", ".log", "/")):
        out.append(tok + ".py")
        head, _, tail = tok.rpartition(".")
        if head and "/" in head and tail and tail[:1].isalpha():
            out.append(head + ".py")
    return out


def resolves(tok: str) -> bool:
    cands = [os.path.join(ROOT, tok), os.path.join(GEN, tok), os.path.join(ENV, tok)]
    cands += [os.path.join(ROOT, f) for f in _module_forms(tok)]
    for c in cands:
        if "*" in c:
            if glob.glob(c):
                return True
        elif os.path.exists(c):
            return True
    return False


def check(path: str, text: str):
    missing, n = [], 0
    for tok in PAT.findall(text):
        if not tok.startswith(PREFIXES) or tok.endswith((".py::", "::")) or "::" in tok:
            continue
        if tok.endswith("/") and not tok.startswith(("e", "_", "tools", "docs", "spec", "tests", "evaluation", "envs", "simulation", "agent", "results")):
            continue
        for t in expand(tok):
            n += 1
            if not resolves(t.rstrip("/")):
                missing.append(t)
    return n, sorted(set(missing))


def main(argv=None):
    docs = [os.path.abspath(a) for a in (argv or sys.argv[1:])] or [d for d in DEFAULT_DOCS if os.path.exists(d)]
    total, bad = 0, 0
    for d in docs:
        with open(d, "r", encoding="utf-8") as fh:
            n, miss = check(d, fh.read())
        total += n; bad += len(miss)
        print(f"{os.path.relpath(d, ROOT)}: {n} cited paths, {len(miss)} missing")
        for m in miss:
            print(f"   MISSING {m}")
    if os.path.exists(LOG) and not (argv or sys.argv[1:]):
        rows = [l for l in open(LOG, encoding="utf-8").read().splitlines() if l.startswith("| P7-")]
        n, miss = check(LOG, "\n".join(rows))
        total += n; bad += len(miss)
        print(f"DECISION_LOG.md P7 rows: {n} cited paths, {len(miss)} missing")
        for m in miss:
            print(f"   MISSING {m}")
    print(f"checked {total} cited paths; {bad} missing")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
