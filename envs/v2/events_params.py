"""
v2.1 Phase 4: the event / schedule / control block in force, read from envs/v2/params/events.json.

Loader policy (the volatility_params.py pattern, P3-* precedent):
  * file ABSENT   -> `PRESENT = False` and every constant keeps its v2 DESIGN value, so the repository runs
                     unchanged before `tools/phase4/apply_e4.py` has been executed;
  * file PRESENT  -> it governs the schedule ranges, the hazard, the blow-off criterion, the post-top leg,
                     the control definition, the event-dynamics formulation and the calendar rendering;
  * file MALFORMED-> raises, loudly, as `hazard.json`, `value.json` and `volatility.json` do.

`tests/test_v2_1_phase_4.py::test_schedule_ranges_from_params` and `::test_hazard_params_provenance` assert the
file exists once Phase 4 is applied and that the running schedule draws inside the FIT ranges recorded here,
so absence cannot persist past the hand-over.

Keys (each a dict with value + provenance {label, source, date, interval, n, ...}):
  schedule_ranges, hazard, blowoff, post_top, crash_v_drift, control, dynamics, calendar, multi_asset
"""
from __future__ import annotations

import json
import os
from typing import Dict, Optional

PARAM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "params")
EVENTS_PATH = os.path.join(PARAM_DIR, "events.json")

# v2 DESIGN values, in force until Phase 4 is applied (envs/v2/schedule.py's historical uniforms).
# These are exactly the ranges E4.2 replaces, kept here so the "before" column of the report is code, not prose.
V2 = {
    "det_len": [15, 40],
    "panic_len": [15, 70],
    "delta": [0.70, 0.70],
    "D_V": [0.10, 0.30],
    "front_load": [0.50, 0.50],
    "kappa": [0.02, 0.04],
    "post_top_len": [10, 30],
    "post_top_drop": [0.30, 0.50],
    "mu_bull": [0.0015, 0.0025],
    "setup_frac": [0.25, 0.55],
    "setup_event_first": [5, 20],
}
REQUIRED = ("schedule_ranges", "hazard", "blowoff", "post_top", "control", "dynamics", "calendar")


def load(path: Optional[str] = None) -> Optional[Dict]:
    path = path or EVENTS_PATH
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    for k in REQUIRED:
        if k not in d or "value" not in d[k] or "label" not in d[k] or "source" not in d[k]:
            raise RuntimeError(
                f"{path} is malformed: key {k!r} must carry value / label / source / date / interval / n "
                f"(see PREREG_PHASE_4.md section 11 and PHASE_4_REPORT.md). No entry may ship with a null "
                f"interval -- Phase 3's review caught exactly that.")
        if d[k].get("interval", "missing") is None:
            raise RuntimeError(f"{path}: key {k!r} ships with \"interval\": null, which PREREG_PHASE_4.md "
                               f"forbids. State the interval or say why the entry has none.")
    # Every status must be a term the file itself declares.  Nothing checked this before, and by the end of
    # Phase 4 two of ten entries carried undeclared statuses while `hazard` carried one whose declared meaning
    # ("the v2 behaviour stays") contradicted the value in force -- the drift that P4-39 recorded.  A
    # controlled vocabulary is only a control if something enforces it.
    declared = set(d.get("_status_key", {}))
    if declared:
        undeclared = {k: v["status"] for k, v in d.items()
                      if isinstance(v, dict) and "status" in v and v["status"] not in declared}
        if undeclared:
            raise RuntimeError(
                f"{path}: these entries carry a status that _status_key does not declare: {undeclared}. "
                f"Declared terms are {sorted(declared)}. Add the term to _status_key with its meaning, or use "
                f"an existing one -- do not invent a status inline (P4-39).")
    return d


EVENTS = load()
PRESENT: bool = EVENTS is not None

_sr = EVENTS["schedule_ranges"]["value"] if PRESENT else {}
# a range entry is either [lo, hi] (uniform) or {"grid": [...]} (an empirical quantile grid, sampled by
# inverse CDF -- PREREG_PHASE_4_ADDENDUM section 3).  dict entries must survive the merge intact.
# E4.19/P4-40: how the crash depth draw relates to the `crash_discount` arm factor.
#   "unconditional" -- draw depth from the empirical grid and ignore delta (the Phase-4 main-pass
#                     behaviour, which made checklist item 10 exactly inert)
#   "centred"       -- shift that distribution so its centre tracks delta, keeping the fitted shape
DEPTH_MODE: str = str((EVENTS["schedule_ranges"]["value"].get("depth_mode")
                       if PRESENT else None) or "unconditional")
# E4.20/P4-41: multiplicative gain on the TARGET depth, closing the loop between the depth the panel
# asks for and the depth the generator realises.  1.0 = uncalibrated.
DEPTH_GAIN: float = float((EVENTS["schedule_ranges"]["value"].get("depth_gain")
                           if PRESENT else None) or 1.0)

# `schedule_ranges.value` also carries scalar SETTINGS (depth_mode, depth_gain) beside the ranges.
# They must not be merged into RANGES: list("centred") would silently become a list of characters,
# which is the same failure mode as the {"grid": [...]} entries hitting list() in the first pass.
_SETTINGS = ("depth_mode", "depth_gain")
RANGES: Dict[str, object] = {**V2,
                             **{k: (dict(v) if isinstance(v, dict) else list(v))
                                for k, v in _sr.items() if k not in _SETTINGS}}

_hz = EVENTS["hazard"]["value"] if PRESENT else {}
HAZARD_MAPPING: str = str(_hz.get("mapping", "v2_cal"))
HAZARD_H0: Optional[float] = float(_hz["h0"]) if "h0" in _hz else None
HAZARD_B: Optional[float] = float(_hz["b"]) if "b" in _hz else None

_bo = EVENTS["blowoff"]["value"] if PRESENT else {}
# "ex_post" is the v2 behaviour (a label assigned after the run, which cannot drive the variance -- the dead
# multiplier Phase 3 found); "dynamic" assigns it in real time from the drift, so the multiplier reaches the driver.
BLOWOFF_MODE: str = str(_bo.get("mode", "ex_post"))
BLOWOFF_G_THRESHOLD: Optional[float] = float(_bo["g_threshold"]) if "g_threshold" in _bo else None
# v2.1 Phase 4 (P4-11): volatility.json records blow-off at MANIA's value because the v2 label was assigned ex
# post and its multiplier was dead code.  With the label alive the multiplier needs a value of its own.  It
# lives HERE rather than in volatility.json so Phase 3's frozen file is not edited by Phase 4; the generator
# overrides GJRParams.mult["blow-off"] with it when present.
BLOWOFF_MULT: Optional[float] = float(_bo["mult"]) if "mult" in _bo else None

_pt = EVENTS["post_top"]["value"] if PRESENT else {}
POST_TOP_MODE: str = str(_pt.get("mode", "v2_linear"))       # "v2_linear" | "decay" (E4.8's re-derived shape)
POST_TOP_LAM: float = float(_pt.get("lam", 0.10))
POST_TOP_HALF_LIFE: Optional[float] = float(_pt["half_life"]) if "half_life" in _pt else None

_cv = EVENTS["crash_v_drift"]["value"] if PRESENT and "crash_v_drift" in EVENTS else {}
CRASH_V_MODE: str = str(_cv.get("mode", "flat_after_det"))   # v2: mu_V = 0 in panic/stabilisation (item 73)
CRASH_V_TAIL_SHARE: float = float(_cv.get("tail_share", 0.0))

_ct = EVENTS["control"]["value"] if PRESENT else {}
CONTROL_DEF: str = str(_ct.get("definition", "C"))           # REG-7 A | B | C (v2) | D
CONTROL_LAM_SB: float = float(_ct.get("lam_sb", 0.15))
CONTROL_V_THRESHOLD: float = float(_ct.get("v_threshold", 1.2))
CONTROL_X_BAND: Optional[list] = (list(_ct["x_band"]) if _ct.get("x_band") else None)

_dy = EVENTS["dynamics"]["value"] if PRESENT else {}
DYNAMICS: str = str(_dy.get("formulation", "A"))             # REG-8 A (tracking gain) | B | C | D
LAM_PANIC: float = float(_dy.get("lam_panic", 0.10))
PHI_REGIME: Optional[Dict[str, float]] = (dict(_dy["phi_regime"]) if _dy.get("phi_regime") else None)

_cl = EVENTS["calendar"]["value"] if PRESENT else {}
DAY_INDEX_MODE: str = str(_cl.get("day_index", "day_n"))     # REG-9 "day_n" (D6 default) | "none" | "date"
ORDERING_MIX: Optional[Dict[str, float]] = (dict(_cl["ordering_mix"]) if _cl.get("ordering_mix") else None)
RANDOMISE_EPS_QUARTER: bool = bool(_cl.get("randomise_eps_quarter", False))

_ma = EVENTS["multi_asset"]["value"] if PRESENT and "multi_asset" in EVENTS else {}
MA_PER_ASSET_EVENTS: bool = bool(_ma.get("per_asset_events", False))
MA_COMMON_LOADING: Optional[float] = (float(_ma["common_loading"]) if "common_loading" in _ma else None)


def provenance(key: str) -> Dict:
    """The full provenance block for a key, for the report and the tests."""
    if not PRESENT or key not in EVENTS:
        return {}
    return {k: v for k, v in EVENTS[key].items() if k != "value"}
