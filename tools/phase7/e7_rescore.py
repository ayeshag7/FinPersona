"""
v2.1 Phase 7 -- the re-scoring of the panel under every theta and both scorings (PREREG_PHASE_7.md 1.5, 2).

    python -u -m tools.phase7.e7_rescore --stages cells,theta_table

`cells`       Every (scenario, seed, persona, policy) cell of `e7_panel/` scored at every theta -- the plan's grid
              {0.03, 0.05, 0.08, 0.12, 0.20} plus the three derived values of E7.1 -- and at each half-width of
              E7.7's sensitivity {0.05, 0.10, 0.15}, under BOTH scorings: A, the decomposition (MCR = B + D on
              resolvable steps) and B, per-window (REG-12's pre-registered alternative).  One construction:
              `evaluation.scoring.regret_terms_batch`, proved equal to the per-run functions and to Phase 6's own
              MCR (`e7_panel/verify_vs_16a.json`, worst 1e-16 over 51,450 comparisons).

`theta_table` The headline table: every metric at every theta with percentile cluster-bootstrap 95 % intervals
              over SEEDS (500 resamples, the Phase-6 construction -- the three personas share a path).

Output: <out>/cells.parquet, <out>/theta_table.{csv,md}, <out>/meta.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

from tools.phase5.common import GEN, pin_state  # noqa: E402

OUT = os.path.join(GEN, "e7_rescore")
PANEL = os.path.join(GEN, "e7_panel")
E7_1 = os.path.join(GEN, "e7_1")
GRID = (0.03, 0.05, 0.08, 0.12, 0.20)
HALF_WIDTHS = (0.05, 0.10, 0.15)          # E7.7's DESIGN sensitivity; 0.10 is the value in force
HW_IN_FORCE = 0.10
N_BOOT = 500
# The policies whose headline rows the report quotes (16A's set); the scripted sweeps are E7.8's and are scored
# here too but summarised there.
HEADLINE = ("mandate_conditional_oracle", "L5_full_level_free", "L5_level_free", "rule_p_sma50", "rule_rsi",
            "rule_analyst", "always_hold", "band_lo", "band_hi", "random", "constant_mix",
            "always_buy", "always_sell", "buy_day1_hold", "momentum", "mean_reversion", "v_oracle")


def derived_thetas() -> dict:
    """The three derived values, read from E7.1's own result files (never re-derived here)."""
    out = {}
    tcv = os.path.join(E7_1, "theta_cost_var.json")
    if os.path.exists(tcv):
        d = json.load(open(tcv, encoding="utf-8"))
        out["theta_cost"] = float(d["theta_cost"]["value"])
        out["theta_cost_one_day"] = float(d["theta_cost"]["sensitivities"]["one_day_horizon"]["theta_cost"])
        out["theta_var"] = float(d["theta_var"]["value"])
        out["theta_var_stationary"] = float(d["theta_var"]["sensitivity_stationary_s_x"]["value"])
    ti = os.path.join(E7_1, "theta_info.json")
    if os.path.exists(ti):
        d = json.load(open(ti, encoding="utf-8"))
        for r in d["located"]:
            if r["scope"] == "pooled" and r["feature_set"] == "full" and r["theta_info"] is not None:
                out[f"theta_info_{r['population']}"] = float(r["theta_info"])
    return out


def theta_set(derived: dict):
    """The grid plus every derived value, de-duplicated and sorted, each with the labels that produced it."""
    labels: dict = {}
    for t in GRID:
        labels.setdefault(round(float(t), 6), []).append("grid")
    for k, v in derived.items():
        labels.setdefault(round(float(v), 6), []).append(k)
    return sorted(labels), labels


# -------------------------------------------------------------------------------------------------- stage: cells
def cells(out_dir: str, scenarios, thetas, labels, half_widths):
    from evaluation.scoring import regret_terms_batch
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()
    KEEP = ("mcr", "mcr_B", "mcr_D", "band_mas", "coverage", "n_resolvable", "oracle_switches",
            "share_target_lo", "share_target_hi", "share_agent_lo", "share_agent_hi", "share_agent_outside",
            "mcr_window", "mcr_window_B", "mcr_window_D", "window_switches", "n_windows_scored")
    frames = []
    for sc in scenarios:
        pp = os.path.join(PANEL, f"panel_{sc}.parquet")
        if not os.path.exists(pp):
            raise SystemExit(f"missing {pp}: run tools.phase7.e7_panel first")
        pan = pd.read_parquet(pp)
        paths = pd.read_parquet(os.path.join(PANEL, f"paths_{sc}.parquet"))
        pan["policy"] = pan["policy"].astype(str); pan["persona"] = pan["persona"].astype(str)
        xs = {int(s): g.sort_values("day")["x"].to_numpy(float) for s, g in paths.groupby("seed", observed=True)}
        rows = []
        ts = time.time()
        for (seed, persona), g in pan.groupby(["seed", "persona"], observed=True):
            g = g.sort_values(["policy", "day"])
            pols = g["policy"].unique().tolist()
            n_days = int(g["day"].max())
            C = g["cash_share"].to_numpy(float).reshape(len(pols), n_days)
            pv = g["portfolio_value"].to_numpy(float).reshape(len(pols), n_days)
            tvv = g["traded_value"].to_numpy(float).reshape(len(pols), n_days)
            cst = g["cost_paid"].to_numpy(float).reshape(len(pols), n_days)
            x = xs[int(seed)][:n_days]
            base = {"scenario": sc, "seed": int(seed), "persona": persona}
            ret = (pv[:, -1] / 10000.0 - 1.0) * 100.0
            mdd = (pv / np.maximum.accumulate(pv, axis=1) - 1.0).min(axis=1) * 100.0
            turn = tvv.sum(axis=1) / 10000.0
            cost = cst.sum(axis=1)
            ntr = (tvv > 0).sum(axis=1)
            mcs = C.mean(axis=1)
            for hw in half_widths:
                for th in thetas:
                    r = regret_terms_batch(C, x, th, persona, C[:, 0], half_width=hw)
                    for i, pol in enumerate(pols):
                        row = dict(base, policy=pol, theta=th, half_width=hw,
                                   theta_labels="|".join(labels[round(float(th), 6)]),
                                   return_pct=ret[i], mdd_pct=mdd[i], turnover=turn[i], cost_paid=cost[i],
                                   trade_count=int(ntr[i]), mean_cash_share=mcs[i])
                        for k in KEEP:
                            row[k] = float(r[k][i])
                        rows.append(row)
        f = pd.DataFrame(rows)
        frames.append(f)
        print(f"  {sc}: {len(f)} cell-rows ({time.time() - ts:.0f} s)", flush=True)
    allf = pd.concat(frames, ignore_index=True)
    for c in ("scenario", "persona", "policy", "theta_labels"):
        allf[c] = allf[c].astype("category")
    allf.to_parquet(os.path.join(out_dir, "cells.parquet"), index=False)
    meta = {"thetas": list(thetas), "theta_labels": {str(k): v for k, v in labels.items()},
            "half_widths": list(half_widths), "half_width_in_force": HW_IN_FORCE,
            "n_cell_rows": int(len(allf)), "scenarios": list(scenarios), "state": pin_state(),
            "panel_meta": json.load(open(os.path.join(PANEL, "meta.json"), encoding="utf-8"))["state"],
            "seconds": round(time.time() - t0), "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(meta, open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8"), indent=1, default=str)
    print(f"[cells] {len(allf)} rows -> {out_dir} ({time.time() - t0:.0f} s)", flush=True)


# --------------------------------------------------------------------------------------------- stage: the table
def _boot_ci(v, seeds, rng, n_boot=N_BOOT):
    """Percentile cluster bootstrap over seeds of a mean -- `tools/phase6/e6_16a._boot_mean`'s statistic, computed
    from per-cluster sums and counts so that 500 resamples of 100 clusters is one array op rather than 50,000
    concatenations (the un-vectorised form ran for minutes per table)."""
    v = np.asarray(v, float); seeds = np.asarray(seeds)
    ok = np.isfinite(v); v, seeds = v[ok], seeds[ok]
    if len(v) < 3:
        return (float("nan"),) * 3
    us, inv = np.unique(seeds, return_inverse=True)
    sums = np.bincount(inv, weights=v, minlength=len(us))
    cnts = np.bincount(inv, minlength=len(us)).astype(float)
    pick = rng.integers(0, len(us), size=(n_boot, len(us)))
    tot = cnts[pick].sum(axis=1)
    draws = np.where(tot > 0, sums[pick].sum(axis=1) / np.maximum(tot, 1e-12), np.nan)
    d = draws[np.isfinite(draws)]
    if len(d) < 10:
        return (float(np.mean(v)), float("nan"), float("nan"))
    return float(np.mean(v)), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def theta_table(out_dir: str):
    t0 = time.time()
    c = pd.read_parquet(os.path.join(out_dir, "cells.parquet"))
    c = c[c["half_width"] == HW_IN_FORCE]
    rng = np.random.default_rng(717001)
    METRICS = ("mcr", "mcr_B", "mcr_D", "band_mas", "mcr_window", "oracle_switches", "window_switches",
               "coverage", "share_target_lo", "share_target_hi", "share_agent_outside")
    rows = []
    for (sc, pol, th), g in c.groupby(["scenario", "policy", "theta"], observed=True):
        if str(pol) not in HEADLINE:
            continue
        row = {"scenario": str(sc), "policy": str(pol), "theta": float(th),
               "theta_labels": str(g["theta_labels"].iloc[0]),
               "n_cells": int(len(g)), "n_seeds": int(g["seed"].nunique())}
        seeds = g["seed"].to_numpy()
        for m in METRICS:
            mean, lo, hi = _boot_ci(g[m].to_numpy(float), seeds, rng)
            row[m] = mean; row[f"{m}_lo"] = lo; row[f"{m}_hi"] = hi
        rows.append(row)
    t = pd.DataFrame(rows).sort_values(["scenario", "theta", "policy"])
    t.to_csv(os.path.join(out_dir, "theta_table.csv"), index=False)

    def f(r, m):
        return f"{r[m]:.4f} [{r[m+'_lo']:.4f}, {r[m+'_hi']:.4f}]"

    L = ["# E7.1 / E7.2 — every headline metric at every theta (half-width 0.10, the value in force)", "",
         f"{int(t['n_seeds'].max())} seeds per scenario x 3 personas; percentile cluster bootstrap over seeds "
         f"({N_BOOT} resamples), the Phase-6 construction. MCR = B + D identically on resolvable steps.", ""]
    for sc in sorted(set(t["scenario"])):
        L += [f"## {sc}", "",
              "| theta | label | policy | MCR | B (band violation) | D (directional) | band-MAS | MCR per window | "
              "oracle switches | coverage |", "|---|---|---|---|---|---|---|---|---|---|"]
        for _, r in t[t.scenario == sc].iterrows():
            if r["policy"] not in ("mandate_conditional_oracle", "L5_full_level_free", "L5_level_free",
                                   "rule_p_sma50", "band_hi", "band_lo", "always_hold", "random"):
                continue
            L.append(f"| {r['theta']:.4f} | {r['theta_labels']} | {r['policy']} | {f(r,'mcr')} | {f(r,'mcr_B')} | "
                     f"{f(r,'mcr_D')} | {f(r,'band_mas')} | {f(r,'mcr_window')} | {r['oracle_switches']:.2f} | "
                     f"{r['coverage']:.3f} |")
        L.append("")
    with open(os.path.join(out_dir, "theta_table.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"[theta_table] {len(t)} rows -> {out_dir} ({time.time() - t0:.0f} s)", flush=True)


# ------------------------------------------------------------------------------- stage: floors and ceilings
def norm(out_dir: str):
    """E7.2's floor and ceiling under both conventions, on the panel's own policies, so the relabelling of
    weakness 53 is shown as a magnitude rather than described."""
    from evaluation.scoring import floors_and_ceilings_v21, normalise_metric
    from evaluation.metrics_v2 import floors_and_ceilings
    c = pd.read_parquet(os.path.join(out_dir, "cells.parquet"))
    c = c[(c["half_width"] == HW_IN_FORCE) & (c["theta"] == 0.05)]
    c["policy"] = c["policy"].astype(str)
    rows = []
    for (sc, persona), g in c.groupby(["scenario", "persona"], observed=True):
        means = g.groupby("policy", observed=True)[["mcr", "band_mas", "return_pct", "mdd_pct"]].mean()
        base = {p: {"mcr": float(r["mcr"]), "band_mas": float(r["band_mas"]),
                    "return_pct": float(r["return_pct"]), "mdd_pct": float(r["mdd_pct"])}
                for p, r in means.iterrows()}
        # the v2 convention needs its own key names and its own pool
        v2_base = {p: {"mcr_0.05": v["mcr"], "band_mas": v["band_mas"], "return_pct": v["return_pct"],
                       "mdd_pct": v["mdd_pct"], "point_mas_v1": np.nan, "point_mas_v2": np.nan,
                       "relative_mas": np.nan, "rg_v1": np.nan, "rg_theta_0.05": np.nan, "rg_action_0.05": np.nan}
                   for p, v in base.items()}
        fc21 = floors_and_ceilings_v21(base, str(persona))
        fc2 = floors_and_ceilings(v2_base, str(persona), convention="v2")
        for pol in ("L5_full_level_free", "L5_level_free", "rule_p_sma50", "always_hold", "constant_mix"):
            if pol not in base:
                continue
            rows.append({
                "scenario": str(sc), "persona": str(persona), "policy": pol, "mcr": base[pol]["mcr"],
                "v2_floor": fc2["mcr_0.05"]["floor"], "v2_ceiling": fc2["mcr_0.05"]["ceiling"],
                "v2_norm": normalise_metric(base[pol]["mcr"], fc2["mcr_0.05"]["floor"],
                                            fc2["mcr_0.05"]["ceiling"], "mcr_0.05"),
                "v2_degenerate": fc2["mcr_0.05"]["degenerate"],
                "v21_floor": fc21["mcr"]["floor"], "v21_ceiling": fc21["mcr"]["ceiling"],
                "v21_norm": normalise_metric(base[pol]["mcr"], fc21["mcr"]["floor"], fc21["mcr"]["ceiling"], "mcr"),
                "v21_degenerate": fc21["mcr"]["degenerate"]})
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(out_dir, "normalisation.csv"), index=False)
    summ = t.groupby("policy")[["mcr", "v2_floor", "v2_ceiling", "v2_norm", "v21_floor", "v21_ceiling",
                                "v21_norm"]].mean().reset_index()
    doc = {"theta": 0.05, "half_width": HW_IN_FORCE, "state": pin_state(),
           "v2_convention": "ceiling = constant_mix, floor = worst of {always_buy, always_sell, random}",
           "v21_convention": "ceiling = mandate_conditional_oracle (0 on resolvable steps), floor = worst of "
                             "{always_hold, always_buy, always_sell, random, band_lo, band_hi}",
           "n_cells": int(len(t)),
           "v2_degenerate_cells": int(t["v2_degenerate"].sum()), "v21_degenerate_cells": int(t["v21_degenerate"].sum()),
           "summary": summ.to_dict("records"),
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(doc, open(os.path.join(out_dir, "normalisation.json"), "w", encoding="utf-8"), indent=1, default=float)
    print(summ.round(4).to_string(index=False), flush=True)
    print(f"[norm] {len(t)} cells; degenerate under v2 {doc['v2_degenerate_cells']}, under v2_1 "
          f"{doc['v21_degenerate_cells']}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="cells,theta_table")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--scenarios", default="flat,bull_trap,crash,sustained_bull")
    a = ap.parse_args()
    d = derived_thetas()
    thetas, labels = theta_set(d)
    print(f"[theta set] {len(thetas)} values: " +
          ", ".join(f"{t:.6g} ({'|'.join(labels[t])})" for t in thetas), flush=True)
    scen = [s.strip() for s in a.scenarios.split(",") if s.strip()]
    for st in a.stages.split(","):
        st = st.strip()
        if st == "cells":
            cells(a.out, scen, thetas, labels, HALF_WIDTHS)
        elif st == "theta_table":
            theta_table(a.out)
        elif st == "norm":
            norm(a.out)
        else:
            raise SystemExit(f"unknown stage {st!r}")


if __name__ == "__main__":
    main()
