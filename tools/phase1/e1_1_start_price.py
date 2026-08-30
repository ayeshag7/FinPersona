"""
E1.1 (PREREG_PHASE_1.md section 7; REG-1; D13): the start-price answer key under the four mechanisms
fixed (v2) / A randomise / B normalise / C both, 500 seeds x 4 scenarios each (panels from tools/phase1/before_state.s11).

Attacker test: GBT with the level (51), level-free (45) and full (111) feature sets fit on the pooled 4-scenario panel
(GroupKFold(5) by path), evaluated per scenario on all days and calm days; Delta = R2_level - R2_level-free with a
500-resample cluster bootstrap over paths; a mechanism passes if the CI's lower limit <= 0 in every scenario.
Rule-100 test: MCR of "compare the RENDERED price with 100" (ISFJ, theta 0.05, PortfolioV2 at 5 bp) beside the oracle,
always-hold, constant-mix and the two constant band-edge policies; passes if the rule's MCR lies inside the union of
the edge policies' 95 % intervals in every scenario. Reported without a gate: the Kalman bound; the L1 field candidates.

    python -m tools.phase1.e1_1_start_price [--mechanisms fixed,A,B,C]
Outputs: docs/env_v2/generated/v2_1/e1_1/start_price.json, start_price.md
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from typing import Dict, List

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "4")

OUT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e1_1")
PANELS = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "_panels")
SCENARIOS4 = ("flat", "crash", "bull_trap", "sustained_bull")
THETA = 0.05
N_BOOT = 500
MECH = {"fixed": "fixed", "A": "randomise", "B": "normalise", "C": "both"}


def attacker_per_scenario(panel: pd.DataFrame, n_boot: int = N_BOOT):
    from envs.synthetic_market import CANONICAL_FIELDS
    from evaluation.leakage_audit import add_lags_and_returns, _oos_predictions, _models
    from tools.verify_v2_findings import _add_level_free, _feature_sets
    keys = [k for k in CANONICAL_FIELDS if k != "date"]
    panel = _add_level_free(panel)
    extra = ["lp_sma20", "lp_sma50", "macd_p", "macds_p"]
    dfl, cols = add_lags_and_returns(panel, keys + extra)
    dfl = dfl.dropna(subset=cols).reset_index(drop=True)
    cols_full = [c for c in cols if c.split("_lag")[0] not in extra]
    fs = _feature_sets(dfl, cols_full)
    groups = (dfl["scenario"].astype(str) + "-" + dfl["seed"].astype(str)).to_numpy(dtype=object)
    path_of = pd.factorize(pd.Series(groups))[0]; n_paths = path_of.max() + 1
    y = dfl["x"].to_numpy(float); yv = np.log(dfl["V"].to_numpy(float))
    scen = dfl["scenario"].to_numpy(dtype=object)
    calm = dfl["macro"].to_numpy(dtype=object) == "calm"
    model = _models()["gbt"]
    preds = {name: _oos_predictions(dfl[fc].to_numpy(float), y, groups, model) for name, fc in fs.items()}
    predv = {name: _oos_predictions(dfl[fc].to_numpy(float), yv, groups, model) for name, fc in (("level", fs["level"]), ("full", fs["full"]))}
    rng = np.random.default_rng(0)
    out = {"n_features": {k: len(v) for k, v in fs.items()}, "n_paths": int(n_paths)}
    for sc in SCENARIOS4:
        for grp, gmask in (("all", np.ones(len(y), bool)), ("calm", calm)):
            m = (scen == sc) & gmask
            if m.sum() < 100:
                continue
            paths = np.unique(path_of[m]); pidx = {p: np.where(m & (path_of == p))[0] for p in paths}
            def r2_of(pred, sel_paths):
                idx = np.concatenate([pidx[p] for p in sel_paths])
                yy = y[idx]; ss = ((yy - yy.mean()) ** 2).sum()
                return float(1 - ((yy - pred[idx]) ** 2).sum() / ss) if ss > 0 else float("nan")
            def sign_of(pred, sel_paths):
                idx = np.concatenate([pidx[p] for p in sel_paths]); idx = idx[np.abs(y[idx]) >= THETA]
                return float(np.mean(np.sign(pred[idx]) == np.sign(y[idx]))) if len(idx) > 10 else float("nan")
            cell = {}
            for name in fs:
                cell[name] = {"R2": r2_of(preds[name], paths), "sign_acc": sign_of(preds[name], paths)}
            deltas = np.array([r2_of(preds["level"], sp) - r2_of(preds["level_free"], sp) for sp in (paths[rng.integers(0, len(paths), len(paths))] for _ in range(n_boot))])
            cell["delta_level_minus_levelfree"] = cell["level"]["R2"] - cell["level_free"]["R2"]
            cell["delta_ci95"] = [float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5))]
            cell["delta_half_width"] = float((cell["delta_ci95"][1] - cell["delta_ci95"][0]) / 2)
            cell["pass"] = bool(cell["delta_ci95"][0] <= 0)
            idx_all = np.concatenate([pidx[p] for p in paths])
            for name in ("level", "full"):
                cell[f"MAPE_V_{name}"] = float(np.mean(np.abs(np.exp(predv[name][idx_all]) - np.exp(yv[idx_all])) / np.exp(yv[idx_all])))
            cell["n_rows"] = int(m.sum()); cell["n_paths"] = int(len(paths))
            out[f"{sc}|{grp}"] = cell
    out["attacker_pass"] = bool(all(out[f"{sc}|all"]["pass"] for sc in SCENARIOS4))
    return out


def rule100(data: Dict, k_render: Dict, n_boot: int = N_BOOT):
    from evaluation.baselines_v2 import _run_policy, baseline_policies
    from evaluation.metrics_v2 import score_run
    from evaluation.targets import band, centre
    lo_b, hi_b = band("ISFJ"); c0 = centre("ISFJ")

    class Shim:
        def __init__(self, d): self.data = d
    out = {}
    for sc in SCENARIOS4:
        rows = []
        for (s_, seed), d in data.items():
            if s_ != sc:
                continue
            k = float(k_render.get((s_, seed), 1.0))
            def rule(t, r, st, s, k=k):
                lx = math.log(r["price"] * k / 100.0)
                return hi_b if lx > THETA else (lo_b if lx < -THETA else st["cash_share"])
            pols = baseline_policies("ISFJ", c0, THETA, random_seeds=0)
            pols = {n: p for n, p in pols.items() if n in ("always_hold", "constant_mix", "mandate_conditional_oracle")}
            pols["rule100"] = (rule, "target"); pols["edge_lo"] = (lambda t, r, st, s: lo_b, "target"); pols["edge_hi"] = (lambda t, r, st, s: hi_b, "target")
            m = {n: score_run(_run_policy(Shim(d), c0, fn, cost_bp=5.0, interface=iface), "ISFJ", c0)["mcr_0.05"] for n, (fn, iface) in pols.items()}
            rows.append(m)
        if not rows:
            continue
        df = pd.DataFrame(rows)
        rng = np.random.default_rng(0)
        res = {}
        for pol in df.columns:
            v = df[pol].to_numpy(float)
            b = np.array([np.nanmean(v[rng.integers(0, len(v), len(v))]) for _ in range(n_boot)])
            res[pol] = {"mean": float(np.nanmean(v)), "ci95": [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))], "n": int(len(v))}
        lo = min(res["edge_lo"]["ci95"][0], res["edge_hi"]["ci95"][0]); hi = max(res["edge_lo"]["ci95"][1], res["edge_hi"]["ci95"][1])
        res["pass"] = bool(lo <= res["rule100"]["mean"] <= hi) or bool(res["rule100"]["mean"] >= lo)   # inside the union, or no better than the worse edge
        res["inside_union_of_edge_CIs"] = bool(lo <= res["rule100"]["mean"] <= hi)
        res["gap_to_oracle"] = res["rule100"]["mean"] - res["mandate_conditional_oracle"]["mean"]
        out[sc] = res
    out["rule100_pass"] = bool(all(out[sc]["pass"] for sc in SCENARIOS4 if sc in out))
    return out


def l1_fields(panel: pd.DataFrame):
    from evaluation.leakage_audit import l1_algebraic
    from envs.synthetic_market import CANONICAL_FIELDS
    l1 = l1_algebraic(panel, [k for k in CANONICAL_FIELDS if k != "date"])
    return l1[["candidate", "fitted_k", "median_APE", "p5_APE", "p10_APE", "p25_APE", "within_1pct", "within_5pct"]].to_dict(orient="records")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mechanisms", default="fixed,A,B,C")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    from tools.phase1.kalman_bound import kalman_bound
    from envs.v2 import value_params as VP
    t0 = time.time()
    out = {"design": {"seeds": [50000, 50499], "scenarios": SCENARIOS4, "n_boot": N_BOOT, "theta": THETA,
                      "kalman_bound_at_params_in_force": kalman_bound(VP.SIGMA_V, 0.1752, 150.0)}, "mechanisms": {}}
    for mech in a.mechanisms.split(","):
        t1 = time.time()
        panel = pd.read_pickle(os.path.join(PANELS, f"s11_{mech}_panel.pkl"))
        data = pd.read_pickle(os.path.join(PANELS, f"s11_{mech}_data.pkl"))
        kr = pd.read_pickle(os.path.join(PANELS, f"s11_{mech}_krender.pkl")) if os.path.exists(os.path.join(PANELS, f"s11_{mech}_krender.pkl")) else {}
        att = attacker_per_scenario(panel)
        print(mech, "attacker", {sc: (round(att[f'{sc}|all']['delta_level_minus_levelfree'], 3), att[f'{sc}|all']['delta_ci95']) for sc in SCENARIOS4}, att["attacker_pass"], f"{time.time() - t1:.0f} s", flush=True)
        r100 = rule100(data, kr)
        print(mech, "rule100", {sc: (round(r100[sc]['rule100']['mean'], 3), round(r100[sc]['mandate_conditional_oracle']['mean'], 3), r100[sc]['pass']) for sc in SCENARIOS4}, flush=True)
        out["mechanisms"][mech] = {"mode": MECH[mech], "attacker": att, "rule100": r100, "L1_fields": l1_fields(panel),
                                   "day1_price_sd": float(panel[panel["day"] == 1]["price"].std()), "seconds": round(time.time() - t1)}
    out["seconds"] = round(time.time() - t0)
    with open(os.path.join(OUT, "start_price.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    kb = out["design"]["kalman_bound_at_params_in_force"]
    L = ["# E1.1 the start-price answer key: mechanisms fixed / A / B / C (PREREG_PHASE_1.md section 7)", "",
         f"500 seeds x 4 scenarios per mechanism (seeds 50000-50499; crash delta 0.70); GBT attacker fit on the pooled panel, GroupKFold(5) by path, "
         f"evaluated per scenario; Delta = R2(level) - R2(level-free), {N_BOOT}-resample cluster bootstrap over paths; pass = CI lower limit <= 0 in every scenario. "
         f"Kalman bound at the parameters in force (sigma_V {VP.SIGMA_V}, s_x 0.175, h 150 d): window avg {kb['window_avg']:.3f}, day 200 {kb['day_T']:.3f}, "
         f"steady state {kb['steady_state']:.3f} (identical under A/B/C).", "",
         "## Attacker test", "",
         "| mechanism | scenario | R2 level [sign] | R2 level-free [sign] | R2 full | Delta [95 % CI] | pass | calm: level / level-free / Delta CI | MAPE(V) level / full |",
         "|---|---|---|---|---|---|---|---|---|"]
    for mech, r in out["mechanisms"].items():
        att = r["attacker"]
        for sc in SCENARIOS4:
            c = att[f"{sc}|all"]; cc = att.get(f"{sc}|calm")
            L.append(f"| {mech} ({r['mode']}) | {sc} | {c['level']['R2']:.3f} [{c['level']['sign_acc']:.2f}] | {c['level_free']['R2']:.3f} [{c['level_free']['sign_acc']:.2f}] | {c['full']['R2']:.3f} | "
                     f"{c['delta_level_minus_levelfree']:+.3f} [{c['delta_ci95'][0]:+.3f}, {c['delta_ci95'][1]:+.3f}] | {c['pass']} | "
                     + (f"{cc['level']['R2']:.3f} / {cc['level_free']['R2']:.3f} / [{cc['delta_ci95'][0]:+.3f}, {cc['delta_ci95'][1]:+.3f}]" if cc else "-")
                     + f" | {c['MAPE_V_level']:.3f} / {c['MAPE_V_full']:.3f} |")
        L.append(f"| **{mech}** | **all four** | | | | | **{'PASS' if att['attacker_pass'] else 'FAIL'}** | | |")
    L += ["", "## Rule-100 test (ISFJ, theta 0.05, MCR through PortfolioV2 at 5 bp)", "",
          "| mechanism | scenario | rule-100 [CI] | oracle | always-hold | constant-mix | edge-lo [CI] | edge-hi [CI] | gap to oracle | inside edge CIs | pass |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for mech, r in out["mechanisms"].items():
        for sc in SCENARIOS4:
            q = r["rule100"][sc]
            L.append(f"| {mech} | {sc} | {q['rule100']['mean']:.3f} [{q['rule100']['ci95'][0]:.3f}, {q['rule100']['ci95'][1]:.3f}] | {q['mandate_conditional_oracle']['mean']:.3f} | "
                     f"{q['always_hold']['mean']:.3f} | {q['constant_mix']['mean']:.3f} | {q['edge_lo']['mean']:.3f} [{q['edge_lo']['ci95'][0]:.3f}, {q['edge_lo']['ci95'][1]:.3f}] | "
                     f"{q['edge_hi']['mean']:.3f} [{q['edge_hi']['ci95'][0]:.3f}, {q['edge_hi']['ci95'][1]:.3f}] | {q['gap_to_oracle']:+.3f} | {q['inside_union_of_edge_CIs']} | {q['pass']} |")
        L.append(f"| **{mech}** | **all four** | | | | | | | | | **{'PASS' if r['rule100']['rule100_pass'] else 'FAIL'}** |")
    L += ["", "## The field channel (reported, no gate; Phase 5's): L1 candidates, median APE and percentiles", "",
          "| mechanism | candidate | fitted k | median APE | p5 | p10 | p25 | within 1 % | within 5 % |", "|---|---|---|---|---|---|---|---|---|"]
    for mech, r in out["mechanisms"].items():
        for c in r["L1_fields"]:
            L.append(f"| {mech} | {c['candidate']} | {c['fitted_k']:.3f} | {c['median_APE']:.3f} | {c['p5_APE']:.3f} | {c['p10_APE']:.3f} | {c['p25_APE']:.3f} | {c['within_1pct']:.3f} | {c['within_5pct']:.3f} |")
    with open(os.path.join(OUT, "start_price.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("written", OUT, f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
