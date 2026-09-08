"""
v2.1 Phase 6 -- the loud loader of the checklist criteria and the derived audit gates
(`evaluation/params/phase6_criteria.json`).

Modelled on `envs/v2/observables_params.py`: the file is the single source of every criterion in force; the
loader raises on a missing block, an undeclared status, a missing date, n or interval, and never substitutes a
default silently.  `PRESENT` is False when the file is absent (the v2 criteria in `evaluation/stylized_facts.py`
then remain the only ones, unchanged), so that every consumer is a switch with the v2 behaviour behind it.

Blocks:
  criterion_B, criterion_C   REG-14's two derived criterion forms (D0, the share rule)
  crash_window_rule          the DESIGN definition of a real crash window (the reference of items 8 and 20)
  reference                  P10/P50/P90 with n per statistic: overall, crash windows, per sub-period (FIT, E6.1)
  items                      which statistics each checklist item is judged on, and on which population
  gates                      (E6.6 / E6.7, written when the nulls have run) the derived L2 / L2b margins with the
                             null percentiles and the sampling half-widths they are built from; and E6.5's floor

    from evaluation import criteria as CR
    CR.PRESENT; CR.reference("kurtosis", "all")["p10"]; CR.D0; CR.gate("l2b")["margin"]
"""
from __future__ import annotations

import json
import os
from typing import Dict, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRITERIA_PATH = os.path.join(ROOT, "evaluation", "params", "phase6_criteria.json")

REQUIRED = ("criterion_B", "criterion_C", "crash_window_rule", "reference", "items")
PROVENANCE_FIELDS = ("value", "status", "label", "source", "date", "interval", "n")


class CriteriaError(RuntimeError):
    pass


def _check(doc: Dict, path: str) -> None:
    if "_status_key" not in doc or not isinstance(doc["_status_key"], dict) or not doc["_status_key"]:
        raise CriteriaError(f"{path}: no _status_key vocabulary")
    declared = set(doc["_status_key"])
    for key in REQUIRED:
        if key not in doc:
            raise CriteriaError(f"{path}: missing block '{key}'")
    for key, blk in doc.items():
        if key.startswith("_") or key in ("items", "not_in_reference"):
            continue
        if not isinstance(blk, dict):
            raise CriteriaError(f"{path}: block '{key}' is not an object")
        if key == "gates":
            for g, gb in blk.items():
                for f in PROVENANCE_FIELDS:
                    if f not in gb:
                        raise CriteriaError(f"{path}: gates.{g} is missing '{f}'")
                if gb["status"] not in declared:
                    raise CriteriaError(f"{path}: gates.{g} has undeclared status '{gb['status']}'")
            continue
        for f in PROVENANCE_FIELDS:
            if f not in blk:
                raise CriteriaError(f"{path}: block '{key}' is missing '{f}'")
        if blk["status"] not in declared:
            raise CriteriaError(f"{path}: block '{key}' has undeclared status '{blk['status']}'")
        if blk["interval"] is None or blk["n"] is None or not blk["date"]:
            raise CriteriaError(f"{path}: block '{key}' ships a null interval, n or date")
    ref = doc["reference"]["value"]
    if not ref:
        raise CriteriaError(f"{path}: the reference block is empty (a table with no rows is not a result)")
    for st, blk in ref.items():
        if "all" not in blk or blk["all"].get("n", 0) <= 0:
            raise CriteriaError(f"{path}: reference.{st} has no overall percentiles with n > 0")


def load(path: str = CRITERIA_PATH) -> Dict:
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    _check(doc, path)
    return doc


PRESENT = os.path.exists(CRITERIA_PATH)
_DOC: Optional[Dict] = load() if PRESENT else None

D0 = _DOC["criterion_B"]["value"]["D0"] if _DOC else None
SHARE_P0 = _DOC["criterion_C"]["value"]["p0"] if _DOC else None
CRASH_MDD = _DOC["crash_window_rule"]["value"]["mdd_at_or_below"] if _DOC else None


def reference(statistic: str, scope: str = "all") -> Dict:
    """P10/P50/P90 with n; scope 'all', 'crash_windows', or a sub-period label."""
    if _DOC is None:
        raise CriteriaError("phase6_criteria.json is absent")
    blk = _DOC["reference"]["value"].get(statistic)
    if blk is None:
        raise CriteriaError(f"no reference for statistic '{statistic}'")
    if scope in ("all", "crash_windows"):
        return blk[scope]
    if scope in blk.get("by_sub_period", {}):
        return blk["by_sub_period"][scope]
    raise CriteriaError(f"no scope '{scope}' for statistic '{statistic}'")


def items() -> Dict:
    if _DOC is None:
        raise CriteriaError("phase6_criteria.json is absent")
    return _DOC["items"]


def gate(name: str) -> Dict:
    """A derived gate ('l2', 'l2_calm', 'l2b', 'l1_floor', ...): margin, the null percentile and half-width it is built from."""
    if _DOC is None:
        raise CriteriaError("phase6_criteria.json is absent")
    gates = _DOC.get("gates") or {}
    if name not in gates:
        raise CriteriaError(f"no derived gate '{name}' (the null it needs has not been written to the criteria file)")
    return gates[name]


def provenance(key: str) -> Dict:
    if _DOC is None:
        raise CriteriaError("phase6_criteria.json is absent")
    blk = _DOC.get(key) or (_DOC.get("gates") or {}).get(key)
    if blk is None:
        raise CriteriaError(f"no block '{key}'")
    return {f: blk.get(f) for f in PROVENANCE_FIELDS if f != "value"}
