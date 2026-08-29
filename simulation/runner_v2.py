"""
Simulation runner v2 (plan Sections 2.1 blocks 8-10, 7, 8; E3).

One function, `run_simulation_v2(cfg)`, drives: v2 environment -> V2Agent (any arm)
-> PortfolioV2 (target-share or v1 interface, start design, cost tier, execution
rule) -> one CSV row per day with the referee fields, the harness factors and the
provenance hashes (IO_CONTRACT.md section 2.5).  Optional forked restatement
probe every `probe_every` days (off-transcript; logged to a separate column).
Parse fallbacks are flagged (`Parse_Status`) rather than hidden.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional

import pandas as pd

from envs.synthetic_market import SyntheticMarketEnv
from evaluation.targets import start_cash_share, band, centre, category
from simulation.portfolio_v2 import PortfolioV2
from simulation.provenance import env_provenance, agent_provenance


@dataclass
class RunConfig:
    # cell identity
    model_name: str = "gemini-2.5-flash"
    persona: str = "ISFJ"                 # ISFJ | INTJ | ENTJ | O1_conservative | ... | NONE (trader)
    arm: str = "static"                   # registry key (experiments/arms_v2.py)
    scenario: str = "flat"
    seed: int = 42
    T: int = 200
    crash_discount: float = 0.70
    ordering: str = "setup_first"
    n_assets: int = 1
    decode_replicate: int = 0
    # arm parameters (filled from the registry)
    mandate_block: str = "none"
    mandate_persona: Optional[str] = None
    wording: str = "rewritten"
    track: str = "B"
    objective: str = "none"
    mandate_in_system: bool = False
    liquidity_condition: bool = False
    # environment / harness factors
    start_design: str = "target"          # target | common | v1
    action_interface: str = "target"      # target | v1
    cost_bp: float = 5.0
    cost_visible: bool = False
    execution: str = "same_day"           # same_day | next_open
    disclose_horizon: bool = False
    field_order: str = "canonical"
    b_pred: Optional[float] = None
    engine: str = "fw_fallback_hl150"     # the engine that runs (envs.v2.mispricing.ENGINE_DEFAULT)
    temperature: float = 0.2
    probe_every: int = 0                  # 0 = no restatement probe
    context_mode: str = "stateless"       # stateless | rolling | full | summary   (E5 stateful arm)
    context_window: int = 20              # rolling: steps retained
    context_token_budget: int = 60000     # full: token budget
    initial_value: float = 10000.0
    output_dir: str = "results_v2"
    env_config: Dict[str, Any] = field(default_factory=dict)
    agent_llm: Any = None                 # injected LLM (tests)

    def run_id(self) -> str:
        d = f"_d{self.crash_discount}" if self.scenario == "crash" else ""
        na = f"_N{self.n_assets}" if self.n_assets > 1 else ""
        return (f"{self.model_name.replace('/', '_')}__{self.persona}__{self.arm}__{self.scenario}{d}{na}"
                f"__seed{self.seed}__rep{self.decode_replicate}")


def run_simulation_v2(cfg: RunConfig, verbose: bool = True) -> Optional[pd.DataFrame]:
    from agent.v2_agent import V2Agent
    from agent.stateful_agent import StatefulV2Agent

    env = SyntheticMarketEnv(cfg.scenario, cfg.T, cfg.seed, crash_discount=cfg.crash_discount,
                             ordering=cfg.ordering, n_assets=cfg.n_assets, engine=cfg.engine,
                             b_pred=cfg.b_pred, disclose_horizon=cfg.disclose_horizon,
                             field_order=cfg.field_order, config=cfg.env_config or None)
    agent_kw = dict(persona=cfg.persona, model_name=cfg.model_name, mandate_block=cfg.mandate_block,
                    mandate_persona=cfg.mandate_persona, wording=cfg.wording, track=cfg.track,
                    action_interface=cfg.action_interface, n_assets=cfg.n_assets,
                    disclose_horizon=cfg.disclose_horizon, T=cfg.T, cost_visible=cfg.cost_visible,
                    cost_bp=cfg.cost_bp, objective=cfg.objective, mandate_in_system=cfg.mandate_in_system,
                    temperature=cfg.temperature, liquidity_condition=cfg.liquidity_condition, llm=cfg.agent_llm)
    if cfg.context_mode == "stateless":
        agent = V2Agent(**agent_kw)
    else:
        agent = StatefulV2Agent(context_mode=cfg.context_mode, window=cfg.context_window,
                                token_budget=cfg.context_token_budget, **agent_kw)
    persona_for_start = cfg.persona if cfg.persona not in ("NONE", "TRADER") else "TRADER"
    c0 = 0.5 if persona_for_start == "TRADER" and cfg.start_design != "v1" else start_cash_share(persona_for_start, cfg.start_design)
    obs = env.reset()
    p0 = [a["price"] for a in obs["assets"]] if cfg.n_assets > 1 else obs["price"]
    port = PortfolioV2(cfg.initial_value, c0, p0, n_assets=cfg.n_assets)
    prov = {**env_provenance(env), **agent_provenance(agent)}
    meta = env.get_metadata()
    # the no-persona trader is band-free, (0, 1), as in evaluation/metrics_v2.py and baselines_v2.py (v2.1 Phase 0, item 73;
    # the runner previously logged (0.4, 0.6))
    lo, hi = band(persona_for_start) if persona_for_start != "TRADER" else (0.0, 1.0)
    run_id = cfg.run_id()
    if verbose:
        print(f"[RunnerV2] {run_id}  C0={c0:.2f}  attempts={env.attempts}  {prov['Prompt_Hash']}")

    rows = []
    for t in range(cfg.T):
        if obs is None:
            break
        price = obs["price"]
        if cfg.execution == "next_open":
            port.settle_pending([a["price"] for a in obs["assets"]] if cfg.n_assets > 1 else price, t + 1)
        state = port.get_state([a["price"] for a in obs["assets"]] if cfg.n_assets > 1 else price)
        decision = agent.decide(obs, state)
        parse_status = agent.last_parse_status
        prices = [a["price"] for a in obs["assets"]] if cfg.n_assets > 1 else price
        if cfg.action_interface == "target":
            tw = getattr(decision, "target_weights", None)
            if cfg.n_assets > 1 and tw is not None:
                tw = [max(float(w), 0.0) for w in tw][:cfg.n_assets]
                tw = tw + [0.0] * (cfg.n_assets - len(tw))
                ssum = sum(tw); tw = [w / ssum for w in tw] if ssum > 0 else None
            rec = port.retarget(decision.target_cash_share, prices, t + 1, cost_bp=cfg.cost_bp,
                                target_weights=tw, execution=cfg.execution)
            action_label, target, qty = rec["derived_action"], decision.target_cash_share, None
        else:
            rec = port.execute_v1_action(decision.action, decision.quantity, price, t + 1, cost_bp=cfg.cost_bp)
            action_label, target, qty = decision.action, None, decision.quantity
        probe = ""
        if cfg.probe_every and (t % cfg.probe_every == 0):
            probe = agent.probe_restatement(obs, state)
        gt = env.get_ground_truth()
        st = port.get_state(prices)
        row = {
            "Date": obs["date"], "Day": t + 1, "Model": cfg.model_name, "Persona": cfg.persona, "Arm": cfg.arm,
            "Scenario": cfg.scenario, "Seed": cfg.seed, "Crash_Discount": cfg.crash_discount, "Ordering": cfg.ordering,
            "Decode_Replicate": cfg.decode_replicate, "Track": cfg.track, "Mandate_Block": cfg.mandate_block,
            "Mandate_Persona": cfg.mandate_persona or cfg.persona, "Wording": cfg.wording,
            "Start_Design": cfg.start_design, "Start_Cash_Share": c0, "Action_Interface": cfg.action_interface,
            "Cost_bp": cfg.cost_bp, "Cost_Visible": cfg.cost_visible, "Execution": cfg.execution,
            "Disclose_Horizon": cfg.disclose_horizon, "Field_Order": cfg.field_order, "Temperature": cfg.temperature,
            "Phase": gt["phase"], "Macro_Phase": gt["macro_phase"], "Price": price,
            "Fundamental_Value": gt["fundamental_value"], "x": gt["x"],
            "Resolvable_0.03": bool(gt["resolvable_0.03"]), "Resolvable_0.05": bool(gt["resolvable_0.05"]),
            "Resolvable_0.08": bool(gt["resolvable_0.08"]),
            "Portfolio_Value": st["total_value"], "Cash": st["cash"], "Holdings_Value": st["holdings_value"],
            "Cash_Share": st["cash_share"], "Holdings_Qty": port.holdings_qty[0],
            "Target_Cash_Share": target, "Quantity_Percent": qty, "Action": action_label,
            "Traded_Value": rec["traded_value"], "Cost_Paid": rec["cost_paid"],
            "Band_Lo": lo, "Band_Hi": hi, "Band_Centre": centre(persona_for_start) if persona_for_start != "TRADER" else 0.5,
            "Rationale": decision.rationale, "Parse_Status": parse_status, "Restatement_Probe": probe,
            "Env_Attempts": env.attempts, "Event_Topped": env.event_meta.get("topped"),
            "Event_Top_Day": env.event_meta.get("top_day"), "Schedule_Setup_Len": env.schedule.setup_len,
        }
        for k in ("SMA20", "SMA50", "RSI14", "MACD", "MACD_signal", "volume", "volume_ratio", "news_sentiment",
                  "sentiment_MA5", "sentiment_change", "implied_volatility", "reported_PE", "dividend_yield",
                  "analyst_fair_value", "days_since_eps_announcement", "trend_strength", "trend_regime"):
            row["obs_" + k] = obs.get(k)
        if cfg.n_assets > 1:   # per-asset referee fields and realised weights (multi-asset extension)
            tv = st["total_value"]
            for i, a_gt in enumerate(gt["assets"]):
                row[f"price_asset{i}"] = a_gt["price"]; row[f"V_asset{i}"] = a_gt["fundamental_value"]
                row[f"x_asset{i}"] = a_gt["x"]
                row[f"weight_asset{i}"] = port.holdings_qty[i] * a_gt["price"] / tv if tv > 0 else 0.0
        if hasattr(agent, "context_log"):
            row.update(agent.context_log())
        else:
            row.update({"Context_Mode": "stateless", "Context_Tokens": None, "Mandate_Offset_Tokens": None, "Context_Turns": 0,
                        "Summary_Calls": 0, "Summary_Mentions_Mandate": False, "Summary_Text": ""})
        row.update(prov)
        rows.append(row)
        obs, done = env.step()
        if done:
            break

    df = pd.DataFrame(rows)
    if len(df) < cfg.T * 0.1:
        print(f"[RunnerV2] WARNING: only {len(df)}/{cfg.T} days logged; treating as failed run")
        return None
    out_dir = os.path.join(cfg.output_dir, cfg.model_name.replace("/", "_"), cfg.scenario, f"seed{cfg.seed}")
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(os.path.join(out_dir, f"{run_id}.csv"), index=False)
    with open(os.path.join(out_dir, f"{run_id}.meta.json"), "w", encoding="utf-8") as fh:
        json.dump({"run_config": {k: v for k, v in asdict(cfg).items() if k != "agent_llm"},
                   "env_metadata": meta, "provenance": prov,
                   "turnover": port.turnover_value / cfg.initial_value, "cost_paid_total": port.cost_paid_total,
                   "n_trades": len(port.trades),
                   "system_prompt": agent.full_system_prompt, "human_template": agent.human_template,
                   "mandate_block_text": agent.core_mandate}, fh, indent=1, default=str)
    if verbose:
        print(f"[RunnerV2] done {run_id}: final value {df['Portfolio_Value'].iloc[-1]:.2f}, trades {len(port.trades)}")
    return df
