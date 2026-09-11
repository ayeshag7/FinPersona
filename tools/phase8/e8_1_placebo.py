"""
v2.1 Phase 8 -- E8.1(e): the directive placebo's matching to each persona's mandate, on the rendered texts
(PREREG_PHASE_8.md 1.6; weakness 60).

    python -u -m tools.phase8.e8_1_placebo

For ISFJ, INTJ and ENTJ at the grid's wording (`rewritten`): the real block, and the placebo block under
`placebo_version` "v2" (the text every published run used) and "v2_1" (the per-persona matched placebo), measured with
`agent/prompt_matching.py` -- the registered word rule, clause rule and imperative annotation.  Phase 7's pooled
measurement (`e7_7/placebo_length.json`) is carried beside for comparison.

Output: docs/env_v2/generated/v2_1/e8_1/placebo_matching.{json,md}
"""
from __future__ import annotations

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e8_1")
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
WORDING = "rewritten"


def main():
    from agent import v2_prompts as P
    from agent import prompt_matching as PM
    rows = []
    for p in PERSONAS:
        real = P.mandate_block("mandate", p, WORDING)
        for ver in P.PLACEBO_VERSIONS:
            plac = P.mandate_block("placebo_directive", p, WORDING, ver)
            r = PM.matching(real, plac)
            r.update({"persona": p, "placebo_version": ver, "clauses_real": PM.clauses(real),
                      "clauses_placebo": PM.clauses(plac), "placebo_block": plac, "real_block": real})
            rows.append(r)
    p7 = None
    p7path = os.path.join(GEN, "e7_7", "placebo_length.json")
    if os.path.exists(p7path):
        p7 = json.load(open(p7path, encoding="utf-8")).get("words")
    doc = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "wording": WORDING,
           "word_tolerance": PM.WORD_TOLERANCE, "rows": rows, "phase7_pooled_words": p7,
           "v2_pass_count": sum(1 for r in rows if r["placebo_version"] == "v2" and r["pass"]),
           "v2_1_pass_count": sum(1 for r in rows if r["placebo_version"] == "v2_1" and r["pass"])}
    os.makedirs(OUT, exist_ok=True)
    json.dump(doc, open(os.path.join(OUT, "placebo_matching.json"), "w", encoding="utf-8"), indent=1)
    L = ["# E8.1(e) — the directive placebo against each persona's mandate, on the rendered texts", "",
         "| persona | placebo version | words real / placebo (rel. diff) | within 10 % | imperatives real / placebo | equal | both criteria |",
         "|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['persona']} | {r['placebo_version']} | {r['words_real']} / {r['words_placebo']} ({r['word_rel_diff']:.3f}) | "
                 f"{'yes' if r['words_pass'] else '**no**'} | {r['imperatives_real']} / {r['imperatives_placebo']} | "
                 f"{'yes' if r['imperatives_pass'] else '**no**'} | {'**PASS**' if r['pass'] else '**FAIL**'} |")
    with open(os.path.join(OUT, "placebo_matching.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))
    for r in rows:
        if r["placebo_version"] == "v2_1":
            print(f"\n{r['persona']} v2_1 placebo block:\n{r['placebo_block']}")


if __name__ == "__main__":
    main()
