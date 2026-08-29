"""
Calibrate the bubble-top hazard h_t = h0 exp(b x_t) (plan 2.1 block 3; checklist 11):
target ~50% of bull-trap seeds topped inside T = 200 and a median peak P/V of
1.6-2.5 among topped seeds.  Grid search over (h0, b); writes
envs/v2/params/hazard.json with the chosen pair and the full grid table to
docs/env_v2/generated/hazard_calibration.csv.

Usage: python -m tools.calibrate_hazard [--seeds 60]
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from envs.v2.generator import GenConfig, generate  # noqa: E402
from envs.v2.mispricing import PARAM_DIR  # noqa: E402


def evaluate(h0: float, b: float, seeds: int, T: int = 200, g_max: float = 0.012) -> dict:
    topped, peak_t, peak_u, top_days, att = [], [], [], [], []
    for s in range(seeds):
        r = generate(GenConfig(scenario="bull_trap", seed=s, T=T, hazard_h0=h0, hazard_b=b, g_max=g_max))
        m = r.day >= 1
        pv = float(np.exp(r.x[0, m]).max())
        t = bool(r.event_meta.get("topped"))
        topped.append(t); att.append(r.attempts)
        (peak_t if t else peak_u).append(pv)
        if t:
            top_days.append(r.event_meta["top_day"] - r.schedule.event_start)
    return {"h0": h0, "b": b, "g_max": g_max, "topped_share": float(np.mean(topped)),
            "peak_pv_topped_median": float(np.median(peak_t)) if peak_t else np.nan,
            "peak_pv_topped_q10": float(np.quantile(peak_t, 0.1)) if peak_t else np.nan,
            "peak_pv_topped_q90": float(np.quantile(peak_t, 0.9)) if peak_t else np.nan,
            "peak_pv_untopped_median": float(np.median(peak_u)) if peak_u else np.nan,
            "top_day_in_mania_median": float(np.median(top_days)) if top_days else np.nan,
            "mean_attempts": float(np.mean(att))}


def score(row: dict) -> float:
    # distance to the target box: topped 0.5, topped peak median 2.0 (inside 1.6-2.5)
    s = abs(row["topped_share"] - 0.5) * 4
    med = row["peak_pv_topped_median"]
    if np.isnan(med):
        return 9e9
    s += max(0.0, 1.6 - med) + max(0.0, med - 2.5) + 0.25 * abs(med - 2.0)
    # early tops (x_top < 0.30) are rejected runs: keep the joint conditioning below the 5% target
    s += 5.0 * max(0.0, row["mean_attempts"] - 1.05)
    return s


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=60)
    a = ap.parse_args()
    rows = []
    for g_max, h0, b in itertools.product([0.010, 0.012, 0.015], [1e-4, 3e-4, 1e-3, 3e-3], [4.0, 6.0, 8.0]):
        row = evaluate(h0, b, a.seeds, g_max=g_max)
        row["score"] = score(row)
        rows.append(row)
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}, flush=True)
    df = pd.DataFrame(rows).sort_values("score")
    out_dir = os.path.join(ROOT, "docs", "env_v2", "generated")
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(os.path.join(out_dir, "hazard_calibration.csv"), index=False)
    best = df.iloc[0].to_dict()
    os.makedirs(PARAM_DIR, exist_ok=True)
    with open(os.path.join(PARAM_DIR, "hazard.json"), "w", encoding="utf-8") as fh:
        json.dump({"h0": best["h0"], "b": best["b"], "g_max": best["g_max"], "seeds": a.seeds, "T": 200,
                   "topped_share": best["topped_share"], "peak_pv_topped_median": best["peak_pv_topped_median"],
                   "note": "h_t = h0 * exp(b * x_t); calibrated by tools/calibrate_hazard.py"}, fh, indent=1)
    print("BEST", best)
