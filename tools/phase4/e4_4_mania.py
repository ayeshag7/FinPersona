"""
E4.4 (PREREG_PHASE_4.md section 6): the mania drift, and the drift cap revisited (amendment A5).

    python -m tools.phase4.e4_4_mania [--seeds 500] [--workers 3]

The registered route was to draw kappa and the mania length JOINTLY from E4.1's LPPLS fits so that the drift
cap becomes unnecessary.  **That route is not supported by the data.**  The registered trigger --

    the LPPLS route supports a super-exponential mania drift iff the stable share is >= 0.50 AND the median m
    is inside (0, 1) with a CI excluding 1.0

-- returns stable share **0.329 [0.313, 0.344]** over 3125 converged fits on 398 stocks (e4_1/lppls.json).
The m clause passes (median m 0.926 [0.900, 0.953], excluding 1.0) but is itself close to the exponential
boundary m = 1.  The stability clause fails decisively, so E4.4 takes the **registered fallback**: the
scripted-drift alternative with its shape FIT from the run-up table.  This is the plan's own contingency
("if the fits do not support a super-exponential drift over 40-100 days, the report says so"), not a
relaxation of the rule.

The fallback's shape, FIT from the panel's run-ups:
  mania length   the run-up length distribution, truncated by T = 200 with the truncation rate reported
  kappa          the compounding rate that reproduces the panel's own run-up CONVEXITY -- the ratio of the
                 log gain in the last third of [start, top] to that in the first third.  For a drift
                 g_t = g0 (1+k)^t over L days that ratio is
                     ((1+k)^L - (1+k)^(2L/3)) / ((1+k)^(L/3) - 1),
                 which is solved for k on the panel's median ratio.

Then the cap: the share of mania days on which g hits g_max, with the upper 95 % bootstrap limit against the
registered 0.05, and the convexity of the pre-cap segment.

Output: docs/env_v2/generated/v2_1/e4_4/{mania.json, mania.md}
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
OUT = os.path.join(GEN, "e4_4")
SEED0 = 270000
N_BOOT = 1000
CAP_MAX_SHARE = 0.05


def convexity_fit():
    """kappa FIT from the panel's run-up convexity (last third vs first third of the log gain)."""
    from tools.phase1.panel import analysis_sets, load_prices
    ru = pd.read_csv(os.path.join(GEN, "e4_1", "runup4.csv"))
    A = analysis_sets(write=False)["A"]
    px = load_prices(A).ffill()
    ratios, lens = [], []
    for t, g in ru.groupby("ticker"):
        if t not in px.columns:
            continue
        p = px[t].to_numpy(float)
        lp = np.log(np.where(np.isfinite(p) & (p > 0), p, np.nan))
        for _, row in g.iterrows():
            s0, s1 = int(row["start"]), int(row["top"])
            L = s1 - s0
            if L < 30:
                continue
            a, b = s0 + L // 3, s0 + 2 * L // 3
            if not np.isfinite([lp[s0], lp[a], lp[b], lp[s1]]).all():
                continue
            first = lp[a] - lp[s0]
            last = lp[s1] - lp[b]
            if first <= 1e-6:
                continue
            ratios.append(last / first)
            lens.append(L)
    r = np.array(ratios, float)
    r = r[np.isfinite(r) & (r > 0)]
    med = float(np.median(r))
    L = float(np.median(lens))

    def ratio_of(k):
        if k <= 1e-9:
            return 1.0
        f = (1.0 + k)
        return (f ** L - f ** (2 * L / 3)) / max(f ** (L / 3) - 1.0, 1e-12)

    lo, hi = 1e-6, 0.20
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if ratio_of(mid) < med:
            lo = mid
        else:
            hi = mid
    k = 0.5 * (lo + hi)
    return {"kappa": float(k), "panel_convexity_ratio_median": med,
            "panel_convexity_p10_p90": [float(np.percentile(r, 10)), float(np.percentile(r, 90))],
            "median_runup_length": L, "n_runups": int(len(r)),
            "v2_range": [0.02, 0.04],
            "definition": "kappa solves ((1+k)^L - (1+k)^(2L/3)) / ((1+k)^(L/3) - 1) = the panel's median "
                          "ratio of last-third to first-third log gain over [start, top]",
            "label": "FIT"}


def _one(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    seed, cfg = args
    env = SyntheticMarketEnv("bull_trap", 200, seed, config=cfg)
    d = env.data[env.data["asset"] == 0]
    p = d["price"].to_numpy(float)
    ph = d["phase"].to_numpy(object)
    meta = env.event_meta
    m = np.isin(ph, ["mania", "blow-off"])
    out = {"seed": seed, "mania_days": int(m.sum()), "cap_hits": meta.get("cap_hits") or 0,
           "cap_binding_share": meta.get("cap_binding_share"),
           "kappa": float(env.schedule.kappa), "topped": bool(meta.get("topped"))}
    if m.sum() >= 12:
        lp = np.log(p[m])
        L = len(lp)
        a, b = L // 3, 2 * L // 3
        first, last = lp[a] - lp[0], lp[-1] - lp[b]
        out["convexity_ratio"] = float(last / first) if first > 1e-6 else None
        # convex iff the second difference of the log price is positive on average over the run
        out["convex"] = bool(np.mean(np.diff(lp, 2)) > 0)
    return out


def pmap(items, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_one, items, chunksize=4))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=500)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    lp = json.load(open(os.path.join(GEN, "e4_1", "lppls.json"), encoding="utf-8"))
    trig = lp["e4_4_trigger"]
    print(f"[trigger] LPPLS route met: {trig['met']} (stable share {trig['stable_share']:.3f} "
          f"{[round(v,3) for v in trig['stable_share_ci95']]}, m {trig['m_median']:.3f} "
          f"{[round(v,3) for v in trig['m_ci95']]})", flush=True)
    conv = convexity_fit()
    print(f"[fit] kappa {conv['kappa']:.5f} from the panel's convexity ratio "
          f"{conv['panel_convexity_ratio_median']:.3f} over {conv['n_runups']} run-ups "
          f"(v2 range {conv['v2_range']})", flush=True)

    ru = pd.read_csv(os.path.join(GEN, "e4_1", "runup4.csv"))
    rl = pd.to_numeric(ru["runup_len"], errors="coerce").dropna()
    mania_grid = {"grid": [float(v) for v in np.quantile(rl, np.linspace(0.10, 0.90, 33))]}
    trunc_rate = float((rl > 190).mean())

    arms = {"v2_kappa_uniform": {},
            "v21_kappa_FIT": {"schedule_mode": "v21",
                              "schedule_ranges": {"kappa": [conv["kappa"], conv["kappa"]]}}}
    res = {"design": {"prereg": "PREREG_PHASE_4.md section 6", "seeds": a.seeds, "seed0": SEED0,
                      "cap_max_share": CAP_MAX_SHARE, "n_boot": N_BOOT},
           "lppls_trigger": trig,
           "route": ("FALLBACK (scripted drift, shape FIT from the run-up table) -- the registered "
                     "contingency, because the LPPLS stability clause failed"),
           "kappa_fit": conv,
           "mania_length": {"panel_runup_len_p10_p50_p90": [float(np.percentile(rl, q)) for q in (10, 50, 90)],
                            "share_longer_than_the_horizon": trunc_rate,
                            "note": "the panel's run-ups have a median length of "
                                    f"{float(np.median(rl)):.0f} trading days against a benchmark horizon of "
                                    "200, so a mania length drawn from the panel is truncated on "
                                    f"{trunc_rate:.1%} of draws; the mania length is therefore a HORIZON "
                                    "artefact and is reported as such rather than as a fitted quantity",
                            "grid_if_untruncated": mania_grid},
           "arms": {}}
    for name, cfg in arms.items():
        rows = pmap([(s, cfg) for s in range(SEED0, SEED0 + a.seeds)], a.workers)
        df = pd.DataFrame(rows)
        cb = pd.to_numeric(df["cap_binding_share"], errors="coerce").fillna(0.0).to_numpy(float)
        rng = np.random.default_rng(400080)
        bs = [float(cb[rng.integers(0, len(cb), len(cb))].mean()) for _ in range(N_BOOT)]
        upper = float(np.percentile(bs, 97.5))
        conv_share = float(df["convex"].dropna().astype(bool).mean()) if "convex" in df else None
        res["arms"][name] = {
            "n_paths": int(len(df)), "kappa_median": float(df["kappa"].median()),
            "cap_binding_share_mean": float(cb.mean()), "cap_binding_upper95": upper,
            "cap_unnecessary": bool(upper < CAP_MAX_SHARE),
            "verdict": ("CAP UNNECESSARY" if upper < CAP_MAX_SHARE else "CAP STILL BINDS"),
            "convex_share": conv_share,
            "convexity_ratio_median": float(pd.to_numeric(df.get("convexity_ratio"),
                                                          errors="coerce").median()),
            "mania_days_median": float(df["mania_days"].median()),
            "topped_share": float(df["topped"].astype(bool).mean()),
        }
        v = res["arms"][name]
        print(f"  {name:20s} kappa {v['kappa_median']:.4f}  cap binding {v['cap_binding_share_mean']:.4f} "
              f"(upper95 {upper:.4f}) -> {v['verdict']}  convex {conv_share}", flush=True)
    res["amendment_A5"] = {
        "revisited_with": "the LPPLS stability failure plus the cap-binding measurement above",
        "conclusion": ("the drift cap cannot be retired on the LPPLS route because that route is not "
                       "supported by the panel; whether it is needed under the FIT kappa is answered by the "
                       "cap-binding upper limit in the table"),
    }
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(os.path.join(OUT, "mania.json"), "w", encoding="utf-8"), indent=1, default=str)
    L = ["# E4.4 - mania drift, and the cap (amendment A5)", "",
         "`python -m tools.phase4.e4_4_mania` - PREREG_PHASE_4.md section 6.", "",
         "## The registered LPPLS route is NOT supported", "",
         f"- rule: {trig['rule']}",
         f"- stable share **{trig['stable_share']:.3f} [{trig['stable_share_ci95'][0]:.3f}, "
         f"{trig['stable_share_ci95'][1]:.3f}]** (needs >= 0.50) over {lp['n_converged']} converged fits / "
         f"{lp['n_stocks']} stocks",
         f"- median m {trig['m_median']:.3f} [{trig['m_ci95'][0]:.3f}, {trig['m_ci95'][1]:.3f}] -- the CI "
         "excludes 1.0, but m sits close to the exponential boundary",
         f"- **met: {trig['met']}** -> the registered fallback is taken", "",
         "## The fallback's shape, FIT from the run-up table", "",
         f"- kappa **{conv['kappa']:.5f}** (v2 drew U(0.02, 0.04)), from the panel's median convexity ratio "
         f"{conv['panel_convexity_ratio_median']:.3f} over {conv['n_runups']} run-ups",
         f"- mania length: the panel's run-ups run {float(np.percentile(rl, 10)):.0f} / "
         f"{float(np.median(rl)):.0f} / {float(np.percentile(rl, 90)):.0f} days (P10/P50/P90) against a "
         f"200-day horizon, so {trunc_rate:.1%} of draws are truncated -- the mania length is a horizon "
         "artefact and is reported as one", "",
         "| arm | kappa | cap binding share | upper 95 % | verdict | convex share | mania days |",
         "|---|---|---|---|---|---|---|"]
    for name, v in res["arms"].items():
        L.append(f"| {name} | {v['kappa_median']:.4f} | {v['cap_binding_share_mean']:.4f} | "
                 f"{v['cap_binding_upper95']:.4f} | **{v['verdict']}** | {v['convex_share']} | "
                 f"{v['mania_days_median']:.0f} |")
    L += ["", "## Amendment A5", "", f"- {res['amendment_A5']['conclusion']}", ""]
    open(os.path.join(OUT, "mania.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"wrote {OUT}/mania.json in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
