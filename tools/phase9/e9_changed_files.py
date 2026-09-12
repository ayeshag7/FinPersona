"""
v2.1 Phase 9 -- PHASE_9_CHANGED_FILES.md generated from git and verified against disk (the Phase-7 and Phase-8 pattern).

    python -m tools.phase9.e9_changed_files [--base 66ba535] [--check]

**Phases 7 and 8 are committed** (`aadf9e0`, then the Phase-9 execution prompt as `66ba535`), so unlike Phase 8's list
git separates this phase cleanly: the diff from `66ba535` and the untracked files of the working tree are Phase 9's own
work, and no "also in the previous phase's list" column is needed.

The list excludes itself (rule 17) and the simulation caches. `--check` exits 1 when the document on disk differs from
what git and the tree give now.
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.phase7 import e7_changed_files as C7   # noqa: E402

DOC = os.path.join(ROOT, "docs", "env_v2", "v2_1", "PHASE_9_CHANGED_FILES.md")
BASE_DEFAULT = "66ba535"
IGNORE = ("docs/env_v2/generated/v2_1/e9_3/_cache/", "docs/env_v2/generated/v2_1/e6_1/cache/", "COMMIT",
          "docs/env_v2/v2_1/PHASE_9_CHANGED_FILES.md")


def render(base: str) -> str:
    C7.IGNORE = IGNORE
    rows = C7.rows(base)
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
    empty = sum(1 for x in rows if x["empty"])
    same = base.startswith(head) or head.startswith(base)
    L = [f"# Phase 9 — files written or changed (generated from git `{base}..{head}` and the working tree by "
         f"`tools/phase9/e9_changed_files.py`; verified against disk by `--check`)", "",
         f"{len(rows)} paths in the working tree against `{base}`, the commit that carries the Phase-9 execution "
         f"prompt. Phases 7 and 8 are committed, so every path here is this phase's own. "
         f"{empty} empty on disk (an empty generated file is not a result).", ""]
    if same:
        L[2] += (f" **Nothing of this phase is committed:** `HEAD` is still `{head}`, so the commit range is empty and "
                 f"every path below is an uncommitted change or an untracked file in the working tree.")
    for g, xs in groups.items():
        if not xs:
            continue
        L += [f"## {g}", "", "| path | status | bytes |", "|---|---|---|"]
        for x in xs:
            b = "—" if x["bytes"] is None else f"{x['bytes']:,}"
            flag = " **EMPTY**" if x["empty"] else ("" if x["on_disk"] or x["status"] == "deleted" else " **MISSING ON DISK**")
            L.append(f"| `{x['path']}` | {x['status']}{flag} | {b} |")
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
        strip = lambda t: "\n".join(l.rsplit("|", 2)[0] for l in t.splitlines() if l.startswith("| `"))   # noqa: E731
        if strip(cur) != strip(text):
            print("PHASE_9_CHANGED_FILES.md is stale"); return 1
        print("PHASE_9_CHANGED_FILES.md matches git and disk"); return 0
    with open(DOC, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text + "\n")
    print(f"written {os.path.relpath(DOC, ROOT)}: {text.count(chr(10))} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
