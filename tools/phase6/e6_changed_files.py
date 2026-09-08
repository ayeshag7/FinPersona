"""
v2.1 Phase 6 -- PHASE_6_CHANGED_FILES.md generated from git and verified against disk (the execution prompt's rule).

    python -m tools.phase6.e6_changed_files [--base 0b2c48c] [--check]

Every path is the diff between the Phase-5 hand-over commit and HEAD plus the untracked files under the phase's
directories, with its status (added / modified / renamed / deleted / untracked), size on disk, and -- for generated
outputs -- whether the file is non-empty (P5-12: a tool's "done" check tests emptiness, not presence).  `--check`
exits 1 when the document on disk differs from what git and the tree give now.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOC = os.path.join(ROOT, "docs", "env_v2", "v2_1", "PHASE_6_CHANGED_FILES.md")
BASE_DEFAULT = "0b2c48c"     # the Phase-5 commit
IGNORE = ("docs/env_v2/generated/v2_1/e6_1/cache/", "COMMIT")


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout


def rows(base: str):
    out = []
    for line in _git("diff", "--name-status", "-M", base, "HEAD").splitlines():
        parts = line.split("\t")
        st, path = parts[0], parts[-1]
        out.append((path, {"A": "added", "M": "modified", "D": "deleted"}.get(st[0], "renamed" if st[0] == "R" else st)))
    for line in _git("status", "--porcelain", "--untracked-files=all").splitlines():
        st, path = line[:2].strip(), line[3:].strip()
        if st == "??":
            out.append((path, "untracked"))
        elif st in ("M", "A", "AM", "MM"):
            out.append((path, "modified (uncommitted)"))
    seen = {}
    for p, s in out:
        p = p.replace("\\", "/")
        if any(p.startswith(i) or p == i for i in IGNORE):
            continue
        seen[p] = s
    res = []
    for p, s in sorted(seen.items()):
        full = os.path.join(ROOT, p)
        exists = os.path.exists(full)
        size = os.path.getsize(full) if exists else None
        res.append({"path": p, "status": s, "on_disk": exists, "bytes": size,
                    "empty": (size == 0 and not p.endswith("__init__.py")) if exists else None})
    return res


def render(base: str) -> str:
    r = rows(base)
    head = _git("rev-parse", "--short", "HEAD").strip()
    groups = {"envs/": [], "evaluation/": [], "tools/": [], "tests/": [], "docs/env_v2/v2_1/": [], "docs/env_v2/spec/": [],
              "docs/env_v2/decisions/": [], "docs/env_v2/generated/": [], "other": []}
    for x in r:
        for g in groups:
            if g != "other" and x["path"].startswith(g):
                groups[g].append(x); break
        else:
            groups["other"].append(x)
    L = [f"# Phase 6 — files written or changed (generated from git `{base}..{head}` and the working tree by "
         f"`tools/phase6/e6_changed_files.py`; verified against disk by `--check`)", "",
         f"{len(r)} paths; {sum(1 for x in r if x['status'] == 'deleted')} deleted; "
         f"{sum(1 for x in r if x['empty'])} empty on disk (an empty generated file is not a result).", ""]
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
        # the sizes of files that are still being written change; compare the path/status columns only
        strip = lambda t: "\n".join(l.rsplit("|", 2)[0] for l in t.splitlines() if l.startswith("| `"))
        if strip(cur) != strip(text):
            print("PHASE_6_CHANGED_FILES.md is stale"); return 1
        print("PHASE_6_CHANGED_FILES.md matches git and disk"); return 0
    with open(DOC, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text + "\n")
    print(f"written {os.path.relpath(DOC, ROOT)}: {text.count(chr(10))} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
