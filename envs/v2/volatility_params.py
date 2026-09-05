"""
v2.1 Phase 3: the volatility-block parameters in force, read from envs/v2/params/volatility.json.

Loader policy (the mispricing_params.py pattern, P2-* precedent):
  * file ABSENT   -> `PRESENT = False` and every constant keeps its v2 CAL value, so the repository runs
                     unchanged before `tools/phase3/apply_e3.py` has been executed;
  * file PRESENT  -> it governs the GARCH shape, scale, jumps mapping, mechanism and the IV construction;
  * file MALFORMED-> raises, loudly, as `hazard.json` and `value.json` do.
`tests/test_v2_1_phase_3.py::test_garch_params_in_force` asserts the file exists once Phase 3 is applied and
that the running GJRParams equal the values recorded here with their provenance, so absence cannot persist past
the hand-over.

Keys (each a dict with value + provenance {label, source, date, interval, n, survivor_vs_literature_gap, ...}):
  garch_shape, sbar, jumps, phase_multipliers, mechanism, iv, item73, shape_sensitivity_sets
"""
from __future__ import annotations

import json
import os
from typing import Dict, Optional

PARAM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "params")
VOLATILITY_PATH = os.path.join(PARAM_DIR, "volatility.json")

# v2 CAL values, in force until Phase 3 is applied (envs/v2/garch.py's historical defaults)
V2 = dict(alpha=0.10, gamma=0.10, beta=0.83, sbar=0.017, df=5.0, panic_mult=5.0, scale_mode="variance")
REQUIRED = ("garch_shape", "sbar", "jumps", "phase_multipliers", "mechanism", "iv")


def load(path: Optional[str] = None) -> Optional[Dict]:
    path = path or VOLATILITY_PATH
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    for k in REQUIRED:
        if k not in d or "value" not in d[k] or "label" not in d[k] or "source" not in d[k]:
            raise RuntimeError(f"{path} is malformed: key {k!r} must carry value / label / source / date / "
                               f"interval / n (see PREREG_PHASE_3.md section 11 and PHASE_3_REPORT.md)")
    return d


VOLATILITY = load()
PRESENT: bool = VOLATILITY is not None
_shape = VOLATILITY["garch_shape"]["value"] if PRESENT else {}
ALPHA: float = float(_shape.get("alpha", V2["alpha"]))
GAMMA: float = float(_shape.get("gamma", V2["gamma"]))
BETA: float = float(_shape.get("beta", V2["beta"]))
DF: float = float(_shape.get("df", V2["df"]))
SBAR: float = float(VOLATILITY["sbar"]["value"]) if PRESENT else V2["sbar"]
_mech = VOLATILITY["mechanism"]["value"] if PRESENT else {}
SCALE_MODE: str = str(_mech.get("scale_mode", V2["scale_mode"]))
MULT: Optional[Dict[str, float]] = (dict(_mech["mult"]) if PRESENT and _mech.get("mult") else None)
RAMP_DAYS: int = int(_mech.get("ramp_days", 0)) if PRESENT else 0
SWITCHING: Optional[Dict] = (dict(_mech["switching"]) if PRESENT and _mech.get("switching") else None)
PANIC_MULT: float = float(MULT["panic"]) if MULT and "panic" in MULT else V2["panic_mult"]
IV: Optional[Dict] = dict(VOLATILITY["iv"]["value"]) if PRESENT else None
JUMPS: Optional[Dict] = dict(VOLATILITY["jumps"]["value"]) if PRESENT else None
