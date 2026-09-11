"""
v2.1 Phase 8 -- PHASE_8_CHANGED_FILES.md generated from git and verified against disk (the Phase-7 pattern).

    python -m tools.phase8.e8_changed_files [--base 22d572d] [--check]

**Phase 7 is not committed** (its files are modified or untracked in the working tree, like Phase 8's), so git cannot
separate the two phases: the diff from the Phase-6 close-out commit contains both.  Every path is therefore marked
with whether it also appears in `PHASE_7_CHANGED_FILES.md`; a path in both lists was changed by Phase 7 and may have
been changed again by Phase 8 (the report's section 6 names the ones that were).  The list excludes itself (rule 17)
and the simulation caches.  `--check` exits 1 when the document on disk differs from what git and the tree give now.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.phase7 import e7_changed_files as C7   # noqa: E402

DOC = os.path.join(ROOT, "docs", "env_v2", "v2_1", "PHASE_8_CHANGED_FILES.md")
P7_DOC = os.path.join(ROOT, "docs", "env_v2", "v2_1", "PHASE_7_CHANGED_FILES.md")
BASE_DEFAULT = "22d572d"
IGNORE = ("docs/env_v2/generated/v2_1/e6_1/cache/", "COMMIT", "docs/env_v2/generated/v2_1/e7_1/_scratch/",
          "docs/env_v2/generated/v2_1/e8_3/_cache/", "docs/env_v2/v2_1/PHASE_8_CHANGED_FILES.md")


def phase7_paths() -> set:
    if not os.path.exists(P7_DOC):
        return set()
    return set(re.findall(r"^\| `([^`]+)` \|", open(P7_DOC, encoding="utf-8").read(), flags=re.M))


def render(base: str) -> str:
    C7.IGNORE = IGNORE
    rows = C7.rows(base)
    p7 = phase7_paths()
    head = C7._git("rev-parse", "--short", "HEAD").strip()
    groups = {"agent/": [], "experiments/": [], "evaluation/": [], "simulation/": [], "tools/": [], "tests/": [],
              "docs/env_v2/v2_1/": [], "docs/env_v2/spec/": [], "docs/env_v2/status/": [], "docs/env_v2/decisions/": [],
              "docs/env_v2/generated/": [], "other": []}
    for x in rows:
        for g in groups:
            if g != "other" and x["path"].startswith(g):
                groups[g].append(x); break
        else:
            groups["other"].append(x)
    n8 = sum(1 for x in rows if x["path"] not in p7)
    L = [f"# Phase 8 — files written or changed (generated from git `{base}..{head}` and the working tree by "
         f"`tools/phase8/e8_changed_files.py`; verified against disk by `--check`)", "",
         f"{len(rows)} paths in the working tree against `{base}`; **{n8} not in Phase 7's list** (Phase 8's own), "
         f"{len(rows) - n8} also in `PHASE_7_CHANGED_FILES.md` (Phase 7 is uncommitted, so git cannot separate the two); "
         f"{sum(1 for x in rows if x['empty'])} empty on disk (an empty generated file is not a result).", ""]
    for g, xs in groups.items():
        if not xs:
            continue
        L += [f"## {g}", "", "| path | status | in Phase 7's list | bytes |", "|---|---|---|---|"]
        for x in xs:
            b = "—" if x["bytes"] is None else f"{x['bytes']:,}"
            flag = " **EMPTY**" if x["empty"] else ("" if x["on_disk"] or x["status"] == "deleted" else " **MISSING ON DISK**")
            L.append(f"| `{x['path']}` | {x['status']}{flag} | {'yes' if x['path'] in p7 else 'no'} | {b} |")
        L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=BASE_DEFAULT)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    text = render(a.base)
    if a.check:
        cur = open(DOC, encoding="utf-8").read() if os.path.exists(DOC) else ""
        strip = lambda t: "\n".join(l.rsplit("|", 2)[0] for l in t.splitlines() if l.startswith("| `"))
        if strip(cur) != strip(text):
            print("PHASE_8_CHANGED_FILES.md is stale"); return 1
        print("PHASE_8_CHANGED_FILES.md matches git and disk"); return 0
    with open(DOC, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text + "\n")
    print(f"written {os.path.relpath(DOC, ROOT)}: {text.count(chr(10))} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
