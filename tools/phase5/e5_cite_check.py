"""
P4-37's guard: every generated-file path a Phase-5 document cites must exist on disk, and every changed file the
changed-files list names must exist.

    python -m tools.phase5.e5_cite_check

Scans PHASE_5_REPORT.md, PHASE_5_CHANGED_FILES.md, PREREG_PHASE_5.md and the P5-* rows of DECISION_LOG.md for
backticked paths (`e5_*/...`, `_panels/...`, `path_hashes_*`, `tools/...`, `envs/...`, `tests/...`, `docs/...`) and
reports the ones that do not resolve.  Exit code 1 if any is missing.
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
DOCS = [os.path.join(ROOT, "docs", "env_v2", "v2_1", f) for f in ("PHASE_5_REPORT.md", "PHASE_5_CHANGED_FILES.md", "PREREG_PHASE_5.md")]
LOG = os.path.join(ROOT, "docs", "env_v2", "decisions", "DECISION_LOG.md")
PAT = re.compile(r"`([A-Za-z0-9_./\-]+(?:\{[A-Za-z0-9_,.]+\})?[A-Za-z0-9_./\-]*)`")


def expand(tok: str):
    m = re.search(r"\{([^}]*)\}", tok)
    if not m:
        return [tok]
    return [tok[:m.start()] + alt + tok[m.end():] for alt in m.group(1).split(",")]


def resolve(tok: str):
    if tok.startswith("params/"):  # the documents' short form of envs/v2/params/<file> (the Phase-4 convention)
        tok = "envs/v2/" + tok
    cands = [os.path.join(ROOT, tok), os.path.join(GEN, tok), os.path.join(ROOT, "docs", "env_v2", tok),
             os.path.join(ROOT, "docs", "env_v2", "v2_1", tok)]
    return any(os.path.exists(c) for c in cands)


def main():
    texts = []
    for p in DOCS:
        if os.path.exists(p):
            texts.append((os.path.basename(p), open(p, encoding="utf-8").read()))
    if os.path.exists(LOG):
        log = open(LOG, encoding="utf-8").read()
        i = log.find("## Phase 5")
        if i >= 0:
            texts.append(("DECISION_LOG.md (P5-*)", log[i:]))
    missing = {}
    n_checked = 0
    for name, text in texts:
        for tok in PAT.findall(text):
            if "/" not in tok or tok.endswith("/") or tok.startswith("http"):
                continue
            if any(tok.endswith(s) for s in (".py", ".json", ".md", ".csv", ".pkl", ".npz", ".log", ".txt", ".xls")) or "e5_" in tok or "path_hashes" in tok or "_panels" in tok:
                for t in expand(tok):
                    t = t.rstrip(".,;:")
                    n_checked += 1
                    if not resolve(t):
                        missing.setdefault(name, set()).add(t)
    print(f"checked {n_checked} cited paths across {len(texts)} documents")
    for name, ms in missing.items():
        print(f"MISSING in {name}:")
        for t in sorted(ms):
            print("   ", t)
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
