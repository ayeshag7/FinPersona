"""
E4.19 -- re-registering the inherited criteria against what the generator can express (report section 5,
items 1, 5 and 6; the decision the other items depend on).

    python -m tools.phase4.e4_19_criteria [--n-boot 2000] [--out DIR]

Three registered criteria failed in Phase 4 for three different reasons -- E4.6's coverage threshold (a
premise above the panel's own self-coverage), E4.5's KS equivalence bound (undecidable at the achieved n) and
REG-18's topped share (dominated by the remaining horizon).  Section 5.1 recommended that they share one
root: a panel statistic adopted as a generator target without checking the generator could express it.  That
is a HYPOTHESIS and this module tests it, one criterion at a time, on the STORED per-path output of E4.6 and
the panel episode table -- no regeneration, so nothing here can drift from what was decided on.

It also tests the two claims section 5.1's D5 recommendation rests on.  Both were read off point estimates
and neither had an interval:

  (a) the script-share ranking metric has a NOISE FLOOR, because arm D is unscripted by construction yet
      measures 0.0299.  If so, arms at or below that floor are indistinguishable from unscripted and the
      "adopt the lowest script share" rule cannot rank them.
  (b) correcting the coverage threshold to the panel's own self-coverage still rejects every arm.

Bootstrap over seeds throughout; the seed is the independent unit in E4.6's design.

Output: <out>/criteria.{json,md}
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
E46 = os.path.join(GEN, "e4_6")
ARMS = ["A_lam0.02", "A_lam0.05", "A_lam0.1", "A_lam0.25",
        "B_shifted_pstar", "C_scripted_no_feedback", "D_unscripted_regime"]
UNSCRIPTED = "D_unscripted_regime"   # no scripted path exists, so its script share IS the metric's null
FAST_MAX_DURATION = 126              # dd30_fast's own selection rule (e4_1/episodes4.json)


def boot_ci(v, stat, n_boot, seed=419):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if len(v) < 5:
        return float("nan"), [float("nan")] * 2
    rng = np.random.default_rng(seed)
    b = [stat(v[rng.integers(0, len(v), len(v))]) for _ in range(n_boot)]
    return float(stat(v)), [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


def diff_ci(a, b, stat, n_boot, seed=420):
    """CI on stat(a) - stat(b), resampling each arm independently."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    rng = np.random.default_rng(seed)
    d = [stat(a[rng.integers(0, len(a), len(a))]) - stat(b[rng.integers(0, len(b), len(b))])
         for _ in range(n_boot)]
    return float(stat(a) - stat(b)), [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]


def ks_null_floor(n_acc, n_rej, n_sim=2000, seed=4190):
    """95th percentile of the two-sample KS statistic under the null that both samples share a distribution.
    An equivalence bound below this floor cannot be met however good the generator is."""
    from scipy.stats import ks_2samp
    rng = np.random.default_rng(seed)
    return float(np.percentile([ks_2samp(rng.standard_normal(n_acc), rng.standard_normal(n_rej)).statistic
                                for _ in range(n_sim)], 95))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--out", default=os.path.join(GEN, "e4_19"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    res = {"what": "E4.19: the inherited criteria re-registered against what the generator can express, plus "
                   "the two untested claims behind section 5.1's D5 recommendation.",
           "design": {"source": "e4_6/crash_*.csv (stored per-path output, no regeneration)",
                      "n_boot": a.n_boot, "cluster": "seed"}}

    e41 = json.load(open(os.path.join(GEN, "e4_1", "episodes4.json"), encoding="utf-8"))
    fam = e41["panel_families"]["dd30_fast"]
    q = fam["quantiles"]
    box = {"depth": [q["depth"]["p10"], q["depth"]["p90"]],
           "duration": [q["duration"]["p10"], q["duration"]["p90"]]}
    res["panel_box"] = box
    res["panel_family"] = {"n_episodes": fam["n_episodes"], "n_stocks": fam["n_stocks"],
                           "selection": fam["selection"]}

    # ---------- the panel's own self-coverage, and whether it is a window artefact ----------
    dd = pd.read_csv(os.path.join(GEN, "e4_1", "dd30.csv"))
    fast = dd[dd["duration"] <= FAST_MAX_DURATION]
    inbox = ((fast["depth"] >= box["depth"][0]) & (fast["depth"] <= box["depth"][1]) &
             (fast["duration"] >= box["duration"][0]) & (fast["duration"] <= box["duration"][1]))
    self_cov, self_ci = boot_ci(inbox.to_numpy(float), np.mean, a.n_boot)
    res["panel_self_coverage"] = {
        "value": self_cov, "ci95": self_ci, "n": int(len(fast)),
        "note": "dd30_fast is ALREADY duration-restricted to <= 126 d, i.e. the coverage box is "
                "window-matched on duration before any of this. The 0.643 is not a horizon artefact -- it is "
                "what a P10-P90 box on TWO correlated quantities captures."}

    # ---------- per arm: coverage, where it fails, and the script-share metric ----------
    arms = {}
    for name in ARMS:
        p = os.path.join(E46, "crash_%s.csv" % name)
        if not os.path.exists(p):
            continue
        df = pd.read_csv(p)
        d = pd.to_numeric(df["depth"], errors="coerce")
        u = pd.to_numeric(df["duration"], errors="coerce")
        # E4.6 conditions coverage on the path HAVING a measurable episode (e4_6_dynamics.py:197-199);
        # match that estimand exactly, and report the discarded share separately -- a path with no
        # measurable episode is a different failure from one whose episode falls outside the box.
        meas = d.notna() & u.notna()
        d_ok = (d >= box["depth"][0]) & (d <= box["depth"][1])
        t_ok = (u >= box["duration"][0]) & (u <= box["duration"][1])
        cov, cov_ci = boot_ci((d_ok & t_ok)[meas].to_numpy(float), np.mean, a.n_boot)
        sr, sr_ci = boot_ci(df["script_r2"].to_numpy(float), np.median, a.n_boot)
        arms[name] = {
            "n": int(len(df)),
            "n_measurable": int(meas.sum()),
            "share_no_measurable_episode": float(1.0 - meas.mean()),
            "coverage": cov, "coverage_ci95": cov_ci,
            "fail_depth_only": float(((~d_ok) & t_ok)[meas].mean()),
            "fail_duration_only": float((d_ok & (~t_ok))[meas].mean()),
            "fail_both": float(((~d_ok) & (~t_ok))[meas].mean()),
            "depth_median": float(d[meas].median()),
            "duration_median": float(u[meas].median()),
            "rise_median": float(df["rise"].median()),
            "script_share_median": sr, "script_share_ci95": sr_ci,
        }

    # (a) can the script metric separate an arm from the unscripted null?
    null = pd.read_csv(os.path.join(E46, "crash_%s.csv" % UNSCRIPTED))["script_r2"].to_numpy(float)
    for name in arms:
        if name == UNSCRIPTED:
            arms[name]["vs_unscripted_null"] = {"value": 0.0, "ci95": [0.0, 0.0], "separable": False,
                                                "note": "this arm IS the null"}
            continue
        cur = pd.read_csv(os.path.join(E46, "crash_%s.csv" % name))["script_r2"].to_numpy(float)
        d, ci = diff_ci(cur, null, np.median, a.n_boot)
        arms[name]["vs_unscripted_null"] = {"value": d, "ci95": ci,
                                            "separable": bool(ci[0] > 0 or ci[1] < 0)}

    # (b) corrected threshold: is coverage distinguishable from the panel's own self-coverage?
    for name, v in arms.items():
        lo, hi = v["coverage_ci95"]
        v["vs_panel_self_coverage"] = {
            "panel": self_cov,
            "below_panel_and_separable": bool(hi < self_ci[0]),
            "ci_overlaps_panel": bool(not (hi < self_ci[0] or lo > self_ci[1]))}
    # pairwise coverage differences -- overlapping CIs are a CONSERVATIVE test, not a verdict, so the
    # comparisons section 5.1 leaned on are redone as explicit differences with their own intervals.
    pair = {}
    meas_cov = {}
    for name in arms:
        df = pd.read_csv(os.path.join(E46, "crash_%s.csv" % name))
        d = pd.to_numeric(df["depth"], errors="coerce")
        u = pd.to_numeric(df["duration"], errors="coerce")
        m = d.notna() & u.notna()
        meas_cov[name] = (((d >= box["depth"][0]) & (d <= box["depth"][1]) &
                           (u >= box["duration"][0]) & (u <= box["duration"][1]))[m]).to_numpy(float)
    order = [n for n in ARMS if n in arms]
    for i, x in enumerate(order):
        for y in order[i + 1:]:
            v, ci = diff_ci(meas_cov[x], meas_cov[y], np.mean, a.n_boot, seed=421)
            pair["%s - %s" % (x, y)] = {"value": v, "ci95": ci,
                                        "separable": bool(ci[0] > 0 or ci[1] < 0)}
    res["pairwise_coverage"] = pair
    res["arms"] = arms

    # ---------- the JOINT window constraint: setup + event must fit 200 days ----------
    from envs.v2.schedule import draw_schedule
    rng = np.random.default_rng(4190)
    setups, events = [], []
    for _ in range(4000):
        s = draw_schedule("crash", 200, rng, "setup_first", delta=0.7, schedule_mode="v21")
        setups.append(s.setup_len)
        events.append(s.det_len + s.panic_len)
    setups, events = np.asarray(setups, float), np.asarray(events, float)
    headroom = 200.0 - setups - 10.0     # days left for the event after setup and a minimum resolution
    pd_dur = fast["duration"].to_numpy(float)
    reach = {"setup_p10": float(np.percentile(setups, 10)), "setup_p50": float(np.median(setups)),
             "setup_p90": float(np.percentile(setups, 90)),
             "event_p10": float(np.percentile(events, 10)), "event_p50": float(np.median(events)),
             "event_p90": float(np.percentile(events, 90)),
             "headroom_p50": float(np.median(headroom)),
             "panel_duration_p90": float(box["duration"][1]),
             "panel_episodes_that_fit_a_median_setup": float(np.mean(pd_dur <= np.median(headroom))),
             "panel_episodes_that_fit_the_p90_setup": float(
                 np.mean(pd_dur <= (200.0 - np.percentile(setups, 90) - 10.0)))}
    res["window_reach"] = reach

    # ---------- E4.5's KS bound: the n at which it becomes decidable ----------
    ks = {"registered_bound": 0.10, "achieved": {"n_acc": 419, "n_rej": 81}}
    ks["floor_at_achieved_n"] = ks_null_floor(419, 81)
    curve = {}
    for m in (81, 200, 400, 800, 1600, 3200, 6400):
        curve[m] = ks_null_floor(int(round(m * 419 / 81)), m)
    ks["floor_vs_n_rej"] = curve
    ks["n_rej_needed_for_bound"] = next((m for m, f in curve.items() if f < 0.10), None)
    res["ks_bound"] = ks

    with open(os.path.join(a.out, "criteria.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)

    L = ["# E4.19 the inherited criteria, re-registered against what the generator can express", "",
         res["what"], "",
         "Panel family `dd30_fast`: n = %d episodes, %d stocks. Selection: %s"
         % (fam["n_episodes"], fam["n_stocks"], fam["selection"]), "",
         "## 1. Is the coverage box a window artefact? NO", "",
         "`dd30_fast` is **already** restricted to peak-to-trough duration <= %d d -- the sub-population that "
         "fits a 200-day horizon -- so the box is window-matched on duration before any of this. Its "
         "self-coverage recomputed here: **%.4f [%.4f, %.4f]** (n = %d), reproducing E4.6's 0.643. The 0.70 "
         "threshold sits above it, and that is a property of putting a P10-P90 box on **two correlated "
         "quantities**, not of the horizon."
         % (FAST_MAX_DURATION, self_cov, self_ci[0], self_ci[1], len(fast)), "",
         "## 2. Per arm: coverage, where it fails, and the script metric", "",
         "Coverage matches E4.6's estimand exactly: conditional on the path having a measurable episode. The "
         "discarded share is reported beside it, because a path with no measurable episode is a different "
         "failure from one whose episode lands outside the box.", "",
         "| arm | coverage | 95 % CI | no measurable episode | fail depth only | fail duration only | "
         "fail both | script share | 95 % CI | minus unscripted null | separable |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for n_, v in arms.items():
        vs = v["vs_unscripted_null"]
        L.append("| %s | %.3f | [%.3f, %.3f] | %.3f | %.3f | %.3f | %.3f | %.4f | [%.4f, %.4f] | %+.4f "
                 "[%+.4f, %+.4f] | %s |"
                 % (n_, v["coverage"], v["coverage_ci95"][0], v["coverage_ci95"][1],
                    v["share_no_measurable_episode"],
                    v["fail_depth_only"], v["fail_duration_only"], v["fail_both"],
                    v["script_share_median"], v["script_share_ci95"][0], v["script_share_ci95"][1],
                    vs["value"], vs["ci95"][0], vs["ci95"][1],
                    "**yes**" if vs["separable"] else "no"))
    L += ["", "## 2b. Pairwise coverage differences (an overlap of CIs is not a verdict)", "",
          "| comparison | difference | 95 % CI | separable |", "|---|---|---|---|"]
    for k, v in pair.items():
        L.append("| %s | %+.4f | [%+.4f, %+.4f] | %s |"
                 % (k, v["value"], v["ci95"][0], v["ci95"][1], "**yes**" if v["separable"] else "no"))
    L += ["", "## 3. The joint window constraint, measured on 4000 deployed draws", "",
          "- setup_len p10/p50/p90: %.0f / %.0f / %.0f"
          % (reach["setup_p10"], reach["setup_p50"], reach["setup_p90"]),
          "- realised event length (det + panic) p10/p50/p90: %.0f / %.0f / %.0f"
          % (reach["event_p10"], reach["event_p50"], reach["event_p90"]),
          "- headroom after a median setup and a 10-day minimum resolution: **%.0f d**, against the panel "
          "box's duration p90 of %.0f d" % (reach["headroom_p50"], reach["panel_duration_p90"]),
          "- share of the panel's own target episodes that fit alongside a **median** setup: **%.3f**; "
          "alongside a **p90** setup: **%.3f**"
          % (reach["panel_episodes_that_fit_a_median_setup"],
             reach["panel_episodes_that_fit_the_p90_setup"]), "",
          "## 4. E4.5's KS equivalence bound: the n at which it becomes decidable", "",
          "Null floor (95th percentile of the two-sample KS statistic when both samples share a "
          "distribution) at the achieved n_acc/n_rej = 419/81: **%.3f**, against a registered bound of 0.10 "
          "-- so the bound was **not decidable**." % ks["floor_at_achieved_n"], "",
          "| n_rej (n_acc scaled at the same 419:81 ratio) | null floor |", "|---|---|"]
    for m, f_ in curve.items():
        L.append("| %d | %.3f |" % (m, f_))
    L += ["", "**n_rej needed for the 0.10 bound to be decidable: %s.**"
              % (ks["n_rej_needed_for_bound"] or "more than 6400"), ""]
    with open(os.path.join(a.out, "criteria.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
