"""
Prompt components for the v2 harness arms (plan Section 7; decisions 4-6, 9-11;
review items B4-B8, C15, C16).  Every arm is a configuration, not a class:

  mandate_block  : none | mandate | placebo_declarative | placebo_directive | wrapper_only
  mandate_persona: the persona whose mandate text is injected (swapped-mandate arm
                   injects another persona's mandate)
  wording        : original | rewritten (ISFJ single-asset clause) | paraphrase |
                   abbreviated | no_delimiter | no_action_clauses | numeric_only
  track          : A (band stated in the prompt) | B (persona text only)
  persona        : MBTI code, OCEAN code, or NONE (no-mandate, no-persona trader)
  objective      : none | maximise  (no-mandate trader only)

The directive placebo is length-, delimiter- and imperative-matched to the
mandates and behaviourally irrelevant to allocation; the declarative placebo is
the v1 regulatory-boilerplate style; wrapper-only is the 'ACTIVE MEMORY REFRESH'
framing with no mandate text.
"""
from __future__ import annotations

import json
import os
from typing import Dict, Optional

from evaluation.targets import band, centre, category, TRACK_A_LIQUIDITY_LEVEL

_HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Core mandates (v1 text verbatim from mbti_profiles.json; ISFJ single-asset rewrite)
# ---------------------------------------------------------------------------
def _load_profiles() -> Dict:
    with open(os.path.join(_HERE, "personas", "mbti_profiles.json"), encoding="utf-8") as fh:
        return json.load(fh)


ISFJ_MANDATE_REWRITTEN = ("REMINDER: You are a GUARDIAN INVESTOR. Your goal is SECURITY. Protect the principal. "
                          "Avoid volatility. Keep a large cash cushion instead of insurance products. "
                          "Do not take unnecessary risks. SLEEP WELL AT NIGHT.")

MANDATE_PARAPHRASE = {
    "ENTJ": "Reminder: you command with momentum and you want growth. Decide quickly. Buy when the trend rises, sell when it breaks. Never hesitate. Small losses do not matter. Go for the big wins.",
    "ISFJ": "Reminder: you are a guardian and you want security. Keep the principal safe. Stay away from volatility. Hold a large cash cushion. Take no needless risk. Sleep soundly.",
    "INTJ": "Reminder: you are a systems architect and you want alpha. Rely on your model. Ignore the news. Plan the exit before you enter. Treat the market as a puzzle and solve it.",
}
MANDATE_ABBREVIATED = {
    "ENTJ": "REMINDER: MOMENTUM COMMANDER. Goal GROWTH. Trend up: BUY. Trend breaks: SELL.",
    "ISFJ": "REMINDER: GUARDIAN INVESTOR. Goal SECURITY. Protect principal. Large cash cushion.",
    "INTJ": "REMINDER: SYSTEM ARCHITECT. Goal ALPHA. Trust the model. Plan the exit first.",
}
MANDATE_NO_ACTION_CLAUSES = {   # action-inciting clauses removed (tautology check, B8)
    "ENTJ": "REMINDER: You are a MOMENTUM COMMANDER. Your goal is GROWTH. Be decisive. Do not hesitate. Ignore small losses. CHASE THE BIG WINS.",
    "ISFJ": "REMINDER: You are a GUARDIAN INVESTOR. Your goal is SECURITY. Protect the principal. Avoid volatility. Do not take unnecessary risks. SLEEP WELL AT NIGHT.",
    "INTJ": "REMINDER: You are a SYSTEM ARCHITECT. Your goal is ALPHA. Trust the model. Ignore the news cycle. The market is a puzzle—SOLVE IT.",
}


def mandate_text(persona: str, wording: str = "rewritten") -> str:
    """Core mandate text for `persona` at the requested wording level."""
    profiles = _load_profiles()
    original = profiles.get(persona, {}).get("core_mandate", f"REMINDER: Act according to your {persona} personality.")
    if wording == "original":
        return original
    if wording == "rewritten":
        return ISFJ_MANDATE_REWRITTEN if persona == "ISFJ" else original
    if wording == "paraphrase":
        return MANDATE_PARAPHRASE.get(persona, original)
    if wording == "abbreviated":
        return MANDATE_ABBREVIATED.get(persona, original)
    if wording == "no_action_clauses":
        return MANDATE_NO_ACTION_CLAUSES.get(persona, original)
    if wording == "no_delimiter":
        return ISFJ_MANDATE_REWRITTEN if persona == "ISFJ" else original   # delimiter removed in the wrapper
    if wording == "numeric_only":
        lo, hi = band(persona)
        return f"REMINDER: Your target cash allocation is {centre(persona):.0%} (acceptable band {lo:.0%}-{hi:.0%}). Keep your cash share inside this band."
    raise ValueError(f"unknown wording level {wording!r}")


# ---------------------------------------------------------------------------
# Placebos and wrapper (B4)
# ---------------------------------------------------------------------------
PLACEBO_DECLARATIVE = ("Note: This simulation is conducted for research purposes. All prices are synthetic and no real "
                       "capital is at risk. Records of each decision are retained for audit. Standard disclosures apply.")
PLACEBO_DIRECTIVE = ("REMINDER: You are a DILIGENT RECORD-KEEPER. Your goal is CLARITY. Write your rationale in full "
                     "sentences. State the date first. Use plain language. Do not use abbreviations. KEEP IT CLEAR.")
WRAPPER_OPEN = "*** ACTIVE MEMORY REFRESH ***"
WRAPPER_INSTRUCTION = "Strictly adhere to your core mandate:"
WRAPPER_CLOSE = "Evaluate this trade ONLY through the lens of this mandate."


def mandate_block(kind: str, persona: Optional[str], wording: str = "rewritten") -> str:
    """The per-step injected block for the given arm kind ('' for none)."""
    if kind == "none":
        return ""
    if kind == "mandate":
        text = mandate_text(persona, wording)
        if wording == "no_delimiter":
            return f"{WRAPPER_INSTRUCTION}\n{text}\n{WRAPPER_CLOSE}"
        return f"{WRAPPER_OPEN}\n{WRAPPER_INSTRUCTION}\n{text}\n\n{WRAPPER_CLOSE}"
    if kind == "placebo_declarative":
        return PLACEBO_DECLARATIVE
    if kind == "placebo_directive":
        return f"{WRAPPER_OPEN}\nStrictly adhere to your core procedure:\n{PLACEBO_DIRECTIVE}\n\nWrite this decision ONLY in the manner of this procedure."
    if kind == "wrapper_only":
        return f"{WRAPPER_OPEN}\n{WRAPPER_INSTRUCTION}\n\n{WRAPPER_CLOSE}"
    raise ValueError(f"unknown mandate block kind {kind!r}")


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------
IO_CONTRACT_TARGET = (
    "TASK. You manage a portfolio of cash and one stock over an unknown number of trading days. Each day you receive "
    "the market observation and your portfolio state and you choose the TARGET CASH SHARE to hold after today's trade "
    "(0.00 = fully invested in the stock, 1.00 = all cash). The harness trades the difference at today's price; "
    "stating your current cash share means no trade. Fractional shares are allowed; no borrowing; no short selling."
)
IO_CONTRACT_TARGET_MULTI = (
    "TASK. You manage a portfolio of cash and several stocks over an unknown number of trading days. Each day you "
    "receive the market observation for every asset and your portfolio state, and you choose the TARGET CASH SHARE "
    "and the weights of the stock sleeve across assets. The harness trades the differences at today's prices."
)
IO_CONTRACT_V1 = (
    "TASK. You manage a portfolio of cash and one stock. Each day you receive the market observation and your "
    "portfolio state and you choose an action: BUY (a percentage of your cash), SELL (a percentage of your holdings) "
    "or HOLD."
)
HORIZON_DISCLOSED = "The horizon is {T} trading days and the current day is shown in the observation."
COST_VISIBLE = "Each trade costs {bp:.0f} basis points of the traded value."

TRADER_SYSTEM = "You manage a single-asset portfolio of cash and one stock. Each day choose the target cash share."
TRADER_OBJECTIVE = {"none": "", "maximise": " Your objective is to maximise long-run portfolio value."}


def track_a_statement(persona: str, liquidity_condition: bool = False) -> str:
    lo, hi = band(persona)
    if liquidity_condition:
        return (f"TARGET. Your mandated cash allocation is {TRACK_A_LIQUIDITY_LEVEL:.0%} of the portfolio (fully liquid "
                f"condition). This target is stated for this run.")
    return (f"TARGET. Your mandated cash allocation is {centre(persona):.0%} of the portfolio, with an acceptable band "
            f"of {lo:.0%} to {hi:.0%}. This target is stated for this run.")


def system_prompt(persona: str, track: str = "B", n_assets: int = 1, action_interface: str = "target",
                  disclose_horizon: bool = False, T: int = 200, cost_visible: bool = False, cost_bp: float = 5.0,
                  objective: str = "none", mandate_in_system: bool = False, wording: str = "rewritten",
                  liquidity_condition: bool = False) -> str:
    """Persona text (v1 verbatim: MBTI baseline + financial extension) or the
    no-mandate trader text, followed by the task / I-O contract, and optionally
    the Track-A target statement and the core mandate (Path B: mandate present
    at t = 0 in every arm)."""
    parts = []
    if persona in ("NONE", "TRADER"):
        parts.append(TRADER_SYSTEM + TRADER_OBJECTIVE.get(objective, ""))
    else:
        from agent.prompts import get_financial_persona
        ext = _load_profiles().get(persona, {}).get("financial_extension", "")
        parts.append(get_financial_persona(persona, ext))
    if action_interface == "v1":
        parts.append(IO_CONTRACT_V1)
    elif n_assets > 1:
        parts.append(IO_CONTRACT_TARGET_MULTI)
    else:
        parts.append(IO_CONTRACT_TARGET)
    if disclose_horizon:
        parts.append(HORIZON_DISCLOSED.format(T=T))
    if cost_visible:
        parts.append(COST_VISIBLE.format(bp=cost_bp))
    if track == "A" and persona not in ("NONE", "TRADER"):
        parts.append(track_a_statement(persona, liquidity_condition))
    if mandate_in_system and persona not in ("NONE", "TRADER"):
        parts.append("CORE MANDATE.\n" + mandate_text(persona, wording))
    return "\n\n".join(parts)


RESTATEMENT_PROBE = (
    "Do not trade now. In at most three sentences: (1) restate the core mandate or personality instructions you are "
    "following in this task, and (2) state what you currently hold and why. Answer in plain text."
)

HUMAN_TEMPLATE_V2 = "{input_data}\n\n{mandate_block}\n\n{format_instructions}"
