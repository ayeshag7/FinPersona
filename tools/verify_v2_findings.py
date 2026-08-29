"""
Phase 0 (v2.1) reproduction of the computational review findings (plan Section 4, item 0.1;
PREREG_PHASE_0.md Sections 1-3 fix every seed, statistic, interval and verdict rule used here).

Every numbered finding of `docs/env_v2/reviews/V2_WEAKNESSES.md` that is computational is recomputed on
fresh seeds with a cluster-bootstrap interval and printed beside the reviewers' value with the verdict
R (reproduced) / S (reproduced in substance) / N (not reproduced) / D (documentary).

Usage:
    python -m tools.verify_v2_findings                       # full pre-registered run ("before" the Phase-0 fixes)
    python -m tools.verify_v2_findings --fast                # 6 seeds per block, for a dry run of the code only
    python -m tools.verify_v2_findings --only R3,R5,R10 --tag after   # the analyst-affected blocks after the fix
    python -m tools.verify_v2_findings --render              # rebuild the markdown from the stored JSON blocks

Outputs (docs/env_v2/generated/v2_1/):
    findings/<block>[_<tag>].json   per-block numbers (seeds, n, intervals, reviewer values, verdicts)
    findings_reproduction.md        the report table
    phase0_numbers.json             the canonical numbers the documents and tests/test_docs_numbers.py refer to
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from typing import Callable, Dict, List

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "8")

OUT_DEFAULT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
GEN_DIR = os.path.join(ROOT, "docs", "env_v2", "generated")
THETA = 0.05
N_BOOT = 2000
N_BOOT_CLF = 200

SEEDS = {
    "S200": list(range(10000, 10050)), "S800": list(range(11000, 11050)), "S5000": list(range(12000, 12010)),
    "SMULTI": list(range(13000, 13050)), "SANALYST": list(range(15000, 15100)), "SSB50": list(range(18000, 18050)),
    "SPILOT": [9001, 9002, 9003, 9004, 9005],
}
SCENARIOS4 = ("flat", "crash", "bull_trap", "sustained_bull")


# ----------------------------------------------------------------------------------------------------
# helpers: generation jobs (module level for ProcessPoolExecutor), bootstrap, verdicts
# ----------------------------------------------------------------------------------------------------
def _path_job(kw: dict):
    from envs.v2.generator import GenConfig, generate
    return generate(GenConfig(**kw))


def _env_job(kw: dict):
    from envs.synthetic_market import SyntheticMarketEnv
    from evaluation.leakage_audit import panel_from_env
    kw = dict(kw)
    label = kw.pop("_label", "")
    env = SyntheticMarketEnv(**kw)
    panel = panel_from_env(env, env.scenario, env.seed)
    keep_full = ["day", "asset", "phase", "garch_sigma", "implied_volatility", "x", "fvar21", "fw_weight"]
    return {"label": label, "kw": kw, "panel": panel, "data": env.data.copy(),
            "full": env._full[keep_full].copy(), "attempts": int(env.attempts),
            "event_meta": {k: v for k, v in env.event_meta.items() if k != "assets"},
            "schedule": env.schedule.to_dict(), "engine_params": env.result.params.name}


def pmap(fn: Callable, items: list, workers: int):
    if workers <= 1:
        return [fn(it) for it in items]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, items, chunksize=1))


def boot(stat: Callable[[list], float], clusters: list, n_boot: int = N_BOOT, seed: int = 0):
    """Percentile cluster bootstrap over `clusters` (one entry per path). Returns (lo, hi, sd)."""
    rng = np.random.default_rng(seed)
    k = len(clusters)
    vals = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, k, k)
        vals[b] = stat([clusters[i] for i in idx])
    ok = np.isfinite(vals)
    if ok.sum() < 10:
        return (float("nan"), float("nan"), float("nan"))
    return (float(np.percentile(vals[ok], 2.5)), float(np.percentile(vals[ok], 97.5)), float(np.std(vals[ok])))


def wilson(k: int, n: int):
    if n == 0:
        return (float("nan"), float("nan"))
    z = 1.959964; p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


def verdict_R(mine, lo, hi, rev, n_mine=None, n_rev=None, sd=None, tol=None):
    """PREREG §3 rule R: reviewer value inside my 95 % interval, or within the two-sample allowance
    1.96 sqrt(SE^2 + SE^2 n_mine/n_rev); deterministic quantities: |mine - rev| <= tol."""
    if rev is None:
        return "D"
    if tol is not None:
        return "R" if abs(mine - rev) <= tol else "N"
    if lo == lo and hi == hi and lo <= rev <= hi:
        return "R"
    if n_mine and n_rev and sd is not None and sd == sd:
        if abs(mine - rev) <= 1.96 * math.sqrt(sd ** 2 + sd ** 2 * n_mine / n_rev):
            return "R"
    return "N"


def acf1(x):
    x = np.asarray(x, float); x = x - x.mean()
    den = (x * x).sum()
    return float((x[:-1] * x[1:]).sum() / den) if den > 0 else float("nan")


def hl_from_acf(a):
    return float(-math.log(2) / math.log(a)) if 0 < a < 1 else float("inf")


def bench(res):
    m = res.day >= 1
    return m


def fmt(v, d=3):
    if v is None:
        return "—"
    if isinstance(v, str):
        return v
    if isinstance(v, (bool, np.bool_)):
        return str(bool(v))
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if v != v:
        return "nan"
    if abs(v) >= 100:
        return f"{v:.1f}"
    return f"{v:.{d}f}"


class Rows:
    """Collects report rows: one per statistic."""

    def __init__(self, block: str):
        self.block = block
        self.rows: List[dict] = []
        self.detail: Dict = {}

    def add(self, item, statistic, mine, n, ci=None, reviewer=None, rev_source="", verdict="", note="", rev_n=None):
        self.rows.append({"block": self.block, "item": item, "statistic": statistic, "mine": mine, "n": n,
                          "ci": ci, "reviewer": reviewer, "rev_source": rev_source, "rev_n": rev_n,
                          "verdict": verdict, "note": note})

    def save(self, out_dir: str, tag: str = ""):
        os.makedirs(os.path.join(out_dir, "findings"), exist_ok=True)
        p = os.path.join(out_dir, "findings", f"{self.block}{('_' + tag) if tag else ''}.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump({"block": self.block, "tag": tag, "rows": self.rows, "detail": self.detail}, fh, indent=1, default=_js)
        return p


def _js(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return str(o)


# ----------------------------------------------------------------------------------------------------
# calm-engine pilots (the long pilots of PREREG §1 SPILOT; never touch mispricing._PILOT_CACHE)
# ----------------------------------------------------------------------------------------------------
def long_pilot(params, engine: str, n_steps: int, sd_e: float, seed: int, w_norm, burn: int):
    from envs.v2.mispricing import MispricingState
    rng = np.random.default_rng(seed)
    st = MispricingState(params, engine, x0=0.0, w_norm=w_norm)
    e = rng.normal(0.0, sd_e, n_steps)
    nfs = np.empty(n_steps); ws = np.empty(n_steps); xs = np.empty(n_steps)
    for i in range(n_steps):
        nfs[i] = st.n_f; ws[i] = st.raw_weight(); xs[i] = st.x
        st.step(e[i], 0.0)
    x = xs[burn:]
    a = acf1(x)
    return {"n_bar": float(nfs[burn:].mean()), "w_bar_raw": float(ws[burn:].mean()), "sd_x": float(x.std()),
            "acf1_x": a, "half_life": hl_from_acf(a), "share_nf_gt_099": float(np.mean(nfs[burn:] > 0.99)),
            "seed": seed, "n_steps": n_steps, "sd_e": sd_e, "w_norm": w_norm, "burn": burn}


def _pilot_job(kw):
    from envs.v2.mispricing import load_params, FWParams
    p = kw.pop("params")
    if isinstance(p, dict):
        p = FWParams(**p)
    else:
        p = load_params(p)
    return long_pilot(p, kw.pop("engine"), **kw)


# ----------------------------------------------------------------------------------------------------
# blocks
# ----------------------------------------------------------------------------------------------------
def block_R1(envs_a: dict, out) -> Rows:
    """Item 1: the 'compare price with 100' rule vs the oracle and trivial policies (ISFJ, theta 0.05)."""
    from evaluation.baselines_v2 import _run_policy, baseline_policies
    from evaluation.metrics_v2 import score_run, oracle_target
    from evaluation.targets import band, centre
    R = Rows("R1_start_price_rule")
    lo_b, hi_b = band("ISFJ"); c0 = centre("ISFJ")

    class Shim:
        def __init__(self, data): self.data = data

    def rule100(t, r, st, s):
        lx = math.log(r["price"] / 100.0)
        return hi_b if lx > THETA else (lo_b if lx < -THETA else st["cash_share"])

    per_sc = {}
    for sc in SCENARIOS4:
        rows = []
        for e in envs_a[sc]:
            env = Shim(e["data"])
            pols = baseline_policies("ISFJ", c0, THETA, random_seeds=2)
            pols["rule100"] = (rule100, "target")
            pols["edge_lo"] = (lambda t, r, st, s: lo_b, "target")
            pols["edge_hi"] = (lambda t, r, st, s: hi_b, "target")
            m = {}
            for name, (fn, iface) in pols.items():
                if name in ("momentum", "mean_reversion", "v_oracle", "buy_day1_hold", "always_buy", "always_sell"):
                    continue
                df = _run_policy(env, c0, fn, cost_bp=5.0, interface=iface)
                m[name] = score_run(df, "ISFJ", c0)["mcr_0.05"]
            # direct scoring (no execution): the rule's target vs the oracle target
            d = e["data"]; x = d["x"].to_numpy(float); P = d["price"].to_numpy(float)
            lx = np.log(P / 100.0); tgt = np.empty(len(x)); cur = c0
            for i in range(len(x)):
                cur = hi_b if lx[i] > THETA else (lo_b if lx[i] < -THETA else cur)
                tgt[i] = cur
            cs = oracle_target(x, THETA, "ISFJ", prev_target=c0)
            res = np.abs(x) >= THETA
            m["rule100_direct"] = float(np.mean(np.abs(tgt[res] - cs[res]))) if res.any() else float("nan")
            m["always_hold_direct"] = float(np.mean(np.abs(c0 - cs[res]))) if res.any() else float("nan")
            m["random_mean"] = float(np.nanmean([m.pop("random_0"), m.pop("random_1")]))
            rows.append(m)
        per_sc[sc] = rows
    rev = {"flat": 0.014, "crash": 0.007, "bull_trap": 0.005, "sustained_bull": 0.098}
    rev_direct = {"flat": 0.022, "crash": 0.011, "bull_trap": 0.007, "sustained_bull": 0.083}
    summary = {}
    for sc, rows in per_sc.items():
        summary[sc] = {}
        for pol in ("rule100", "mandate_conditional_oracle", "always_hold", "constant_mix", "edge_lo", "edge_hi", "random_mean", "rule100_direct", "always_hold_direct"):
            vals = [r[pol] for r in rows]
            mean = float(np.nanmean(vals)); lo, hi, sd = boot(lambda c: float(np.nanmean(c)), vals)
            summary[sc][pol] = {"mean": mean, "lo": lo, "hi": hi, "sd": sd, "n": len(vals)}
        s = summary[sc]
        R.add(1, f"{sc}: MCR of the 'compare with 100' rule (PortfolioV2, 5 bp)", s["rule100"]["mean"], s["rule100"]["n"],
              (s["rule100"]["lo"], s["rule100"]["hi"]), rev[sc], "C §A.2 (12 seeds)",
              verdict_R(s["rule100"]["mean"], s["rule100"]["lo"], s["rule100"]["hi"], rev[sc], 50, 12, s["rule100"]["sd"]),
              note=f"oracle {s['mandate_conditional_oracle']['mean']:.3f}, always-hold {s['always_hold']['mean']:.3f}, "
                   f"constant-mix {s['constant_mix']['mean']:.3f}, edge-lo {s['edge_lo']['mean']:.3f}, edge-hi {s['edge_hi']['mean']:.3f}, random {s['random_mean']['mean']:.3f}", rev_n=12)
        R.add(1, f"{sc}: MCR of the rule, direct scoring (no execution)", s["rule100_direct"]["mean"], s["rule100_direct"]["n"],
              (s["rule100_direct"]["lo"], s["rule100_direct"]["hi"]), rev_direct[sc], "LOG §1 (12 seeds)",
              verdict_R(s["rule100_direct"]["mean"], s["rule100_direct"]["lo"], s["rule100_direct"]["hi"], rev_direct[sc], 50, 12, s["rule100_direct"]["sd"]),
              note=f"always-hold direct {s['always_hold_direct']['mean']:.3f}", rev_n=12)
    # substance: rule within 0.02 of the oracle in flat/crash/bull and > 0.05 in the sustained bull
    gap = {sc: summary[sc]["rule100"]["mean"] - summary[sc]["mandate_conditional_oracle"]["mean"] for sc in SCENARIOS4}
    substance = all(gap[sc] <= 0.02 for sc in ("flat", "crash", "bull_trap")) and gap["sustained_bull"] > 0.05
    R.add(1, "substance: rule within 0.02 of the oracle in flat/crash/bull and > 0.05 above it in sustained bull",
          "yes" if substance else "no", 200, None, "yes", "C §A.2 / W 1", "S" if substance else "N",
          note="gaps " + ", ".join(f"{sc} {gap[sc]:+.3f}" for sc in SCENARIOS4))
    R.detail = {"summary": summary}
    return R


def block_R2(paths: dict, pilots: dict, out) -> Rows:
    """Items 2, 11: fundamentalist share saturation."""
    R = Rows("R2_fw_inert")
    rev = {"flat": 0.983, "crash": 0.987, "bull_trap": 0.991}
    for sc in ("flat", "crash", "bull_trap"):
        nfs = [r.n_f[0, bench(r)] for r in paths[sc]]
        share = float(np.mean(np.concatenate(nfs) > 0.99)); mean_nf = float(np.mean(np.concatenate(nfs)))
        lo, hi, sd = boot(lambda c: float(np.mean(np.concatenate(c) > 0.99)), nfs)
        R.add(2, f"{sc}: share of days with n_f > 0.99", share, len(nfs), (lo, hi), rev[sc], "C §A.1 (10 seeds)",
              verdict_R(share, lo, hi, rev[sc], 50, 10, sd), note=f"mean n_f {mean_nf:.4f}", rev_n=10)
    p100 = pilots["live_20k"]; p1 = pilots["index_scale1_20k"]; p100i = pilots["index_scale100_20k"]
    R.add(2, "pilot n̄ at price_scale 100, index set (20,000 steps, seed 12345)", p100i["n_bar"], 1, None, 0.9985, "LOG §1",
          verdict_R(p100i["n_bar"], None, None, 0.9985, tol=0.001), note=f"live engine (phi 0.463) n̄ {p100['n_bar']:.4f}")
    R.add(2, "pilot n̄ at price_scale 1, index set (20,000 steps, seed 12345)", p1["n_bar"], 1, None, 0.8268, "LOG §1 / C (0.83)",
          verdict_R(p1["n_bar"], None, None, 0.8268, tol=0.001), note=f"chartist share {1 - p1['n_bar']:.3f}; SABCEMM DCA-HPM 0.2285 (simulated, own noise)")
    R.detail = {"pilots": {k: v for k, v in pilots.items() if k.endswith("20k")}}
    return R


def _feature_sets(dfl: pd.DataFrame, cols: List[str]):
    from evaluation.leakage_audit import PRICE_ONLY_KEYS
    level = [c for c in cols if c.split("_lag")[0] in PRICE_ONLY_KEYS]
    lf_base = ["ret_1", "ret_5", "ret_20", "lp_sma20", "lp_sma50", "RSI14", "macd_p", "macds_p", "trend_strength", "trend_regime"]
    lf = [c for c in dfl.columns if c in lf_base or (c.split("_lag")[0] in lf_base and "_lag" in c)]
    return {"level": level, "level_free": lf, "full": cols}


def _add_level_free(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["lp_sma20"] = np.log(df["price"] / df["SMA20"]); df["lp_sma50"] = np.log(df["price"] / df["SMA50"])
    df["macd_p"] = df["MACD"] / df["price"]; df["macds_p"] = df["MACD_signal"] / df["price"]
    return df


def attacker_table(panel: pd.DataFrame, feature_keys: List[str], n_boot: int = 500):
    """GBT (audit settings), GroupKFold by path; OOS R2(x), sign accuracy on resolvable steps, MAPE(V) per phase
    group and feature set, with cluster-bootstrap intervals over paths."""
    from evaluation.leakage_audit import add_lags_and_returns, _oos_predictions, _models
    panel = _add_level_free(panel)
    extra = ["lp_sma20", "lp_sma50", "macd_p", "macds_p"]
    dfl, cols = add_lags_and_returns(panel, feature_keys + extra)
    dfl = dfl.dropna(subset=cols).reset_index(drop=True)
    cols_full = [c for c in cols if c.split("_lag")[0] not in extra]
    fs = _feature_sets(dfl, cols_full)
    groups = (dfl["scenario"].astype(str) + "-" + dfl["seed"].astype(str)).to_numpy(dtype=object)
    y_x = dfl["x"].to_numpy(float); y_lv = np.log(dfl["V"].to_numpy(float))
    pg = dfl["macro"].replace({"down-event": "event", "up-event": "event"}).to_numpy(dtype=object)
    model = _models()["gbt"]
    ug = np.unique(groups); gidx = {g: np.where(groups == g)[0] for g in ug}
    out = {}
    for name, fc in fs.items():
        X = dfl[fc].to_numpy(float)
        px = _oos_predictions(X, y_x, groups, model)
        pv = _oos_predictions(X, y_lv, groups, model)
        out[name] = {"n_features": len(fc)}
        for grp in ("calm", "event", "all"):
            m = np.ones(len(y_x), bool) if grp == "all" else (pg == grp)
            def stat_r2(sel_groups, m=m):
                idx = np.concatenate([gidx[g] for g in sel_groups]); idx = idx[m[idx]]
                if len(idx) < 30: return float("nan")
                yy = y_x[idx]; ss = ((yy - yy.mean()) ** 2).sum()
                return float(1 - ((yy - px[idx]) ** 2).sum() / ss) if ss > 0 else float("nan")
            def stat_sign(sel_groups, m=m):
                idx = np.concatenate([gidx[g] for g in sel_groups]); idx = idx[m[idx] & (np.abs(y_x[idx]) >= THETA)]
                return float(np.mean(np.sign(px[idx]) == np.sign(y_x[idx]))) if len(idx) > 10 else float("nan")
            def stat_mape(sel_groups, m=m):
                idx = np.concatenate([gidx[g] for g in sel_groups]); idx = idx[m[idx]]
                return float(np.mean(np.abs(np.exp(pv[idx]) - np.exp(y_lv[idx])) / np.exp(y_lv[idx]))) if len(idx) else float("nan")
            r2 = stat_r2(list(ug)); sg = stat_sign(list(ug)); mp = stat_mape(list(ug))
            b_r2 = boot(stat_r2, list(ug), n_boot); b_sg = boot(stat_sign, list(ug), n_boot); b_mp = boot(stat_mape, list(ug), n_boot)
            out[name][grp] = {"R2_x": r2, "R2_ci": b_r2[:2], "R2_sd": b_r2[2], "sign_acc": sg, "sign_ci": b_sg[:2], "sign_sd": b_sg[2],
                              "MAPE_V": mp, "MAPE_ci": b_mp[:2], "MAPE_sd": b_mp[2], "n_rows": int(m.sum())}
    return out, len(ug)


def block_R3(envs_a: dict, envs_b: dict, out, n_boot=500) -> Rows:
    """Items 3, 5, 43: attackers on the anchored panel and on the randomised-start panel."""
    from envs.synthetic_market import CANONICAL_FIELDS
    R = Rows("R3_attackers")
    keys = [k for k in CANONICAL_FIELDS if k != "date"]
    res = {}
    for label, envs in (("anchored", envs_a), ("random_start", envs_b)):
        panel = pd.concat([e["panel"] for sc in SCENARIOS4 for e in envs[sc]], ignore_index=True)
        t0 = time.time(); tab, ng = attacker_table(panel, keys, n_boot); res[label] = tab
        print(f"  [R3] {label}: {ng} paths, {len(panel)} rows, {time.time() - t0:.0f} s", flush=True)
    # reviewer values
    revs = [("random_start", "level", "calm", "R2_x", 0.217, "C §A.3 price-only calm R2 (24 seeds)"),
            ("random_start", "level", "calm", "sign_acc", 0.768, "C §A.3"),
            ("random_start", "level", "event", "R2_x", 0.730, "C §A.3"),
            ("random_start", "level", "all", "MAPE_V", 0.153, "C §A.3 MAPE(V) price-only"),
            ("random_start", "full", "calm", "R2_x", 0.779, "C §A.3 full calm R2"),
            ("random_start", "full", "calm", "sign_acc", 0.862, "C §A.3"),
            ("random_start", "full", "event", "R2_x", 0.904, "C §A.3"),
            ("random_start", "full", "all", "MAPE_V", 0.101, "C §A.3 MAPE(V) full"),
            ("anchored", "level", "all", "R2_x", 0.84, "C §A.2 level features (OOS R2)"),
            ("anchored", "level", "all", "sign_acc", 0.945, "C §A.2"),
            ("anchored", "level_free", "all", "R2_x", 0.40, "C §A.2 level-free"),
            ("anchored", "level_free", "all", "sign_acc", 0.71, "C §A.2 level-free sign acc on resolvable steps"),
            ("anchored", "full", "calm", "R2_x", 0.898, "leakage_audit_v2.md (150 paths)"),
            ("anchored", "level", "calm", "R2_x", 0.787, "leakage_audit_v2.md price-only calm"),
            ("anchored", "full", "calm", "MAPE_V", 0.035, "leakage_audit_v2.md MAPE(V) calm"),
            ("anchored", "full", "event", "MAPE_V", 0.049, "leakage_audit_v2.md MAPE(V) event")]
    n_rev = {"C §A.3": 24, "C §A.2": 48, "leakage": 150}
    for label, fs, grp, stat, rv, src in revs:
        cell = res[label][fs][grp]
        key = {"R2_x": ("R2_x", "R2_ci", "R2_sd"), "sign_acc": ("sign_acc", "sign_ci", "sign_sd"), "MAPE_V": ("MAPE_V", "MAPE_ci", "MAPE_sd")}[stat]
        mine = cell[key[0]]; lo, hi = cell[key[1]]; sd = cell[key[2]]
        nr = 24 if "A.3" in src else (48 if "A.2" in src else 150)
        R.add({"anchored": 5, "random_start": 3}[label] if stat != "sign_acc" or fs != "level_free" else 43,
              f"{label} / {fs} / {grp}: {stat}", mine, 200, (lo, hi), rv, src, verdict_R(mine, lo, hi, rv, 200, nr, sd), rev_n=nr)
    # substance checks
    a, b = res["anchored"], res["random_start"]
    sel_r = b["full"]["calm"]["R2_x"] - b["level"]["calm"]["R2_x"]
    sel_a = a["full"]["calm"]["R2_x"] - a["level"]["calm"]["R2_x"]
    R.add(3, "substance: selectivity of the non-price fields (full − level, calm R2) is small when anchored and large when the start is randomised",
          f"anchored {sel_a:+.3f}; random-start {sel_r:+.3f}", 200, None, "+0.11 anchored vs +0.56 randomised", "C §A.3 / W 3",
          "S" if (sel_r > 0.3 and sel_a < 0.2) else "N")
    R.add(43, "substance: level-free attacker far below the level attacker on the anchored panel (R2 and sign)",
          f"level {a['level']['all']['R2_x']:.3f} / {a['level']['all']['sign_acc']:.3f}; level-free {a['level_free']['all']['R2_x']:.3f} / {a['level_free']['all']['sign_acc']:.3f}",
          200, None, "0.84 / 0.945 vs 0.40 / 0.71", "C §A.2 / W 43",
          "S" if (a["level"]["all"]["R2_x"] - a["level_free"]["all"]["R2_x"] > 0.2) else "N")
    R.detail = {"tables": res}
    return R


def block_R4(paths: dict, out) -> Rows:
    """Item 4: the flat control is biased cheap."""
    from envs.v2.mispricing import load_params, pilot_stats
    R = Rows("R4_flat_bias")
    xs = [r.x[0, bench(r)] for r in paths["flat"]]
    pm = [float(x.mean()) for x in xs]
    mean = float(np.mean(pm)); lo, hi, sd = boot(lambda c: float(np.mean(c)), pm)
    R.add(4, "flat: mean x (mean of path means)", mean, len(pm), (lo, hi), -0.100, "C §A.4 (30 seeds); LOG −0.077 (SE 0.019)", verdict_R(mean, lo, hi, -0.100, 50, 30, sd), rev_n=30)
    med = float(np.median(np.concatenate(xs))); lo2, hi2, sd2 = boot(lambda c: float(np.median(np.concatenate(c))), xs)
    R.add(4, "flat: pooled median x", med, len(xs), (lo2, hi2), -0.068, "C §A.4", verdict_R(med, lo2, hi2, -0.068, 50, 30, sd2), rev_n=30)
    pneg = float(np.mean(np.concatenate(xs) < 0)); lo3, hi3, sd3 = boot(lambda c: float(np.mean(np.concatenate(c) < 0)), xs)
    R.add(4, "flat: P(x < 0)", pneg, len(xs), (lo3, hi3), 0.70, "C §A.4", verdict_R(pneg, lo3, hi3, 0.70, 50, 30, sd3), rev_n=30)
    x1 = [float(x[0]) for x in xs]; m1 = float(np.mean(x1)); lo4, hi4, sd4 = boot(lambda c: float(np.mean(c)), x1)
    R.add(4, "flat: mean x on day 1", m1, len(x1), (lo4, hi4), -0.076, "C §A.4", verdict_R(m1, lo4, hi4, -0.076, 50, 30, sd4), rev_n=30)
    def under(c):
        z = np.concatenate(c); r = np.abs(z) >= THETA
        return float(np.mean(z[r] < 0)) if r.any() else float("nan")
    u = under(xs); lo5, hi5, sd5 = boot(under, xs)
    R.add(4, "flat: share of resolvable steps (|x| >= 0.05) that are undervalued", u, len(xs), (lo5, hi5), 0.74, "C §A.4", verdict_R(u, lo5, hi5, 0.74, 50, 30, sd5), rev_n=30)
    xc = [r.x[0, bench(r)] for r in paths["crash"]]
    uc = under(xc); lo6, hi6, sd6 = boot(under, xc)
    R.add(4, "crash δ 0.70: share of resolvable steps undervalued", uc, len(xc), (lo6, hi6), 0.84, "C §A.4", verdict_R(uc, lo6, hi6, 0.84, 50, 30, sd6), rev_n=30)
    xn = [r.x[0, bench(r)] for r in paths["flat_nojump"]]
    pmn = [float(x.mean()) for x in xn]; mn = float(np.mean(pmn)); lo7, hi7, sd7 = boot(lambda c: float(np.mean(c)), pmn)
    R.add(4, "flat, jumps off: mean x", mn, len(pmn), (lo7, hi7), -0.018, "C §A.4; LOG +0.009", verdict_R(mn, lo7, hi7, -0.018, 50, 30, sd7), rev_n=30)
    pn = float(np.mean(np.concatenate(xn) < 0)); lo8, hi8, sd8 = boot(lambda c: float(np.mean(np.concatenate(c) < 0)), xn)
    R.add(4, "flat, jumps off: P(x < 0)", pn, len(xn), (lo8, hi8), 0.50, "C §A.4; LOG 0.46", verdict_R(pn, lo8, hi8, 0.50, 50, 30, sd8), rev_n=30)
    p = load_params("fw_single"); ps = pilot_stats(p, "fw_single")
    pull = p.mu * ps["n_bar"] * p.phi
    analytic = -(0.010 * 0.04) / pull
    R.add(4, "analytic stationary mean −(rate × mean jump)/(μ n̄ φ)", analytic, 0, None, -0.087, "LOG §1", verdict_R(analytic, None, None, -0.087, tol=0.002),
          note=f"pull rate {pull:.5f}/day; rate 0.010, mean −0.04 (code)")
    R.detail = {"pull_rate": pull, "analytic_mean": analytic, "path_means": pm}
    return R


def block_R5(envs_a: dict, out) -> Rows:
    """Items 5, 20: L1 candidates and the extended three-term candidate on the anchored panel."""
    from envs.synthetic_market import CANONICAL_FIELDS
    from evaluation.leakage_audit import l1_algebraic, NOISE_FLOOR
    R = Rows("R5_L1_candidates")
    panel = pd.concat([e["panel"] for sc in SCENARIOS4 for e in envs_a[sc]], ignore_index=True)
    l1 = l1_algebraic(panel, list(CANONICAL_FIELDS))
    rev = {"k * P (price itself)": 0.1236, "k * P / reported_PE": 0.1546, "k * P * dividend_yield": 0.1558, "k * analyst_fair_value": 0.2235}
    P = panel["P"].to_numpy(float); V = panel["V"].to_numpy(float)
    groups = (panel["scenario"].astype(str) + "-" + panel["seed"].astype(str)).to_numpy(dtype=object)
    ug = np.unique(groups); gidx = {g: np.where(groups == g)[0] for g in ug}
    bases = {"k * P (price itself)": P, "k * P / reported_PE": P / panel["reported_PE"].replace(0, np.nan).to_numpy(float),
             "k * P * dividend_yield": P * panel["dividend_yield"].to_numpy(float), "k * analyst_fair_value": panel["analyst_fair_value"].to_numpy(float),
             "k * SMA50": panel["SMA50"].to_numpy(float)}
    apes = {}
    for name, base in bases.items():
        ok = np.isfinite(base) & (base > 0)
        k = np.exp(np.nanmedian(np.log(V[ok]) - np.log(base[ok])))
        apes[name] = np.abs(k * base - V) / V
    def _khat(base):
        ok = np.isfinite(base) & (base > 0)
        return np.exp(np.nanmedian(np.log(V[ok]) - np.log(base[ok]))) * base
    vhat3 = np.nanmean(np.column_stack([_khat(bases["k * SMA50"]), _khat(bases["k * P / reported_PE"]), _khat(bases["k * analyst_fair_value"])]), axis=1)
    apes["mean(k*SMA50, k*P/PE, k*analyst)"] = np.abs(vhat3 - V) / V
    detail = {}
    for name, ape in apes.items():
        def stat_med(sel, ape=ape):
            idx = np.concatenate([gidx[g] for g in sel]); return float(np.nanmedian(ape[idx]))
        med = stat_med(list(ug)); lo, hi, sd = boot(stat_med, list(ug), 500)
        pct = {q: float(np.nanpercentile(ape, q)) for q in (5, 10, 25, 50)}
        within = {w: float(np.nanmean(ape <= w)) for w in (0.01, 0.02, 0.05)}
        detail[name] = {"median_APE": med, "ci": (lo, hi), "percentiles": pct, "share_within": within, "share_above_floor": float(np.nanmean(ape > NOISE_FLOOR))}
        rv = rev.get(name); src = "leakage_audit_v2.md (150 paths)" if rv else "B row 5 (64 paths): 9.2 %, 27 % within 5 %"
        if name.startswith("mean("):
            rv = 0.092
        if name == "k * SMA50":
            rv = None; src = ""
        R.add(5, f"L1 median APE: {name}", med, len(ug), (lo, hi), rv, src, verdict_R(med, lo, hi, rv, 200, 150 if "leakage" in src else 64, sd) if rv is not None else "D",
              note=f"p5 {pct[5]:.3f}, p10 {pct[10]:.3f}, p25 {pct[25]:.3f}; within 1/2/5 %: {within[0.01]:.2f}/{within[0.02]:.2f}/{within[0.05]:.2f}", rev_n=150 if rv else None)
    R.add(5, "substance: the best single candidate is price itself (median APE = median |x|), and a three-term mean beats it",
          f"price {detail['k * P (price itself)']['median_APE']:.3f} vs three-term {detail['mean(k*SMA50, k*P/PE, k*analyst)']['median_APE']:.3f}", len(ug), None,
          "0.124 vs 0.092", "B rows 3, 5", "S" if detail["mean(k*SMA50, k*P/PE, k*analyst)"]["median_APE"] < detail["k * P (price itself)"]["median_APE"] else "N")
    R.detail = {"l1_audit_table": l1.to_dict(orient="records"), "candidates": detail}
    return R


def block_R6(paths: dict, out) -> Rows:
    """Item 6: the calendar is a phase clock in the setup-first population."""
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.model_selection import GroupKFold, cross_val_score
    import evaluation.stylized_facts as sf
    R = Rows("R6_calendar_clock")
    rev = {"crash": (0.804, 0.40), "bull_trap": (0.872, 0.54)}
    for sc in ("crash", "bull_trap"):
        rows = []
        for r in paths[sc]:
            m = bench(r); d = r.day[m]; ph = r.phase[m]
            rows.append(pd.DataFrame({"day": d, "macro": pd.Series(ph).map(sf.MACRO_OF).fillna("calm").values, "seed": r.cfg.seed}))
        df = pd.concat(rows, ignore_index=True)
        early = df[df.day <= 50]; late = df[df.day >= 170]
        p_calm_early = float(np.mean(early["macro"] == "calm")); p_ev_late = float(np.mean(late["macro"] != "calm"))
        R.add(6, f"{sc} setup-first: P(calm | day <= 50)", p_calm_early, len(rows), wilson(int((early['macro'] == 'calm').sum()), len(early)), 1.000, "C §C.20 (40 seeds)",
              verdict_R(p_calm_early, *wilson(int((early['macro'] == 'calm').sum()), len(early)), 1.000), note=f"{len(early)} path-days")
        R.add(6, f"{sc} setup-first: P(event | day >= 170)", p_ev_late, len(rows), wilson(int((late['macro'] != 'calm').sum()), len(late)), 1.000, "C §C.20",
              verdict_R(p_ev_late, *wilson(int((late['macro'] != 'calm').sum()), len(late)), 1.000), note=f"{len(late)} path-days")
        X = df[["day"]].to_numpy(float); y = df["macro"].to_numpy(dtype=object); g = df["seed"].to_numpy(dtype=object)
        acc = float(cross_val_score(HistGradientBoostingClassifier(max_depth=3), X, y, cv=GroupKFold(5), groups=g).mean())
        maj = float(pd.Series(y).value_counts(normalize=True).iloc[0])
        seeds = sorted(set(g))
        def stat_acc(sel):
            parts = []
            for j, s in enumerate(sel):
                part = df[df.seed == s].copy(); part["grp"] = j; parts.append(part)
            sub = pd.concat(parts, ignore_index=True)
            if sub["macro"].nunique() < 2: return float("nan")
            gg = sub["grp"].to_numpy(dtype=object)
            return float(cross_val_score(HistGradientBoostingClassifier(max_depth=3), sub[["day"]].to_numpy(float), sub["macro"].to_numpy(dtype=object), cv=GroupKFold(min(5, len(sel))), groups=gg).mean())
        lo, hi, sd = boot(stat_acc, seeds, 60)
        R.add(6, f"{sc} setup-first: day-only macro-phase accuracy (within scenario)", acc, len(rows), (lo, hi), rev[sc][0], "C §C.20 (40 seeds)",
              verdict_R(acc, lo, hi, rev[sc][0], 50, 40, sd), note=f"majority class {maj:.3f} (reviewer {rev[sc][1]:.2f}); bootstrap 60 resamples", rev_n=40)
    # mixed set (checklist item 15 as built) on my seeds
    row = sf.item15_phase_time({"mixed": [_pathdata(r, r.cfg.scenario) for r in paths["mixed"]]})
    m = re.search(r"= ([0-9.]+)% \(mixed set", row["statistic"]); mixed = float(m.group(1)) / 100 if m else float("nan")
    R.add(6, "mixed set (event-first + setup-first + flat): day-only macro accuracy (checklist item 15 statistic)", mixed, len(paths["mixed"]), None, 0.648, "checklist_v2.md (470 paths)",
          verdict_R(mixed, None, None, 0.648, tol=0.03), note=row["statistic"])
    return R


def _pathdata(res, scenario):
    import evaluation.stylized_facts as sf
    m = bench(res)
    df = pd.DataFrame({"day": res.day[m], "price": res.P[0, m], "value": res.V[0, m], "phase": res.phase[m], "x": res.x[0, m],
                       "sigma": res.sigma[0, m], "volume": np.nan, "sentiment": res.sent[0, m], "iv": np.nan})
    meta = {"delta": res.cfg.delta, "D_V": res.schedule.D_V, "topped": res.event_meta.get("topped"), "rejected": False,
            "n_rejections": res.attempts - 1, "b_pred": res.cfg.b_pred, "ordering": res.cfg.ordering}
    return sf.PathData(scenario, res.cfg.seed, df, meta)


def block_R7(paths: dict, out) -> Rows:
    """Item 13 (coupling with 4): jumps and the flat kurtosis share."""
    from scipy import stats
    R = Rows("R7_jumps_kurtosis")
    rev = {"flat": 0.85, "flat_meanzero": 0.70, "flat_nojump": 0.60}
    lab = {"flat": "current jumps (N(−0.04, 0.03), rate 0.010)", "flat_meanzero": "mean-zero jumps", "flat_nojump": "no jumps"}
    for key in ("flat", "flat_meanzero", "flat_nojump"):
        ks = []; mx = []
        for r in paths[key]:
            m = bench(r); rr = np.diff(np.log(r.P[0, m])); ks.append(float(stats.kurtosis(rr))); mx.append(float(r.x[0, m].mean()))
        share = float(np.mean(np.array(ks) > 1.5)); lo, hi = wilson(int(np.sum(np.array(ks) > 1.5)), len(ks))
        R.add(13, f"flat, {lab[key]}: share of paths with excess kurtosis > 1.5", share, len(ks), (lo, hi), rev[key], "LOG §2 (40 seeds); pass-3 review 0.70/0.55/0.45",
              verdict_R(share, lo, hi, rev[key]), note=f"median kurtosis {np.median(ks):.2f}; mean x {np.mean(mx):+.3f}")
    return R


def block_R8(paths: dict, out) -> Rows:
    """Items 16, 47: script share of event-phase moves; mania days at the drift cap."""
    from envs.v2.events import make_driver
    from envs.v2.rng import Streams
    from envs.v2.mispricing import load_params, pilot_stats, FW_INDEX_2012
    R = Rows("R8_script_share")

    def rerun(res):
        cfg, sched = res.cfg, res.schedule
        driver = make_driver(sched, cfg.hazard_h0, cfg.hazard_b, cfg.g_max, cfg.lam_panic)
        u = Streams(cfg.seed, res.attempts - 1).get("hazard", 0).random(res.L)
        x = res.x[0]; day = res.day; L = res.L
        d = np.zeros(L); ph = np.empty(L, dtype=object); cap = np.zeros(L, bool)
        for i in range(L):
            di, mu, p = driver.begin(int(day[i]), float(x[i]))
            d[i] = di; ph[i] = p
            if p == "mania":
                cap[i] = abs(di - cfg.g_max) < 1e-12
            if i + 1 < L:
                driver.end(int(day[i + 1]), float(x[i + 1]), u[i])
        assert driver.meta().get("top_day") == res.event_meta.get("top_day"), "driver re-run did not reproduce the top day"
        dx = np.diff(x); return d[:-1], ph[:-1], cap[:-1], dx

    def share_stats(sel, phase_set):
        num = 0.0; den = 0.0; vd = []; vdx = []
        for (d, ph, cap, dx) in sel:
            m = np.isin(ph, list(phase_set))
            if m.sum() < 5: continue
            num += ((dx[m] - d[m]) ** 2).sum(); den += ((dx[m] - dx[m].mean()) ** 2).sum(); vd.append(d[m]); vdx.append(dx[m])
        if den == 0: return float("nan"), float("nan")
        vd = np.concatenate(vd); vdx = np.concatenate(vdx)
        return float(1 - num / den), float(vd.var() / vdx.var())
    crash = [rerun(r) for r in paths["crash"]]; bull = [rerun(r) for r in paths["bull_trap"]]
    for name, sel, phs in (("crash panic", crash, {"panic"}), ("crash stabilisation", crash, {"stabilisation"}), ("bull post-top", bull, {"post-top"}), ("bull mania", bull, {"mania"})):
        r2, vr = share_stats(sel, phs); lo, hi, sd = boot(lambda c, phs=phs: share_stats(c, phs)[0], sel, 500)
        R.add(16, f"{name}: script share R² of Δx on the scripted drift d_t", r2, len(sel), (lo, hi), None, "not quantified by the reviews (W 16 asks for it)", "D",
              note=f"var(d)/var(Δx) = {vr:.3f}")
    caps = [(int(c.sum()), int(np.sum(ph == "mania"))) for (d, ph, c, dx) in bull]
    tot_c = sum(a for a, b in caps); tot_m = sum(b for a, b in caps)
    share = tot_c / tot_m if tot_m else float("nan"); lo, hi, sd = boot(lambda c: (sum(a for a, b in c) / max(1, sum(b for a, b in c))), caps)
    R.add(47, "bull_trap: share of mania days at the drift cap g_max", share, len(bull), (lo, hi), 0.38, "C §A.8 (seeds 0-29)", verdict_R(share, lo, hi, 0.38, 50, 30, sd), rev_n=30)
    p = load_params("fw_single"); nb = pilot_stats(p, "fw_single")["n_bar"]
    pull_live = p.mu * nb * p.phi * 0.30; pull_index = FW_INDEX_2012.mu * nb * FW_INDEX_2012.phi * 0.30
    step = np.median(np.abs(np.concatenate([d[np.isin(ph, ["panic"])] for (d, ph, c, dx) in crash])))
    R.add(16, "FW pull per day at x = −0.30: live φ (0.463) / index φ (0.12)", f"{pull_live:.5f} / {pull_index:.5f}", 0, None, "0.00034 (index φ)", "C §A.8",
          verdict_R(pull_index, None, None, 0.00034, tol=0.00005), note=f"median scripted panic step |d_t| = {step:.4f}/day")
    return R


def block_R9(paths: dict, out) -> Rows:
    """Items 18, 42: sustained-bull first-attempt selection."""
    from envs.v2.generator import check_validity
    R = Rows("R9_sb_selection")
    acc, rej = [], []
    for r in paths["sb_first"]:
        m = bench(r); rr = np.diff(np.log(r.P[0, m])); P = r.P[0, m]
        d = {"sd": float(rr.std()), "acf1": acf1(rr), "sd20": float(np.std(np.log(P[20:] / P[:-20]))), "reason": check_validity(r)}
        (acc if d["reason"] is None else rej).append(d)
    flat = []
    for r in paths["flat"]:
        m = bench(r); rr = np.diff(np.log(r.P[0, m])); P = r.P[0, m]
        flat.append({"sd": float(rr.std()), "acf1": acf1(rr), "sd20": float(np.std(np.log(P[20:] / P[:-20])))})
    wl = wilson(len(rej), len(acc) + len(rej))
    R.add(18, "sustained_bull first attempts: accepted / rejected", f"{len(acc)} / {len(rej)}", len(acc) + len(rej), wl, "33 / 27 (C), 32 / 18 (LOG)", "C §A.5, LOG §1",
          "R" if (wl[0] <= 0.45 <= wl[1]) or (wl[0] <= 0.36 <= wl[1]) else "N",
          note=f"rejected share {len(rej) / (len(acc) + len(rej)):.2f}; interval = Wilson 95 % for the rejected share (reviewer 0.45 / LOG 0.36)")
    for stat, rv_a, rv_r, src in (("sd", 0.0147, 0.0240, "C §A.5 daily sd"), ("acf1", -0.025, None, "C §A.5 ACF1 (accepted vs flat +0.024)"), ("sd20", 0.044, None, "C §A.5 20-day return sd (accepted vs flat 0.080)")):
        va = [d[stat] for d in acc]; vr = [d[stat] for d in rej]; vf = [d[stat] for d in flat]
        ma = float(np.mean(va)); la, ha, sa = boot(lambda c: float(np.mean(c)), va); mr = float(np.mean(vr)); lr, hr, sr = boot(lambda c: float(np.mean(c)), vr)
        mf = float(np.mean(vf)); lf, hf, sf_ = boot(lambda c: float(np.mean(c)), vf)
        R.add(18, f"{stat}: accepted", ma, len(va), (la, ha), rv_a, src, verdict_R(ma, la, ha, rv_a, len(va), 33, sa), note=f"rejected {mr:.4f} [{lr:.4f}, {hr:.4f}] (n {len(vr)}); flat {mf:.4f} [{lf:.4f}, {hf:.4f}]", rev_n=33)
        if rv_r is not None:
            R.add(18, f"{stat}: rejected", mr, len(vr), (lr, hr), rv_r, src, verdict_R(mr, lr, hr, rv_r, len(vr), 27, sr), rev_n=27)
    rate_num = sum(r.attempts - 1 for r in paths["sb_rej"]); rate_den = sum(r.attempts for r in paths["sb_rej"])
    rate = rate_num / rate_den
    R.add(42, "sustained_bull rejection rate under rejection sampling (rejections / attempts)", rate, len(paths["sb_rej"]), wilson(rate_num, rate_den), 0.398, "checklist_v2.md item 17 (50 seeds); LOG 0.36",
          verdict_R(rate, *wilson(rate_num, rate_den), 0.398), note=f"mean attempts {rate_den / len(paths['sb_rej']):.2f}")
    sda = float(np.mean([d["sd"] for d in acc])); sdr = float(np.mean([d["sd"] for d in rej]))
    R.add(42, "substance: accepted paths are quieter than rejected ones (daily sd) and than flat", "yes" if (sda < sdr and sda < float(np.mean([d['sd'] for d in flat]))) else "no", len(acc), None, "yes", "C §A.5 / W 42",
          "S" if (sda < sdr) else "N", note=f"{sda:.4f} vs {sdr:.4f}; relative difference {(sdr - sda) / sdr:.2%}")
    R.detail = {"accepted": acc, "rejected": rej}
    return R


def analyst_stats(seeds, tag=""):
    from envs.v2 import observables as obs
    from envs.v2.rng import Streams
    L = 460; day = np.arange(L) - 260 + 1; V = np.ones(L)
    us = []
    for s in seeds:
        u = obs.analyst_block(day, V, Streams(s, 0).get("analyst", 0))["analyst_error_u"]
        us.append(u)
    return us, day


def block_R10(envs_a: dict, out, seeds=None) -> Rows:
    """Items 21, 68: analyst error sd as implemented."""
    R = Rows("R10_analyst")
    seeds = seeds or SEEDS["SANALYST"]
    us, day = analyst_stats(seeds)
    m = day >= 1
    sd_full = float(np.concatenate(us).std()); lo, hi, sd = boot(lambda c: float(np.concatenate(c).std()), us)
    sd_b = float(np.concatenate([u[m] for u in us]).std()); lob, hib, sdb = boot(lambda c: float(np.concatenate([u[m] for u in c]).std()), us)
    med = float(np.median(np.abs(np.concatenate([u[m] for u in us])))); lom, him, sdm = boot(lambda c: float(np.median(np.abs(np.concatenate([u[m] for u in c])))), us)
    R.add(68, "pooled sd(u), full 460-day timeline", sd_full, len(us), (lo, hi), 0.306, "LOG §1 (30 crash seeds); PLAN 0.350", verdict_R(sd_full, lo, hi, 0.306, len(us), 30, sd), rev_n=30)
    R.add(68, "pooled sd(u), benchmark days", sd_b, len(us), (lob, hib), 0.333, "C §D.24 measured 0.333; LOG 0.330; analytic 0.15√5 = 0.335", verdict_R(sd_b, lob, hib, 0.333, len(us), 30, sdb), rev_n=30)
    R.add(68, "median |u|, benchmark days", med, len(us), (lom, him), 0.222, "LOG §1; B 0.21", verdict_R(med, lom, him, 0.222, len(us), 30, sdm), rev_n=30)
    R.add(68, "documented stationary sd", 0.15, 0, None, 0.15, "observables.py docstring, spec §6, slide 5", "D", note="analytic implemented value 0.15 × √5 = 0.335")
    # the reviewers' design: crash envs
    uc = [e["data"]["analyst_error_u"].to_numpy(float) for e in envs_a["crash"]]
    sdc = float(np.concatenate(uc).std()); loc, hic, sdc_ = boot(lambda c: float(np.concatenate(c).std()), uc)
    R.add(68, "crash δ 0.70 envs: pooled sd(u) on benchmark days", sdc, len(uc), (loc, hic), 0.330, "LOG §1", verdict_R(sdc, loc, hic, 0.330, len(uc), 30, sdc_), rev_n=30)
    # the analyst field's own APE (what slide 5 calls the '22 %' error)
    ape = [np.abs(e["data"]["analyst_fair_value"].to_numpy(float) / e["data"]["fundamental_value"].to_numpy(float) - 1) for sc in SCENARIOS4 for e in envs_a[sc]]
    ma = float(np.median(np.concatenate(ape))); loa, hia, sda = boot(lambda c: float(np.median(np.concatenate(c))), ape)
    R.add(21, "median |F/V − 1| of the analyst field (all four scenarios)", ma, len(ape), (loa, hia), 0.2235, "leakage_audit_v2.md k·analyst median APE", verdict_R(ma, loa, hia, 0.2235, len(ape), 150, sda), rev_n=150)
    R.detail = {"sd_full": sd_full, "sd_bench": sd_b, "median_abs_u": med, "median_ape": ma}
    return R


def block_R11(envs_a: dict, out) -> Rows:
    """Item 25: the IV stress threshold is a full-path quantile (look-ahead)."""
    R = Rows("R11_iv_lookahead")
    diffs = []; flagged_panic = []
    for e in envs_a["crash"]:
        f = e["full"]; s2 = f["garch_sigma"].to_numpy(float) ** 2; day = f["day"].to_numpy(int); ph = f["phase"].to_numpy(dtype=object)
        thr = np.quantile(s2, 0.9); flag_full = s2 >= thr
        flag_past = np.array([s2[i] >= np.quantile(s2[: i + 1], 0.9) for i in range(len(s2))])
        m = day >= 1
        diffs.append(float(np.mean(flag_full[m] != flag_past[m])))
        fl = flag_full & m
        flagged_panic.append(float(np.mean(ph[fl] == "panic")) if fl.any() else float("nan"))
    d = float(np.mean(diffs)); lo, hi, sd = boot(lambda c: float(np.mean(c)), diffs)
    R.add(25, "crash: share of benchmark days whose stress flag differs between the full-path and a past-only 0.9 quantile", d, len(diffs), (lo, hi), 0.09, "C §A.7", verdict_R(d, lo, hi, 0.09, 50, 30, sd), rev_n=30)
    fp = float(np.nanmean(flagged_panic)); lo2, hi2, sd2 = boot(lambda c: float(np.nanmean(c)), flagged_panic)
    R.add(25, "crash: share of flagged days (full-path rule) that are panic days", fp, len(flagged_panic), (lo2, hi2), 0.75, "C §A.7", verdict_R(fp, lo2, hi2, 0.75, 50, 30, sd2), rev_n=30)
    return R


def block_R12(pilots: dict, out) -> Rows:
    """Item 35: the SMM attempt (documentary) and the regime of the J-profile."""
    R = Rows("R12_smm")
    rej = json.load(open(os.path.join(ROOT, "envs", "v2", "params", "fw_single_stock.REJECTED.json"), encoding="utf-8"))
    prof = pd.read_csv(os.path.join(GEN_DIR, "fw_J_profile.csv"))
    R.add(35, "REJECTED.json: J", rej["J"], 0, None, 408.15, "B row 12", "D", note=f"start-J recorded: {'J_index_start' in rej}; tickers {len(rej['tickers'])} (survivors); price_scale {rej['price_scale']}")
    R.add(35, "J-profile over phi (diagonal 1/target² proxy weights): min–max of J", f"{prof['J'].min():.2f}–{prof['J'].max():.2f}", len(prof), None, "2.9–3.2 (flat)", "CALIBRATION_REPORT §6", "D",
          note="phi grid " + ", ".join(str(v) for v in prof["phi"].tolist()))
    nbar = {k: v["n_bar"] for k, v in pilots.items() if k.startswith("profile_phi_")}
    R.add(35, "pilot n̄ at every phi of the profile grid (price_scale 100, 20,000 steps, seed 12345)", "; ".join(f"φ {k.split('_')[-1]}: {v:.4f}" for k, v in nbar.items()), len(nbar), None, "n_f ≈ 1 throughout", "B row 12 / C §A.1",
          "R" if all(v > 0.99 for v in nbar.values()) else "N", note="the profile was computed where chartists never act")
    return R


def block_R13(paths: dict, pilots: dict, out) -> Rows:
    """Items 36, 62, 71: the half-life estimator, the long pilots, the stationary sd(x)."""
    import evaluation.stylized_facts as sf
    from envs.v2.mispricing import load_params, pilot_stats
    R = Rows("R13_half_life")
    # (a) sample half-life on calm windows
    def hl_stats(plist):
        hls = []; sds = []; a1 = []
        for r in plist:
            m = bench(r); x = r.x[0, m]
            a = sf.acf(x, 1); hls.append(hl_from_acf(a)); sds.append(float(np.std(x))); a1.append(a)
        return np.array(hls), np.array(sds), np.array(a1)
    revs = {"S200": (26.0, "PLAN 26 d (30 flat); LOG 35 d; C 14 d (calm windows)"), "S800": (72.0, "checklist item 9 (20 paths) 72 d; PLAN/LOG 65 d; B 62 d"), "S5000": (None, "")}
    for key, plist in (("S200", paths["flat"]), ("S800", paths["flat_800"]), ("S5000", paths["flat_5000"])):
        hls, sds, a1 = hl_stats(plist); fin = np.isfinite(hls)
        med = float(np.median(hls[fin])) if fin.any() else float("nan"); lo, hi, sd = boot(lambda c: float(np.median([v for v in c if np.isfinite(v)])), hls.tolist(), 1000)
        sh60 = float(np.mean(hls >= 60)); q = np.percentile(hls[fin], [25, 75]) if fin.any() else (np.nan, np.nan)
        rv, src = revs[key]
        R.add(36, f"{key}: median sample half-life −ln2/ln ACF(1) of x on the whole (calm) window", med, len(plist), (lo, hi), rv, src,
              verdict_R(med, lo, hi, rv, len(plist), 30 if key == "S200" else 20, sd) if rv else "D",
              note=f"IQR {q[0]:.0f}–{q[1]:.0f} d; share >= 60 d {sh60:.2f} (Wilson {wilson(int(np.sum(hls >= 60)), len(hls))[0]:.2f}–{wilson(int(np.sum(hls >= 60)), len(hls))[1]:.2f}); median within-window sd(x) {np.median(sds):.3f}; median ACF(1) {np.median(a1):.4f}", rev_n=30 if key == "S200" else 20)
    # (b) pure AR(1) table
    rng = np.random.default_rng(14000); table = {}
    for hl_true in (60, 150, 580):
        rho = 2 ** (-1 / hl_true); s_stat = 1.0 / math.sqrt(1 - rho ** 2)
        for T in (200, 800, 2000, 5000):
            n = 200; x = np.empty((n, T)); x[:, 0] = rng.normal(0, s_stat, n)
            eps = rng.normal(0, 1, (n, T))
            for t in range(1, T):
                x[:, t] = rho * x[:, t - 1] + eps[:, t]
            hls = np.array([hl_from_acf(sf.acf(x[i], 1)) for i in range(n)])
            fin = np.isfinite(hls)
            table[f"hl{hl_true}_T{T}"] = {"median": float(np.median(hls[fin])), "p5": float(np.percentile(hls[fin], 5)), "p95": float(np.percentile(hls[fin], 95)), "share_ge_60": float(np.mean(hls >= 60)), "n": n}
    revb = {"hl150_T800": (62.0, 0.54), "hl150_T200": (21.0, None), "hl150_T2000": (98.0, None), "hl150_T5000": (127.0, None), "hl580_T800": (84.0, None), "hl60_T800": (41.0, None)}
    for k, (rv, rs) in revb.items():
        t = table[k]
        R.add(36, f"pure AR(1) {k}: median sample half-life (200 paths)", t["median"], 200, (t["p5"], t["p95"]), rv, "B row 9 (check_bias.py)", verdict_R(t["median"], None, None, rv, tol=max(0.15 * rv, 5.0)),
              note=f"5–95 %: {t['p5']:.0f}–{t['p95']:.0f} d; share >= 60 d {t['share_ge_60']:.2f}" + (f" (reviewer {rs})" if rs else "") + "; tolerance 15 % (sampling of 200-path medians)")
    # (c) the long pilots
    p = load_params("fw_single"); ps = pilot_stats(p, "fw_single")
    pull_hl = math.log(2) / (p.mu * ps["n_bar"] * p.phi)
    R.add(71, "pull-rate half-life ln2/(μ n̄ φ) at the live parameters", pull_hl, 0, None, 150.0, "LOG §1", verdict_R(pull_hl, None, None, 150.0, tol=0.5), note=f"φ = {p.phi:.4f}, n̄ = {ps['n_bar']:.4f}, μ = {p.mu}")
    R.add(71, "cached 20,000-step pilot (seed 12345, sd_e 0.016, raw weights): ACF(1)-implied half-life", hl_from_acf(ps["acf1_x"]), 1, None, 188.5, "LOG §1", verdict_R(hl_from_acf(ps["acf1_x"]), None, None, 188.5, tol=1.0),
          note=f"ACF(1) {ps['acf1_x']:.5f}; sd_x {ps['sd_x']:.4f} (what CALIBRATION_REPORT §1 prints as 0.142)")
    for cfg_key, label in (("live_200k_e017_engine", "engine weights, sd_e 0.017"), ("live_200k_e016_engine", "engine weights, sd_e 0.016"), ("live_200k_e017_raw", "raw weights, sd_e 0.017"), ("live_200k_e016_raw", "raw weights, sd_e 0.016")):
        runs = [v for k, v in pilots.items() if k.startswith(cfg_key + "_")]
        hls = [r["half_life"] for r in runs]; sds = [r["sd_x"] for r in runs]
        rv_hl = 147.0 if "engine" in cfg_key else None
        R.add(71, f"five 200,000-step pilots ({label}): ACF(1) half-life mean [min–max]", float(np.mean(hls)), 5, (float(min(hls)), float(max(hls))), rv_hl, "LOG §1 (141–154, mean 147); pass-3 142 / 160" if rv_hl else "",
              verdict_R(float(np.mean(hls)), None, None, rv_hl, tol=8.0) if rv_hl else "D", note=f"sd(x) mean {np.mean(sds):.4f} [{min(sds):.4f}–{max(sds):.4f}]; mean n_f {np.mean([r['n_bar'] for r in runs]):.4f}")
    # sd(x) hypothesis (PREREG §8)
    def _mean_sd(prefix):
        return float(np.mean([v["sd_x"] for k, v in pilots.items() if k.startswith(prefix)]))
    eng16 = _mean_sd("live_200k_e016_engine_"); raw16 = _mean_sd("live_200k_e016_raw_")
    eng17 = _mean_sd("live_200k_e017_engine_"); raw17 = _mean_sd("live_200k_e017_raw_")
    rho = 1 - p.mu * ps["n_bar"] * p.phi; k = 1 / math.sqrt(1 - rho ** 2)
    pred = {"engine_016": 0.016 * k, "engine_017": 0.017 * k, "raw_016": 0.016 * k * ps["w_bar"], "raw_017": 0.017 * k * ps["w_bar"]}
    R.add(71, "stationary sd(x): 200k pilots, engine weights (sd_e 0.016 / 0.017)", f"{eng16:.4f} / {eng17:.4f}", 5, None, "0.162–0.169 (LOG, held)", "LOG §1; PREREG §8 prediction "
          f"{pred['engine_016']:.3f} / {pred['engine_017']:.3f}", "R" if 0.155 <= eng16 <= 0.175 or 0.155 <= eng17 <= 0.18 else "N")
    R.add(71, "stationary sd(x): 200k pilots, raw weights as pilot_stats measures (sd_e 0.016 / 0.017)", f"{raw16:.4f} / {raw17:.4f}", 5, None, "0.131 / 0.140 (pass-3, sd_e 0.017); 0.142 (calibration report, 20k)", "PREREG §8 prediction "
          f"{pred['raw_016']:.3f} / {pred['raw_017']:.3f}", "R" if 0.125 <= raw17 <= 0.145 else "N",
          note=f"ratio raw/engine = {raw17 / eng17:.3f} vs w̄ = {ps['w_bar']:.3f} (hypothesis H: the pilot understates the engine's sd by the factor w̄)")
    # full generator T = 5000
    for key, lab in (("flat_5000", "jumps on"), ("flat_5000_nojump", "jumps off")):
        sds = [float(np.std(r.x[0, bench(r)])) for r in paths[key]]
        R.add(71, f"full generator, T = 5000 flat ({lab}): sample sd(x) mean over 10 seeds", float(np.mean(sds)), len(sds), (float(min(sds)), float(max(sds))), None, "", "D", note="min–max over seeds; GARCH-t innovations")
    # 200k normalisation deltas (deferred change, PREREG §4.5)
    r200 = [v for k, v in pilots.items() if k.startswith("live_200k_e016_raw_")]
    nb200 = float(np.mean([r["n_bar"] for r in r200])); wb200 = float(np.mean([r["w_bar_raw"] for r in r200]))
    phi200 = (math.log(2) / 150.0) / (p.mu * nb200)
    R.add(71, "what a 200,000-step normalisation would change: n̄, w̄, φ (relative to the cached 20k values)", f"n̄ {nb200:.5f} vs {ps['n_bar']:.5f}; w̄ {wb200:.5f} vs {ps['w_bar']:.5f}; φ {phi200:.5f} vs {p.phi:.5f} ({(phi200 / p.phi - 1):+.3%})", 5, None, None, "", "D",
          note="deferred to Phase 2: any change moves every path (PREREG §4.5)")
    R.detail = {"ar1_table": table, "pull_hl": pull_hl, "phi": p.phi, "n_bar": ps["n_bar"], "w_bar": ps["w_bar"], "pred": pred,
                "pilots": {k: v for k, v in pilots.items() if "200k" in k}, "sd_engine_016": eng16, "sd_engine_017": eng17, "sd_raw_016": raw16, "sd_raw_017": raw17}
    return R


def block_R14(paths: dict, out) -> Rows:
    """Item 40: checklist item 10 with an interval."""
    import evaluation.stylized_facts as sf
    R = Rows("R14_item10")
    crash = [_pathdata(r, "crash") for d in (0.55, 0.70, 0.85) for r in paths[f"crash_{d}"]]
    row = sf.item10_delta_matters(crash)
    rows = [(p.meta["delta"], p.meta["D_V"], sf._event_window_mdd(p), p.seed) for p in crash]
    df = pd.DataFrame(rows, columns=["delta", "D_V", "mdd", "seed"]).dropna()
    seeds = sorted(df["seed"].unique())
    def stat(sel, which):
        sub = pd.concat([df[df.seed == s] for s in sel], ignore_index=True)
        pr2, spread, g = sf._delta_stats(sub); return pr2 if which == "pr2" else spread
    pr2 = stat(seeds, "pr2"); spread = stat(seeds, "spread")
    lo, hi, sd = boot(lambda c: stat(c, "pr2"), seeds, 1000); lo2, hi2, sd2 = boot(lambda c: stat(c, "spread"), seeds, 1000)
    R.add(40, "crash: event-window MDD partial R² of δ (controlling D_V)", pr2, len(df), (lo, hi), 0.38, "checklist_v2.md (150 paths)", verdict_R(pr2, lo, hi, 0.38, 150, 150, sd), rev_n=150)
    R.add(40, "crash: event-window MDD spread δ 0.55 vs 0.85 (pp)", spread, len(df), (lo2, hi2), 18.0, "checklist_v2.md", verdict_R(spread, lo2, hi2, 18.0, 150, 150, sd2), note=row["statistic"], rev_n=150)
    return R


def block_R15(paths: dict, out) -> Rows:
    """Item 41: the un-capped mania claim."""
    R = Rows("R15_uncapped")
    for key, lab in (("bull_uncapped", "g_max = 1.0, reject=False"), ("bull_uncapped_rej", "g_max = 1.0, rejection sampling"), ("bull_trap", "live cap 0.012, rejection sampling")):
        pv = []; topped = []
        for r in paths[key]:
            m = bench(r); pv.append(float(np.exp(r.x[0, m]).max())); topped.append(bool(r.event_meta.get("topped")))
        gt3 = int(np.sum(np.array(pv) > 3)); ts = float(np.mean(topped))
        R.add(41, f"bull_trap ({lab}): share of runs with peak P/V > 3", gt3 / len(pv), len(pv), wilson(gt3, len(pv)), 1.0 if key == "bull_uncapped" else None, "A5 / spec §3: 'without a cap every run reaches P/V > 3'" if key == "bull_uncapped" else "",
              ("S" if gt3 / len(pv) > 0.8 else "N") if key == "bull_uncapped" else "D", note=f"topped share {ts:.2f}; median peak P/V {np.median(pv):.2f}; mean attempts {np.mean([r.attempts for r in paths[key]]):.2f}")
    return R


def block_R16(envs_a: dict, out) -> Rows:
    """Item 46: IV is a one-day phase step."""
    R = Rows("R16_iv_step")
    def transitions(envs, pairs):
        out = {p: [] for p in pairs}; calm_diffs = []
        for e in envs:
            d = e["data"]; ph = d["phase"].to_numpy(dtype=object); liv = np.log(d["implied_volatility"].to_numpy(float))
            dl = np.diff(liv)
            both_calm = (ph[:-1] == "calm") & (ph[1:] == "calm"); calm_diffs.append(dl[both_calm])
            for (a, b) in pairs:
                idx = np.where((ph[:-1] == a) & (ph[1:] == b))[0]
                if len(idx): out[(a, b)].append(float(dl[idx[0]]))
        return out, calm_diffs
    tc, cd_c = transitions(envs_a["crash"], [("deterioration", "panic"), ("panic", "stabilisation"), ("calm", "deterioration")])
    tb, cd_b = transitions(envs_a["bull_trap"], [("calm", "mania"), ("blow-off", "post-top")])
    calm_sd = float(np.concatenate(cd_c + cd_b).std()); lo, hi, sdd = boot(lambda c: float(np.concatenate(c).std()), cd_c + cd_b)
    R.add(46, "calm day-to-day sd of log IV (pooled, crash + bull calm days)", calm_sd, len(cd_c + cd_b), (lo, hi), 0.089, "C §A.6 (30+30 seeds); LOG 0.086", verdict_R(calm_sd, lo, hi, 0.089, 100, 60, sdd), rev_n=60)
    rev = {("deterioration", "panic"): 0.62, ("panic", "stabilisation"): -0.64, ("calm", "deterioration"): 0.15, ("calm", "mania"): 0.15, ("blow-off", "post-top"): 0.33}
    for tr, vals in list(tc.items()) + list(tb.items()):
        m = float(np.mean(vals)); lo2, hi2, sd2 = boot(lambda c: float(np.mean(c)), vals)
        R.add(46, f"mean Δlog IV at {tr[0]} → {tr[1]}", m, len(vals), (lo2, hi2), rev[tr], "C §A.6", verdict_R(m, lo2, hi2, rev[tr], len(vals), 30, sd2), note=f"z = {m / calm_sd:+.2f} (×{math.exp(m):.2f})", rev_n=30)
    return R


def block_R17(paths: dict, out) -> Rows:
    """Item 48: one-shot side call."""
    from evaluation.metrics_v2 import oracle_target
    from evaluation.targets import band, centre
    R = Rows("R17_one_shot")
    lo_b, hi_b = band("ISFJ"); c0 = centre("ISFJ")
    rev_med = {"flat": 0, "crash": 1, "bull_trap": 1, "sustained_bull": 2}
    rev_share = {"flat": 0.25, "crash": 0.45, "bull_trap": 0.30, "sustained_bull": 0.55}
    for sc in SCENARIOS4:
        sw = []; edge = []
        for r in paths[sc]:
            m = bench(r); x = r.x[0, m]; cs = oracle_target(x, THETA, "ISFJ", prev_target=c0)
            sw.append(int(np.sum(np.diff(cs) != 0)))
            res = np.abs(x) >= THETA
            if res.sum():
                edge.append(max(float(np.mean(cs[res] == lo_b)), float(np.mean(cs[res] == hi_b))))
        med = float(np.median(sw)); share2 = float(np.mean(np.array(sw) >= 2))
        R.add(48, f"{sc}: median oracle target switches per run (ISFJ, θ 0.05)", med, len(sw), (float(np.percentile(sw, 25)), float(np.percentile(sw, 75))), rev_med[sc], "C §B.15 (30) / LOG §2 (30) / pass-3 (20)", verdict_R(med, None, None, rev_med[sc], tol=1.0),
              note=f"share of runs with >= 2 switches {share2:.2f} (Wilson {wilson(int(np.sum(np.array(sw) >= 2)), len(sw))[0]:.2f}–{wilson(int(np.sum(np.array(sw) >= 2)), len(sw))[1]:.2f}; pass-3 {rev_share[sc]}); IQR shown as the interval")
        me = float(np.mean(edge)); lo, hi, sd = boot(lambda c: float(np.mean(c)), edge)
        R.add(48, f"{sc}: share of resolvable steps at a single band edge (mean over runs)", me, len(edge), (lo, hi), 0.84 if sc != "sustained_bull" else None, "C §B.15: 77–91 % (flat/crash/bull)", verdict_R(me, lo, hi, 0.84, len(edge), 30, sd) if sc != "sustained_bull" else "D", rev_n=30)
    return R


def block_R18(paths: dict, out) -> Rows:
    """Item 49: blow-off label and the top day."""
    R = Rows("R18_blowoff_top")
    un = 0; bo_start = []; offby = []; xdiff = []
    for r in paths["bull_trap"]:
        m = bench(r); day = r.day[m]; ph = r.phase[m]; x = r.x[0, m]
        if not r.event_meta.get("topped"):
            un += 1; idx = np.where(ph == "blow-off")[0]
            if len(idx): bo_start.append(int(day[idx[0]]))
        else:
            td = int(r.event_meta["top_day"]); imax = int(day[np.argmax(x)])
            offby.append(imax == td + 1); xdiff.append(float(x.max() - r.event_meta["x_top"]))
    n = len(paths["bull_trap"])
    R.add(49, "bull_trap: un-topped share", un / n, n, wilson(un, n), 0.58, "C §A.11 (seeds 0-29?)", verdict_R(un / n, *wilson(un, n), 0.58), note=f"blow-off label starts on day {min(bo_start) if bo_start else '-'}–{max(bo_start) if bo_start else '-'} in un-topped runs (reviewer 153–170)")
    R.add(49, "topped runs: share whose realised maximum of x falls on top_day + 1", float(np.mean(offby)), len(offby), wilson(int(np.sum(offby)), len(offby)), "most", "C §A.12 (off by one)", "S" if np.mean(offby) > 0.5 else "N",
          note=f"mean (max x − x_top) = {np.mean(xdiff):+.4f} (≈ the mania drift g)")
    return R


def block_R19(paths: dict, pilots: dict, out) -> Rows:
    """Item 50: burn-in adequacy per engine."""
    R = Rows("R19_burn_in")
    for key, eng in (("flat", "fw_single (live)"), ("flat_fw_index", "fw_index"), ("flat_pruna", "pruna")):
        x1 = [float(r.x[0, bench(r)][0]) for r in paths[key]]
        sd1 = float(np.std(x1)); lo, hi, sd = boot(lambda c: float(np.std(c)), x1)
        pk = {"flat": "live_200k_e017_engine_9001", "flat_fw_index": "index_200k_engine", "flat_pruna": "pruna_200k_engine"}[key]
        pil = pilots[pk]; ratio = sd1 / pil["sd_x"]; hl = pil["half_life"]
        rv = 0.6 if key == "flat_fw_index" else None
        R.add(50, f"{eng}: sd of x on day 1 across seeds / long-run sd (200k pilot)", ratio, len(x1), (lo / pil["sd_x"], hi / pil["sd_x"]), rv, "C §A.9 (fw_index ≈ 0.6 σ_stat)" if rv else "",
              verdict_R(ratio, lo / pil["sd_x"], hi / pil["sd_x"], rv) if rv else "D", note=f"sd(x_1) {sd1:.4f}; pilot sd {pil['sd_x']:.4f}, pilot half-life {hl:.0f} d; burn-in 260 d = {260 / hl:.2f} half-lives")
    return R


def block_R20(paths: dict, envs_multi: list, out) -> Rows:
    """Item 58: multi-asset structure."""
    R = Rows("R20_multi_asset")
    corrs = []; spreads = []
    for r in paths["multi"]:
        m = bench(r); X = r.x[:, m]
        c = np.corrcoef(X); corrs.append(float(np.mean(c[np.triu_indices(3, 1)])))
        spreads.append(float(np.mean((X.max(axis=0) - X.min(axis=0)) >= THETA)))
    mc = float(np.mean(corrs)); lo, hi, sd = boot(lambda c: float(np.mean(c)), corrs)
    R.add(58, "3-asset crash: mean pairwise correlation of x across assets", mc, len(corrs), (lo, hi), 0.55, "C §G.41: 0.46–0.65 (10 seeds)", "R" if 0.46 <= mc <= 0.65 or lo <= 0.55 <= hi else "N", note=f"min/max over pairs of the seed means: {min(corrs):.2f}–{max(corrs):.2f}")
    ms = float(np.mean(spreads)); lo2, hi2, sd2 = boot(lambda c: float(np.mean(c)), spreads)
    R.add(58, "3-asset crash: spread-resolvable share (max x − min x >= 0.05)", ms, len(spreads), (lo2, hi2), 0.87, "C §G.41", verdict_R(ms, lo2, hi2, 0.87, 50, 10, sd2), rev_n=10)
    ratios = {0: [], 2: []}
    for e in envs_multi:
        for a in (0, 2):
            d = e["data"][e["data"]["asset"] == a]; P = d["price"].to_numpy(float); iv = d["implied_volatility"].to_numpy(float)
            r = np.diff(np.log(P)); rv = np.array([np.std(r[i:i + 21]) * math.sqrt(252) * 100 for i in range(len(r) - 21)])
            ratios[a].append(float(np.mean(iv[:len(rv)]) / np.mean(rv)))
    for a, rv in ((0, 1.28), (2, 1.06)):
        m_ = float(np.mean(ratios[a])); lo3, hi3, sd3 = boot(lambda c: float(np.mean(c)), ratios[a])
        R.add(58, f"3-asset crash: mean IV / realised-21-day-vol ratio, asset {a}", m_, len(ratios[a]), (lo3, hi3), rv, "C §G.41 (10 seeds)", verdict_R(m_, lo3, hi3, rv, 50, 10, sd3), rev_n=10)
    return R


def block_R21(out) -> Rows:
    """Item 39: footer counts vs CSV counts."""
    R = Rows("R21_footers")
    files = ["checklist_v2"] + [f"checklist_v2_sens_{k}" for k in ("fw_index", "pruna", "hl60", "omega_mode", "panic3", "panic6")]
    rev = {"checklist_v2": (8, 7), "checklist_v2_sens_fw_index": (7, 6), "checklist_v2_sens_pruna": (6, 7), "checklist_v2_sens_hl60": (7, 8), "checklist_v2_sens_omega_mode": (6, 7), "checklist_v2_sens_panic3": (8, 5), "checklist_v2_sens_panic6": (7, 6)}
    detail = {}
    for f in files:
        df = pd.read_csv(os.path.join(GEN_DIR, f + ".csv"))
        vals = df["pass"].map(lambda v: None if pd.isna(v) else (str(v) == "True")).tolist()
        n_pass = sum(1 for v in vals if v is True); n_fail = sum(1 for v in vals if v is False)
        md = open(os.path.join(GEN_DIR, f + ".md"), encoding="utf-8").read()
        m = re.search(r"\*\*Pass (\d+) / fail (\d+) / not applicable (\d+)\.\*\*", md)
        foot = (int(m.group(1)), int(m.group(2))) if m else None
        detail[f] = {"csv": (n_pass, n_fail), "footer": foot}
        R.add(39, f"{f}: CSV pass/fail vs .md footer", f"CSV {n_pass}/{n_fail}; footer {foot[0]}/{foot[1]}" if foot else f"CSV {n_pass}/{n_fail}; footer missing", len(df), None,
              f"footer {rev[f][0]}/{rev[f][1]}", "W 39 / LOG §5", "R" if foot == rev[f] else "N", note="footer wrong" if foot != (n_pass, n_fail) else "footer correct")
    R.detail = detail
    return R


def block_R22(out) -> Rows:
    """Items 30, 44, 61: the n behind the published numbers (documentary, read from the generated files)."""
    R = Rows("R22_n_table")
    ck = pd.read_csv(os.path.join(GEN_DIR, "checklist_v2.csv"))
    for _, r in ck.iterrows():
        if int(r["n_seeds"]) not in (470, 100, 150, 200, 50):
            R.add(30, f"checklist item {int(r['item'])}: n behind the published statistic", int(r["n_seeds"]), int(r["n_seeds"]), None, "'50 seeds per scenario'", "slide 2 / script", "D", note=str(r["property"]))
    hz = json.load(open(os.path.join(ROOT, "envs", "v2", "params", "hazard.json"), encoding="utf-8"))
    R.add(30, "hazard calibration seeds", hz["seeds"], hz["seeds"], None, "'50 seeds'", "", "D")
    md = open(os.path.join(GEN_DIR, "leakage_audit_v2.md"), encoding="utf-8").read()
    m = re.search(r"; (\d+) steps", md)
    R.add(30, "leakage audit (50 seeds -> 400 paths -> MAX_ROWS subsample): steps audited", int(m.group(1)) if m else None, 0, None, "'50 seeds'", "leakage_audit_v2.md", "D", note="150 of 400 paths (evaluation/leakage_audit.py MAX_ROWS = 30000); L2 rows after lag dropping: 27,000")
    R.add(30, "L5 observables oracle: training / evaluation seeds", "12 / 10", 10, None, "'50 seeds'", "l5_observables_oracle.md", "D")
    R.add(30, "generator sensitivities: seeds per scenario", 25, 25, None, "'50 seeds'", "checklist_v2_sens_*.md preambles", "D")
    R.add(44, "pilot scenarios", "flat, bull_trap, crash δ 0.70 (3)", 48, None, "'the four scenarios' (script slide 26)", "PILOT_NOTES.md", "D")
    return R


def block_R23(out) -> Rows:
    """Items 71, 72: stale statements located."""
    R = Rows("R23_stale_statements")
    pats = [(r"60-120", "half-life 60–120 d"), (r"\b120 d\b", "half-life 120 d"), (r"~90", "half-life ~90 d"), (r"\b18[78]\b", "half-life 187/188 d"),
            (r"'sustained-bull': 0\.25|sustained-bull 0\.25|sustained-bull\s+0\.25\)", "sustained-bull multiplier 0.25"), (r"jump_rate 0\.008|0\.008/day|jump_rate': 0\.008", "jump rate 0.008"),
            (r"four scenarios", "four scenarios"), (r"~72 d|72 d realised|72 days|70-day realised|70 days realised|about 70 days", "realised half-life 72/70 d")]
    files = ["docs/env_v2/spec/E1_V2_GENERATOR_SPEC.md", "docs/env_v2/spec/CALIBRATION_REPORT.md", "docs/env_v2/decisions/DECISION_LOG.md", "docs/env_v2/status/E1_E4_STATUS.md",
             "docs/env_v2/status/PILOT_NOTES.md", "docs/env_v2/generated/e1_calibration_variants.md", "envs/v2/mispricing.py", "envs/v2/garch.py", "envs/v2/events.py", "envs/synthetic_market.py",
             "docs/env_v2/slides/SPEAKER_SCRIPT.md", "tools/build_slides.py"]
    hits = []
    for f in files:
        p = os.path.join(ROOT, f)
        if not os.path.exists(p): continue
        for i, line in enumerate(open(p, encoding="utf-8", errors="replace").read().splitlines(), 1):
            for pat, lab in pats:
                if re.search(pat, line):
                    hits.append({"file": f, "line": i, "what": lab, "text": line.strip()[:160]})
    R.detail = {"hits": hits}
    R.add(71, "stale statements found (file:line list in the JSON detail and the report)", len(hits), len(hits), None, None, "W 71, 72", "D")
    return R


# ----------------------------------------------------------------------------------------------------
# generation orchestration
# ----------------------------------------------------------------------------------------------------
def generate_all(seeds: dict, workers: int, fast: bool):
    S = seeds["S200"]; jobs = {}
    def add(key, kws):
        jobs[key] = kws
    add("flat", [dict(scenario="flat", seed=s) for s in S])
    add("flat_nojump", [dict(scenario="flat", seed=s, jumps=False) for s in S])
    add("flat_meanzero", [dict(scenario="flat", seed=s, jump_mean=0.0) for s in S])
    add("bull_trap", [dict(scenario="bull_trap", seed=s) for s in S])
    add("bull_uncapped", [dict(scenario="bull_trap", seed=s, g_max=1.0, reject=False) for s in S])
    add("bull_uncapped_rej", [dict(scenario="bull_trap", seed=s, g_max=1.0) for s in S])
    for d in (0.55, 0.70, 0.85):
        add(f"crash_{d}", [dict(scenario="crash", seed=s, delta=d) for s in S])
    add("sustained_bull", [dict(scenario="sustained_bull", seed=s) for s in S])
    add("sb_first", [dict(scenario="sustained_bull", seed=s, reject=False) for s in seeds["SSB50"]])
    add("sb_rej", [dict(scenario="sustained_bull", seed=s) for s in seeds["SSB50"]])
    mixed = []
    for i, s in enumerate(S):
        sc = ("crash", "bull_trap")[i % 2]
        mixed += [dict(scenario=sc, seed=s, ordering="event_first"), dict(scenario=sc, seed=s, ordering="setup_first"), dict(scenario="flat", seed=s)]
    add("mixed", mixed)
    add("flat_800", [dict(scenario="flat", seed=s, T=800) for s in seeds["S800"]])
    add("flat_5000", [dict(scenario="flat", seed=s, T=5000) for s in seeds["S5000"]])
    add("flat_5000_nojump", [dict(scenario="flat", seed=s, T=5000, jumps=False) for s in seeds["S5000"]])
    add("flat_fw_index", [dict(scenario="flat", seed=s, engine="fw_index") for s in S])
    add("flat_pruna", [dict(scenario="flat", seed=s, engine="pruna") for s in S])
    add("multi", [dict(scenario="crash", seed=s, delta=0.70, n_assets=3, asset_vol_scale=[1.0, 1.0, 0.5], rho_common=0.3) for s in seeds["SMULTI"]])
    paths = {}
    t0 = time.time()
    for key, kws in jobs.items():
        paths[key] = pmap(_path_job, kws, workers)
        print(f"  paths {key}: {len(kws)} done ({time.time() - t0:.0f} s)", flush=True)
    paths["crash"] = paths["crash_0.7"]
    return paths


def generate_envs(seeds: dict, workers: int):
    S = seeds["S200"]
    rng = np.random.default_rng(20000)
    envs_a, envs_b = {}, {}
    for sc in SCENARIOS4:
        kws_a, kws_b = [], []
        for s in S:
            base = dict(scenario=sc, n_days=200, seed=s, _label="a")
            if sc == "crash": base["crash_discount"] = 0.70
            kws_a.append(base)
            kws_b.append({**base, "_label": "b", "start_price": float(rng.uniform(20.0, 500.0))})
        envs_a[sc] = pmap(_env_job, kws_a, workers)
        envs_b[sc] = pmap(_env_job, kws_b, workers)
        print(f"  envs {sc}: {len(S)} anchored + {len(S)} random-start", flush=True)
    kws_m = [dict(scenario="crash", n_days=200, seed=s, crash_discount=0.70, n_assets=3, config={"asset_vol_scale": [1.0, 1.0, 0.5], "rho_common": 0.3}, _label="m") for s in seeds["SMULTI"]]
    envs_multi = pmap(_env_job, kws_m, workers)
    return envs_a, envs_b, envs_multi


def run_pilots(seeds: dict, workers: int):
    from envs.v2.mispricing import load_params, pilot_stats, FW_INDEX_2012, PRUNA_2016
    live = load_params("fw_single"); ps = pilot_stats(live, "fw_single")
    jobs = {}
    for s in seeds["SPILOT"]:
        for sd_e in (0.016, 0.017):
            tag = f"e{str(sd_e).replace('0.', '')}"
            jobs[f"live_200k_{tag}_engine_{s}"] = dict(params=asdict(live), engine="fw_single", n_steps=200_000, sd_e=sd_e, seed=s, w_norm=ps["w_bar"], burn=5000)
            jobs[f"live_200k_{tag}_raw_{s}"] = dict(params=asdict(live), engine="fw_single", n_steps=200_000, sd_e=sd_e, seed=s, w_norm=1.0, burn=5000)
    jobs["live_20k"] = dict(params=asdict(live), engine="fw_single", n_steps=20_000, sd_e=0.016, seed=12345, w_norm=1.0, burn=2000)
    jobs["index_scale100_20k"] = dict(params=asdict(FW_INDEX_2012), engine="fw_index", n_steps=20_000, sd_e=0.016, seed=12345, w_norm=1.0, burn=2000)
    jobs["index_scale1_20k"] = dict(params={**asdict(FW_INDEX_2012), "price_scale": 1.0, "name": "fw_index_scale1"}, engine="fw_index", n_steps=20_000, sd_e=0.016, seed=12345, w_norm=1.0, burn=2000)
    jobs["index_200k_engine"] = dict(params=asdict(FW_INDEX_2012), engine="fw_index", n_steps=200_000, sd_e=0.017, seed=9001, w_norm=pilot_stats(FW_INDEX_2012, "fw_index")["w_bar"], burn=5000)
    jobs["pruna_200k_engine"] = dict(params=asdict(PRUNA_2016), engine="pruna", n_steps=200_000, sd_e=0.017, seed=9001, w_norm=pilot_stats(PRUNA_2016, "pruna")["w_bar"], burn=5000)
    prof = pd.read_csv(os.path.join(GEN_DIR, "fw_J_profile.csv"))
    for ph in prof["phi"].tolist():
        jobs[f"profile_phi_{ph}"] = dict(params={**asdict(FW_INDEX_2012), "phi": float(ph), "name": f"profile_phi_{ph}"}, engine="fw_index", n_steps=20_000, sd_e=0.016, seed=12345, w_norm=1.0, burn=2000)
    keys = list(jobs); res = pmap(_pilot_job, [dict(jobs[k]) for k in keys], workers)
    return dict(zip(keys, res))


# ----------------------------------------------------------------------------------------------------
# report
# ----------------------------------------------------------------------------------------------------
def render(out_dir: str):
    blocks = []
    for p in sorted(glob.glob(os.path.join(out_dir, "findings", "*.json"))):
        blocks.append(json.load(open(p, encoding="utf-8")))
    before = [b for b in blocks if not b["tag"]]; after = {b["block"]: b for b in blocks if b["tag"] == "after"}
    L = ["# Phase 0 findings reproduction (v2.1)", "",
         "Every computational finding of the three v2 reviews recomputed on fresh seeds (PREREG_PHASE_0.md §1–3) on the "
         "**unmodified** v2.0 generator (`before`), with n, the 95 % interval and the reviewers' value beside mine. Verdicts: "
         "**R** reproduced (PREREG §3), **S** reproduced in substance, **N** not reproduced, **D** documentary. Intervals are "
         "percentile cluster bootstraps over paths unless the row says Wilson / IQR / min–max. Produced by "
         "`python -m tools.verify_v2_findings`; the per-block numbers are in `findings/*.json`.", ""]
    counts = {"R": 0, "S": 0, "N": 0, "D": 0}
    for b in before:
        for r in b["rows"]:
            counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    L += [f"Verdict counts over {sum(counts.values())} rows: " + ", ".join(f"{k} {v}" for k, v in counts.items()), ""]
    L += ["| Block | Item | Statistic | Mine | n | 95 % interval | Reviewer | Source | Verdict | Note |", "|---|---|---|---|---|---|---|---|---|---|"]
    for b in before:
        for r in b["rows"]:
            ci = r["ci"]
            ci_s = f"[{fmt(ci[0])}, {fmt(ci[1])}]" if ci and ci[0] is not None else "—"
            L.append(f"| {b['block']} | {r['item']} | {r['statistic']} | {fmt(r['mine'])} | {r['n']} | {ci_s} | {fmt(r['reviewer'])} | {r['rev_source']} | **{r['verdict']}** | {r['note']} |")
    if after:
        L += ["", "## Before / after the analyst-error fix (same seeds; only the analyst field changed)", "",
              "| Block | Statistic | Before | After |", "|---|---|---|---|"]
        for name, ab in after.items():
            bef = {r["statistic"]: r for b in before if b["block"] == name for r in b["rows"]}
            for r in ab["rows"]:
                if r["statistic"] in bef:
                    L.append(f"| {name} | {r['statistic']} | {fmt(bef[r['statistic']]['mine'])} | {fmt(r['mine'])} |")
    # details worth printing
    for b in before:
        if b["block"] == "R23_stale_statements":
            L += ["", "## Stale statements located (items 71, 72, 44)", "", "| File | Line | What | Text |", "|---|---|---|---|"]
            for h in b["detail"]["hits"]:
                L.append(f"| {h['file']} | {h['line']} | {h['what']} | {h['text'].replace('|', '\\|')} |")
        if b["block"] == "R13_half_life":
            t = b["detail"]["ar1_table"]
            L += ["", "## Pure AR(1) estimator table (200 Gaussian paths per cell; sample half-life from ACF(1))", "", "| true half-life | T | median | 5–95 % | share >= 60 d |", "|---|---|---|---|---|"]
            for k, v in t.items():
                hl, T = k.replace("hl", "").split("_T")
                L.append(f"| {hl} | {T} | {v['median']:.0f} | {v['p5']:.0f}–{v['p95']:.0f} | {v['share_ge_60']:.2f} |")
        if b["block"] == "R3_attackers":
            L += ["", "## Attacker table (GBT, GroupKFold by path; 200 paths per panel)", "", "| Panel | Features | Group | R²(x) [CI] | sign acc [CI] | MAPE(V) [CI] | rows |", "|---|---|---|---|---|---|---|"]
            for panel, tab in b["detail"]["tables"].items():
                for fs, cells in tab.items():
                    for grp in ("calm", "event", "all"):
                        c = cells[grp]
                        L.append(f"| {panel} | {fs} ({cells['n_features']}) | {grp} | {c['R2_x']:.3f} [{c['R2_ci'][0]:.3f}, {c['R2_ci'][1]:.3f}] | {c['sign_acc']:.3f} [{c['sign_ci'][0]:.3f}, {c['sign_ci'][1]:.3f}] | {c['MAPE_V']:.3f} [{c['MAPE_ci'][0]:.3f}, {c['MAPE_ci'][1]:.3f}] | {c['n_rows']} |")
            if "R3_attackers" in after:
                L += ["", "After the analyst fix (full feature set only changes):", "", "| Panel | Features | Group | R²(x) | sign acc | MAPE(V) |", "|---|---|---|---|---|---|"]
                for panel, tab in after["R3_attackers"]["detail"]["tables"].items():
                    for fs, cells in tab.items():
                        for grp in ("calm", "event", "all"):
                            c = cells[grp]
                            L.append(f"| {panel} | {fs} | {grp} | {c['R2_x']:.3f} | {c['sign_acc']:.3f} | {c['MAPE_V']:.3f} |")
    with open(os.path.join(out_dir, "findings_reproduction.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("written", os.path.join(out_dir, "findings_reproduction.md"))
    # canonical numbers for the documents / tests
    num = {}
    for b in before + list(after.values()):
        if b["block"] == "R13_half_life" and not b["tag"]:
            d = b["detail"]; num.update({"pull_rate_half_life_days": d["pull_hl"], "phi_live": d["phi"], "n_bar_20k": d["n_bar"], "w_bar_20k": d["w_bar"],
                                          "sd_x_engine_200k_e016": d["sd_engine_016"], "sd_x_engine_200k_e017": d["sd_engine_017"], "sd_x_raw_200k_e016": d["sd_raw_016"], "sd_x_raw_200k_e017": d["sd_raw_017"]})
            hls = [v["half_life"] for k, v in d["pilots"].items() if k.startswith("live_200k_e017_engine_")]
            if hls: num.update({"long_pilot_half_life_mean": float(np.mean(hls)), "long_pilot_half_life_min": float(min(hls)), "long_pilot_half_life_max": float(max(hls))})
            for r in b["rows"]:
                if r["statistic"].startswith("S200:"): num["sample_half_life_T200_median"] = r["mine"]
                if r["statistic"].startswith("S800:"): num["sample_half_life_T800_median"] = r["mine"]
        if b["block"] == "R10_analyst":
            key = "analyst_sd_bench_after" if b["tag"] else "analyst_sd_bench_before"
            num[key] = b["detail"]["sd_bench"]; num[key.replace("sd_bench", "median_ape")] = b["detail"]["median_ape"]
        if b["block"] == "R21_footers" and not b["tag"]:
            num["sensitivity_counts_csv"] = {k: v["csv"] for k, v in b["detail"].items()}
    num.update({"sustained_bull_variance_multiplier": 1.0, "jump_rate": 0.010, "jump_mean": -0.04, "jump_sd": 0.03, "analyst_sd_documented": 0.15, "analyst_rho": 0.95,
                "hazard_h0": 0.0003, "hazard_b": 6.0, "g_max": 0.012, "pilot_scenarios": 3, "pilot_runs": 48, "burn_in": 260})
    with open(os.path.join(out_dir, "phase0_numbers.json"), "w", encoding="utf-8") as fh:
        json.dump(num, fh, indent=1, default=_js)
    print("written", os.path.join(out_dir, "phase0_numbers.json"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--fast", action="store_true", help="6 seeds per block (code dry run only; not the pre-registered run)")
    ap.add_argument("--only", default=None, help="comma-separated block ids, e.g. R3,R5,R10")
    ap.add_argument("--tag", default="", help="suffix for the JSON blocks (e.g. 'after')")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--render", action="store_true", help="only rebuild the markdown from the stored blocks")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.render:
        render(a.out); return
    seeds = {k: (v[:6] if a.fast and k != "SPILOT" else v) for k, v in SEEDS.items()}
    if a.fast:
        seeds["SPILOT"] = SEEDS["SPILOT"][:2]
    only = set(a.only.split(",")) if a.only else None
    want = lambda b: (only is None) or (b in only)
    try:
        from threadpoolctl import threadpool_limits
        threadpool_limits(limits=a.workers)
    except Exception:
        pass
    t0 = time.time()
    need_paths = any(want(b) for b in ("R2", "R4", "R6", "R7", "R8", "R9", "R13", "R14", "R15", "R17", "R18", "R19", "R20"))
    need_envs = any(want(b) for b in ("R1", "R3", "R5", "R10", "R11", "R16", "R20"))
    need_pilots = any(want(b) for b in ("R2", "R12", "R13", "R19"))
    paths = generate_all(seeds, a.workers, a.fast) if need_paths else {}
    envs_a = envs_b = None; envs_multi = []
    if need_envs:
        envs_a, envs_b, envs_multi = generate_envs(seeds, a.workers)
    pilots = run_pilots(seeds, a.workers) if need_pilots else {}
    print(f"generation done in {time.time() - t0:.0f} s", flush=True)
    blocks = []
    def run(bid, fn):
        if not want(bid): return
        t = time.time(); Rb = fn(); p = Rb.save(a.out, a.tag); blocks.append(Rb)
        print(f"  [{bid}] {Rb.block}: {len(Rb.rows)} rows -> {p} ({time.time() - t:.0f} s)", flush=True)
    run("R1", lambda: block_R1(envs_a, a.out))
    run("R2", lambda: block_R2(paths, pilots, a.out))
    run("R3", lambda: block_R3(envs_a, envs_b, a.out, 100 if a.fast else 500))
    run("R4", lambda: block_R4(paths, a.out))
    run("R5", lambda: block_R5(envs_a, a.out))
    run("R6", lambda: block_R6(paths, a.out))
    run("R7", lambda: block_R7(paths, a.out))
    run("R8", lambda: block_R8(paths, a.out))
    run("R9", lambda: block_R9(paths, a.out))
    run("R10", lambda: block_R10(envs_a, a.out, seeds["SANALYST"]))
    run("R11", lambda: block_R11(envs_a, a.out))
    run("R12", lambda: block_R12(pilots, a.out))
    run("R13", lambda: block_R13(paths, pilots, a.out))
    run("R14", lambda: block_R14(paths, a.out))
    run("R15", lambda: block_R15(paths, a.out))
    run("R16", lambda: block_R16(envs_a, a.out))
    run("R17", lambda: block_R17(paths, a.out))
    run("R18", lambda: block_R18(paths, a.out))
    run("R19", lambda: block_R19(paths, pilots, a.out))
    run("R20", lambda: block_R20(paths, envs_multi, a.out))
    run("R21", lambda: block_R21(a.out))
    run("R22", lambda: block_R22(a.out))
    run("R23", lambda: block_R23(a.out))
    render(a.out)
    print(f"total {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
