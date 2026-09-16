"""
v2.1 Phase 9 -- the paid-call runner for the smoke tests, the roster pilots (E9.2) and the grid (E9.4).

This is E8.5's runner (`tools/phase8/e8_5_variance_pilot.py`) generalised to every candidate configuration in
`tools/phase9/e9_roster.py`, with the provider options written on every row (`RunConfig.provider_options`).

    python -u -m tools.phase9.e9_runner check-clients                       # no calls: every candidate client builds
    python -u -m tools.phase9.e9_runner smoke --configs untimed             # 2 runs per configuration, all at once
    python -u -m tools.phase9.e9_runner run --manifest <file> --config <model|tag> --workers 15
    python -u -m tools.phase9.e9_runner status --manifest <file>

Rules carried from E8.5:

* **Checkpoint.** A run enters the checkpoint only after its CSV, `meta.json` and `usage.json` exist and are
  non-empty. A crash loses at most the runs in flight.
* **Contamination.** A run is discarded (renamed `*.contaminated.*`), logged, and re-run at most twice if it has a
  fallback whose recorded error is not a parse error, or has fallbacks and provider errors in the same run. Genuine
  parse fallbacks are the model's behaviour and are kept.
* **Ledger.** Every attempt is a ledger row, keyed by configuration tag.
* **Resume refusal.** A manifest run refuses to resume if its fingerprint no longer matches: the prompt hash of every
  (configuration, persona, arm), `Env_Code_Hash`, and the LF sha256 of the harness sources.

New in Phase 9:

* **Concurrency (P9-1).** `--workers` above 15 is refused. Every process registers the in-flight calls it will make
  per model under `results_v2/phase9/active/`; a process that would take a model above 15 refuses to start.
* **No cost gate.** Cost is not a constraint (P9-1). Tokens are logged per run, and dollars only where a price was
  read.
* **The harness is the grid's:** `harness_version="v2_1"`, `placebo_version="v2_1"` (P8-4, P8-5), dividends paid
  (P7-2), crash delta 0.70.
* **Progress.** Every finished run prints a progress line with an ETA.

Outputs:

* run CSV / meta / usage under `results_v2/phase9/<subdir>/<setting>/<config_tag>/<model>/...` (git-ignored, like
  every harness output);
* ledgers under `docs/env_v2/generated/v2_1/<ledger_dir>/ledger_<tag>_<model>.jsonl`;
* smoke summaries under `e9_0/smoke/`.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from typing import Dict, List

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.phase9 import e9_roster as RO  # noqa: E402

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
RESULTS = os.path.join(ROOT, "results_v2", "phase9")
ACTIVE = os.path.join(RESULTS, "active")
SMOKE_DIR = os.path.join(GEN, "e9_0", "smoke")
T = 200
CRASH_DISCOUNT = 0.70
MAX_INFLIGHT_PER_MODEL = 15                         # P9-1
MAX_ATTEMPTS = 3
HARNESS = {"harness_version": "v2_1", "placebo_version": "v2_1"}    # P8-4, P8-5: the grid's harness
SMOKE_CELLS = ({"persona": "ISFJ", "arm": "static", "scenario": "bull_trap", "seed": 2001, "rep": 0},
               {"persona": "ISFJ", "arm": "memory", "scenario": "bull_trap", "seed": 2001, "rep": 0})   # E8.5's smoke cells
PARSE_MARKERS = ("OUTPUT_PARSING_FAILURE", "Failed to parse", "Invalid json output", "validation error",
                 "Expecting value", "Invalid json")
SOURCES = ("agent/v2_agent.py", "agent/v2_prompts.py", "agent/render.py", "agent/stateful_agent.py",
           "simulation/runner_v2.py", "simulation/portfolio_v2.py", "experiments/arms_v2.py", "tools/phase9/e9_roster.py")

_LOCK = threading.Lock()


def _utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ============================================================================================ concurrency registry
def _pid_alive(pid: int) -> bool:
    """Without psutil and without os.kill (which on Windows TERMINATES the process for any signal but the console
    ones): OpenProcess + GetExitCodeProcess == STILL_ACTIVE."""
    if os.name == "nt":
        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(0x1000, False, int(pid))          # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k32.GetExitCodeProcess(h, ctypes.byref(code))
        k32.CloseHandle(h)
        return bool(ok) and code.value == 259                 # STILL_ACTIVE
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False


def inflight(model: str) -> int:
    n = 0
    if not os.path.isdir(ACTIVE):
        return 0
    for f in os.listdir(ACTIVE):
        try:
            r = json.load(open(os.path.join(ACTIVE, f), encoding="utf-8"))
        except Exception:                                     # noqa: BLE001 -- a half-written file from a dead process
            continue
        if r.get("model") == model and _pid_alive(int(r["pid"])):
            n += int(r["calls"])
    return n


def register(model: str, calls: int) -> str:
    if calls > MAX_INFLIGHT_PER_MODEL:
        raise SystemExit(f"REFUSED: {calls} concurrent calls for {model} exceed the team's cap of {MAX_INFLIGHT_PER_MODEL} (P9-1)")
    with _LOCK:
        have = inflight(model)
        if have + calls > MAX_INFLIGHT_PER_MODEL:
            raise SystemExit(f"REFUSED: {model} already has {have} in-flight calls registered by live processes; "
                             f"{calls} more would exceed the cap of {MAX_INFLIGHT_PER_MODEL} (P9-1)")
        os.makedirs(ACTIVE, exist_ok=True)
        p = os.path.join(ACTIVE, f"{RO.ModelConfig(model, '', '', None).slug}__{os.getpid()}__{threading.get_ident()}.json")
        json.dump({"pid": os.getpid(), "model": model, "calls": calls, "started_utc": _utc()}, open(p, "w", encoding="utf-8"))
        return p


def unregister(path: str):
    try:
        os.remove(path)
    except OSError:
        pass


# ============================================================================================ one run
def cfg_for(mc: RO.ModelConfig, cell: dict, subdir: str, provider_options=None, T_run: int = T):
    from experiments.arms_v2 import build_config
    kw = dict(T=T_run, output_dir=os.path.join(RESULTS, subdir, cell.get("setting", "default"), mc.config_tag),
              dividends=True, temperature=mc.temperature, provider_options=provider_options,
              env_config=dict(cell.get("env_config") or {}), **HARNESS)
    kw.update(cell.get("factors") or {})
    return build_config(mc.model, cell["persona"], cell["arm"], cell["scenario"], int(cell["seed"]), int(cell.get("rep", 0)),
                        crash_discount=CRASH_DISCOUNT, **kw)


def run_paths(cfg) -> Dict[str, str]:
    d = os.path.join(cfg.output_dir, cfg.model_name.replace("/", "_"), cfg.scenario, f"seed{cfg.seed}")
    rid = cfg.run_id()
    return {"dir": d, "csv": os.path.join(d, f"{rid}.csv"), "meta": os.path.join(d, f"{rid}.meta.json"),
            "usage": os.path.join(d, f"{rid}.usage.json")}


def run_key(cell: dict, cfg) -> str:
    return f"{cell.get('setting', 'default')}|{cfg.run_id()}"


def checkpoint_path(subdir: str, mc: RO.ModelConfig) -> str:
    return os.path.join(RESULTS, subdir, "_checkpoints", f"{mc.config_tag}__{mc.slug}.txt")


def done_keys(subdir: str, mc: RO.ModelConfig, cells: List[dict]) -> set:
    p = checkpoint_path(subdir, mc)
    if not os.path.exists(p):
        return set()
    listed = set(open(p, encoding="utf-8").read().split())
    ok = set()
    for c in cells:
        cfg = cfg_for(mc, c, subdir)
        k = run_key(c, cfg)
        if k in listed and all(os.path.exists(f) and os.path.getsize(f) > 0 for f in
                               (run_paths(cfg)[x] for x in ("csv", "meta", "usage"))):
            ok.add(k)
    return ok


def ledger_file(ledger_dir: str, mc: RO.ModelConfig) -> str:
    return os.path.join(GEN, ledger_dir, f"ledger_{mc.config_tag}_{mc.slug}.jsonl")


def append_ledger(path: str, rec: dict):
    with _LOCK:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(rec, default=str) + "\n")


def read_ledger(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def usage_recorder_v9():
    """E8.5's recorder plus what an OpenRouter run needs (P9-8): the response `id` of every call, so the serving
    upstream and the exact snapshot can be audited afterwards through OpenRouter's generation endpoint, and the cost
    the provider itself reports, so this phase's spend is measured rather than priced from a table."""
    from langchain_core.callbacks import BaseCallbackHandler

    class UsageRecorderV9(BaseCallbackHandler):
        def __init__(self):
            super().__init__()
            self.calls: List[Dict] = []
            self.errors: List[str] = []

        def on_llm_end(self, response, **kw):
            for gens in response.generations:
                for g in gens:
                    msg = getattr(g, "message", None)
                    um = getattr(msg, "usage_metadata", None) or {}
                    det = dict(um.get("output_token_details") or {})
                    rm = getattr(msg, "response_metadata", None) or {}
                    tu = dict(rm.get("token_usage") or {})
                    self.calls.append({"in": int(um.get("input_tokens") or 0), "out": int(um.get("output_tokens") or 0),
                                       "reasoning": int(det.get("reasoning") or 0),
                                       "id": rm.get("id"), "usd_reported": tu.get("cost")})

        def on_llm_error(self, error, **kw):
            self.errors.append(f"{type(error).__name__}: {str(error)[:200]}")

    return UsageRecorderV9()


def run_one(mc: RO.ModelConfig, cell: dict, subdir: str, ledger_dir: str, kind: str, T_run: int = T) -> dict:
    from simulation.runner_v2 import run_simulation_v2
    from tools.phase8.e8_5_variance_pilot import usage_recorder as usage_recorder_e85
    # OpenRouter runs need the response id and the provider-reported cost (P9-8); every other route keeps E8.5's
    # recorder unchanged, so a Google or OpenAI run records exactly what it did before.
    make_recorder = usage_recorder_v9 if mc.provider == "openrouter" else usage_recorder_e85
    client = RO.make_client(mc)
    po = RO.provider_options_record(mc, client)
    cfg = cfg_for(mc, cell, subdir, po, T_run)
    rid, key, paths = cfg.run_id(), run_key(cell, cfg_for(mc, cell, subdir, None, T_run)), run_paths(cfg)
    rec = make_recorder()
    t0 = time.time()
    status, err, df = "ok", "", None
    try:
        df = run_simulation_v2(replace(cfg, agent_llm=client.with_config(callbacks=[rec])), verbose=False)
        if df is None:
            status, err = "failed", "run_simulation_v2 returned None (fewer than 10 % of days logged)"
    except Exception as e:                                   # noqa: BLE001
        status, err = "failed", f"{type(e).__name__}: {str(e)[:300]}"
    tin = sum(c["in"] for c in rec.calls); tout = sum(c["out"] for c in rec.calls)
    treas = sum(c["reasoning"] for c in rec.calls)
    pr = RO.price(mc.model)
    usd_reported = sum(float(c["usd_reported"]) for c in rec.calls if c.get("usd_reported"))
    usd = usd_reported if usd_reported else ((tin / 1e6 * pr[0] + tout / 1e6 * pr[1]) if pr else None)
    gen_ids = [c["id"] for c in rec.calls if c.get("id")]
    # P9-8 / addendum 6: an OpenRouter run must be served by the upstream its configuration pinned.  The serving
    # upstream does NOT reach the LangChain callback -- `response_metadata` carries token_usage, model_provider (the
    # client class, not the backend), model_name, system_fingerprint, id, service_tier, finish_reason and logprobs, and
    # no `provider` field (measured 12 Sep 2026).  The pin is therefore enforced by `allow_fallbacks: false` in the
    # request, and audited out-of-band; `served` stays empty until that audit is wired.
    served: List[str] = []
    wrong_upstream: List[str] = []
    n_fb = n_prov_fb = 0
    parse_counts = {}
    if df is not None:
        parse_counts = df["Parse_Status"].astype(str).value_counts().to_dict()
        fb = df[df["Parse_Status"].astype(str) == "fallback"]
        n_fb = int(len(fb))
        n_prov_fb = int(sum(1 for r in fb["Rationale"].astype(str) if not any(m in r for m in PARSE_MARKERS)))
        if n_prov_fb > 0 or (n_fb > 0 and rec.errors):
            status = "contaminated"
    if wrong_upstream and status == "ok":
        status, err = "contaminated", f"served by {wrong_upstream} but pinned to {mc.upstream!r} (P9-8)"
    usage = {"run_id": rid, "run_key": key, "model": mc.model, "config_tag": mc.config_tag, "kind": kind,
             "setting": cell.get("setting", "default"), "temperature": mc.temperature, "provider_options": po,
             "status": status, "error": err, "seconds": time.time() - t0, "n_llm_calls": len(rec.calls),
             "calls_expected": T_run, "input_tokens": tin, "output_tokens": tout, "reasoning_tokens": treas,
             "usd": usd, "usd_source": "provider-reported" if usd_reported else ("price table" if pr else "not priced"),
             "prices_per_M": list(pr) if pr else None, "upstreams_served_by": served,
             "generation_ids": gen_ids[:5] + gen_ids[-5:] if len(gen_ids) > 10 else gen_ids,
             "n_generation_ids": len(gen_ids), "upstream_pinned": mc.upstream,
             "n_fallbacks": n_fb, "n_provider_fallbacks": n_prov_fb,
             "parse_status_counts": parse_counts, "llm_errors": rec.errors[:50], "calls": rec.calls}
    os.makedirs(paths["dir"], exist_ok=True)
    if status == "ok":
        with open(paths["usage"], "w", encoding="utf-8", newline="\n") as fh:
            json.dump(usage, fh, default=str)
        with _LOCK:
            os.makedirs(os.path.dirname(checkpoint_path(subdir, mc)), exist_ok=True)
            with open(checkpoint_path(subdir, mc), "a", encoding="utf-8", newline="\n") as fh:
                fh.write(key + "\n")
    else:
        stamp = time.strftime("%Y%m%dT%H%M%S")
        for k in ("csv", "meta"):
            if os.path.exists(paths[k]):
                os.replace(paths[k], paths[k].replace(".csv", f".{status}.{stamp}.csv").replace(".meta.json", f".{status}.{stamp}.meta.json"))
        with open(paths["usage"].replace(".usage.json", f".{status}.{stamp}.usage.json"), "w", encoding="utf-8") as fh:
            json.dump(usage, fh, default=str)
    append_ledger(ledger_file(ledger_dir, mc), {k: v for k, v in usage.items() if k != "calls"} | {"cell": cell, "utc": _utc()})
    return usage


# ============================================================================================ stages
def stage_check_clients() -> int:
    """No call is made: every candidate client is constructed and its effective settings recorded."""
    out, bad = [], 0
    for mc in RO.CANDIDATES:
        try:
            c = RO.make_client(mc)
            out.append({"key": mc.key, "basis": mc.basis, "record": RO.provider_options_record(mc, c), "error": ""})
        except Exception as e:                               # noqa: BLE001
            bad += 1
            out.append({"key": mc.key, "basis": mc.basis, "record": None, "error": f"{type(e).__name__}: {str(e)[:300]}"})
        print(json.dumps(out[-1], default=str), flush=True)
    os.makedirs(SMOKE_DIR, exist_ok=True)
    json.dump({"clients": out, "generated_utc": _utc()}, open(os.path.join(SMOKE_DIR, "clients.json"), "w", encoding="utf-8"),
              indent=1, default=str)
    return 1 if bad else 0


def _smoke_checks(mc: RO.ModelConfig, u: dict) -> dict:
    """The configuration a smoke confirms: every call completed, the run is ok, the Provider_Options column is on
    every row and equals the record, the temperature the client holds, the reasoning tokens it spent."""
    chk = {"calls_complete": u["n_llm_calls"] >= u["calls_expected"], "status_ok": u["status"] == "ok",
           "temperature_sent": mc.temperature, "temperature_client": u["provider_options"].get("temperature_client"),
           "reasoning_tokens_per_call": u["reasoning_tokens"] / max(u["n_llm_calls"], 1),
           "output_tokens_per_call": u["output_tokens"] / max(u["n_llm_calls"], 1),
           "parse_status_counts": u["parse_status_counts"], "llm_errors": len(u["llm_errors"])}
    cfg = cfg_for(mc, u["cell"], "smoke")
    p = run_paths(cfg)["csv"]
    if u["status"] == "ok" and os.path.exists(p):
        df = pd.read_csv(p)
        col = df["Provider_Options"] if "Provider_Options" in df else None
        chk["provider_options_column_every_row"] = bool(col is not None and col.notna().all()
                                                        and all(json.loads(v) == json.loads(json.dumps(u["provider_options"], sort_keys=True, default=str)) for v in col))
        chk["temperature_column"] = sorted({str(v) for v in df["Temperature"]})
    return chk


def context_smoke_cells() -> tuple:
    """The context-length factor's cells (P8-7: {5, 20, 50, full} x static / memory), on E8.5's smoke path: a stateful
    call grows with its context, so each level is timed on its own before any design prices it."""
    from experiments.arms_v2 import CONTEXT_LEVELS
    return tuple({"persona": "ISFJ", "arm": arm, "scenario": "bull_trap", "seed": 2001, "rep": 0}
                 for level in CONTEXT_LEVELS for arm in CONTEXT_LEVELS[level])


def stage_smoke(configs: str, cells_kind: str = "stateless") -> int:
    if configs == "untimed":
        mcs = [c for c in RO.CANDIDATES if c.key not in RO.TIMED_IN_E8_5]
    else:
        mcs = [RO.by_key(k.strip()) for k in configs.split(",") if k.strip()]
    cells = SMOKE_CELLS if cells_kind == "stateless" else context_smoke_cells()
    kind = "smoke" if cells_kind == "stateless" else "smoke_context"
    per_model: Dict[str, int] = {}
    for mc in mcs:
        per_model[mc.model] = per_model.get(mc.model, 0) + len(cells)
    regs = [register(m, n) for m, n in per_model.items()]
    jobs = [(mc, dict(cell)) for mc in mcs for cell in cells]
    print(f"[{kind}] {len(jobs)} runs on {len(mcs)} configurations, all at once; started {_utc()}", flush=True)
    t0 = time.time()
    results = []

    def _one(job):
        mc, cell = job
        print(f"[{kind}] start {mc.key} {cell['persona']} {cell['arm']}", flush=True)
        u = run_one(mc, cell, "smoke", os.path.relpath(SMOKE_DIR, GEN) if kind == "smoke" else os.path.relpath(os.path.join(SMOKE_DIR, "context"), GEN), kind)
        u["cell"] = cell
        print(f"[smoke] {mc.key} {cell['arm']}: {u['status']} {u['seconds']:.0f}s, {u['n_llm_calls']} calls, "
              f"in {u['input_tokens']:,} out {u['output_tokens']:,} (reasoning {u['reasoning_tokens']:,}), "
              f"parse {u['parse_status_counts']}, errors {len(u['llm_errors'])} {u['error'][:160]} "
              f"[{time.time() - t0:.0f}s elapsed]", flush=True)
        return mc, u

    try:
        with ThreadPoolExecutor(max_workers=len(jobs)) as ex:
            for fu in as_completed([ex.submit(_one, j) for j in jobs]):
                results.append(fu.result())
    finally:
        for r in regs:
            unregister(r)
    by_cfg: Dict[str, list] = {}
    for mc, u in results:
        by_cfg.setdefault(mc.key, []).append({"checks": _smoke_checks(mc, u), **{k: v for k, v in u.items() if k != "calls"}})
    for key, runs in by_cfg.items():
        mc = RO.by_key(key)
        doc = {"key": key, "basis": mc.basis, "runs": runs, "pass": all(r["checks"]["status_ok"] and r["checks"]["calls_complete"]
                                                                         for r in runs), "generated_utc": _utc()}
        name = f"smoke_{mc.config_tag}_{mc.slug}.json" if kind == "smoke" else f"smoke_context_{mc.config_tag}_{mc.slug}.json"
        json.dump(doc, open(os.path.join(SMOKE_DIR, name), "w", encoding="utf-8"), indent=1, default=str)
        print(f"[{kind}] {key}: {'PASS' if doc['pass'] else 'FAIL'}", flush=True)
    return 0


# ---------------------------------------------------------------------------------------------- manifests
# The RunConfig fields a cell's `factors` can set that reach the RENDERED PROMPT (agent/v2_prompts.system_prompt and
# mandate_block).  A factor outside this set -- start_design, ordering, env_config -- changes the run but not the text
# the model sees, so it must not split the prompt-hash key: if it did, the slice manifest's fingerprint would move for
# no reason.  Track A was the first grid factor to touch the prompt, and it exposed that the key had no room for one.
PROMPT_FACTORS = ("track", "wording", "action_interface", "disclose_horizon", "cost_visible", "cost_bp", "objective",
                  "mandate_in_system", "liquidity_condition", "n_assets", "T", "placebo_version")


def prompt_factors(cell: dict) -> dict:
    """The subset of a cell's factors that changes the rendered prompt."""
    f = cell.get("factors") or {}
    return {k: f[k] for k in PROMPT_FACTORS if k in f}


def prompt_key(config_key: str, cell: dict) -> str:
    """The prompt-hash key for one cell.  Cells whose factors do not touch the prompt keep the historic three-part
    key, so manifests written before this existed keep their fingerprints unchanged."""
    pf = prompt_factors(cell)
    base = f"{config_key}|{cell['persona']}|{cell['arm']}"
    return base if not pf else base + "|" + ",".join(f"{k}={pf[k]}" for k in sorted(pf))


def fingerprint(manifest: dict) -> dict:
    """What a resumed manifest run must still be: every (configuration, persona, arm, prompt-factor) prompt hash,
    Env_Code_Hash, the harness sources.

    The probe config is built from a REAL cell of the manifest, not a synthetic one, so that the cell's
    prompt-affecting factors reach the rendered prompt and the stored hash is the hash the runs will produce."""
    from langchain_core.runnables import RunnableLambda
    from agent.v2_agent import V2Agent
    from envs.synthetic_market import SyntheticMarketEnv
    from simulation.provenance import agent_provenance, env_provenance
    out = {"prompt_hash": {}}
    # One representative cell per (persona, arm, prompt-factor signature); a signature the prompt does not depend on
    # collapses to the historic (persona, arm) pair.
    reps: Dict[tuple, dict] = {}
    for c in manifest["cells"]:
        reps.setdefault((c["persona"], c["arm"], json.dumps(prompt_factors(c), sort_keys=True)), c)
    for key in manifest["configs"]:
        mc = RO.by_key(key)
        for (p, a, _), rep in sorted(reps.items()):
            probe = {"persona": p, "arm": a, "scenario": "flat", "seed": 1}
            pf = prompt_factors(rep)
            if pf:
                probe["factors"] = pf
            cfg = cfg_for(mc, probe, manifest["subdir"])
            if cfg.context_mode != "stateless":
                continue
            ag = V2Agent(persona=cfg.persona, model_name=cfg.model_name, mandate_block=cfg.mandate_block,
                         mandate_persona=cfg.mandate_persona, wording=cfg.wording, track=cfg.track,
                         action_interface=cfg.action_interface, n_assets=cfg.n_assets, disclose_horizon=cfg.disclose_horizon,
                         T=cfg.T, cost_visible=cfg.cost_visible, cost_bp=cfg.cost_bp, objective=cfg.objective,
                         mandate_in_system=cfg.mandate_in_system, temperature=cfg.temperature,
                         liquidity_condition=cfg.liquidity_condition, llm=RunnableLambda(lambda m: None),
                         placebo_version=cfg.placebo_version)
            out["prompt_hash"][prompt_key(key, rep)] = agent_provenance(ag)["Prompt_Hash"]
    out["Env_Code_Hash"] = env_provenance(SyntheticMarketEnv("flat", T, 1))["Env_Code_Hash"]
    out["sources_sha256_lf"] = {rel: hashlib.sha256(open(os.path.join(ROOT, rel), "rb").read().replace(b"\r\n", b"\n")).hexdigest()
                                for rel in SOURCES}
    return out


def load_manifest(path: str) -> dict:
    m = json.load(open(path, encoding="utf-8"))
    for k in ("name", "kind", "subdir", "ledger_dir", "configs", "cells", "fingerprint"):
        if k not in m:
            raise SystemExit(f"manifest {path} lacks '{k}'")
    return m


def verify_fingerprint(m: dict):
    cur = fingerprint(m)
    bad = [k for k, v in m["fingerprint"]["prompt_hash"].items() if cur["prompt_hash"].get(k) != v]
    if cur["Env_Code_Hash"] != m["fingerprint"]["Env_Code_Hash"]:
        bad.append("Env_Code_Hash")
    bad += [f"source:{k}" for k, v in m["fingerprint"]["sources_sha256_lf"].items() if cur["sources_sha256_lf"].get(k) != v]
    if bad:
        raise SystemExit(f"REFUSING TO RUN: the harness no longer matches manifest {m['name']!r} for {bad}. A design that "
                         f"moved after its first batch is not the pre-registered design.")


def stage_run(manifest_path: str, config: str, workers: int, max_runs: int = 0) -> int:
    m = load_manifest(manifest_path)
    mc = RO.by_key(config)
    if mc.key not in m["configs"]:
        raise SystemExit(f"{mc.key} is not in manifest {m['name']!r}: {m['configs']}")
    verify_fingerprint(m)
    cells = m["cells"]
    T_run = int(m.get("T", T))
    have = done_keys(m["subdir"], mc, cells)
    tries: Dict[str, int] = {}
    for r in read_ledger(ledger_file(m["ledger_dir"], mc)):
        if r.get("status") != "ok":
            tries[r["run_key"]] = tries.get(r["run_key"], 0) + 1
    keyed = [(run_key(c, cfg_for(mc, c, m["subdir"])), c) for c in cells]
    pending = [c for k, c in keyed if k not in have and tries.get(k, 0) < MAX_ATTEMPTS]
    abandoned = [k for k, c in keyed if k not in have and tries.get(k, 0) >= MAX_ATTEMPTS]
    if max_runs:
        pending = pending[:max_runs]
    reg = register(mc.model, workers)
    print(f"[{m['name']}] {mc.key}: {len(cells)} runs in the manifest, {len(have)} done, {len(pending)} pending, "
          f"{len(abandoned)} abandoned after {MAX_ATTEMPTS} non-ok attempts; {workers} workers; started {_utc()}", flush=True)
    t0 = time.time(); n = 0; bad = 0
    try:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(run_one, mc, c, m["subdir"], m["ledger_dir"], m["kind"], T_run) for c in pending]
            for fu in as_completed(futs):
                u = fu.result()
                n += 1; bad += u["status"] != "ok"
                rate = n / max(time.time() - t0, 1.0)
                eta_h = (len(pending) - n) / rate / 3600 if rate > 0 else float("nan")
                print(f"[{n}/{len(pending)}] {u['run_key']} -> {u['status']} ({u['seconds']:.0f}s, fallbacks {u['n_fallbacks']}, "
                      f"errors {len(u['llm_errors'])}); non-ok so far {bad}; {rate * 3600:.1f} runs/h; ETA {eta_h:.1f} h", flush=True)
    finally:
        unregister(reg)
    return 0


def stage_status(manifest_path: str) -> int:
    m = load_manifest(manifest_path)
    for key in m["configs"]:
        mc = RO.by_key(key)
        led = read_ledger(ledger_file(m["ledger_dir"], mc))
        st = pd.Series([r["status"] for r in led]).value_counts().to_dict() if led else {}
        print(f"{key}: {len(done_keys(m['subdir'], mc, m['cells']))}/{len(m['cells'])} done; attempts {st}; in-flight "
              f"registered {inflight(mc.model)}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["check-clients", "smoke", "run", "status"])
    ap.add_argument("--configs", default="untimed")
    ap.add_argument("--cells", choices=["stateless", "context"], default="stateless")
    ap.add_argument("--config", default="")
    ap.add_argument("--manifest", default="")
    ap.add_argument("--workers", type=int, default=MAX_INFLIGHT_PER_MODEL)
    ap.add_argument("--max-runs", type=int, default=0)
    a = ap.parse_args(argv)
    if a.stage == "check-clients":
        return stage_check_clients()
    if a.stage == "smoke":
        return stage_smoke(a.configs, a.cells)
    if a.stage == "run":
        if a.workers > MAX_INFLIGHT_PER_MODEL:
            raise SystemExit(f"REFUSED: --workers {a.workers} exceeds the team's cap of {MAX_INFLIGHT_PER_MODEL} per model (P9-1)")
        return stage_run(a.manifest, a.config, a.workers, a.max_runs)
    return stage_status(a.manifest)


if __name__ == "__main__":
    raise SystemExit(main())
