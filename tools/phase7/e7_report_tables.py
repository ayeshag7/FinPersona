"""
v2.1 Phase 7 -- every report table generated from its file into a marked block (rule 14; Phase 6's pattern).

    python -m tools.phase7.e7_report_tables            # rewrite the blocks of PHASE_7_REPORT.md from the files
    python -m tools.phase7.e7_report_tables --check    # exit 1 if any block differs from what the files give

Blocks: <!-- table:NAME --> ... <!-- /table:NAME -->.  A block whose file is absent is left alone and reported as
"no file", not as a mismatch.  `tests/test_v2_1_phase_7.py::test_phase7_report_tables_match_files` runs `--check`.
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
REPORT = os.path.join(ROOT, "docs", "env_v2", "v2_1", "PHASE_7_REPORT.md")


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


# ------------------------------------------------------------------------------------------- E7.1a theta_info
def t_theta_info() -> Optional[str]:
    d = _j("e7_1/theta_info.json")
    t = _c("e7_1/theta_info.csv")
    if not d or t is None:
        return None
    L = ["| scope | population | feature set | theta_info | sign accuracy there | coverage | n resolvable | "
         "max accuracy (at theta) | theta_info on the interval's lower end |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(d["located"], key=lambda r: (r["scope"] != "pooled", r["scope"], r["population"], r["feature_set"])):
        th = r["theta_info"]
        acc = f"{_f(r.get('sign_acc_at_theta_info'), 3)} [{_f(r.get('sign_lo_at_theta_info'), 3)}, " \
              f"{_f(r.get('sign_hi_at_theta_info'), 3)}]" if th is not None else "—"
        L.append(f"| {r['scope']} | {r['population']} | {r['feature_set']} | "
                 f"{'**not reached**' if th is None else f'**{th:.2f}**'} | {acc} | "
                 f"{_f(r.get('coverage_at_theta_info'), 3)} | {int(r.get('n_resolvable_at_theta_info') or 0):,} | "
                 f"{_f(r.get('max_acc'), 3)} (at {_f(r.get('theta_at_max'), 2)}) | "
                 f"{_f(r.get('theta_info_ci_lower'), 2)} |")
    L += ["", "The pooled curve, both feature sets (the level-free observables surrogate and its level-free "
              "price-only control):", "",
          "| theta | coverage | sign accuracy, all rows | sign accuracy, calm rows | n resolvable (all / calm) |",
          "|---|---|---|---|---|"]
    fa = t[(t.scope == "pooled") & (t.population == "all") & (t.feature_set == "full")].sort_values("theta")
    fc = t[(t.scope == "pooled") & (t.population == "calm") & (t.feature_set == "full")].sort_values("theta")
    for _, r in fa.iterrows():
        rc = fc[fc.theta == r["theta"]]
        cm = rc.iloc[0] if len(rc) else None
        L.append(f"| {r['theta']:.2f} | {r['coverage']:.3f} | {_f(r['sign_acc'], 3)} [{_f(r['sign_lo'], 3)}, "
                 f"{_f(r['sign_hi'], 3)}] | " +
                 (f"{_f(cm['sign_acc'], 3)} [{_f(cm['sign_lo'], 3)}, {_f(cm['sign_hi'], 3)}]" if cm is not None else "—") +
                 f" | {int(r['n_resolvable']):,} / " + (f"{int(cm['n_resolvable']):,}" if cm is not None else "—") + " |")
    return "\n".join(L)


# ------------------------------------------------------------------------------------- E7.1b/c theta_cost, var
def t_theta_cost() -> Optional[str]:
    d = _j("e7_1/theta_cost_var.json")
    if not d:
        return None
    tc, tv = d["theta_cost"], d["theta_var"]
    i = tc["inputs"]
    L = ["| quantity | value | source |", "|---|---|---|",
         f"| cost rate c ({i['cost_bp_per_trade']} bp per trade) | {i['cost_rate_c']:.6f} | `simulation/runner_v2.py` "
         f"`RunConfig.cost_bp`; charged on \\|traded value\\| per trade by `simulation/portfolio_v2.py` |",
         f"| FIT half-life h | {i['half_life_days']:.4f} d [{i['half_life_interval'][0]:.2f}, "
         f"{i['half_life_interval'][1]:.2f}] | `envs/v2/params/mispricing.json` `half_life.value` (n = 417) |",
         f"| band width w (every persona) | {sorted(set(round(v, 2) for v in i['band_widths'].values()))[0]:.2f} | "
         f"`evaluation/targets.py` `BANDS` — **cancels** |",
         f"| f, one half-life (primary) | {i['f_half_life']:.4f} | by definition of the half-life |",
         f"| **theta_cost = 2c/f = 4c** | **{tc['value']:.6f}** | the same for every persona |", "",
         "| horizon | f | theta_cost |", "|---|---|---|",
         f"| one half-life — **primary** | {i['f_half_life']:.4f} | **{tc['value']:.6f}** |"]
    s = tc["sensitivities"]
    L += [f"| one day | {s['one_day_horizon']['f']:.4f} | {s['one_day_horizon']['theta_cost']:.6f} |",
          f"| one day at h = {s['one_day_horizon_h_lo']['h']:.2f} | {s['one_day_horizon_h_lo']['f']:.4f} | "
          f"{s['one_day_horizon_h_lo']['theta_cost']:.6f} |",
          f"| one day at h = {s['one_day_horizon_h_hi']['h']:.2f} | {s['one_day_horizon_h_hi']['f']:.4f} | "
          f"{s['one_day_horizon_h_hi']['theta_cost']:.6f} |",
          f"| infinite | {s['infinite_horizon']['f']:.4f} | {s['infinite_horizon']['theta_cost']:.6f} |", "",
          "The closed form checked numerically against the real `PortfolioV2` at three band widths:", "",
          "| band width | closed form at the discrete horizon | numeric break-even | relative error |",
          "|---|---|---|---|"]
    for ck in tc["numeric_check"]["rows"]:
        L.append(f"| {ck['band_width']:.2f} | {ck['closed_form_at_T_hold']:.6f} | {ck['numeric']:.6f} | "
                 f"{ck['rel_error']:.2%} |")
    L += ["", f"Spread of the numeric break-even across band widths **{tc['numeric_check']['break_even_spread_across_band_widths']:.2e}** "
              f"— w cancels as a measurement, not only algebraically. Worst relative error "
              f"**{tc['numeric_check']['worst_rel_error']:.2%}**, within the pre-registered 10 %.", "",
          "What cost tier would put theta_cost on the grid:", "",
          "| grid theta | bp per trade required | multiple of the implemented tier |", "|---|---|---|"]
    for tr in tc["sensitivities"]["cost_tier"]:
        L.append(f"| {tr['theta']:.2f} | {tr['bp_per_trade_required']:.0f} | "
                 f"{tr['multiple_of_implemented_tier']:.0f}× |")
    L += ["", f"**theta_var = {tv['value']:.6f}** — the generator's median 200-day sd(x) on flat paths "
              f"(n = {tv['n']} seeds), inside the AR(1) reference band [{tv['interval'][0]:.5f}, "
              f"{tv['interval'][1]:.5f}] at the FIT half-life. Sensitivity: the stationary "
              f"s_x = {tv['sensitivity_stationary_s_x']['value']:.6f}."]
    return "\n".join(L)


# ---------------------------------------------------------------------------------- E7.1 the headline table
def t_theta_table() -> Optional[str]:
    t = _c("e7_rescore/theta_table.csv")
    if t is None:
        return None
    keep = ("mandate_conditional_oracle", "L5_full_level_free", "L5_level_free", "rule_p_sma50", "band_hi",
            "band_lo", "always_hold")
    L = ["| scenario | theta | label | policy | MCR | B (band violation) | D (directional) | band-MAS | "
         "MCR per window | oracle switches | coverage |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for sc in ("flat", "bull_trap", "crash", "sustained_bull"):
        g = t[(t.scenario == sc) & (t.policy.isin(keep))].sort_values(["theta", "policy"])
        for _, r in g.iterrows():
            L.append(f"| {sc} | {r['theta']:.4g} | {r['theta_labels']} | {r['policy']} | "
                     f"{_f(r['mcr'])} [{_f(r['mcr_lo'])}, {_f(r['mcr_hi'])}] | {_f(r['mcr_B'])} | {_f(r['mcr_D'])} | "
                     f"{_f(r['band_mas'])} | {_f(r['mcr_window'])} | {r['oracle_switches']:.2f} | "
                     f"{r['coverage']:.3f} |")
    return "\n".join(L)


# --------------------------------------------------------------------------------------------- E7.3 Merton
def t_merton() -> Optional[str]:
    d = _j("e7_3/merton.json")
    if not d:
        return None
    L = ["| scenario | mu (total return) | sigma (total return) | mu (price only) | sigma (price only) | "
         "realised dividend yield | payer share |", "|---|---|---|---|---|---|---|"]
    for sc, p in d["per_scenario"].items():
        tr, po = p["total_return"], p["price_only"]
        L.append(f"| {sc}{' (primary)' if sc == d['primary_population'] else ''} | "
                 f"{_f(tr['mu'])} [{_f(tr['mu_ci95'][0])}, {_f(tr['mu_ci95'][1])}] | "
                 f"{_f(tr['sigma'])} [{_f(tr['sigma_ci95'][0])}, {_f(tr['sigma_ci95'][1])}] | "
                 f"{_f(po['mu'])} | {_f(po['sigma'])} | {_f(p['dividend_yield_realised_annualised'], 5)} | "
                 f"{_f(p['payer_share'], 3)} |")
    L += ["", "| gamma | risky share w* | cash share 1 − w* | unclipped | 95 % interval |", "|---|---|---|---|---|"]
    for r in d["merton_table"]:
        L.append(f"| {int(r['gamma'])} | {_f(r['risky_share'], 3)} | **{_f(r['cash_share'], 3)}** | "
                 f"{_f(r['cash_share_unclipped'], 3)} | [{_f(r['cash_share_ci95_lo'], 3)}, "
                 f"{_f(r['cash_share_ci95_hi'], 3)}] |")
    L += ["", "| persona | category | practitioner cash band (reading A, scored) | gammas whose Merton cash share "
              "falls inside it | nearest gamma to the band centre | Merton cash there |",
          "|---|---|---|---|---|---|"]
    for p in d["placement"]:
        L.append(f"| {p['persona']} | {p['category']} | {p['band'][0]:.2f}–{p['band'][1]:.2f} | "
                 f"{p['gammas_inside_band'] or '—'} | {p['nearest_gamma_to_band_centre']} | "
                 f"{_f(p['merton_cash_at_nearest_gamma'], 3)} |")
    return "\n".join(L)


# --------------------------------------------------------------------------------------------- E7.8
def t_sweeps() -> Optional[str]:
    d = _j("e7_8/sweeps_verdicts.json")
    t = _c("e7_8/sweeps.csv")
    if not d or t is None:
        return None
    th = d["theta_reported"]
    L = ["| scoring | family | swept parameter | target metric | registered direction | reversals | "
         "outside the interval | monotone |", "|---|---|---|---|---|---|---|---|"]
    for v in d["verdicts"]:
        L.append(f"| {v['scoring']} | {v['family']} | {[round(x, 3) for x in v['swept']]} | `{v['metric']}` | "
                 f"{v['direction']} | {v['n_reversals']} | "
                 f"{v['n_reversals_outside_interval']} | **{'yes' if v['monotone'] else 'NO'}** |")
    L += ["", f"The cell means with their percentile cluster-bootstrap 95 % intervals over seeds "
              f"(theta = {th}, half-width 0.10):", "",
          "| scoring | family | swept value | target metric | mean [95 % interval] | n cells | n seeds |",
          "|---|---|---|---|---|---|---|"]
    sub = t[t.theta == th].sort_values(["scoring", "family", "swept"])
    for _, r in sub.iterrows():
        L.append(f"| {r['scoring']} | {r['family']} | {r['swept']:.3f} | `{r['metric']}` | "
                 f"{_f(r['mean'])} [{_f(r['lo'])}, {_f(r['hi'])}] | {int(r['n_cells'])} | {int(r['n_seeds'])} |")
    return chr(10).join(L)


def t_matrix() -> Optional[str]:
    d = _j("e7_8/matrix.json")
    t = _c("e7_8/matrix.csv")
    if not d or t is None:
        return None
    L = ["| scoring | pair | \\|r\\| across cells | collinear by construction |", "|---|---|---|---|"]
    for _, r in t.sort_values(["scoring", "abs_r"], ascending=[True, False]).iterrows():
        L.append(f"| {r['scoring']} | {r['a']} — {r['b']} | {_f(r['abs_r'], 3)} | "
                 f"{'yes' if r['collinear_by_construction'] else 'no'} |")
    L += ["", "| scoring | collinearity floor | its 95 % interval | half-width | **ceiling** | observed "
              "\\|r\\|(MCR, band-MAS) | below the ceiling |", "|---|---|---|---|---|---|---|"]
    for sc in ("A_decomposition", "B_per_window"):
        c = d[sc]["ceiling"]
        L.append(f"| {sc} | {_f(c['collinearity_floor'], 4)} | [{_f(c['floor_ci95'][0], 4)}, "
                 f"{_f(c['floor_ci95'][1], 4)}] | {_f(c['half_width'], 4)} | **{_f(c['ceiling'], 4)}** | "
                 f"{_f(d[sc]['observed_abs_corr_mcr_band_mas'], 4)} | "
                 f"**{'yes' if d[sc]['below_ceiling'] else 'NO'}** |")
    return "\n".join(L)


def t_adopt() -> Optional[str]:
    d = _j("e7_8/adopt.json")
    if not d:
        return None
    L = ["| scoring | every sweep monotone | failing sweeps | \\|r\\|(MCR, band-MAS) | ceiling | below ceiling | "
         "qualifies |", "|---|---|---|---|---|---|---|"]
    for s, r in d["per_scoring"].items():
        L.append(f"| {s} | {'yes' if r['all_sweeps_monotone'] else 'NO'} | "
                 f"{', '.join(r['failing_sweeps']) or '—'} | {_f(r['observed_abs_corr_mcr_band_mas'], 4)} | "
                 f"{_f(r['ceiling'], 4)} | {'yes' if r['below_ceiling'] else 'NO'} | "
                 f"**{'yes' if r['qualifies'] else 'no'}** |")
    L += ["", f"**Adopted: {d['adopted'] or 'NONE'}** — {d['why']}"]
    return "\n".join(L)


# --------------------------------------------------------------------------------------------- 16A re-stated
def t_16a() -> Optional[str]:
    d = _j("e7_16a/restate.json")
    if not d:
        return None
    p6 = d["phase6_verdict"]
    lab = {"mcr": "MCR — the Phase-6 statistic", "mcr_B": "B, the band-violation term",
           "mcr_D": "D, the directional term", "mcr_window": "MCR per 25-day window (REG-12 B)"}
    L = [f"Phase 6's verdict, which stands: G1 {'PASS' if p6['G1'] else 'FAIL'}, G2 {'PASS' if p6['G2'] else 'FAIL'}, "
         f"G3 {'PASS' if p6['G3'] else 'FAIL'}, G4a {'PASS' if p6['G4a'] else 'FAIL'}, "
         f"G4b {'PASS' if p6['G4b'] else 'FAIL'}.", "",
         "| statistic the gate is read on | G1 (4 of 4) | G2 (≥ 3 of 4) | G4a (4 of 4) |", "|---|---|---|---|"]
    for m, v in d["restated"].items():
        L.append(f"| {lab.get(m, m)} | {v['G1']['n_pass']} of 4 — **{'PASS' if v['G1']['pass'] else 'FAIL'}** | "
                 f"{v['G2']['n_pass']} of 4 — **{'PASS' if v['G2']['pass'] else 'FAIL'}** | "
                 f"{v['G4a']['n_pass']} of 4 — **{'PASS' if v['G4a']['pass'] else 'FAIL'}** |")
    scen = list(d["G3"]["daily"]["per_scenario"])
    L += ["", "| G3 reading | " + " | ".join(scen) + " | verdict |", "|---|" + "---|" * (len(scen) + 1)]
    for name in ("daily", "per_window"):
        g = d["G3"][name]
        L.append(f"| {name} | " + " | ".join(f"median {g['per_scenario'][sc]['median_switches']:.0f}, share "
                                             f"{g['per_scenario'][sc]['share_ge2']:.2f}" for sc in scen) +
                 f" | **{'PASS' if g['pass'] else 'FAIL'}** |")
    return "\n".join(L)


# --------------------------------------------------------------------------------------------- E7.6 / pilot
def t_repro() -> Optional[str]:
    d = _j("e7_6/repro.json")
    if not d:
        return None
    L = ["| question | answer |", "|---|---|",
         f"| pilot runs | {d['n_runs']} |",
         f"| engines recorded | {', '.join(d['recorded_engines'])} |",
         f"| environments CONSTRUCTIBLE under the recorded engine | **{d['n_regen_ok_as_recorded']} of {d['n_runs']}** |",
         f"| paths that reproduce under the recorded engine | **{d['n_path_reproduces']} of {d['n_runs']}** |",
         f"| constructible under the documented CAL fallback engine | {d['n_regen_ok_fallback']} of {d['n_runs']} |",
         f"| paths that reproduce under the fallback engine | {d['n_path_reproduces_under_fallback_engine']} of {d['n_runs']} |",
         f"| worst abs difference against the logged price / V / x, fallback engine | median "
         f"{_f(d['worst_abs_diff_fallback_median'], 2)}, minimum {_f(d['worst_abs_diff_fallback_min'], 2)} |",
         f"| `Gen_Config_Hash` recomputed from the stored metadata matches | {d['n_gen_config_hash_matches']} of "
         f"{d['n_runs']} |"]
    if d.get("regen_error_as_recorded"):
        L += ["", "The generator's own refusal, verbatim:", "", "```", d["regen_error_as_recorded"][0], "```"]
    return "\n".join(L)


def t_pilot() -> Optional[str]:
    d = _j("e7_pilot/pilot_rescore.json")
    if not d:
        return None
    rep = d["meta"].get("published_reproduction", {})
    L = []
    if rep.get("checked"):
        L += [f"The re-score reproduces `generated/pilot_report_per_run.csv` run by run: {rep['n_matched']} of "
              f"{rep['n_published_rows']} runs matched, worst absolute difference in `mcr_0.05` "
              f"**{rep['worst_abs_diff']:.3e}** — the decomposition is a decomposition of exactly the statistic "
              f"that was published.", ""]
    L += ["| persona | arm | n (published / T200) | MCR as published | MCR in the note | MCR now (T200) | "
          "B | D | MCR per window | oracle switches | share outside band | norm_MCR in the note (v2-era) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in d["headline"]:
        L.append(f"| {r['persona']} | {r['arm']} | {int(r['n_runs_as_published'])} / {int(r['n_runs_T200'])} | "
                 f"{_f(r['mcr_as_published'])} | {_f(r['mcr_published'], 2)} | {_f(r['mcr_now'])} | "
                 f"{_f(r['mcr_B_now'])} | {_f(r['mcr_D_now'])} | {_f(r['mcr_window_now'])} | "
                 f"{_f(r['oracle_switches_now'], 1)} | {_f(r['share_agent_outside_now'], 3)} | "
                 f"{_f(r['norm_mcr_published'], 2)} |")
    if rep.get("prose_vs_table"):
        L += ["", "The prose figures in `PILOT_NOTES.md` against the table they were written from:", "",
              "| persona | arm | MCR in the prose | MCR in the table | agrees to 2 dp | norm in the prose | "
              "norm in the table | agrees to 2 dp |", "|---|---|---|---|---|---|---|---|"]
        for r in rep["prose_vs_table"]:
            L.append(f"| {r['persona']} | {r['arm']} | {r['prose_mcr']:.2f} | {_f(r['table_mcr'])} | "
                     f"{'yes' if r['mcr_agrees_to_2dp'] else '**no**'} | {r['prose_norm_mcr']:.2f} | "
                     f"{_f(r['table_norm_mcr'])} | {'yes' if r['norm_agrees_to_2dp'] else '**no**'} |")
    return "\n".join(L)


def t_dividends() -> Optional[str]:
    d = _j("e7_7/dividends.json")
    if not d:
        return None
    L = [f"{d['seeds_per_scenario']} seeds x {len(d['scenarios'])} scenarios x {len(d['personas'])} personas, "
         f"T = {d['T']}; {d['payer_share']:.1%} of paths are payers (a per-seed draw at the FIT payer share, so a "
         f"non-payer path receives nothing even with the switch on). The price path is not ex-dividend adjusted.", "",
         "| policy | return % off → on (Δ) | MDD % off → on (Δ) | MCR(0.05) off → on (Δ) | band-MAS off → on (Δ) | "
         "turnover off → on (Δ) |", "|---|---|---|---|---|---|"]
    for r in d["summary"]:
        L.append(f"| {r['policy']} | {r['return_pct_off']:.3f} → {r['return_pct_on']:.3f} "
                 f"({r['return_pct_delta']:+.3f}) | {r['mdd_pct_off']:.3f} → {r['mdd_pct_on']:.3f} "
                 f"({r['mdd_pct_delta']:+.3f}) | {r['mcr_0.05_off']:.4f} → {r['mcr_0.05_on']:.4f} "
                 f"({r['mcr_0.05_delta']:+.4f}) | {r['band_mas_off']:.4f} → {r['band_mas_on']:.4f} "
                 f"({r['band_mas_delta']:+.4f}) | {r['turnover_off']:.3f} → {r['turnover_on']:.3f} "
                 f"({r['turnover_delta']:+.3f}) |")
    return chr(10).join(L)


def t_placebo() -> Optional[str]:
    d = _j("e7_7/placebo_length.json")
    if not d:
        return None
    if "chars" not in d:
        return f"**{d.get('status', 'NOT COMPUTABLE')}** — {d.get('reason', '')}"
    L = [f"From the pilot's own prompt records (`mandate_block_text`); n by arm: {d['n_by_arm']}.", "",
         "| unit | real directive (mean ± sd, n) | placebo (mean ± sd, n) | ratio placebo/real | Mann–Whitney p |",
         "|---|---|---|---|---|"]
    for unit in ("chars", "words", "tokens_approx"):
        r = d[unit]
        L.append(f"| {unit} | {r['real_mean']:.1f} ± {r['real_sd']:.1f} (n = {r['n_real']}) | "
                 f"{r['placebo_mean']:.1f} ± {r['placebo_sd']:.1f} (n = {r['n_placebo']}) | "
                 f"{r['ratio_placebo_over_real']:.3f} | {r['p']:.3f} |")
    L += ["", d["rule"]]
    return chr(10).join(L)


def t_theta_cost_policy() -> Optional[str]:
    d = _j("e7_1b/theta_cost_policy.json")
    if not d:
        return None
    m = d["meta"]
    L = [f"The mandate-conditional oracle **acting** at each candidate theta on {m['seeds_per_scenario']} seeds x 4 "
         f"scenarios x 3 personas, at {m['cost_bp']} bp per trade and again at 0 bp. The oracle knows x exactly, "
         f"which is the case theta_cost's derivation assumes. Cluster-bootstrap 95 % intervals over seeds.", "",
         "| acting theta | label | net return % | gross return % (0 bp) | cost drag pp | trades per run | turnover |",
         "|---|---|---|---|---|---|---|"]
    for r in d["summary"]:
        L.append(f"| {r['acting_theta']:.6g} | {r['labels']} | **{_f(r['return_net_pct'], 3)}** "
                 f"[{_f(r['net_lo'], 3)}, {_f(r['net_hi'], 3)}] | {_f(r['return_gross_pct'], 3)} | "
                 f"{_f(r['cost_drag_pct'], 3)} | {_f(r['trades_per_run'], 1)} | {_f(r['turnover'], 2)} |")
    L += ["", f"Derived theta_cost **{_f(d['theta_cost_derived'], 4)}**; best acting theta by net return "
              f"**{d['best_acting_theta_by_net_return']:.6g}**, by gross return "
              f"{d['best_acting_theta_by_gross_return']:.6g}. Cost drag at theta_cost "
              f"{_f(d['cost_drag_at_theta_cost_pp'], 3)} pp on {_f(d['trades_at_theta_cost'], 0)} trades a run."]
    return chr(10).join(L)


def t_adopt_robust() -> Optional[str]:
    d = _j("e7_8/adopt_robustness.json")
    if not d:
        return None
    L = [f"REG-12's rule re-applied at **every** theta in the re-score ({len(d['thetas'])}) and **every** half-width "
         f"in E7.7's sensitivity ({len(d['half_widths'])}) — {d['n_combinations']} combinations in all.", "",
         "| outcome | combinations |", "|---|---|",
         f"| adopts **A** (the decomposition) | **{d['adopts_A']} of {d['n_combinations']}** |",
         f"| adopts B (per-window) | {d['adopts_B']} |",
         f"| adopts neither | {d['adopts_none']} |", "",
         f"**{'The verdict does not depend on the theta it is read at' if d['stable'] else 'THE VERDICT DEPENDS ON THE THETA IT IS READ AT'}.** "
         f"Worst margin for A across all {d['n_combinations']} combinations (ceiling minus observed): "
         f"**{_f(d['worst_margin_A'], 4)}**."]
    return chr(10).join(L)


def t_half_width() -> Optional[str]:
    d = _j("e7_16a/half_width_sensitivity.json")
    t = _c("e7_16a/half_width_sensitivity.csv")
    if not d or t is None:
        return None
    gc = [c for c in t.columns if c.endswith(("_G1", "_G2", "_G4a"))]
    hits = [{"gate": c, "half_width": float(r["half_width"]), "theta": float(r["theta"])}
            for c in gc for _, r in t[t[c] == True].iterrows()]   # noqa: E712
    L = [f"G1, G2 and G4a on each of the four statistics, at every half-width in E7.7's DESIGN sensitivity "
         f"({d['half_widths']}) and every theta ({len(d['thetas'])}) — {d['n_combinations']} slices x 4 statistics "
         f"x 3 gates.", "",
         "| gate that passes anywhere | half-width | theta |", "|---|---|---|"]
    if hits:
        for h in hits:
            L.append(f"| `{h['gate']}` | {h['half_width']:.2f} | {h['theta']:.6g} |")
    else:
        L.append("| — none | — | — |")
    L += ["", "| half-width | G3 (daily) passes at | observables oracle at theta 0.05: MCR = B + D |",
          "|---|---|---|"]
    import numpy as _np
    for hw in d["half_widths"]:
        g = t[t.half_width == hw]
        ths = [f"{float(r['theta']):.6g}" for _, r in g[g["G3_daily"]].iterrows()]
        row = g[_np.isclose(g.theta, 0.05)]
        L.append(f"| {hw:.2f} | {', '.join(ths) if ths else '—'} | {_f(row['L5_mcr'].iloc[0])} = "
                 f"{_f(row['L5_B'].iloc[0])} + {_f(row['L5_D'].iloc[0])} |")
    return chr(10).join(L)


GENERATORS = {
    "e7_theta_cost_policy": t_theta_cost_policy,
    "e7_adopt_robust": t_adopt_robust,
    "e7_half_width": t_half_width,
    "e7_dividends": t_dividends,
    "e7_placebo": t_placebo,
    "e7_theta_info": t_theta_info,
    "e7_theta_cost": t_theta_cost,
    "e7_theta_table": t_theta_table,
    "e7_merton": t_merton,
    "e7_sweeps": t_sweeps,
    "e7_matrix": t_matrix,
    "e7_adopt": t_adopt,
    "e7_16a": t_16a,
    "e7_repro": t_repro,
    "e7_pilot": t_pilot,
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
        print(f"  {k:16s} {v}")
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
