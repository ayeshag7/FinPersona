"""
v2.1 Phase 6 -- 16A, the go/no-go checkpoint, computed exactly as written (plan Section 16A; PREREG_PHASE_6.md 12).

    python -m tools.phase6.e6_16a --out docs/env_v2/generated/v2_1/e6_16a [--scored 100 --train 40 --workers 24]

Policies, per persona (ISFJ / INTJ / ENTJ) x scenario x scored seed, all on the same price path with PortfolioV2, the
persona's band centre as the start allocation, the 5 bp cost tier:
  * the mandate-conditional true-V oracle (`baselines_v2`, unchanged)
  * the LEVEL-FREE observables oracle: every rendered field except the level fields (price, SMA20, SMA50, MACD,
    MACD_signal) plus the level-free ratios (log P/SMA, MACD/P, returns), current day + a 20-day history, GBT trained
    on 40 disjoint seeds (the frozen `ObservablesOracle` machinery; only the feature keys and the lag depth differ,
    the n/m encoding is `e5_l5.OracleNM`'s)
  * the level-free PRICE-ONLY oracle (the same, on the level-free price features alone) -- G4(a)'s comparator
  * the best simple level-free rule from the pre-registered family {P vs SMA50 threshold, RSI14 thresholds, analyst
    vs price threshold}, each family's scale AND direction fitted on the training seeds (lowest mean MCR at theta =
    0.05 over personas and scenarios); the family with the lowest training MCR is "the best simple rule"
  * the trivial policies: always-hold at the centre, the constant band edges (lo, hi), random (10 seeds averaged),
    constant-mix at the centre (reported)
Metric: MCR at theta in {0.03, 0.05, 0.08, 0.12, 0.20} (0.05 the checkpoint, the rest sensitivities); the oracle's
target switches per run (G3) counted on the mandate-conditional oracle's target series.  Intervals: percentile
cluster bootstrap over scored seeds (the three personas share a path), 500 resamples.

G1  oracle < observables oracle < best trivial, non-overlapping adjacent 95 % intervals, every scenario
G2  best simple rule > observables oracle, non-overlapping, in >= 3 of 4 scenarios
G3  median oracle switches >= 2 in the three event scenarios AND share of runs with >= 2 switches >= 0.5
G4a level-free observables oracle < level-free price-only oracle, non-overlapping, every scenario
G4b PREREG 7.3 (read from e6_6/bound.json: the ladder's rung 7 against bound + allowance)
Output: <out>/runs.csv (every run), <out>/16A.{json,md}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

from envs.synthetic_market import SyntheticMarketEnv, CANONICAL_FIELDS  # noqa: E402
from evaluation.observables_oracle import ObservablesOracle, LEVEL_FREE_KEYS  # noqa: E402
from evaluation.leakage_audit import add_lags_and_returns, add_level_free_columns  # noqa: E402
from evaluation.baselines_v2 import _run_policy, run_baselines  # noqa: E402
from evaluation.metrics_v2 import score_run, oracle_target  # noqa: E402
from evaluation.targets import band, centre  # noqa: E402
from tools.phase5.common import GEN, encode_nm, pin_state  # noqa: E402

THETAS = (0.03, 0.05, 0.08, 0.12, 0.20)
THETA0 = 0.05
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
SCENARIOS = ("flat", "bull_trap", "crash", "sustained_bull")
LEVEL_FIELDS = ("price", "SMA20", "SMA50", "MACD", "MACD_signal")
N_LAGS_16A = 20
N_BOOT = 500
TRAIN_SEED0 = 500
GRID = (0.01, 0.02, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20)
RSI_GRID = ((30, 70), (35, 65), (40, 60), (25, 75), (20, 80))


# ------------------------------------------------------------------------------------------ the oracles
class Oracle16A(ObservablesOracle):
    """The frozen oracle with (i) the n/m encoding of e5_l5.OracleNM, (ii) a 20-day history, (iii) the two level-free
    feature sets 16A names: 'full_level_free' (every non-level field + the level-free ratios) and 'level_free' (the
    price features alone).  fit() and predict_x() are the parent's with those three changes only."""

    def __init__(self, feature_set: str, n_lags: int = N_LAGS_16A, **k):
        base_fs = "level_free" if feature_set in ("level_free", "full_level_free") else feature_set
        super().__init__(feature_set=base_fs, **k)
        self.feature_set_16a = feature_set
        self.n_lags = n_lags
        if feature_set == "full_level_free":
            self.keys = [x for x in CANONICAL_FIELDS if x != "date" and x not in LEVEL_FIELDS] + ["reported_PE_nm"] + list(LEVEL_FREE_KEYS)
        elif feature_set == "level_free":
            self.keys = list(LEVEL_FREE_KEYS)

    def _panel(self, seeds):
        return encode_nm(super()._panel(seeds))

    def fit(self):
        from sklearn.ensemble import HistGradientBoostingRegressor
        from sklearn.model_selection import GroupKFold
        panel = add_level_free_columns(self._panel(self.train_seeds))
        if "reported_PE_nm" not in panel:
            panel["reported_PE_nm"] = 0.0
        dfl, cols = add_lags_and_returns(panel, [k for k in self.keys if k in panel.columns], n_lags=self.n_lags)
        dfl = dfl.dropna(subset=cols).reset_index(drop=True)
        self.cols = cols
        X = dfl[cols].to_numpy(dtype=float); y = dfl["x"].to_numpy(dtype=float)
        groups = (dfl["scenario"].astype(str) + "-" + dfl["seed"].astype(str)).to_numpy(dtype=object)
        pred = np.full(len(y), np.nan)
        for tr, te in GroupKFold(n_splits=5).split(X, y, groups):
            m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, max_depth=6, random_state=0).fit(X[tr], y[tr])
            pred[te] = m.predict(X[te])
        pg = dfl["macro"].replace({"down-event": "event", "up-event": "event"}).to_numpy(dtype=object)
        for g in ("calm", "event", "resolution"):
            mk = pg == g
            if mk.sum() > 30:
                ss = ((y[mk] - y[mk].mean()) ** 2).sum(); res = mk & (np.abs(y) >= self.theta)
                self.oos[g] = {"R2": float(1 - ((y[mk] - pred[mk]) ** 2).sum() / ss) if ss > 0 else np.nan,
                               "sign_acc": float(np.mean(np.sign(pred[res]) == np.sign(y[res]))) if res.any() else np.nan}
        self.model = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, max_depth=6, random_state=0).fit(X, y)
        return self

    def predict_x(self, env):
        assert env.seed not in self.train_seeds, "held-out seed required"
        d = env.data[env.data["asset"] == 0].copy()
        rows = []
        env.reset()
        for t in range(env.n_days):
            o = env.get_observation()
            row = {k: float(v) for k, v in o.items() if k != "date" and not isinstance(v, (list, str))}
            if o.get("reported_PE") == "n/m":
                row["reported_PE"] = np.nan
            rows.append(row); env.step()
        env.reset()
        f = pd.DataFrame(rows); f["scenario"] = env.scenario; f["seed"] = env.seed; f["day"] = np.arange(1, len(f) + 1)
        f["P"] = d["price"].values; f["V"] = d["fundamental_value"].values; f["x"] = d["x"].values
        f = add_level_free_columns(encode_nm(f))
        if "reported_PE_nm" not in f:
            f["reported_PE_nm"] = 0.0
        fl, cols = add_lags_and_returns(f, [k for k in self.keys if k in f.columns], n_lags=self.n_lags)
        X = fl[self.cols].to_numpy(dtype=float)
        ok = ~np.isnan(X).any(axis=1)
        xh = np.zeros(len(fl)); xh[ok] = self.model.predict(X[ok])
        return xh


# ------------------------------------------------------------------------------------------ the simple rules
def rule_policy(family: str, scale, direction: int, persona: str):
    """A level-free two-line rule: signal s_t from one shown quantity; cash -> band low when the rule says
    'undervalued', band high when 'overvalued', unchanged otherwise.  direction = +1 reads a HIGH signal as
    overvalued (mean reversion), -1 the opposite (momentum); both are candidates, the training seeds decide."""
    lo, hi = band(persona)

    def sig(r):
        if family == "p_sma50":
            return float(np.log(max(r["price"], 1e-9) / max(r["SMA50"], 1e-9)))
        if family == "rsi":
            return float(r["RSI14"])
        if family == "analyst":
            F = r.get("analyst_fair_value", np.nan)
            return float(np.log(max(r["price"], 1e-9) / max(F, 1e-9))) if np.isfinite(F) and F > 0 else 0.0
        raise ValueError(family)

    def pol(t, r, st, s):
        v = sig(r)
        if family == "rsi":
            over = v > scale[1] if direction > 0 else v < scale[0]
            under = v < scale[0] if direction > 0 else v > scale[1]
        else:
            over = v > scale if direction > 0 else v < -scale
            under = v < -scale if direction > 0 else v > scale
        return hi if over else (lo if under else min(max(st["cash_share"], lo), hi))
    return pol


def _mcr(df: pd.DataFrame, persona: str, theta: float) -> float:
    C = df["Cash_Share"].to_numpy(float); x = df["x"].to_numpy(float)
    res = np.abs(x) >= theta
    if not res.any():
        return np.nan
    c_star = oracle_target(x, theta, persona, prev_target=C[0])
    return float(np.mean(np.abs(C[res] - c_star[res])))


def _switches(x: np.ndarray, theta: float, persona: str, c0: float) -> int:
    tgt = oracle_target(x, theta, persona, prev_target=c0)
    return int(np.sum(np.diff(tgt) != 0))


# ------------------------------------------------------------------------------------------ one seed
_ORACLES: Dict = {}


def _init_worker(oracle_paths):
    import pickle, warnings
    warnings.filterwarnings("ignore")
    os.environ["OMP_NUM_THREADS"] = "1"
    for k, p in oracle_paths.items():
        with open(p, "rb") as fh:
            _ORACLES[k] = pickle.load(fh)


def _score_seed(args):
    sc, s, rules, T = args
    env = SyntheticMarketEnv(sc, T, s)
    d = env.data[env.data["asset"] == 0].reset_index(drop=True)
    x = d["x"].to_numpy(float)
    xh = {k: o.predict_x(env) for k, o in _ORACLES.items()}
    rows = []
    for persona in PERSONAS:
        c0 = centre(persona); lo, hi = band(persona)
        trajs = run_baselines(env, persona, c0, random_seeds=10)
        pol = {"oracle": trajs["mandate_conditional_oracle"], "always_hold": trajs["always_hold"], "constant_mix": trajs["constant_mix"],
               "band_lo": _run_policy(env, c0, lambda t, r, st, s_, lo=lo: lo), "band_hi": _run_policy(env, c0, lambda t, r, st, s_, hi=hi: hi)}
        rand = [trajs[k] for k in trajs if k.startswith("random_")]
        for k, o in _ORACLES.items():
            targets = o.policy(persona, xh[k], c0)
            pol[f"L5_{k}"] = _run_policy(env, c0, lambda t, r, st, s_, tg=targets: float(tg[t]))
        for fam, (scale, direction) in rules.items():
            pol[f"rule_{fam}"] = _run_policy(env, c0, rule_policy(fam, scale, direction, persona))
        for name, df in pol.items():
            row = {"scenario": sc, "seed": s, "persona": persona, "policy": name}
            for th in THETAS:
                row[f"mcr_{th}"] = _mcr(df, persona, th)
            rows.append(row)
        rr = {"scenario": sc, "seed": s, "persona": persona, "policy": "random"}
        for th in THETAS:
            rr[f"mcr_{th}"] = float(np.nanmean([_mcr(df, persona, th) for df in rand]))
        rows.append(rr)
        sw = {"scenario": sc, "seed": s, "persona": persona, "policy": "oracle_switches"}
        for th in THETAS:
            sw[f"mcr_{th}"] = float(_switches(x, th, persona, c0))
        rows.append(sw)
    return rows


# ------------------------------------------------------------------------------------------ rule fitting
def fit_rules(train_seeds: List[int], T: int) -> Dict:
    """One scale and direction per family, the lowest mean MCR (theta 0.05) over personas and scenarios on the
    training seeds; and which family is best."""
    envs = [SyntheticMarketEnv(sc, T, s) for sc in SCENARIOS for s in train_seeds]
    out = {}
    for fam in ("p_sma50", "rsi", "analyst"):
        best = None
        grid = RSI_GRID if fam == "rsi" else GRID
        for scale in grid:
            for direction in (+1, -1):
                vals = []
                for env in envs:
                    for persona in PERSONAS:
                        df = _run_policy(env, centre(persona), rule_policy(fam, scale, direction, persona))
                        vals.append(_mcr(df, persona, THETA0))
                m = float(np.nanmean(vals))
                if best is None or m < best[0]:
                    best = (m, scale, direction)
        out[fam] = {"train_mcr": best[0], "scale": best[1], "direction": best[2]}
        print(f"  rule {fam}: scale {best[1]}, direction {best[2]:+d}, training MCR {best[0]:.4f}", flush=True)
    out["best_family"] = min(("p_sma50", "rsi", "analyst"), key=lambda f: out[f]["train_mcr"])
    return out


# ------------------------------------------------------------------------------------------ the checkpoint
def _boot_mean(v: np.ndarray, seeds: np.ndarray, n_boot: int, rng) -> tuple:
    us = np.unique(seeds)
    by = {u: v[seeds == u] for u in us}
    draws = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.choice(us, len(us))
        draws[b] = np.mean(np.concatenate([by[u] for u in pick]))
    return float(np.mean(v)), float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def evaluate(runs: pd.DataFrame, rules: Dict, n_boot: int = N_BOOT) -> Dict:
    rng = np.random.default_rng(616001)
    best_rule = f"rule_{rules['best_family']}"
    summ = {"policies": {}, "G": {}, "theta_sensitivity": {}}
    for th in THETAS:
        col = f"mcr_{th}"
        tab = {}
        for sc in SCENARIOS:
            g = runs[(runs.scenario == sc) & (runs.policy != "oracle_switches")]
            per = {}
            for pol, gg in g.groupby("policy"):
                v = gg[col].to_numpy(float); ok = np.isfinite(v)
                if ok.sum() < 3:               # a smoke run has 2 seeds x 3 personas; the registered run has 300 per cell
                    continue
                m, lo, hi = _boot_mean(v[ok], gg["seed"].to_numpy()[ok], n_boot, rng)
                per[pol] = {"mean": m, "ci95": [lo, hi], "n_runs": int(ok.sum()), "n_seeds": int(gg["seed"].nunique())}
            triv = min((k for k in ("always_hold", "band_lo", "band_hi", "random") if k in per), key=lambda k: per[k]["mean"])
            per["_best_trivial"] = triv
            tab[sc] = per
        summ["policies"][str(th)] = tab

    def sep(a, b):  # a's interval entirely below b's
        return a["ci95"][1] < b["ci95"][0]
    for th in THETAS:
        tab = summ["policies"][str(th)]
        G1 = {sc: bool(sep(t["oracle"], t["L5_full_level_free"]) and sep(t["L5_full_level_free"], t[t["_best_trivial"]])) for sc, t in tab.items()}
        G2 = {sc: bool(sep(t["L5_full_level_free"], t[best_rule])) for sc, t in tab.items()}
        G4a = {sc: bool(sep(t["L5_full_level_free"], t["L5_level_free"])) for sc, t in tab.items()}
        sw = runs[runs.policy == "oracle_switches"]
        G3 = {}
        for sc in SCENARIOS:
            v = sw[sw.scenario == sc][f"mcr_{th}"].to_numpy(float)
            G3[sc] = {"median_switches": float(np.median(v)), "share_ge2": float(np.mean(v >= 2)), "n_runs": int(len(v))}
        ev = [sc for sc in SCENARIOS if sc != "flat"]
        summ["G"][str(th)] = {
            "G1": {"per_scenario": G1, "pass": all(G1.values())},
            "G2": {"per_scenario": G2, "n_pass": sum(G2.values()), "pass": sum(G2.values()) >= 3, "best_rule": best_rule},
            "G3": {"per_scenario": G3, "pass": all(G3[sc]["median_switches"] >= 2 and G3[sc]["share_ge2"] >= 0.5 for sc in ev)},
            "G4a": {"per_scenario": G4a, "pass": all(G4a.values())}}
    # G4b from the bound file (PREREG 7.3)
    bp = os.path.join(GEN, "e6_6", "bound.json")
    if os.path.exists(bp):
        b = json.load(open(bp, encoding="utf-8"))
        rungs = {r["rung"]: r for r in b["ladder"]["rungs"]}
        allowance = rungs[4]["levelfree_R2"] - rungs[1]["levelfree_R2"]
        ceiling = rungs[7]["bound_window_avg"] + allowance
        summ["G4b"] = {"surrogate_R2": rungs[7]["levelfree_R2"], "ci95": rungs[7]["ci95"], "bound_window_avg": rungs[7]["bound_window_avg"],
                       "allowance_rung4_minus_rung1": allowance, "ceiling": ceiling, "pass": bool(rungs[7]["ci95"][0] <= ceiling),
                       "rule": "CI lower end <= bound (window average, realised s_x of the calm population) + allowance (E3.8 rung 4 - rung 1)"}
    return summ


def to_markdown(summ: Dict, rules: Dict, meta: Dict) -> str:
    L = [f"# 16A — the go/no-go checkpoint on the frozen generator (Phase 6)", "",
         f"{meta['scored']} scored seeds per scenario (seeds {meta['scored_seed0']}..), {meta['train']} training seeds ({TRAIN_SEED0}..) for the oracles "
         f"and the rules' scales; T = {meta['T']}; {N_BOOT}-resample cluster bootstrap over seeds; personas {', '.join(PERSONAS)}. "
         f"Checkpoint θ = {THETA0}; sensitivities at {', '.join(str(t) for t in THETAS if t != THETA0)}.", "",
         "## Rules fitted on the training seeds", "", "| family | scale | direction | training MCR |", "|---|---|---|---|"]
    for fam in ("p_sma50", "rsi", "analyst"):
        r = rules[fam]; L.append(f"| {fam} | {r['scale']} | {r['direction']:+d} | {r['train_mcr']:.4f} |")
    L += [f"\nBest simple rule: **{rules['best_family']}**.", ""]
    for th in THETAS:
        tab = summ["policies"][str(th)]; G = summ["G"][str(th)]
        L += [f"## θ = {th}" + (" — the checkpoint" if th == THETA0 else " (sensitivity)"), "",
              "| scenario | oracle | L5 level-free observables | L5 level-free price-only | best rule | best trivial | always-hold | random |",
              "|---|---|---|---|---|---|---|---|"]
        def f(p):
            return "—" if p is None else f"{p['mean']:.4f} [{p['ci95'][0]:.4f}, {p['ci95'][1]:.4f}]"
        for sc, t in tab.items():
            L.append(f"| {sc} | {f(t.get('oracle'))} | {f(t.get('L5_full_level_free'))} | {f(t.get('L5_level_free'))} | {f(t.get(G['G2']['best_rule']))} | "
                     f"{t['_best_trivial']}: {f(t.get(t['_best_trivial']))} | {f(t.get('always_hold'))} | {f(t.get('random'))} |")
        g3 = G["G3"]["per_scenario"]
        L += ["", "| gate | per scenario | verdict |", "|---|---|---|",
              f"| G1 oracle < observables < trivial (non-overlapping) | {G['G1']['per_scenario']} | **{'PASS' if G['G1']['pass'] else 'FAIL'}** |",
              f"| G2 best rule > observables oracle in ≥ 3 of 4 | {G['G2']['per_scenario']} ({G['G2']['n_pass']} of 4) | **{'PASS' if G['G2']['pass'] else 'FAIL'}** |",
              f"| G3 median oracle switches ≥ 2 and share ≥ 0.5 (event scenarios) | " + ", ".join(f"{sc}: median {v['median_switches']:.0f}, share {v['share_ge2']:.2f}" for sc, v in g3.items()) + f" | **{'PASS' if G['G3']['pass'] else 'FAIL'}** |",
              f"| G4a level-free observables < level-free price-only (non-overlapping) | {G['G4a']['per_scenario']} | **{'PASS' if G['G4a']['pass'] else 'FAIL'}** |", ""]
    if "G4b" in summ:
        g = summ["G4b"]
        L += ["## G4b — the price-only surrogate against the Appendix-B bound (PREREG 7.3)", "",
              f"level-free calm-trained R²(x) {g['surrogate_R2']:.4f} [{g['ci95'][0]:.4f}, {g['ci95'][1]:.4f}] vs bound {g['bound_window_avg']:.4f} + "
              f"allowance {g['allowance_rung4_minus_rung1']:.4f} = ceiling **{g['ceiling']:.4f}** → **{'PASS' if g['pass'] else 'FAIL'}** ({g['rule']}).", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(GEN, "e6_16a"))
    ap.add_argument("--scored", type=int, default=100)
    ap.add_argument("--scored-seed0", type=int, default=0)
    ap.add_argument("--train", type=int, default=40)
    ap.add_argument("--T", type=int, default=200)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    state = pin_state()
    t0 = time.time()
    train_seeds = list(range(TRAIN_SEED0, TRAIN_SEED0 + a.train))
    import pickle
    oracle_paths = {}
    for fs in ("full_level_free", "level_free"):
        p = os.path.join(a.out, f"oracle_{fs}.pkl")
        if not os.path.exists(p):
            print(f"[oracle] fitting {fs} on {a.train} seeds", flush=True)
            o = Oracle16A(fs, train_seeds=train_seeds, T=a.T).fit()
            with open(p, "wb") as fh:
                pickle.dump(o, fh)
            print(f"  oos: {o.oos}", flush=True)
        oracle_paths[fs] = p
    rp = os.path.join(a.out, "rules.json")
    if os.path.exists(rp):
        rules = json.load(open(rp, encoding="utf-8"))
    else:
        print("[rules] fitting the family on the training seeds", flush=True)
        rules = fit_rules(train_seeds, a.T)
        json.dump(rules, open(rp, "w", encoding="utf-8"), indent=1)
    rule_arg = {fam: (rules[fam]["scale"], rules[fam]["direction"]) for fam in ("p_sma50", "rsi", "analyst")}
    runs_p = os.path.join(a.out, "runs.csv")
    done = set()
    if os.path.exists(runs_p):
        prev = pd.read_csv(runs_p); done = set(zip(prev.scenario, prev.seed)); frames = [prev]
    else:
        frames = []
    jobs = [(sc, s, rule_arg, a.T) for sc in SCENARIOS for s in range(a.scored_seed0, a.scored_seed0 + a.scored) if (sc, s) not in done]
    print(f"[score] {len(jobs)} (scenario, seed) jobs on {a.workers} workers ({len(done)} done)", flush=True)
    with ProcessPoolExecutor(max_workers=a.workers, initializer=_init_worker, initargs=(oracle_paths,)) as ex:
        buf = []
        for i, rows in enumerate(ex.map(_score_seed, jobs, chunksize=2), 1):
            buf.extend(rows)
            if i % 20 == 0 or i == len(jobs):
                frames.append(pd.DataFrame(buf)); buf = []
                pd.concat(frames, ignore_index=True).to_csv(runs_p, index=False)
                print(f"  {i}/{len(jobs)} ({time.time() - t0:.0f} s)", flush=True)
    runs = pd.read_csv(runs_p)
    summ = evaluate(runs, rules)
    meta = {"scored": a.scored, "scored_seed0": a.scored_seed0, "train": a.train, "T": a.T, "state": state,
            "n_runs": int(len(runs)), "seconds": round(time.time() - t0), "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump({"meta": meta, "rules": rules, "summary": summ}, open(os.path.join(a.out, "16A.json"), "w", encoding="utf-8"), indent=1, default=float)
    md = to_markdown(summ, rules, meta)
    with open(os.path.join(a.out, "16A.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md + "\n")
    print(md[:3000]); print(f"-> {a.out} ({meta['seconds']} s)")


if __name__ == "__main__":
    main()
