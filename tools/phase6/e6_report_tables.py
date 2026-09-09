"""
v2.1 Phase 6 -- every report table generated from its file into a marked block (rule 13: Phase 4's report went stale
twice, Phase 5's never did).

    python -m tools.phase6.e6_report_tables            # rewrite the blocks of PHASE_6_REPORT.md from the files
    python -m tools.phase6.e6_report_tables --check    # exit 1 if any block differs from what the files give

Blocks: <!-- table:NAME --> ... <!-- /table:NAME --> for NAME in e6_9, e6_1, e6_3, e6_2, e6_5, e6_6, e6_null, e6_after.
A block whose file is absent is left as it is (and --check reports it as "no file", not as a mismatch).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Callable, Dict, Optional

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
REPORT = os.path.join(ROOT, "docs", "env_v2", "v2_1", "PHASE_6_REPORT.md")


def _j(rel):
    p = os.path.join(GEN, rel)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _f(x, nd=4):
    return "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}"


# ------------------------------------------------------------------------------------------ generators
def t_e6_9() -> Optional[str]:
    d = _j("e6_9/known_answers.json")
    if not d:
        return None
    L = ["| case | statistic | target | T = 200 median [P10, P90] | long-T mean | verdict |", "|---|---|---|---|---|---|"]
    for c in d["cases"]:
        hs = sorted(int(k) for k in c["horizons"]); b = c["horizons"][str(hs[0])]; lo = c["horizons"][str(hs[-1])]
        if c["kind"] == "point":
            L.append(f"| `{c['name']}` | {c['statistic']} | {_f(c['target'])} | {_f(b['median'])} [{_f(b['p10'])}, {_f(b['p90'])}] | "
                     f"{_f(lo['mean'])} | {c['verdict']['status']} |")
        else:
            ci = b.get("rate_ci95") or [np.nan, np.nan]
            L.append(f"| `{c['name']}` | {c['statistic']} | nominal {_f(c['target'], 3)} | rejection {_f(b['rejection_rate'])} "
                     f"[{_f(ci[0], 3)}, {_f(ci[1], 3)}] | {_f(lo['rejection_rate'])} | {c['verdict']['status']} |")
    n = {s: sum(1 for c in d["cases"] if c["verdict"]["status"] == s) for s in ("pass", "fail", "reported")}
    L.append(f"\n{len(d['cases'])} cases: {n['pass']} pass / {n['fail']} fail / {n['reported']} reported (no closed form); "
             f"{d['meta']['reps']} reps (GARCH {d['meta']['garch_reps']}), root seed {d['meta']['root_seed']}.")
    return "\n".join(L)


def t_e6_1() -> Optional[str]:
    d = _j("e6_1/reference.json")
    if not d:
        return None
    m = d["meta"]; p = pd.DataFrame(d["percentiles"])
    show = ["lb_p_r", "abs_acf1_r", "kurtosis", "hill", "jb_p", "lb_p_absr", "arch_lm_p", "acf1_absr", "garch_persistence",
            "garch_alpha", "gjr_gamma", "leverage_corr", "volume_absr_spearman", "logvolume_acf1", "logvolume_shapiro_p",
            "skew", "worst_over_best", "mdd", "daily_sigma", "worst_day"]
    a = p[p.scope == "all"].set_index("statistic")
    subs = sorted(s for s in p.scope.unique() if s != "all")
    L = [f"{m['n_windows']:,} windows of {m['n_names']} names (T = {m['T_window']}); sub-periods " +
         ", ".join(f"{k} {v:,}" for k, v in m["sub_periods"].items()) + f"; {m['n_errors']} errors.", "",
         "| statistic | n | P10 | P50 | P90 | " + " | ".join(f"P50 {s}" for s in subs) + " |",
         "|---|---|---|---|---|" + "---|" * len(subs)]
    for st in show:
        if st not in a.index:
            continue
        r = a.loc[st]
        cells = [f"{p[(p.scope == s) & (p.statistic == st)]['p50'].iloc[0]:.4g}" for s in subs]
        L.append(f"| `{st}` | {int(r['n']):,} | {r['p10']:.4g} | {r['p50']:.4g} | {r['p90']:.4g} | " + " | ".join(cells) + " |")
    iv = _j("e6_1/iv_reference.json")
    if iv:
        L += ["", "IV block (`e6_1/iv_reference.md`):", "", "| pair | n | IV mean P10 / P50 / P90 | corr(IV, next-20d RV) P50 | IV − RV20 P50 |", "|---|---|---|---|---|"]
        for pair, b in iv["summary"].items():
            u = b["unconditional"]
            L.append(f"| {pair} | {b['n_windows']} | {u['iv_mean']['p10']:.1f} / {u['iv_mean']['p50']:.1f} / {u['iv_mean']['p90']:.1f} | "
                     f"{u['iv_rv20_corr']['p50']:.2f} | {u['iv_minus_rv20_mean']['p50']:+.2f} |")
    return "\n".join(L)


def t_e6_3() -> Optional[str]:
    d = _j("e6_3/power_v2.json")
    if not d:
        return None
    m = d["meta"]
    L = [f"Pilot `{m['panel']}` ({m['n_paths']} paths: {m['per_scenario']}); planned n = {m['n_planned']}.", "",
         "| criterion | item | kind | pilot n | observed | n required | decidable at planned n |", "|---|---|---|---|---|---|---|"]
    for r in d["rows"]:
        obs = f"share {r.get('p_observed', float('nan')):.3f}" if r["kind"] == "share" else f"median {r.get('median', float('nan')):.4g}"
        dec = r.get("verdict_decidable_at_planned_n")
        L.append(f"| `{r['criterion']}` | {r['item']} | {r['kind']} | {r['n_pilot']} | {obs} | {r.get('n_required') if r.get('n_required') is not None else '—'} | "
                 f"{'yes' if dec else ('no' if dec is False else '—')} |")
    return "\n".join(L)


def t_e6_2() -> Optional[str]:
    d = _j("e6_2/criteria.json")
    if not d:
        return None
    rows = [r for r in d["rows"] if "B" in r and r.get("is_main_population")]
    v2 = d.get("v2_verdicts", {})
    L = ["| item | statistic | pop | n_gen / n_ref | gen P50 | ref P50 | B: D (upper) | B | C: share (thr) | C | A (v2) |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        a = v2.get(str(r["item"]), {}).get("pass")
        L.append(f"| {r['item']} | `{r['statistic']}` | {r['population']} | {r['n_gen']} / {r['n_ref']} | {r['gen_p50']:.3g} | {r['ref_p50']:.3g} | "
                 f"{r['B']['D']:.3f} ({r['B']['D_upper95']:.3f}) | {'PASS' if r['B']['pass'] else 'FAIL'} | {r['C']['share_inside']:.3f} ({r['C']['threshold']:.3f}) | "
                 f"{'PASS' if r['C']['pass'] else 'FAIL'} | {'PASS' if a else ('FAIL' if a is False else 'n/a')} |")
    sp = [r for r in d["rows"] if r.get("population") == "size_power"]
    if sp:
        ns = sorted({int(n) for r in sp for n in r["size_power"]})
        L += ["", "Size and power (pass rates of B / C at true D = 0, 0.05, 0.10):", "",
              "| item | statistic | " + " | ".join(f"n = {n}: D0 / D.05 / D.10" for n in ns) + " |", "|---|---|" + "---|" * len(ns)]
        for r in sp:
            cells = []
            for n in ns:
                s = r["size_power"].get(str(n))
                cells.append("—" if not s else " / ".join(f"{s[k]['pass_rate_B']:.2f} {s[k]['pass_rate_C']:.2f}" for k in ("D0.00", "D0.05", "D0.10")))
            L.append(f"| {r['item']} | `{r['statistic']}` | " + " | ".join(cells) + " |")
    return "\n".join(L)


def t_e6_5() -> Optional[str]:
    d = _j("e6_5/floor.json")
    if not d:
        return None
    r = d["rule"]; e = d["empirical_trivial"]
    L = [f"s_x = {d['inputs']['s_x']:.4f}; B (day 200) = {d['inputs']['bound_day_T']:.4f}; ceiling at 5 % = {r['ceiling_5pct']:.4f}; "
         f"half-width {r['halfwidth_5pct']:.4f}; **margin {r['margin_5pct']:.4f}**; trivial line (generator) {e['tau_0.05']['share']:.3f} "
         f"[{e['tau_0.05']['ci95'][0]:.3f}, {e['tau_0.05']['ci95'][1]:.3f}].", "",
         "| candidate | within-5 % | passes the derived ceiling |", "|---|---|---|"]
    for v in d["verdicts_5pct"]:
        L.append(f"| {v['candidate']} ({v['source']}) | {v['within_5pct']:.3f} | {'PASS' if v['pass_derived'] else 'FAIL'} |")
    return "\n".join(L)


def t_e6_6() -> Optional[str]:
    d = _j("e6_6/bound.json")
    if not d:
        return None
    b = d["bound"]; a = b["adopted"]; s = d.get("sweep", {}); lad = d.get("ladder", {})
    L = [f"Adopted: σ_V = {b['params']['sigma_V']:.6f}, h = {b['params']['h']:.2f} d, s_x = {a['s_x']:.4f} (identity with the jumps); "
         f"bound window average **{a['window_avg']:.4f}**, day 200 **{a['day_T']:.4f}**, steady {a['steady_state']:.4f}. "
         f"Sweep: {s.get('n_points')} points, CI lower end above the window-average bound at {s.get('n_ci_lo_above_window_avg')}, "
         f"above the day-200 bound at {s.get('n_ci_lo_above_day_T')}.", "",
         "| rung | arm | n | level-free R²(x) [CI] | bound (window) | increment |", "|---|---|---|---|---|---|"]
    for r in lad.get("rungs", []):
        inc = "—" if r.get("increment_over_previous") is None else f"{r['increment_over_previous']:+.4f}"
        L.append(f"| {r['rung']} | {r['label']} | {r['n_paths']} | {r['levelfree_R2']:.4f} [{r['ci95'][0]:.4f}, {r['ci95'][1]:.4f}] | {r['bound_window_avg']:.4f} | {inc} |")
    return "\n".join(L)


def t_e6_null() -> Optional[str]:
    d = _j("e6_6/null/null.json")
    if not d or not d.get("summary"):
        return None
    L = ["| statistic | pop | BASE | FULL | measured selectivity [paired CI] | half-width | null median | null p95 (draws) | margin | verdict |", "|---|---|---|---|---|---|---|---|---|---|"]
    for k, b in d["summary"].items():
        tg, pop = k.split("|"); n = b["null"]
        nm = "L2 R²(x)" if tg == "x" else "L2b accuracy"
        L.append(f"| {nm} | {pop} | {b['base_value']:+.4f} | {b['full_value']:+.4f} | {b['measured_selectivity']:+.4f} "
                 f"[{b['selectivity_ci95_paired'][0]:+.4f}, {b['selectivity_ci95_paired'][1]:+.4f}] | {b['sampling_halfwidth']:.4f} | "
                 f"{_f(n['median'])} | {_f(n['p95'])} ({n['n_draws']}) | " + (f"{b['derived_margin']:+.4f}" if "derived_margin" in b else "—") + " | "
                 + (("PASS" if b["verdict_under_derived_margin"] else "FAIL") if "derived_margin" in b else "—") + " |")
    return "\n".join(L)


def t_e6_after() -> Optional[str]:
    p = os.path.join(GEN, "e6_after_checklist_reference_items.csv")
    if not os.path.exists(p):
        return None
    pi = pd.read_csv(p)
    v2 = {}
    pa = os.path.join(GEN, "e6_after_checklist.csv")
    if os.path.exists(pa):
        a = pd.read_csv(pa)
        v2 = {int(r["item"]): (None if pd.isna(r["pass"]) else str(r["pass"]) == "True") for _, r in a.iterrows()}
    L = ["| item | property | population | n | A (v2) | B | C |", "|---|---|---|---|---|---|---|"]
    for _, r in pi.iterrows():
        av = v2.get(int(r["item"]))
        L.append(f"| {r['item']} | {r['property']} | {r['population']} | {r['n_gen']} | {'PASS' if av else ('FAIL' if av is False else 'n/a')} | "
                 f"{'PASS' if r['B_pass'] else 'FAIL'} | {'PASS' if r['C_pass'] else 'FAIL'} |")
    ps = os.path.join(GEN, "e6_after_checklist_reference.csv")
    if os.path.exists(ps):
        s = pd.read_csv(ps); s = s[s["is_main"] == True]
        L += ["", "| item | statistic | pop | n_gen / n_ref | gen P50 | ref P50 | B: D (upper) | B | C: share (thr) | C |", "|---|---|---|---|---|---|---|---|---|---|"]
        for _, r in s.iterrows():
            L.append(f"| {r['item']} | `{r['statistic']}` | {r['population']} | {r['n_gen']} / {r['n_ref']} | {r['gen_p50']:.3g} | {r['ref_p50']:.3g} | "
                     f"{r['B_D']:.3f} ({r['B_upper95']:.3f}) | {'PASS' if r['B_pass'] else 'FAIL'} | {r['C_share']:.3f} ({r['C_threshold']:.3f}) | {'PASS' if r['C_pass'] else 'FAIL'} |")
    pe = os.path.join(GEN, "e6_after_checklist_reference_extra.csv")
    if os.path.exists(pe):
        e = pd.read_csv(pe)
        L += ["", "| item | statistic | pop | value | reference | criterion | result | n |", "|---|---|---|---|---|---|---|---|"]
        for _, r in e.iterrows():
            L.append(f"| {r['item']} | {r['statistic']} | {r['population']} | {r['value']:.5g} {r['ci95'] if isinstance(r['ci95'], str) else ''} | {r['reference']} | "
                     f"{r['criterion']} | {'PASS' if r['pass'] else 'FAIL'} | {r['n_gen']} |")
    pl = os.path.join(GEN, "e6_after_checklist_long.json")
    if os.path.exists(pl):
        d = _j("e6_after_checklist_long.json")
        L += ["", "Long horizons (descriptive, 100 flat seeds): " + "; ".join(
            f"T = {T}: ACF(1) of x {v['acf1_x_median']:.4f}, half-life {v['half_life_median']:.1f} d, sd(x) {v['sd_x_median']:.4f}"
            for T, v in d["by_T"].items()) + "."]
    return "\n".join(L)


def t_e6_16a() -> Optional[str]:
    d = _j("e6_16a/16A.json")
    if not d or not d.get("summary", {}).get("G"):
        return None
    s = d["summary"]; m = d["meta"]; rules = d["rules"]
    L = [f"{m['scored']} scored seeds per scenario, {m['train']} training seeds; best simple rule `{rules['best_family']}` "
         f"(scale {rules[rules['best_family']]['scale']}, direction {rules[rules['best_family']]['direction']:+d}).", ""]
    for th, G in s["G"].items():
        tab = s["policies"][th]
        L += [f"**θ = {th}**" + (" — the checkpoint" if float(th) == 0.05 else " (sensitivity)"), "",
              "| scenario | oracle | L5 level-free observables | L5 level-free price-only | best rule | best trivial |", "|---|---|---|---|---|---|"]
        def f(p):
            return "—" if not p else f"{p['mean']:.4f} [{p['ci95'][0]:.4f}, {p['ci95'][1]:.4f}]"
        for sc, t in tab.items():
            L.append(f"| {sc} | {f(t.get('oracle'))} | {f(t.get('L5_full_level_free'))} | {f(t.get('L5_level_free'))} | "
                     f"{f(t.get(G['G2']['best_rule']))} | {t['_best_trivial']}: {f(t.get(t['_best_trivial']))} |")
        g3 = G["G3"]["per_scenario"]
        L += ["", "| gate | per scenario | verdict |", "|---|---|---|",
              f"| G1 | {G['G1']['per_scenario']} | {'PASS' if G['G1']['pass'] else 'FAIL'} |",
              f"| G2 ({G['G2']['n_pass']} of 4) | {G['G2']['per_scenario']} | {'PASS' if G['G2']['pass'] else 'FAIL'} |",
              "| G3 | " + ", ".join(f"{sc}: median {v['median_switches']:.0f}, share≥2 {v['share_ge2']:.2f}" for sc, v in g3.items()) + f" | {'PASS' if G['G3']['pass'] else 'FAIL'} |",
              f"| G4a | {G['G4a']['per_scenario']} | {'PASS' if G['G4a']['pass'] else 'FAIL'} |", ""]
    if "G4b" in s:
        g = s["G4b"]
        L.append(f"G4b: surrogate {g['surrogate_R2']:.4f} [{g['ci95'][0]:.4f}, {g['ci95'][1]:.4f}] vs ceiling {g['ceiling']:.4f} "
                 f"(bound {g['bound_window_avg']:.4f} + allowance {g['allowance_rung4_minus_rung1']:.4f}) → {'PASS' if g['pass'] else 'FAIL'}")
    return "\n".join(L)


GENERATORS: Dict[str, Callable[[], Optional[str]]] = {"e6_9": t_e6_9, "e6_1": t_e6_1, "e6_3": t_e6_3, "e6_2": t_e6_2, "e6_5": t_e6_5,
                                                        "e6_6": t_e6_6, "e6_null": t_e6_null, "e6_after": t_e6_after, "e6_16a": t_e6_16a}


def render(text: str) -> tuple:
    """Returns (new_text, {name: status}) with status in {'updated', 'unchanged', 'no file', 'no block'}."""
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


APPENDIX = os.path.join(ROOT, "docs", "env_v2", "spec", "CALIBRATION_REPORT.md")
FILES = [REPORT, APPENDIX]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--files", default=None, help="comma list; default: the report and the calibration appendix")
    a = ap.parse_args(argv)
    files = [f.strip() for f in a.files.split(",")] if a.files else [f for f in FILES if os.path.exists(f)]
    rc = 0
    for path in files:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        new, status = render(text)
        print(os.path.relpath(path, ROOT))
        for k, v in status.items():
            if v != "no block":
                print(f"  {k:9s} {v}")
        if a.check:
            stale = [k for k, v in status.items() if v == "updated"]
            if stale:
                print("  STALE blocks:", stale); rc = 1
        elif new != text:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(new)
            print("  updated")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
