"""For each of E5's twelve levels: on what share of the sweep's own 240 (scenario, seed) paths does the level
actually change the market?

    python -u -m tools.phase9.e9_5_path_change

A level that leaves the path byte-identical to the default re-measures the default under another name, and no
hash check can see it: `Gen_Config_Hash` differs on those runs because the rate is part of the hashed
configuration, while the price series it produced is the same.  `PREREG_PHASE_9_STAGE2_E5.md` 2 registers the
consequence in advance -- the two `jump_rate` levels are run as the design fixes them, but their **primary
verdict is read on the paths the level actually changed**, with the full 240 beside it as the sensitivity.

This file is that measurement, and `e9_4/e5_path_change.json` is its output.  Jumps are rare by construction
(the fitted rate is 5.825e-4 a day), so over 200 days plus the 750-day burn-in most paths draw no jump at
either level and the shared uniform stream reproduces the default exactly.
"""
from __future__ import annotations

import hashlib
import json
import os

import numpy as np

from envs.synthetic_market import SyntheticMarketEnv
from tools.phase9.e9_1_ranking import level_configs

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e9_4", "e5_path_change.json")

SIX = ("garch_set", "sbar", "mu_V", "half_life", "sigma_V", "jump_rate")
SCEN = ("flat", "bull_trap", "crash", "sustained_bull")
SEEDS = range(10001, 10061)


def digest(cfg, sc, seed) -> str:
    """sha256[:16] of asset 0's price series, rounded to 10 dp so a float formatting change is not a difference."""
    e = SyntheticMarketEnv(sc, 200, seed, crash_discount=0.70, config=cfg or None)
    d = e.data[e.data["asset"] == 0]
    return hashlib.sha256(np.round(np.asarray(d["price"], dtype=float), 10).tobytes()).hexdigest()[:16]


def main() -> int:
    levels = {k: v for k, v in level_configs().items() if k != "default" and k.split("__")[0] in SIX}
    if len(levels) != 12:
        raise SystemExit(f"expected E5's twelve levels, got {len(levels)}: {sorted(levels)}")

    base = {(sc, s): digest({}, sc, s) for sc in SCEN for s in SEEDS}
    out = {}
    for name in sorted(levels):
        # `changed_paths` is the point of the file: the counts say how much of the verdict is real, but only the
        # identities let the analysis READ the verdict on those paths, which section 2 requires for `jump_rate`.
        # The key is `Scenario_Cell|Seed`, the same string `stats_v2.seed_level_pairs` builds as `Path`, so the
        # list joins the per-seed differences directly.  `scenario_cell` appends the crash discount only when
        # `per_run.csv` carries a `Crash_Discount` column; the scored grid does not, so the cell is the bare
        # scenario name and `crash` stays `crash`.  Checked against `stats_stage1_open/*_v21_contrasts.csv`.
        changed = [f"{sc}|{s}" for sc in SCEN for s in SEEDS if digest(levels[name], sc, s) != base[(sc, s)]]
        per = {sc: sum(1 for p in changed if p.split("|")[0] == sc) for sc in SCEN}
        diff = len(changed)
        out[name] = {"changed": diff, "of": 240, "share": round(diff / 240, 4), "by_scenario": per,
                     "changed_paths": changed}
        print(f"{name:26s} path changes on {diff:3d}/240 = {diff / 240:6.1%}   {per}", flush=True)

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out, indent=1) + "\n")
    print(f"\nwritten -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
