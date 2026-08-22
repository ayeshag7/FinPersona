"""
Config-driven arm registry and grid runner for the v2 harness (plan Section 7; E3).

Arms (each a dict of RunConfig overrides):
  static              persona only, no per-step block                      (v1 'static', stateless control)
  memory              persona + core mandate re-injected every step         (v1 'memory')
  placebo_declarative persona + declarative boilerplate every step          (v1 placebo)
  placebo_directive   persona + imperative/delimiter/length-matched placebo (B4)
  wrapper_only        persona + 'ACTIVE MEMORY REFRESH' wrapper, no mandate (B4)
  swapped             persona + the OTHER persona's mandate (ISFJ<->ENTJ; INTJ gets ENTJ) (B5)
  trader              no persona, no mandate; starts at 0.5 (B6); objective none | maximise
  path_b_static       core mandate in the system prompt at t=0, no re-injection (11.1)
  path_b_memory       mandate in system prompt AND re-injected
  stateful_static     E5: rolling-window context (last 20 steps as prior turns), mandate in system prompt
  stateful_memory     E5: rolling-window context AND per-step re-injection
  stateful_full_*     E5: full transcript up to a 60k-token budget
Wording levels, Track A/B, start design, action interface, cost tier/visibility,
horizon disclosure, field order, execution and decode replicates are factors.

CLI:  python -m experiments.arms_v2 --models gemini-2.5-flash --personas ISFJ ENTJ INTJ
        --arms static memory --scenarios flat crash bull_trap --seeds 42 123 456 --reps 1
"""
from __future__ import annotations

import argparse
import itertools
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from typing import Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from simulation.runner_v2 import RunConfig, run_simulation_v2  # noqa: E402

SWAP = {"ISFJ": "ENTJ", "ENTJ": "ISFJ", "INTJ": "ENTJ", "O1_conservative": "O2_aggressive", "O2_aggressive": "O1_conservative"}

ARMS: Dict[str, Dict] = {
    "static": {"mandate_block": "none"},
    "memory": {"mandate_block": "mandate"},
    "placebo_declarative": {"mandate_block": "placebo_declarative"},
    "placebo_directive": {"mandate_block": "placebo_directive"},
    "wrapper_only": {"mandate_block": "wrapper_only"},
    "swapped": {"mandate_block": "mandate", "mandate_persona": "__swap__"},
    "trader": {"persona": "NONE", "mandate_block": "none", "objective": "none", "start_design": "common"},
    "trader_maximise": {"persona": "NONE", "mandate_block": "none", "objective": "maximise", "start_design": "common"},
    "path_b_static": {"mandate_block": "none", "mandate_in_system": True},
    "path_b_memory": {"mandate_block": "mandate", "mandate_in_system": True},
    # E5 stateful arms (context accumulates; mandate in the system prompt at t = 0 for all of them)
    "stateful_static": {"mandate_block": "none", "mandate_in_system": True, "context_mode": "rolling"},
    "stateful_memory": {"mandate_block": "mandate", "mandate_in_system": True, "context_mode": "rolling"},
    "stateful_full_static": {"mandate_block": "none", "mandate_in_system": True, "context_mode": "full"},
    "stateful_full_memory": {"mandate_block": "mandate", "mandate_in_system": True, "context_mode": "full"},
}

# Multi-asset extension (decision 8): the scenario asset, a correlated peer and a low-volatility
# 'defensive' risky asset (vol/omega x 0.5); the scheduled event applies to all three, each with its own
# mispricing process and hazard; the cash-share band is scored on the total cash share.
THREE_ASSET = {"n_assets": 3, "env_config": {"asset_vol_scale": [1.0, 1.0, 0.5], "rho_common": 0.3}}

FACTOR_DEFAULTS = {
    "wording": "rewritten", "track": "B", "start_design": "target", "action_interface": "target",
    "cost_bp": 5.0, "cost_visible": False, "execution": "same_day", "disclose_horizon": False,
    "field_order": "canonical", "probe_every": 0, "temperature": 0.2,
}
# the 100%-cash / v1-interface bridge cell to v1 (plan 8.6)
BRIDGE_CELL = {"start_design": "v1", "action_interface": "v1", "wording": "original", "cost_bp": 0.0}


def build_config(model: str, persona: str, arm: str, scenario: str, seed: int, rep: int = 0,
                 crash_discount: float = 0.70, factors: Dict = None, bridge: bool = False, **kw) -> RunConfig:
    if arm not in ARMS:
        raise KeyError(f"unknown arm {arm!r}; known: {sorted(ARMS)}")
    spec = dict(ARMS[arm])
    if spec.get("mandate_persona") == "__swap__":
        spec["mandate_persona"] = SWAP.get(persona, "ENTJ")
    f = dict(FACTOR_DEFAULTS)
    f.update(factors or {})
    if bridge:
        f.update(BRIDGE_CELL)
    f.update(kw)   # explicit keyword overrides win over factor defaults
    cfg = RunConfig(model_name=model, persona=spec.pop("persona", persona), arm=arm, scenario=scenario, seed=seed,
                    decode_replicate=rep, crash_discount=crash_discount, **f)
    return replace(cfg, **spec)


def expand_grid(models: List[str], personas: List[str], arms: List[str], scenarios: List[str], seeds: List[int],
                reps: int = 1, crash_discounts=(0.70,), factors: Dict = None, bridge: bool = False, **kw) -> List[RunConfig]:
    out = []
    for m, p, a, sc, s, r in itertools.product(models, personas, arms, scenarios, seeds, range(reps)):
        for d in (crash_discounts if sc == "crash" else [0.70]):
            out.append(build_config(m, p, a, sc, s, r, crash_discount=d, factors=factors, bridge=bridge, **kw))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["gemini-2.5-flash"])
    ap.add_argument("--personas", nargs="+", default=["ISFJ", "INTJ", "ENTJ"])
    ap.add_argument("--arms", nargs="+", default=["static", "memory"])
    ap.add_argument("--scenarios", nargs="+", default=["flat", "bull_trap", "crash"])
    ap.add_argument("--seeds", nargs="+", type=int, default=[42, 123, 456, 789, 999])
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--discounts", nargs="+", type=float, default=[0.55, 0.70, 0.85])
    ap.add_argument("--T", type=int, default=200)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default="results_v2")
    ap.add_argument("--bridge", action="store_true", help="run the 100%-cash / v1-interface bridge cell")
    ap.add_argument("--track", default="B"); ap.add_argument("--start", default="target")
    ap.add_argument("--wording", default="rewritten"); ap.add_argument("--cost_bp", type=float, default=5.0)
    ap.add_argument("--cost_visible", action="store_true"); ap.add_argument("--disclose", action="store_true")
    ap.add_argument("--field_order", default="canonical"); ap.add_argument("--execution", default="same_day")
    ap.add_argument("--probe_every", type=int, default=0)
    ap.add_argument("--three_asset", action="store_true", help="run the 3-asset extension configuration")
    ap.add_argument("--context_window", type=int, default=20)
    a = ap.parse_args()
    factors = {"track": a.track, "start_design": a.start, "wording": a.wording, "cost_bp": a.cost_bp,
               "cost_visible": a.cost_visible, "disclose_horizon": a.disclose, "field_order": a.field_order,
               "execution": a.execution, "probe_every": a.probe_every}
    extra = dict(T=a.T, output_dir=a.out, context_window=a.context_window)
    if a.three_asset:
        extra.update(THREE_ASSET)
    cfgs = expand_grid(a.models, a.personas, a.arms, a.scenarios, a.seeds, a.reps, a.discounts, factors,
                       bridge=a.bridge, **extra)
    done = set()
    ck = os.path.join(a.out, "checkpoint.txt")
    if os.path.exists(ck):
        done = set(open(ck).read().split())
    pending = [c for c in cfgs if c.run_id() not in done]
    print(f"{len(cfgs)} cells, {len(pending)} pending")
    os.makedirs(a.out, exist_ok=True)
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(run_simulation_v2, c, False): c for c in pending}
        for i, fu in enumerate(as_completed(futs)):
            c = futs[fu]
            try:
                ok = fu.result() is not None
            except Exception as exc:
                ok = False; print(f"[FAIL] {c.run_id()}: {exc}")
            if ok:
                with open(ck, "a") as fh:
                    fh.write(c.run_id() + "\n")
            print(f"[{i+1}/{len(pending)}] {c.run_id()} -> {'ok' if ok else 'FAIL'}")


if __name__ == "__main__":
    main()
