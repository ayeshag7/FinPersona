"""
v2.1 Phase 9 -- every report table generated from its file into a marked block (rule 15; the Phase-7 and Phase-8 pattern).

    python -m tools.phase9.e9_report_tables            # rewrite the blocks of PHASE_9_REPORT.md from the files
    python -m tools.phase9.e9_report_tables --check    # exit 1 if any block differs from what the files give

Blocks: <!-- table:NAME --> ... <!-- /table:NAME -->.  A block whose file is absent is left alone and reported as
"no file", not as a mismatch.  `tests/test_v2_1_phase_9.py::test_phase9_report_tables_match_files` runs `--check`.
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
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
REPORT = os.path.join(ROOT, "docs", "env_v2", "v2_1", "PHASE_9_REPORT.md")
DESIGNS_SHOWN = ("headline_12cells", "tierA_shape")
SEEDS_SHOWN = (47, 93)
MS_SHOWN = (3, 4, 5, 6, 8, 10, 12, 14)


def _j(rel):
    p = os.path.join(GEN, rel)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _c(rel):
    p = os.path.join(GEN, rel)
    return pd.read_csv(p) if os.path.exists(p) else None


def _f(x, nd=3):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    return f"{float(x):.{nd}f}"


# ------------------------------------------------------------------------------------------------ E9.0
def t_throughput() -> Optional[str]:
    t = _c("e9_0/throughput.csv")
    d = _j("e9_0/throughput.json")
    if t is None or d is None:
        return None
    t = t[t.config_tag != "untagged"]
    keep = []
    for (_, _), g in t.groupby(["model", "config_tag"]):
        keep.append(g[g.kind == "batch"].iloc[0] if "batch" in set(g.kind) else g[g.kind == "smoke"].iloc[0])
    k = pd.DataFrame(keep).sort_values("runs_per_stream_hour", ascending=False)
    L = ["Every roster configuration, from the ledgers. A configuration timed by smoke has n = 2 runs at low "
         "concurrency, so its seconds per run are a lower bound on a batch's. Measured batch ÷ smoke: "
         + "; ".join(f"{r['model']} {r['batch_over_smoke_mean_s']:.2f}" for r in d["batch_smoke_ratios"]) + ".", "",
         "| model · configuration | timed by | s / run | s / call | reasoning tokens / call | runs per stream-hour | LLM errors / fallbacks |",
         "|---|---|---|---|---|---|---|"]
    for _, r in k.iterrows():
        L.append(f"| {r['model']} · {r['config_tag']} | {r['kind']} (n = {int(r['n_runs'])}) | {r['mean_s_per_run']:.0f} | "
                 f"{r['s_per_call']:.2f} | {r['reasoning_tokens_per_call']:.0f} | {r['runs_per_stream_hour']:.2f} | "
                 f"{int(r['llm_errors'])} / {int(r['fallbacks'])} |")
    return "\n".join(L)


def t_wallclock() -> Optional[str]:
    w = _c("e9_0/wallclock.csv")
    if w is None:
        return None
    w = w[(w.streams == 15) & w.design.isin(DESIGNS_SHOWN) & w.seeds_per_cell.isin(SEEDS_SHOWN)]
    runs = {(d, s): int(w[(w.design == d) & (w.seeds_per_cell == s)]["runs_per_model"].iloc[0]) for d in DESIGNS_SHOWN for s in SEEDS_SHOWN}
    L = ["Days per model at 15 concurrent calls. Every model runs at once, so a roster's wall-clock is its slowest "
         "member's. A smoke-timed rate carries, in brackets, the same design at that rate scaled by the largest "
         "measured batch ÷ smoke ratio.", "",
         "| model · configuration (rate) | " + " | ".join(f"{d} @ {s} seeds ({runs[(d, s)]:,} runs)" for d in DESIGNS_SHOWN for s in SEEDS_SHOWN) + " |",
         "|---|" + "---|" * (len(DESIGNS_SHOWN) * len(SEEDS_SHOWN))]
    for (model, tag, src), g in w.groupby(["model", "config_tag", "rate_source"]):
        cells = []
        for d in DESIGNS_SHOWN:
            for s in SEEDS_SHOWN:
                r = g[(g.design == d) & (g.seeds_per_cell == s)]
                if r.empty:
                    cells.append("—"); continue
                r = r.iloc[0]
                cells.append(f"{r['days']:.1f}" + (f" ({r['hours_smoke_ratio_adjusted'] / 24:.1f})" if src == "smoke" else ""))
        L.append(f"| {model} · {tag} ({src}) | " + " | ".join(cells) + " |")
    return "\n".join(L)


# ------------------------------------------------------------------------------------------------ E9.3
def t_refdist() -> Optional[str]:
    d = _j("e9_3/refdist_fresh.json")
    rc = _j("e9_3/rule_check.json")
    if d is None:
        return None
    reg, r5 = d["recommendation_registered_candidates"], d["recommendation_with_R5"]
    L = [f"Null conditions per M: 48 for the analytic candidates ({d['n_datasets']:,} datasets each), 8 for R3. A "
         "candidate 'breaks' a condition when its size's Wilson lower limit exceeds the nominal level at α = 0.05 or "
         "α′ = 0.05 / 36. R1, R2 and R4 are the registered candidates; R5 was added after their rates were read "
         "(addendum 1) and is judged only on these fresh datasets.", "",
         "| models | R1 breaks | R2 breaks | R4 breaks | R5 breaks | R3 | registered rule | rule with R5 |",
         "|---|---|---|---|---|---|---|---|"]
    for M in MS_SHOWN:
        a, b = reg.get(str(M)), r5.get(str(M))
        if a is None or b is None:
            continue
        r3 = ("holds" if a["holds_size"].get("R3") else "**fails**") if "R3" in a["holds_size"] else "not run"
        L.append(f"| {M} | {a['n_conditions_breaking']['R1']} | {a['n_conditions_breaking']['R2']} | "
                 f"{a['n_conditions_breaking']['R4']} | {b['n_conditions_breaking']['R5']} | {r3} | "
                 f"**{a['recommended'] or 'none'}** | {b['recommended'] or 'none'} |")
    if rc:
        L += ["", f"**An exactly sized test breaks this rule at a given M with probability "
                  f"{rc['exactly_sized_test_fails_rule_per_M_analytic']:.2f}** (48 conditions, both α), so the rule is "
                  f"unmeetable by construction (addendum 3)."]
    return "\n".join(L)


# ------------------------------------------------------------------------------------------------ E9.1
def t_ranking() -> Optional[str]:
    d = _j("e9_1/ranking.json")
    if d is None:
        return None
    t = pd.DataFrame(d["table"])
    dec = d["decision"]
    L = [f"{int(t.ranked.sum())} ranked candidates, each at two levels against the default: 100 seeds × 4 scenarios × "
         f"3 personas per panel. E is the cell-mean standardised effect, the maximum over a parameter's levels; the "
         f"oracle effect averages the two co-primary θ. The share is the fraction of {d['n_boot']:,} seed-bootstrap "
         f"resamples in which the candidate is in the top six.", "",
         "| candidate | in the plan's six | E oracle | E scripted | rank oracle | rank scripted | rank sum | top-six share |",
         "|---|---|---|---|---|---|---|---|"]
    for _, r in t[t.ranked].sort_values("rank_sum").iterrows():
        name = f"**{r['candidate']}**" if r["candidate"] in dec["list_run"] else r["candidate"]
        L.append(f"| {name} | {'yes' if r['plan_six'] else 'no'} | {_f(r['E_oracle'])} | {_f(r['E_scripted'])} | "
                 f"{int(r['rank_oracle'])} | {int(r['rank_scripted'])} | {int(r['rank_sum'])} | {_f(r['top_six_share_boot'], 3)} |")
    L += ["", f"**The data-driven six:** {', '.join(dec['data_driven_six'])}. They share "
              f"{dec['n_shared']} parameters with the plan's six ({', '.join(dec['shared_with_plan'])}), where the rule "
              f"asks for five, so **{dec['run']}** run (P9-6)."]
    cov = [(c[6:], v) for _, r in t.iterrows() for c, v in r.items()
           if c.startswith("level_") and isinstance(v, dict) and (v.get("cells_with_a_resolvable_day_theta_0.05") or 1.0) < 1.0]
    for lvl, v in cov:
        L.append(f"\n**{lvl}** leaves only {v['cells_with_a_resolvable_day_theta_0.05']:.3f} of its path × persona cells "
                 f"with a day resolvable at θ = 0.05 (sd(x) {v['sd_x']:.4f}), so MCR there is undefined on the rest "
                 f"(addendum 4).")
    return "\n".join(L)


GENERATORS = {
    "e9_throughput": t_throughput,
    "e9_wallclock": t_wallclock,
    "e9_refdist": t_refdist,
    "e9_ranking": t_ranking,
}


def t_criteria() -> Optional[str]:
    """E9.3 `criteria` (PREREG 3.2, addendum 9): the three robustness criteria at the shapes the design may take."""
    d = _j("e9_3/criteria.json")
    if d is None:
        return None
    t = pd.DataFrame(d["table"])
    L, S = int(t["L"].max()), int(t["S"].max())
    out = [f"{d['n_conditions']} conditions × {d['n_datasets']:,} datasets. Equivalence margin ± {d['margin']} "
           f"(half of `inference_params` `min_effect.band_mas`), {int(round(d['conf'] * 100))} % interval. The slice "
           f"shown is the design's own: L = {L} non-default levels, S = {S} seeds. τ_LAM is the level × arm × model "
           f"sd; ½τ is half the measured band-MAS σ_d limit. (i) and (iii) are read at a TRUE interaction of 0 — "
           f"every rate below is a FALSE finding except the two marked power.",
           "",
           "| models M | (i) false level-dependent, plain, β = ½Δ | (i) same, significant-only | (ii) holds at every "
           "level, α | (ii) at α′ | (iii) equivalence power, τ_LAM 0 | (iii) power at ½τ | (iii) false equivalence "
           "at the margin |",
           "|---|---|---|---|---|---|---|---|"]
    for M in sorted(t["M"].unique()):
        base = t[(t.M == M) & (t.S == S)]
        i_sl = base[(base.L == L) & (base.tau_lam_label == "half_limit") & (base.beta_label == "half_delta")
                    & (base.int_label == "0")]
        ii = base[(base.beta_label == "delta") & (base.int_label == "0") & (base.L == L)]
        iii0 = base[(base.int_label == "0") & (base.tau_lam_label == "0") & (base.L == L)]
        iiih = base[(base.int_label == "0") & (base.tau_lam_label == "half_limit") & (base.L == L)]
        iiim = base[(base.int_label == "margin") & (base.L == L)]
        out.append(f"| {M} | {_f(i_sl['level_dependent_plain'].mean())} | "
                   f"{_f(i_sl['level_dependent_significant_only'].mean())} | {_f(ii['ii_holds_alpha'].mean())} | "
                   f"{_f(ii['ii_holds_alpha_prime'].mean())} | {_f(iii0['equivalence_declared'].mean())} | "
                   f"{_f(iiih['equivalence_declared'].mean())} | {_f(iiim['equivalence_declared'].mean())} |")
    out += ["", f"**The sign criterion as the plan writes it reaches {_f(d['sign_criterion_false_level_dependent_max'])} "
                f"when the effect is the same at every level**; read as significant-only it reaches "
                f"{_f(d['sign_criterion_false_level_dependent_max_significant_only'])}. Equivalence power at a true "
                f"interaction of 0 spans {_f(d['equivalence_power_at_zero_min'])}–"
                f"{_f(d['equivalence_power_at_zero_max'])} across all conditions, with "
                f"{len(d['shapes_with_zero_equivalence_power'])} shapes at essentially zero; false equivalence at the "
                f"margin stays at or below {_f(d['false_equivalence_at_margin_max'])}."]
    return "\n".join(out)


def t_sizing() -> Optional[str]:
    """E9.2: each roster configuration's band-MAS sigma_d at R = 1, its 90 % limit, and the seed count the maximum
    of those limits gives (P8-16, Appendix A at the Bonferroni alpha')."""
    d = _j("e9_2/sizing.json")
    s = _c("e9_2/sigma.csv")
    if d is None or s is None:
        return None
    bm = s[s["metric"] == "band_mas"]
    bm = bm[bm["Model"].isin(d["roster"])].sort_values("sigma_d_R1_limit90")
    out = [f"Band-MAS σ_d at R = 1 per roster configuration, with its one-sided 90 % chi-square limit. The plug-in is "
           f"the **maximum** of that limit over the roster (P8-16); stage 1's seeds follow Appendix A at the "
           f"Bonferroni α′ = {d['alpha_bonferroni']:.6f} for Δ = {d['delta']}. A pilot truncated by the clock "
           f"(addendum 5) or by a registered seed list (addendum 10) carries fewer df, which **widens** its limit.",
           "",
           "| configuration | σ_d (R = 1) | 90 % limit | df_d | pairs | source |",
           "|---|---|---|---|---|---|"]
    for _, r in bm.iterrows():
        mark = " **← plug-in**" if r["Model"] == d["plugin_model"] else ""
        out.append(f"| `{r['Model']}`{mark} | {_f(r['sigma_d_R1'], 4)} | {_f(r['sigma_d_R1_limit90'], 4)} | "
                   f"{int(r['df_d'])} | {int(r['n_pairs'])} | {r['source']} |")
    not_piloted = ", ".join(f"`{k}`" for k in d.get("not_piloted_registered", []))
    out += ["", f"**Plug-in σ_d = {_f(d['plugin_sigma_d_band_mas'], 4)}**, from `{d['plugin_model']}`, taken over "
                f"**{d['plugin_over_n_of_roster'][0]} of {d['plugin_over_n_of_roster'][1]}** configurations "
                f"({not_piloted} not piloted, P9-10). **Stage 1 seeds by Appendix A: "
                f"{d['stage1_seeds_appA']}** ({d['stage1_seeds_paired_correct']} by the paired-correct count). "
                f"Every roster pilot is complete (`complete`: {d['complete']}); the four configurations dropped by "
                f"P9-7 and P9-8 are reported as `dropped_and_unfinished` and size nothing."]
    return "\n".join(out)


GENERATORS["e9_criteria"] = t_criteria          # defined below the dict, registered here
GENERATORS["e9_sizing"] = t_sizing


def render(text: str) -> tuple:
    status = {}
    for name, gen in GENERATORS.items():
        pat = re.compile(r"(<!-- table:" + re.escape(name) + r" -->\n?)(.*?)(<!-- /table:" + re.escape(name) + r" -->)", re.S)
        m = pat.search(text)
        if not m:
            status[name] = "no block"; continue
        body = gen()
        if body is None:
            status[name] = "no file"; continue
        new = "<!-- table:" + name + " -->\n" + body + "\n" + m.group(3)
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
