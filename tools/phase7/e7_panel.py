"""
v2.1 Phase 7 -- the per-day policy panel every re-scoring reads (PREREG_PHASE_7.md 1.5, 2, 4).

    python -u -m tools.phase7.e7_panel --stages panel [--scored 100 --workers 6 --groups base,rules,l5,scripted]

WHY THIS EXISTS.  The Phase-7 execution prompt says `e6_16a/runs.csv` carries "every run's per-day allocations".
It does not: it carries one row per (scenario, seed, persona, policy) with the MCR at five thetas -- 14,400 rows,
no allocation series.  A re-scoring under a different theta, a different decomposition or a per-window rule cannot
be computed from it, so the trajectories are regenerated here.  Nothing about the generator, the oracles or the
rules changes: the pickled oracles under `e6_16a/` and the fitted `rules.json` are loaded, not refitted, so the
16A policies on this panel are the same policies Phase 6 scored (verified by `--stages verify`, which recomputes
16A's MCR from this panel and compares it with `runs.csv` row by row).

Policies per (scenario, seed, persona), all on the same price path with `PortfolioV2` at the 5 bp tier and the
persona's band centre as the start allocation:

  base      the `baselines_v2` set: always_hold, always_buy, always_sell, buy_day1_hold, constant_mix, momentum,
            mean_reversion, v_oracle, mandate_conditional_oracle, random_0..random_9  (+ band_lo, band_hi, 16A's
            constant band edges, which the PREREG 2.2 floor pool contains)
  rules     the pre-registered simple-rule family at 16A's fitted scale and direction: p_sma50, rsi, analyst
  l5        the two pickled level-free oracles: full_level_free (observables), level_free (price-only)
  scripted  E7.8's construct-validity sweeps: drift(d), align(p), panic(k)  -- see `scripted_policies`

Output: <out>/panel_<scenario>.parquet (per-day: cash_share, pre/post-trade share, portfolio value, traded value,
cost), <out>/paths_<scenario>.parquet (per-day x, price, phase -- one copy per path, not per policy),
<out>/meta.json.  Everything downstream reads these files; nothing downstream re-simulates.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

from tools.phase5.common import GEN, encode_nm, pin_state  # noqa: E402

OUT = os.path.join(GEN, "e7_panel")
E6_16A = os.path.join(GEN, "e6_16a")
SCENARIOS = ("flat", "bull_trap", "crash", "sustained_bull")
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
N_LAGS_16A = 20
# The reference theta of the `align` scripted policy: a property of the POLICY (which target it aims at), not of
# the scoring.  Fixed at the Phase-6 checkpoint value so the sweep is one family across every theta it is scored at.
ALIGN_REF_THETA = 0.05
DRIFT_RATES = (0.000, 0.002, 0.005, 0.010, 0.020, 0.040)
ALIGN_PROBS = (0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0)
PANIC_K = (0.0, 0.25, 0.5, 0.75, 1.0)
PANIC_DD = -0.10          # the drawdown at which the panic policy fires
CEIL_FIXED_P = 0.5        # E7.8's ceiling family: the directional probability held fixed while d varies


# ------------------------------------------------------------------------------------- rendering, shared per path
def _render_frame(env):
    """The rendered-field frame exactly as `Oracle16A.predict_x` builds it, done ONCE per path and shared by both
    oracles (the only optimisation in this file; it changes no number -- `--stages verify` proves it)."""
    from evaluation.leakage_audit import add_level_free_columns
    d = env.data[env.data["asset"] == 0]
    rows = []
    env.reset()
    for _ in range(env.n_days):
        o = env.get_observation()
        row = {k: float(v) for k, v in o.items() if k != "date" and not isinstance(v, (list, str))}
        if o.get("reported_PE") == "n/m":
            row["reported_PE"] = np.nan
        rows.append(row)
        env.step()
    env.reset()
    f = pd.DataFrame(rows)
    f["scenario"] = env.scenario; f["seed"] = env.seed; f["day"] = np.arange(1, len(f) + 1)
    f["P"] = d["price"].values; f["V"] = d["fundamental_value"].values; f["x"] = d["x"].values
    f = add_level_free_columns(encode_nm(f))
    if "reported_PE_nm" not in f:
        f["reported_PE_nm"] = 0.0
    return f


def _predict_from_frame(oracle, f):
    """`Oracle16A.predict_x` from the rendered frame onwards, verbatim."""
    from evaluation.leakage_audit import add_lags_and_returns
    fl, _ = add_lags_and_returns(f, [k for k in oracle.keys if k in f.columns], n_lags=N_LAGS_16A)
    X = fl[oracle.cols].to_numpy(dtype=float)
    ok = ~np.isnan(X).any(axis=1)
    xh = np.zeros(len(fl)); xh[ok] = oracle.model.predict(X[ok])
    return xh


# -------------------------------------------------------------------------------------- E7.8's scripted policies
def scripted_policies(persona: str, scenario: str, seed: int, x: np.ndarray):
    """The three construct-validity sweeps (PREREG 4.1).  Each is a deterministic function of a seeded RNG, so the
    same (scenario, seed, persona) gives the same trajectory on every run.

      drift(d)  the target walks away from the band centre at rate d per day, in a direction drawn once per run
      align(p)  with probability p the target is the true-x oracle's band edge, else the opposite edge
      panic(k)  while the portfolio is more than PANIC_DD below its running peak, the target moves a fraction k of
                the way from the band centre to full cash; otherwise it is the centre
      ceil(d)   align at a FIXED directional probability CEIL_FIXED_P plus drift d -- the family E7.8's correlation
                ceiling is derived from (PREREG 4.2: "hold the directional probability fixed and vary only the
                drift rate"); it is the only family that carries both, which is why it exists
    """
    from evaluation.scoring import centre_and_hw
    c2, hw = centre_and_hw(persona)
    lo, hi = c2 - hw, c2 + hw
    key = abs(hash((scenario, int(seed), persona))) % (2 ** 31)
    out = {}

    dir_rng = np.random.default_rng(700000 + key)
    direction = 1.0 if dir_rng.random() < 0.5 else -1.0
    for d in DRIFT_RATES:
        def pol(t, r, st, s, d=d, direction=direction, c2=c2):
            return float(min(max(c2 + direction * d * t, 0.0), 1.0))
        out[f"drift_{d:.3f}"] = pol

    # the true-x oracle's target series at the policy's reference theta
    tgt = np.empty(len(x)); cur = c2
    for i, xi in enumerate(x):
        if xi < -ALIGN_REF_THETA:
            cur = lo
        elif xi > ALIGN_REF_THETA:
            cur = hi
        tgt[i] = cur
    for p in ALIGN_PROBS:
        u = np.random.default_rng(710000 + key).random(len(x))
        opp = np.where(np.isclose(tgt, hi), lo, hi)
        series = np.where(u < p, tgt, opp)

        def pol(t, r, st, s, series=series):
            return float(series[t])
        out[f"align_{p:.1f}"] = pol

    # E7.8's CEILING family (PREREG 4.2): the directional probability held FIXED at 0.5 while only the drift rate
    # varies.  The registered ceiling construction needs one family carrying both, which `drift` and `align` do not
    # -- see PREREG_PHASE_7_ADDENDUM.md section 2.  target = align(0.5) target + the same drift as `drift(d)`.
    u_fix = np.random.default_rng(710000 + key).random(len(x))
    opp_fix = np.where(np.isclose(tgt, hi), lo, hi)
    series_fix = np.where(u_fix < CEIL_FIXED_P, tgt, opp_fix)
    for d in DRIFT_RATES:
        def pol(t, r, st, s, d=d, direction=direction, series=series_fix):
            return float(min(max(series[t] + direction * d * t, 0.0), 1.0))
        out[f"ceil_d{d:.3f}"] = pol

    for k in PANIC_K:
        def pol(t, r, st, s, k=k, c2=c2):
            peak = s.setdefault("peak", st["total_value"])
            peak = s["peak"] = max(peak, st["total_value"])
            dd = st["total_value"] / peak - 1.0 if peak > 0 else 0.0
            return float(c2 + k * (1.0 - c2)) if dd < PANIC_DD else float(c2)
        out[f"panic_{k:.2f}"] = pol
    return out


# ---------------------------------------------------------------------------------------------------- one path
_ORACLES: dict = {}
_RULES: dict = {}


def _init_worker(oracle_paths, rules):
    import warnings
    warnings.filterwarnings("ignore")
    os.environ["OMP_NUM_THREADS"] = "1"
    _load_oracles(oracle_paths)
    _RULES.update(rules)


def _load_oracles(oracle_paths):
    """Phase 6 pickled the oracles from `python -m tools.phase6.e6_16a`, so the class is recorded as
    `__main__.Oracle16A`.  Rebind it before unpickling rather than re-fitting: these must be the SAME oracles
    Phase 6 scored (16A's training pool, its 20-day history, its n/m encoding)."""
    import __main__
    from tools.phase6.e6_16a import Oracle16A
    if not hasattr(__main__, "Oracle16A"):
        __main__.Oracle16A = Oracle16A
    for k, p in oracle_paths.items():
        with open(p, "rb") as fh:
            _ORACLES[k] = pickle.load(fh)


def _rows_from_policy(env, persona, start, policy, cost_bp, interface="target"):
    """`baselines_v2._run_policy` with the pre/post-trade shares kept (weakness 60)."""
    from simulation.portfolio_v2 import PortfolioV2
    d = env.data[env.data["asset"] == 0].reset_index(drop=True)
    P = d["price"].to_numpy(dtype=float)
    port = PortfolioV2(10000.0, start, P[0])
    rows = []
    state = {}
    for t in range(len(P)):
        row = d.iloc[t]
        st = port.get_state(P[t])
        if interface == "target":
            rec = port.retarget(policy(t, row, st, state), P[t], t + 1, cost_bp=cost_bp)
        else:
            a, q = policy(t, row, st, state)
            rec = port.execute_v1_action(a, q, P[t], t + 1, cost_bp=cost_bp)
        st2 = port.get_state(P[t])
        rows.append((t + 1, st2["cash_share"], st2["total_value"], rec["traded_value"], rec["cost_paid"],
                     rec.get("cash_share_before", st["cash_share"]), rec.get("cash_share_after", st2["cash_share"])))
    return rows


def _one_path(args):
    sc, seed, T, groups, cost_bp = args
    from envs.synthetic_market import SyntheticMarketEnv
    from evaluation.baselines_v2 import baseline_policies
    from evaluation.targets import band, centre
    from tools.phase6.e6_16a import rule_policy
    env = SyntheticMarketEnv(sc, T, seed)
    d = env.data[env.data["asset"] == 0].reset_index(drop=True)
    x = d["x"].to_numpy(float)
    xh = {}
    if "l5" in groups:
        f = _render_frame(env)
        xh = {k: _predict_from_frame(o, f) for k, o in _ORACLES.items()}
    out = []
    for persona in PERSONAS:
        c0 = centre(persona); lo, hi = band(persona)
        pols = {}
        if "base" in groups:
            for name, (fn, iface) in baseline_policies(persona, c0, random_seeds=10).items():
                pols[name] = (fn, iface)
            pols["band_lo"] = ((lambda t, r, st, s, lo=lo: lo), "target")
            pols["band_hi"] = ((lambda t, r, st, s, hi=hi: hi), "target")
        if "rules" in groups:
            for fam in ("p_sma50", "rsi", "analyst"):
                r = _RULES[fam]
                pols[f"rule_{fam}"] = (rule_policy(fam, tuple(r["scale"]) if isinstance(r["scale"], list) else r["scale"],
                                                   r["direction"], persona), "target")
        if "l5" in groups:
            for k, o in _ORACLES.items():
                tg = o.policy(persona, xh[k], c0)
                pols[f"L5_{k}"] = ((lambda t, r, st, s, tg=tg: float(tg[t])), "target")
        if "scripted" in groups:
            for name, fn in scripted_policies(persona, sc, seed, x).items():
                pols[name] = (fn, "target")
        for name, (fn, iface) in pols.items():
            for (day, cs, pv, tv, cp, pre, post) in _rows_from_policy(env, persona, c0, fn, cost_bp, iface):
                out.append((sc, seed, persona, name, day, cs, pv, tv, cp, pre, post))
    path = [(sc, seed, int(t + 1), float(x[t]), float(d["price"].iloc[t]), str(d["phase"].iloc[t]))
            for t in range(len(x))]
    return out, path


COLS = ["scenario", "seed", "persona", "policy", "day", "cash_share", "portfolio_value",
        "traded_value", "cost_paid", "cash_share_pre", "cash_share_post"]
PCOLS = ["scenario", "seed", "day", "x", "price", "phase"]


def _shrink(df: pd.DataFrame) -> pd.DataFrame:
    """Categoricals and int32 for the labels; float64 kept for every number.  A first build stored the shares as
    float32 and `--stages verify` then read 3e-8 against Phase 6 -- float32 rounding, not a construction
    difference, but the panel is what every downstream number is computed from and an exact reproduction of 16A is
    worth more than the disk it costs."""
    for c in ("seed", "day"):
        if c in df:
            df[c] = df[c].astype("int32")
    for c in ("scenario", "persona", "policy", "phase"):
        if c in df:
            df[c] = df[c].astype("category")
    return df


def panel(scored: int, seed0: int, T: int, workers: int, groups, cost_bp: float, scenarios):
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    oracle_paths = {fs: os.path.join(E6_16A, f"oracle_{fs}.pkl") for fs in ("full_level_free", "level_free")}
    for p in oracle_paths.values():
        if not os.path.exists(p):
            raise SystemExit(f"missing pickled oracle {p} -- Phase 6's 16A must have run")
    rules = json.load(open(os.path.join(E6_16A, "rules.json"), encoding="utf-8"))
    state = pin_state()
    print(f"[panel] {len(scenarios)} scenarios x {scored} seeds, groups {sorted(groups)}, {workers} workers", flush=True)
    written = {}
    for sc in scenarios:
        pp = os.path.join(OUT, f"panel_{sc}.parquet")
        if os.path.exists(pp):
            print(f"  {sc}: exists, skipped", flush=True); written[sc] = pp; continue
        jobs = [(sc, s, T, groups, cost_bp) for s in range(seed0, seed0 + scored)]
        buf, pbuf = [], []
        ts = time.time()
        with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker,
                                 initargs=(oracle_paths, rules)) as ex:
            for i, (rows, path) in enumerate(ex.map(_one_path, jobs, chunksize=1), 1):
                buf.extend(rows); pbuf.extend(path)
                if i % 20 == 0 or i == len(jobs):
                    print(f"  {sc} {i}/{len(jobs)} ({time.time() - ts:.0f} s)", flush=True)
        _shrink(pd.DataFrame(buf, columns=COLS)).to_parquet(pp, index=False)
        _shrink(pd.DataFrame(pbuf, columns=PCOLS)).to_parquet(os.path.join(OUT, f"paths_{sc}.parquet"), index=False)
        written[sc] = pp
        print(f"  {sc}: {len(buf)} rows -> {pp} ({time.time() - ts:.0f} s)", flush=True)
    meta = {"scored": scored, "seed0": seed0, "T": T, "groups": sorted(groups), "cost_bp": cost_bp,
            "scenarios": list(scenarios), "personas": list(PERSONAS), "state": state,
            "oracles": {k: os.path.relpath(v, ROOT) for k, v in oracle_paths.items()}, "rules": rules,
            "align_ref_theta": ALIGN_REF_THETA, "drift_rates": list(DRIFT_RATES), "align_probs": list(ALIGN_PROBS),
            "panic_k": list(PANIC_K), "panic_drawdown": PANIC_DD, "n_lags_16a": N_LAGS_16A,
            "ceil_fixed_p": CEIL_FIXED_P, "ceil_drift_rates": list(DRIFT_RATES),
            "seconds": round(time.time() - t0), "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(meta, open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8"), indent=1, default=str)
    print(f"[panel] -> {OUT} ({time.time() - t0:.0f} s)", flush=True)


def verify():
    """Recompute 16A's MCR from this panel and compare with `e6_16a/runs.csv`, row by row.  This is the proof that
    sharing the rendered frame between the two oracles changed nothing (PREREG 9: every change proved inert)."""
    from evaluation.metrics_v2 import oracle_target
    from evaluation.targets import centre
    ref = pd.read_csv(os.path.join(E6_16A, "runs.csv"))
    name_map = {"oracle": "mandate_conditional_oracle", "always_hold": "always_hold", "constant_mix": "constant_mix",
                "band_lo": "band_lo", "band_hi": "band_hi", "L5_full_level_free": "L5_full_level_free",
                "L5_level_free": "L5_level_free", "rule_p_sma50": "rule_p_sma50", "rule_rsi": "rule_rsi",
                "rule_analyst": "rule_analyst"}
    rows = []
    for sc in SCENARIOS:
        pp = os.path.join(OUT, f"panel_{sc}.parquet")
        if not os.path.exists(pp):
            continue
        pan = pd.read_parquet(pp); paths = pd.read_parquet(os.path.join(OUT, f"paths_{sc}.parquet"))
        xmap = {(int(s), int(d)): float(v) for s, d, v in zip(paths.seed, paths.day, paths.x)}
        for (seed, persona, policy), g in pan.groupby(["seed", "persona", "policy"], observed=True):
            if policy not in name_map.values():
                continue
            g = g.sort_values("day")
            x = np.array([xmap[(int(seed), int(d))] for d in g.day])
            C = g.cash_share.to_numpy(float)
            for th in (0.03, 0.05, 0.08, 0.12, 0.20):
                res = np.abs(x) >= th
                if not res.any():
                    continue
                cs = oracle_target(x, th, persona, prev_target=C[0])
                mine = float(np.mean(np.abs(C[res] - cs[res])))
                back = {v: k for k, v in name_map.items()}[policy]
                r = ref[(ref.scenario == sc) & (ref.seed == seed) & (ref.persona == persona) & (ref.policy == back)]
                if r.empty:
                    continue
                rows.append({"scenario": sc, "seed": int(seed), "persona": persona, "policy": policy, "theta": th,
                             "phase7": mine, "phase6": float(r[f"mcr_{th}"].iloc[0])})
    t = pd.DataFrame(rows)
    if t.empty:
        print("[verify] no overlapping rows"); return
    t["abs_diff"] = (t.phase7 - t.phase6).abs()
    worst = float(t.abs_diff.max())
    t.to_csv(os.path.join(OUT, "verify_vs_16a.csv"), index=False)
    summ = t.groupby("policy", observed=True)["abs_diff"].agg(["max", "mean", "size"]).reset_index()
    print(summ.to_string(index=False), flush=True)
    print(f"[verify] {len(t)} comparisons, worst |phase7 - phase6| = {worst:.3e} -> "
          f"{'IDENTICAL' if worst <= 1e-12 else 'DIFFERS'}", flush=True)
    json.dump({"n": len(t), "worst_abs_diff": worst, "identical": bool(worst <= 1e-12),
               "by_policy": summ.to_dict("records")},
              open(os.path.join(OUT, "verify_vs_16a.json"), "w", encoding="utf-8"), indent=1, default=float)


def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="panel,verify")
    ap.add_argument("--scored", type=int, default=100)
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--T", type=int, default=200)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--groups", default="base,rules,l5,scripted")
    ap.add_argument("--scenarios", default=",".join(SCENARIOS))
    ap.add_argument("--cost-bp", type=float, default=5.0)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    OUT = a.out
    groups = set(g.strip() for g in a.groups.split(",") if g.strip())
    scen = [s.strip() for s in a.scenarios.split(",") if s.strip()]
    for st in a.stages.split(","):
        st = st.strip()
        if st == "panel":
            panel(a.scored, a.seed0, a.T, a.workers, groups, a.cost_bp, scen)
        elif st == "verify":
            verify()
        else:
            raise SystemExit(f"unknown stage {st!r}")


if __name__ == "__main__":
    main()
