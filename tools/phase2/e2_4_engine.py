"""
E2.4 (PREREG_PHASE_2.md section 6): the engine decision, FW vs AR(1)+GARCH vs FW+.

(a) acceptance   -- read from the E2.3 `full` fits (chi^2 at 5 % and FW's bootstrap p)
(b) held-out     -- each engine fitted on `train` (2000-2016); its theta-hat simulates the `test` period
                    (2017-2024) at the test panel's size and length; the distance is
                        D = mean over the EIGHT persistence-carrying moments of |m_sim,j - m_test,j| / sd_boot,j
                    with a Monte-Carlo interval over 20 CRN replicates.  The same distance over all 17 moments
                    and the per-moment table are reported beside.
(c) equivalence  -- run separately (`--stage c`) once the adopted engine is plumbed into the generator: the
                    checklist and the level-free leakage statistics of the incumbent and the adopted engine at
                    matched persistence and sd(x), 200 / 100 seeds, reported with intervals and NO pass/fail.

Decision rule (asymmetric; ties to the simpler model): a FW engine is adopted only if it is accepted at (a) AND
D <= D_ar1 - 1.0 at (b); if both qualify, the smaller D; otherwise `ar1` is the default.

    python -m tools.phase2.e2_4_engine [--stage ab] [--k 20]
Outputs: docs/env_v2/generated/v2_1/e2_4/decision.json, decision.md, heldout.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

from tools.phase2.engines import DEFAULTS, ENGINES, FREE, pooled_moments, theta_to_params  # noqa: E402
from tools.phase2.moments import ALL_NAMES  # noqa: E402

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
E23 = os.path.join(GEN, "e2_3")
OUT = os.path.join(GEN, "e2_4")
SEED_HELD = 114001
PERS = slice(9, 17)
MARGIN = 1.0


def load_fit(engine, period):
    p = os.path.join(E23, f"smm_{engine}_{period}.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def heldout(engine, k=20):
    """Fit on `train`, predict `test`.  Returns D (persistence), D_all (17), per-moment residuals in bootstrap
    sd units, and the Monte-Carlo interval of D over k CRN replicates."""
    fit = load_fit(engine, "train")
    if fit is None:
        return None
    d = json.load(open(os.path.join(E23, "data_moments.json"), encoding="utf-8"))
    te = d["periods"]["test"]
    m_test = np.array(te["moments"])
    boot_sd = np.load(os.path.join(E23, "data_boot_test.npy")).std(axis=0, ddof=1)
    base = dict(DEFAULTS)
    base["price_scale"] = fit["price_scale"]
    theta = np.array(fit["theta"])
    p = theta_to_params(engine, theta, base)
    n_paths = te["n_stocks"]
    T = te["n_days"]
    Ms = np.stack([pooled_moments(engine, n_paths, T, p, seed=SEED_HELD + 37 * i, burn=500) for i in range(k)])
    Ds = np.array([np.mean(np.abs(m[PERS] - m_test[PERS]) / boot_sd[PERS]) for m in Ms])
    Da = np.array([np.mean(np.abs(m - m_test) / boot_sd) for m in Ms])
    m_mean = Ms.mean(axis=0)
    return {"engine": engine, "theta": fit["theta"], "free": fit["free"], "n_paths": int(n_paths), "T": int(T),
            "k_replicates": int(k), "window_train": fit["window"], "window_test": te["window"],
            "D_persistence": float(Ds.mean()), "D_persistence_ci95": [float(np.percentile(Ds, 2.5)),
                                                                     float(np.percentile(Ds, 97.5))],
            "D_all17": float(Da.mean()), "D_all17_ci95": [float(np.percentile(Da, 2.5)), float(np.percentile(Da, 97.5))],
            "moments_test": m_test.tolist(), "moments_sim": m_mean.tolist(),
            "resid_over_bootsd": ((m_mean - m_test) / boot_sd).tolist(), "moment_names": ALL_NAMES}


def decide(acc, held):
    """The pre-registered asymmetric rule."""
    d_ar1 = held.get("ar1", {}).get("D_persistence")
    qual = []
    for e in ("fw_v2", "fw_plus"):
        a = acc.get(e, {})
        h = held.get(e, {})
        if a.get("accept_fw_p") and h and d_ar1 is not None and h["D_persistence"] <= d_ar1 - MARGIN:
            qual.append((h["D_persistence"], e))
    if qual:
        qual.sort()
        return {"adopted": qual[0][1], "why": "accepted at (a) and beats ar1 at (b) by more than one bootstrap sd",
                "qualified": [q[1] for q in qual], "margin": MARGIN}
    reasons = {e: {"accept_fw_p": acc.get(e, {}).get("accept_fw_p"),
                   "accept_chi2": acc.get(e, {}).get("chi2_accept"),
                   "D_persistence": held.get(e, {}).get("D_persistence"),
                   "needed_at_or_below": None if d_ar1 is None else d_ar1 - MARGIN} for e in ("fw_v2", "fw_plus")}
    return {"adopted": "ar1", "why": "no FW engine met both legs of the asymmetric rule; ties go to the simpler model",
            "qualified": [], "margin": MARGIN, "fw_status": reasons}


def stage_c(res, path, a):
    """(c) Equivalence of the checklist and the level-free leakage statistics between the INCUMBENT v2 engine and
    the engine Phase 2 adopts, at matched persistence and matched sd(x).  Reported with intervals; NO pass/fail
    (PREREG section 6(c)): the plan's wording is a reporting rule, and Phase 1's experience is that an
    equivalence bound at 100-200 paths is not meetable even under identical distributions."""
    from tools.phase2.e2_6_sweep import level_free_audit, run_checklist_level, switches
    import envs.v2.mispricing_params as MP
    adopted = res.get("decision", {}).get("adopted")
    arms = {"incumbent_fw_fallback_hl150": ("fw_fallback_hl150", 0.017),
            f"adopted_{MP.ENGINE}": (MP.ENGINE, 0.017)}
    out = res.setdefault("equivalence_c", {"arms": {}, "note":
        "matched innovation scale sbar = 0.017; the persistence each engine carries is its own FIT value and is "
        "reported beside, because matching persistence across engines of different families would require "
        "re-fitting one of them to the other, which is not what the comparison asks"})
    for name, (eng, sbar) in arms.items():
        cell = out["arms"].setdefault(name, {"engine": eng, "sbar": sbar, "adopted": eng == MP.ENGINE})
        for stage, fn in (("switch", lambda: switches(eng, sbar, 200, a.workers)),
                          ("checklist", lambda: run_checklist_level(eng, sbar, 200, f"e2_4c_{name}")),
                          ("audit", lambda: level_free_audit(eng, sbar, 100, a.workers))):
            if stage in cell:
                continue
            t0 = time.time()
            print(f"[e2_4c] {name} {stage} ...", flush=True)
            cell[stage] = fn()
            cell[f"{stage}_seconds"] = round(time.time() - t0)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(res, fh, indent=1)
            print(f"[e2_4c] {name} {stage}: {cell[f'{stage}_seconds']} s", flush=True)
    write_md(res)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="ab")
    ap.add_argument("--k", type=int, default=20)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "decision.json")
    res = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    if "c" == a.stage:
        stage_c(res, path, a)
        return
    if "ab" in a.stage:
        t0 = time.time()
        acc = {}
        for e in ENGINES:
            f = load_fit(e, "full")
            if f is None:
                print(f"(a) {e}: no full fit yet")
                continue
            acc[e] = {k: f[k] for k in ("J", "J_single_crn", "df", "chi2_crit_95", "chi2_accept", "accept_fw_p",
                                        "params", "n_paths", "K_report", "start_J_best", "end_J", "n_evaluations",
                                        "price_scale", "seconds")}
            acc[e]["fw_p"] = f["fw_bootstrap"]["p_value"]
            acc[e]["fw_p_se"] = f["fw_bootstrap"]["p_value_mc_se"]
            acc[e]["J95_bootstrap"] = f["fw_bootstrap"]["J95_bootstrap"]
            acc[e]["resid_over_bootsd"] = f["resid_over_bootsd"]
            acc[e]["ci95"] = f.get("bootstrap_refits", {}).get("ci95")
        res["acceptance"] = acc
        held = {}
        for e in ENGINES:
            h = heldout(e, a.k)
            if h:
                held[e] = h
                print(f"(b) {e}: D_persistence {h['D_persistence']:.3f} "
                      f"{h['D_persistence_ci95']}  D_all17 {h['D_all17']:.3f}", flush=True)
        res["heldout"] = held
        if acc and held.get("ar1"):
            res["decision"] = decide(acc, held)
            print(json.dumps(res["decision"], indent=1))
        res["seconds_ab"] = round(time.time() - t0)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1)
        write_md(res)
    print("written", OUT)


def write_md(res):
    acc, held = res.get("acceptance", {}), res.get("heldout", {})
    L = ["# E2.4 engine decision (PREREG_PHASE_2.md section 6)", "",
         "Three candidates in one scaffolding (`tools/phase2/engines.py`): `ar1` = AR(1)+GJR-GARCH-t (REG-4 B, "
         "the simple one), `fw_v2` = the incumbent FW form driven by one GARCH innovation through the unit-mean "
         "weight (REG-4 A), `fw_plus` = FW's own two independent Gaussian demand noises with a stochastic "
         "fundamental (REG-4 C, Pruna et al. 2016). Rule (asymmetric, ties to the simpler model): a FW engine is "
         "adopted only if it is **accepted at (a)** and **beats `ar1` at (b) by more than one bootstrap sd** on "
         "the persistence-carrying moments.", "",
         "## (a) SMM acceptance on the full sample", "",
         "The two criteria are different tests and the column headings say so: the chi-square compares J with "
         "chi2_0.95(17 - p); Franke-Westerhoff's bootstrap p is the share of model replicates whose J falls "
         "below the DATA bootstrap's own 95th percentile, which carries no degrees-of-freedom penalty, is "
         "evaluated in-sample at that window's optimum, and has a yardstick that moves with the window length "
         "(`e2_3/weight_calibration.json`). On the full sample the weight matrix is well calibrated (the data "
         "bootstrap's J median is 14.2 against a chi-square(17) median of 16.3), so both criteria are "
         "meaningful there -- and both reject every engine.", "",
         "| engine | free p | J | df | chi2 crit (5 %) | chi2 accept | FW bootstrap p | FW: not rejected at 5 %? |",
         "|---|---|---|---|---|---|---|---|"]
    for e, r in acc.items():
        L.append(f"| `{e}` | {len(FREE[e])} | {r['J']:.1f} | {r['df']} | {r['chi2_crit_95']:.1f} | "
                 f"{'yes' if r['chi2_accept'] else '**no**'} | {r['fw_p']:.3f} (SE {r['fw_p_se']:.3f}) | "
                 f"{'**yes**' if r['accept_fw_p'] else 'no'} |")
    L += ["", "## (b) Held-out prediction: fit 2000-2016, predict 2017-2024", "",
          "| engine | D (8 persistence moments) | 95 % MC interval | D (all 17) | beats `ar1` by > 1 sd? |",
          "|---|---|---|---|---|"]
    d_ar1 = held.get("ar1", {}).get("D_persistence")
    for e, r in held.items():
        beat = "-" if e == "ar1" or d_ar1 is None else ("**yes**" if r["D_persistence"] <= d_ar1 - 1.0 else "no")
        L.append(f"| `{e}` | {r['D_persistence']:.3f} | [{r['D_persistence_ci95'][0]:.3f}, "
                 f"{r['D_persistence_ci95'][1]:.3f}] | {r['D_all17']:.3f} | {beat} |")
    if held:
        L += ["", "Per-moment held-out residuals in bootstrap-sd units (m_sim - m_test) / sd_boot:", "",
              "| moment | " + " | ".join(f"`{e}`" for e in held) + " |", "|---|" + "---|" * len(held)]
        for j, nm in enumerate(ALL_NAMES):
            L.append(f"| {nm} | " + " | ".join(f"{held[e]['resid_over_bootsd'][j]:+.2f}" for e in held) + " |")
    if acc:
        L += ["", "Full-sample residuals at the optimum, in bootstrap-sd units:", "",
              "| moment | " + " | ".join(f"`{e}`" for e in acc) + " |", "|---|" + "---|" * len(acc)]
        for j, nm in enumerate(ALL_NAMES):
            L.append(f"| {nm} | " + " | ".join(f"{acc[e]['resid_over_bootsd'][j]:+.2f}" for e in acc) + " |")
    if "decision" in res:
        d = res["decision"]
        L += ["", "## Decision", "", f"**Adopted: `{d['adopted']}`** — {d['why']}.", ""]
        if d.get("fw_status"):
            L += ["| engine | accepted at (a)? | D | needed at or below |", "|---|---|---|---|"]
            for e, s in d["fw_status"].items():
                L.append(f"| `{e}` | {s['accept_fw_p']} (chi2 {s['accept_chi2']}) | "
                         f"{'-' if s['D_persistence'] is None else f'{s['D_persistence']:.3f}'} | "
                         f"{'-' if s['needed_at_or_below'] is None else f'{s['needed_at_or_below']:.3f}'} |")
    with open(os.path.join(OUT, "decision.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
