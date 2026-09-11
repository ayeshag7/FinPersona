"""
v2.1 Phase 7 -- the loud loader of the scoring parameters (`evaluation/params/scoring.json`).

Modelled on `evaluation/criteria.py` (Phase 6) and `envs/v2/observables_params.py`: the file is the single source
of every scoring parameter in force; the loader raises on a missing block, an undeclared status, or a null
interval, n or date, and never substitutes a default silently.  `PRESENT` is False when the file is absent, in
which case every consumer keeps its v2 constant unchanged -- so the file is a switch with v2 behind it.

    from evaluation import scoring_params as SP
    SP.PRESENT
    SP.block("theta_cost")["value"]
    SP.thetas()                # the theta grid in force
    SP.theta_in_force()        # raises until D7 and D8 are recorded and the block is written

**theta_in_force is deliberately absent until D7 and D8 are recorded** (PREREG_PHASE_7.md 1.4).  Asking for it
before then raises `ScoringParamsError` rather than returning a default: a theta that nobody chose must not be able
to reach a table.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORING_PATH = os.path.join(ROOT, "evaluation", "params", "scoring.json")

# Every block that must be in the file for it to be usable at all.  `theta_in_force` is NOT here: it is written
# only when D7 and D8 are recorded, and `theta_in_force()` raises while it is missing.
REQUIRED = ("theta_grid", "theta_info", "theta_cost", "theta_var", "theta_rule", "half_width", "dead_band",
            "cost_tier", "band_convention", "decomposition", "window")
PROVENANCE_FIELDS = ("value", "status", "label", "source", "date", "interval", "n")


class ScoringParamsError(RuntimeError):
    pass


def _check(doc: Dict, path: str) -> None:
    if "_status_key" not in doc or not isinstance(doc["_status_key"], dict) or not doc["_status_key"]:
        raise ScoringParamsError(f"{path}: no _status_key vocabulary")
    declared = set(doc["_status_key"])
    for key in REQUIRED:
        if key not in doc:
            raise ScoringParamsError(f"{path}: missing block '{key}'")
    for key, blk in doc.items():
        if key.startswith("_"):
            continue
        if not isinstance(blk, dict):
            raise ScoringParamsError(f"{path}: block '{key}' is not an object")
        for f in PROVENANCE_FIELDS:
            if f not in blk:
                raise ScoringParamsError(f"{path}: block '{key}' is missing '{f}'")
        if blk["status"] not in declared:
            raise ScoringParamsError(f"{path}: block '{key}' has undeclared status '{blk['status']}'")
        if blk["interval"] is None or blk["n"] is None or not blk["date"] or not blk["source"]:
            raise ScoringParamsError(f"{path}: block '{key}' ships a null interval, n, date or source")
    if not doc["theta_grid"]["value"]:
        raise ScoringParamsError(f"{path}: the theta grid is empty (a grid with no values is not a grid)")


def load(path: str = SCORING_PATH) -> Dict:
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    _check(doc, path)
    return doc


def file_sha256(path: str = SCORING_PATH) -> Optional[str]:
    """The hash every tool records beside its numbers (P4-19: pin the configuration a tool measures)."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


PRESENT = os.path.exists(SCORING_PATH)
_DOC: Optional[Dict] = load() if PRESENT else None
SHA256: Optional[str] = file_sha256() if PRESENT else None


def _doc() -> Dict:
    if _DOC is None:
        raise ScoringParamsError(f"{SCORING_PATH} is absent; every consumer keeps its v2 constant")
    return _DOC


def block(name: str) -> Dict:
    d = _doc()
    if name not in d:
        raise ScoringParamsError(f"no block '{name}' in {SCORING_PATH}")
    return d[name]


def provenance(name: str) -> Dict:
    return {f: block(name).get(f) for f in PROVENANCE_FIELDS if f != "value"}


def thetas() -> List[float]:
    """The theta grid in force."""
    return [float(v) for v in block("theta_grid")["value"]]


def theta_in_force() -> Dict:
    """The theta (or co-primary thetas) actually in force.

    Raises while the block is absent -- which it is until D7 and D8 are recorded (PREREG 1.4).  The message names
    the decisions, so a caller that hits it learns why rather than getting a silent default.
    """
    d = _doc()
    if "theta_in_force" not in d:
        raise ScoringParamsError(
            "no 'theta_in_force' block in evaluation/params/scoring.json: the theta in force is written only after "
            "D7 (theta_info not reached on a population -> theta_cost alone primary) and D8 (the one-shot question, "
            "now theta-conditional) are recorded in DECISION_LOG.md. Until then read theta_info / theta_cost / "
            "theta_var and report at the grid.")
    return d["theta_in_force"]


def half_width(name: str = "value") -> float:
    return float(block("half_width")["value"])


def dead_band() -> float:
    return float(block("dead_band")["value"])


def cost_bp() -> float:
    return float(block("cost_tier")["value"])
