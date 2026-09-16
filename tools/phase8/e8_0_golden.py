"""
v2.1 Phase 8 -- the golden record of the pre-Phase-8 behaviour (PREREG_PHASE_8.md section 7), captured from the
UNMODIFIED code before the first edit to `agent/`, `experiments/`, `tools/stats_v2.py` or `evaluation/salience.py`.

    python -m tools.phase8.e8_0_golden --write     # once, before any edit: writes tests/phase8_golden.json
    python -m tools.phase8.e8_0_golden --check     # exit 1 if the current code's defaults differ from the record

Every switch this phase adds keeps the current behaviour behind its default; `capture()` exercises only the defaults,
so `--check` (and `tests/test_v2_1_phase_8.py::test_phase8_switches_inert`) is the proof that "off" means bit for
bit.  What is recorded:

* the stateful agent (a deterministic fake LLM on a real environment's observations): for rolling (window 5 and
  20), full (budget 3,000) and summary, with and without the injected mandate, and one run with a forced parse
  fallback -- per step the sha256 of every message list the model received, the sha256 of the retained history, the
  parse status and `context_log()`;
* every mandate / placebo / wrapper block for five personas and seven wording levels, and the system prompts;
* `build_config` for every arm in the registry, and `Prompt_Hash` / `System_Prompt_Hash` for the stateless arms;
* `tools/stats_v2.run_stats`, `windowed_trend_vs_null` and `paired_sign_flip` on fixed synthetic frames;
* `evaluation/salience.salience_by_window` on a fixed synthetic frame;
* the LF-normalised sha256 of each source module at capture time (the evidence that the record predates the edits).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
from dataclasses import asdict

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

GOLDEN = os.path.join(ROOT, "tests", "phase8_golden.json")
MODULES = ("agent/stateful_agent.py", "agent/v2_agent.py", "agent/v2_prompts.py", "agent/llm_factory.py",
           "experiments/arms_v2.py", "tools/stats_v2.py", "evaluation/salience.py", "simulation/runner_v2.py")
PERSONAS = ("ISFJ", "INTJ", "ENTJ", "O1_conservative", "O2_aggressive")
WORDINGS = ("original", "rewritten", "paraphrase", "abbreviated", "no_action_clauses", "no_delimiter", "numeric_only")
KINDS = ("none", "mandate", "placebo_declarative", "placebo_directive", "wrapper_only")


def _sha(s) -> str:
    if not isinstance(s, (bytes, bytearray)):
        s = json.dumps(s, sort_keys=True, default=str).encode("utf-8") if not isinstance(s, str) else s.encode("utf-8")
    return hashlib.sha256(s).hexdigest()


def _clean(x):
    """JSON-safe, exact: floats kept by repr, numpy scalars converted, NaN kept as the string 'nan'."""
    if isinstance(x, dict):
        return {str(k): _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    if isinstance(x, (np.floating, float)):
        v = float(x)
        return "nan" if math.isnan(v) else ("inf" if math.isinf(v) and v > 0 else ("-inf" if math.isinf(v) else v))
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    return x


def _records(df: pd.DataFrame):
    return _clean(df.to_dict("records")) if df is not None else None


# --------------------------------------------------------------------------------------------- the fake LLM
def fake_llm(calls: list, unparseable_day: str = ""):
    """Deterministic: the reply depends only on the day in the last message; a summary request gets a fixed note;
    a message containing `unparseable_day` gets text no parser accepts (every retry)."""
    from langchain_core.messages import AIMessage
    from langchain_core.runnables import RunnableLambda

    def _run(messages):
        msgs = messages if isinstance(messages, list) else [messages]
        contents = [getattr(m, "content", str(m)) for m in msgs]
        calls.append(_sha(contents))
        last = contents[-1]
        if any("neutral note-taker" in c for c in contents):
            return AIMessage(content="Held mostly cash; cited stability; no trades of note.")
        if unparseable_day and unparseable_day in last:
            return AIMessage(content="I cannot decide today.")
        import re
        m = re.search(r"Day-(\d+)", last)
        k = int(m.group(1)) if m else 0
        return AIMessage(content=json.dumps({"target_cash_share": round(0.10 + 0.07 * (k % 9), 2),
                                             "rationale": f"day {k}: holding to plan"}))
    return RunnableLambda(_run)


def _observations(n: int):
    from envs.synthetic_market import SyntheticMarketEnv
    env = SyntheticMarketEnv("flat", max(n + 2, 30), 7)
    obs = env.reset()
    out = []
    for t in range(n):
        o = dict(obs)
        o["date"] = f"Day-{t + 1}"
        out.append(o)
        obs, done = env.step()
        if done:
            break
    return out


# --------------------------------------------------------------------------------------------- captures
def capture_stateful() -> dict:
    from agent.stateful_agent import StatefulV2Agent
    cases = {
        "rolling_w5_none": dict(mandate_block="none", context_mode="rolling", window=5, steps=12),
        "rolling_w5_mandate": dict(mandate_block="mandate", context_mode="rolling", window=5, steps=12),
        "rolling_w20_mandate": dict(mandate_block="mandate", context_mode="rolling", window=20, steps=24),
        "full_b3000_none": dict(mandate_block="none", context_mode="full", token_budget=3000, steps=14),
        "full_b3000_mandate": dict(mandate_block="mandate", context_mode="full", token_budget=3000, steps=14),
        "summary_none": dict(mandate_block="none", context_mode="summary", steps=22),
        "summary_mandate": dict(mandate_block="mandate", context_mode="summary", steps=22),
        "fallback_w5_mandate": dict(mandate_block="mandate", context_mode="rolling", window=5, steps=7,
                                    unparseable_day="Day-4"),
    }
    obs = _observations(24)
    out = {}
    for name, c in cases.items():
        c = dict(c)
        steps = c.pop("steps"); bad = c.pop("unparseable_day", "")
        calls: list = []
        a = StatefulV2Agent("ENTJ", "fake", llm=fake_llm(calls, bad), **c)
        if bad:
            import agent.stateful_agent as SA
            SA.time.sleep = lambda s: None          # the retry pause, not behaviour
        rec = []
        cash = 0.10
        for t in range(steps):
            port = {"cash": 10000.0 * cash, "holdings_value": 10000.0 * (1 - cash), "cash_share": cash}
            d = a.decide(obs[t], port)
            cash = float(d.target_cash_share)
            rec.append({"parse": a.last_parse_status, "log": _clean(a.context_log()),
                        "history_sha": _sha(a.history), "n_history": len(a.history)})
        out[name] = {"steps": rec, "calls": calls, "system_sha": _sha(a.full_system_prompt)}
    return out


def capture_prompts() -> dict:
    from agent import v2_prompts as P
    blocks = {}
    for kind in KINDS:
        for p in PERSONAS:
            for w in WORDINGS:
                try:
                    blocks[f"{kind}|{p}|{w}"] = _sha(P.mandate_block(kind, p, w))
                except Exception as e:                       # noqa: BLE001
                    blocks[f"{kind}|{p}|{w}"] = f"ERROR:{type(e).__name__}"
    systems = {}
    for p in PERSONAS + ("NONE",):
        for mis in (False, True):
            for track in ("A", "B"):
                try:
                    systems[f"{p}|mis={mis}|track={track}"] = _sha(P.system_prompt(p, track=track, mandate_in_system=mis))
                except Exception as e:                       # noqa: BLE001
                    systems[f"{p}|mis={mis}|track={track}"] = f"ERROR:{type(e).__name__}"
    return {"blocks": blocks, "systems": systems, "human_template": P.HUMAN_TEMPLATE_V2}


# Phase 8's declared ADDITIONS (PREREG_PHASE_8.md 7): new arms, and new RunConfig fields at their v2 default.  An
# addition is not a change to an existing behaviour; a new field at a NON-default value, or a new arm's absence from
# the registry, still shows as a difference.
PHASE8_ADDED_ARMS = ("stateful_w50_static", "stateful_w50_memory")
PHASE8_ADDED_FIELDS = {"harness_version": "v2", "placebo_version": "v2"}
# v2.1 Phase 9's declared addition (PREREG_PHASE_9.md): the provider-options field, None by default, which leaves the
# run log unchanged (tests/test_v2_1_phase_9.py::test_provider_options_column_inert)
PHASE9_ADDED_FIELDS = {"provider_options": None}
# v2.1 pre-grid additions (B3b, B2), declared here for the same reason Phase 8 and Phase 9 declared theirs.
#   phase_probe_every: REG-9's phase-restatement side call, 0 by default, which leaves the run log unchanged
#     (tests/test_v2_1_phase_8.py::test_phase_probe_off_by_default).
#   O1_conservative / O2_aggressive: the OCEAN vocabulary personas. The golden record was captured while
#     agent/prompts.py had no BASELINE_PERSONAS entry for them, so it stores "ERROR:ValueError" for every one of
#     their prompt keys; now that they resolve, those keys hold real hashes. Dropping them from BOTH sides is the
#     treatment PHASE8_ADDED_ARMS gets in capture_arms(): every other key still has to match exactly, and the new
#     personas' prompts are checked by tests/test_v2_1_phase_5.py instead.
PRE_GRID_ADDED_FIELDS = {"phase_probe_every": 0}
PRE_GRID_ADDED_PERSONAS = ("O1_conservative", "O2_aggressive")


def _drop_added_personas(doc: dict) -> dict:
    """Both sides of --check lose the declared-addition personas' prompt keys; nothing else is touched."""
    out = dict(doc)
    prompts = out.get("prompts")
    if not isinstance(prompts, dict):
        return out
    pruned = dict(prompts)
    for section in ("blocks", "systems"):
        entries = pruned.get(section)
        if isinstance(entries, dict):
            pruned[section] = {k: v for k, v in entries.items()
                               if not any(f"|{p}|" in f"|{k}|" or k.startswith(f"{p}|") or f"|{p}|" in k
                                          for p in PRE_GRID_ADDED_PERSONAS)}
    out["prompts"] = pruned
    return out


def capture_arms() -> dict:
    from experiments.arms_v2 import ARMS, build_config
    from agent.v2_agent import V2Agent
    from simulation.provenance import agent_provenance
    configs, hashes = {}, {}
    for arm in sorted(ARMS):
        if arm in PHASE8_ADDED_ARMS:
            continue
        cfg = build_config("fake", "ENTJ", arm, "crash", 3, 1)
        d = {k: v for k, v in asdict(cfg).items() if k != "agent_llm"}
        for k, default in {**PHASE8_ADDED_FIELDS, **PHASE9_ADDED_FIELDS, **PRE_GRID_ADDED_FIELDS}.items():
            if k in d and d[k] == default:
                d.pop(k)
        configs[arm] = _clean(d)
        if cfg.context_mode != "stateless":
            continue
        for persona in ("ISFJ", "INTJ", "ENTJ"):
            c = build_config("fake", persona, arm, "flat", 1, 0)
            ag = V2Agent(persona=c.persona, model_name="fake", mandate_block=c.mandate_block,
                         mandate_persona=c.mandate_persona, wording=c.wording, track=c.track,
                         action_interface=c.action_interface, n_assets=c.n_assets, disclose_horizon=c.disclose_horizon,
                         T=c.T, cost_visible=c.cost_visible, cost_bp=c.cost_bp, objective=c.objective,
                         mandate_in_system=c.mandate_in_system, temperature=c.temperature,
                         liquidity_condition=c.liquidity_condition, llm=fake_llm([]))
            prov = agent_provenance(ag)
            hashes[f"{arm}|{persona}"] = {k: prov.get(k) for k in ("Prompt_Hash", "System_Prompt_Hash")}
    return {"configs": configs, "prompt_hashes": hashes}


def _per_run_table():
    rng = np.random.default_rng(0)
    rows = []
    for m in range(6):
        base_m = rng.normal(0.3, 0.05)
        for p in ("ISFJ", "ENTJ"):
            for s in range(3):
                for arm, shift in (("static", 0.0), ("memory", -0.1 if p == "ISFJ" else 0.1)):
                    rows.append({"Model": f"m{m}", "Persona": p, "Arm": arm, "Scenario": "flat", "Seed": s,
                                 "Decode_Replicate": 0, "Crash_Discount": 0.7,
                                 "mcr_0.05": base_m + shift + rng.normal(0, 0.02),
                                 "band_mas": 0.1 + shift + rng.normal(0, 0.02), "point_mas_v2": 0.2,
                                 "rg_theta_0.05": 70.0, "return_pct": 1.0, "mdd_pct": -5.0, "turnover": 1.0,
                                 "fallback_share": 0.0, "zero_trade": False, "degenerate_rg_v1": True})
    return pd.DataFrame(rows)


def _per_step_table():
    rng = np.random.default_rng(1)
    rows = []
    for arm in ("memory", "stateful_memory"):
        for seed in range(4):
            y = 0.2
            for day in range(1, 201):
                y = 0.9 * y + rng.normal(0, 0.02) + (0.0002 * day if arm == "stateful_memory" else 0.0)
                rows.append({"Model": "m0", "Persona": "ISFJ", "Arm": arm, "Scenario": "flat", "Seed": seed,
                             "Decode_Replicate": 0, "Day": day, "band_mas_t": y, "Phase": "calm"})
    return pd.DataFrame(rows)


def capture_stats() -> dict:
    from tools import stats_v2 as S
    with tempfile.TemporaryDirectory() as td:
        t = S.run_stats(_per_run_table(), os.path.join(td, "stats"))
    ps = _per_step_table()
    return {"contrasts": _records(t["contrasts"]), "mixedlm": _records(t["mixedlm"]),
            "degeneracy": _records(t["degeneracy"]),
            "trend_circular": _clean(S.windowed_trend_vs_null(ps[ps.Arm == "stateful_memory"], n_perm=99, seed=3)),
            "trend_perm": _clean(S.windowed_trend_vs_null(ps[ps.Arm == "stateful_memory"], n_perm=99, seed=3, null="perm")),
            "sign_flip": _clean(S.paired_sign_flip(ps, n_perm=199, seed=4)),
            "bh": _clean(list(S.bh_adjust(np.array([0.01, 0.04, 0.03, 0.5, 0.002])))),
            "cliffs": S.cliffs_delta([1, 2, 3, 4], [2, 2, 5]), "hedges": S.hedges_g([1, 2, 3, 4], [2, 2, 5])}


def _salience_frame():
    from evaluation.targets import centre
    from evaluation.salience import MARKET_FEATURES
    rng = np.random.default_rng(2)
    rows = []
    for p in ("ISFJ", "ENTJ"):
        for arm, mb in (("static", "none"), ("memory", "mandate")):
            for seed in range(4):
                for day in range(1, 51):
                    r = {"Model": "m0", "Persona": p, "Arm": arm, "Mandate_Block": mb, "Mandate_Persona": p,
                         "Seed": seed, "Decode_Replicate": 0, "Day": day, "Start_Design": "target",
                         "Start_Cash_Share": centre(p)}
                    for f in MARKET_FEATURES:
                        r[f] = rng.normal()
                    r["Target_Cash_Share"] = float(np.clip(centre(p) + 0.05 * r["obs_RSI14"] + rng.normal(0, 0.05), 0, 1))
                    r["Cash_Share"] = r["Target_Cash_Share"]
                    rows.append(r)
    return pd.DataFrame(rows)


def capture_salience() -> dict:
    """Under joblib's sequential backend: `surrogate_shares` hard-codes n_jobs=2, and two workers sum the forest's
    tree predictions in a varying order, so the unmodified code differs from itself at the last bit (1e-17..1e-14,
    observed on the first capture). The backend changes the order of a float sum, not the statistic."""
    from joblib import parallel_config
    from evaluation.salience import salience_by_window
    with parallel_config(backend="sequential"):
        out = salience_by_window(_salience_frame(), window=25, null_reps=1, n_estimators=20, n_repeats=2)
    return {"salience_by_window": _records(out)}


def source_hashes() -> dict:
    out = {}
    for rel in MODULES:
        with open(os.path.join(ROOT, rel), "rb") as fh:
            out[rel] = hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()
    return out


def capture() -> dict:
    return {"stateful": capture_stateful(), "prompts": capture_prompts(), "arms": capture_arms(),
            "stats": capture_stats(), "salience": capture_salience()}


def diff(a, b, path="") -> list:
    """Paths at which two captures differ (exact; 'nan' equals 'nan')."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}/{k}: present in only one")
            else:
                out += diff(a[k], b[k], f"{path}/{k}")
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path}: length {len(a)} != {len(b)}"]
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff(x, y, f"{path}[{i}]")
        return out
    return [] if a == b else [f"{path}: {a!r} != {b!r}"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    cur = _clean(capture())
    if a.write:
        if os.path.exists(GOLDEN):
            print(f"{GOLDEN} exists; the golden record is written once, before the first edit. Refusing.")
            return 1
        import subprocess
        doc = {"_note": "Phase 8 golden record of the pre-Phase-8 defaults (PREREG_PHASE_8.md section 7); written by "
                        "tools/phase8/e8_0_golden.py --write before the first edit. Never regenerated.",
               "_captured_utc": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
               "_git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
               "_source_sha256_lf": source_hashes(), **cur}
        with open(GOLDEN, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, indent=1, sort_keys=True)
        print(f"written {os.path.relpath(GOLDEN, ROOT)}")
        return 0
    with open(GOLDEN, "r", encoding="utf-8") as fh:
        ref = json.load(fh)
    ref = {k: v for k, v in ref.items() if not k.startswith("_")}
    d = diff(_drop_added_personas(ref), _drop_added_personas(cur))
    print(f"{len(d)} differences from the golden record")
    for x in d[:40]:
        print("  ", x)
    return 1 if d else 0


if __name__ == "__main__":
    raise SystemExit(main())
