"""Preflight for a vLLM pilot on HiPerGator: a few real harness decisions against the live server, before the pilot
spends GPU hours.

    python -m tools.cluster.preflight_vllm --manifest <manifest.json> --config "vllm/<served>|default"

It builds the agent exactly as `simulation.runner_v2.run_simulation_v2` does, for the first cell of each
(persona, arm) in the manifest, and makes the first two decisions of each: twelve calls for a pilot manifest. It exits 0
only when no decision falls back and at most one needed a retry.

Why it exists: Muse Glimmer served without its reasoning parser (job 42570388, 18-19 Sep 2026) wrote its reasoning into
the reply, so 173 to 182 of every 200 decisions fell back and each run took about 12 hours before anyone could tell.
"""
from __future__ import annotations

import argparse
import sys
import time


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Make a few real harness decisions against a live vLLM server.")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--config", required=True, help='the roster key, e.g. "vllm/openai/gpt-oss-120b|default"')
    ap.add_argument("--decisions", type=int, default=2, help="decisions per cell (default 2)")
    a = ap.parse_args(argv)

    from agent.v2_agent import V2Agent
    from envs.synthetic_market import SyntheticMarketEnv
    from evaluation.targets import start_cash_share
    from simulation.portfolio_v2 import PortfolioV2
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R

    m = R.load_manifest(a.manifest)
    mc = RO.by_key(a.config)
    client = RO.make_client(mc)
    picks, seen = [], set()
    for c in m["cells"]:
        if (c["persona"], c["arm"]) not in seen:
            seen.add((c["persona"], c["arm"]))
            picks.append(c)

    counts = {"ok": 0, "retry": 0, "fallback": 0}
    for c in picks:
        cfg = R.cfg_for(mc, c, m["subdir"])
        # the same construction as simulation/runner_v2.run_simulation_v2, so the prompts are the pilot's prompts
        env = SyntheticMarketEnv(cfg.scenario, cfg.T, cfg.seed, crash_discount=cfg.crash_discount, ordering=cfg.ordering,
                                 n_assets=cfg.n_assets, engine=cfg.engine, b_pred=cfg.b_pred,
                                 disclose_horizon=cfg.disclose_horizon, field_order=cfg.field_order,
                                 config=cfg.env_config or None)
        agent = V2Agent(persona=cfg.persona, model_name=cfg.model_name, mandate_block=cfg.mandate_block,
                        mandate_persona=cfg.mandate_persona, wording=cfg.wording, track=cfg.track,
                        action_interface=cfg.action_interface, n_assets=cfg.n_assets,
                        disclose_horizon=cfg.disclose_horizon, T=cfg.T, cost_visible=cfg.cost_visible,
                        cost_bp=cfg.cost_bp, objective=cfg.objective, mandate_in_system=cfg.mandate_in_system,
                        temperature=cfg.temperature, liquidity_condition=cfg.liquidity_condition, llm=client,
                        placebo_version=cfg.placebo_version)
        obs = env.reset()
        port = PortfolioV2(cfg.initial_value, start_cash_share(cfg.persona, cfg.start_design), obs["price"],
                           n_assets=cfg.n_assets, dividends=cfg.dividends)
        for day in range(1, a.decisions + 1):
            t0 = time.time()
            d = agent.decide(obs, port.get_state(obs["price"]))
            st = agent.last_parse_status
            kind = "ok" if st == "ok" else ("fallback" if st == "fallback" else "retry")
            counts[kind] += 1
            print(f"{cfg.persona:5s} {cfg.arm:8s} {cfg.scenario:15s} day {day}: {st:10s} "
                  f"target_cash_share={getattr(d, 'target_cash_share', None)}  {time.time() - t0:6.1f}s", flush=True)
            if kind != "ok":
                print(f"    rationale: {str(getattr(d, 'rationale', ''))[:400]}", flush=True)
            obs, done = env.step()
            if obs is None or done:
                break

    passed = counts["fallback"] == 0 and counts["retry"] <= 1
    print(f"PREFLIGHT {'PASS' if passed else 'FAIL'}: {counts}", flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
