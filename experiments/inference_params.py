"""
v2.1 Phase 8 -- the loud loader of the inference parameters (`experiments/params/inference.json`;
PREREG_PHASE_8.md 6).

The file carries every statistical choice the arm contrasts are made with -- D12's minimum effect, the sigma plug-in
rule, the pairing unit, the alpha rule, the power, the family definition, the multiplicity procedure, the temporal
null, the cluster bootstrap, the mixed-model formula, E8.5's design, the transfer rule, the main grid's sizing and the
cost gate -- each with
`value`, `status`, `label`, `source`, `date`, `interval`, `n` and a declared `_status_key`.  The loader raises on a
missing block, an undeclared status, or a null interval, n, date or source; it never substitutes a default.
`PRESENT` is False when the file is absent, in which case nothing in `tools/stats_v2.py`'s v2 functions reads it.

    from experiments import inference_params as IP
    IP.block("min_effect")["value"]
    IP.decision_rule(n_confirmatory_families)     # "bh_within" or "by_across", as the file says
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Dict, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INFERENCE_PATH = os.path.join(ROOT, "experiments", "params", "inference.json")

REQUIRED = ("min_effect", "sigma_plugin", "pairing_unit", "alpha_rule", "power", "family_definition",
            "multiplicity", "temporal_null", "cluster_bootstrap", "mixed_model", "variance_pilot_design",
            "transfer_rule", "main_grid_sizing", "cost_gate")
PROVENANCE_FIELDS = ("value", "status", "label", "source", "date", "interval", "n")


class InferenceParamsError(RuntimeError):
    pass


def _check(doc: Dict, path: str) -> None:
    if not isinstance(doc.get("_status_key"), dict) or not doc["_status_key"]:
        raise InferenceParamsError(f"{path}: no _status_key vocabulary")
    declared = set(doc["_status_key"])
    for key in REQUIRED:
        if key not in doc:
            raise InferenceParamsError(f"{path}: missing block '{key}'")
    for key, blk in doc.items():
        if key.startswith("_"):
            continue
        if not isinstance(blk, dict):
            raise InferenceParamsError(f"{path}: block '{key}' is not an object")
        for f in PROVENANCE_FIELDS:
            if f not in blk:
                raise InferenceParamsError(f"{path}: block '{key}' is missing '{f}'")
        if blk["status"] not in declared:
            raise InferenceParamsError(f"{path}: block '{key}' has undeclared status '{blk['status']}'")
        if blk["interval"] is None or blk["n"] is None or not blk["date"] or not blk["source"]:
            raise InferenceParamsError(f"{path}: block '{key}' ships a null interval, n, date or source")
    rule = doc["multiplicity"]["value"].get("decision_rule") if isinstance(doc["multiplicity"]["value"], dict) else None
    if not isinstance(rule, dict) or set(rule) != {"one_family", "several_families"}:
        raise InferenceParamsError(f"{path}: multiplicity.value.decision_rule must name the rule for one family and for "
                                   f"several families (PREREG_PHASE_8_ADDENDUM.md 5)")


def load(path: str = INFERENCE_PATH) -> Dict:
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    _check(doc, path)
    return doc


def file_sha256(path: str = INFERENCE_PATH) -> Optional[str]:
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


PRESENT = os.path.exists(INFERENCE_PATH)
_DOC: Optional[Dict] = load() if PRESENT else None
SHA256: Optional[str] = file_sha256() if PRESENT else None


def block(name: str) -> Dict:
    if _DOC is None:
        raise InferenceParamsError(f"{INFERENCE_PATH} is absent; the v2.1 inference functions have no rules to read")
    if name not in _DOC:
        raise InferenceParamsError(f"no block '{name}' in {INFERENCE_PATH}")
    return _DOC[name]


def decision_rule(n_confirmatory_families: int) -> str:
    """The multiplicity procedure a claim is decided by, as the file records it: on one confirmatory family the
    within-family procedure, on several the across-family one (the registered adoption rule's outcome)."""
    if n_confirmatory_families < 1:
        raise InferenceParamsError("a grid with no confirmatory family has no decision rule")
    rule = block("multiplicity")["value"]["decision_rule"]
    return rule["one_family"] if n_confirmatory_families == 1 else rule["several_families"]
