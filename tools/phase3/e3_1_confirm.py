"""
E3.1 confirmation (PREREG_PHASE_3.md sections 1 and 3): verify the inherited numbers before building on them.

    python -m tools.phase3.e3_1_confirm

V1  recompute the set-A full-sample medians and 1,000-resample stock-bootstrap CIs from garch_fits.csv and diff
    them against e3_1/summary.json (the file the documents cite).
V2  re-derive q, the window share and the in/out rates from e1_4/panel_residuals_split.parquet and diff against
    e1_4/panel_split.json.
V3  params/mispricing.json structural == e2_3/smm_ar1_full.json; value.json sigma_V equals both.
V5  the AR(1)-family FW weight is frozen at w = 1.4225 on a generated path, and the handed-over IV carries it
    (disclosure 3 of the pre-registration).

Also computes the P25/P75 shape sensitivity sets of PREREG section 3.2 (quantiles of (alpha, gamma, nu,
persistence), beta derived) — written into the output for volatility.json to carry.

Output: docs/env_v2/generated/v2_1/e3_1/confirm.json (+ .md)
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
PARAMS = os.path.join(ROOT, "envs", "v2", "params")
N_BOOT = 1000


def _boot_median(v, seed=0, n_boot=N_BOOT):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    rng = np.random.default_rng(seed)
    meds = np.median(v[rng.integers(0, len(v), (n_boot, len(v)))], axis=1)
    return float(np.median(v)), float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))


def v1():
    fits = pd.read_csv(os.path.join(GEN, "e3_1", "garch_fits.csv"))
    summ = json.load(open(os.path.join(GEN, "e3_1", "summary.json"), encoding="utf-8"))["summary"]["A|full"]
    g = fits[(fits["set"] == "A") & (fits["period"] == "full") & fits["converged"]]
    out = {"n_converged": int(len(g)), "n_cited": summ["n_converged"], "params": {}, "agree": True}
    for k in ("alpha", "gamma", "beta", "nu", "persistence", "uncond_sd"):
        m, lo, hi = _boot_median(g[k])
        cited = summ[k]
        ok = abs(m - cited["median"]) <= 1e-9 and abs(lo - cited["ci95"][0]) < 5e-4 and abs(hi - cited["ci95"][1]) < 5e-4
        out["params"][k] = {"recomputed": [round(m, 6), round(lo, 6), round(hi, 6)],
                            "cited": [round(cited["median"], 6)] + [round(c, 6) for c in cited["ci95"]], "agree": bool(ok)}
        out["agree"] &= ok
    return out


def v2():
    sp = pd.read_parquet(os.path.join(GEN, "e1_4", "panel_residuals_split.parquet"))
    cited = json.load(open(os.path.join(GEN, "e1_4", "panel_split.json"), encoding="utf-8"))["point"]
    jump = np.abs(sp["z"].to_numpy(float)) > 4.0
    m = sp["in_window"].to_numpy(bool)
    q = float((jump & m).sum() / jump.sum())
    out = {"q_recomputed": round(q, 4), "q_cited": round(cited["q_share_of_jumps_in_window"], 4),
           "window_share_recomputed": round(float(m.mean()), 4), "window_share_cited": round(cited["window_share_of_days"], 4),
           "n_jumps": int(jump.sum()), "n_days": int(len(sp)),
           "rate_in": round(float((jump & m).sum() / m.sum()), 5), "rate_out": round(float((jump & ~m).sum() / (~m).sum()), 5)}
    out["agree"] = (abs(out["q_recomputed"] - out["q_cited"]) < 5e-4
                    and out["n_jumps"] == cited["n_jumps"] and out["n_days"] == cited["n_days"])
    return out


def v3():
    mis = json.load(open(os.path.join(PARAMS, "mispricing.json"), encoding="utf-8"))
    val = json.load(open(os.path.join(PARAMS, "value.json"), encoding="utf-8"))
    fit = json.load(open(os.path.join(GEN, "e2_3", "smm_ar1_full.json"), encoding="utf-8"))
    st = mis["structural"]["value"]
    out = {"sigma_V": [st["sigma_V"], fit["params"]["sigma_V"], val["sigma_V"]["value"]],
           "sbar": [st["sbar"], fit["params"]["sbar"]], "h": [st["h"], fit["params"]["h"]]}
    out["agree"] = (st["sigma_V"] == fit["params"]["sigma_V"] == val["sigma_V"]["value"]
                    and st["sbar"] == fit["params"]["sbar"] and st["h"] == fit["params"]["h"])
    return out


def v5():
    from envs.synthetic_market import SyntheticMarketEnv
    env = SyntheticMarketEnv("flat", 50, 780050)
    d = env.data[env.data["asset"] == 0]
    w = d["fw_weight"].to_numpy(float)
    iv = d["implied_volatility"].to_numpy(float)
    fvar = d["fvar21"].to_numpy(float)
    sv = float(env.cfg.sigma_V)
    # the handed-over construction: iv = sqrt(252 (sigma_V^2 + w^2 fvar)) * (1 + prem) * 100, prem 0.20/0.35
    iv_w1 = np.sqrt(252.0 * (sv ** 2 + 1.0 ** 2 * fvar)) * 1.20 * 100.0
    return {"w_constant": bool(np.allclose(w, w[0])), "w_value": float(w[0]),
            "w_expected": round((0.5 * 0.758 + 0.5 * 2.087) / 1.0, 6),
            "median_iv": float(np.median(iv)), "median_iv_if_w_were_1": float(np.median(np.maximum(iv_w1, 12.0))),
            "note": "constant factor, no leak; removed by E3.5's construction"}


def sensitivity_sets():
    fits = pd.read_csv(os.path.join(GEN, "e3_1", "garch_fits.csv"))
    g = fits[(fits["set"] == "A") & (fits["period"] == "full") & fits["converged"]]
    out = {}
    for name, q in (("P25", 25), ("P75", 75)):
        a = float(np.percentile(g["alpha"], q))
        gm = float(np.percentile(g["gamma"], q))
        nu = float(np.percentile(g["nu"], q))
        pers = float(np.percentile(g["persistence"], q))
        beta = pers - a - gm / 2.0
        out[name] = {"alpha": round(a, 4), "gamma": round(gm, 4), "beta": round(beta, 4), "nu": round(nu, 3),
                     "persistence": round(pers, 4),
                     "construction": "quantiles of (alpha, gamma, nu, persistence); beta derived = pers - alpha - gamma/2"}
    raw_p75 = {k: float(np.percentile(g[k], 75)) for k in ("alpha", "gamma", "beta")}
    out["raw_P75_persistence_note"] = round(raw_p75["alpha"] + raw_p75["gamma"] / 2 + raw_p75["beta"], 4)
    return out


def main():
    t0 = time.time()
    out = {"V1": v1(), "V2": v2(), "V3": v3(), "V5": v5(), "shape_sensitivity_sets": sensitivity_sets(),
           "seconds": round(time.time() - t0)}
    os.makedirs(os.path.join(GEN, "e3_1"), exist_ok=True)
    with open(os.path.join(GEN, "e3_1", "confirm.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
