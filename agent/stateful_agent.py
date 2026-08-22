"""
Stateful arm (E5; plan Sections 6 and 11.1; Position plan Path B).

Context genuinely accumulates: at step t the model sees the system prompt, a
retained record of earlier steps (its own observations and decisions as prior
conversation turns) and the current observation.  The core mandate is present in
the SYSTEM prompt at t = 0 for every stateful arm (Path B requirement 2); the
stateful 'memory' arm additionally re-injects it at the end of the current turn.

Context design (DECISION_LOG, E5 decision): `context_mode`
  rolling   : the last `window` steps verbatim (default 20 steps ~ 12-18k tokens);
              mimics the forced-closure regime (When Attention Closes) -- the
              mandate's distance from the generation point grows until the window
              is full, then stays roughly constant.
  full      : every step up to `token_budget` tokens, oldest steps dropped first
              (distance keeps growing until the budget binds).
  summary   : (not implemented in this version) summarisation memory.
Per step the agent reports `context_tokens` (approximate, chars/4, plus the
provider's usage metadata when available) and `mandate_offset_tokens` = tokens
between the END of the mandate span in the system prompt and the generation
point, which is the covariate M1 needs.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser

from agent.v2_agent import V2Agent
from agent.schemas import TargetAllocation, TradeDecision
from agent import v2_prompts as P


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class StatefulV2Agent(V2Agent):
    def __init__(self, *args, context_mode: str = "rolling", window: int = 20, token_budget: int = 60000, **kw):
        kw.setdefault("mandate_in_system", True)      # Path B: mandate present at t = 0 in every stateful arm
        super().__init__(*args, **kw)
        if context_mode not in ("rolling", "full"):
            raise ValueError("context_mode must be 'rolling' or 'full'")
        self.context_mode, self.window, self.token_budget = context_mode, int(window), int(token_budget)
        self.history: List[Dict[str, str]] = []     # [{"human": ..., "ai": ...}]
        self.last_context_tokens = 0
        self.last_mandate_offset = 0
        self.last_n_turns = 0
        # where the mandate sits inside the system prompt (chars), for the offset covariate
        m = P.mandate_text(self.persona, self.wording) if self.persona not in ("NONE", "TRADER") else ""
        self._mandate_end_char = (self.full_system_prompt.find(m) + len(m)) if m and m in self.full_system_prompt else len(self.full_system_prompt)

    # ------------------------------------------------------------------ context
    def _retained(self) -> List[Dict[str, str]]:
        if self.context_mode == "rolling":
            return self.history[-self.window:]
        # full: drop oldest until under budget
        kept = list(self.history)
        while kept and sum(_approx_tokens(h["human"]) + _approx_tokens(h["ai"]) for h in kept) > self.token_budget:
            kept.pop(0)
        return kept

    def build_messages(self, market_state: Dict[str, Any], portfolio_state: Dict[str, float]) -> List:
        human_now = self.rendered_human_message(market_state, portfolio_state)
        msgs = [SystemMessage(content=self.full_system_prompt)]
        retained = self._retained()
        for h in retained:
            msgs.append(HumanMessage(content=h["human"]))
            msgs.append(AIMessage(content=h["ai"]))
        msgs.append(HumanMessage(content=human_now))
        total_chars = sum(len(m.content) for m in msgs)
        self.last_context_tokens = _approx_tokens(" ".join(m.content for m in msgs))
        self.last_mandate_offset = _approx_tokens("x" * (total_chars - self._mandate_end_char))
        self.last_n_turns = len(retained)
        return msgs

    # ------------------------------------------------------------------ decisions
    def decide(self, market_state: Dict[str, Any], portfolio_state: Dict[str, float]):
        msgs = self.build_messages(market_state, portfolio_state)
        last_error = None
        for attempt in range(3):
            try:
                resp = self.llm.invoke(msgs)
                text = resp.content if hasattr(resp, "content") else str(resp)
                out = self.parser.parse(text)
                self.last_parse_status = "ok" if attempt == 0 else f"ok_retry{attempt}"
                self.history.append({"human": msgs[-1].content, "ai": text if isinstance(text, str) else json.dumps(text)})
                usage = getattr(resp, "usage_metadata", None)
                if usage and isinstance(usage, dict) and usage.get("input_tokens"):
                    self.last_context_tokens = int(usage["input_tokens"])
                return out
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(1)
        self.last_parse_status = "fallback"
        if self.action_interface == "target":
            cur = float(portfolio_state.get("cash_share", 1.0))
            out = TargetAllocation(target_cash_share=min(max(cur, 0.0), 1.0), rationale=f"Error after 3 attempts: {last_error}")
        else:
            out = TradeDecision(action="HOLD", quantity=0.0, rationale=f"Error after 3 attempts: {last_error}")
        self.history.append({"human": msgs[-1].content, "ai": out.model_dump_json()})
        return out

    def context_log(self) -> Dict[str, Any]:
        return {"Context_Mode": self.context_mode, "Context_Tokens": self.last_context_tokens,
                "Mandate_Offset_Tokens": self.last_mandate_offset, "Context_Turns": self.last_n_turns}

    def reset(self):
        self.history = []
