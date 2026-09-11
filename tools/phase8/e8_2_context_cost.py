"""
v2.1 Phase 8 -- E8.2: the cost of the context-length factor's levels for Phase 9's grid (PREREG_PHASE_8.md 2), from
the pilot's MEASURED context growth, not an estimate.

    python -u -m tools.phase8.e8_2_context_cost

Inputs, each from a file:
* per retained turn, in the provider's unit: (`Context_Tokens` on day 21 − day 1) / 20, averaged over the pilot's three
  `stateful_memory` runs (`results_v2_pilot/stateful/`); the day-1 context likewise;
* the replayed block's share of a retained turn's characters (the logged `chars/4` offset grows by one turn's
  characters per day until the window fills) -- removed under `harness="v2_1"` (E8.1(b));
* output tokens per call: E8.5's smoke usage (`e8_5/smoke.json`) when present, else the plan's 120 (labelled);
* prices: plan 0.4 (read 26–27 Aug 2026), no caching discount.

Per run, input tokens = Σ_{t=1..200} (day-1 context + min(t − 1, K) × per-turn tokens), K = the window, or for
`full` the turns that fit the 60,000-token budget in the harness's own count (chars/4 under v2; o200k under v2_1).
The summary arm keeps 5 raw turns plus a ≤ 1,200-character summary and adds 20 summariser calls.  A Tier-A-shaped
block is 3 personas × 2 arms × 3 scenarios × 5 seeds × 1 replicate = 90 runs per level.

Output: docs/env_v2/generated/v2_1/e8_2/context_cost.{json,md}
"""
from __future__ import annotations

import glob
import json
import os
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e8_2")
T = 200
BUDGET = 60000
PRICES = {"gemini-2.5-flash": (0.30, 2.50), "gpt-5-mini": (0.25, 2.00)}
TIER_A_RUNS = 3 * 2 * 3 * 5 * 1
LEVELS = [("stateless", 0), ("rolling 5", 5), ("rolling 20", 20), ("rolling 50", 50), ("full (60k)", "full"),
          ("summary (5 raw)", "summary")]


def main():
    import tiktoken
    enc = tiktoken.get_encoding("o200k_base")
    runs = []
    for f in sorted(glob.glob(os.path.join(ROOT, "results_v2_pilot", "stateful", "*", "*", "*", "*stateful_memory*.csv"))):
        d = pd.read_csv(f).set_index("Day")
        meta = json.load(open(f.replace(".csv", ".meta.json"), encoding="utf-8"))
        block = meta["mandate_block_text"]
        per_turn_prov = (d.loc[21, "Context_Tokens"] - d.loc[1, "Context_Tokens"]) / 20.0
        per_turn_chars = (d.loc[21, "Mandate_Offset_Tokens"] - d.loc[1, "Mandate_Offset_Tokens"]) * 4 / 20.0
        runs.append({"persona": d["Persona"].iloc[0], "day1_provider": float(d.loc[1, "Context_Tokens"]),
                     "per_turn_provider_v2": per_turn_prov, "per_turn_chars_v2": per_turn_chars,
                     "block_chars": len(block), "block_share_of_turn_chars": len(block) / per_turn_chars,
                     "provider_tokens_per_char": per_turn_prov / per_turn_chars,
                     "stateless_calls_total_provider_input": float(d["Context_Tokens"].sum())})
    r = pd.DataFrame(runs)
    base = float(r.day1_provider.mean())
    pt_v2 = float(r.per_turn_provider_v2.mean())
    share = float(r.block_share_of_turn_chars.mean())
    pt_v21 = pt_v2 * (1 - share)
    chars_turn_v2 = float(r.per_turn_chars_v2.mean())
    chars_turn_v21 = chars_turn_v2 * (1 - share)
    # the o200k tokens of ONE retained turn, measured on the harness's own rendering (a retained turn is mostly numbers
    # and JSON, so the chars-per-token of prose would overstate how many turns fit): a human turn rendered without the
    # block (bull_trap, seed 2001, day 1, ISFJ) plus a reply carrying the pilot's median-length rationale
    from langchain_core.runnables import RunnableLambda
    from agent.stateful_agent import StatefulV2Agent
    from envs.synthetic_market import SyntheticMarketEnv
    env = SyntheticMarketEnv("bull_trap", T, 2001)
    o = env.reset()
    ag = StatefulV2Agent("ISFJ", "fake", mandate_block="mandate", harness="v2_1", llm=RunnableLambda(lambda m: None))
    human_tok = len(enc.encode(ag._human_without_block(o, {"cash": 8000.0, "holdings_value": 2000.0, "cash_share": 0.8})))
    rat = pd.concat([pd.read_csv(f)["Rationale"] for f in glob.glob(os.path.join(ROOT, "results_v2_pilot", "stateful", "*", "*", "*", "*stateful_memory*.csv"))])
    med = rat.iloc[(rat.str.len() - rat.str.len().median()).abs().argsort().iloc[0]]
    ai_tok = len(enc.encode(json.dumps({"target_cash_share": 0.8, "rationale": med})))
    turn_o200k_v21 = human_tok + ai_tok
    chars_per_o200k = chars_turn_v21 / turn_o200k_v21
    k_full = {"v2": int(BUDGET // (chars_turn_v2 / 4)), "v2_1": int(BUDGET // turn_o200k_v21)}
    smoke = os.path.join(GEN, "e8_5", "smoke.json")
    out_per_call = {}
    for m in PRICES:
        out_per_call[m] = {"value": 120.0, "source": "plan assumption (smoke not available)"}
    if os.path.exists(smoke):
        sj = json.load(open(smoke, encoding="utf-8"))
        man_path = os.path.join(GEN, "e8_5", "manifest.json")
        budgets = json.load(open(man_path, encoding="utf-8")).get("thinking_budget", {}) if os.path.exists(man_path) else {}
        for which, blk in sj["per_design"].items():
            v = blk.get("output_tokens_per_call")
            if v is not None and np.isfinite(v):
                tb = budgets.get(blk["model"], "provider default")
                cfg = "thinking off" if tb == 0 else "provider-default thinking"
                out_per_call[blk["model"]] = {"value": float(v), "source": f"e8_5/smoke.json, billed usage, {cfg}"}

    def input_tokens(level, per_turn, k_full_h):
        if level == 0:
            return base * T
        if level == "summary":
            summ = 1200 * float(r.provider_tokens_per_char.mean())      # <= 1,200 characters, in provider units
            return sum(base + min(t, 5) * per_turn + (summ if t >= 10 else 0) for t in range(T))
        k = k_full_h if level == "full" else level
        return sum(base + min(t, k) * per_turn for t in range(T))

    rows = []
    for harness, pt, kf in (("v2", pt_v2, k_full["v2"]), ("v2_1", pt_v21, k_full["v2_1"])):
        for name, level in LEVELS:
            tin = input_tokens(level, pt, kf)
            calls = T + (T // 10 if level == "summary" else 0)
            row = {"harness": harness, "level": name, "calls_per_run": calls, "input_tokens_per_run": tin,
                   "retained_turns_at_plateau": (0 if level == 0 else (5 if level == "summary" else (kf if level == "full" else level)))}
            for m, (pin, pout) in PRICES.items():
                oc = out_per_call[m]["value"]
                usd = tin / 1e6 * pin + calls * oc / 1e6 * pout
                row[f"usd_per_run_{m}"] = usd
                row[f"usd_tierA_block_{m}"] = usd * TIER_A_RUNS
            rows.append(row)
    t = pd.DataFrame(rows)
    ref = t[t.level == "stateless"].set_index("harness")
    for m in PRICES:
        t[f"x_stateless_{m}"] = t.apply(lambda x: x[f"usd_per_run_{m}"] / ref.loc[x["harness"], f"usd_per_run_{m}"], axis=1)
    os.makedirs(OUT, exist_ok=True)
    doc = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "n_pilot_runs": int(len(r)),
           "pilot_runs": json.loads(r.to_json(orient="records")), "day1_context_provider": base,
           "per_turn_provider_v2": pt_v2, "block_share_of_turn": share, "per_turn_provider_v2_1": pt_v21,
           "full_budget_turns": k_full, "chars_per_o200k_token": chars_per_o200k,
           "output_tokens_per_call": out_per_call, "tier_a_runs_per_level": TIER_A_RUNS, "prices_per_M": PRICES,
           "table": json.loads(t.to_json(orient="records"))}
    json.dump(doc, open(os.path.join(OUT, "context_cost.json"), "w", encoding="utf-8"), indent=1)
    L = ["# E8.2 — the cost of the context-length levels (per run and per Tier-A-shaped block of 90 runs)", "",
         f"From the pilot's measured growth (n = {len(r)} stateful runs): day-1 context {base:,.0f} provider tokens; "
         f"{pt_v2:,.1f} per retained turn under v2, {pt_v21:,.1f} under v2_1 (the replayed block was {share:.1%} of a turn). "
         f"The 60,000-token budget holds {k_full['v2']} turns under v2 (chars/4) and {k_full['v2_1']} under v2_1 (o200k). "
         f"Output tokens per call: " + "; ".join(f"{m} {v['value']:.0f} ({v['source']})" for m, v in out_per_call.items()) + ".", "",
         "| harness | level | calls / run | input tokens / run | turns at plateau | Flash $ / run | Flash $ / 90 runs | × stateless | GPT-5 mini $ / run | GPT-5 mini $ / 90 runs |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for _, x in t.iterrows():
        L.append(f"| {x['harness']} | {x['level']} | {x['calls_per_run']} | {x['input_tokens_per_run']:,.0f} | {x['retained_turns_at_plateau']} | "
                 f"{x['usd_per_run_gemini-2.5-flash']:.3f} | {x['usd_tierA_block_gemini-2.5-flash']:.2f} | {x['x_stateless_gemini-2.5-flash']:.1f} | "
                 f"{x['usd_per_run_gpt-5-mini']:.3f} | {x['usd_tierA_block_gpt-5-mini']:.2f} |")
    with open(os.path.join(OUT, "context_cost.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
