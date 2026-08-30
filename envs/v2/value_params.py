"""
v2.1 Phase 1: the value-and-price-structure parameters in force, read from envs/v2/params/value.json with a LOUD loader
(as hazard.json: a missing file raises; every generator default that Phase 1 fitted or decided comes from here, with its
provenance record). The file is the record; the module constants below are read from it at import.

Keys (each a dict with value + provenance {label, source, date, interval, n, ...}):
  sigma_V, mu_V, df_V, s_x_fit, h_fit, start_price_mode, start_price_range, jump (placement, p_ann, lam_res, jump_sd,
  jump_rate_x, jump_mean_x), burn_in (per engine + mode), analysis_set (n, exclusion rule)
"""
from __future__ import annotations

import json
import os
from typing import Dict, Optional

PARAM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "params")
VALUE_PATH = os.path.join(PARAM_DIR, "value.json")


def load_value_params(path: Optional[str] = None) -> Dict:
    path = path or VALUE_PATH
    if not os.path.exists(path):
        raise RuntimeError(f"{path} is missing: the Phase-1 value/price-structure parameters (sigma_V, mu_V, df_V, start-price "
                           f"mechanism, jump placement, burn-in) must be present with their provenance; see PHASE_1_REPORT.md")
    with open(path, encoding="utf-8") as fh:
        v = json.load(fh)
    for k in ("sigma_V", "mu_V", "df_V", "start_price_mode", "start_price_range", "jump", "burn_in"):
        if k not in v:
            raise RuntimeError(f"{path} lacks key {k!r}")
    return v


VALUE = load_value_params()
SIGMA_V: float = float(VALUE["sigma_V"]["value"])
MU_V: float = float(VALUE["mu_V"]["value"])
DF_V: Optional[float] = VALUE["df_V"]["value"]                 # None = Gaussian
START_PRICE_MODE: str = str(VALUE["start_price_mode"]["value"])   # fixed | randomise (A) | normalise (B) | both (C)
START_PRICE_RANGE = tuple(float(x) for x in VALUE["start_price_range"]["value"])
JUMP = VALUE["jump"]["value"]                                    # placement, p_ann, lam_res, jump_sd, jump_rate_x, jump_mean_x
BURN_IN = VALUE["burn_in"]["value"]                              # {"mode": "long"|"stored", "days": {engine: n}, "stored_days": 60}


def burn_in_for(engine: str) -> int:
    d = BURN_IN["days"]
    return int(d.get(engine, d.get("default", 260)))


def burn_in_mode_for(engine: str) -> str:
    """E1.5 (REG-17) decides per engine: 'long' (option A) or 'stored' (option B). value.json carries the per-engine modes
    under burn_in.value.modes_by_engine; 'mode' is the default engine's choice."""
    return str(BURN_IN.get("modes_by_engine", {}).get(engine, BURN_IN["mode"]))


def stored_state_path(engine: str) -> str:
    return os.path.join(PARAM_DIR, f"burn_in_states_{engine}.npz")
