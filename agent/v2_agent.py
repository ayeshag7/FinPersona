"""
V2Agent: one configurable, stateless single-turn LLM agent for every harness arm
(plan Section 7; E3).  The arm is a configuration (see agent/v2_prompts.py and
experiments/arms_v2.py), not a subclass:

    V2Agent(persona="ISFJ", model_name="gemini-2.5-flash",
            mandate_block="mandate", mandate_persona=None, wording="rewritten",
            track="B", action_interface="target", n_assets=1, disclose_horizon=False,
            T=200, cost_visible=False, cost_bp=5.0, objective="none",
            mandate_in_system=False, temperature=0.2, liquidity_condition=False)

decide(market_state, portfolio_state) -> TargetAllocation (or TradeDecision for the
v1 interface); parse failures are retried 3x and then returned as a fallback with
parse_status="fallback" so the evaluation layer can exclude them (plan 8.5).
probe_restatement(...) is the forked off-transcript restatement probe (B7).
prompt_components() feeds simulation/provenance.py.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from agent.base import BaseAgent
from agent.llm_factory import make_llm
from agent.render import render_v2_input, render_static_input, HUMAN_TEMPLATE_STATIC
from agent.schemas import TargetAllocation, TradeDecision
from agent import v2_prompts as P


class V2Agent(BaseAgent):
    def __init__(self, persona: str = "ISFJ", model_name: str = "gemini-2.5-flash",
                 mandate_block: str = "none", mandate_persona: Optional[str] = None, wording: str = "rewritten",
                 track: str = "B", action_interface: str = "target", n_assets: int = 1,
                 disclose_horizon: bool = False, T: int = 200, cost_visible: bool = False, cost_bp: float = 5.0,
                 objective: str = "none", mandate_in_system: bool = False, temperature: float = 0.2,
                 liquidity_condition: bool = False, llm=None):
        super().__init__(persona)
        self.persona = persona
        self.model_name = model_name
        self.mandate_block_kind = mandate_block
        self.mandate_persona = mandate_persona or persona
        self.wording = wording
        self.track = track
        self.action_interface = action_interface
        self.n_assets = n_assets
        self.disclose_horizon, self.T = disclose_horizon, T
        self.cost_visible, self.cost_bp = cost_visible, cost_bp
        self.objective = objective
        self.mandate_in_system = mandate_in_system
        self.temperature = temperature
        self.liquidity_condition = liquidity_condition
        self.name = f"V2Agent-{persona}-{mandate_block}"
        self.last_parse_status = "ok"

        self.full_system_prompt = P.system_prompt(
            persona, track=track, n_assets=n_assets, action_interface=action_interface,
            disclose_horizon=disclose_horizon, T=T, cost_visible=cost_visible, cost_bp=cost_bp,
            objective=objective, mandate_in_system=mandate_in_system, wording=wording,
            liquidity_condition=liquidity_condition)
        self.core_mandate = P.mandate_block(mandate_block, self.mandate_persona, wording) if mandate_block != "none" else ""
        self.human_template = P.HUMAN_TEMPLATE_V2 if action_interface == "target" else HUMAN_TEMPLATE_STATIC
        self.parser = PydanticOutputParser(pydantic_object=TargetAllocation if action_interface == "target" else TradeDecision)
        self.llm = llm if llm is not None else make_llm(model_name, temperature)
        if action_interface == "target":
            tmpl = ChatPromptTemplate.from_messages([("system", "{persona}"), ("human", P.HUMAN_TEMPLATE_V2)])
            self.chain = tmpl.partial(persona=self.full_system_prompt,
                                      format_instructions=self.parser.get_format_instructions()) | self.llm | self.parser
        else:
            tmpl = ChatPromptTemplate.from_messages([("system", "{persona}"), ("human", HUMAN_TEMPLATE_STATIC)])
            self.chain = tmpl.partial(persona=self.full_system_prompt,
                                      format_instructions=self.parser.get_format_instructions()) | self.llm | self.parser
        probe_tmpl = ChatPromptTemplate.from_messages([("system", "{persona}"), ("human", "{input_data}\n\n{probe}")])
        self.probe_chain = probe_tmpl.partial(persona=self.full_system_prompt, probe=P.RESTATEMENT_PROBE) | self.llm | StrOutputParser()

    # ------------------------------------------------------------------ prompts
    def render_input(self, market_state: Dict[str, Any], portfolio_state: Dict[str, float]) -> str:
        if self.action_interface == "target":
            return render_v2_input(market_state, portfolio_state, cost_visible=self.cost_visible, cost_bp=self.cost_bp)
        # v1 bridge cell: the v1 observation block (needs the v1 keys; the runner maps SMA50 -> SMA60)
        ms = dict(market_state)
        ms.setdefault("SMA60", ms.get("SMA50"))
        return render_static_input(ms, portfolio_state)

    def prompt_components(self) -> Dict[str, str]:
        return {"system": self.full_system_prompt, "human": self.human_template,
                "format_instructions": self.parser.get_format_instructions(), "mandate": self.core_mandate}

    def rendered_human_message(self, market_state, portfolio_state) -> str:
        """Exact human message text (for logging / publication)."""
        inp = self.render_input(market_state, portfolio_state)
        if self.action_interface == "target":
            return P.HUMAN_TEMPLATE_V2.format(input_data=inp, mandate_block=self.core_mandate,
                                              format_instructions=self.parser.get_format_instructions())
        return HUMAN_TEMPLATE_STATIC.format(input_data=inp, format_instructions=self.parser.get_format_instructions())

    # ------------------------------------------------------------------ decisions
    def decide(self, market_state: Dict[str, Any], portfolio_state: Dict[str, float]):
        inp = self.render_input(market_state, portfolio_state)
        payload = {"input_data": inp}
        if self.action_interface == "target":
            payload["mandate_block"] = self.core_mandate
        last_error = None
        for attempt in range(3):
            try:
                out = self.chain.invoke(payload)
                self.last_parse_status = "ok" if attempt == 0 else f"ok_retry{attempt}"
                return out
            except Exception as exc:  # provider or parse error
                last_error = exc
                if attempt < 2:
                    time.sleep(1)
        self.last_parse_status = "fallback"
        if self.action_interface == "target":
            cur = float(portfolio_state.get("cash_share", 1.0))
            return TargetAllocation(target_cash_share=min(max(cur, 0.0), 1.0),
                                    rationale=f"Error after 3 attempts: {last_error}")
        return TradeDecision(action="HOLD", quantity=0.0, rationale=f"Error after 3 attempts: {last_error}")

    def probe_restatement(self, market_state: Dict[str, Any], portfolio_state: Dict[str, float]) -> str:
        """Forked, off-transcript restatement probe (B7). Never enters the decision context."""
        try:
            return self.probe_chain.invoke({"input_data": self.render_input(market_state, portfolio_state)})
        except Exception as exc:
            return f"PROBE_ERROR: {exc}"

    def reset(self):
        pass
