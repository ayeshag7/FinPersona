"""
v2.1 Phase 2: the mispricing-engine parameters in force, read from envs/v2/params/mispricing.json.

Loader policy (deliberately different from value_params.py's "missing file raises"):
  * file ABSENT   -> the module reports `PRESENT = False` and every constant keeps its v2 value, so the
                     repository runs unchanged before `tools/phase2/apply_e2.py` has been executed;
  * file PRESENT  -> it governs the engine that runs, its structural parameters and the units convention;
  * file MALFORMED-> raises, loudly, as `hazard.json` and `value.json` do.
`tests/test_v2_1_phase_2.py::test_persistence_in_force` asserts that the file exists once Phase 2 is applied and
that the running engine's persistence equals the value recorded here with its provenance.

Keys (each a dict with value + provenance {label, source, date, interval, n, survivor_vs_literature_gap}):
  engine, price_scale, structural, half_life, garch_shape, moments, estimator_table[, chartist_share]
"""
from __future__ import annotations

import json
import os
from typing import Dict, Optional

PARAM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "params")
MISPRICING_PATH = os.path.join(PARAM_DIR, "mispricing.json")

# v2 values, in force until Phase 2 is applied
V2_ENGINE = "fw_fallback_hl150"
V2_PRICE_SCALE = 100.0
REQUIRED = ("engine", "price_scale", "structural", "half_life")


def load(path: Optional[str] = None) -> Optional[Dict]:
    path = path or MISPRICING_PATH
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    for k in REQUIRED:
        if k not in d or "value" not in d[k] or "label" not in d[k] or "source" not in d[k]:
            raise RuntimeError(f"{path} is malformed: key {k!r} must carry value / label / source / date / "
                               f"interval / n (see PREREG_PHASE_2.md section 10 and PHASE_2_REPORT.md)")
    return d


MISPRICING = load()
PRESENT: bool = MISPRICING is not None
ENGINE: str = str(MISPRICING["engine"]["value"]) if PRESENT else V2_ENGINE
ENGINE_FAMILY: str = str(MISPRICING["engine"].get("family", "")) if PRESENT else "fw_v2"
PRICE_SCALE: float = float(MISPRICING["price_scale"]["value"]) if PRESENT else V2_PRICE_SCALE
STRUCTURAL: Dict = dict(MISPRICING["structural"]["value"]) if PRESENT else {}
HALF_LIFE: Optional[float] = float(MISPRICING["half_life"]["value"]) if PRESENT else None
CHARTIST_SHARE: Optional[float] = (float(MISPRICING["chartist_share"]["value"])
                                  if PRESENT and "chartist_share" in MISPRICING else None)
