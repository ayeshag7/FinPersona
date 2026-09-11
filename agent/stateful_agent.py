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

`harness="v2"` (default) is the code every published stateful run used.  Per step it reports `context_tokens`
(chars/4, overwritten by the provider's usage metadata when available) and `mandate_offset_tokens` = chars/4
between the END of the mandate span in the system prompt and the generation point.

`harness="v2_1"` (v2.1 Phase 8, E8.1; PREREG_PHASE_8.md 1.2-1.5; weakness 57) corrects four defects:
  (a) the offset is measured to the NEAREST copy the model can attend to -- the system copy, or in the memory arm
      the block re-injected into the current turn -- and both are logged;
  (b) retained history turns store the human message rendered WITHOUT the injected block (the block is rendered
      into the current turn only), so the static and memory arms' histories are byte-identical under the same
      replies and the two arms have matched token budgets;
  (c) a parse fallback is stored as "no valid answer", never as the fabricated decision;
  (d) tokens come from the provider's usage metadata when available, a tokenizer (tiktoken o200k_base) otherwise,
      chars/4 only if the tokenizer cannot load -- and the method reaches the log.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser

from agent.v2_agent import V2Agent
from agent.schemas import TargetAllocation, TradeDecision
from agent import v2_prompts as P


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


HARNESS_VERSIONS = ("v2", "v2_1")
FALLBACK_HISTORY_TEXT = "no valid answer"      # E8.1(c): what a fallback leaves in the history (plan 12.2)
TOKENIZER_NAME = "o200k_base"
_ENCODER: Any = None


def _encoder():
    global _ENCODER
    if _ENCODER is None:
        try:
            import tiktoken
            _ENCODER = tiktoken.get_encoding(TOKENIZER_NAME)
        except Exception:                            # noqa: BLE001 -- the fallback is labelled, never silent
            _ENCODER = False
    return _ENCODER or None


def count_tokens(text: str) -> Tuple[int, str]:
    """(count, method): the tokenizer when it loads, chars/4 as the labelled last resort; the empty string is 0."""
    if not text:
        return 0, (f"tokenizer:{TOKENIZER_NAME}" if _encoder() is not None else "chars4")
    enc = _encoder()
    if enc is not None:
        return len(enc.encode(text, disallowed_special=())), f"tokenizer:{TOKENIZER_NAME}"
    return _approx_tokens(text), "chars4"


class StatefulV2Agent(V2Agent):
    def __init__(self, *args, context_mode: str = "rolling", window: int = 20, token_budget: int = 60000,
                 summary_every: int = 10, summary_raw_turns: int = 5, harness: str = "v2", **kw):
        kw.setdefault("mandate_in_system", True)      # Path B: mandate present at t = 0 in every stateful arm
        super().__init__(*args, **kw)
        if context_mode not in ("rolling", "full", "summary"):
            raise ValueError("context_mode must be 'rolling', 'full' or 'summary'")
        if harness not in HARNESS_VERSIONS:
            raise ValueError(f"harness must be one of {HARNESS_VERSIONS}, got {harness!r}")
        self.harness = harness
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
        # v2_1 state (unused under v2)
        self._mandate_text = m
        self._system_has_copy = bool(m) and m in self.full_system_prompt
        self._injects_own_mandate = (self.mandate_block_kind == "mandate" and self.mandate_persona == self.persona
                                     and bool(self.core_mandate))
        self._human_for_history = ""
        self.last_offset_system: Optional[int] = None
        self.last_offset_injected: Optional[int] = None
        self.last_copies = 0
        self.last_context_tokens_tokenizer = 0
        self.last_token_method = ""
        self.last_offset_method = ""
        self.last_token_scale: Optional[float] = None
        self.fallback_turns = 0

    # ------------------------------------------------------------------ context
    def _retained(self) -> List[Dict[str, str]]:
        if self.context_mode == "rolling":
            return self.history[-self.window:]
        if self.context_mode == "summary":
            return self.history[-self.summary_raw_turns:]
        # full: drop oldest until under budget
        kept = list(self.history)
        if self.harness == "v2_1":                   # E8.1(d): the budget in the harness's own token count
            while kept and sum(h["ntok"] for h in kept) > self.token_budget:
                kept.pop(0)
            return kept
        while kept and sum(_approx_tokens(h["human"]) + _approx_tokens(h["ai"]) for h in kept) > self.token_budget:
            kept.pop(0)
        return kept

    def _human_without_block(self, market_state: Dict[str, Any], portfolio_state: Dict[str, float]) -> str:
        """E8.1(b): the human turn as retained history stores it -- rendered with an EMPTY mandate block."""
        if self.action_interface == "target":
            return P.HUMAN_TEMPLATE_V2.format(input_data=self.render_input(market_state, portfolio_state),
                                              mandate_block="", format_instructions=self.parser.get_format_instructions())
        return self.rendered_human_message(market_state, portfolio_state)

    def build_messages(self, market_state: Dict[str, Any], portfolio_state: Dict[str, float]) -> List:
        if self.harness == "v2_1":
            return self._build_messages_v2_1(market_state, portfolio_state)
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

    def _build_messages_v2_1(self, market_state: Dict[str, Any], portfolio_state: Dict[str, float]) -> List:
        human_now = self.rendered_human_message(market_state, portfolio_state)
        self._human_for_history = self._human_without_block(market_state, portfolio_state)
        msgs = [SystemMessage(content=self.full_system_prompt)]
        if self.context_mode == "summary" and self.summary_text:
            msgs.append(HumanMessage(content="SUMMARY OF YOUR EARLIER STEPS (written by you):\n" + self.summary_text))
            msgs.append(AIMessage(content="Noted."))
        retained = self._retained()
        for h in retained:
            msgs.append(HumanMessage(content=h["human"]))
            msgs.append(AIMessage(content=h["ai"]))
        msgs.append(HumanMessage(content=human_now))
        counts = [count_tokens(m.content) for m in msgs]
        method = counts[0][1]
        ntok = [c for c, _ in counts]
        # (a) the system copy: the rest of the system prompt after the copy, then every later message
        self.last_offset_system = (count_tokens(self.full_system_prompt[self._mandate_end_char:])[0] + sum(ntok[1:])
                                   if self._system_has_copy else None)
        # (a) the injected copy: the rest of the current turn after the rendered block
        self.last_offset_injected = None
        if self._injects_own_mandate:
            pos = human_now.rfind(self.core_mandate)
            if pos >= 0:
                self.last_offset_injected = count_tokens(human_now[pos + len(self.core_mandate):])[0]
        present = [o for o in (self.last_offset_system, self.last_offset_injected) if o is not None]
        self.last_mandate_offset = min(present) if present else None
        self.last_copies = sum(m.content.count(self._mandate_text) for m in msgs) if self._mandate_text else 0
        self.last_context_tokens_tokenizer = sum(ntok)
        self.last_context_tokens = sum(ntok)
        self.last_token_method = method
        self.last_offset_method = method
        self.last_token_scale = None
        self.last_n_turns = len(retained)
        return msgs

    def _provider_units(self, resp) -> None:
        """E8.1(d): the provider's count replaces the tokenizer's for the context, and scales the offsets into the
        provider's unit (the provider reports no span positions)."""
        usage = getattr(resp, "usage_metadata", None)
        if not (usage and isinstance(usage, dict) and usage.get("input_tokens")):
            return
        provider = int(usage["input_tokens"])
        self.last_context_tokens = provider
        self.last_token_method = "provider"
        if self.last_offset_method.startswith("tokenizer:") and self.last_context_tokens_tokenizer > 0:
            scale = provider / self.last_context_tokens_tokenizer
            self.last_token_scale = scale
            if self.last_offset_system is not None:
                self.last_offset_system = int(round(self.last_offset_system * scale))
            if self.last_offset_injected is not None:
                self.last_offset_injected = int(round(self.last_offset_injected * scale))
            present = [o for o in (self.last_offset_system, self.last_offset_injected) if o is not None]
            self.last_mandate_offset = min(present) if present else None
            self.last_offset_method = f"tokenizer:{TOKENIZER_NAME}*provider_scale"

    def _append_history_v2_1(self, ai_text: str) -> None:
        human = self._human_for_history
        self.history.append({"human": human, "ai": ai_text,
                             "ntok": count_tokens(human)[0] + count_tokens(ai_text)[0]})

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
                ai_text = text if isinstance(text, str) else json.dumps(text)
                if self.harness == "v2_1":
                    self._append_history_v2_1(ai_text)
                    self._provider_units(resp)
                else:
                    self.history.append({"human": msgs[-1].content, "ai": ai_text})
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
        if self.harness == "v2_1":
            self._append_history_v2_1(FALLBACK_HISTORY_TEXT)        # E8.1(c): never the fabricated decision
            self.fallback_turns += 1
        else:
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
        log = {"Context_Mode": self.context_mode, "Context_Tokens": self.last_context_tokens,
               "Mandate_Offset_Tokens": self.last_mandate_offset, "Context_Turns": self.last_n_turns,
               "Summary_Calls": self.summary_calls, "Summary_Mentions_Mandate": self.summary_mentions_mandate,
               "Summary_Text": self.summary_text if self.context_mode == "summary" else ""}
        if self.harness == "v2_1":
            log.update({"Harness_Version": "v2_1",
                        "Mandate_Offset_System": self.last_offset_system,
                        "Mandate_Offset_Injected": self.last_offset_injected,
                        "Mandate_Copies_In_Context": self.last_copies,
                        "Offset_Count_Method": self.last_offset_method,
                        "Token_Count_Method": self.last_token_method,
                        "Context_Tokens_Tokenizer": self.last_context_tokens_tokenizer,
                        "Token_Scale": self.last_token_scale,
                        "History_Fallback_Turns": self.fallback_turns})
        return log

    def reset(self):
        self.history = []
