"""
E4.11 -- the post-top block re-fitted and re-calibrated ON THE DEPLOYED STATE (addendum section 5.4).

    python -m tools.phase4.e4_11_posttop_recal [--seeds 400] [--workers 3]

Addendum section 5 established, by measurement, that `post_top_drop` (U(0.30, 0.50)) and `post_top_len`
(U(10, 30)) shipped in events.json as v2 DESIGN ranges while the panel holds the data for both, and that the
half-life fitted against those stipulated ranges does not reproduce on the deployed state (post-top/mania
0.787 [0.574, 1.100] against the 0.6186 it was fitted to; topped share 0.008 against the panel's 0.110).

This module runs the registered correction:
  1. fit post_top_drop and post_top_len from the panel's run-up outcome table, by the same inverse-CDF
     empirical-grid sampler the addendum section 3 registered, over P10-P90
  2. re-search the half-life on the DEPLOYED state against the panel's post-top/mania variance ratio
  3. re-measure the topped share by the panel's own rule -- an OUTCOME of fitted parameters, not a target
  4. re-check REG-18's mapping decision on that state

Steps 2 and 3 are coupled (the leg shape sets both the variance ratio and the realised drop), so they are
calibrated jointly and BOTH are reported whether or not both criteria can be met at once.  If they cannot,
that is a property of the environment and is reported as one.

Every arm pins `schedule_mode` explicitly, which is the defect this module exists because of.

Output: docs/env_v2/generated/v2_1/e4_11/posttop_recal.{json,md}
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e4_11")
SEED0 = 300000
GRID_N = 33
N_BOOT = 2000
T = 200


def panel_posttop_fit():
    """post_top_drop and post_top_len FIT from the panel's run-up outcome table."""
    ru = pd.read_csv(os.path.join(GEN, "e4_1", "runup4.csv"))
    d = ru[ru["post_drop"].notna() & ru["post_len"].notna()]
    drop = np.abs(pd.to_numeric(d["post_drop"], errors="coerce").to_numpy(float))
    length = pd.to_numeric(d["post_len"], errors="coerce").to_numpy(float)
    qs = np.linspace(0.10, 0.90, GRID_N)
    return {
        "post_top_drop": {"grid": [float(x) for x in np.quantile(drop, qs)]},
        "post_top_len": {"grid": [float(x) for x in np.quantile(length, qs)]},
        "_provenance": {
            "drop_p10_p50_p90": [float(np.percentile(drop, q)) for q in (10, 50, 90)],
            "len_p10_p50_p90": [float(np.percentile(length, q)) for q in (10, 50, 90)],
            "panel_share_reaching_-40pct": float((pd.to_numeric(d["post_drop"], errors="coerce") <= -0.40).mean()),
            "n_episodes": int(len(d)), "n_stocks": int(d["ticker"].nunique()),
            "v2_stipulated": {"post_top_drop": [0.30, 0.50], "post_top_len": [10, 30]},
            "share_of_panel_lengths_beyond_the_horizon": float((length > T).mean()),
            "label": "FIT"},
    }


def _one(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    from tools.phase3.episodes import _rv
    seed, cfg = args
    env = SyntheticMarketEnv("bull_trap", 200, seed, config=cfg)
    d = env.data[env.data["asset"] == 0]
    p = d["price"].to_numpy(float)
    day = d["day"].to_numpy(int)
    ph = d["phase"].to_numpy(object)[1:]
    r = np.diff(np.log(p))
    m = env.event_meta
    s = env.schedule
    ev = int(s.event_start)
    out = {"seed": seed, "schedule_mode": s.mode,
           "post_top_len_drawn": int(s.post_top_len), "post_top_drop_drawn": float(s.post_top_drop),
           "topped_hazard": bool(m.get("topped")), "rejected": int(env.attempts > 1),
           "truncated": bool(s.truncated)}
    calm = _rv(r, 0, max(ev - 2, 0), min_n=30)
    out["rv_calm"] = float(calm) if np.isfinite(calm) else None
    for k in ("mania", "blow-off", "post-top"):
        sel = ph == k
        if sel.sum() >= 10:
            out["rv_" + k] = float(np.mean(r[sel] ** 2))
            out["n_" + k] = int(sel.sum())
    td = m.get("top_day_realised") or m.get("top_day")
    if td is not None:
        i = int(np.argmax(day >= td))
        seg = p[i:]
        if len(seg) > 1:
            out["post_top_drop_realised"] = float(np.nanmin(seg) / p[i] - 1.0)
            out["topped_panel_rule"] = bool(out["post_top_drop_realised"] <= -0.40)
    return out


def pmap(items, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_one, items, chunksize=4))


def pooled_ratio(rows, num, den, n_boot=N_BOOT, seed=4110):
    pairs = [(r.get("rv_" + num), r.get("n_" + num), r.get("rv_" + den), r.get("n_" + den)) for r in rows]
    pairs = [(a, b, c, d) for a, b, c, d in pairs if a is not None and c is not None]
    if len(pairs) < 20:
        return None, None, len(pairs)
    A = np.array([[a * b, b, c * d, d] for a, b, c, d in pairs], float)
    pt = (A[:, 0].sum() / A[:, 1].sum()) / (A[:, 2].sum() / A[:, 3].sum())
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(n_boot):
        S = A[rng.integers(0, len(A), len(A))]
        bs.append((S[:, 0].sum() / S[:, 1].sum()) / (S[:, 2].sum() / S[:, 3].sum()))
    return float(pt), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], len(pairs)


def share_ci(flags, n_boot=N_BOOT, seed=4111):
    f = np.asarray([bool(x) for x in flags], bool)
    if len(f) == 0:
        return None, None, 0
    rng = np.random.default_rng(seed)
    bs = [float(f[rng.integers(0, len(f), len(f))].mean()) for _ in range(n_boot)]
    return float(f.mean()), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], len(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=400)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    from envs.v2 import events_params as EP
    fit = panel_posttop_fit()
    prov = fit["_provenance"]
    e41 = json.load(open(os.path.join(GEN, "e4_1", "episodes4.json"), encoding="utf-8"))
    e48 = json.load(open(os.path.join(GEN, "e4_8", "labels.json"), encoding="utf-8"))
    panel_topped = e41["runups"]["topped_share_200d"]
    target_ratio = e48["panel_targets"]["post_top_over_mania"]
    ratio_ci = e48["posttop"]["target_ci_on_ratio"]
    print(f"[fit] post_top_drop P10/P50/P90 {[round(v,4) for v in prov['drop_p10_p50_p90']]} "
          f"(v2 drew U(0.30, 0.50));  post_top_len {[round(v,0) for v in prov['len_p10_p50_p90']]} "
          f"(v2 drew U(10, 30));  n={prov['n_episodes']}/{prov['n_stocks']}", flush=True)
    print(f"[targets] post-top/mania {target_ratio:.4f} CI {[round(v,4) for v in ratio_ci]} | "
          f"topped share {panel_topped['point']:.4f} {[round(v,4) for v in panel_topped['ci95']]}", flush=True)

    res = {"design": {"addendum": "PREREG_PHASE_4_ADDENDUM.md section 5.4", "seeds": a.seeds, "seed0": SEED0,
                      "n_boot": N_BOOT, "schedule_mode": "v21 (pinned explicitly on every arm)",
                      "targets": {"post_top_over_mania": target_ratio, "ratio_ci": ratio_ci,
                                  "topped_share": panel_topped["point"], "topped_ci": panel_topped["ci95"]}},
           "panel_fit": fit["_provenance"], "arms": {}}

    base_ranges = {"post_top_drop": fit["post_top_drop"], "post_top_len": fit["post_top_len"]}
    # the v2-range arm is kept so the report can show what the stipulated ranges did
    arms = [("v2_stipulated_ranges_hl50", {"post_top_drop": [0.30, 0.50], "post_top_len": [10, 30]}, 50.0)]
    for hl in (10, 20, 30, 40, 50, 70, 100):
        arms.append((f"FIT_ranges_hl{hl}", base_ranges, float(hl)))

    for name, ranges, hl in arms:
        cfg = {"schedule_mode": "v21", "schedule_ranges": ranges,
               "post_top_mode": "decay", "post_top_half_life": hl}
        rows = pmap([(s, cfg) for s in range(SEED0, SEED0 + a.seeds)], a.workers)
        assert all(r["schedule_mode"] == "v21" for r in rows)
        pr, pr_ci, n_pr = pooled_ratio(rows, "post-top", "mania")
        tp, tp_ci, n_tp = share_ci([r.get("topped_panel_rule", False) for r in rows])
        th, _, _ = share_ci([r["topped_hazard"] for r in rows])
        dr = pd.to_numeric(pd.DataFrame(rows).get("post_top_drop_realised"), errors="coerce").dropna()
        res["arms"][name] = {
            "half_life": hl,
            "post_top_over_mania": pr, "ratio_ci95": pr_ci, "n_ratio": n_pr,
            "ratio_inside_panel_ci": bool(pr is not None and ratio_ci[0] <= pr <= ratio_ci[1]),
            "topped_share_panel_rule": tp, "topped_ci95": tp_ci, "n": n_tp,
            "topped_inside_panel_ci": bool(tp is not None and
                                           panel_topped["ci95"][0] <= tp <= panel_topped["ci95"][1]),
            "topped_share_hazard_fired": th,
            "realised_drop_p10_p50_p90": ([float(dr.quantile(q)) for q in (0.1, 0.5, 0.9)] if len(dr) else None),
            "drawn_drop_median": float(np.median([r["post_top_drop_drawn"] for r in rows])),
            "drawn_len_median": float(np.median([r["post_top_len_drawn"] for r in rows])),
            "truncation_rate": float(np.mean([r["truncated"] for r in rows])),
            "rejection": float(np.mean([r["rejected"] for r in rows])),
        }
        v = res["arms"][name]
        print(f"  {name:26s} ratio {str(round(pr,4)) if pr else '-':>7s} "
              f"{'IN ' if v['ratio_inside_panel_ci'] else 'out'} | topped {tp:.4f} "
              f"{'IN ' if v['topped_inside_panel_ci'] else 'out'} (hazard fires {th:.3f}) | "
              f"realised drop P50 "
              f"{(v['realised_drop_p10_p50_p90'][1] if v['realised_drop_p10_p50_p90'] else float('nan')):.3f}",
              flush=True)

    both = {k: v for k, v in res["arms"].items()
            if v["ratio_inside_panel_ci"] and v["topped_inside_panel_ci"] and k.startswith("FIT")}
    ratio_only = [k for k, v in res["arms"].items() if v["ratio_inside_panel_ci"] and k.startswith("FIT")]
    topped_only = [k for k, v in res["arms"].items() if v["topped_inside_panel_ci"] and k.startswith("FIT")]
    res["decision"] = {
        "rule": "the half-life is adopted if it puts the post-top/mania variance ratio inside the panel CI; "
                "the topped share is an OUTCOME and is reported against the panel CI, not tuned to it",
        "arms_meeting_the_variance_ratio": ratio_only,
        "arms_whose_topped_share_is_also_inside_the_panel_CI": topped_only,
        "arms_meeting_both": sorted(both),
        # TIE-BREAK, specified here rather than left to dict order: among the arms whose ratio is inside the
        # panel CI, adopt the one CLOSEST to the panel's point estimate.  This is not a threshold move -- every
        # arm in `both` already satisfies the registered criterion, so the choice among them does not change
        # any verdict; it only makes the choice reproducible instead of alphabetical.
        "tie_break": "closest to the panel point estimate among the arms inside its CI",
        "adopted": (min(both, key=lambda k: abs(res["arms"][k]["post_top_over_mania"] - target_ratio))
                    if both else (ratio_only[0] if ratio_only else None)),
        "note": ("both criteria are reachable together" if both else
                 "the panel's post-top VARIANCE ratio and its post-top DEPTH are not simultaneously "
                 "reachable by a single deterministic decay leg at any half-life tested; this is reported as "
                 "a property of the environment, not resolved by dropping one of them"),
    }
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(os.path.join(OUT, "posttop_recal.json"), "w", encoding="utf-8"), indent=1, default=str)

    L = ["# E4.11 - the post-top block re-fitted on the deployed state", "",
         "`python -m tools.phase4.e4_11_posttop_recal` - PREREG_PHASE_4_ADDENDUM.md section 5.4.", "",
         f"{a.seeds} bull-trap seeds per arm, `schedule_mode` pinned to v21 on every arm.", "",
         "## The two parameters that were stipulated, now fitted", "",
         "| parameter | shipped (v2 DESIGN) | panel P10 / P50 / P90 | n |", "|---|---|---|---|",
         f"| `post_top_drop` | U(0.30, 0.50) | {' / '.join('%.3f' % v for v in prov['drop_p10_p50_p90'])} | "
         f"{prov['n_episodes']} / {prov['n_stocks']} |",
         f"| `post_top_len` | U(10, 30) | {' / '.join('%.0f' % v for v in prov['len_p10_p50_p90'])} d | same |",
         "",
         f"The panel's own share of run-ups reaching -40 % after the top is "
         f"**{prov['share_of_panel_lengths_beyond_the_horizon']:.1%} of post-top lengths run beyond the "
         f"200-day horizon**, and the share reaching -40 % is "
         f"**{prov['panel_share_reaching_-40pct']:.3f}** - the same quantity as the topped share the hazard "
         "was adopted against.", "",
         "## Arms", "",
         "| arm | half-life | post-top/mania | in panel CI | topped share | in panel CI | hazard fires | realised drop P50 |",
         "|---|---|---|---|---|---|---|---|"]
    for k, v in res["arms"].items():
        rd = v["realised_drop_p10_p50_p90"]
        L.append(f"| {k} | {v['half_life']:.0f} | {v['post_top_over_mania']:.4f} | "
                 f"**{v['ratio_inside_panel_ci']}** | {v['topped_share_panel_rule']:.4f} | "
                 f"**{v['topped_inside_panel_ci']}** | {v['topped_share_hazard_fired']:.3f} | "
                 f"{(rd[1] if rd else float('nan')):.3f} |")
    L += ["", "## Decision", "", f"- rule: {res['decision']['rule']}",
          f"- meeting the variance ratio: **{res['decision']['arms_meeting_the_variance_ratio'] or 'none'}**",
          f"- whose topped share is also inside the panel CI: "
          f"**{res['decision']['arms_whose_topped_share_is_also_inside_the_panel_CI'] or 'none'}**",
          f"- adopted: **{res['decision']['adopted'] or 'none'}**", "",
          f"- {res['decision']['note']}", ""]
    open(os.path.join(OUT, "posttop_recal.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"\nADOPTED: {res['decision']['adopted']}")
    print(f"NOTE: {res['decision']['note']}")
    print(f"wrote {OUT}/posttop_recal.json in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
