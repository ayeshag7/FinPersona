"""
v2.1 Phase 8 -- E8.5, the variance pilot (PREREG_PHASE_8.md section 5).  Resumable per run, checkpointed, with a
cost gate and a contamination rule.  The design below is the registered one and does not move after the first batch.

    python -u -m tools.phase8.e8_5_variance_pilot dry-run                      # no calls: manifest, paths, price
    python -u -m tools.phase8.e8_5_variance_pilot smoke                        # 2 Flash + 2 GPT-5 mini runs; the gate
    python -u -m tools.phase8.e8_5_variance_pilot run --model main --workers 16
    python -u -m tools.phase8.e8_5_variance_pilot run --model transfer --workers 8
    python -u -m tools.phase8.e8_5_variance_pilot status

Outputs.  Run CSVs / meta / usage under `results_v2/phase8_e8_5/<model>/...` (git-ignored, like every v2 harness
output); the manifest, the dry run, the smoke gate and the ledger of every attempt under
`docs/env_v2/generated/v2_1/e8_5/`.

Rules implemented here, each registered:
* **checkpoint** -- a run id enters `checkpoint.txt` only after its CSV, `meta.json` and `usage.json` exist and are
  non-empty (P5-12); a crash loses at most the runs in flight;
* **resume refuses** if any (persona, arm) `Prompt_Hash` or the `Env_Code_Hash` differs from the launch manifest;
* **contamination** -- a run with a parse fallback whose recorded error is not a parse error, or with fallbacks and
  provider errors in the same run, is discarded (files renamed `*.contaminated.*`), logged, and re-run at most twice;
  genuine parse fallbacks are the model's behaviour and are kept;
* **the cost gate** -- `smoke` projects the total from billed usage and refuses `run` above $174; `run` also stops
  when the ledger's actual spend passes $174 less the L3 estimate;
* **temperature** -- `langchain_openai` silently drops any temperature other than 1 for gpt-5 models
  (`BaseChatOpenAI.validate_temperature`), so GPT-5 mini is configured and LOGGED at 1.0, the only value the provider
  accepts; the transfer ratio is then a model-and-temperature transfer (PREREG 5.1).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e8_5")
RESULTS = os.path.join(ROOT, "results_v2", "phase8_e8_5")

# ------------------------------------------------------------------------------------------ the registered design
MAIN_MODEL = "gemini-2.5-flash"
TRANSFER_MODEL = "gpt-5-mini"
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
ARMS = ("static", "memory")
SCENARIOS = ("flat", "bull_trap", "crash", "sustained_bull")
TRANSFER_SCENARIOS = ("bull_trap",)
SEEDS = tuple(range(2001, 2009))
REPS = 3
T = 200
CRASH_DISCOUNT = 0.70
TEMPERATURE = {MAIN_MODEL: 0.2, TRANSFER_MODEL: 1.0}
TEMPERATURE_NOTE = {MAIN_MODEL: "the harness default (FACTOR_DEFAULTS), the pilot's value",
                    TRANSFER_MODEL: "gpt-5-mini accepts only temperature 1; langchain_openai drops any other value "
                                    "silently, so 1.0 is configured and logged (PREREG 5.1 contingency)"}
PRICES = {MAIN_MODEL: (0.30, 2.50), TRANSFER_MODEL: (0.25, 2.00)}   # USD per M input / output (plan 0.4, 26-27 Aug)
# P8-8 (10 Sep 2026): the first gate stopped the registered design at a measured ~$594 (Flash thinks ~1,540 tokens per
# call, billed as output); the team chose Flash with thinking OFF for E8.5 and the main grid.  Registered before any
# batch (PREREG_PHASE_8_ADDENDUM.md 9); the approval and the gate are re-set from that answer by the 125 % rule.
THINKING_BUDGET = {MAIN_MODEL: 0, TRANSFER_MODEL: None}          # None = the provider default
CONFIG_TAG = {MAIN_MODEL: "thinking0", TRANSFER_MODEL: "default"}
APPROVED_USD = 151.0
GATE_USD = 189.0
FIRST_GATE = {"approved_usd": 139.0, "gate_usd": 174.0, "projected_usd": 594.43, "verdict": "STOP",
              "file": "smoke_thinking_default.json", "manifest": "manifest_thinking_default.json"}
L3_ESTIMATE_USD = 12.0
SMOKE_CELLS = [("ISFJ", "static", "bull_trap", 2001, 0), ("ISFJ", "memory", "bull_trap", 2001, 0)]
PARSE_MARKERS = ("OUTPUT_PARSING_FAILURE", "Failed to parse", "Invalid json output", "validation error",
                 "Expecting value", "Invalid json")
MAX_ATTEMPTS = 3

_LOCK = threading.Lock()


def slug(model: str) -> str:
    return model.replace("/", "_")


def design(which: str) -> Tuple[str, List[tuple]]:
    model = MAIN_MODEL if which == "main" else TRANSFER_MODEL
    scen = SCENARIOS if which == "main" else TRANSFER_SCENARIOS
    cells = [(p, a, sc, s, r) for p in PERSONAS for a in ARMS for sc in scen for s in SEEDS for r in range(REPS)]
    return model, cells


def cfg_for(model: str, cell: tuple):
    from experiments.arms_v2 import build_config
    p, a, sc, s, r = cell
    return build_config(model, p, a, sc, s, r, crash_discount=CRASH_DISCOUNT, T=T,
                        output_dir=os.path.join(RESULTS, CONFIG_TAG[model]), dividends=True, temperature=TEMPERATURE[model])


def run_paths(cfg) -> Dict[str, str]:
    d = os.path.join(RESULTS, CONFIG_TAG[cfg.model_name], slug(cfg.model_name), cfg.scenario, f"seed{cfg.seed}")
    rid = cfg.run_id()
    return {"dir": d, "csv": os.path.join(d, f"{rid}.csv"), "meta": os.path.join(d, f"{rid}.meta.json"),
            "usage": os.path.join(d, f"{rid}.usage.json")}


def make_llm_with_retries(model: str, temperature: float, max_retries: int = 8, thinking_budget=None):
    """`agent.llm_factory.make_llm` with the client's own retry-with-backoff raised, so a transient 429 is absorbed
    before the agent's three attempts turn it into a fallback, and -- for Gemini -- the thinking budget of P8-8.  Same
    constructor arguments otherwise (`test_e8_5_llm_matches_factory`)."""
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"))
    if "gemini" in model.lower():
        from langchain_google_genai import ChatGoogleGenerativeAI
        extra = {} if thinking_budget is None else {"thinking_budget": int(thinking_budget)}
        return ChatGoogleGenerativeAI(model=model, temperature=temperature, google_api_key=os.getenv("GOOGLE_API_KEY"),
                                      max_retries=max_retries, **extra)
    if "gpt" in model.lower():
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, temperature=temperature, api_key=os.getenv("OPENAI_API_KEY"),
                          max_retries=max_retries)
    raise ValueError(f"E8.5 registers only {MAIN_MODEL} and {TRANSFER_MODEL}; got {model!r}")


def usage_recorder():
    from langchain_core.callbacks import BaseCallbackHandler

    class UsageRecorder(BaseCallbackHandler):
        """Billed tokens per call, every attempt (a call whose reply fails to parse is still billed)."""

        def __init__(self):
            super().__init__()
            self.calls: List[Dict[str, int]] = []
            self.errors: List[str] = []

        def on_llm_end(self, response, **kw):
            for gens in response.generations:
                for g in gens:
                    um = getattr(getattr(g, "message", None), "usage_metadata", None) or {}
                    det = dict(um.get("output_token_details") or {})
                    self.calls.append({"in": int(um.get("input_tokens") or 0), "out": int(um.get("output_tokens") or 0),
                                       "reasoning": int(det.get("reasoning") or 0)})

        def on_llm_error(self, error, **kw):
            self.errors.append(f"{type(error).__name__}: {str(error)[:200]}")

    return UsageRecorder()


def agent_kw(cfg) -> dict:
    """The runner's own agent arguments (simulation/runner_v2.py), for the fingerprint."""
    return dict(persona=cfg.persona, model_name=cfg.model_name, mandate_block=cfg.mandate_block,
                mandate_persona=cfg.mandate_persona, wording=cfg.wording, track=cfg.track,
                action_interface=cfg.action_interface, n_assets=cfg.n_assets, disclose_horizon=cfg.disclose_horizon,
                T=cfg.T, cost_visible=cfg.cost_visible, cost_bp=cfg.cost_bp, objective=cfg.objective,
                mandate_in_system=cfg.mandate_in_system, temperature=cfg.temperature,
                liquidity_condition=cfg.liquidity_condition)


def fingerprint() -> dict:
    """What a resumed batch must still be: the prompt of every (model, persona, arm) and the environment code."""
    from langchain_core.runnables import RunnableLambda
    from agent.v2_agent import V2Agent
    from envs.synthetic_market import SyntheticMarketEnv
    from simulation.provenance import agent_provenance, env_provenance
    out = {"prompt_hash": {}, "system_prompt_hash": {}}
    for which in ("main", "transfer"):
        model, _ = design(which)
        for p in PERSONAS:
            for a in ARMS:
                cfg = cfg_for(model, (p, a, "flat", SEEDS[0], 0))
                ag = V2Agent(**agent_kw(cfg), llm=RunnableLambda(lambda m: None))
                pv = agent_provenance(ag)
                out["prompt_hash"][f"{model}|{p}|{a}"] = pv["Prompt_Hash"]
                out["system_prompt_hash"][f"{model}|{p}|{a}"] = pv.get("System_Prompt_Hash")
    env = SyntheticMarketEnv("flat", T, SEEDS[0])
    out["Env_Code_Hash"] = env_provenance(env)["Env_Code_Hash"]
    return out


def _source_sha() -> dict:
    out = {}
    for rel in ("agent/v2_agent.py", "agent/v2_prompts.py", "agent/render.py", "simulation/runner_v2.py",
                "simulation/portfolio_v2.py", "experiments/arms_v2.py"):
        with open(os.path.join(ROOT, rel), "rb") as fh:
            out[rel] = hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()
    return out


def manifest_path():
    return os.path.join(OUT, "manifest.json")


def verify_fingerprint():
    with open(manifest_path(), "r", encoding="utf-8") as fh:
        man = json.load(fh)
    cur = fingerprint()
    bad = [k for k, v in man["fingerprint"]["prompt_hash"].items() if cur["prompt_hash"].get(k) != v]
    if cur["Env_Code_Hash"] != man["fingerprint"]["Env_Code_Hash"]:
        bad.append("Env_Code_Hash")
    if bad:
        raise SystemExit(f"REFUSING TO RESUME: the harness no longer produces the launch manifest's prompts/environment "
                         f"for {bad}. A variance pilot whose design moved after the first batch is not a variance pilot.")


# ------------------------------------------------------------------------------------------ ledger / checkpoint
def ledger_path():
    return os.path.join(OUT, "ledger.jsonl")


def read_ledger() -> List[dict]:
    """Every attempt, from `ledger.jsonl` (the smokes) and the per-model batch ledgers: the main and transfer batches run
    as separate processes, and an in-process lock cannot serialise two processes' appends to one file."""
    import glob
    out = []
    for p in sorted(glob.glob(os.path.join(OUT, "ledger*.jsonl"))):
        with open(p, "r", encoding="utf-8") as fh:
            out += [json.loads(l) for l in fh if l.strip()]
    return out


def append_ledger(rec: dict):
    model = rec.get("model", "")
    path = os.path.join(OUT, f"ledger_{CONFIG_TAG.get(model, 'unknown')}_{slug(model)}.jsonl") if model in CONFIG_TAG else ledger_path()
    with _LOCK:
        os.makedirs(OUT, exist_ok=True)
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(rec, default=str) + "\n")


def checkpoint_path(model):
    return os.path.join(RESULTS, CONFIG_TAG[model], slug(model), "checkpoint.txt")


def done_ids(model) -> set:
    p = checkpoint_path(model)
    if not os.path.exists(p):
        return set()
    ids = set(open(p, encoding="utf-8").read().split())
    ok = set()
    for rid in ids:
        parts = rid.split("__")
        sc = parts[3].split("_d")[0]
        seed = parts[4].replace("seed", "")
        d = os.path.join(RESULTS, CONFIG_TAG[model], slug(model), sc, f"seed{seed}")
        files = [os.path.join(d, f"{rid}{ext}") for ext in (".csv", ".meta.json", ".usage.json")]
        if all(os.path.exists(f) and os.path.getsize(f) > 0 for f in files):
            ok.add(rid)
    return ok


def spend_so_far() -> float:
    return float(sum(r.get("usd", 0.0) or 0.0 for r in read_ledger()))


# ------------------------------------------------------------------------------------------ one run
def run_one(model: str, cell: tuple) -> dict:
    from simulation.runner_v2 import run_simulation_v2
    cfg = cfg_for(model, cell)
    rid = cfg.run_id()
    paths = run_paths(cfg)
    rec = usage_recorder()
    llm = make_llm_with_retries(model, cfg.temperature, thinking_budget=THINKING_BUDGET[model]).with_config(callbacks=[rec])
    t0 = time.time()
    status, err, df = "ok", "", None
    try:
        df = run_simulation_v2(replace(cfg, agent_llm=llm), verbose=False)
        if df is None:
            status, err = "failed", "run_simulation_v2 returned None (fewer than 10 % of days logged)"
    except Exception as e:                                   # noqa: BLE001
        status, err = "failed", f"{type(e).__name__}: {str(e)[:300]}"
    pin, pout = PRICES[model]
    tin = sum(c["in"] for c in rec.calls); tout = sum(c["out"] for c in rec.calls)
    treas = sum(c["reasoning"] for c in rec.calls)
    usd = tin / 1e6 * pin + tout / 1e6 * pout
    n_fb = n_prov_fb = 0
    if df is not None:
        fb = df[df["Parse_Status"].astype(str) == "fallback"]
        n_fb = int(len(fb))
        n_prov_fb = int(sum(1 for r in fb["Rationale"].astype(str) if not any(m in r for m in PARSE_MARKERS)))
        if n_prov_fb > 0 or (n_fb > 0 and rec.errors):
            status = "contaminated"
    usage = {"run_id": rid, "model": model, "temperature": cfg.temperature, "thinking_budget": THINKING_BUDGET[model],
             "config_tag": CONFIG_TAG[model], "status": status, "error": err,
             "seconds": time.time() - t0, "n_llm_calls": len(rec.calls), "input_tokens": tin, "output_tokens": tout,
             "reasoning_tokens": treas, "usd": usd, "prices_per_M": [pin, pout], "n_fallbacks": n_fb,
             "n_provider_fallbacks": n_prov_fb, "llm_errors": rec.errors[:50], "calls": rec.calls}
    os.makedirs(paths["dir"], exist_ok=True)
    if status == "ok":
        with open(paths["usage"], "w", encoding="utf-8", newline="\n") as fh:
            json.dump(usage, fh)
        with _LOCK:
            with open(checkpoint_path(model), "a", encoding="utf-8", newline="\n") as fh:
                fh.write(rid + "\n")
    else:
        stamp = time.strftime("%Y%m%dT%H%M%S")
        for k in ("csv", "meta"):
            if os.path.exists(paths[k]):
                os.replace(paths[k], paths[k].replace(".csv", f".{status}.{stamp}.csv").replace(".meta.json", f".{status}.{stamp}.meta.json"))
        with open(paths["usage"].replace(".usage.json", f".{status}.{stamp}.usage.json"), "w", encoding="utf-8") as fh:
            json.dump(usage, fh)
    append_ledger({k: v for k, v in usage.items() if k != "calls"} | {"cell": list(cell), "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    return usage


def attempts(model: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for r in read_ledger():
        if r.get("model") == model and r.get("config_tag") == CONFIG_TAG[model] and r.get("status") != "ok":
            out[r["run_id"]] = out.get(r["run_id"], 0) + 1
    return out


# ------------------------------------------------------------------------------------------ stages
def stage_dry_run():
    from envs.synthetic_market import SyntheticMarketEnv
    import tiktoken
    os.makedirs(OUT, exist_ok=True)
    res = {"design": {}, "paths": [], "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for which in ("main", "transfer"):
        model, cells = design(which)
        ids = [cfg_for(model, c).run_id() for c in cells]
        assert len(ids) == len(set(ids)), "duplicate run ids in the design"
        res["design"][which] = {"model": model, "n_runs": len(cells), "n_calls": len(cells) * T,
                                "temperature": TEMPERATURE[model], "temperature_note": TEMPERATURE_NOTE[model],
                                "scenarios": list(SCENARIOS if which == "main" else TRANSFER_SCENARIOS)}
    for sc in SCENARIOS:
        for s in SEEDS:
            t0 = time.time()
            env = SyntheticMarketEnv(sc, T, s, crash_discount=CRASH_DISCOUNT)
            res["paths"].append({"scenario": sc, "seed": s, "attempts": int(env.attempts),
                                 "topped": env.event_meta.get("topped"), "seconds": round(time.time() - t0, 2)})
    # price at the plan's output assumption, from today's rendered prompt (o200k)
    from langchain_core.runnables import RunnableLambda
    from agent.v2_agent import V2Agent
    from simulation.portfolio_v2 import PortfolioV2
    from evaluation.targets import start_cash_share
    enc = tiktoken.get_encoding("o200k_base")
    env = SyntheticMarketEnv("bull_trap", T, SEEDS[0]); obs = env.reset()
    toks = []
    for p in PERSONAS:
        for a in ARMS:
            cfg = cfg_for(MAIN_MODEL, (p, a, "bull_trap", SEEDS[0], 0))
            ag = V2Agent(**agent_kw(cfg), llm=RunnableLambda(lambda m: None))
            st = PortfolioV2(10000.0, start_cash_share(p, "target"), obs["price"]).get_state(obs["price"])
            toks.append(len(enc.encode(ag.full_system_prompt)) + len(enc.encode(ag.rendered_human_message(obs, st))))
    per_call_in = float(np.mean(toks))
    est = {}
    for which in ("main", "transfer"):
        model, cells = design(which)
        pin, pout = PRICES[model]
        est[which] = {"input_tokens_per_call_o200k": per_call_in, "output_tokens_per_call_assumed": 120,
                      "usd": len(cells) * T * (per_call_in * pin + 120 * pout) / 1e6}
    res["price_estimate_before_smoke"] = est
    res["price_note"] = ("output tokens per call are the plan's assumption (120); thinking tokens bill as output and "
                         "are measured by the smoke stage, which decides the gate")
    man = {"design": res["design"], "seeds": list(SEEDS), "personas": list(PERSONAS), "arms": list(ARMS),
           "scenarios": list(SCENARIOS), "transfer_scenarios": list(TRANSFER_SCENARIOS), "reps": REPS, "T": T,
           "crash_discount": CRASH_DISCOUNT, "dividends": True, "prices_per_M": PRICES, "approved_usd": APPROVED_USD,
           "gate_usd": GATE_USD, "thinking_budget": THINKING_BUDGET, "config_tag": CONFIG_TAG,
           "first_gate": FIRST_GATE, "decision": "DECISION_LOG P8-8; PREREG_PHASE_8_ADDENDUM.md 9",
           "fingerprint": fingerprint(), "source_sha256_lf": _source_sha(),
           "written_utc": res["generated_utc"]}
    if os.path.exists(manifest_path()):
        verify_fingerprint()
        print("manifest exists and the fingerprint matches; not rewritten")
    else:
        with open(manifest_path(), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(man, fh, indent=1, default=str)
        print("manifest written", manifest_path())
    with open(os.path.join(OUT, "dryrun.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1, default=str)
    print(json.dumps(res["design"], indent=1))
    print("paths constructible:", len(res["paths"]), "; attempts > 1:", sum(1 for p in res["paths"] if p["attempts"] > 1))
    print("price before smoke:", {k: round(v["usd"], 2) for k, v in est.items()}, f"(input {per_call_in:.0f} o200k tokens/call)")


def stage_smoke():
    verify_fingerprint()
    rows = []
    jobs = []
    for which in ("main", "transfer"):
        model, _ = design(which)
        have = done_ids(model)
        for cell in SMOKE_CELLS:
            jobs.append((which, model, cell, cfg_for(model, cell).run_id() in have))

    def _smoke(job):
        which, model, cell, have = job
        rid = cfg_for(model, cell).run_id()
        if have:
            u = json.load(open(run_paths(cfg_for(model, cell))["usage"], encoding="utf-8"))
        else:
            print(f"[smoke] {rid} started", flush=True)
            u = run_one(model, cell)
        print(f"[smoke] {rid}: {u['status']} {u['seconds']:.0f}s, {u['n_llm_calls']} calls, in {u['input_tokens']:,} "
              f"out {u['output_tokens']:,} (reasoning {u['reasoning_tokens']:,}), ${u['usd']:.3f}", flush=True)
        return {"which": which, **{k: v for k, v in u.items() if k != "calls"}}

    with ThreadPoolExecutor(max_workers=len(jobs)) as ex:     # the four smoke runs at once
        rows = list(ex.map(_smoke, jobs))
    return write_gate(rows)


def write_gate(rows) -> int:
    """The gate from the smoke runs' BILLED usage.  A run that completed all T calls is priced whatever happened to it
    afterwards: the first smoke's four runs completed 200 of 200 calls and then failed on the runner's meta write
    (P8-6), which does not change what they cost.  Passing still requires every smoke run to be `ok`."""
    df = pd.DataFrame(rows)
    ok = df[df.n_llm_calls >= T]
    proj = {}
    for which in ("main", "transfer"):
        model, cells = design(which)
        m = ok[ok.which == which]
        per_run = float(m["usd"].mean()) if len(m) else float("nan")
        proj[which] = {"model": model, "usd_per_run_measured": per_run, "n_smoke_runs_ok": int(len(m)),
                       "n_runs": len(cells), "usd_projected": per_run * len(cells),
                       "seconds_per_run": float(m["seconds"].mean()) if len(m) else float("nan"),
                       "input_tokens_per_call": float((m["input_tokens"] / m["n_llm_calls"]).mean()) if len(m) else float("nan"),
                       "output_tokens_per_call": float((m["output_tokens"] / m["n_llm_calls"]).mean()) if len(m) else float("nan"),
                       "reasoning_tokens_per_call": float((m["reasoning_tokens"] / m["n_llm_calls"]).mean()) if len(m) else float("nan")}
    total = sum(v["usd_projected"] for v in proj.values()) + L3_ESTIMATE_USD
    all_ok = bool((df.status == "ok").all())
    gate = {"projected_total_usd": total, "l3_estimate_usd": L3_ESTIMATE_USD, "approved_usd": APPROVED_USD,
            "gate_usd": GATE_USD, "pass": bool(np.isfinite(total) and total <= GATE_USD and all_ok),
            "priced_on": "billed usage of every smoke run that completed all its calls", "all_smoke_runs_ok": all_ok,
            "usd_spent_on_smoke": float(df["usd"].sum()),
            "per_design": proj, "runs": rows, "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(os.path.join(OUT, "smoke.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(gate, fh, indent=1, default=str)
    print(json.dumps({k: v for k, v in gate.items() if k != "runs"}, indent=1, default=str))
    if not gate["pass"]:
        print("STOP: the cost gate is not passed (or a smoke run did not complete). The batch does not start; "
              "the team is asked (PREREG 5.3).")
        return 2
    return 0


def stage_gate():
    """Recompute the gate from the ledger's smoke rows (the last attempt of each smoke cell); no call is made."""
    led = read_ledger()
    rows = []
    for which in ("main", "transfer"):
        model, _ = design(which)
        for cell in SMOKE_CELLS:
            rid = cfg_for(model, cell).run_id()
            mine = [r for r in led if r["run_id"] == rid and r.get("config_tag") == CONFIG_TAG[model]]
            if mine:
                rows.append({"which": which, **mine[-1]})
    return write_gate(rows)


def stage_run(which: str, workers: int, max_runs: int = 0):
    verify_fingerprint()
    sm = os.path.join(OUT, "smoke.json")
    if not os.path.exists(sm) or not json.load(open(sm, encoding="utf-8"))["pass"]:
        raise SystemExit("the smoke gate has not passed; run `smoke` first (PREREG 5.3)")
    model, cells = design(which)
    have = done_ids(model)
    tries = attempts(model)
    pending = [c for c in cells if cfg_for(model, c).run_id() not in have
               and tries.get(cfg_for(model, c).run_id(), 0) < MAX_ATTEMPTS]
    abandoned = [c for c in cells if cfg_for(model, c).run_id() not in have
                 and tries.get(cfg_for(model, c).run_id(), 0) >= MAX_ATTEMPTS]
    if max_runs:
        pending = pending[:max_runs]
    stop_at = GATE_USD - L3_ESTIMATE_USD
    print(f"{model}: {len(cells)} runs in the design, {len(have)} done, {len(pending)} pending, "
          f"{len(abandoned)} abandoned after {MAX_ATTEMPTS} non-ok attempts; spend so far ${spend_so_far():.2f} "
          f"(stop at ${stop_at:.2f})", flush=True)
    t0 = time.time(); n = 0; stop = threading.Event()

    def _job(c):
        if stop.is_set():
            return None
        return run_one(model, c)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_job, c): c for c in pending}
        for fu in as_completed(futs):
            u = fu.result()
            if u is None:
                continue
            n += 1
            spent = spend_so_far()
            rate = n / max(time.time() - t0, 1.0)
            eta_h = (len(pending) - n) / rate / 3600 if rate > 0 else float("nan")
            print(f"[{n}/{len(pending)}] {u['run_id']} -> {u['status']} ({u['seconds']:.0f}s, ${u['usd']:.3f}, "
                  f"fallbacks {u['n_fallbacks']}); spend ${spent:.2f}; ETA {eta_h:.1f} h", flush=True)
            if spent > stop_at and not stop.is_set():
                stop.set()
                print(f"STOP: actual spend ${spent:.2f} passed ${stop_at:.2f} (the gate less the L3 estimate); "
                      f"in-flight runs finish, nothing new starts; the team is asked", flush=True)
    return 0


def stage_status():
    for which in ("main", "transfer"):
        model, cells = design(which)
        have = done_ids(model)
        led = [r for r in read_ledger() if r.get("model") == model]
        st = pd.Series([r["status"] for r in led]).value_counts().to_dict() if led else {}
        print(f"{model}: {len(have)}/{len(cells)} done; attempts by status {st}; "
              f"spend ${sum(r.get('usd', 0) for r in led):.2f}")
    print(f"total spend ${spend_so_far():.2f} of ${APPROVED_USD:.0f} approved (gate ${GATE_USD:.0f})")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["dry-run", "smoke", "gate", "run", "status"])
    ap.add_argument("--model", choices=["main", "transfer"], default="main")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--max-runs", type=int, default=0)
    a = ap.parse_args(argv)
    if a.stage == "dry-run":
        return stage_dry_run() or 0
    if a.stage == "smoke":
        return stage_smoke()
    if a.stage == "gate":
        return stage_gate()
    if a.stage == "run":
        return stage_run(a.model, a.workers, a.max_runs)
    return stage_status() or 0


if __name__ == "__main__":
    raise SystemExit(main())
