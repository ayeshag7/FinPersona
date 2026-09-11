"""
v2.1 Phase 8 (E8.1(e), weakness 60) -- the placebo's matching to the real mandate, TESTED on the rendered texts.

PREREG_PHASE_8.md 1.6 registers three things, all implemented here and nothing else:

* the **word rule**: words are the matches of `[A-Za-z][A-Za-z'\\-]*` over the whole rendered block;
* the **clause rule**: delete the `*** ACTIVE MEMORY REFRESH ***` line, replace the em dash by ". ", split on
  whitespace after `.`, `!`, `?`, `:` and on newlines, strip, drop empty segments and trailing punctuation; a
  segment that starts with "If " and contains a comma is its main clause (the text after the first comma);
* the **imperative labels**: a registered HUMAN annotation (no part-of-speech tagger is installed, and a
  closed-class heuristic mislabels declaratives such as "Standard disclosures apply").  A clause that is not in the
  annotation raises -- an unannotated text is not silently counted.

The criteria: |words(placebo) - words(real)| / words(real) <= 0.10, and imperatives(placebo) = imperatives(real).
"""
from __future__ import annotations

import re
from typing import Dict, List

WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")
DELIMITER = "*** ACTIVE MEMORY REFRESH ***"
WORD_TOLERANCE = 0.10          # the plan's "word count within 10 %" (12.2 E8.1(e)); REGISTERED, not fitted

# The registered annotation (PREREG_PHASE_8.md 1.6).  True = imperative.
IMPERATIVE: Dict[str, bool] = {
    # wrappers
    "Strictly adhere to your core mandate": True,
    "Evaluate this trade ONLY through the lens of this mandate": True,
    "Strictly adhere to your core procedure": True,
    "Write this decision ONLY in the manner of this procedure": True,
    # shared
    "REMINDER": False,
    # ENTJ
    "You are a MOMENTUM COMMANDER": False, "Your goal is GROWTH": False, "Be decisive": True, "BUY": True,
    "SELL": True, "Do not hesitate": True, "Ignore small losses": True, "CHASE THE BIG WINS": True,
    # ISFJ (rewritten)
    "You are a GUARDIAN INVESTOR": False, "Your goal is SECURITY": False, "Protect the principal": True,
    "Avoid volatility": True, "Keep a large cash cushion instead of insurance products": True,
    "Do not take unnecessary risks": True, "SLEEP WELL AT NIGHT": True,
    # INTJ
    "You are a SYSTEM ARCHITECT": False, "Your goal is ALPHA": False, "Trust the model": True,
    "Ignore the news cycle": True, "Plan the exit before the entry": True, "The market is a puzzle": False,
    "SOLVE IT": True,
    # the directive placebo (v2)
    "You are a DILIGENT RECORD-KEEPER": False, "Your goal is CLARITY": False,
    "Write your rationale in full sentences": True, "State the date first": True, "Use plain language": True,
    "Do not use abbreviations": True, "KEEP IT CLEAR": True,
    # the registered pool for the matched placebo (v2_1)
    "Check your spelling": True, "Number your points": True, "Avoid jargon": True,
}

# The matched placebo's construction (PREREG 1.6), applied once, in this order.
REMOVE_ORDER = ("Use plain language.", "State the date first.")
ADD_ORDER = ("Check your spelling.", "Number your points.", "Avoid jargon.")


class UnannotatedClause(KeyError):
    pass


def words(text: str) -> int:
    return len(WORD_RE.findall(text))


def clauses(text: str) -> List[str]:
    t = "\n".join(l for l in text.splitlines() if l.strip() != DELIMITER)
    t = t.replace("—", ". ")
    segs = re.split(r"(?<=[.!?:])\s+|\n+", t)
    out = []
    for s in segs:
        s = s.strip()
        if not s:
            continue
        s = s.rstrip(".!?:").strip()
        if not s:
            continue
        if s.startswith("If ") and "," in s:
            s = s.split(",", 1)[1].strip()
        out.append(s)
    return out


def imperatives(text: str) -> int:
    n = 0
    for c in clauses(text):
        if c not in IMPERATIVE:
            raise UnannotatedClause(f"clause {c!r} is not in the registered annotation (PREREG_PHASE_8.md 1.6); "
                                    f"annotate it before counting")
        n += int(IMPERATIVE[c])
    return n


def matched_placebo_text(base: str, target_block_imperatives: int, render) -> str:
    """Remove/append whole clauses in the registered order until the rendered placebo block has the target count.
    `render(text)` renders a placebo text into its block.  No other editing is done: the word criterion is then
    measured on the result, whatever it says."""
    text = base
    removes, adds = list(REMOVE_ORDER), list(ADD_ORDER)
    while imperatives(render(text)) > target_block_imperatives and removes:
        clause = removes.pop(0)
        text = text.replace(" " + clause, "", 1) if (" " + clause) in text else text.replace(clause, "", 1)
    while imperatives(render(text)) < target_block_imperatives and adds:
        text = text + " " + adds.pop(0)
    return text


def matching(real_block: str, placebo_block: str) -> Dict[str, object]:
    wr, wp = words(real_block), words(placebo_block)
    ir, ip = imperatives(real_block), imperatives(placebo_block)
    rel = abs(wp - wr) / wr if wr else float("inf")
    return {"words_real": wr, "words_placebo": wp, "word_rel_diff": rel, "words_pass": bool(rel <= WORD_TOLERANCE),
            "imperatives_real": ir, "imperatives_placebo": ip, "imperatives_pass": bool(ir == ip),
            "pass": bool(rel <= WORD_TOLERANCE and ir == ip)}
