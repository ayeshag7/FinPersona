"""
E4.2 (PREREG_PHASE_4.md section 4): the schedule's sampling ranges replaced by the panel's empirical P10-P90,
and the rise-time criterion Phase 3 handed over with its target already measured.

    python -m tools.phase4.e4_2_schedule [--seeds 500] [--workers 3]

Phase 3 measured the target and established who owns it: the panel's FAST crashes (peak-to-trough <= 126 d,
642 episodes / 313 stocks) go from onset (first -10 %) to the 21-day realised-variance peak in 30 d [29, 35],
and the generator could not get below 75.5 d under ANY of REG-6's three variance mechanisms -- because the
deterioration length plus the panic build-up is set by schedule.py, not by the variance block.

Arms, both at the same seeds so the comparison is paired:
  v2    the stipulated uniforms (det_len U(15,40), panic_len U(15,70), front-loading fixed at 0.5, delta 0.70)
  v21   the FIT ranges from E4.1's dd30_fast family (det_len [3, 26], panic_len [15, 101], front_load
        [0.088, 0.574], depth [-0.538, -0.312], rec60 [0.236, 1.037])

Statistic: the generator's median onset -> RV21-peak rise time, measured by the SAME
tools/phase3/episodes.py::rise_decay estimator used on the panel.
Rule: accepted iff the generator's median rise time's 95 % bootstrap CI OVERLAPS the panel's [29, 35].
If no admissible parameterisation reaches it, the best achieved value is reported with its CI, the binding
constraint is named, and the criterion is recorded as NOT MET -- it is not relaxed.

The report publishes the whole surface (rise time against the drawn det_len and front_load), not the winning
cell, and the truncation rate per parameter that T = 200 forces.

Output: docs/env_v2/generated/v2_1/e4_2/{schedule.json, schedule.md}
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

from tools.phase3.episodes import drawdown_episodes, rise_decay, _rv  # noqa: E402

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e4_2")
SEED0 = 220000
N_BOOT = 2000
PANEL_RISE_CI = [29.0, 35.0]


GRID_N = 33          # quantile grid points from q = 0.10 to q = 0.90 inclusive


def fit_ranges():
    """The FIT ranges from E4.1's fast-crash family (D4: the single-stock panel is primary), in BOTH forms.

    `uniform` is the rule as first registered (a uniform over [P10, P90]); `grid` is the corrected rule of
    PREREG_PHASE_4_ADDENDUM.md section 3 -- an equally spaced empirical quantile grid over the same interval,
    so the fitted SHAPE survives as well as the fitted interval.  Both are run and both are reported."""
    e = json.load(open(os.path.join(GEN, "e4_1", "episodes4.json"), encoding="utf-8"))
    q = e["panel_families"]["dd30_fast"]["quantiles"]
    df = pd.read_csv(os.path.join(GEN, "e4_1", "dd30.csv"))
    fast = df[pd.to_numeric(df["duration"], errors="coerce") <= 126]
    cols = ("det_len", "panic_len", "front_load", "depth", "rec60")
    uni, grid = {}, {}
    qs = np.linspace(0.10, 0.90, GRID_N)
    for c in cols:
        v = pd.to_numeric(fast[c], errors="coerce").dropna().to_numpy(float)
        uni[c] = [float(np.percentile(v, 10)), float(np.percentile(v, 90))]
        grid[c] = {"grid": [float(x) for x in np.quantile(v, qs)]}
    return uni, grid, q, {c: int(pd.to_numeric(fast[c], errors="coerce").notna().sum()) for c in cols}


def one_path(args):
    """One crash path -> the E3.4/E4.2 statistics, measured with the SHARED estimator."""
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    seed, cfg = args
    env = SyntheticMarketEnv("crash", 200, seed, crash_discount=0.70, config=cfg)
    d = env.data[env.data["asset"] == 0]
    p = d["price"].to_numpy(float)
    r = np.diff(np.log(p))
    ev = int(env.schedule.event_start)
    s = env.schedule
    out = {"seed": seed, "attempts": int(env.attempts), "rejected": int(env.attempts > 1),
           "det_len": int(s.det_len), "panic_len": int(s.panic_len), "front_load": float(s.front_load),
           "delta": float(s.delta), "D_V": float(s.D_V), "delta_end": float(s.delta_end),
           "setup_len": int(s.setup_len), "mode": s.mode,
           "trunc": ";".join(sorted(s.truncated)) if s.truncated else ""}
    rv_calm = _rv(r, 0, max(ev - 2, 0), min_n=30)
    if np.isfinite(rv_calm) and rv_calm > 0:
        out["rv_calm"] = float(rv_calm)
        # MATCHED POPULATION: the panel target comes from dd30_fast, i.e. drawdowns of >= 30 % whose
        # peak-to-trough duration is <= 126 trading days.  Applying the same two conditions to the generator
        # is what makes the comparison like for like; measuring the generator on an unfiltered dd20 family
        # against a dd30_fast target would compare two different populations.
        eps = [e for e in drawdown_episodes(p, depth_thr=-0.30) if (e["trough"] - e["peak"]) <= 126]
        if eps:
            ep = min(eps, key=lambda e: e["depth"])
            out["depth"] = float(ep["depth"])
            out["duration"] = int(ep["trough"] - ep["peak"])
            out["ep_peak_rel_event"] = int(ep["peak"] - ev)
            rd = rise_decay(ep, p, r, rv_calm)
            if rd:
                out["rise"] = rd["rise"]
                out["onset_lag_before_event"] = int(ev - rd["onset"])
                out["realised_det_len"] = int(rd["onset"] - ep["peak"])
                out["decay_half_life"] = rd["decay_half_life"]
                out["stress_spell"] = rd["stress_spell"]
    return out


def run_arm(seeds, cfg, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(one_path, [(s, cfg) for s in seeds], chunksize=4))


def boot_median(v, n_boot=N_BOOT, seed=400040):
    v = np.asarray([x for x in v if x is not None and np.isfinite(x)], float)
    if len(v) < 20:
        return None, None, len(v)
    rng = np.random.default_rng(seed)
    b = [float(np.median(v[rng.integers(0, len(v), len(v))])) for _ in range(n_boot)]
    return float(np.median(v)), [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))], int(len(v))


def coverage(df, q):
    """Share of generated paths whose depth AND duration fall inside the panel's P10-P90 (REG-8's rule input)."""
    d = pd.to_numeric(df.get("depth"), errors="coerce")
    u = pd.to_numeric(df.get("duration"), errors="coerce")
    ok = d.notna() & u.notna()
    if ok.sum() < 20:
        return None
    ind = ((d >= q["depth"]["p10"]) & (d <= q["depth"]["p90"]) &
           (u >= q["duration"]["p10"]) & (u <= q["duration"]["p90"]))[ok]
    n = int(ok.sum())
    p = float(ind.mean())
    se = math.sqrt(max(p * (1 - p), 1e-12) / n)
    return {"coverage": p, "ci95": [max(0.0, p - 1.96 * se), min(1.0, p + 1.96 * se)], "n": n}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=500)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    R, RG, q, n_by = fit_ranges()
    seeds = list(range(SEED0, SEED0 + a.seeds))
    arms = {"v2": {"schedule_mode": "v2"},
            "v21_uniform": {"schedule_mode": "v21", "schedule_ranges": R},
            "v21_empirical": {"schedule_mode": "v21", "schedule_ranges": RG}}
    res = {"design": {"prereg": "PREREG_PHASE_4.md section 4", "seeds": a.seeds, "seed0": SEED0,
                      "scenario": "crash", "delta_arg": 0.70, "T": 200, "n_boot": N_BOOT,
                      "estimator": "tools/phase3/episodes.py::rise_decay -- the same code path that measured "
                                   "the panel, so the comparison is like for like",
                      "panel_target": {"rise_ci95": PANEL_RISE_CI, "n_episodes": 642, "n_stocks": 313,
                                       "source": "e4_1/episodes4.json panel_families.dd30_fast (which "
                                                 "reproduces Phase 3's 642/313 and its 30 d [29, 35])"},
                      "fit_ranges_uniform": R,
                      "fit_ranges_grid_q": [0.10, 0.90], "grid_points": GRID_N,
                      "fit_ranges_grid": RG, "n_episodes_by_parameter": n_by,
                      "addendum": "PREREG_PHASE_4_ADDENDUM.md section 3 -- the empirical arm is the corrected "
                                  "sampler; the uniform arm is the rule as first registered and is reported "
                                  "beside it",
                      "v2_ranges": {"det_len": [15, 40], "panic_len": [15, 70], "front_load": [0.5, 0.5],
                                    "delta": [0.70, 0.70], "rec60": "delta_end ~ U(delta, 1)"}},
           "arms": {}}
    frames = {}
    for name, cfg in arms.items():
        print(f"[{name}] {a.seeds} crash seeds ...", flush=True)
        rows = run_arm(seeds, cfg, a.workers)
        df = pd.DataFrame(rows)
        frames[name] = df
        df.to_csv(os.path.join(OUT, f"paths_{name}.csv"), index=False)
        rise, rise_ci, n_rise = boot_median(df.get("rise"))
        dep, dep_ci, _ = boot_median(df.get("depth"))
        dur, dur_ci, _ = boot_median(df.get("duration"))
        dec, dec_ci, _ = boot_median(df.get("decay_half_life"))
        overlaps = bool(rise_ci and not (rise_ci[1] < PANEL_RISE_CI[0] or rise_ci[0] > PANEL_RISE_CI[1]))
        trunc = df["trunc"].fillna("")
        tr_rates = {}
        for k in ("panic_len", "setup_len", "det_len"):
            tr_rates[k] = float(trunc.str.contains(k).mean())
        res["arms"][name] = {
            "n_paths": int(len(df)),
            "rise_median": rise, "rise_ci95": rise_ci, "n_rise_measured": n_rise,
            "rise_ci_overlaps_panel": overlaps,
            "verdict": ("ACCEPTED" if overlaps else "NOT MET"),
            "depth_median": dep, "depth_ci95": dep_ci,
            "duration_median": dur, "duration_ci95": dur_ci,
            "decay_half_life_median": dec, "decay_half_life_ci95": dec_ci,
            "rejection_rate": float(df["rejected"].mean()),
            "mean_attempts": float(df["attempts"].mean()),
            "truncation_rate": tr_rates,
            "depth_duration_coverage_vs_panel": coverage(df, q),
            "drawn": {k: {"mean": float(pd.to_numeric(df[k], errors="coerce").mean()),
                          "p10": float(pd.to_numeric(df[k], errors="coerce").quantile(0.10)),
                          "p90": float(pd.to_numeric(df[k], errors="coerce").quantile(0.90))}
                      for k in ("det_len", "panic_len", "front_load", "delta", "D_V", "delta_end")},
        }
        print(f"    rise median {rise} {rise_ci} (panel [29, 35]) -> {res['arms'][name]['verdict']}", flush=True)
        print(f"    depth {dep}  duration {dur}  rejection {df['rejected'].mean():.3f}  "
              f"truncation {tr_rates}", flush=True)

    # ---- what actually binds the rise time (the decomposition Phase 3's hand-off could not see)
    binding = {}
    for name, df in frames.items():
        d = df[pd.to_numeric(df.get("rise"), errors="coerce").notna()].copy()
        if len(d) < 40:
            continue
        for c in ("rise", "onset_lag_before_event", "det_len", "panic_len", "duration",
                  "realised_det_len", "ep_peak_rel_event"):
            d[c] = pd.to_numeric(d.get(c), errors="coerce")
        cors = {}
        for c in ("onset_lag_before_event", "det_len", "panic_len"):
            m = d[c].notna() & d["rise"].notna()
            cors[c] = float(np.corrcoef(d.loc[m, c], d.loc[m, "rise"])[0, 1]) if m.sum() > 20 else None
        bylag = []
        for lo, hi in ((-10 ** 9, 0), (0, 10), (10, 30), (30, 10 ** 9)):
            g = d[(d["onset_lag_before_event"] > lo) & (d["onset_lag_before_event"] <= hi)]
            if len(g) >= 10:
                bylag.append({"lag_bin": f"({lo if lo > -10**8 else '-inf'}, {hi if hi < 10**8 else 'inf'}]",
                              "n": int(len(g)), "rise_median": float(g["rise"].median()),
                              "duration_median": float(g["duration"].median())})
        binding[name] = {
            "correlations_with_rise": cors,
            "rise_by_onset_lag": bylag,
            "onset_lag_median": float(d["onset_lag_before_event"].median()),
            "realised_det_len_median": float(d["realised_det_len"].median()),
            "drawn_det_len_median": float(d["det_len"].median()),
            "reading": "the SCRIPTED deterioration length is what E4.2 sets; the REALISED one is peak -> onset, "
                       "and it is inflated whenever the episode's running peak falls in the calm setup rather "
                       "than at the scripted event",
        }
    res["what_binds"] = binding

    # ---- the surface: rise time against the two parameters that set it
    surf = {}
    for name, df in frames.items():
        d = df[pd.to_numeric(df.get("rise"), errors="coerce").notna()].copy()
        if len(d) < 40:
            continue
        d["rise"] = pd.to_numeric(d["rise"], errors="coerce")
        db = pd.qcut(pd.to_numeric(d["det_len"], errors="coerce"), 4, duplicates="drop")
        fb = pd.qcut(pd.to_numeric(d["front_load"], errors="coerce"), 2, duplicates="drop")
        cells = []
        for (dk, fk), g in d.groupby([db, fb], observed=True):
            if len(g) >= 15:
                cells.append({"det_len_bin": str(dk), "front_load_bin": str(fk), "n": int(len(g)),
                              "rise_median": float(g["rise"].median()),
                              "depth_median": float(pd.to_numeric(g["depth"], errors="coerce").median())})
        # the marginal effect of det_len on the rise time, which is the mechanism Phase 3 pointed at
        x = pd.to_numeric(d["det_len"], errors="coerce").to_numpy(float)
        y = d["rise"].to_numpy(float)
        m = np.isfinite(x) & np.isfinite(y)
        slope = float(np.polyfit(x[m], y[m], 1)[0]) if m.sum() > 20 else None
        surf[name] = {"cells": cells, "rise_per_extra_det_day": slope,
                      "corr_det_rise": float(np.corrcoef(x[m], y[m])[0, 1]) if m.sum() > 20 else None}
    res["surface"] = surf
    res["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(OUT, "schedule.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)

    L = ["# E4.2 - the schedule's ranges from the panel, and the rise time", "",
         "`python -m tools.phase4.e4_2_schedule` - PREREG_PHASE_4.md section 4.", "",
         f"{a.seeds} crash seeds per arm, the same seeds in both, seeds {SEED0}+.",
         "Rise time measured by `tools/phase3/episodes.py::rise_decay`, the same code path that measured the "
         "panel. Panel target: **30 d [29, 35]** (fast crashes, 642 episodes / 313 stocks).", "",
         "## Ranges: before and after", "",
         "| parameter | v2 (DESIGN, stipulated) | v2.1 (FIT, panel P10-P90) |", "|---|---|---|",
         f"| det_len | U(15, 40) | [{R['det_len'][0]:.0f}, {R['det_len'][1]:.0f}], median {RG['det_len']['grid'][GRID_N//2]:.0f} |",
         f"| panic_len | U(15, 70) | [{R['panic_len'][0]:.0f}, {R['panic_len'][1]:.0f}], median {RG['panic_len']['grid'][GRID_N//2]:.0f} |",
         f"| front_load | fixed 0.50 | [{R['front_load'][0]:.3f}, {R['front_load'][1]:.3f}], median {RG['front_load']['grid'][GRID_N//2]:.3f} |",
         f"| depth -> delta | delta fixed 0.70 | [{R['depth'][0]:.3f}, {R['depth'][1]:.3f}], median {RG['depth']['grid'][GRID_N//2]:.3f} |",
         f"| delta_end | U(delta, 1) | via rec60 [{R['rec60'][0]:.3f}, {R['rec60'][1]:.3f}], median {RG['rec60']['grid'][GRID_N//2]:.3f} |", "",
         "## Results", "",
         "| arm | rise median | 95 % CI | overlaps [29, 35] | depth | duration | rejection | coverage |",
         "|---|---|---|---|---|---|---|---|"]
    for name, v in res["arms"].items():
        cov = v["depth_duration_coverage_vs_panel"]
        L.append(f"| {name} | {v['rise_median']} | {v['rise_ci95']} | **{v['rise_ci_overlaps_panel']}** | "
                 f"{v['depth_median']:.3f} | {v['duration_median']:.0f} | {v['rejection_rate']:.3f} | "
                 f"{(cov['coverage'] if cov else float('nan')):.3f} |")
    L += ["", "## Truncation forced by T = 200", "", "| arm | panic_len | setup_len | det_len |", "|---|---|---|---|"]
    for name, v in res["arms"].items():
        t = v["truncation_rate"]
        L.append(f"| {name} | {t['panic_len']:.3f} | {t['setup_len']:.3f} | {t['det_len']:.3f} |")
    L += ["", "## What actually binds the rise time", "",
          "| arm | corr(onset lag, rise) | corr(det_len, rise) | corr(panic_len, rise) | drawn det_len | realised det_len |",
          "|---|---|---|---|---|---|"]
    for name, v in binding.items():
        c = v["correlations_with_rise"]
        L.append(f"| {name} | {c['onset_lag_before_event']:.3f} | {c['det_len']:.3f} | {c['panic_len']:.3f} | "
                 f"{v['drawn_det_len_median']:.0f} | {v['realised_det_len_median']:.0f} |")
    for name, v in binding.items():
        L += ["", f"### {name}: rise time by how far the onset precedes the scripted event", "",
              "| onset lag before event | n | rise median | duration median |", "|---|---|---|---|"]
        for b_ in v["rise_by_onset_lag"]:
            L.append(f"| {b_['lag_bin']} | {b_['n']} | {b_['rise_median']:.1f} | {b_['duration_median']:.1f} |")
    L += ["", "## The surface (rise time against the two parameters that set it)", ""]
    for name, sv in surf.items():
        L += [f"### {name}", "",
              f"- rise time changes by **{sv['rise_per_extra_det_day']:.2f} d per extra deterioration day** "
              f"(correlation {sv['corr_det_rise']:.3f})", "",
              "| det_len bin | front_load bin | n | rise median | depth median |", "|---|---|---|---|---|"]
        for c in sv["cells"]:
            L.append(f"| {c['det_len_bin']} | {c['front_load_bin']} | {c['n']} | {c['rise_median']:.0f} | "
                     f"{c['depth_median']:.3f} |")
        L.append("")
    with open(os.path.join(OUT, "schedule.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"wrote {OUT}/schedule.json in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
