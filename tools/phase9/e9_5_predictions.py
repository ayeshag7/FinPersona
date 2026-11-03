"""The registered predictions of E2-E5, evaluated beside each experiment's statistics.

    imported by tools.phase9.e9_5_e{2,3,4,5}_analyse

Why this is a module of its own.  Each stage-2 pre-registration closes its section 4 with the same
sentence -- *"A wrong prediction is reported as wrong."* -- over four predictions that sit outside every
BH family.  Sixteen in all, and not one of the four analysers evaluated any of them.  The contrasts and
the absorption tables did hold the material, so a verdict could always be read off by hand, and that is
exactly how a wrong prediction goes unreported: nothing fails, because nothing is computed.  Two of E2's
four are in fact wrong and were written down nowhere until this file existed.

The four verdicts, and why there are four rather than two:

*   `holds` / `fails` -- the registered bar, evaluated on the artefacts the experiment's own analyser
    wrote, with the numbers that decided it carried in `stat`.

*   `unevaluated` -- the inputs are not in `per_run.csv`.  E3's P1, P2 and P4 read the per-STEP series
    (salience shares, the day-1 gate, the static arm's mean cash share) and one row per run cannot answer
    them.  An unevaluated prediction is never reported as holding, and never counted in a tally of the
    ones that did.

*   `degenerate` -- the bar is met, but by arithmetic rather than by evidence.  E4's P2 correlates the
    size of the Track-A reduction against the static arm's headroom while the reduced arm sits on the
    metric's floor: reduction = headroom - 0, so the two are the same number and Spearman returns +1.000
    whatever the models did.  It is its own verdict so that it can never be quoted as support.

A prediction is keyed by experiment and id, carries the pre-registration's own words, and is written to
`predictions.csv` beside the statistics it was computed from, so the verdict and the numbers behind it
travel together.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List

import pandas as pd

HOLDS, FAILS, UNEVALUATED, DEGENERATE = "holds", "fails", "unevaluated", "degenerate"
PASSING = (HOLDS,)                      # `degenerate` is deliberately not in here


@dataclass
class Prediction:
    """One registered prediction, its bar, and what the data did against it."""
    pid: str
    registered: str                     # the pre-registration's own words, trimmed to the claim
    bar: str                            # the threshold, as section 4 states it
    verdict: str                        # holds | fails | unevaluated | degenerate
    evidence: str                       # one line a reader can check against the artefacts
    stat: Dict = field(default_factory=dict)

    def __post_init__(self):
        if self.verdict not in (HOLDS, FAILS, UNEVALUATED, DEGENERATE):
            raise ValueError(f"{self.pid}: {self.verdict!r} is not a verdict")


def verdict_of(ok: bool) -> str:
    return HOLDS if ok else FAILS


def write(experiment: str, preds: List[Prediction], out_dir: str) -> List[Dict]:
    """Write `predictions.csv`, print the block, and return rows for the caller's summary.json."""
    rows = [{"experiment": experiment, "prediction": p.pid, "verdict": p.verdict, "bar": p.bar,
             "evidence": p.evidence, "registered": p.registered,
             "stat": json.dumps(p.stat, sort_keys=True)} for p in preds]
    pd.DataFrame(rows).to_csv(os.path.join(out_dir, "predictions.csv"), index=False)

    n_held = sum(p.verdict == HOLDS for p in preds)
    n_fail = sum(p.verdict == FAILS for p in preds)
    n_other = len(preds) - n_held - n_fail
    print(f"\n  --- {experiment} registered predictions ({experiment} pre-registration, section 4) ---")
    for p in preds:
        print(f"    {p.pid}  {p.verdict.upper():<12} {p.evidence}")
    print(f"    {n_held} hold, {n_fail} fail, {n_other} neither; a wrong prediction is reported as wrong")
    return [{k: v for k, v in r.items() if k != "registered"} for r in rows]
