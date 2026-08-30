"""
E1.2 decision (PREREG_PHASE_1.md sections 4.4-4.5, REG-5 / REG-2 / D3): which estimators are usable (recovery study),
then h / s_x (FIT targets for Phase 2) and sigma_V (into the generator) by the pre-registered rules. Writes
e1_2/decision.{json,md} and updates envs/v2/params/value.json (sigma_V, s_x_fit, h_fit) with provenance.

Usability is read at each estimator's NEAREST recovery cell (the grid h in {30, 60, 120, 150, 250, 500} closest to the
estimator's own data h; sigma_V cell closest to its own sigma_V estimate, both cells for B, which carries no sigma_V).
The pre-registration says "usable at a given h" without naming the cell; this file names it and reports every cell.

    python -m tools.phase1.apply_e1_2 [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e1_2")
PARAMS = os.path.join(ROOT, "envs", "v2", "params", "value.json")
V2_SIGMA_V = 0.006


def nearest(v, grid):
    return min(grid, key=lambda g: abs(np.log(g) - np.log(v)))


def load_estimates():
    vr = json.load(open(os.path.join(GEN, "vr_fit.json"), encoding="utf-8"))["periods"]["full"]
    pv = json.load(open(os.path.join(GEN, "pv_fit.json"), encoding="utf-8"))["variants"]["EarningsPerShareBasic|sector"]
    est = {"A": {"name": "variance ratios (set A, full sample)", "h": vr["fit"]["h_days"], "h_ci": vr["ci_stock_bootstrap"]["h_days"],
                 "h_ci_block": vr["ci_block_bootstrap"]["h_days"], "s_x": vr["fit"]["s_x"], "s_x_ci": vr["ci_stock_bootstrap"]["s_x"],
                 "sigma_V": vr["fit"]["sigma_V"], "sigma_V_ci": vr["ci_stock_bootstrap"]["sigma_V"],
                 "sigma_V_ci_block": vr["ci_block_bootstrap"]["sigma_V"], "n": vr["n_stocks"]},
           "B": {"name": "log(P/V_hat) AR(1), median-unbiased (set A, EPS basic, sector multiple)",
                 "h": pv["h_days_median_unbiased"]["median"], "h_ci": pv["h_days_median_unbiased"]["ci95"],
                 "s_x": pv["s_x"]["median"], "s_x_ci": pv["s_x"]["ci95"], "sigma_V": None, "sigma_V_ci": None, "n": pv["n_stocks"],
                 "note": "sigma_V from dlog V_hat is overstated by measurement noise and is not used (PREREG 4.2)"}}
    p = os.path.join(GEN, "smm_fit.json")
    if os.path.exists(p):
        c = json.load(open(p, encoding="utf-8"))
        est["C"] = {"name": "SMM on persistence-carrying moments (set A)", "h": c["fit"]["h"], "h_ci": c["ci95_h"],
                    "s_x": c["fit"]["s_x"], "s_x_ci": c["ci95_s_x"], "sigma_V": c["fit"]["sigma_V"], "sigma_V_ci": c["ci95_sigma_V"],
                    "n": 417, "J": c["fit"]["J"]}
    return est


def usability_table(rec, est):
    hs, svs = rec["design"]["hs"], rec["design"]["sigma_Vs"]
    out = {}
    for k, e in est.items():
        key = {"A": "A", "B": "B_rho0.0", "C": "C"}[k]
        hn = nearest(e["h"], hs)
        cells = svs if e["sigma_V"] is None else [nearest(e["sigma_V"], svs)]
        rows = []
        for sv in cells:
            cell = rec["cells"][f"h{hn}|sv{sv}"]
            u = cell[key]
            row = {"cell_h": hn, "cell_sigma_V": sv, "median_rel_error": u["median_rel_error"], "rmse_rel": u.get("rmse_rel"),
                   "coverage": u.get("coverage"), "usable": bool(u["usable"]), "n_reps": u.get("n")}
            if k == "C" and (u.get("n") or 0) < 50:
                # ADDENDUM section 5: at 8 replications a median within +/- 0.05 of the 0.20 boundary is UNDECIDED, not usable
                err = u["median_rel_error"]
                row["verdict"] = "usable" if err < 0.15 else ("undecided" if err < 0.25 else "unusable")
                row["usable"] = row["verdict"] == "usable"
            if k == "B":
                u9 = cell["B_rho0.9"]
                row["rho_m_0.9"] = {"median_rel_error": u9["median_rel_error"], "coverage": u9.get("coverage"), "usable": bool(u9["usable"])}
            rows.append(row)
        rm = [r["rmse_rel"] for r in rows if r["rmse_rel"] is not None]
        out[k] = {"nearest_h": hn, "h_in_grid": bool(min(hs) <= e["h"] <= max(hs)), "cells": rows,
                  "usable": all(r["usable"] for r in rows), "rmse_rel": float(np.mean(rm)) if rm else float("nan")}
    return out


def decide(est, use):
    usable = [k for k in est if use[k]["usable"]]
    d = {"usable": usable}
    if not usable:
        d["h_s_x"] = {"adopted": None, "reason": "no estimator is usable at its nearest cell: all reported, union of intervals to Phase 2 (E2.6); D3"}
    else:
        cands = []
        for k in sorted(usable, key=lambda k: use[k]["rmse_rel"]):
            lo, hi = est[k]["h_ci"]
            if all(lo <= est[o]["h"] <= hi for o in usable if o != k):
                cands.append(k)
        if cands:
            k = cands[0]
            d["h_s_x"] = {"adopted": k, "h": est[k]["h"], "h_ci": est[k]["h_ci"], "s_x": est[k]["s_x"], "s_x_ci": est[k]["s_x_ci"],
                          "reason": "smallest RMSE among usable estimators whose data interval contains the other usable estimators' points (usable: %s)" % usable}
        else:
            d["h_s_x"] = {"adopted": None,
                          "reason": "usable estimators %s have disjoint h intervals: none adopted; union handed to Phase 2 (E2.6)" % usable,
                          "h_union": [min(est[k]["h_ci"][0] for k in usable), max(est[k]["h_ci"][1] for k in usable)],
                          "s_x_union": [min(est[k]["s_x_ci"][0] for k in usable), max(est[k]["s_x_ci"][1] for k in usable)]}
    sv_est = [k for k in usable if est[k]["sigma_V"] is not None]
    if not sv_est:
        d["sigma_V"] = {"adopted": None, "value_in_force": V2_SIGMA_V, "reason": "no usable estimator carries sigma_V: D3, v2's 0.006 kept and labelled"}
    elif len(sv_est) == 1:
        k = sv_est[0]
        d["sigma_V"] = {"adopted": k, "value": est[k]["sigma_V"], "ci": est[k]["sigma_V_ci"], "reason": "the only usable estimator with a sigma_V"}
    else:
        los = [est[k]["sigma_V_ci"][0] for k in sv_est]
        his = [est[k]["sigma_V_ci"][1] for k in sv_est]
        if max(los) <= min(his):
            w = np.array([1.0 / ((est[k]["sigma_V_ci"][1] - est[k]["sigma_V_ci"][0]) / 3.92) ** 2 for k in sv_est])
            v = float(np.sum(w * np.array([est[k]["sigma_V"] for k in sv_est])) / w.sum())
            d["sigma_V"] = {"adopted": "+".join(sv_est), "value": v, "ci": [min(los), max(his)],
                            "reason": "intervals overlap: inverse-variance pooled FIT, interval = union"}
        else:
            d["sigma_V"] = {"adopted": None, "value_in_force": V2_SIGMA_V,
                            "reason": "sigma_V intervals of %s do not overlap: D3, both reported with the E1.3 tables; v2's 0.006 kept and labelled" % sv_est}
    return d


def fmt(x, nd=2):
    return "-" if x is None else f"{x:.{nd}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    rec = json.load(open(os.path.join(GEN, "recovery.json"), encoding="utf-8"))
    est = load_estimates()
    use = usability_table(rec, est)
    d = decide(est, use)
    out = {"estimates": est, "usability": use, "decision": d,
           "rule": "PREREG_PHASE_1.md 4.4-4.5; nearest-cell convention stated in tools/phase1/apply_e1_2.py"}
    with open(os.path.join(GEN, "decision.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    L = ["# E1.2 decision (PREREG_PHASE_1.md sections 4.4-4.5)", "",
         "| estimator | data h (d) [CI] | s_x [CI] | sigma_V/day [CI] | nearest cell | median rel. error / RMSE / coverage per cell | usable |",
         "|---|---|---|---|---|---|---|"]
    for k, e in est.items():
        u = use[k]
        cells = "; ".join(f"({r['cell_h']}, {r['cell_sigma_V']}): {fmt(r['median_rel_error'])} / {fmt(r['rmse_rel'])} / {fmt(r['coverage'])}"
                          + (f" [{r['verdict']}, n = {r['n_reps']}]" if "verdict" in r else "") for r in u["cells"])
        sv = "-" if e["sigma_V"] is None else f"{e['sigma_V']:.4f} [{e['sigma_V_ci'][0]:.4f}, {e['sigma_V_ci'][1]:.4f}]"
        grid = "" if u["h_in_grid"] else " (data h outside the grid)"
        L.append(f"| {k}: {e['name']} | {e['h']:.0f} [{e['h_ci'][0]:.0f}, {e['h_ci'][1]:.0f}] | {e['s_x']:.3f} [{e['s_x_ci'][0]:.3f}, {e['s_x_ci'][1]:.3f}] | {sv} | h {u['nearest_h']}{grid} | {cells} | {u['usable']} |")
    L += ["", "**h / s_x:** " + json.dumps(d["h_s_x"]), "", "**sigma_V:** " + json.dumps(d["sigma_V"])]
    with open(os.path.join(GEN, "decision.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))
    if a.dry_run:
        return
    p = json.load(open(PARAMS, encoding="utf-8"))
    s = d["sigma_V"]
    if s["adopted"]:
        p["sigma_V"] = {"value": s["value"], "label": f"FIT E1.2 ({s['adopted']}; {s['reason']}); survivor panel set A (REG-15: the full-universe value is not measurable on this panel)",
                        "source": "e1_2/decision.json", "date": "2026-08-29", "interval": s["ci"], "n": 417}
    else:
        p["sigma_V"] = {"value": V2_SIGMA_V, "label": f"D3 PENDING (E1.2: {s['reason']}); v2's stipulated 0.006 stays in force until the team decides",
                        "source": "e1_2/decision.json", "date": "2026-08-29", "interval": None, "n": None}
    h = d["h_s_x"]
    if h["adopted"]:
        p["s_x_fit"] = {"value": h["s_x"], "label": f"FIT target for Phase 2 (E1.2 estimator {h['adopted']}; not a generator parameter)",
                        "source": "e1_2/decision.json", "date": "2026-08-29", "interval": h["s_x_ci"]}
        p["h_fit"] = {"value": h["h"], "label": f"FIT target for Phase 2 (E1.2 estimator {h['adopted']}; days)",
                      "source": "e1_2/decision.json", "date": "2026-08-29", "interval": h["h_ci"]}
    else:
        p["s_x_fit"] = {"value": None, "label": f"NOT ADOPTED (E1.2: {h['reason']})", "source": "e1_2/decision.json", "date": "2026-08-29", "interval": h.get("s_x_union")}
        p["h_fit"] = {"value": None, "label": f"NOT ADOPTED (E1.2: {h['reason']})", "source": "e1_2/decision.json", "date": "2026-08-29", "interval": h.get("h_union")}
    with open(PARAMS, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(p, fh, indent=1)
    print("value.json updated: sigma_V, s_x_fit, h_fit")


if __name__ == "__main__":
    main()
