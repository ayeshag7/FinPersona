"""
E4.12 -- is the generator's topped share unreachable because of the HORIZON rather than the parameters?

    python -m tools.phase4.e4_12_horizon [--seeds 600] [--workers 3]

E4.11 fitted post_top_drop and post_top_len from the panel and still could not reach the panel's topped share
of 0.110 [0.0966, 0.1245] at ANY half-life -- while the realised post-top drop (P50 -0.239) is DEEPER than the
panel's own median (-0.169).  Those two facts cannot both be explained by the drop being too small.

The hypothesis to test: the panel measures every run-up's outcome over a FULL 200 trading days after its top,
whereas a generated bull-trap path tops at some point inside its own 200-day horizon and has only T - top_day
days left.  If so, the topped share is a HORIZON property of the benchmark and not a parameter defect, and no
setting of the hazard or the leg can reach it.

Falsifier: restrict the generator's topped share to paths with a long post-top window.  If the share rises
toward the panel's band as the available window grows, the horizon is the cause; if it stays near zero, it is
not, and the parameters are still wrong.

The panel side is re-measured the same way for comparison: its topped share restricted to run-ups whose
post-top window is itself short.

Output: docs/env_v2/generated/v2_1/e4_12/horizon.{json,md}
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
OUT = os.path.join(GEN, "e4_12")
SEED0 = 310000
N_BOOT = 2000
T = 200


def _one(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    seed, cfg = args
    env = SyntheticMarketEnv("bull_trap", 200, seed, config=cfg)
    d = env.data[env.data["asset"] == 0]
    p = d["price"].to_numpy(float)
    day = d["day"].to_numpy(int)
    m = env.event_meta
    out = {"seed": seed, "topped_hazard": bool(m.get("topped")),
           "post_top_drop_drawn": float(env.schedule.post_top_drop),
           "post_top_len_drawn": int(env.schedule.post_top_len)}
    td = m.get("top_day_realised") or m.get("top_day")
    if td is None:
        return out
    out["top_day"] = int(td)
    out["days_remaining"] = int(T - td)
    i = int(np.argmax(day >= td))
    seg = p[i:]
    if len(seg) > 1:
        out["realised_drop"] = float(np.nanmin(seg) / p[i] - 1.0)
        out["topped_panel_rule"] = bool(out["realised_drop"] <= -0.40)
    return out


def pmap(items, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_one, items, chunksize=4))


def share_ci(flags, n_boot=N_BOOT, seed=4120):
    f = np.asarray([bool(x) for x in flags], bool)
    if len(f) < 5:
        return None, None, len(f)
    rng = np.random.default_rng(seed)
    bs = [float(f[rng.integers(0, len(f), len(f))].mean()) for _ in range(n_boot)]
    return float(f.mean()), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], len(f)


def panel_by_window():
    """The panel's own topped share, restricted by how much post-top window each run-up actually had.

    A run-up whose top is near the end of the price series has a truncated window in the panel too; E4.1's
    `runup_outcome` used min(top + 200, len - 1), so the available window is recoverable."""
    from tools.phase1.panel import analysis_sets, load_prices
    ru = pd.read_csv(os.path.join(GEN, "e4_1", "runup4.csv"))
    A = analysis_sets(write=False)["A"]
    px = load_prices(A).ffill()
    n_by = {t: int(np.isfinite(px[t].to_numpy(float)).nonzero()[0].max() + 1)
            if t in px.columns and np.isfinite(px[t].to_numpy(float)).any() else 0 for t in A}
    ru = ru[ru["post_drop"].notna()].copy()
    ru["window"] = [min(200, max(n_by.get(t, 0) - 1 - int(tp), 0))
                    for t, tp in zip(ru["ticker"], ru["top"])]
    ru["topped"] = ru["post_drop"] <= -0.40
    out = {}
    for lo, hi in ((0, 50), (50, 100), (100, 150), (150, 201)):
        g = ru[(ru["window"] >= lo) & (ru["window"] < hi)]
        if len(g) >= 20:
            pt, ci, n = share_ci(g["topped"].to_numpy(bool), seed=4121)
            out[f"{lo}-{hi}"] = {"topped_share": pt, "ci95": ci, "n": n,
                                 "median_drop": float(g["post_drop"].median())}
    pt, ci, n = share_ci(ru["topped"].to_numpy(bool), seed=4122)
    out["all"] = {"topped_share": pt, "ci95": ci, "n": n,
                  "median_window": float(ru["window"].median())}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=600)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    e41 = json.load(open(os.path.join(GEN, "e4_1", "episodes4.json"), encoding="utf-8"))
    panel_all = e41["runups"]["topped_share_200d"]
    e411 = json.load(open(os.path.join(GEN, "e4_11", "posttop_recal.json"), encoding="utf-8"))
    fitted = e411["panel_fit"]

    # the adopted E4.11 configuration: FIT drop/length ranges, half-life 10
    ru = pd.read_csv(os.path.join(GEN, "e4_1", "runup4.csv"))
    d = ru[ru["post_drop"].notna() & ru["post_len"].notna()]
    qs = np.linspace(0.10, 0.90, 33)
    ranges = {"post_top_drop": {"grid": [float(x) for x in np.quantile(
                  np.abs(pd.to_numeric(d["post_drop"], errors="coerce").to_numpy(float)), qs)]},
              "post_top_len": {"grid": [float(x) for x in np.quantile(
                  pd.to_numeric(d["post_len"], errors="coerce").to_numpy(float), qs)]}}
    cfg = {"schedule_mode": "v21", "schedule_ranges": ranges,
           "post_top_mode": "decay", "post_top_half_life": 10.0}

    print(f"[gen] {a.seeds} bull-trap seeds on the E4.11-adopted configuration ...", flush=True)
    rows = pmap([(s, cfg) for s in range(SEED0, SEED0 + a.seeds)], a.workers)
    df = pd.DataFrame(rows)
    topped = df[df["topped_hazard"] & df["days_remaining"].notna()].copy()

    res = {"design": {"seeds": a.seeds, "seed0": SEED0, "T": T, "config": "E4.11-adopted (FIT drop and "
                      "length grids, decay half-life 10), schedule_mode pinned to v21",
                      "hypothesis": "the topped share is unreachable because a generated path tops INSIDE "
                                    "its own 200-day horizon and has only T - top_day days left, whereas the "
                                    "panel gives every run-up a full 200 days after its top",
                      "falsifier": "restrict the generator to paths with a long post-top window; if the "
                                   "share rises toward the panel's band the horizon is the cause"},
           "panel_topped_share_all": panel_all,
           "panel_fitted_drop_len": fitted}

    res["generator_days_remaining"] = {
        "p10": float(topped["days_remaining"].quantile(0.10)),
        "p50": float(topped["days_remaining"].quantile(0.50)),
        "p90": float(topped["days_remaining"].quantile(0.90)),
        "share_with_at_least_120_days": float((topped["days_remaining"] >= 120).mean()),
        "n_topped_paths": int(len(topped)),
        "panel_post_top_length_p50": fitted["len_p10_p50_p90"][1]}
    print(f"    days remaining after the top: P10 {res['generator_days_remaining']['p10']:.0f} / "
          f"P50 {res['generator_days_remaining']['p50']:.0f} / "
          f"P90 {res['generator_days_remaining']['p90']:.0f}; "
          f"{res['generator_days_remaining']['share_with_at_least_120_days']:.3f} have 120+ days "
          f"(the panel's median post-top length is {fitted['len_p10_p50_p90'][1]:.0f} d)", flush=True)

    res["generator_by_window"] = {}
    for lo, hi in ((0, 50), (50, 100), (100, 150), (150, 201)):
        g = topped[(topped["days_remaining"] >= lo) & (topped["days_remaining"] < hi)]
        if len(g) >= 10:
            pt, ci, n = share_ci(g["topped_panel_rule"].fillna(False).to_numpy(bool), seed=4123)
            res["generator_by_window"][f"{lo}-{hi}"] = {
                "topped_share": pt, "ci95": ci, "n": n,
                "median_realised_drop": float(g["realised_drop"].median()),
                "median_drawn_drop": float(g["post_top_drop_drawn"].median())}
            print(f"    days remaining {lo:3d}-{hi:3d}: topped {pt:.4f} {[round(v,4) for v in ci]} "
                  f"n={n}  realised drop P50 {float(g['realised_drop'].median()):.3f}", flush=True)

    print("[panel] the same restriction on the panel ...", flush=True)
    res["panel_by_window"] = panel_by_window()
    for k, v in res["panel_by_window"].items():
        if k != "all":
            print(f"    window {k:>8s}: topped {v['topped_share']:.4f} "
                  f"{[round(z,4) for z in v['ci95']]} n={v['n']}", flush=True)

    # ---- verdict: the correct test is WITHIN-BIN, generator against panel on the SAME available window.
    # Comparing the generator's overall share with the panel's overall share is not like for like, because
    # the two populations have completely different post-top windows -- which is the hypothesis.
    gw, pw = res["generator_by_window"], res["panel_by_window"]
    matched = {}
    for k in ("0-50", "50-100", "100-150", "150-201"):
        g, p_ = gw.get(k), pw.get(k)
        if g and p_:
            overlap = not (g["ci95"][1] < p_["ci95"][0] or g["ci95"][0] > p_["ci95"][1])
            matched[k] = {"generator": g["topped_share"], "generator_ci95": g["ci95"], "n_gen": g["n"],
                          "panel": p_["topped_share"], "panel_ci95": p_["ci95"], "n_panel": p_["n"],
                          "cis_overlap": bool(overlap)}
    agree = bool(matched) and all(v["cis_overlap"] for v in matched.values())
    bins_gen = [k for k in ("100-150", "150-201") if k in gw]
    share_long = res["generator_days_remaining"]["share_with_at_least_120_days"]
    res["verdict"] = {
        "window_matched_comparison": matched,
        "generator_matches_panel_within_every_shared_window_bin": agree,
        "generator_bins_at_120_plus_days": bins_gen,
        "share_of_generator_topped_paths_with_120_plus_days": share_long,
        "panel_share_at_150_201_days": (pw.get("150-201") or {}).get("topped_share"),
        "conclusion": (
            "HORIZON -- within every window bin the two populations share, the generator's topped share "
            "agrees with the panel's; the panel's headline 0.110 comes almost entirely from run-ups that "
            "have a 150-200 day post-top window, and only "
            f"{share_long:.1%} of generated topped paths have even 120 days left (median "
            f"{res['generator_days_remaining']['p50']:.0f}). The topped share is therefore a property of "
            "fitting a mania AND its aftermath into one 200-day horizon, not a parameter defect, and the "
            "hazard's adoption criterion cannot be met on the deployed state as it is written. It must be "
            "re-expressed on a window-matched basis."
            if agree and share_long < 0.10 else
            "NOT THE HORIZON -- the generator's share differs from the panel's even within a shared window "
            "bin, so the parameters are still wrong"
            if not agree else
            "MIXED -- see the window-matched table")}
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(os.path.join(OUT, "horizon.json"), "w", encoding="utf-8"), indent=1, default=str)

    L = ["# E4.12 - is the topped share a horizon property?", "",
         "`python -m tools.phase4.e4_12_horizon`", "",
         f"{a.seeds} bull-trap seeds on E4.11's adopted configuration, `schedule_mode` pinned to v21.", "",
         f"**Hypothesis.** {res['design']['hypothesis']}", "",
         f"**Falsifier.** {res['design']['falsifier']}", "",
         "## Days remaining after the realised top", "",
         f"P10 {res['generator_days_remaining']['p10']:.0f} / P50 "
         f"{res['generator_days_remaining']['p50']:.0f} / P90 "
         f"{res['generator_days_remaining']['p90']:.0f} trading days; "
         f"{res['generator_days_remaining']['share_with_at_least_120_days']:.1%} of topped paths have 120 or "
         f"more. The panel's median post-top length is {fitted['len_p10_p50_p90'][1]:.0f} d and its P90 is "
         f"{fitted['len_p10_p50_p90'][2]:.0f} d.", "",
         "## Topped share by the window actually available", "",
         "| days remaining | generator | 95 % CI | n | panel (same restriction) | 95 % CI | n |",
         "|---|---|---|---|---|---|---|"]
    for k in ("0-50", "50-100", "100-150", "150-201"):
        g = res["generator_by_window"].get(k)
        p_ = res["panel_by_window"].get(k)
        if not g:
            continue
        L.append(f"| {k} | {g['topped_share']:.4f} | [{g['ci95'][0]:.4f}, {g['ci95'][1]:.4f}] | {g['n']} | "
                 + (f"{p_['topped_share']:.4f} | [{p_['ci95'][0]:.4f}, {p_['ci95'][1]:.4f}] | {p_['n']} |"
                    if p_ else "- | - | - |"))
    L += ["", "## Window-matched verdict", "",
          "| days remaining | generator | panel | CIs overlap |", "|---|---|---|---|"]
    for k, v in res["verdict"]["window_matched_comparison"].items():
        L.append(f"| {k} | {v['generator']:.4f} (n={v['n_gen']}) | {v['panel']:.4f} (n={v['n_panel']}) | "
                 f"**{v['cis_overlap']}** |")
    L += ["", f"Panel, all run-ups: **{panel_all['point']:.4f} "
              f"[{panel_all['ci95'][0]:.4f}, {panel_all['ci95'][1]:.4f}]** (n = {panel_all['n_episodes']}).",
          "", "## Verdict", "", f"**{res['verdict']['conclusion']}**", ""]
    open(os.path.join(OUT, "horizon.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"\nVERDICT: {res['verdict']['conclusion']}")
    print(f"wrote {OUT}/horizon.json in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
