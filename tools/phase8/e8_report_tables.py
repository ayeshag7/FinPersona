"""
v2.1 Phase 8 -- every report table generated from its file into a marked block (rule 15; the Phase-7 pattern).

    python -m tools.phase8.e8_report_tables            # rewrite the blocks of PHASE_8_REPORT.md from the files
    python -m tools.phase8.e8_report_tables --check    # exit 1 if any block differs from what the files give

Blocks: <!-- table:NAME --> ... <!-- /table:NAME -->.  A block whose file is absent is left alone and reported as
"no file", not as a mismatch.  `tests/test_v2_1_phase_8.py::test_phase8_report_tables_match_files` runs `--check`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Optional

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
REPORT = os.path.join(ROOT, "docs", "env_v2", "v2_1", "PHASE_8_REPORT.md")


def _j(rel):
    p = os.path.join(GEN, rel)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _c(rel):
    p = os.path.join(GEN, rel)
    return pd.read_csv(p) if os.path.exists(p) else None


def _f(x, nd=4):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    return f"{float(x):.{nd}f}"


def _ci(p, lo, hi, nd=3):
    return f"{_f(p, nd)} [{_f(lo, nd)}, {_f(hi, nd)}]"


# ------------------------------------------------------------------------------------------------ E8.1
def t_pilot_offsets() -> Optional[str]:
    t = _c("e8_1/pilot_offsets.csv"); d = _j("e8_1/pilot_offsets.json")
    if t is None or d is None:
        return None
    L = [f"From the pilot's three `stateful_memory` logs (`results_v2_pilot/stateful/`, flat, seed 42, rolling 20). "
         f"The format instructions after the injected block: {d['format_instructions_chars']:,} characters, "
         f"{d['tail_o200k']} o200k tokens with the separator.", "",
         "| persona | day | turns | v2 offset as logged (chars/4, system copy) | v2_1 system-copy offset (chars/4) | "
         "v2_1 nearest copy (chars/4 / o200k) | logged ÷ nearest | copies v2 → v2_1 | Context_Tokens logged (provider) | "
         "chars/4 of the same context | v2_1 context, est. |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in t[t.day.isin([1, 20, 21, 200])].iterrows():
        L.append(f"| {r.persona} | {int(r.day)} | {int(r.context_turns)} | {int(r.v2_offset_system_logged_chars4):,} | "
                 f"{r.v21_offset_system_chars4:,.0f} | {int(r.v21_offset_nearest_chars4)} / {int(r.v21_offset_nearest_o200k)} | "
                 f"{r.ratio_logged_over_nearest_chars4:.1f} | {int(r.copies_v2)} → {int(r.copies_v21)} | "
                 f"{int(r.context_tokens_logged):,} | {int(r.context_chars4_of_same_context):,} | {r.v21_context_tokens_est:,.0f} |")
    s = d["summary"]
    L += ["", f"Day 200, n = {d['n_runs']} runs: logged {s['logged_offset_day200_range'][0]:,}–{s['logged_offset_day200_range'][1]:,} "
              f"against a nearest copy {s['nearest_offset_chars4']} (chars/4) / {s['nearest_offset_o200k']} (o200k) away — "
              f"**{s['ratio_logged_over_nearest_day200'][0]:.1f}–{s['ratio_logged_over_nearest_day200'][1]:.1f}× too large**; "
              f"the replayed blocks were **{s['replayed_block_share_of_context_day200']:.1%}** of the context's characters."]
    return "\n".join(L)


def t_placebo() -> Optional[str]:
    d = _j("e8_1/placebo_matching.json")
    if d is None:
        return None
    L = ["| persona | placebo version | words real / placebo (rel. diff) | within 10 % | imperatives real / placebo | equal | both |",
         "|---|---|---|---|---|---|---|"]
    for r in d["rows"]:
        L.append(f"| {r['persona']} | {r['placebo_version']} | {r['words_real']} / {r['words_placebo']} ({r['word_rel_diff']:.3f}) | "
                 f"{'yes' if r['words_pass'] else '**no**'} | {r['imperatives_real']} / {r['imperatives_placebo']} | "
                 f"{'yes' if r['imperatives_pass'] else '**no**'} | {'**PASS**' if r['pass'] else '**FAIL**'} |")
    L += ["", f"v2 placebo: **{d['v2_pass_count']} of 3** personas matched; matched v2_1 placebo: **{d['v2_1_pass_count']} of 3**."]
    return "\n".join(L)


# ------------------------------------------------------------------------------------------------ E8.2
def t_context_cost() -> Optional[str]:
    d = _j("e8_2/context_cost.json")
    if d is None:
        return None
    oc = "; ".join(f"{m} {v['value']:.0f} ({v['source']})" for m, v in d["output_tokens_per_call"].items())
    L = [f"Measured growth, n = {d['n_pilot_runs']} pilot stateful runs: day-1 context {d['day1_context_provider']:,.0f} provider "
         f"tokens; {d['per_turn_provider_v2']:,.1f} per retained turn (v2), {d['per_turn_provider_v2_1']:,.1f} (v2_1). "
         f"The 60,000-token budget holds {d['full_budget_turns']['v2']} turns (v2) / {d['full_budget_turns']['v2_1']} (v2_1). "
         f"Output tokens per call: {oc}. Prices per M input/output: "
         + "; ".join(f"{m} ${p[0]:.2f} / ${p[1]:.2f}" for m, p in d["prices_per_M"].items()) + " (plan 0.4; no caching).", "",
         "| harness | level | calls / run | input tokens / run | turns at plateau | Flash $ / run | Flash $ / 90 runs | × stateless | GPT-5 mini $ / run | GPT-5 mini $ / 90 runs |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for x in d["table"]:
        L.append(f"| {x['harness']} | {x['level']} | {x['calls_per_run']} | {x['input_tokens_per_run']:,.0f} | {x['retained_turns_at_plateau']} | "
                 f"{x['usd_per_run_gemini-2.5-flash']:.3f} | {x['usd_tierA_block_gemini-2.5-flash']:.2f} | {x['x_stateless_gemini-2.5-flash']:.1f} | "
                 f"{x['usd_per_run_gpt-5-mini']:.3f} | {x['usd_tierA_block_gpt-5-mini']:.2f} |")
    return "\n".join(L)


# ------------------------------------------------------------------------------------------------ E8.3
def _mixed_table(t: pd.DataFrame, gp: bool) -> str:
    L = ["| M | S | R | σ model×arm | ρ | β | n | E0 v2 nested | E1 crossed | E2 two-way bootstrap | E3 run bootstrap | E2 coverage |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in t.sort_values(["beta", "M", "S", "R", "s_ma", "rho"]).iterrows():
        cells = []
        for e in ("e0", "e1", "e2", "e3"):
            txt = _ci(r[f"{e}_reject"], r[f"{e}_reject_lo"], r[f"{e}_reject_hi"])
            if r["beta"] == 0.0 and r[f"{e}_reject_lo"] > 0.05:
                txt = f"**{txt}**"
            cells.append(txt)
        L.append(f"| {int(r.M)} | {int(r.S)} | {int(r.R)} | {r.s_ma:.2f} | {r.rho:.1f} | {r.beta:.2f} | {int(r.n_datasets)} | "
                 + " | ".join(cells) + f" | {_f(r.e2_coverage, 3)} |")
    return "\n".join(L)


def t_mixed() -> Optional[str]:
    t = _c("e8_3/mixed.csv")
    if t is None:
        return None
    L = ["Rejection rate of β = 0 at α = 0.05 with its Wilson 95 % interval: **size** in the β = 0 rows (bold = the interval "
         "lies above 0.05, size does not hold), **power** in the β = 0.05 rows. The tested cell is ENTJ × bull_trap "
         "(E1, E2, E3) and ENTJ pooled over scenarios (E0, as implemented). Path effect: the real band-MAS of the "
         "observables oracle (sd 0.0003–0.0005; addendum 3).", "", _mixed_table(t, False), "",
         "E1's variance components (median over datasets) and the share of fits with the model × arm component at the zero boundary:", "",
         "| M | S | R | σ model×arm planted | β | model (planted 0.0025) | model×arm | path | model×arm at boundary | fit failures |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in t.sort_values(["beta", "M", "S", "R", "s_ma", "rho"]).iterrows():
        L.append(f"| {int(r.M)} | {int(r.S)} | {int(r.R)} | {r.s_ma:.2f} (ρ {r.rho:.1f}) | {r.beta:.2f} | {_f(r.get('e1_vc_model_median'), 5)} | "
                 f"{_f(r.get('e1_vc_model_arm_median'), 5)} | {_f(r.get('e1_vc_path_median'), 6)} | "
                 f"{_f(r.get('e1_vc_model_arm_at_boundary'), 2)} | {int(r.e1_fit_fail)} |")
    return "\n".join(L)


def t_mixed_gpath() -> Optional[str]:
    t = _c("e8_3/mixed_gpath.csv")
    if t is None:
        return None
    return ("**Unregistered sensitivity** (addendum 3): a Gaussian path intercept, sd 0.04, S = 10.\n\n" + _mixed_table(t, True))


def t_recovery() -> Optional[str]:
    d = _j("e8_3/recovery_band.json")
    if d is None:
        return None
    L = [f"Design: M = {d['design']['M']}, S = {d['design']['S']}, all-Gaussian in E1's own parameterisation; "
         f"{d['band']['model']['n']} datasets. Power at β = 0.05: {_ci(*d['power_at_beta'])}.", "",
         "| component | planted variance | p05 | median | p95 | planted inside [p05, p95] |", "|---|---|---|---|---|---|"]
    for k, b in d["band"].items():
        L.append(f"| {k} | {b['planted']:.5f} | {b['p05']:.5f} | {b['p50']:.5f} | {b['p95']:.5f} | {'yes' if b['planted_inside_p05_p95'] else '**no**'} |")
    return "\n".join(L)


def t_multiplicity() -> Optional[str]:
    d = _j("e8_3/multiplicity.json")
    if d is None:
        return None
    tc = d["tier_c"]; C = np.asarray(tc["corr"])
    L = [f"Tier C's correlation on {tc['n_cells']} cells ({tc['construction']}; |r|(band-MAS, D at 0.05) = "
         f"{tc['check_band_mas_D_0.05_abs_r']:.3f}, reproducing `e7_8/matrix.json`): |r|(band-MAS, D at 0.0020) = {abs(C[0, 2]):.3f}, "
         f"**|r|(D at 0.05, D at 0.0020) = {abs(C[1, 2]):.3f}**. {d['reps']:,} replications, non-null shift {d['shift']:.0f}.", "",
         "| grid | tests | π₁ | procedure | FDR (MC half-width) | FWER | power | FDR ≤ 0.05 + MC |", "|---|---|---|---|---|---|---|---|"]
    for r in d["table"]:
        L.append(f"| {r['grid']} {r['families']} | {r['n_tests']} | {r['pi1']:.1f} | {r['procedure']} | {r['fdr']:.4f} ({r['fdr_mc_halfwidth']:.4f}) | "
                 f"{r['fwer']:.3f} | {_f(r['power'], 3)} | {'yes' if r['fdr_holds'] else '**no**'} |")
    return "\n".join(L)


def t_null() -> Optional[str]:
    d = _j("e8_3/null.json")
    if d is None:
        return None
    pp = d["phi_pilot"]
    t = pd.DataFrame(d["table"])
    L = [f"AR(1) daily series, T = 200, no trend; {d['reps']:,} replications, {d['draws']} null draws each. φ_pilot = the "
         f"median lag-1 autocorrelation of daily cash share over the pilot's {pp['n_runs']} main runs = **{pp['median']:.4f}** "
         f"(P10 {pp['p10']:.3f}, P90 {pp['p90']:.3f}). One run under N0 has at most {d['exact_N0_distinct_values_per_run']} "
         f"rotations, so its smallest attainable p is {d['min_p_N0_one_run_exact']:.3f}.", "",
         "| φ | runs (pairs for N3) | N0 circular shift (v2) | N1 window permutation | N2 day-block permutation | N3 path-level sign-flip |",
         "|---|---|---|---|---|---|"]
    for (phi, n), g in t.groupby(["phi", "n_runs"]):
        cells = []
        for k in ("N0", "N1", "N2", "N3"):
            r = g[g["null"] == k].iloc[0]
            txt = _ci(r["size"], r["size_lo"], r["size_hi"])
            cells.append(txt if r["size_holds"] else f"**{txt}**")
        L.append(f"| {phi:.4g}{' (pilot)' if g['phi_is_pilot'].iloc[0] else ''} | {int(n)} | " + " | ".join(cells) + " |")
    return "\n".join(L)


# ------------------------------------------------------------------------------------------------ E8.4
def t_identification() -> Optional[str]:
    d = _j("e8_4/identification.json")
    if d is None:
        return None
    L = ["Clause (i) is read on the persona and directive blocks; as registered it also asked the start block to vary, which "
         "clause (iii) forbids, so no design passes as registered (addendum 10) — that verdict is the last column.", "",
         "| design | runs | start designs | rank P / D / S / all | (i) P, D vary | (ii) | (iii) | (iv) | R² of S on P, D | max canonical corr P~S | P~D | **identified** | as registered |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, c in d.items():
        rk = c["ranks"]; cc = c["max_canonical_corr"]; yn = lambda b: "yes" if b else "**no**"
        L.append(f"| {name} | {c['n_runs']} | {', '.join(c['start_designs'])} | {rk['persona']} / {rk['directive']} / {rk['start']} / {rk['all']} | "
                 f"{yn(c['clauses']['i'])} | {yn(c['clauses']['ii'])} | {yn(c['clauses']['iii'])} | {yn(c['clauses']['iv'])} | "
                 f"{_f(c['r2_block_on_others'].get('start'), 3)} | {_f(cc.get('persona~start'), 3)} | {_f(cc.get('persona~directive'), 3)} | "
                 f"**{'yes' if c['identified'] else 'NO'}** | {'yes' if c.get('identified_as_registered') else 'no'} |")
    return "\n".join(L)


def t_salience_shares() -> Optional[str]:
    t = _c("e8_4/shares_synthetic.csv")
    if t is None:
        return None
    g = t.groupby(["design", "window_start"])
    L = ["Known answer: c* depends on the persona and the market only (no directive effect). Shares over 10 surrogate seeds:", "",
         "| design | window | S_persona mean (min–max) | S_start mean (min–max) | S_directive mean (min–max) | S_market mean | OOF R² |",
         "|---|---|---|---|---|---|---|"]
    for (des, w), x in g:
        L.append(f"| {des} | {int(w)} | {x.S_persona.mean():.3f} ({x.S_persona.min():.3f}–{x.S_persona.max():.3f}) | "
                 f"{x.S_start.mean():.3f} ({x.S_start.min():.3f}–{x.S_start.max():.3f}) | "
                 f"{x.S_directive.mean():.3f} ({x.S_directive.min():.3f}–{x.S_directive.max():.3f}) | {x.S_market.mean():.3f} | {x.r2.mean():.3f} |")
    return "\n".join(L)


def t_salience_bootstrap() -> Optional[str]:
    d = _j("e8_4/bootstrap.json")
    if d is None:
        return None
    grp = d.get("cv_groups") or ("**the relabelled copy — the leaky run of addendum 18, superseded by its re-run; "
                                 "these intervals are not used**")
    L = [f"Design B through `salience_by_window(identification=\"v2_1\")`, {d['n_boot']} seed-cluster refits per window; "
         f"cross-validation folds grouped by {grp}.", "",
         "| window | status | S_persona [95 %] | excludes 0 | S_directive [95 %] | covers 0 |", "|---|---|---|---|---|---|"]
    def small(v, lo, hi):                   # a directive share of ~1e-5 printed at three decimals would read as 0.000
        f = lambda x: f"{x:.2e}" if abs(x) < 0.001 else f"{x:.3f}"
        return f"{f(v)} [{f(lo)}, {f(hi)}]"

    for w in d["windows"]:
        L.append(f"| {w['window_start']} | {w['status']} | {_ci(w['S_persona'], *w['S_persona_ci'])} | {'yes' if w['persona_interval_excludes_0'] else '**no**'} | "
                 f"{small(w['S_directive'], *w['S_directive_ci'])} | {'yes' if w['directive_interval_covers_0'] else '**no**'} |")
    L += ["", d["note"]]
    return "\n".join(L)


# ------------------------------------------------------------------------------------------------ E8.5
def t_validate() -> Optional[str]:
    """E8.5's power analysis on known answers (addendum 13, 16): does the plug-in upper limit cover the truth?"""
    d = _j("e8_5/validate.json")
    t = _c("e8_5/validate.csv")
    if d is None or t is None:
        return None
    ds = d["design"]
    L = [f"{ds['personas']} personas × 2 arms × {ds['scenarios']} scenarios × {ds['seeds']} seeds × {ds['reps']} replicates per "
         f"dataset; {int(t.groupby(['s_int', 's_rep']).size().iloc[0])} datasets per setting; {ds['boot']:,} bootstrap resamples. "
         f"Nominal coverage of a one-sided limit: {d['nominal_coverage']:.2f}. Coverage with its Wilson 95 % interval.", "",
         "| seed × arm sd | replicate sd | median estimate ÷ truth (R = 1) | percentile bootstrap (registered), R = 1 | R = 3 | "
         "closed-form limit, R = 1 | R = 3 | plug-in seeds below the truth's: bootstrap | closed form |",
         "|---|---|---|---|---|---|---|---|---|"]
    from scipy.stats import norm
    z = norm.ppf(0.975)

    def w(k, n):
        p = k / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den
        h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
        txt = f"{p:.2f} [{c - h:.2f}, {c + h:.2f}]"
        return f"**{txt}**" if c + h < 0.90 else txt

    for (si, sr), g in t.groupby(["s_int", "s_rep"]):
        n = len(g)
        mls1 = w(int(g["mls_covers_R1"].sum()), n) if "mls_covers_R1" in g else "—"
        mls3 = w(int(g["mls_covers_R3"].sum()), n) if "mls_covers_R3" in g else "—"
        below_mls = f"{(g['n_seeds_mls_R1'] < g['n_seeds_truth_R1']).mean():.2f}" if "n_seeds_mls_R1" in g else "—"
        L.append(f"| {si:.2f} | {sr:.2f} | {(g['est_R1'] / g['truth_R1']).median():.3f} | {w(int(g['covers_R1'].sum()), n)} | "
                 f"{w(int(g['covers_R3'].sum()), n)} | {mls1} | {mls3} | "
                 f"{(g['n_seeds_plugin_R1'] < g['n_seeds_truth_R1']).mean():.2f} | {below_mls} |")
    L += ["", "Bold: the interval lies entirely below the nominal 0.90, so the limit does not deliver its assurance."]
    return "\n".join(L)


def t_smoke_first() -> Optional[str]:
    """The first smoke, at the provider-default thinking, whose gate stopped the registered design (P8-8)."""
    return t_smoke("e8_5/smoke_thinking_default.json")


def t_smoke(rel: str = "e8_5/smoke.json") -> Optional[str]:
    d = _j(rel)
    if d is None:
        return None
    L = ["| run | status | seconds | calls | input tokens | output tokens (reasoning) | $ |", "|---|---|---|---|---|---|---|"]
    for r in d["runs"]:
        L.append(f"| `{r['run_id']}` | {r['status']} | {r['seconds']:.0f} | {r['n_llm_calls']} | {r['input_tokens']:,} | "
                 f"{r['output_tokens']:,} ({r['reasoning_tokens']:,}) | {r['usd']:.3f} |")
    L += ["", "| design | model | $ per run (measured) | runs | projected $ | output tokens / call | reasoning / call | seconds / run |",
          "|---|---|---|---|---|---|---|---|"]
    for k, v in d["per_design"].items():
        L.append(f"| {k} | {v['model']} | {_f(v['usd_per_run_measured'], 3)} | {v['n_runs']} | {_f(v['usd_projected'], 2)} | "
                 f"{_f(v['output_tokens_per_call'], 0)} | {_f(v['reasoning_tokens_per_call'], 0)} | {_f(v['seconds_per_run'], 0)} |")
    L += ["", f"Projected total with L3 (${d['l3_estimate_usd']:.0f}): **${d['projected_total_usd']:.2f}** against the approval "
              f"${d['approved_usd']:.0f} and the gate ${d['gate_usd']:.0f} → **{'PASS' if d['pass'] else 'STOP'}**."]
    return "\n".join(L)


def t_components() -> Optional[str]:
    t = _c("e8_5/components.csv")
    if t is None:
        return None
    L = ["| model | metric | pairs | mean memory − static | σ_d(R=1) point [closed-form 90 % limit; bootstrap limit] | σ_d(R=3) | σ²_int | σ²_rep | share of Var(d) at R=1 from seed×arm | ICC path | ICC path×arm |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in t.iterrows():
        L.append(f"| {r.Model} | `{r.metric}` | {int(r.n_pairs)} | {_f(r.mean_d, 4)} | {_f(r.sigma_d_R1, 4)} "
                 f"[{_f(r.get('sigma_d_R1_mls90'), 4)}; {_f(r.sigma_d_R1_ucl90, 4)}] | "
                 f"{_f(r.sigma_d_R3, 4)} | {_f(r.sigma2_int, 6)} | {_f(r.sigma2_rep, 6)} | {_f(r.share_int_R1, 3)} | "
                 f"{_f(r.get('icc_path'), 3)} | {_f(r.get('icc_path_arm'), 3)} |")
    return "\n".join(L)


def t_power() -> Optional[str]:
    d = _j("e8_5/power.json")
    if d is None:
        return None
    L = [f"D12: Δ = {d['delta_band_mas']} band-MAS, power {d['power']}, α' = 0.05 / {d['m_Q1_C']} = {d['alpha_bonferroni']:.5f}; "
         f"plug-in: {d['plugin']}.", "",
         "| replicates R | σ_d point | σ_d closed-form 90 % limit | **seeds / cell, App. A (Bonferroni)** | paired-correct (Bonferroni) | App. A (nominal α) | paired (nominal) | App. A at the point σ | bootstrap limit (registered): σ_d / seeds | bootstrap 80 % / 95 % limit: seeds | runs / contrast cell |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for R, s in d["sized_band_mas"].items():
        L.append(f"| {R} | {_f(s['sigma_point'], 4)} | {_f(s['sigma_limit'], 4)} | **{s['appA_bonf']}** | {s['paired_bonf']} | {s['appA_nominal']} | "
                 f"{s['paired_nominal']} | {s['appA_bonf_at_point']} | {_f(s['sigma_bootstrap_ucl90'], 4)} / {s['appA_bonf_bootstrap']} | "
                 f"{s['appA_bonf_bootstrap_ucl80']} / {s['appA_bonf_bootstrap_ucl95']} | {s['runs_per_contrast_cell_appA_bonf']} |")
    L += ["", "Minimum detectable difference (80 % power) in each metric's own units, at the closed-form limit (the registered bootstrap limit beside):", "",
          "| metric | design | seeds / cell | R | σ_d closed-form limit | MDD App. A (Bonferroni) | paired (Bonferroni) | App. A (nominal) | App. A (Bonferroni) at the bootstrap limit |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in d["mdd"]:
        L.append(f"| `{r['metric']}` | {r['design']} | {r['seeds_per_cell']} | {r['reps']} | {_f(r['sigma_limit'], 4)} | "
                 f"{_f(r['mdd_appA_bonf'], 4)} | {_f(r['mdd_paired_bonf'], 4)} | {_f(r['mdd_appA_nominal'], 4)} | "
                 f"{_f(r['mdd_appA_bonf_bootstrap'], 4)} |")
    L += ["", "Model-level power (DESIGN: the between-model sd is not estimable from one model):", "",
          "| models | τ / σ_d | seeds / cell | power (Bonferroni α, t with M − 1 df) |", "|---|---|---|---|"]
    for r in d["model_level_DESIGN"]:
        L.append(f"| {r['models']} | {r['tau_over_sigma']} | {r['seeds_per_cell']} | {r['power_bonf']:.3f} |")
    return "\n".join(L)


def t_transfer() -> Optional[str]:
    d = _j("e8_5/transfer.json")
    if d is None:
        return None
    L = ["| metric | σ_d Flash (bull_trap) | σ_d GPT-5 mini (bull_trap) | ratio [90 %] | main-grid σ_d limit (Flash's limit × max(1, ratio)) | MDD at the main grid's seeds (App. A, Bonferroni) |",
         "|---|---|---|---|---|---|"]
    for m, v in d["per_metric"].items():
        L.append(f"| `{m}` | {_f(v['sigma_d_flash_bull_trap'], 4)} | {_f(v['sigma_d_gpt5mini_bull_trap'], 4)} | "
                 f"{_ci(v['ratio'], *v['ratio_ci90'])} | {_f(v.get('sigma_limit_main_grid'), 4)} | {_f(v.get('mdd_appA_bonf_main_grid'), 4)} |")
    p = d["band_mas_plugin"]
    L += ["", f"Main-grid plug-in σ_d (band-MAS, R = 1), closed-form limit: {p['sigma_limit_flash_R1']:.4f} × max(1, {p['ratio']:.3f}) = "
              f"**{p['plugin_main_grid']:.4f}**; at the ratio's upper limit {p['plugin_at_ratio_upper']:.4f}; at the registered "
              f"bootstrap limit {p['plugin_main_grid_bootstrap']:.4f}. {d['caveat']}."]
    if "seeds_appA_bonf_main_grid" in p:
        L += ["", f"Seeds per persona × scenario cell the main grid needs at that plug-in (R = 1, App. A, α' = {p['alpha_bonferroni']:.5f}): "
                  f"**{p['seeds_appA_bonf_main_grid']}** (paired-correct {p['seeds_paired_bonf_main_grid']}); at the ratio's upper limit "
                  f"{p['seeds_appA_bonf_at_ratio_upper']}; at the registered bootstrap limit {p['seeds_appA_bonf_main_grid_bootstrap']}."]
    return "\n".join(L)


def t_l3() -> Optional[str]:
    """Phase 6's L3 probe as run under this phase's D2 (P8-12), with what the answers are made of beside."""
    d = _j("e6_l3/l3.json")
    if d is None or not d.get("models"):
        return None
    ra = _j("e6_l3/rule_analysis.json") or {}
    s = d["surrogate_levelfree_gbt"]
    L = [f"{d['n_probes']} probes; the entitled reader (level-free GBT) scores {_ci(s['sign_acc'], *s['wilson95'])}; ceiling "
         f"for a model {d['ceiling']:.3f}; null p95 {d['null_of_accuracy_sign_perm']['p95']:.3f}. The rule \"over-valued iff "
         f"price > analyst fair-value estimate\" scores {_f(ra.get('rule_sign_accuracy_normal'), 3)} on the same probes.", "",
         "| model | arm | temperature that ran | sign accuracy [Wilson 95 %] | fair / unparsed | errors | agreement with the analyst rule | verdict |",
         "|---|---|---|---|---|---|---|---|"]
    for m, arms in d["models"].items():
        for arm, b in arms.items():
            v = b.get("pass_vs_surrogate_ceiling", b.get("within_null"))
            verdict = b.get("verdict") or ("PASS" if v else "FAIL")
            agree = (ra.get("models", {}).get(m, {}).get(arm, {}) or {}).get("agreement_with_rule")
            L.append(f"| {m} | {arm} | {b.get('temperature', '—')} | {_ci(b['sign_acc'], *b['wilson95'])} | "
                     f"{b['share_fair_or_unparsed']:.2f} | {b['n_errors']} | {_f(agree, 3)} | {verdict} |")
    if ra.get("pairwise_agreement_normal"):
        L += ["", "Pairwise agreement between models, normal arm: " +
              "; ".join(f"{k.replace('|', ' / ')} {v:.3f}" for k, v in ra["pairwise_agreement_normal"].items()) + "."]
    return "\n".join(L)


def t_mixed_optimizer() -> Optional[str]:
    """Addendum 17: how often lbfgs stops at a local optimum on E8.3's own conditions, and what it does to E1."""
    d = _j("e8_3/mixed_optimizer.json")
    if d is None:
        return None
    L = [f"Unregistered (addendum 17): E1 fitted by {' and '.join(d['methods'])}, the higher REML likelihood kept (E1-best); "
         f"a local optimum is {d['local_optimum_rule']}. Fresh datasets from E8.3's process; model × arm sd 0.03.", "",
         "| models | seeds | β | datasets | lbfgs stops short | largest gap | decisions that change | E1 as registered (lbfgs) [Wilson 95 %] | E1-best |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in d["table"]:
        L.append(f"| {r['M']} | {r['S']} | {r['beta']} | {r['n_datasets']} | {100 * r['lbfgs_local_share']:.0f} % | {r['llf_gap_max']:.1f} | "
                 f"{r['decision_flips']} | {_ci(r['e1_reject'], r['e1_reject_lo'], r['e1_reject_hi'])} | "
                 f"{_ci(r['e1b_reject'], r['e1b_reject_lo'], r['e1b_reject_hi'])} |")
    return "\n".join(L)


def t_mixed_pp() -> Optional[str]:
    """Addendum 17: E1 as registered, E1-best and E1-amended (seed-level differences) on E8.5's measured components."""
    d = _j("e8_3/mixed_pp.json")
    if d is None:
        return None
    comp = ", ".join(f"{k} {v:.2g}" for k, v in d["components"].items())
    L = [f"Unregistered (addendum 17). Planted: E8.5's band-MAS components ({comp}); {d['seeds']} seeds per scenario, R = 1, "
         f"2 scenarios, 3 personas, model intercept sd 0.05. Reject rates [Wilson 95 %] at α = {d['alpha']}; at α′ = "
         f"{d['alpha_bonferroni']:.5f} beside. E1: as registered (lbfgs). E1-best: E1 at the better of lbfgs and Powell. "
         "E1-amended: E1 on seed-level differences. SE ÷ sd: the median model SE over the sd of the estimates (1 = calibrated).", "",
         "| persona × path | models | model × arm sd | β | datasets | E1 | E1-best | E1-amended | E1 at α′ | E1-amended at α′ | E2 | SE ÷ sd: E1 / E1-best / E1-amended |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in d["table"]:
        L.append(f"| {'shared' if r['shared'] else 'model-specific'} | {r['M']} | {r['s_ma']} | {r['beta']} | {r['n_datasets']} | "
                 f"{_ci(r['e1_reject'], r['e1_reject_lo'], r['e1_reject_hi'])} | {_ci(r['e1b_reject'], r['e1b_reject_lo'], r['e1b_reject_hi'])} | "
                 f"{_ci(r['e1a_reject'], r['e1a_reject_lo'], r['e1a_reject_hi'])} | {r['e1_reject_bonf']:.3f} | {r['e1a_reject_bonf']:.3f} | "
                 f"{_ci(r['e2_reject'], r['e2_reject_lo'], r['e2_reject_hi'])} | "
                 f"{r['e1_se_over_sd']:.2f} / {r['e1b_se_over_sd']:.2f} / {r['e1a_se_over_sd']:.2f} |")
    sz, pw = d["size_holds_M6"], d["power_not_below_M6"]
    L += ["", f"Adoption rule at six models (addendum 17): E1-amended's size holds in {sum(sz.values())} of {len(sz)} settings; its power "
              f"at α′ is not below E1's in {sum(pw.values())} of {len(pw)}. **E1-amended adopted: {'yes' if d['adopt_e1_amended'] else 'no'}.**"]
    return "\n".join(L)


GENERATORS = {
    "e8_mixed_optimizer": t_mixed_optimizer, "e8_mixed_pp": t_mixed_pp,
    "e8_l3": t_l3,
    "e8_validate": t_validate,
    "e8_pilot_offsets": t_pilot_offsets, "e8_placebo": t_placebo, "e8_context_cost": t_context_cost,
    "e8_mixed": t_mixed, "e8_mixed_gpath": t_mixed_gpath, "e8_recovery": t_recovery, "e8_multiplicity": t_multiplicity,
    "e8_null": t_null, "e8_identification": t_identification, "e8_salience_shares": t_salience_shares,
    "e8_salience_bootstrap": t_salience_bootstrap, "e8_smoke_first": t_smoke_first, "e8_smoke": t_smoke,
    "e8_components": t_components,
    "e8_power": t_power, "e8_transfer": t_transfer,
}


def render(text: str) -> tuple:
    status = {}
    for name, gen in GENERATORS.items():
        pat = re.compile(r"(<!-- table:" + re.escape(name) + r" -->\n)(.*?)(<!-- /table:" + re.escape(name) + r" -->)", re.S)
        m = pat.search(text)
        if not m:
            status[name] = "no block"; continue
        body = gen()
        if body is None:
            status[name] = "no file"; continue
        new = m.group(1) + body + "\n" + m.group(3)
        if new == m.group(0):
            status[name] = "unchanged"
        else:
            status[name] = "updated"
            text = text[:m.start()] + new + text[m.end():]
    return text, status


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    with open(REPORT, "r", encoding="utf-8") as fh:
        text = fh.read()
    new, status = render(text)
    print(os.path.relpath(REPORT, ROOT))
    for k, v in status.items():
        print(f"  {k:22s} {v}")
    if a.check:
        stale = [k for k, v in status.items() if v == "updated"]
        if stale:
            print("  STALE blocks:", stale)
            return 1
        return 0
    if new != text:
        with open(REPORT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(new)
        print("  updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
