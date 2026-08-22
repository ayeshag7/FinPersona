"""
Regenerate the paper's Table 2 (agent observation space) FROM CODE.

For every column the generator produces, the table states
  - whether it is in the internal DataFrame (env.data),
  - whether get_observation() exposes it to the agent (and with what rounding),
  - whether the static / memory prompt actually renders it (from agent/render.py),
  - the definition (curated text keyed by column; the script fails if a column
    produced by the generator has no definition, which forces the table and the
    code to stay in sync),
plus the portfolio-state fields the prompt renders and the hidden fields.

Usage:  python -m tools.gen_table2 [--env v1|v2] [--out docs/env_v2/generated]
Writes  table2_<env>_from_code.md and .tex and rendered_prompt_<env>_<agent>.txt
"""
from __future__ import annotations

import argparse
import inspect
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from agent.render import (render_full_human_message, rendered_market_fields,
                          rendered_portfolio_fields)
from simulation.provenance import env_provenance, text_hash

# ---------------------------------------------------------------------------
# Curated definitions for the v1 generator, keyed by DataFrame column.
# Line references are to envs/v1/synthetic_market_v1.py (== tag v1-env-freeze).
# ---------------------------------------------------------------------------
V1_DEFINITIONS = {
    "day": ("Index", "Trading-day index 1..T. Shown to the agent as the string 'Day-N' under the key 'date'; T itself is never disclosed.", "l.182, l.310"),
    "price": ("Price action", "Observable market price P_t. flat: V_t + N(0, 0.5)*phi_t (additive dollars, phi_t the 'GARCH-like' regime); bull_trap: phase-1 V_t+N(0,1) floored at 1; phase-2 cumulative N(1.5,0.5) dollar drift floored at the phase-1 exit; phase-3 cumulative N(0.5,2.5) floored at 1.05x mania entry; crash: delta*V_t + N(0,1.5), capped at 0.98 V_t from phase 2 onward, floored at 1.", "l.83-100, l.130-143, l.170-171"),
    "fundamental_value": ("Hidden", "Fundamental value V_t (ground truth, never rendered). flat: GBM with mu=0.0005, sigma=0.02; bull_trap: three-phase log-random walk (N(0.001,0.01), N(0,0.002), N(-0.0005,0.002)); crash: linear -12 dollars over phase 1 + N(0,0.5), then cumulative N(-0.5,1.0), then N(0.02,0.5), floored at 10.", "l.69-79, l.114-123, l.156-159"),
    "implied_volatility": ("Risk", "15 x phi_t (percent). phi_t is a deterministic per-phase linspace in bull_trap (1 -> 1.5 -> 2.5) and crash (1 -> 1.5 -> 3 -> 2), identical across seeds; in flat phi_t = 0.7 phi_{t-1} + 0.3 |N(0,1)| floored at 0.5. Not a forecast of realised volatility.", "l.105-109, l.146-150, l.162-168, l.188"),
    "volume": ("Liquidity", "1e6 x (1 + 0.5 U(0,1)) i.i.d., times a deterministic phase multiplier (bull_trap: 1, 1 -> 3, 3 -> 5; crash: 1, 2 -> 4, 1.5 -> 1; flat: none).", "l.191-209"),
    "news_sentiment": ("Sentiment", "i.i.d. N(0, 0.3); N(0.7, 0.2) from bull_trap phase 2 onward; N(-0.8, 0.2) in crash phase 2; clipped to [-1, 1]. No autocorrelation, no link to returns; the phase shift is a phase clock.", "l.212-219"),
    "sentiment_MA5": ("Sentiment", "5-day rolling mean of news_sentiment.", "l.222"),
    "sentiment_change": ("Sentiment", "news_sentiment minus sentiment_MA5.", "l.223"),
    "earnings_per_share": ("Valuation (internal)", "EPS_t = V_t / 15 every day (floored at 0.01). Never rendered directly, but P/E and dividend yield are exact functions of it, so V_t = 15 P_t / PE_t (audit F-1).", "l.230-231"),
    "reported_PE": ("Valuation", "P_t / EPS_t = 15 P_t / V_t, capped at 200. Algebraically inverts to V_t.", "l.237-239"),
    "dividend_yield": ("Valuation", "(0.4 EPS_t / max(P_t, 0.10)) x 100 = 40 V_t / (15 P_t) percent. Also inverts to V_t.", "l.245-246"),
    "SMA20": ("Trend", "Simple moving average of price over min(20, max(5, T//5)) days (20 at T >= 100), min_periods=1.", "l.250, l.256, l.260"),
    "SMA60": ("Trend", "Mislabelled: the long SMA is min(50, max(10, T//2)) days (50 at T >= 100), stored under the key 'SMA60' and rendered as 'SMA20/60'.", "l.251, l.257, l.261"),
    "SMA50": ("Trend", "Same series as SMA60 under its correct name (only present when T >= 100).", "l.257"),
    "trend_strength": ("Trend", "(SMA20 - SMA_long) / SMA_long x 100.", "l.265-267"),
    "trend_regime": ("Trend", "1 if trend_strength > 2, -1 if < -2, else 0.", "l.271-272"),
    "volume_SMA20": ("Liquidity (internal)", "Rolling mean of volume over the short SMA window.", "l.275"),
    "volume_ratio": ("Liquidity", "volume / volume_SMA20.", "l.278"),
    "RSI14": ("Momentum", "Cutler RSI (simple 14-day means of gains and losses), NaN -> 50 for the first 14 days.", "l.281-286"),
    "MACD": ("Momentum", "EMA12 - EMA26 of price; no signal line.", "l.289-291"),
}
V1_PORTFOLIO_DEFS = {
    "cash": "Cash balance in dollars after the previous day's trade (initial 10,000 for every run).",
    "holdings_value": "Mark-to-market value of shares held (initial 0 for every run).",
}
V1_OBS_ROUNDING = {  # from get_observation()
    "date": "string 'Day-N'", "price": "2 dp", "SMA20": "2 dp", "SMA60": "2 dp", "RSI14": "1 dp",
    "MACD": "4 dp", "volume": "int", "volume_ratio": "2 dp", "news_sentiment": "2 dp",
    "sentiment_MA5": "2 dp", "sentiment_change": "2 dp", "implied_volatility": "1 dp",
    "reported_PE": "1 dp", "dividend_yield": "2 dp", "trend_strength": "2 dp", "trend_regime": "int",
}


def _load_env(version: str, scenario: str, T: int, seed: int):
    if version == "v1":
        from envs.v1.synthetic_market_v1 import SyntheticMarketEnv
        return SyntheticMarketEnv(scenario=scenario, n_days=T, seed=seed)
    from envs.synthetic_market import SyntheticMarketEnv  # v2 once it lands
    return SyntheticMarketEnv(scenario=scenario, n_days=T, seed=seed)


def _definitions(version: str):
    if version == "v1":
        return V1_DEFINITIONS, V1_PORTFOLIO_DEFS, V1_OBS_ROUNDING
    try:
        from envs.synthetic_market import TABLE2_DEFINITIONS, TABLE2_PORTFOLIO_DEFS, TABLE2_OBS_ROUNDING
        return TABLE2_DEFINITIONS, TABLE2_PORTFOLIO_DEFS, TABLE2_OBS_ROUNDING
    except ImportError as exc:
        raise SystemExit("v2 generator must export TABLE2_DEFINITIONS / TABLE2_PORTFOLIO_DEFS / "
                         "TABLE2_OBS_ROUNDING") from exc


def build_rows(version: str, T: int = 200, seed: int = 42):
    defs, pdefs, rounding = _definitions(version)
    envs = {s: _load_env(version, s, T, seed) for s in ("flat", "bull_trap", "crash")}
    env = envs["flat"]
    df_cols = []
    for e in envs.values():
        for c in e.data.columns:
            if c not in df_cols:
                df_cols.append(c)
    obs_keys = list(env.get_observation().keys())
    # key 'date' maps to column 'day'
    col_of_key = {k: ("day" if k == "date" else k) for k in obs_keys}
    if version == "v1":
        static_fields = rendered_market_fields("static")
        memory_fields = rendered_market_fields("memory")
    else:  # v2: every observation key is rendered (contract); the arms differ only in the mandate block
        static_fields = memory_fields = list(obs_keys)
    missing = [c for c in df_cols if c not in defs]
    if missing:
        raise SystemExit(f"Table 2 definitions missing for generator columns: {missing}")
    rows = []
    for c in df_cols:
        cat, definition, ref = defs[c]
        keys = [k for k, col in col_of_key.items() if col == c]
        key = keys[0] if keys else ""
        rows.append({
            "column": c, "obs_key": key, "category": cat, "definition": definition,
            "in_dataframe": True, "in_observation": bool(keys),
            "rounding": rounding.get(key, "") if keys else "",
            "rendered_static": key in static_fields if keys else False,
            "rendered_memory": key in memory_fields if keys else False,
            "code_ref": ref,
        })
    prows = [{"field": f, "definition": pdefs[f],
              "rendered_static": f in rendered_portfolio_fields("static"),
              "rendered_memory": f in rendered_portfolio_fields("memory")} for f in pdefs]
    return rows, prows, envs


def write_outputs(version: str, out_dir: str, T: int = 200, seed: int = 42):
    os.makedirs(out_dir, exist_ok=True)
    rows, prows, envs = build_rows(version, T, seed)
    env = envs["flat"]
    prov = env_provenance(env)
    yes = lambda b: "yes" if b else "no"

    # ---- Markdown ----
    md = [f"# Table 2 regenerated from code (generator {version}, T={T}, seed={seed})", "",
          f"Generated by `python -m tools.gen_table2 --env {version}`. Env code hash `{prov['Env_Code_Hash']}`, "
          f"generator config hash `{prov['Gen_Config_Hash']}`.", "",
          "Columns: *in obs* = returned by `get_observation()`; *static / memory prompt* = actually rendered into the "
          "human message by `agent/render.py` (verified byte-identical to the v1 agents at tag `v1-env-freeze`).", "",
          "| Category | DataFrame column | obs key | In obs (rounding) | Static prompt | Memory prompt | Definition (code) | Code ref |",
          "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        inobs = f"yes ({r['rounding']})" if r["in_observation"] else "no"
        md.append(f"| {r['category']} | `{r['column']}` | `{r['obs_key']}` | {inobs} | {yes(r['rendered_static'])} | "
                  f"{yes(r['rendered_memory'])} | {r['definition']} | {r['code_ref']} |")
    md += ["", "## Portfolio state rendered in the prompt (absent from the paper's Table 2)", "",
           "| Field | Static prompt | Memory prompt | Definition |", "|---|---|---|---|"]
    for p in prows:
        md.append(f"| `{p['field']}` | {yes(p['rendered_static'])} | {yes(p['rendered_memory'])} | {p['definition']} |")
    n_obs = sum(r["in_observation"] for r in rows)
    n_static = sum(r["rendered_static"] for r in rows)
    shown = [r["obs_key"] for r in rows if r["rendered_static"]]
    unshown = [r["obs_key"] for r in rows if r["in_observation"] and not r["rendered_static"]]
    md += ["", "## Summary", "",
           f"- Generator columns: {len(rows)}; exposed by get_observation(): {n_obs}; rendered into the prompt: {n_static}.",
           f"- Rendered market fields: {', '.join('`'+k+'`' for k in shown)}.",
           f"- Exposed but NEVER rendered: {', '.join('`'+k+'`' for k in unshown)}.",
           "- Rendered portfolio fields: " + ", ".join('`'+p['field']+'`' for p in prows if p['rendered_static']) + ".",
           "- The memory prompt renders the same market and portfolio fields as the static prompt, plus the "
           "`*** ACTIVE MEMORY REFRESH ***` block containing the persona's core mandate.",
           ""]
    with open(os.path.join(out_dir, f"table2_{version}_from_code.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(md))

    # ---- LaTeX (booktabs) ----
    def tex_esc(s):
        return (s.replace("\\", "\\textbackslash{}").replace("&", "\\&").replace("%", "\\%")
                 .replace("_", "\\_").replace("#", "\\#").replace("$", "\\$").replace("^", "\\^{}")
                 .replace("{", "\\{").replace("}", "\\}").replace("~", "\\~{}")
                 .replace("<", "$<$").replace(">", "$>$").replace("|", "$|$"))
    tex = ["% Auto-generated by tools/gen_table2.py -- do not edit by hand",
           "\\begin{table}[t]\\centering\\small",
           "\\begin{tabular}{llp{0.42\\linewidth}ccc}\\toprule",
           "Category & Variable & Definition / generation logic & In obs. & Static prompt & Memory prompt \\\\ \\midrule"]
    for r in rows:
        tex.append(f"{tex_esc(r['category'])} & \\texttt{{{tex_esc(r['obs_key'] or r['column'])}}} & "
                   f"{tex_esc(r['definition'])} & {yes(r['in_observation'])} & {yes(r['rendered_static'])} & "
                   f"{yes(r['rendered_memory'])} \\\\")
    tex.append("\\midrule")
    for p in prows:
        tex.append(f"Portfolio & \\texttt{{{tex_esc(p['field'])}}} & {tex_esc(p['definition'])} & -- & "
                   f"{yes(p['rendered_static'])} & {yes(p['rendered_memory'])} \\\\")
    tex += ["\\bottomrule\\end{tabular}",
            f"\\caption{{Agent observation space $O_t$ regenerated from code (generator {version}). "
            "`In obs.' = exposed by \\texttt{get\\_observation()}; prompt columns = rendered into the human message. "
            "Fundamental value is hidden and used only by the evaluation layer.}",
            "\\label{tab:obs_space}", "\\end{table}"]
    with open(os.path.join(out_dir, f"table2_{version}_from_code.tex"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(tex))

    # ---- Rendered prompts, verbatim (day 7 of the flat scenario) ----
    for _ in range(6):
        env.step()
    obs = env.get_observation()
    portfolio = {"cash": 10000.0, "holdings_value": 0.0}
    hashes = {}
    for agent_type in ("static", "memory"):
        mandate = ("REMINDER: You are a GUARDIAN INVESTOR. Your goal is SECURITY. Protect the principal. "
                   "Avoid volatility. Buy insurance (puts/hedges). Do not take unnecessary risks. SLEEP WELL AT NIGHT.")
        if version == "v1":
            text = render_full_human_message(agent_type, obs, portfolio, core_mandate=mandate if agent_type == "memory" else "")
        else:
            from agent.render import render_v2_input
            text = render_v2_input(obs, {"cash": 8000.0, "holdings_value": 2000.0, "cash_share": 0.8})
            if agent_type == "memory":
                text += "\n\n*** ACTIVE MEMORY REFRESH *** (mandate block, E3)"
        path = os.path.join(out_dir, f"rendered_prompt_{version}_{agent_type}.txt")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# Human message as sent by the " + agent_type + " agent (system prompt = persona text, see "
                     "agent/prompts.py + mbti_profiles.json). {format_instructions} is the PydanticOutputParser text.\n")
            fh.write(text)
        hashes[agent_type] = text_hash(text)
    json.dump({"rows": rows, "portfolio": prows, "provenance": prov, "sample_prompt_hashes": hashes},
              open(os.path.join(out_dir, f"table2_{version}_from_code.json"), "w", encoding="utf-8"), indent=1)
    return rows, prows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="v1", choices=["v1", "v2"])
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "env_v2", "generated"))
    ap.add_argument("--T", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    rows, prows = write_outputs(a.env, a.out, a.T, a.seed)
    print(f"Table 2 ({a.env}): {len(rows)} generator columns, "
          f"{sum(r['in_observation'] for r in rows)} in observation, "
          f"{sum(r['rendered_static'] for r in rows)} rendered; written to {a.out}")
