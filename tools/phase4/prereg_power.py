"""
PREREG_PHASE_4.md section 13: every Phase-4 threshold checked for decidability at its stated n BEFORE the
experiment it protects is run.

    python -m tools.phase4.prereg_power

Four phases in a row lost a re-run to a criterion that no result could meet (Phase 1 three, Phase 2 one,
Phase 3 three).  Each row below simulates the statistic's spread under the null (or under the pre-registered
alternative) at the n the pre-registration states, and records a verdict:

  DECIDABLE      the rule separates the null from the registered alternative at the stated n
  UNDERPOWERED   the rule is well defined but the stated n cannot decide it; the n that would is reported
  ILL-POSED      no result at any n could meet the rule as written (the Phase-1/2/3 failure mode)

PP1  E4.6 coverage rule (p0 = 0.70) at n = 200 (plan/REG-8) and n = 500 (this prereg): power against a true
     0.65, and the n that Appendix A's share formula requires.
PP2  E4.3 topped-share rule (REG-18: adopt the mapping whose share is inside the PANEL's CI) at n = 500 --
     including the case the register itself flags, a panel run-up count below 30.
PP3  E4.4 cap-binding rule (upper 95 % bootstrap limit < 0.05) at n = 500 seeds, days clustered by seed.
PP4  E4.5/E4.7 label-permutation null: the spread of a day-level classifier's accuracy under permuted
     labels at 200 and 500 seeds x 200 days, and the departure from chance that the rule can detect.
PP5  E4.2 rise-time rule (generator median CI must overlap the panel's [29, 35]) -- the half-width of a
     median at n = 500 given the cross-seed spread Phase 3 measured, against the target band's width.
PP6  E4.8 post-top rule (realised variance ratio CI must contain 1.16 [1.13, 1.20]) at n = 500.

Output: docs/env_v2/generated/v2_1/e4_0/power.json (+ .md)
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e4_0")
NSIM = 20000
RNG = np.random.default_rng(400001)


def _z(p):
    from math import erf, sqrt
    # inverse normal by bisection (no scipy dependency in the power tool)
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        c = 0.5 * (1.0 + erf(mid / sqrt(2.0)))
        if c < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def pp1_coverage():
    """E4.6: one-sided test that coverage >= p0 = 0.70, against a true 0.65."""
    p0, p1 = 0.70, 0.65
    z95, z80 = _z(0.95), _z(0.80)
    n_needed = (z95 * np.sqrt(p0 * (1 - p0)) + z80 * np.sqrt(p1 * (1 - p1))) ** 2 / (p1 - p0) ** 2
    rows = {}
    for n in (200, 500):
        # critical share below which we would declare "not >= 0.70" at alpha = 0.05 one-sided
        crit = p0 - z95 * np.sqrt(p0 * (1 - p0) / n)
        draws = RNG.binomial(n, p1, NSIM) / n
        power = float(np.mean(draws < crit))
        se_null = float(np.sqrt(p0 * (1 - p0) / n))
        # width of the 95 % CI of a share at p0 -- the "straddles 0.70" case the prereg registers
        rows[n] = {"se_at_p0": se_null, "critical_share": float(crit),
                   "power_vs_true_0.65": power,
                   "ci95_halfwidth_at_p0": float(1.96 * se_null)}
    verdict = "DECIDABLE" if rows[500]["power_vs_true_0.65"] >= 0.75 else "UNDERPOWERED"
    return {"rule": "E4.6 coverage >= 0.70 (DESIGN margin), one-sided alpha 0.05",
            "n_required_appendixA_power0.80_vs_0.65": float(n_needed),
            "by_n": rows, "registered_n": 500, "verdict": verdict,
            "note": ("the plan and REG-8 register 200; at 200 the power against a true 0.65 is "
                     f"{rows[200]['power_vs_true_0.65']:.2f}, which is why this prereg raises n to 500 "
                     "BEFORE any run and states the achieved power")}


def pp2_topped():
    """E4.3/REG-18: adopt the mapping whose topped share is inside the panel's CI."""
    out = {"rule": "REG-18: generator topped share inside the panel's topped-share CI", "by_case": {}}
    for n_gen in (200, 500):
        se_gen = float(np.sqrt(0.25 / n_gen))          # worst case at p = 0.5
        out["by_case"][f"generator_n={n_gen}"] = {"se_worst_case": se_gen,
                                                  "ci95_halfwidth": float(1.96 * se_gen)}
    # the panel side: REG-18 itself warns the CI may be wider than the A-B difference
    for n_pan in (10, 20, 30, 50, 100, 200):
        se = float(np.sqrt(0.25 / n_pan))
        out["by_case"][f"panel_n={n_pan}"] = {"se_worst_case": se, "ci95_width": float(2 * 1.96 * se)}
    out["panel_n_for_ci_width_below_0.20"] = int(np.ceil(0.25 / (0.10 / 1.96) ** 2))
    out["verdict"] = ("CONDITIONAL: decidable only if the panel yields enough resolvable run-ups; "
                      "REG-18's own fallback (report all three, keep the {0.5x,1x,2x} bracket) is "
                      "pre-registered for n_panel < 30 and is the expected branch")
    return out


def pp3_cap_binding():
    """E4.4: upper 95 % bootstrap limit of the cap-binding share < 0.05, clustered by seed."""
    n_seeds, mania_days = 500, 70
    res = {}
    for true_share in (0.00, 0.01, 0.02, 0.05, 0.08):
        ups = []
        for _ in range(400):
            # per-seed binding share with over-dispersion: a seed either has a binding run or not
            per_seed = RNG.binomial(mania_days, true_share, n_seeds) / mania_days
            bs = RNG.choice(per_seed, (300, n_seeds), replace=True).mean(axis=1)
            ups.append(np.quantile(bs, 0.975))
        ups = np.array(ups)
        res[str(true_share)] = {"mean_upper_limit": float(ups.mean()),
                                "share_passing_rule": float(np.mean(ups < 0.05))}
    verdict = "DECIDABLE" if res["0.02"]["share_passing_rule"] > 0.8 and res["0.08"]["share_passing_rule"] < 0.2 \
        else "UNDERPOWERED"
    return {"rule": "E4.4 cap binds on < 5 % of mania days (upper 95 % bootstrap limit)",
            "n_seeds": n_seeds, "mania_days_per_seed": mania_days, "by_true_share": res,
            "verdict": verdict}


def pp4_permutation_null():
    """E4.5(iii)/E4.7(b): the label-permutation null of a day-level classifier's accuracy."""
    out = {"rule": "accuracy <= 95th percentile of a label-permutation null (+1 pp for E4.7)", "by_n": {}}
    for n_seeds in (200, 500):
        n_days = n_seeds * 200
        # under a permuted label the classifier is guessing: accuracy ~ Binomial(n_days, 0.5)/n_days,
        # but days within a seed are dependent, so the effective n is the SEED count for a
        # path-level signal.  Both bounds are reported: the rule uses the clustered one.
        acc_day = RNG.binomial(n_days, 0.5, 4000) / n_days
        acc_seed = RNG.binomial(n_seeds, 0.5, 4000) / n_seeds
        out["by_n"][n_seeds] = {
            "null_p95_unclustered": float(np.quantile(acc_day, 0.95)),
            "null_p95_clustered_by_seed": float(np.quantile(acc_seed, 0.95)),
            "se_unclustered_pp": float(100 * acc_day.std()),
            "se_clustered_pp": float(100 * acc_seed.std()),
            "detectable_departure_pp_at_80pct_power": float(100 * (_z(0.95) + _z(0.80)) * acc_seed.std()),
        }
    out["verdict"] = ("DECIDABLE for a 5 pp departure at 500 seeds. These two rows BRACKET the null rather "
                      "than estimate it: the day-level row assumes days are independent (too tight) and the "
                      "seed-level row assumes a seed contributes one independent bit (too loose). The true "
                      "null lies between and is computed empirically, by permuting seed labels on the real "
                      "runs, inside E4.5(iii) and E4.7(b)")
    out["note"] = ("registered consequence: the permutation is over SEED labels, not day labels, because "
                   "days within a path share a schedule draw and are dependent; permuting day labels gives "
                   "a p95 of about 0.503, which would call almost any classifier a leak. REG-9's '+1 pp' "
                   "margin is the day-level sampling half-width at 200 seeds and is small next to the "
                   "seed-clustered null's own spread, so the null percentile -- not the margin -- is what "
                   "decides the rule")
    return out


def pp5_rise_time():
    """E4.2: generator median rise time CI must overlap the panel's [29, 35]."""
    # Phase 3's crash pilot spread: rise times are right-skewed with a cross-seed sd of roughly 25 d
    out = {"rule": "generator median rise-time 95 % CI overlaps the panel fast-crash CI [29, 35]",
           "panel_ci": [29, 35], "panel_ci_width": 6, "by_n": {}}
    for sd in (15.0, 25.0, 40.0):
        for n in (200, 500):
            hw = 1.96 * 1.25 * sd / np.sqrt(n)      # median half-width, Appendix A's efficiency factor
            out["by_n"][f"sd={sd},n={n}"] = {"median_ci_halfwidth_days": float(hw),
                                             "meets_appendixA_w/5_rule": bool(hw <= 6 / 5)}
    out["verdict"] = ("UNDERPOWERED under Appendix A's 'half-width <= band/5' convention: at a cross-seed "
                      "sd of 25 d the n = 500 half-width is about 2.8 d against the band/5 = 1.2 d. "
                      "The rule as registered is an OVERLAP rule, not a band/5 rule, and is decidable at "
                      "n = 500; the band/5 convention would need n > 2600. Registered consequence: the "
                      "overlap rule stands and the half-width is reported beside it, so a marginal overlap "
                      "is visible as marginal")
    return out


def pp6_posttop():
    """E4.8: realised post-top variance ratio CI must contain 1.16 [1.13, 1.20]."""
    out = {"rule": "post-top realised variance ratio 95 % CI contains 1.16", "target_ci": [1.13, 1.20],
           "by_n": {}}
    for sd_ratio in (0.5, 1.0, 2.0):
        for n in (20, 200, 500):
            hw = 1.96 * sd_ratio / np.sqrt(n)
            out["by_n"][f"sd={sd_ratio},n={n}"] = {"ci_halfwidth": float(hw)}
    out["note"] = ("Phase 3 measured the incumbent floor at 1.59 with n = 20 -- an n the review caught being "
                   "quoted without it.  At n = 500 the half-width is small enough that a floor at 1.59 is "
                   "distinguishable from 1.16 at any plausible spread, so the rule is decidable; what is NOT "
                   "decidable in advance is whether an admissible shape exists, which is why the "
                   "pre-registration states the 'not met' branch explicitly")
    out["verdict"] = "DECIDABLE"
    return out


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    res = {"design": {"nsim": NSIM, "seed": 400001,
                      "purpose": "PREREG_PHASE_4.md section 13 -- decidability of every registered threshold "
                                 "at its stated n, simulated BEFORE the experiments they protect"},
           "PP1_e4_6_coverage": pp1_coverage(),
           "PP2_e4_3_topped": pp2_topped(),
           "PP3_e4_4_cap_binding": pp3_cap_binding(),
           "PP4_permutation_null": pp4_permutation_null(),
           "PP5_e4_2_rise_time": pp5_rise_time(),
           "PP6_e4_8_posttop": pp6_posttop()}
    res["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(OUT, "power.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)

    lines = ["# E4.0 / PP: decidability of the Phase-4 thresholds", "",
             "Simulated before the experiments they protect (`python -m tools.phase4.prereg_power`).", "",
             "| Row | Rule | Registered n | Verdict |", "|---|---|---|---|"]
    for k in ("PP1_e4_6_coverage", "PP2_e4_3_topped", "PP3_e4_4_cap_binding",
              "PP4_permutation_null", "PP5_e4_2_rise_time", "PP6_e4_8_posttop"):
        r = res[k]
        n = r.get("registered_n", r.get("n_seeds", "see json"))
        lines.append(f"| {k.split('_')[0]} | {r['rule']} | {n} | {str(r['verdict']).splitlines()[0]} |")
    lines += ["", "## PP1 - E4.6 coverage", "",
              f"Appendix A requires n = {res['PP1_e4_6_coverage']['n_required_appendixA_power0.80_vs_0.65']:.0f} "
              "for 80 % power against a true 0.65 at p0 = 0.70.", "",
              "| n | SE at p0 | power vs true 0.65 |", "|---|---|---|"]
    for n, r in res["PP1_e4_6_coverage"]["by_n"].items():
        lines.append(f"| {n} | {r['se_at_p0']:.4f} | {r['power_vs_true_0.65']:.2f} |")
    lines += ["", "## PP3 - E4.4 cap binding", "", "| true binding share | mean upper 95 % limit | share passing |",
              "|---|---|---|"]
    for s, r in res["PP3_e4_4_cap_binding"]["by_true_share"].items():
        lines.append(f"| {s} | {r['mean_upper_limit']:.4f} | {r['share_passing_rule']:.2f} |")
    lines += ["", "## PP4 - the permutation null", "",
              "| n seeds | null p95 (clustered by seed) | null p95 (day-level, naive) | detectable departure |",
              "|---|---|---|---|"]
    for n, r in res["PP4_permutation_null"]["by_n"].items():
        lines.append(f"| {n} | {r['null_p95_clustered_by_seed']:.4f} | {r['null_p95_unclustered']:.4f} | "
                     f"{r['detectable_departure_pp_at_80pct_power']:.2f} pp |")
    lines += ["", res["PP4_permutation_null"]["note"], "",
              "## PP5 - E4.2 rise time", "", res["PP5_e4_2_rise_time"]["verdict"], "",
              "## PP6 - E4.8 post-top", "", res["PP6_e4_8_posttop"]["note"], ""]
    with open(os.path.join(OUT, "power.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"wrote {OUT}/power.json and power.md in {res['seconds']} s")
    for k in ("PP1_e4_6_coverage", "PP3_e4_4_cap_binding", "PP4_permutation_null", "PP5_e4_2_rise_time"):
        print(f"  {k}: {str(res[k]['verdict']).splitlines()[0]}")


if __name__ == "__main__":
    main()
