"""
E1.3 (PREREG_PHASE_1.md section 8): the sigma_V x df_V x s_x sweep with the analytic Kalman bound beside the surrogate.

Grid: sigma_V in {0.004, 0.006, 0.010, 0.015, 0.020} x df_V in {Gaussian, t5} x s_x in {0.10, 0.13, 0.165, 0.20}, at the
current mispricing engine, jumps / burn-in / start price as in force; s_x set through sbar = 0.017 x s_x / 0.1752
(the engine's sd(x) is linear in sd_e; the realised sd(x) at T = 5,000 is reported at each s_x). 200 seeds x 4
scenarios per point (seeds 60000-60199, crash delta 0.70). Statistics per point: level-free price-only GBT R2(x) on calm
and on all days (cluster-bootstrap CI, 500), the Kalman bound (window average / day 200 / steady state), L4 coverage at
theta in {0.03, 0.05, 0.08}, checklist items 9 (50 flat T = 800 paths) and 20, MAPE of V from a trailing-250-day average
of log P. The level-free features are computed from the hidden path (technicals_block on P), not from the rendered
(rounded) fields -- stated. mu_V nuisance {0, 0.00025, 0.0005} at the adopted (sigma_V, s_x), 50 seeds.

    python -m tools.phase1.e1_3_sweep [--workers 8] [--quick]
Outputs: docs/env_v2/generated/v2_1/e1_3/sweep.json, sweep.md
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

OUT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e1_3")
SEED0, N = 60000, 200
SIGMAS = (0.004, 0.006, 0.010, 0.015, 0.020)
DFS = (("gaussian", None), ("t5", 5.0))
SXS = (0.10, 0.13, 0.165, 0.20)
SBAR_REF, SX_REF = 0.017, 0.1752
SCENARIOS4 = ("flat", "crash", "bull_trap", "sustained_bull")
THETAS = (0.03, 0.05, 0.08)
N_BOOT = 500


def sbar_for(s_x: float) -> float:
    return SBAR_REF * s_x / SX_REF


def _path_job(args):
    """One path -> level-free feature frame (from the hidden path), targets, phase, coverage inputs, MAPE(V) of the SMA."""
    import warnings
    warnings.filterwarnings("ignore")
    from envs.v2.generator import GenConfig, generate
    from envs.v2.observables import technicals_block
    from envs.synthetic_market import MACRO_OF
    seed, sc, over = args
    kw = dict(scenario=sc, seed=seed, T=200, **over)
    if sc == "crash":
        kw["delta"] = 0.70
    r = generate(GenConfig(**kw))
    m = r.day >= 1
    P_full = r.P[0]; lp_full = np.log(P_full)
    tech = technicals_block(P_full)
    P = P_full[m]
    df = pd.DataFrame({"scenario": sc, "seed": seed, "day": r.day[m], "price": P, "SMA20": tech["SMA20"][m], "SMA50": tech["SMA50"][m],
                       "RSI14": tech["RSI14"][m], "MACD": tech["MACD"][m], "MACD_signal": tech["MACD_signal"][m],
                       "trend_strength": tech["trend_strength"][m], "trend_regime": tech["trend_regime"][m],
                       "V": r.V[0, m], "P": P, "x": r.x[0, m], "phase": r.phase[m]})
    df["macro"] = df["phase"].map(MACRO_OF).fillna("calm")
    # MAPE of V from the trailing (up to 250-day) average of log P on the full timeline
    idx = np.where(m)[0]
    vhat = np.array([math.exp(lp_full[max(0, i - 249):i + 1].mean()) for i in idx])
    mape = float(np.mean(np.abs(vhat - r.V[0, m]) / r.V[0, m]))
    ret = np.diff(np.log(P))
    calm = df["phase"].to_numpy(dtype=object) == "calm"
    calm_sd = float(ret[calm[1:]].std()) if calm[1:].sum() > 30 else float("nan")
    mdd = float((P / np.maximum.accumulate(P) - 1).min())
    worst_panic = float(ret[(df["phase"].to_numpy(dtype=object) == "panic")[1:]].min()) if (df["phase"] == "panic").sum() > 1 else float("nan")
    return df, {"seed": seed, "scenario": sc, "mape_v_sma": mape, "calm_sd": calm_sd, "mdd": mdd, "worst_panic": worst_panic}


def _long_job(args):
    from envs.v2.generator import GenConfig, generate
    from evaluation.stylized_facts import acf
    seed, over = args
    r = generate(GenConfig(scenario="flat", seed=seed, T=800, reject=False, **over))
    x = r.x[0, r.day >= 1]
    a = acf(x, 1)
    return {"acf1": a, "hl": -math.log(2) / math.log(a) if 0 < a < 1 else float("inf"), "sd": float(x.std())}


def _sd5000_job(args):
    from envs.v2.generator import GenConfig, generate
    seed, over = args
    r = generate(GenConfig(scenario="flat", seed=seed, T=5000, reject=False, jumps=False, **over))
    return float(r.x[0, r.day >= 1].std())


def surrogate(panel: pd.DataFrame, n_boot: int = N_BOOT):
    from evaluation.leakage_audit import add_level_free_columns, add_lags_and_returns, _oos_predictions, _models, LEVEL_FREE_KEYS
    d = add_level_free_columns(panel)
    keys = [k for k in ("RSI14", "trend_strength", "trend_regime", "lp_sma20", "lp_sma50", "macd_p", "macds_p") if k in d]
    dfl, cols = add_lags_and_returns(d, keys)
    dfl = dfl.dropna(subset=cols).reset_index(drop=True)
    cols = [c for c in cols if c.split("_lag")[0] in LEVEL_FREE_KEYS]
    groups = (dfl["scenario"].astype(str) + "-" + dfl["seed"].astype(str)).to_numpy(dtype=object)
    y = dfl["x"].to_numpy(float)
    p = _oos_predictions(dfl[cols].to_numpy(float), y, groups, _models()["gbt"])
    path_of = pd.factorize(pd.Series(groups))[0]; n_paths = path_of.max() + 1
    calm = dfl["macro"].to_numpy(dtype=object) == "calm"
    rng = np.random.default_rng(0)
    out = {"n_features": len(cols), "n_paths": int(n_paths)}
    for grp, m in (("calm", calm), ("all", np.ones(len(y), bool))):
        cnt = np.bincount(path_of[m], minlength=n_paths).astype(float)
        sy = np.bincount(path_of[m], weights=y[m], minlength=n_paths); syy = np.bincount(path_of[m], weights=y[m] ** 2, minlength=n_paths)
        sres = np.bincount(path_of[m], weights=(y[m] - p[m]) ** 2, minlength=n_paths)
        def r2(idx):
            n = cnt[idx].sum(); ss = syy[idx].sum() - sy[idx].sum() ** 2 / n
            return float(1 - sres[idx].sum() / ss) if ss > 0 else float("nan")
        pt = r2(np.arange(n_paths))
        b = np.array([r2(rng.integers(0, n_paths, n_paths)) for _ in range(n_boot)])
        res = m & (np.abs(y) >= 0.05)
        out[grp] = {"R2": pt, "ci95": [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))],
                    "sign_acc": float(np.mean(np.sign(p[res]) == np.sign(y[res]))) if res.sum() > 10 else float("nan"), "n": int(m.sum())}
    return out


def run_point(ex, over: dict, n_seeds: int, label: str, kb_args):
    from tools.phase1.kalman_bound import kalman_bound
    t1 = time.time()
    jobs = [(s, sc, over) for sc in SCENARIOS4 for s in range(SEED0, SEED0 + n_seeds)]
    res = list(ex.map(_path_job, jobs, chunksize=8))
    panel = pd.concat([r[0] for r in res], ignore_index=True)
    stats_ = pd.DataFrame([r[1] for r in res])
    sur = surrogate(panel)
    kb = kalman_bound(*kb_args)
    cov = {}
    for sc in SCENARIOS4:
        g = panel[panel["scenario"] == sc]
        cov[sc] = {f"theta_{th}": float((g["x"].abs() >= th).mean()) for th in THETAS}
    long = list(ex.map(_long_job, [(s, over) for s in range(SEED0, SEED0 + 50)], chunksize=5))
    sd5 = list(ex.map(_sd5000_job, [(s, over) for s in range(SEED0, SEED0 + 20)], chunksize=2))
    flat = stats_[stats_.scenario == "flat"]; crash = stats_[stats_.scenario == "crash"]
    item9 = {"acf1_median": float(np.median([l["acf1"] for l in long])), "hl_median": float(np.median([l["hl"] for l in long])),
             "sd_median": float(np.median([l["sd"] for l in long])), "pass": None}
    item9["pass"] = bool(item9["acf1_median"] >= 0.98 and item9["hl_median"] >= 60 and 0.08 <= item9["sd_median"] <= 0.20)
    item20 = {"mdd_median": float(crash["mdd"].median()), "calm_sd_median": float(flat["calm_sd"].median()), "worst_panic_median": float(crash["worst_panic"].median())}
    item20["pass"] = bool(-0.65 <= item20["mdd_median"] <= -0.20 and 0.014 <= item20["calm_sd_median"] <= 0.022 and -0.15 <= item20["worst_panic_median"] <= -0.06)
    rng = np.random.default_rng(0); mv = stats_["mape_v_sma"].to_numpy(); bm = np.array([mv[rng.integers(0, len(mv), len(mv))].mean() for _ in range(N_BOOT)])
    out = {"label": label, "overrides": {k: v for k, v in over.items()}, "n_seeds": n_seeds, "surrogate_level_free": sur, "kalman": kb,
           "gap_calm_surrogate_minus_bound_window": sur["calm"]["R2"] - kb["window_avg"],
           "coverage": cov, "item9_T800": item9, "item20": item20,
           "mape_v_sma250": {"mean": float(mv.mean()), "ci95": [float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5))]},
           "realised_sd_x_T5000_jumps_off": {"mean": float(np.mean(sd5)), "min": float(np.min(sd5)), "max": float(np.max(sd5))},
           "seconds": round(time.time() - t1)}
    print(label, f"R2 calm {sur['calm']['R2']:.3f} [{sur['calm']['ci95'][0]:.3f}, {sur['calm']['ci95'][1]:.3f}] bound {kb['window_avg']:.3f}/{kb['day_T']:.3f}/{kb['steady_state']:.3f}; "
          f"sd_x5000 {np.mean(sd5):.3f}; cov flat 0.05 {cov['flat']['theta_0.05']:.2f}; item9 {item9['hl_median']:.0f} d; {time.time() - t1:.0f} s", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    from envs.v2 import value_params as VP
    n_seeds = 40 if a.quick else N
    t0 = time.time()
    out = {"design": {"seeds": [SEED0, SEED0 + n_seeds - 1], "sigmas": SIGMAS, "dfs": [d[0] for d in DFS], "s_xs": SXS, "sbar_rule": f"sbar = {SBAR_REF} x s_x / {SX_REF}",
                      "in_force": {"sigma_V": VP.SIGMA_V, "mu_V": VP.MU_V, "df_V": VP.DF_V, "jump": VP.JUMP, "start_price_mode": VP.START_PRICE_MODE, "burn_in": VP.BURN_IN}},
           "grid": [], "mu_V_nuisance": []}
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for sv in SIGMAS:
            for dname, dfv in DFS:
                for sx in SXS:
                    over = {"sigma_V": sv, "df_V": dfv, "garch": {"sbar": sbar_for(sx)}}
                    out["grid"].append({"sigma_V": sv, "df_V": dname, "s_x": sx, **run_point(ex, over, n_seeds, f"sV {sv} {dname} sx {sx}", (sv, sx, 150.0))})
        for mu in (0.0, 0.00025, 0.0005):
            over = {"mu_V": mu}
            out["mu_V_nuisance"].append({"mu_V": mu, **run_point(ex, over, 50, f"mu_V {mu}", (VP.SIGMA_V, SX_REF, 150.0))})
    out["seconds"] = round(time.time() - t0)
    with open(os.path.join(OUT, "sweep.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    L = ["# E1.3 sigma_V x df_V x s_x sweep with the analytic bound (PREREG_PHASE_1.md section 8)", "",
         f"{n_seeds} seeds x 4 scenarios per grid point (seeds {SEED0}+; crash delta 0.70); engine fw_fallback_hl150; in force: {json.dumps(out['design']['in_force'], default=str)}. "
         "Surrogate = GBT on the level-free price-only set (features from the hidden path), GroupKFold(5) by path, 500-resample cluster CI. "
         "Bound = Kalman (h = 150 d): 200-day window average / day 200 / steady state. Allowance = calm surrogate minus bound on the Gaussian row at the same (sigma_V, s_x).", "",
         "| sigma_V | df_V | s_x (sbar) | realised sd(x) T=5000 | R2 calm [CI] | R2 all | sign acc calm | bound win/d200/ss | calm minus bound | cov flat 0.03/0.05/0.08 | cov crash 0.05 | item 9 hl (T=800) | item 20 calm sd / MDD | MAPE(V) SMA250 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for g in out["grid"]:
        s = g["surrogate_level_free"]; k = g["kalman"]; c = g["coverage"]
        L.append(f"| {g['sigma_V']} | {g['df_V']} | {g['s_x']} ({sbar_for(g['s_x']):.4f}) | {g['realised_sd_x_T5000_jumps_off']['mean']:.3f} | {s['calm']['R2']:.3f} [{s['calm']['ci95'][0]:.3f}, {s['calm']['ci95'][1]:.3f}] | "
                 f"{s['all']['R2']:.3f} | {s['calm']['sign_acc']:.2f} | {k['window_avg']:.3f} / {k['day_T']:.3f} / {k['steady_state']:.3f} | {g['gap_calm_surrogate_minus_bound_window']:+.3f} | "
                 f"{c['flat']['theta_0.03']:.2f} / {c['flat']['theta_0.05']:.2f} / {c['flat']['theta_0.08']:.2f} | {c['crash']['theta_0.05']:.2f} | {g['item9_T800']['hl_median']:.0f} ({'P' if g['item9_T800']['pass'] else 'F'}) | "
                 f"{g['item20']['calm_sd_median']:.4f} / {g['item20']['mdd_median']:.2f} ({'P' if g['item20']['pass'] else 'F'}) | {g['mape_v_sma250']['mean']:.3f} |")
    L += ["", "## mu_V nuisance (50 seeds, at the parameters in force)", "", "| mu_V | R2 calm [CI] | bound win | cov flat 0.05 | item 9 hl | MAPE(V) |", "|---|---|---|---|---|---|"]
    for g in out["mu_V_nuisance"]:
        s = g["surrogate_level_free"]
        L.append(f"| {g['mu_V']} | {s['calm']['R2']:.3f} [{s['calm']['ci95'][0]:.3f}, {s['calm']['ci95'][1]:.3f}] | {g['kalman']['window_avg']:.3f} | {g['coverage']['flat']['theta_0.05']:.2f} | {g['item9_T800']['hl_median']:.0f} | {g['mape_v_sma250']['mean']:.3f} |")
    with open(os.path.join(OUT, "sweep.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("written", OUT, f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
