"""
v2.1 Phase 6 -- E6.6 (analytic half): the level-free price-only bound on R^2(x) at the ADOPTED parameters, its
check against Phase 1's sweep, and the calm-channel ladder on the Phase-5 state.

Plan Section 10.2 (E6.6) and Appendix B; 16A's G4 second clause ("the price-only surrogate's R^2(x) lies at or
below the Appendix B bound within its CI", read with Appendix B's caveat: "within its CI plus the nonlinear
allowance measured on a Gaussian control run").

Three stages, each its own block in bound.json (resumable, rule 14):

  bound   The Kalman bound (`tools/phase1/kalman_bound.py`, verified against LOG section 3) at the parameters
          IN FORCE: sigma_V from value.json, h and its interval from mispricing.json, and s_x DERIVED from the
          volatility block's own identity -- var(innovation) = sbar^2 (+ lambda sigma_J^2 with the jumps) and
          s_x = sqrt(var / (1 - rho^2)), E3.8's construction -- because no parameter file carries a stationary
          sd(x) (the "0.068" quoted in PREREG_PHASE_5 is E3.8's implied value, not a stored entry).  Beside it,
          the REALISED sd(x) of the generator's own flat paths and calm rows, so that the bound is reported at
          both the process' implied and the generator's realised dispersion, and at both ends of h's interval.

  sweep   Appendix B's check "against the surrogate at every (sigma_V, s_x, h) of Phase 1's sweep": the 40 stored
          points of e1_3/sweep.json, each with its surrogate CI and its bound; the count of points at which the
          CI's lower end exceeds the bound is the instrument's validation.

  ladder  The nonlinear allowance, measured like for like on the Phase-5 state.  Rungs:
            1-4  E3.8's arms (exact Gaussian -> + GJR-t -> + jumps -> + both), reused from
                 e3_8/decomposition.json: the process at the parameters still in force (Phases 4 and 5 changed
                 neither the engine nor the volatility block), with no events and no feedback
            5    the GENERATOR's flat scenario with the sentiment feedback OFF (b_pred = b_rev = 0; the e5_arms
                 override), re-simulated on the SEP panel's own flat seeds
            6    the generator's flat scenario as deployed (feedback ON): the SEP panel's flat paths
            7    every calm row of the SEP panel (flat + the pre-event calm of the event scenarios): the figure
                 the reports call "the calm-trained level-free channel" (e5_after/calm_trained_phase5.json)
          Each rung is the calm-TRAINED level-free surrogate (tools/phase3/e3_9_calm_trained.calm_trained, the
          e3_9 estimator, imported unchanged; best of ridge/gbt/mlp; 500-resample cluster bootstrap over paths),
          so 4 -> 5 is the process-to-generator step, 5 -> 6 the feedback's share, 6 -> 7 the events' share.
          The rule that reads the ladder against G4 is PREREG_PHASE_6's; this tool measures.

Usage:
    python -u tools/phase6/e6_6_bound.py --stages bound,sweep,ladder [--workers 3] [--n-boot 500]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

from tools.phase1.kalman_bound import kalman_bound  # noqa: E402
from tools.phase5.common import GEN, PANELS, SEP_SEED0, SEP_N, _one_panel_path, encode_nm, pin_state, shown_fields_of  # noqa: E402

OUT = os.path.join(GEN, "e6_6")
PARAMS = os.path.join(ROOT, "envs", "v2", "params")
SEP_PANEL = os.path.join(PANELS, "sep_phase5_after.pkl")
E38 = os.path.join(GEN, "e3_8", "decomposition.json")
E34_BLOCK = os.path.join(GEN, "e3_4", "block.json")
E13_SWEEP = os.path.join(GEN, "e1_3", "sweep.json")
E5_CALM = os.path.join(GEN, "e5_after", "calm_trained_phase5.json")
V2_REFERENCE_ROWS = [(0.006, 0.13, 150.0), (0.006, 0.165, 150.0)]   # the plan's Appendix-B rows, for orientation


def _load(p):
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _save(res):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "bound.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=float)


# ---------------------------------------------------------------------------------------------- bound
def params_in_force() -> Dict:
    v = _load(os.path.join(PARAMS, "value.json"))
    m = _load(os.path.join(PARAMS, "mispricing.json"))
    blk = _load(E34_BLOCK)
    h = float(m["half_life"]["value"])
    h_int = m["structural"].get("interval", {}).get("h")
    out = {"sigma_V": float(v["sigma_V"]["value"]), "sigma_V_source": "envs/v2/params/value.json sigma_V",
           "h": h, "h_interval": h_int, "h_source": "envs/v2/params/mispricing.json half_life (+ structural.interval.h)",
           "sbar": float(blk["sbar"]), "shape": blk["shape"], "nu": blk.get("nu"),
           "jump_rate": float(blk["jump_rate"]), "jump_sd": float(blk["jump_sd"]),
           "block_source": os.path.relpath(E34_BLOCK, ROOT).replace("\\", "/")}
    rho = 2.0 ** (-1.0 / h)
    out["rho"] = rho
    out["s_x_identity_no_jumps"] = math.sqrt(out["sbar"] ** 2 / (1.0 - rho ** 2))
    out["s_x_identity_with_jumps"] = math.sqrt((out["sbar"] ** 2 + out["jump_rate"] * out["jump_sd"] ** 2) / (1.0 - rho ** 2))
    out["s_x_identity_note"] = ("var(innovation) = sbar^2 (+ lambda sigma_J^2); s_x = sqrt(var / (1 - rho^2)); "
                                "E3.8's construction. No parameter file stores a stationary sd(x).")
    return out


def realised_sd_x(panel: pd.DataFrame) -> Dict:
    flat = panel[panel["scenario"] == "flat"]
    calm = panel[panel["macro"] == "calm"]
    per_path_flat = flat.groupby("seed")["x"].std()
    return {"flat_pooled": float(flat["x"].std()), "flat_per_path_median": float(per_path_flat.median()),
            "flat_per_path_p10_p90": [float(per_path_flat.quantile(0.1)), float(per_path_flat.quantile(0.9))],
            "all_calm_pooled": float(calm["x"].std()), "n_flat_paths": int(flat["seed"].nunique()),
            "n_calm_rows": int(len(calm)),
            "note": "the 200-day sd is biased DOWN for a persistent process (E6.9: -18 % at the engine's half-life), "
                    "so the pooled sd (which keeps the cross-path spread) is the one comparable to the stationary s_x"}


def stage_bound(res: Dict):
    p = params_in_force()
    panel = pd.read_pickle(SEP_PANEL)
    rs = realised_sd_x(panel)
    hs = [("h", p["h"])] + ([("h_lo", p["h_interval"][0]), ("h_hi", p["h_interval"][1])] if p["h_interval"] else [])
    sxs = [("identity_no_jumps", p["s_x_identity_no_jumps"]), ("identity_with_jumps", p["s_x_identity_with_jumps"]),
           ("realised_flat_pooled", rs["flat_pooled"]), ("realised_all_calm_pooled", rs["all_calm_pooled"])]
    rows = []
    for hn, hv in hs:
        for sn, sv in sxs:
            b = kalman_bound(p["sigma_V"], sv, hv, T=200)
            rows.append({"h_label": hn, "s_x_label": sn, **b})
    ref = [{"h_label": "plan v2 row", "s_x_label": f"sigma_V {sv} s_x {sx}", **kalman_bound(sv, sx, h, T=200)}
           for sv, sx, h in V2_REFERENCE_ROWS]
    adopted = kalman_bound(p["sigma_V"], p["s_x_identity_with_jumps"], p["h"], T=200)
    res["bound"] = {"params": p, "realised_sd_x": rs, "table": rows, "plan_reference_rows": ref,
                    "adopted": {"s_x": p["s_x_identity_with_jumps"], **adopted,
                                "note": "the bound at the engine's own implied s_x (with the jumps' variance) and its FIT "
                                        "half-life; the linear-Gaussian ceiling on any level-free reader of the price path"},
                    "panel": os.path.relpath(SEP_PANEL, ROOT).replace("\\", "/")}
    print(f"[bound] sigma_V {p['sigma_V']:.5f}, h {p['h']:.2f} [{p['h_interval']}], s_x identity {p['s_x_identity_no_jumps']:.4f} / "
          f"{p['s_x_identity_with_jumps']:.4f} (jumps), realised flat {rs['flat_pooled']:.4f}, all-calm {rs['all_calm_pooled']:.4f}")
    for r in rows:
        print(f"    {r['h_label']:5s} {r['s_x_label']:26s} s_x {r['s_x']:.4f}: window {r['window_avg']:.4f}  day200 {r['day_T']:.4f}  steady {r['steady_state']:.4f}")
    _save(res)


# ---------------------------------------------------------------------------------------------- sweep
def stage_sweep(res: Dict):
    s = _load(E13_SWEEP)
    rows = []
    n_above_avg = n_above_day = 0
    for r in s["grid"]:
        c = r["surrogate_level_free"]["calm"]; k = r["kalman"]
        above_avg = c["ci95"][0] > k["window_avg"]; above_day = c["ci95"][0] > k["day_T"]
        n_above_avg += above_avg; n_above_day += above_day
        rows.append({"sigma_V": r["sigma_V"], "df_V": r["df_V"], "s_x": r["s_x"], "h": k["h"], "n_paths": r["surrogate_level_free"]["n_paths"],
                     "surrogate_calm_R2": c["R2"], "ci95": c["ci95"], "bound_window_avg": k["window_avg"], "bound_day_T": k["day_T"],
                     "bound_steady": k["steady_state"], "gap_point_minus_window_avg": r["gap_calm_surrogate_minus_bound_window"],
                     "ci_lo_above_window_avg": bool(above_avg), "ci_lo_above_day_T": bool(above_day)})
    res["sweep"] = {"source": os.path.relpath(E13_SWEEP, ROOT).replace("\\", "/"), "design": s["design"], "n_points": len(rows),
                    "n_ci_lo_above_window_avg": n_above_avg, "n_ci_lo_above_day_T": n_above_day, "rows": rows,
                    "reading": "the bound is valid at a point when the surrogate's CI lower end does not exceed it; the count is "
                               "the instrument's validation across the sweep (Appendix B's check)"}
    print(f"[sweep] {len(rows)} points; CI-lo above window-average bound at {n_above_avg}, above day-T bound at {n_above_day}")
    _save(res)


# ---------------------------------------------------------------------------------------------- ladder
def _calm_trained_best(panel: pd.DataFrame, n_boot: int) -> Dict:
    from tools.phase3.e3_9_calm_trained import calm_trained
    pan = encode_nm(panel)
    shown = shown_fields_of(pan)
    rows = calm_trained(pan, shown, n_boot)
    def best(fs):
        cand = [r for r in rows if r["feature_set"] == fs and np.isfinite(r["R2"])]
        return max(cand, key=lambda r: r["R2"]) if cand else None
    lf, fu = best("price_only"), best("full")
    return {"levelfree": {k: lf[k] for k in ("model", "R2", "R2_lo", "R2_hi", "sign_acc_resolvable", "n_rows", "n_paths")},
            "full": {k: fu[k] for k in ("model", "R2", "R2_lo", "R2_hi", "n_rows", "n_paths")}, "all_rows": rows}


def _flat_paths_feedback_off(workers: int) -> pd.DataFrame:
    jobs = [("flat", s, {}, 200, {"b_pred": 0.0, "b_rev": 0.0}) for s in range(SEP_SEED0, SEP_SEED0 + SEP_N)]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        frames = list(ex.map(_one_panel_path, jobs, chunksize=4))
    return pd.concat(frames, ignore_index=True)


def stage_ladder(res: Dict, workers: int, n_boot: int):
    lad = res.get("ladder", {"rungs": []})
    done = {r["rung"] for r in lad["rungs"]}
    p = res.get("bound", {}).get("params") or params_in_force()

    # rungs 1-4: E3.8, reused with provenance
    if 1 not in done:
        e38 = _load(E38)
        for i, arm in enumerate(e38["arms"], 1):
            lad["rungs"].append({"rung": i, "label": f"E3.8: {arm['label']}", "simulator": "tools/phase3/e3_8_decomposition.simulate (process only)",
                                 "population": "all rows (no phases)", "n_paths": e38["design"]["n_paths"],
                                 "levelfree_R2": arm["levelfree_R2"], "ci95": arm["ci95"], "best_model": arm["best_model"],
                                 "s_x_implied": arm["s_x_implied"], "realised_sd_x": arm["realised_sd_x"],
                                 "bound_window_avg": arm["bound_window_avg_gaussian"],
                                 "source": os.path.relpath(E38, ROOT).replace("\\", "/"),
                                 "estimator": "cross-phase-trained = calm-trained here (the process has no phases)"})
        print("[ladder] rungs 1-4 reused from E3.8", flush=True)
        _save({**res, "ladder": lad})

    panel = None
    if 5 not in done:
        t0 = time.time()
        fp = _flat_paths_feedback_off(workers)
        ct = _calm_trained_best(fp, n_boot)
        sd = float(fp["x"].std())
        b = kalman_bound(p["sigma_V"], sd, p["h"], T=200)
        lad["rungs"].append({"rung": 5, "label": "generator flat, feedback OFF (b_pred = b_rev = 0)", "simulator": "envs.synthetic_market (deployed state) + config override",
                             "population": "flat paths, calm rows", "n_paths": int(fp["seed"].nunique()), "seeds": [SEP_SEED0, SEP_SEED0 + SEP_N - 1],
                             "levelfree_R2": ct["levelfree"]["R2"], "ci95": [ct["levelfree"]["R2_lo"], ct["levelfree"]["R2_hi"]],
                             "best_model": ct["levelfree"]["model"], "full_R2": ct["full"]["R2"], "full_ci95": [ct["full"]["R2_lo"], ct["full"]["R2_hi"]],
                             "realised_sd_x": sd, "bound_window_avg": b["window_avg"], "bound_day_T": b["day_T"],
                             "estimator": "calm-trained (e3_9), best of ridge/gbt/mlp", "seconds": round(time.time() - t0)})
        print(f"[ladder] rung 5: R2 {ct['levelfree']['R2']:.4f} [{ct['levelfree']['R2_lo']:.4f}, {ct['levelfree']['R2_hi']:.4f}] "
              f"({ct['levelfree']['model']}); sd(x) {sd:.4f}; bound {b['window_avg']:.4f} ({time.time() - t0:.0f} s)", flush=True)
        _save({**res, "ladder": lad})

    if 6 not in done:
        t0 = time.time()
        panel = pd.read_pickle(SEP_PANEL)
        fl = panel[panel["scenario"] == "flat"].reset_index(drop=True)
        ct = _calm_trained_best(fl, n_boot)
        sd = float(fl["x"].std())
        b = kalman_bound(p["sigma_V"], sd, p["h"], T=200)
        lad["rungs"].append({"rung": 6, "label": "generator flat, as deployed (feedback ON)", "simulator": "the SEP panel's flat paths",
                             "population": "flat paths, calm rows", "n_paths": int(fl["seed"].nunique()),
                             "levelfree_R2": ct["levelfree"]["R2"], "ci95": [ct["levelfree"]["R2_lo"], ct["levelfree"]["R2_hi"]],
                             "best_model": ct["levelfree"]["model"], "full_R2": ct["full"]["R2"], "full_ci95": [ct["full"]["R2_lo"], ct["full"]["R2_hi"]],
                             "realised_sd_x": sd, "bound_window_avg": b["window_avg"], "bound_day_T": b["day_T"],
                             "estimator": "calm-trained (e3_9), best of ridge/gbt/mlp", "seconds": round(time.time() - t0),
                             "panel": os.path.relpath(SEP_PANEL, ROOT).replace("\\", "/")})
        print(f"[ladder] rung 6: R2 {ct['levelfree']['R2']:.4f} [{ct['levelfree']['R2_lo']:.4f}, {ct['levelfree']['R2_hi']:.4f}] "
              f"({ct['levelfree']['model']}); sd(x) {sd:.4f}; bound {b['window_avg']:.4f} ({time.time() - t0:.0f} s)", flush=True)
        _save({**res, "ladder": lad})

    if 7 not in done:
        if os.path.exists(E5_CALM):
            e5 = _load(E5_CALM)
            hl = e5.get("headline", e5.get("states", {})).get("phase5") or e5.get("headline", {}).get("phase5")
            lf = (hl or {}).get("calm_trained_levelfree")
            if lf:
                if panel is None:
                    panel = pd.read_pickle(SEP_PANEL)
                calm = panel[panel["macro"] == "calm"]
                sd = float(calm["x"].std())
                b = kalman_bound(p["sigma_V"], sd, p["h"], T=200)
                lad["rungs"].append({"rung": 7, "label": "generator, every calm row of the SEP panel (flat + pre-event calm)", "simulator": "the SEP panel",
                                     "population": "all scenarios, calm rows", "n_paths": int(calm[["scenario", "seed"]].drop_duplicates().shape[0]),
                                     "levelfree_R2": lf["R2"], "ci95": [lf["R2_lo"], lf["R2_hi"]], "best_model": lf["model"],
                                     "full_R2": ((hl.get("calm_trained_full") or {}).get("R2")),
                                     "realised_sd_x": sd, "bound_window_avg": b["window_avg"], "bound_day_T": b["day_T"],
                                     "estimator": "calm-trained (e3_9), best of ridge/gbt/mlp", "source": os.path.relpath(E5_CALM, ROOT).replace("\\", "/")})
                print(f"[ladder] rung 7 reused from {os.path.relpath(E5_CALM, ROOT)}: R2 {lf['R2']:.4f} [{lf['R2_lo']:.4f}, {lf['R2_hi']:.4f}]", flush=True)
        if 7 not in {r["rung"] for r in lad["rungs"]}:
            t0 = time.time()
            if panel is None:
                panel = pd.read_pickle(SEP_PANEL)
            ct = _calm_trained_best(panel, n_boot)
            calm = panel[panel["macro"] == "calm"]; sd = float(calm["x"].std())
            b = kalman_bound(p["sigma_V"], sd, p["h"], T=200)
            lad["rungs"].append({"rung": 7, "label": "generator, every calm row of the SEP panel (flat + pre-event calm)", "simulator": "the SEP panel",
                                 "population": "all scenarios, calm rows", "n_paths": ct["levelfree"]["n_paths"],
                                 "levelfree_R2": ct["levelfree"]["R2"], "ci95": [ct["levelfree"]["R2_lo"], ct["levelfree"]["R2_hi"]],
                                 "best_model": ct["levelfree"]["model"], "full_R2": ct["full"]["R2"], "realised_sd_x": sd,
                                 "bound_window_avg": b["window_avg"], "bound_day_T": b["day_T"],
                                 "estimator": "calm-trained (e3_9), best of ridge/gbt/mlp", "seconds": round(time.time() - t0)})
            print(f"[ladder] rung 7 computed: R2 {ct['levelfree']['R2']:.4f} ({time.time() - t0:.0f} s)", flush=True)
        _save({**res, "ladder": lad})

    lad["rungs"].sort(key=lambda r: r["rung"])
    for i, r in enumerate(lad["rungs"]):
        r["increment_over_previous"] = (r["levelfree_R2"] - lad["rungs"][i - 1]["levelfree_R2"]) if i else None
        r["excess_over_gaussian_bound"] = r["levelfree_R2"] - r["bound_window_avg"]
    lad["reading"] = ("1 -> 4 the volatility block's nonlinear allowance (E3.8); 4 -> 5 the process-to-generator step at flat "
                      "(same parameters; the generator's V has drift and t innovations, and jumps are placed at x_zero); "
                      "5 -> 6 the sentiment feedback's share; 6 -> 7 the events' share (the pre-event calm of crash and "
                      "bull-trap paths). The rule that reads this against G4's second clause is PREREG_PHASE_6's.")
    res["ladder"] = lad
    _save(res)


# ---------------------------------------------------------------------------------------------- markdown
def to_markdown(res: Dict) -> str:
    L = ["# E6.6 — the analytic level-free bound at the adopted parameters, the sweep check, and the calm-channel ladder", ""]
    if "bound" in res:
        b = res["bound"]; p = b["params"]; rs = b["realised_sd_x"]
        L += ["## The bound at the parameters in force", "",
              f"σ_V = {p['sigma_V']:.6f}/day (`value.json`), h = {p['h']:.2f} d, interval [{p['h_interval'][0]:.2f}, {p['h_interval'][1]:.2f}] "
              f"(`mispricing.json`), sbar = {p['sbar']:.6f}, λ = {p['jump_rate']:.6f}, σ_J = {p['jump_sd']:.4f} (`{p['block_source']}`).", "",
              f"**s_x is derived, not read**: {p['s_x_identity_note']} → **{p['s_x_identity_no_jumps']:.4f}** without the jumps, "
              f"**{p['s_x_identity_with_jumps']:.4f}** with them. Realised on the generator's own paths: flat pooled {rs['flat_pooled']:.4f} "
              f"(per-path median {rs['flat_per_path_median']:.4f}, P10–P90 [{rs['flat_per_path_p10_p90'][0]:.4f}, {rs['flat_per_path_p10_p90'][1]:.4f}], "
              f"n = {rs['n_flat_paths']}), all calm rows pooled {rs['all_calm_pooled']:.4f} (n = {rs['n_calm_rows']:,} rows).", "",
              "| h | s_x | value | window average | day 200 | steady state |", "|---|---|---|---|---|---|"]
        for r in b["table"]:
            L.append(f"| {r['h_label']} = {r['h']:.2f} | {r['s_x_label']} | {r['s_x']:.4f} | {r['window_avg']:.4f} | {r['day_T']:.4f} | {r['steady_state']:.4f} |")
        for r in b["plan_reference_rows"]:
            L.append(f"| {r['h_label']} h = {r['h']:.0f} | {r['s_x_label']} | {r['s_x']:.3f} | {r['window_avg']:.4f} | {r['day_T']:.4f} | {r['steady_state']:.4f} |")
        a = b["adopted"]
        L += ["", f"**Adopted row** (s_x with the jumps, FIT h): window average **{a['window_avg']:.4f}**, day 200 **{a['day_T']:.4f}**, "
                  f"steady state {a['steady_state']:.4f}. At h = 22 d the day-200 value and the steady state coincide: the filter has "
                  f"converged long before the window ends, so the ceiling for a reader with the whole history is the steady state, and "
                  f"the window average is the ceiling for the average day.", ""]
    if "sweep" in res:
        s = res["sweep"]
        L += ["## The check against Phase 1's sweep", "",
              f"{s['n_points']} points of `{s['source']}` (h = 150 d, 200 seeds each): the surrogate's calm R²(x) CI lower end exceeds the "
              f"window-average bound at **{s['n_ci_lo_above_window_avg']}** points and the day-200 bound at **{s['n_ci_lo_above_day_T']}**. "
              f"{s['reading']}.", "",
              "| σ_V | V innov. | s_x | surrogate calm R² [CI] | bound: window / day 200 / steady | point gap |", "|---|---|---|---|---|---|"]
        for r in s["rows"]:
            L.append(f"| {r['sigma_V']:.3f} | {r['df_V']} | {r['s_x']:.3f} | {r['surrogate_calm_R2']:.3f} [{r['ci95'][0]:.3f}, {r['ci95'][1]:.3f}] | "
                     f"{r['bound_window_avg']:.3f} / {r['bound_day_T']:.3f} / {r['bound_steady']:.3f} | {r['gap_point_minus_window_avg']:+.3f} |")
        L.append("")
    if "ladder" in res:
        lad = res["ladder"]
        L += ["## The calm-channel ladder on the Phase-5 state", "",
              "| rung | arm | population | n paths | level-free R²(x) [CI] | best | realised sd(x) | Gaussian bound (window) | excess over bound | increment |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for r in lad["rungs"]:
            inc = "—" if r.get("increment_over_previous") is None else f"{r['increment_over_previous']:+.4f}"
            L.append(f"| {r['rung']} | {r['label']} | {r['population']} | {r['n_paths']} | {r['levelfree_R2']:.4f} [{r['ci95'][0]:.4f}, {r['ci95'][1]:.4f}] | "
                     f"{r['best_model']} | {r['realised_sd_x']:.4f} | {r['bound_window_avg']:.4f} | {r['excess_over_gaussian_bound']:+.4f} | {inc} |")
        L += ["", lad["reading"], ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="bound,sweep,ladder")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--n-boot", type=int, default=500)
    a = ap.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)
    jp = os.path.join(OUT, "bound.json")
    res = _load(jp) if os.path.exists(jp) else {}
    res["state"] = pin_state()
    res["what"] = "E6.6 analytic half: the bound at the adopted parameters, the sweep check, the calm-channel ladder"
    stages = [s.strip() for s in a.stages.split(",")]
    if "bound" in stages:
        stage_bound(res)
    if "sweep" in stages:
        stage_sweep(res)
    if "ladder" in stages:
        stage_ladder(res, a.workers, a.n_boot)
    res["generated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _save(res)
    with open(os.path.join(OUT, "bound.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(to_markdown(res) + "\n")
    print(f"-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
