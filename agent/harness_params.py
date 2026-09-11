"""
v2.1 Phase 8 -- the loud loader of the harness constants (`agent/params/harness.json`; PREREG_PHASE_8.md 6;
weakness 34: the harness constants that lived only in code).

Modelled on `evaluation/scoring_params.py`: the file carries every constant with `value`, `status`, `label`,
`source`, `date`, `interval`, `n` and a declared `_status_key`; the loader raises on a missing block, an undeclared
status, or a null interval, n, date or source, and never substitutes a default.  `PRESENT` is False when the file
is absent.  The agent's constructor defaults are unchanged; `tests/test_v2_1_phase_8.py::test_harness_params_match_code`
asserts that the file and the code say the same thing, so neither can drift silently.

    from agent import harness_params as HP
    HP.block("token_budget")["value"]
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Dict, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARNESS_PATH = os.path.join(ROOT, "agent", "params", "harness.json")

REQUIRED = ("default_harness_version", "context_window_default", "context_window_levels", "token_budget",
            "summary_every", "summary_raw_turns", "summary_word_cap", "summary_char_truncation",
            "summary_step_truncation", "token_count_method", "mandate_offset_definition", "history_injected_block",
            "fallback_history_text", "placebo_matching", "decode_temperature", "parse_retries")
PROVENANCE_FIELDS = ("value", "status", "label", "source", "date", "interval", "n")


class HarnessParamsError(RuntimeError):
    pass


def _check(doc: Dict, path: str) -> None:
    if not isinstance(doc.get("_status_key"), dict) or not doc["_status_key"]:
        raise HarnessParamsError(f"{path}: no _status_key vocabulary")
    declared = set(doc["_status_key"])
    for key in REQUIRED:
        if key not in doc:
            raise HarnessParamsError(f"{path}: missing block '{key}'")
    for key, blk in doc.items():
        if key.startswith("_"):
            continue
        if not isinstance(blk, dict):
            raise HarnessParamsError(f"{path}: block '{key}' is not an object")
        for f in PROVENANCE_FIELDS:
            if f not in blk:
                raise HarnessParamsError(f"{path}: block '{key}' is missing '{f}'")
        if blk["status"] not in declared:
            raise HarnessParamsError(f"{path}: block '{key}' has undeclared status '{blk['status']}'")
        if blk["interval"] is None or blk["n"] is None or not blk["date"] or not blk["source"]:
            raise HarnessParamsError(f"{path}: block '{key}' ships a null interval, n, date or source")


def load(path: str = HARNESS_PATH) -> Dict:
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    _check(doc, path)
    return doc


def file_sha256(path: str = HARNESS_PATH) -> Optional[str]:
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


PRESENT = os.path.exists(HARNESS_PATH)
_DOC: Optional[Dict] = load() if PRESENT else None
SHA256: Optional[str] = file_sha256() if PRESENT else None


def block(name: str) -> Dict:
    if _DOC is None:
        raise HarnessParamsError(f"{HARNESS_PATH} is absent; the agent keeps its constructor defaults")
    if name not in _DOC:
        raise HarnessParamsError(f"no block '{name}' in {HARNESS_PATH}")
    return _DOC[name]
