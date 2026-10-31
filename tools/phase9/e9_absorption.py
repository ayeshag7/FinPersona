"""The absorption ratio A of E2 (`PREREG_PHASE_9_STAGE2_E2.md` 3).

A asks what share of the mandate's effect a content-free block reproduces **in the mandate's own direction**:

    A = ((placebo - static) . s) / |memory - static| ,   s = sign(memory - static) on band-MAS

Both the numerator and the denominator are seed-level paired differences on the same paths, built by
`tools.stats_v2.seed_level_pairs` and estimated by `tools.stats_v2.pigeonhole_ci`, so A is read off exactly the
quantities the registered confirmatory test reads.

The sign alignment and the floor are not decoration.  Measured on stage 1's first 60 seeds over E2's 36 cells,
34 denominators have a bootstrap CI excluding 0 but **14 of those are negative** -- memory *improves* band-MAS
(Phi-4 ENTJ flat -0.375, Llama 3.1 8B ENTJ flat -0.220) -- so an unsigned ratio would average cells whose
mandate effects point opposite ways.  Two more denominators are about 1.5e-4, where a sign-only guard admits
|A| ~ 77.  Hence BOTH guards, registered before E2 ran:

  * the denominator's cluster-bootstrap CI must exclude 0, and
  * |memory - static| must be at least `FLOOR` (0.01, a fifth of the registered Delta of 0.05).

A cell failing either guard yields A = NaN and is counted, never quietly dropped.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from tools.stats_v2 import pigeonhole_ci, scenario_cell, seed_level_pairs

FLOOR = 0.01                 # a fifth of the registered Delta = 0.05
METRIC = "band_mas"
MANDATE_ARM = "memory"
REFERENCE = "static"


def _cell_estimate(pairs: pd.DataFrame, persona: str, cell: str, n_boot: int, seed: int) -> Optional[dict]:
    g = pairs[(pairs["Persona"] == persona) & (pairs["Scenario_Cell"] == cell)]
    if g.empty or g["Path"].nunique() < 2:
        return None
    return pigeonhole_ci(g, n_boot=n_boot, seed=seed)


def absorption(per_run: pd.DataFrame, arm: str, metric: str = METRIC, mandate_arm: str = MANDATE_ARM,
               reference: str = REFERENCE, floor: float = FLOOR, n_boot: int = 1999,
               seed: int = 0) -> pd.DataFrame:
    """One row per Model x Persona x Scenario_Cell, with A and the state of both guards.

    `per_run` must hold `arm`, `mandate_arm` and `reference` rows for the same paths.  Replicates are averaged
    per arm before the difference, as `seed_level_pairs` does.
    """
    den_all = seed_level_pairs(per_run, metric, mandate_arm, reference)
    num_all = seed_level_pairs(per_run, metric, arm, reference)
    if den_all.empty or num_all.empty:
        return pd.DataFrame(columns=["Model", "Persona", "Scenario_Cell", "arm", "A"])

    out = []
    keys = den_all[["Model", "Persona", "Scenario_Cell"]].drop_duplicates()
    for _, k in keys.iterrows():
        model, persona, cell = k["Model"], k["Persona"], k["Scenario_Cell"]
        den = _cell_estimate(den_all[den_all["Model"] == model], persona, cell, n_boot, seed)
        num = _cell_estimate(num_all[num_all["Model"] == model], persona, cell, n_boot, seed)
        if den is None or num is None:
            continue
        d_mand = float(den["estimate"])
        d_arm = float(num["estimate"])
        ci_excludes_0 = bool(den["ci_lo"] > 0 or den["ci_hi"] < 0)
        above_floor = bool(abs(d_mand) >= floor)
        s = float(np.sign(d_mand))
        a = (d_arm * s) / abs(d_mand) if (ci_excludes_0 and above_floor and d_mand != 0) else float("nan")
        out.append({
            "Model": model, "Persona": persona, "Scenario_Cell": cell, "arm": arm, "metric": metric,
            "d_mandate": d_mand, "d_mandate_ci_lo": float(den["ci_lo"]), "d_mandate_ci_hi": float(den["ci_hi"]),
            "d_arm": d_arm, "sign": s, "A": a,
            "guard_ci_excludes_0": ci_excludes_0, "guard_above_floor": above_floor,
            "admitted": bool(ci_excludes_0 and above_floor),
            "n_paths": int(min(den["n_paths"], num["n_paths"])),
        })
    return pd.DataFrame(out)


def guard_counts(t: pd.DataFrame) -> dict:
    """How many cells each guard excluded -- reported beside A, as registered."""
    if t.empty:
        return {"cells": 0, "admitted": 0, "excluded_ci_includes_0": 0, "excluded_below_floor": 0,
                "excluded_by_both": 0, "admitted_negative_mandate": 0}
    ci, fl = t["guard_ci_excludes_0"], t["guard_above_floor"]
    return {
        "cells": int(len(t)),
        "admitted": int((ci & fl).sum()),
        "excluded_ci_includes_0": int((~ci & fl).sum()),
        "excluded_below_floor": int((ci & ~fl).sum()),
        "excluded_by_both": int((~ci & ~fl).sum()),
        "admitted_negative_mandate": int(((ci & fl) & (t["d_mandate"] < 0)).sum()),
    }
