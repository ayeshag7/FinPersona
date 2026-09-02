"""
Apply Phase 2's decisions to the generator (PREREG_PHASE_2.md section 10).

Writes `envs/v2/params/mispricing.json` -- the engine in force and its structural parameters, each entry
carrying value / label / source / date / interval / n / survivor-vs-literature gap, as `value.json` does -- and
updates `value.json`'s `sigma_V` with the value E2.3 fitted (D3 = (b): sigma_V was left free in the SMM and is
applied here, once, jointly identified with the engine's pull rate).

Applying either file changes every path, so the execution-order rule follows: re-freeze, regenerate the path
hashes, re-run the checklist and the level-free audits on the state handed over (`tools/phase2/after_state.py`).

    python -m tools.phase2.apply_e2 [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tools.phase2.engines import DEFAULTS as ENG_DEFAULTS  # noqa: E402

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
PARAMS = os.path.join(ROOT, "envs", "v2", "params")
TODAY = date.today().isoformat()
SURVIVOR_NOTE = ("set A has no delistings by construction (REG-15), so the panel's tails and unconditional "
                 "variance understate the full universe; every moment this fit targets inherits that gap and "
                 "the WRDS re-run (D1 = C) is the remedy the plan foresees")


def jload(p):
    return json.load(open(p, encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    dec = jload(os.path.join(GEN, "e2_4", "decision.json"))
    adopted = dec["decision"]["adopted"]
    fit = jload(os.path.join(GEN, "e2_3", f"smm_{adopted}_full.json"))
    repro = jload(os.path.join(GEN, "e2_1", "fw_repro.json"))
    dm = jload(os.path.join(GEN, "e2_3", "data_moments.json"))
    ci = fit.get("bootstrap_refits", {}).get("ci95", {})
    n_ref = fit.get("bootstrap_refits", {}).get("n")
    n_stocks = dm["periods"]["full"]["n_stocks"]
    engine_name = {"ar1": "ar1_fit", "fw_v2": "fw_smm_v21", "fw_plus": "fw_plus_smm_v21"}[adopted]

    # persistence in the units the documents report
    if adopted == "ar1":
        hl_pull = fit["params"]["h"]
        hl_kind = "AR(1) half-life from rho = 2^(-1/h)"
        chartist = None
    else:
        e22 = jload(os.path.join(GEN, "e2_2", "persistence.json"))
        e = e22["estimators"]["C"]["engines"][adopted]["full"]
        hl_pull = e["half_life_days"]
        hl_kind = "pull-rate half-life ln2 / (mu n_bar phi) at the fitted engine's realised n_bar"
        chartist = e.get("chartist_share_fitted")

    def entry(value, label, source, interval=None, n=None, gap=None, **extra):
        d = {"value": value, "label": label, "source": source, "date": TODAY,
             "interval": interval, "n": n, "survivor_vs_literature_gap": gap}
        d.update(extra)
        return d

    mis = {
        "_note": "v2.1 Phase 2 mispricing-engine parameters in force (PREREG_PHASE_2.md; PHASE_2_REPORT.md). "
                 "Every entry: value + provenance. The engine name here is the engine that RUNS; "
                 "get_metadata()['engine_used'] must equal it (test_engine_named_honestly).",
        "engine": entry(engine_name, f"FIT (E2.4 decision: {dec['decision']['why']})",
                        "e2_4/decision.json, e2_3/smm_%s_full.json" % adopted,
                        n=n_stocks, gap=SURVIVOR_NOTE, candidates=list(dec["acceptance"].keys()),
                        family=adopted),
        "price_scale": entry(1.0 if repro["armA"]["scale1"]["confirmed"] else 100.0,
                             "LIT bug fix (E2.1): FW 2012 works in natural-log price units; the convention that "
                             "reproduces their published joint moment coverage ratio is price_scale = 1",
                             "e2_1/fw_repro.md; FW 2012 eqs (1), (5)-(7), Table 4",
                             interval=repro["armA"]["scale1"]["joint_mcr_ci95_pct"], n=200,
                             published_joint_mcr_pct=repro["armA"]["scale1"]["fw_table4_joint_pct"],
                             measured_joint_mcr_pct=repro["armA"]["scale1"]["joint_mcr_pct"]),
        "structural": entry({**{k: float(v) for k, v in fit["params"].items()},
                             **{k: float(ENG_DEFAULTS[k]) for k in ("beta", "mu", "w_bar")
                                if adopted != "ar1"},
                             **({"sigma_f": float(ENG_DEFAULTS["sigma_f"]),
                                 "sigma_c": float(ENG_DEFAULTS["sigma_c"])}
                                if adopted == "fw_v2" and "sigma_f" not in fit["params"] else {})},
                            "FIT (E2.3 SMM: FW's nine moments plus the persistence-carrying VR(20-500) and the "
                            "ACF of log(P/SMA250); block-bootstrap weight matrix stored to disk)",
                            "e2_3/smm_%s_full.json" % adopted, interval=ci or None,
                            n=n_stocks, gap=SURVIVOR_NOTE,
                            free_parameters=list(fit["free"]),
                            fixed_in_the_fit="beta = 1 and mu = 0.01 are FW's normalisations; w_bar is the "
                                             "v2 reference unit-mean weight constant 0.76113 -- inside the fit "
                                             "only the product w_bar x sbar is identified, so the engine keeps "
                                             "this constant rather than re-deriving it from a fresh pilot",
                            n_bootstrap_refits=n_ref, J=fit["J"], df=fit["df"],
                            chi2_crit_95=fit["chi2_crit_95"], chi2_accept=fit["chi2_accept"],
                            fw_bootstrap_p=fit["fw_bootstrap"]["p_value"], accept_fw_p=fit["accept_fw_p"],
                            n_paths_per_evaluation=fit["n_paths"], K_report=fit["K_report"]),
        "applied": entry(
            {"engine": engine_name, "price_scale": 1.0 if repro["armA"]["scale1"]["confirmed"] else 100.0,
             "half_life_days": hl_pull, "sigma_V_to_value_json": float(fit["params"]["sigma_V"])},
            "WHICH fitted quantities actually govern the generator. The engine name, the units convention, the "
            "half-life and sigma_V are applied. **sbar (the unconditional x-innovation scale) is RECORDED AND "
            "NOT APPLIED**: it is a volatility parameter and Phase 3 owns it (PLAN section 7, E3.1 adopts the "
            "per-stock median unconditional sd; E3.4 decides how the regime enters the variance). Applying "
            "E2.3's sbar here would set a Phase-3 parameter from a Phase-2 fit, and the generator keeps v2's "
            "CAL 0.017 until Phase 3 re-fits it. The consequence is stated in PHASE_2_REPORT.md section 4: the "
            "engine's stationary sd(x) in the handed-over generator is the one E2.6 measures at sbar = 0.017, "
            "not the one the SMM fitted.",
            "e2_3/smm_%s_full.json; PLAN section 7" % adopted, n=n_stocks,
            sbar_fitted_not_applied=float(fit["params"]["sbar"]),
            sbar_in_force=0.017,
            sbar_in_force_source="envs/v2/garch.py GJRParams.sbar (CAL, v2 E1 calibration); Phase 3 re-fits"),
        "half_life": entry(hl_pull, "FIT (E2.3, the engine's own persistence)",
                           "e2_3/smm_%s_full.json; e2_2/persistence.md" % adopted,
                           interval=(ci or {}).get("h"), n=n_stocks, gap=SURVIVOR_NOTE, kind=hl_kind),
        "garch_shape": entry(dict(alpha=0.027, gamma=0.058, beta=0.932, df=4.86),
                             "FIT (E3.1, set-A full-sample per-stock medians; held FIXED inside the SMM, only "
                             "the unconditional scale sbar was free)",
                             "e3_1/summary.md, garch_fits.csv", n=417,
                             gap="set B (shorter, partly delisted names) has fatter tails (nu 4.33 vs 4.86) and "
                                 "higher variance (0.0243 vs 0.0218): the survivor panel understates both"),
        "moments": entry(dm["moment_names"],
                         "DESIGN (PREREG_PHASE_2.md section 4.1): FW 2012's nine plus eight "
                         "persistence-carrying moments, pooled as the cross-sectional mean over set A",
                         "e2_3/data_moments.md",
                         n=n_stocks, weight_matrix="joint stock x block bootstrap, 500 resamples, blocks "
                         "250/750/1250 d by moment group (FW 2012 Appendix A2 extended), 10 % ridge toward the "
                         "diagonal; stored as e2_3/weight_<period>.npy"),
        "estimator_table": entry("e2_5/hl_table.md",
                                 "DESIGN (E2.5): the naive-vs-median-unbiased half-life lookup used whenever a "
                                 "half-life is quoted at a finite horizon", "e2_5/hl_table.json", n=200),
    }
    if chartist is not None:
        mis["chartist_share"] = entry(chartist, "FIT (E2.3, realised mean chartist share of the fitted engine)",
                                      "e2_2/persistence.json", n=n_stocks, gap=SURVIVOR_NOTE)
    out = os.path.join(PARAMS, "mispricing.json")
    print(json.dumps({k: (v["value"] if isinstance(v, dict) else v) for k, v in mis.items()}, indent=1))
    if a.dry_run:
        print("(dry run: nothing written)")
        return
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(mis, fh, indent=1)
    print("written", out)

    # ---- D3 = (b): apply the fitted sigma_V to value.json
    vp = os.path.join(PARAMS, "value.json")
    v = jload(vp)
    prev = dict(v["sigma_V"])
    sv = float(fit["params"]["sigma_V"])
    v["sigma_V"] = {
        "value": sv,
        "label": "FIT (E2.3, this phase): sigma_V was a FREE parameter of the SMM and is jointly identified with "
                 "the engine's pull rate (D3 = (b), the option the execution prompt defaults to when the blank "
                 "is empty). Phase 1's estimator-C value (0.01957 [0.01892, 0.02036]) is recorded beside; the "
                 "value applied here is the one the engine that actually runs was fitted with.",
        "source": "e2_3/smm_%s_full.json; e2_4/decision.json" % adopted,
        "date": TODAY,
        "interval": (ci or {}).get("sigma_V"),
        "n": n_stocks,
        "phase1_estimator_C": prev.get("fitted"),
        "previous": {"value": prev["value"], "label": prev["label"][:120] + " ..."},
    }
    with open(vp, "w", encoding="utf-8") as fh:
        json.dump(v, fh, indent=1)
    print(f"value.json: sigma_V {prev['value']} -> {sv} (execution-order rule now applies: re-freeze, "
          f"regenerate hashes, re-run the checklist and the level-free audits)")


if __name__ == "__main__":
    main()
