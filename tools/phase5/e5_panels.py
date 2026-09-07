"""
Phase-5 arm panels: the SEP design (audit_panel's seeds and layout) rendered under explicit observable designs
(PREREG_PHASE_5.md section 3), with every arm PINNED by its `obs_overrides` (P4-19).

    python -m tools.phase5.e5_panels --arms <json file or inline json> [--workers 3] [--verify]

Two kinds of arm:
  post-hoc     the multiple, EPS/lag, dividend, analyst and volume blocks are computed AFTER the path from the stored
               V, P, r and their own streams, so every post-hoc arm is rendered from ONE generation of the hidden path
               (paired by construction: identical x, V, P across arms);
  re-simulate  sentiment designs and b_pred change the price path through the feedback and are generated afresh
               (paired by seed only).

The renderer (`fast_panel`) reproduces `evaluation.leakage_audit.panel_from_env` column for column -- same rounding
(Python round(), half-even on the decimal representation) and the same k_render scaling -- without stepping the
environment day by day, which is the dominant cost of the stored panels (~0.7 s per path).  `--verify` checks it bit
for bit against panel_from_env on the first seed's eight paths before anything is written.

Output: docs/env_v2/generated/v2_1/_panels/sep_phase5_<arm>.pkl and a manifest beside them.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tools.phase5.common import GEN, PANELS, SEP_SEED0, SEP_N, _sep_jobs, pin_state  # noqa: E402

RENDER_2DP = ("price", "SMA20", "SMA50", "trend_strength", "volume_ratio", "news_sentiment", "sentiment_MA5",
              "sentiment_change", "dividend_yield", "analyst_fair_value")
PRICE_DENOM = ("price", "SMA20", "SMA50", "MACD", "MACD_signal", "analyst_fair_value")


def _round_col(v, dp):
    return np.array([round(float(x), dp) if np.isfinite(x) else np.nan for x in v], float)


def fast_panel(env, scenario, seed) -> pd.DataFrame:
    """panel_from_env's frame from env.data directly (asset 0), identical values."""
    from envs.synthetic_market import MACRO_OF
    d = env.data[env.data["asset"] == 0].reset_index(drop=True)
    k = float(env.result.k_render)
    out = {"scenario": scenario, "seed": seed, "day": d["day"].to_numpy(int), "phase": d["phase"].astype(str).to_numpy(object),
           "V": d["fundamental_value"].to_numpy(float), "P": d["price"].to_numpy(float)}
    rf = env.rendered_fields
    for f in rf:
        if f == "date":
            continue
        col = d[f].to_numpy(float) * (k if f in PRICE_DENOM else 1.0)
        if f in RENDER_2DP:
            out[f] = _round_col(col, 2)
        elif f in ("MACD", "MACD_signal"):
            out[f] = _round_col(col, 4)
        elif f in ("RSI14", "implied_volatility"):
            out[f] = _round_col(col, 1)
        elif f == "reported_PE":
            out[f] = _round_col(col, 1)                        # NaN on 'n/m' days, as panel_from_env leaves it
        elif f in ("trend_regime", "days_since_eps_announcement"):
            out[f] = np.array([float(int(x)) for x in col], float)
        elif f == "volume":
            out[f] = np.array([float(int(x)) for x in col], float)
        else:
            out[f] = col
    df = pd.DataFrame(out)
    df["macro"] = df["phase"].map(MACRO_OF).fillna("calm")
    df["x"] = np.log(df["P"] / df["V"])
    return df


def _job(args):
    """One (scenario, seed, kw): generate once, render every arm that shares the path."""
    import warnings
    warnings.filterwarnings("ignore")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    from envs.synthetic_market import SyntheticMarketEnv, CANONICAL_FIELDS
    from envs.v2 import observables_params as OP
    scenario, seed, kw, T, arms, verify = args
    out = {}
    # group arms by their re-simulation key (config other than obs_overrides): post-hoc arms share one env
    groups = {}
    for name, spec in arms.items():
        key = json.dumps(spec.get("config", {}), sort_keys=True) + "|" + (json.dumps(spec["obs_overrides"].get("sentiment", {}), sort_keys=True))
        groups.setdefault(key, []).append(name)
    for key, names in groups.items():
        first = arms[names[0]]
        cfg = dict(first.get("config", {})); cfg["obs_overrides"] = first["obs_overrides"]
        env = SyntheticMarketEnv(scenario, T, seed, config=cfg, **kw)
        for name in names:
            spec = arms[name]
            if name != names[0]:
                env.cfg.obs_overrides = spec["obs_overrides"]
                env.result.obs_params = OP.resolve(env.cfg.obs_mode, spec["obs_overrides"] or None)
                env.obs_params = env.result.obs_params
                hidden = set()
                if env.obs_params is not None:
                    if str(env.obs_params["dividend"].get("field", "shown")) == "hidden":
                        hidden.add("dividend_yield")
                    a = env.obs_params["analyst"]
                    if str(a.get("field", "shown")) == "hidden" or str(a.get("design", "v2")) == "B":
                        hidden.add("analyst_fair_value")
                env.rendered_fields = [f for f in CANONICAL_FIELDS if f not in hidden]
                env._full, env.data = env._build_frames()
                env._perm = env._field_permutation()
            f = fast_panel(env, scenario, seed)
            if scenario == "crash" and "crash_discount" in kw:
                f["seed"] = seed * 100 + int(round(kw["crash_discount"] * 100))
            if verify:
                from evaluation.leakage_audit import panel_from_env
                g = panel_from_env(env, scenario, seed)
                if scenario == "crash" and "crash_discount" in kw:
                    g["seed"] = seed * 100 + int(round(kw["crash_discount"] * 100))
                bad = [c for c in g.columns if c not in f.columns or not (
                    np.array_equal(g[c].to_numpy(float), f[c].to_numpy(float), equal_nan=True) if c not in ("scenario", "phase", "macro")
                    else (g[c].astype(str).to_numpy() == f[c].astype(str).to_numpy()).all())]
                extra = [c for c in f.columns if c not in g.columns]
                if bad or extra:
                    raise RuntimeError(f"fast_panel differs from panel_from_env for {name} {scenario}-{seed}: {bad} extra {extra}")
            out[name] = f
    return out


def build(arms, n=SEP_N, T=200, seed0=SEP_SEED0, workers=3, verify=False, tag=""):
    jobs = [(sc, s, kw, T, arms, (verify and s == seed0)) for sc, s, kw in _sep_jobs(n, seed0)]
    frames = {name: [] for name in arms}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for i, res in enumerate(ex.map(_job, jobs, chunksize=4)):
            for name, f in res.items():
                frames[name].append(f)
            if (i + 1) % 200 == 0:
                print(f"    {i + 1}/{len(jobs)} paths, {time.time() - t0:.0f} s", flush=True)
    os.makedirs(PANELS, exist_ok=True)
    paths = {}
    for name, L in frames.items():
        panel = pd.concat(L, ignore_index=True)
        p = os.path.join(PANELS, f"sep_phase5_{tag}{name}.pkl")
        panel.to_pickle(p)
        paths[name] = p
        print(f"[panel] {name}: {panel[['scenario', 'seed']].drop_duplicates().shape[0]} paths, {len(panel)} rows -> {os.path.relpath(p, ROOT)}",
              flush=True)
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", required=True, help="json file or inline json: {name: {obs_overrides: {...}, config: {...}}}")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--n", type=int, default=SEP_N)
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    arms = json.load(open(a.arms, encoding="utf-8")) if os.path.exists(a.arms) else json.loads(a.arms)
    state = pin_state()
    t0 = time.time()
    paths = build(arms, n=a.n, workers=a.workers, verify=a.verify, tag=a.tag)
    man = os.path.join(PANELS, f"sep_phase5_{a.tag}manifest.json")
    prev = json.load(open(man, encoding="utf-8")) if os.path.exists(man) else {}
    prev.update({name: {"path": os.path.relpath(p, ROOT), "arm": arms[name], "state": state, "n_seeds": a.n,
                        "seed0": SEP_SEED0, "built": time.strftime("%Y-%m-%d %H:%M")} for name, p in paths.items()})
    json.dump(prev, open(man, "w", encoding="utf-8"), indent=1, default=str)
    print(f"done in {time.time() - t0:.0f} s; manifest {os.path.relpath(man, ROOT)}")


if __name__ == "__main__":
    main()
