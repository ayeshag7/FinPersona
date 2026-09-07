"""
E5.2's residual clock (PREREG_PHASE_5.md section 5.3): `days_since_eps_announcement` re-measured under the FIT
announcement-lag distribution with tools/phase4/e4_7_calendar.py's `eps_clock` UNCHANGED, plus the interior-days
variant that tests the one mechanism this phase can name (the window's edges).

    python -m tools.phase5.e5_2_clock --out DIR [--overrides JSON] [--seeds 200] [--workers 3]

Seeds 326000+ (E4.7's block, so the v2-lag row reproduces P4-29's 0.3958 at n = 150 when --seeds 150).
Output: <out>/clock.{json,md}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

from tools.phase4.e4_7_calendar import pmap, eps_clock, SEED_EPS  # noqa: E402
from tools.phase5.common import pin_state  # noqa: E402


def interior(rows, lo=64, hi=137):
    out = []
    for r in rows:
        days = np.asarray(r["days"]); m = (days >= lo) & (days <= hi)
        out.append({**r, "days": days[m].tolist(), "eps_days": np.asarray(r["eps_days"], float)[m].tolist(),
                    "phases": [p for p, k in zip(r["phases"], m) if k]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--overrides", default="{}")
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(a.out, exist_ok=True)
    overrides = json.loads(a.overrides) if not os.path.exists(a.overrides) else json.load(open(a.overrides, encoding="utf-8"))
    state = pin_state()
    res = {"what": "E5.2 residual clock: e4_7_calendar.eps_clock unchanged, under the v2 lag U(25,35) and the FIT lag grid",
           "state": state, "seeds": [SEED_EPS, SEED_EPS + a.seeds - 1], "arms": {}}
    for label, cfg in (("v2_lags_randomised_grid", {"randomise_eps_quarter": True, "obs_mode": "v2"}),
                       ("fit_lags_randomised_grid", {"randomise_eps_quarter": True, "obs_overrides": overrides})):
        rows = pmap([("flat", s, cfg, ("day_n",)) for s in range(SEED_EPS, SEED_EPS + a.seeds)], a.workers)
        full = eps_clock(rows)
        inter = eps_clock(interior(rows))
        # the registered statistic uses ONE train/test split (E4.7's seed 4702); the excess over the null at n = 200 is
        # of the order of the split-to-split variability, so five further splits are reported beside it
        splits = []
        for sd_ in (4703, 4704, 4705, 4706, 4707):
            f_ = eps_clock(rows, seed=sd_); i_ = eps_clock(interior(rows), seed=sd_)
            splits.append({"seed": sd_, "full_excess_pp": 100 * (f_["accuracy_quarter_third_from_eps_field"] - f_["null_p95"]),
                           "interior_excess_pp": 100 * (i_["accuracy_quarter_third_from_eps_field"] - i_["null_p95"])})
        res["arms"][label] = {"config": cfg, "full_window": full, "interior_days_64_137": inter, "other_splits": splits,
                              "excess_pp_over_6_splits": {"full_mean": float(np.mean([100 * (full["accuracy_quarter_third_from_eps_field"] - full["null_p95"])] + [x["full_excess_pp"] for x in splits])),
                                                          "full_sd": float(np.std([100 * (full["accuracy_quarter_third_from_eps_field"] - full["null_p95"])] + [x["full_excess_pp"] for x in splits], ddof=1)),
                                                          "interior_mean": float(np.mean([100 * (inter["accuracy_quarter_third_from_eps_field"] - inter["null_p95"])] + [x["interior_excess_pp"] for x in splits])),
                                                          "interior_sd": float(np.std([100 * (inter["accuracy_quarter_third_from_eps_field"] - inter["null_p95"])] + [x["interior_excess_pp"] for x in splits], ddof=1))}}
        e6 = res["arms"][label]["excess_pp_over_6_splits"]
        print(f"      6 splits: full excess {e6['full_mean']:+.2f} +/- {e6['full_sd']:.2f} pp; interior {e6['interior_mean']:+.2f} +/- {e6['interior_sd']:.2f} pp", flush=True)
        print(f"    {label:26s} full acc {full['accuracy_quarter_third_from_eps_field']:.4f} vs null {full['null_p95']:.4f} "
              f"(clock {full['carries_a_clock']}); interior acc {inter['accuracy_quarter_third_from_eps_field']:.4f} vs null "
              f"{inter['null_p95']:.4f} (clock {inter['carries_a_clock']})", flush=True)
    res["seconds"] = round(time.time() - t0)
    json.dump(res, open(os.path.join(a.out, "clock.json"), "w", encoding="utf-8"), indent=1, default=str)
    L = ["# E5.2 the residual clock in `days_since_eps_announcement`", "",
         f"{a.seeds} flat seeds ({SEED_EPS}+), quarter grid randomised per seed in both arms; the classifier and its in-time "
         "shuffle null are E4.7's, unchanged. P4-29 measured 0.3958 vs null 0.3625 at n = 150 under the v2 lag U(25, 35).", "",
         "| arm | full-window accuracy | null p95 | clock | interior-days accuracy | null p95 | clock | full excess over 6 splits (pp) | interior excess over 6 splits (pp) |", "|---|---|---|---|---|---|---|---|---|"]
    for k, v in res["arms"].items():
        f, i = v["full_window"], v["interior_days_64_137"]
        e6 = v["excess_pp_over_6_splits"]
        L.append(f"| {k} | {f['accuracy_quarter_third_from_eps_field']:.4f} | {f['null_p95']:.4f} | {f['carries_a_clock']} | "
                 f"{i['accuracy_quarter_third_from_eps_field']:.4f} | {i['null_p95']:.4f} | {i['carries_a_clock']} | "
                 f"{e6['full_mean']:+.2f} +/- {e6['full_sd']:.2f} | {e6['interior_mean']:+.2f} +/- {e6['interior_sd']:.2f} |")
    with open(os.path.join(a.out, "clock.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L)); print(f"wrote {a.out}/clock.json in {res['seconds']} s")


if __name__ == "__main__":
    main()
