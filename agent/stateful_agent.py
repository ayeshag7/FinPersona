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
  summary   : running summary (rewritten by the same model every `summary_every` = 10 steps,
              <= 120 words) + the last `summary_raw_turns` = 5 raw turns; the summariser call is
              counted (Summary_Calls) and is the confound this arm introduces relative to 'rolling'.
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
    def __init__(self, *args, context_mode: str = "rolling", window: int = 20, token_budget: int = 60000,
                 summary_every: int = 10, summary_raw_turns: int = 5, **kw):
        kw.setdefault("mandate_in_system", True)      # Path B: mandate present at t = 0 in every stateful arm
        super().__init__(*args, **kw)
        if context_mode not in ("rolling", "full", "summary"):
            raise ValueError("context_mode must be 'rolling', 'full' or 'summary'")
        self.context_mode, self.window, self.token_budget = context_mode, int(window), int(token_budget)
        self.summary_every, self.summary_raw_turns = int(summary_every), int(summary_raw_turns)
        self.summary_text = ""                         # running summary (summary mode)
        self.summary_calls = 0
        self.summary_mentions_mandate = False
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
        if self.context_mode == "summary":
            return self.history[-self.summary_raw_turns:]
        # full: drop oldest until under budget
        kept = list(self.history)
        while kept and sum(_approx_tokens(h["human"]) + _approx_tokens(h["ai"]) for h in kept) > self.token_budget:
            kept.pop(0)
        return kept

    def build_messages(self, market_state: Dict[str, Any], portfolio_state: Dict[str, float]) -> List:
        human_now = self.rendered_human_message(market_state, portfolio_state)
        msgs = [SystemMessage(content=self.full_system_prompt)]
        if self.context_mode == "summary" and self.summary_text:
            msgs.append(HumanMessage(content="SUMMARY OF YOUR EARLIER STEPS (written by you):\n" + self.summary_text))
            msgs.append(AIMessage(content="Noted."))
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
                self.maybe_summarise()
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
        self.maybe_summarise()
        return out

    SUMMARY_PROMPT = ("Summarise the trader's last {k} trading steps in at most 120 words: what they held, what they did, "
                      "and the reasons they gave. Plain text only. Previous summary (may be empty):\n{prev}\n\nRecent steps:\n{steps}")
    SUMMARY_SYSTEM = ("You are a neutral note-taker. You compress a trading log faithfully; you do not add advice, "
                      "goals or instructions of your own.")   # methods review: the summariser must not be a re-injection channel
    MANDATE_WORDS = ("mandate", "goal is", "guardian", "commander", "architect", "security", "growth", "alpha",
                     "cash cushion", "protect the principal", "momentum", "reminder")

    def maybe_summarise(self):
        """Summary mode: every `summary_every` steps, one extra call rewrites the running summary
        (the summariser is the same model; cost is logged via summary_calls)."""
        if self.context_mode != "summary" or len(self.history) == 0 or len(self.history) % self.summary_every != 0:
            return
        recent = self.history[-self.summary_every:]
        steps = "\n".join(f"- step {i+1}: decided {h['ai'][:160]}" for i, h in enumerate(recent))
        prompt = self.SUMMARY_PROMPT.format(k=self.summary_every, prev=self.summary_text or "(none)", steps=steps)
        try:
            resp = self.llm.invoke([SystemMessage(content=self.SUMMARY_SYSTEM), HumanMessage(content=prompt)])
            self.summary_text = (resp.content if hasattr(resp, "content") else str(resp))[:1200]
            self.summary_calls += 1
            low = self.summary_text.lower()
            self.summary_mentions_mandate = any(w in low for w in self.MANDATE_WORDS)
        except Exception:
            pass

    def context_log(self) -> Dict[str, Any]:
        return {"Context_Mode": self.context_mode, "Context_Tokens": self.last_context_tokens,
                "Mandate_Offset_Tokens": self.last_mandate_offset, "Context_Turns": self.last_n_turns,
                "Summary_Calls": self.summary_calls, "Summary_Mentions_Mandate": self.summary_mentions_mandate,
                "Summary_Text": self.summary_text if self.context_mode == "summary" else ""}

    def reset(self):
        self.history = []
