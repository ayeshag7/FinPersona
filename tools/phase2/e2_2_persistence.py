"""
E2.2 (PREREG_PHASE_2.md section 5): the firm-level persistence estimate, and REG-5's disagreement rule applied
to the CURRENT estimator set.

No new recovery study: Phase 1's full-scale study (32 cells, `e1_2/recovery.md`) already decided usability --
A never usable (interval coverage 0.00-0.01), B not identified (h-hat ~ 36-47 d whatever the truth, and the same
with x == 0), C usable for h <= 150 d.  This module assembles, for each estimator:

  * the pooled fit per period with its bootstrap interval (A from e1_2/vr_fit.json, C from the E2.3 fits);
  * the CROSS-SECTIONAL median half-life with P25/P75 where the estimator has one -- B per stock from
    e1_2/pv_by_stock_*.csv, and A per stock by re-fitting its closed form to each stock's VR curve
    (`vr_moments_by_stock.csv`; descriptive, weights 1/Var across stocks, stated);
  * REG-5's rule, and the union interval E2.6 sweeps over.

    python -m tools.phase2.e2_2_persistence
Outputs: docs/env_v2/generated/v2_1/e2_2/persistence.json, persistence.md
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
E12, E23, OUT = os.path.join(GEN, "e1_2"), os.path.join(GEN, "e2_3"), os.path.join(GEN, "e2_2")
PLAN_LEVELS = [30, 60, 120, 250, 500]
KS = (5, 10, 20, 60, 120, 250, 500)


def per_stock_A():
    """Descriptive cross-section for estimator A: the closed-form RW + AR(1) VR curve fitted to each stock's own
    VR moments (weights 1/Var of the moment across stocks).  A is NOT usable by the recovery study -- this is a
    description of the cross-sectional spread, not an adopted estimate."""
    from tools.phase1.e1_2_vr import fit
    p = os.path.join(E12, "vr_moments_by_stock.csv")
    if not os.path.exists(p):
        return None
    M = pd.read_csv(p, index_col=0)
    X = M.to_numpy()
    w = 1.0 / np.maximum(X.var(axis=0, ddof=1), 1e-30)
    hs, svs, sxs = [], [], []
    for i in range(X.shape[0]):
        f = fit(X[i], w, KS)
        hs.append(f["h"])
        svs.append(f["sigma_V"])
        sxs.append(f["s_x"])
    hs = np.array(hs)
    return {"n": int(len(hs)), "median_h": float(np.median(hs)),
            "p25_p75": [float(np.percentile(hs, 25)), float(np.percentile(hs, 75))],
            "median_sigma_V": float(np.median(svs)), "median_s_x": float(np.median(sxs)),
            "share_h_above_500": float(np.mean(hs > 500)), "weights": "1/Var of each moment across stocks"}


def main():
    os.makedirs(OUT, exist_ok=True)
    res = {"note": "E2.2 assembles the three estimators; usability is Phase 1's full-scale recovery study "
                   "(e1_2/recovery.md), not repeated here.",
           "recovery_verdicts": {
               "A": {"usable": False, "why": "median relative error 0.11 -> 20.0 as h grows and interval "
                                             "coverage 0.00-0.01 in every cell", "source": "e1_2/recovery.md"},
               "B": {"usable": False, "why": "h-hat ~ 36-47 d whatever the truth, and the same on a panel with "
                                             "x == 0: it measures the EDGAR V-hat error, not x",
                     "source": "e1_2/recovery.md"},
               "C": {"usable": True, "range": "h <= 150 d (median relative error 0.03-0.16); unusable at h >= 250",
                     "caveat": "the recovery panels come from C's own model, so the usability test favours C by "
                               "construction", "source": "e1_2/recovery.md, PHASE_1_REPORT.md 4.2"}},
           "estimators": {}}

    # ---- A: pooled fits per Phase-1 sub-period, plus the descriptive cross-section
    vr = json.load(open(os.path.join(E12, "vr_fit.json"), encoding="utf-8"))
    res["estimators"]["A"] = {
        "method": "Lo-MacKinlay variance ratios, pooled weighted minimum distance (E1.2)",
        "periods": {k: {"h_days": v["fit"]["h_days"], "ci95_stocks": v["ci_stock_bootstrap"]["h_days"],
                        "ci95_blocks": v["ci_block_bootstrap"]["h_days"], "sigma_V": v["fit"]["sigma_V"],
                        "s_x": v["fit"]["s_x"], "J": v["fit"]["J"], "n": v["n_stocks"]}
                    for k, v in vr["periods"].items()},
        "cross_section": per_stock_A(), "usable": False}

    # ---- B: per-stock cross-section (its own window; no sub-periods exist)
    pv = json.load(open(os.path.join(E12, "pv_fit.json"), encoding="utf-8"))
    res["estimators"]["B"] = {
        "method": "log(P/V_hat) AR(1), monthly, Andrews median-unbiased (E1.2)",
        "window": pv["window"], "variants": {}, "usable": False}
    for name, v in pv["variants"].items():
        res["estimators"]["B"]["variants"][name] = {
            "n_stocks": v["n_stocks"], "median_h_days": v["h_days_median_unbiased"]["median"],
            "ci95": v["h_days_median_unbiased"]["ci95"], "p25_p75": v["h_days_median_unbiased"]["iqr"],
            "median_h_ols": v["h_days_ols"]["median"], "s_x_median": v["s_x"]["median"],
            "share_at_grid_top": v["share_rho_mu_at_grid_top"]}

    # ---- C: the E2.3 SMM fits (this phase), per period, for whichever engines have fits
    C = {"method": "SMM on FW's nine moments plus the persistence-carrying moments (E2.3, this phase)",
         "engines": {}}
    for f in sorted(os.listdir(E23)) if os.path.isdir(E23) else []:
        if not (f.startswith("smm_") and f.endswith(".json")):
            continue
        d = json.load(open(os.path.join(E23, f), encoding="utf-8"))
        eng, per = d["engine"], d["period"]
        pars = d["params"]
        entry = {"period": per, "J": d["J"], "df": d["df"], "chi2_accept": d["chi2_accept"],
                 "fw_p": d["fw_bootstrap"]["p_value"], "accept_fw_p": d["accept_fw_p"],
                 "params": pars, "ci95": d.get("bootstrap_refits", {}).get("ci95")}
        if eng == "ar1":
            entry["half_life_days"] = pars["h"]
            entry["half_life_kind"] = "AR(1) half-life from rho = 2^(-1/h)"
        else:
            # pull-rate half-life ln2 / (mu n_bar phi); n_bar measured on the fitted engine
            entry["half_life_days"] = None
            entry["half_life_kind"] = "pull-rate ln2/(mu n_bar phi) -- filled by fill_pull_half_life()"
        C["engines"].setdefault(eng, {})[per] = entry
    res["estimators"]["C"] = C
    fill_pull_half_life(res)

    # ---- REG-5's rule
    usable = [k for k in ("A", "B", "C") if res["estimators"][k].get("usable") or k == "C"]
    res["reg5"] = {
        "usable_estimators": ["C"],
        "rule": "adopt the usable estimator with the smallest RMSE whose data interval contains the other "
                "usable estimators' point estimates; if the usable intervals are disjoint, adopt none and sweep "
                "the union",
        "outcome": "Only C survived usability, so the rule reduces to 'adopt the only usable estimator'. It is "
                   "therefore NOT evidence that C is right on the real panel; E2.3's acceptance test is what can "
                   "reject C's model, and its verdict is reported beside.",
        "qualifications": ["the recovery panels come from C's own model (favourable to C by construction)",
                           "Phase 1's data-side J = 66.6 already indicated misspecification on the real panel"]}
    # union interval for E2.6
    hs = []
    for eng, per in res["estimators"]["C"]["engines"].items():
        for p_, e in per.items():
            if p_ == "full" and e.get("half_life_days"):
                hs.append(e["half_life_days"])
                if e.get("ci95") and "h" in (e["ci95"] or {}):
                    hs += list(e["ci95"]["h"])
    lo = min(hs) if hs else None
    hi = max(hs) if hs else None
    levels = sorted(set(PLAN_LEVELS))
    if lo is not None:
        extra = [v for v in (5, 10, 15) if v < min(levels) and lo < min(levels)]
        levels = sorted(set(levels + extra))
    res["e2_6_levels"] = {"plan_levels": PLAN_LEVELS, "fitted_range": [lo, hi], "levels": levels,
                          "rule": "the union of C's fitted interval for the adopted engine and the plan's own "
                                  "sweep levels; the nearest decade below is added when the fit falls below 30 d"}
    with open(os.path.join(OUT, "persistence.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    write_md(res)
    print(json.dumps({"reg5": res["reg5"]["usable_estimators"], "e2_6_levels": res["e2_6_levels"]}, indent=1))
    print("written", OUT)


def fill_pull_half_life(res):
    """The FW engines' persistence is the pull rate ln2 / (mu n_bar phi), with n_bar the realised fundamentalist
    share of the FITTED engine (measured, not the reference pilot constant -- V5)."""
    from tools.phase2.engines import DEFAULTS, simulate, theta_to_params
    import math
    for eng, per in res["estimators"]["C"]["engines"].items():
        for p_, e in per.items():
            if eng == "ar1":
                p = dict(DEFAULTS)
                p.update(e["params"])
                out = simulate("ar1", 20, 20000, p, seed=118001, burn=1000)
                x = out["x"]
                xc = x - x.mean(axis=0)
                a1 = float(np.mean([(xc[:-1, i] * xc[1:, i]).sum() / max((xc[:, i] ** 2).sum(), 1e-300)
                                    for i in range(x.shape[1])]))
                e["sd_x_stationary"] = float(x.std())
                e["half_life_acf1_days"] = float(-math.log(2.0) / math.log(a1)) if 0 < a1 < 1 else None
                continue
            base = dict(DEFAULTS)
            base["price_scale"] = 1.0
            th = [e["params"][k] for k in e["params"]]
            p = dict(base)
            p.update(e["params"])
            out = simulate(eng, 20, 20000, p, seed=118001, burn=1000)   # 20,000 d, not 5,000: the fitted FW
            # engines are bistable and their occupancy is not determined on a 5,000-day window (e2_4/engine_diagnostics.json)
            n_bar = float(out["n_f"].mean())
            x = out["x"]
            xc = x - x.mean(axis=0)
            a1 = float(np.mean([(xc[:-1, i] * xc[1:, i]).sum() / max((xc[:, i] ** 2).sum(), 1e-300)
                                for i in range(x.shape[1])]))
            pull = p["mu"] * n_bar * p["phi"]
            e["n_bar_fitted"] = n_bar
            e["chartist_share_fitted"] = 1.0 - n_bar
            e["half_life_days"] = float(math.log(2.0) / pull) if pull > 0 else None
            e["half_life_acf1_days"] = float(-math.log(2.0) / math.log(a1)) if 0 < a1 < 1 else None
            e["sd_x_stationary"] = float(x.std())


def write_md(res):
    L = ["# E2.2 firm-level persistence and REG-5's disagreement rule (PREREG_PHASE_2.md section 5)", "",
         "Usability is Phase 1's full-scale recovery study (32 cells, 200/50 replications; `e1_2/recovery.md`), "
         "not repeated here:", "",
         "| estimator | usable? | why |", "|---|---|---|"]
    for k, v in res["recovery_verdicts"].items():
        L.append(f"| {k} | {'**yes**' if v['usable'] else 'no'} | {v.get('why', v.get('range', ''))} |")
    a = res["estimators"]["A"]
    L += ["", "## Estimator A (variance ratios) -- pooled fits per Phase-1 sub-period", "",
          "| period | n | h (d) | 95 % CI (stocks) | 95 % CI (blocks) | sigma_V | s_x | J |",
          "|---|---|---|---|---|---|---|---|"]
    for p_, v in a["periods"].items():
        L.append(f"| {p_} | {v['n']} | {v['h_days']:.1f} | [{v['ci95_stocks'][0]:.1f}, {v['ci95_stocks'][1]:.1f}] | "
                 f"[{v['ci95_blocks'][0]:.1f}, {v['ci95_blocks'][1]:.1f}] | {v['sigma_V']:.5f} | {v['s_x']:.3f} | {v['J']:.1f} |")
    if a.get("cross_section"):
        c = a["cross_section"]
        L += ["", f"Cross-section (descriptive; A is not usable): median h = {c['median_h']:.1f} d, "
                  f"P25-P75 {c['p25_p75'][0]:.1f}-{c['p25_p75'][1]:.1f} d over n = {c['n']} stocks; "
                  f"{c['share_h_above_500']:.0%} of stocks fit above 500 d. Weights: {c['weights']}."]
    b = res["estimators"]["B"]
    L += ["", f"## Estimator B (log(P/V-hat) AR(1), Andrews median-unbiased) -- {b['window'][0]}..{b['window'][1]}",
          "", "| variant | n | median h (d) | 95 % CI | P25-P75 | median h (OLS) | share at grid top |",
          "|---|---|---|---|---|---|---|"]
    for name, v in b["variants"].items():
        L.append(f"| {name} | {v['n_stocks']} | {v['median_h_days']:.0f} | [{v['ci95'][0]:.0f}, {v['ci95'][1]:.0f}] | "
                 f"{v['p25_p75'][0]:.0f}-{v['p25_p75'][1]:.0f} | {v['median_h_ols']:.0f} | {v['share_at_grid_top']:.2f} |")
    L += ["", "B has no sub-period breakdown: its monthly panel starts in 2009-06 and a sub-period would leave "
              "fewer than the 60 months its own rule requires. Stated as a gap, not filled."]
    L += ["", "## Estimator C (SMM, this phase's E2.3) -- pooled fits per period", "",
          "| engine | period | half-life (d) | kind | chartist share | sd(x) | J | df | chi2 accept | FW bootstrap p | FW: not rejected? |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for eng, per in res["estimators"]["C"]["engines"].items():
        for p_, e in per.items():
            L.append(f"| `{eng}` | {p_} | {('%.1f' % e['half_life_days']) if e.get('half_life_days') else '-'} | "
                     f"{e['half_life_kind'].split('--')[0].strip()} | "
                     f"{('%.3f' % e['chartist_share_fitted']) if e.get('chartist_share_fitted') is not None else '-'} | "
                     f"{('%.3f' % e['sd_x_stationary']) if e.get('sd_x_stationary') is not None else '-'} | "
                     f"{e['J']:.1f} | {e['df']} | {'yes' if e['chi2_accept'] else 'no'} | "
                     + ("- | " if e["fw_p"] is None else f"{e['fw_p']:.3f} | ")
                     + ("not run |" if e["accept_fw_p"] is None else ("**yes** |" if e["accept_fw_p"] else "no |")))
    r5 = res["reg5"]
    L += ["", "## REG-5's rule applied", "", f"Usable: {r5['usable_estimators']}.", "", r5["outcome"], "",
          "Qualifications carried with the adoption:"] + [f"- {q}" for q in r5["qualifications"]]
    e6 = res["e2_6_levels"]
    L += ["", "## The levels E2.6 sweeps", "",
          f"Fitted range {e6['fitted_range']}; plan levels {e6['plan_levels']}; **swept levels {e6['levels']}**. "
          f"Rule: {e6['rule']}."]
    with open(os.path.join(OUT, "persistence.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
