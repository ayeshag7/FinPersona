"""
E3.8 (PREREG_PHASE_3.md section 11): decompose the +0.10 of level-free calm R2(x) the generator adds over the
exact Appendix-B process (P2-18's finding), one block at a time, at the Phase-3 parameters in force. Phase 3
owns two of the four candidate channels (the GJR innovation and the jumps); the events and the sentiment
feedback remain Phase 6's, and the full-generator number is the after-state SEP audit's.

    python -m tools.phase3.e3_8_decomposition [--n-paths 200] [--T 200]

Arms (same features, estimators, GroupKFold and cluster bootstrap as E2.8 / the SEP audit):
  exact                Gaussian AR(1) x + Gaussian RW logV (the bound's model)
  + gjr                x innovations from the free-running GJR-GARCH-t of the block in force (same stationary sd)
  + jumps              exact + mean-zero jumps in the x innovation at the FIT (lambda, sigma_J)
  + gjr + jumps        both (the Phase-3 volatility block's full x innovation)

Output: docs/env_v2/generated/v2_1/e3_8/decomposition.{json,md}
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e3_8")
SEED0 = 260000


def simulate(n_paths, T, sigma_V, h, sbar, shape, nu, lam, sJ, seed, innov="gauss", jumps=False):
    from envs.v2.observables import technicals_block
    rng = np.random.default_rng(seed)
    rho = 2.0 ** (-1.0 / h)
    var_inn = sbar ** 2 + (lam * sJ ** 2 if jumps else 0.0)
    s_x = math.sqrt(var_inn / (1.0 - rho ** 2))
    burn = 300
    L = burn + T
    if innov == "gjr":
        al, gm, be = shape["alpha"], shape["gamma"], shape["beta"]
        pers = al + gm / 2 + be
        omega = sbar ** 2 * (1 - pers)
        eta = rng.standard_t(nu, (L, n_paths)) / math.sqrt(nu / (nu - 2.0))
        hv = np.full(n_paths, sbar ** 2)
        e_prev = np.zeros(n_paths)
        E = np.empty((L, n_paths))
        for t in range(L):
            lev = np.where(e_prev < 0, gm * e_prev ** 2, 0.0)
            hv = omega + al * e_prev ** 2 + lev + be * hv
            e = np.sqrt(hv) * eta[t]
            E[t] = e
            e_prev = e
    else:
        E = rng.standard_normal((L, n_paths)) * sbar
    if jumps:
        E = E + np.where(rng.random((L, n_paths)) < lam, rng.normal(0.0, sJ, (L, n_paths)), 0.0)
    x = np.empty((L, n_paths))
    x[0] = rng.standard_normal(n_paths) * s_x
    for t in range(1, L):
        x[t] = rho * x[t - 1] + E[t]
    x = x[burn:]
    dlv = rng.standard_normal((T, n_paths)) * sigma_V
    logV = np.cumsum(dlv, axis=0)
    P = np.exp(logV + x) * 100.0
    V = np.exp(logV) * 100.0
    frames = []
    for i in range(n_paths):
        tech = technicals_block(P[:, i])
        frames.append(pd.DataFrame({
            "scenario": "exact", "seed": seed + i, "day": np.arange(1, T + 1), "phase": "calm", "macro": "calm",
            "V": V[:, i], "P": P[:, i], "price": P[:, i], "x": x[:, i],
            **{k: tech[k] for k in ("SMA20", "SMA50", "RSI14", "MACD", "MACD_signal",
                                    "trend_strength", "trend_regime")}}))
    return pd.concat(frames, ignore_index=True), s_x


def run_arm(label, n_paths, T, blk, seed, innov, jumps):
    from evaluation.leakage_audit import l2_surrogate
    from tools.phase1.kalman_bound import kalman_bound
    t0 = time.time()
    panel, s_x = simulate(n_paths, T, blk["sigma_V"], blk["h"], blk["sbar"], blk["shape"], blk["nu"],
                          blk["jump_rate"], blk["jump_sd"], seed, innov=innov, jumps=jumps)
    shown = ["price", "SMA20", "SMA50", "RSI14", "MACD", "MACD_signal", "trend_strength", "trend_regime"]
    l2 = l2_surrogate(panel, shown, control="level_free")
    rows = l2[(l2.target == "x") & (l2.phase_group == "all") & (l2.feature_set == "price_only")]
    best = rows.loc[rows["R2"].idxmax()]
    b = kalman_bound(blk["sigma_V"], s_x, blk["h"], T=T)
    return {"label": label, "innov": innov, "jumps": bool(jumps), "s_x_implied": s_x,
            "bound_window_avg_gaussian": b["window_avg"],
            "levelfree_R2": float(best["R2"]), "ci95": [float(best["R2_lo"]), float(best["R2_hi"])],
            "best_model": str(best["model"]), "realised_sd_x": float(panel["x"].std()),
            "seconds": round(time.time() - t0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-paths", type=int, default=200)
    ap.add_argument("--T", type=int, default=200)
    a = ap.parse_args()
    blk = json.load(open(os.path.join(GEN, "e3_4", "block.json"), encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    arms = [("exact (the bound's model)", "gauss", False),
            ("+ GJR-t innovation (block in force)", "gjr", False),
            ("+ jumps (FIT lambda, sigma_J)", "gauss", True),
            ("+ GJR-t + jumps (the Phase-3 x innovation)", "gjr", True)]
    res = {"what": "E3.8: the level-free calm channel decomposed one volatility block at a time at the Phase-3 "
                   "parameters in force; the events and sentiment channels remain Phase 6's, and the full "
                   "generator's number is the after-state SEP audit's.",
           "block": blk, "design": {"n_paths": a.n_paths, "T": a.T, "seed0": SEED0,
                                    "features_estimators": "identical to E2.8 / the SEP audit"},
           "arms": []}
    for i, (label, innov, jumps) in enumerate(arms):
        r = run_arm(label, a.n_paths, a.T, blk, SEED0 + 1000 * i, innov, jumps)
        res["arms"].append(r)
        print(f"{label}: R2 {r['levelfree_R2']:.3f} [{r['ci95'][0]:.3f}, {r['ci95'][1]:.3f}] "
              f"(gaussian bound {r['bound_window_avg_gaussian']:.3f}; {r['seconds']} s)", flush=True)
    base = res["arms"][0]["levelfree_R2"]
    for r in res["arms"]:
        r["delta_over_exact"] = r["levelfree_R2"] - base
    with open(os.path.join(OUT, "decomposition.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    L = ["# E3.8 the level-free channel, block by block (PREREG_PHASE_3.md section 11; P2-18's hand-off)", "",
         res["what"], "",
         "| arm | level-free calm R2(x) [95 % CI] | delta over exact | Gaussian bound (window avg) |",
         "|---|---|---|---|"]
    for r in res["arms"]:
        L.append(f"| {r['label']} | {r['levelfree_R2']:.3f} [{r['ci95'][0]:.3f}, {r['ci95'][1]:.3f}] | "
                 f"{r['delta_over_exact']:+.3f} | {r['bound_window_avg_gaussian']:.3f} |")
    L += ["", "The Gaussian bound applies exactly to the first arm only; for the others it is the reference "
          "line a NON-Gaussian innovation may legitimately exceed (Appendix B's own caveat). The full "
          "generator's calm number (events + sentiment on top) is in the after-state audit; the remaining gap "
          "between the last arm and that number is the events-plus-sentiment share, Phase 6's to characterise."]
    with open(os.path.join(OUT, "decomposition.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("written", OUT)


if __name__ == "__main__":
    main()
