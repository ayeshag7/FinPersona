"""
v2.1 Phase 8 -- what the L3 probe's answers are made of (the probe is Phase 6's, run under D2 in this phase).

    python -u -m tools.phase8.e8_l3_rule

Two models from different providers (Gemini 2.5 Flash, GPT-5 mini) gave IDENTICAL answers on all 200 normal-arm probes,
and every model scored exactly the same sign accuracy.  This tool tests the explanation that needs no bug: that the
models answer "over- or under-valued relative to fundamental value" by comparing the rendered price with the one
field labelled a value -- the analyst fair-value estimate.

For every probe it parses `Price` and `Analyst fair-value estimate ($)` from the prompt the model saw (in the shuffled
arm, the other probe's fields), forms the rule OVER iff price > analyst estimate, and reports per model and arm: the
share of answers equal to the rule, the rule's own sign accuracy against sign(x), and the pairwise agreement between
models.  Output: docs/env_v2/generated/v2_1/e6_l3/rule_analysis.json
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

D = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e6_l3")


def _num(pat, s):
    m = re.search(pat, s)
    return float(m.group(1)) if m else np.nan


def main():
    from tools.phase6.e6_l3_probe import parse
    pr = pd.read_csv(os.path.join(D, "probes.csv"))
    price = pr["prompt"].apply(lambda s: _num(r"- Price: *([0-9.]+)", s)).to_numpy(float)
    analyst = pr["prompt"].apply(lambda s: _num(r"Analyst fair-value estimate \(\$\): *([0-9.]+)", s)).to_numpy(float)
    if np.isnan(price).any() or np.isnan(analyst).any():
        raise SystemExit("a probe's price or analyst estimate could not be parsed; the rule is not defined for it")
    rule = np.where(price > analyst, 1, -1)
    y = np.sign(pr["x"].to_numpy(float)).astype(int)
    shuffled_from = pr["shuffled_from"].to_numpy(int)
    out = {"n_probes": int(len(pr)), "rule": "OVER iff rendered price > rendered analyst fair-value estimate",
           "rule_sign_accuracy_normal": float(np.mean(rule == y)),
           "rule_sign_accuracy_shuffled": float(np.mean(rule[shuffled_from] == y)),
           "base_rate_x_positive": float(np.mean(y > 0)), "models": {}, "pairwise_agreement_normal": {},
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    preds = {}
    for f in sorted(glob.glob(os.path.join(D, "answers_*.csv"))):
        name = os.path.basename(f)[len("answers_"):-4]
        # only the probe's own answer files, answers_<model>_<normal|shuffled>.csv; the set-aside records of discarded
        # attempts (`.temperature_rejected`, `.thinking_truncated`) are never read -- a first version skipped only one
        # suffix, read the other as an arm called "truncated" and failed on its 146 rows
        m = re.fullmatch(r"(.+)_(normal|shuffled)", name)
        if m is None:
            continue
        model, arm = m.group(1), m.group(2)
        a = pd.read_csv(f).sort_values("i")
        raw = a["raw"].astype(str)
        if raw.str.startswith("ERROR").all():
            out["models"].setdefault(model, {})[arm] = {"all_errors": True}
            continue
        p = np.array([parse(r) for r in raw])
        shown_rule = rule if arm == "normal" else rule[shuffled_from]
        out["models"].setdefault(model, {})[arm] = {
            "n": int(len(p)), "agreement_with_rule": float(np.mean(p == shown_rule)),
            "sign_accuracy": float(np.mean(p == y)), "share_over": float(np.mean(p == 1)),
            "share_under": float(np.mean(p == -1)), "share_fair_or_unparsed": float(np.mean(p == 0))}
        if arm == "normal":
            preds[model] = p
    ks = sorted(preds)
    for i, a in enumerate(ks):
        for b in ks[i + 1:]:
            out["pairwise_agreement_normal"][f"{a}|{b}"] = float(np.mean(preds[a] == preds[b]))
    with open(os.path.join(D, "rule_analysis.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
