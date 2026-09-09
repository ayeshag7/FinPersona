"""
v2.1 Phase 5: the observable-field parameters in force, read from envs/v2/params/observables.json.

Loader policy (the events_params.py pattern, P4-* precedent):
  * file ABSENT   -> `PRESENT = False`; every block keeps its v2 DESIGN behaviour (`V2` below), so the repository
                     runs unchanged before `tools/phase5/apply_e5.py` has been executed;
  * file PRESENT  -> it governs the multiple, the EPS/announcement block, the dividend block, the analyst field, the
                     sentiment process and the volume process;
  * file MALFORMED-> raises, loudly: a missing required entry, a null interval, or a status the file's own
                     `_status_key` does not declare (P4-39b: a controlled vocabulary is only a control if something
                     enforces it).

Resolution for one run: `resolve(obs_mode, overrides)` returns the section dict every block reads, or None when
every section is at its v2 design (the pure v2 code path, bit-identical to the committed functions).  Tools that
measure an ARM pass `obs_overrides` explicitly rather than relying on the file (P4-19: pin the configuration you
measure); `FP_OBS_MODE=v2` in the environment forces the v2 designs for a whole process (the path-hash fixture).

Keys (each a dict with value + provenance {label, source, date, interval, n, status, ...}):
  multiple, eps, dividend, analyst, sentiment, volume, audit_bounds
"""
from __future__ import annotations

import copy
import json
import os
from typing import Dict, Optional

PARAM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "params")
OBSERVABLES_PATH = os.path.join(PARAM_DIR, "observables.json")
REQUIRED = ("multiple", "eps", "dividend", "analyst", "sentiment", "volume", "audit_bounds")
SECTIONS = ("multiple", "eps", "dividend", "analyst", "sentiment", "volume")

# The v2 DESIGN values, in force until Phase 5 is applied (envs/v2/observables.py's historical constants).  These
# are exactly the constants E5.1-E5.6 replace, kept here so the "before" column of the report is code, not prose.
V2: Dict[str, Dict] = {
    "multiple": {"design": "v2", "k_range": [14.0, 22.0]},
    "eps": {"design": "v2", "noise_sd": 0.10, "lag_range": [25, 35], "pe_cap": 200.0},
    "dividend": {"design": "v2", "payout": 0.35, "sticky": 0.7, "field": "shown"},
    "analyst": {"design": "v2", "sd": 0.15, "rho": 0.95, "update_days": 5, "field": "shown"},
    "sentiment": {"design": "v2"},
    "volume": {"design": "v2"},
}


def load(path: Optional[str] = None) -> Optional[Dict]:
    path = path or OBSERVABLES_PATH
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    for k in REQUIRED:
        if k not in d or "value" not in d[k] or "label" not in d[k] or "source" not in d[k]:
            raise RuntimeError(
                f"{path} is malformed: key {k!r} must carry value / label / source / date / interval / n "
                f"(PREREG_PHASE_5.md section 11 and PHASE_5_REPORT.md). No entry may ship with a null interval.")
        if d[k].get("interval", "missing") is None:
            raise RuntimeError(f"{path}: key {k!r} ships with \"interval\": null, which PREREG_PHASE_5.md forbids. "
                               f"State the interval or say why the entry has none.")
        for f in ("date", "n"):
            if f not in d[k]:
                raise RuntimeError(f"{path}: key {k!r} is missing {f!r}")
    declared = set(d.get("_status_key", {}))
    if not declared:
        raise RuntimeError(f"{path} declares no _status_key; every entry's status must be a declared term (P4-39b)")
    undeclared = {k: v["status"] for k, v in d.items()
                  if isinstance(v, dict) and "status" in v and v["status"] not in declared}
    if undeclared:
        raise RuntimeError(
            f"{path}: these entries carry a status that _status_key does not declare: {undeclared}. Declared terms "
            f"are {sorted(declared)}. Add the term to _status_key with its meaning, or use an existing one.")
    missing_status = [k for k in REQUIRED if "status" not in d[k]]
    if missing_status:
        raise RuntimeError(f"{path}: entries without a status: {missing_status}")
    return d


OBSERVABLES = load()
PRESENT: bool = OBSERVABLES is not None


def _deep_merge(base: Dict, over: Optional[Dict]) -> Dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def in_force() -> Dict[str, Dict]:
    """The section dicts the file puts in force (v2 defaults where the file is absent)."""
    base = copy.deepcopy(V2)
    if PRESENT:
        for s in SECTIONS:
            base[s] = _deep_merge(base[s], OBSERVABLES[s]["value"])
    return base


def resolve(obs_mode: Optional[str] = None, overrides: Optional[Dict] = None) -> Optional[Dict[str, Dict]]:
    """Section dicts for one run, or None for the pure v2 path.

    obs_mode: None -> the file (with `overrides` merged on top); "v2" -> every section at its v2 design regardless
    of the file (the freeze check).  FP_OBS_MODE=v2 in the environment has the same effect as obs_mode="v2"."""
    mode = obs_mode or os.environ.get("FP_OBS_MODE") or None
    if mode == "v2":
        return None
    if mode not in (None, "v21", "file"):
        raise ValueError(f"obs_mode must be None, 'v21'/'file' or 'v2', got {mode!r}")
    p = _deep_merge(in_force(), overrides)
    if all(p[s].get("design", "v2") == "v2" for s in SECTIONS):
        return None
    return p


def provenance(key: str) -> Dict:
    """The full provenance block for a key, for the report and the tests."""
    if not PRESENT or key not in OBSERVABLES:
        return {}
    return {k: v for k, v in OBSERVABLES[key].items() if k != "value"}


def summary() -> str:
    p = in_force()
    return " ".join(f"{s}={p[s].get('design', 'v2')}" + (f"/{p[s]['field']}" if "field" in p[s] else "") for s in SECTIONS)


# the P/E cap in force (E5.2: the FIT P99; v2: 200), used by the audit-side encoding of an "n/m" day
PE_CAP: float = float(in_force()["eps"].get("pe_cap", 200.0))
DIVIDEND_FIELD: str = str(in_force()["dividend"].get("field", "shown"))
ANALYST_FIELD: str = str(in_force()["analyst"].get("field", "shown"))
AUDIT_BOUNDS: Dict = dict(OBSERVABLES["audit_bounds"]["value"]) if PRESENT else {}


def _derived_audit_bounds(bounds: Dict) -> Dict:
    """v2.1 Phase 6 (the `audit_bounds` entry names Phase 6 as its owner): when evaluation/params/phase6_criteria.json
    carries the derived gates, the PROVISIONAL numbers are replaced by them and the provenance is recorded in the dict --
    `no_field_deterministic_R2` by the centred L2 all-rows margin (a group's add-one over the level-free control is the
    same construction as FULL - BASE; the uncentred registered margin is negative, PREREG_PHASE_6_ADDENDUM.md section 1,
    and is carried beside), `l2b_margin_phase6_owned` by the derived L2b margin.  Without the file, or before the
    gates are written, the PROVISIONAL values stand and `AUDIT_BOUNDS["status"]` says so."""
    out = dict(bounds)
    out["status"] = "PROVISIONAL"
    try:
        from evaluation import criteria as CR
    except Exception:                                 # evaluation/ absent (a stripped deployment): the file's values stand
        return out
    if not CR.PRESENT:
        return out
    try:
        g = CR.gate("l2_all")["value"]
        out["no_field_deterministic_R2"] = float(g["centred_margin"])
        out["no_field_deterministic_R2_registered_uncentred"] = float(g["margin"])
        out["status"] = "DERIVED"
        out["source"] = "evaluation/params/phase6_criteria.json gates.l2_all (tools/phase6/e6_criteria_extra.py --stages gates)"
    except CR.CriteriaError:
        pass
    try:
        out["l2b_margin_phase6_owned"] = float(CR.gate("l2b")["value"]["margin"])
        out["status"] = "DERIVED"
    except CR.CriteriaError:
        pass
    return out


AUDIT_BOUNDS = _derived_audit_bounds(AUDIT_BOUNDS)
