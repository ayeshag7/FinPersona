"""
The FIT parameter sections of the six observable blocks, assembled from the E5.1-E5.6 result files
(PREREG_PHASE_5.md sections 4-9), used by BOTH the arm definitions (tools/phase5/e5_arms.py) and the parameter-file
writer (tools/phase5/apply_e5.py) -- so an arm and the deployed file cannot carry different numbers for the same design.

    sections(decisions) -> {"multiple": {...}, "eps": {...}, "dividend": {...}, "analyst": {...}, "sentiment": {...},
                            "volume": {...}}   (the `value` blocks of observables.json)

`decisions` names a design per block (and the analyst sd, the multiple width, the sentiment link size, the D10
rendering); every number inside comes from the generated files, never from this module.
"""
from __future__ import annotations

import json
import math
import os
from typing import Dict, Optional

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
SENT_SD_REF = 0.35
ANALYST_LIT_ANCHOR = 0.45 * math.sqrt(math.pi / 2.0)        # E|u| = sd sqrt(2/pi) with E|u| = 0.45 -> 0.564


def _load(rel):
    p = os.path.join(GEN, rel)
    if not os.path.exists(p):
        raise FileNotFoundError(f"{rel} has not been generated; the section that needs it cannot be built")
    return json.load(open(p, encoding="utf-8"))


def s_raw_for_sd(target_sd: float = SENT_SD_REF, n: int = 400000, seed: int = 580001) -> float:
    """DESIGN rendering constant: the scale S with sd(tanh(S z)) = target_sd for z ~ N(0, 1)."""
    z = np.random.default_rng(seed).standard_normal(n)
    lo, hi = 0.05, 2.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if np.tanh(mid * z).std() < target_sd:
            lo = mid
        else:
            hi = mid
    return float(0.5 * (lo + hi))


def sections(decisions: Optional[Dict] = None) -> Dict[str, Dict]:
    d = {"multiple": "A", "width": "P10-P90", "eps": "v21", "dividend": "v21", "dividend_field": "shown",
         "analyst": "C", "analyst_sd": ANALYST_LIT_ANCHOR, "analyst_field": "shown", "sentiment": "A",
         "sentiment_link": "full", "volume": "A"}
    d.update(decisions or {})
    def _try(rel):
        try:
            return _load(rel)
        except FileNotFoundError:
            return None
    e51 = _try("e5_1/multiple.json"); e52 = _try("e5_2/eps.json"); e53 = _try("e5_3/dividends.json")
    e55 = _try("e5_5/sentiment.json"); e56 = _try("e5_6/volume.json")
    out = {}
    # ---- multiple (E5.1); the net-of-noise correction needs E5.2's s_EPS (0 until it exists, and flagged)
    s_eps = float(e52["log_seasonal_change"]["s_EPS_from_robust_sd"]["value"]) if e52 else 0.0
    if e51 is None:
        multiple = None
    else:
      var_within = float(e51["dispersion"]["sd_within"]) ** 2
      sd_x = float(e51["engine"]["sd_x_stationary"])
      s_w2 = var_within - sd_x ** 2 - s_eps ** 2 / 4.0
      multiple = {"design": d["multiple"], "width": d["width"],
                  "grid_A": {w: v["grid"] for w, v in e51["design_grids"]["A"].items()},
                  "grid_B_log_between": {w: v["grid_log"] for w, v in e51["design_grids"]["B_between"].items()},
                  "rho_q": float(e51["persistence"]["rho_q_quarterly"]["median"]),
                  "rho_d": float(e51["persistence"]["rho_d_daily_equivalent"]["median"]),
                  "s_w": float(math.sqrt(max(s_w2, 0.0))), "s_w_net_variance": float(s_w2),
                  "sd_within_gross": float(e51["dispersion"]["sd_within"]), "sd_x_engine": sd_x, "s_eps_used": s_eps}
    # ---- eps (E5.2)
    if e52 is None or e51 is None:
        eps = None
    else:
      lp = e52["loss_process"]; al = e52["announcement_lags"]["announcement_8k"]
      eps = {"design": d["eps"], "s_eps": s_eps, "p_loss": float(lp["p_loss"]["value"]),
           "p_loss_given_loss": float(lp["p_loss_given_loss"]["value"]),
           "p_loss_given_profit": float(lp["p_loss_given_profit"]["value"]),
           "loss_size_grid": lp["size"]["grid"], "pe_cap": float(e51["pe_cap_p99"]["value"]),
           "lag_grid_td": al["grid_td"], "lag_p10_p50_p90_td": [al["p10_td"]["value"], al["p50_td"]["value"], al["p90_td"]["value"]],
           "nm_share_data": float(e52["nm_frequency"]["share_ttm_nonpositive"]["value"])}
    # ---- dividend (E5.3)
    if e53 is None:
        dividend = None
    else:
      st = e53["stickiness"]
      dividend = {"design": d["dividend"], "field": d["dividend_field"], "c_speed": float(st["c_speed"]["value"]),
                "tau": float(st["tau_target_payout"]["value"]),
                "payer_share": float(e53["payer_share"]["payer_share_of_set_A"]),
                "payout_median_data": float(e53["payout"]["median"]["value"])}
    # ---- analyst (E5.4)
    analyst = {"design": d["analyst"], "sd": float(d["analyst_sd"]), "rho": 0.95, "update_days": 5, "field": d["analyst_field"],
               "lit_anchor_sd": ANALYST_LIT_ANCHOR, "bracket_phase9": [0.30, 0.45, 0.60]}
    # ---- sentiment (E5.5): design A's parameters are the 200-day WINDOW medians (like-for-like), C's the 40-week ones
    if e55 is None or "window_200d" not in e55["loadings_market_daily"]:
        sentiment = None
    else:
      W = e55["loadings_market_daily"]["window_200d"]; Wa = e55["aaii_weekly"]["window_fits_40w"]
      val = e55["valuation_link_monthly"]["trailing_120m_mean"]
      c_full = float(val["coef_per_sd_raw_daily"])
      c_val = c_full if d["sentiment_link"] == "full" else 0.5 * c_full
      sentiment = {"design": d["sentiment"], "rho": float(W["rho"]["median"]), "b0": float(W["b0_per_sd"]["median"]),
                 "b1": float(W["b1_per_sd"]["median"]), "sd_e": float(W["sd_e_per_sd"]["median"]),
                 "s_raw": s_raw_for_sd(), "c_val": float(c_val), "c_val_full": c_full, "link_size": d["sentiment_link"],
                 "rho_w": float(Wa["rho"]["median"]), "b0_w": float(Wa["b0_per_sd"]["median"]),
                 "b1_w": float(Wa["b1_per_sd"]["median"]), "sd_e_w": float(Wa["sd_e_per_sd"]["median"]), "update_days": 5,
                 "full_sample_fit": {k: e55["loadings_market_daily"]["full"][k] for k in ("rho", "b0_per_sd_raw", "b1_per_sd_raw", "sd_resid_per_sd_raw")}}
    # ---- volume (E5.6)
    if e56 is None:
        volume = None
    else:
      A = e56["design_A"]; B = e56["design_B"]
      if d["volume"] == "B":
          volume = {"design": "B", "rho_v": float(B["rho_v"]["median"]), "beta_absr": float(B["beta_absr_per_sd_z"]["median"]),
                    "sd_e": float(B["sd_e"]["median"]), "beta_ru": float(B["beta_ru_per_unit_pos_ret252"]["median"])}
      else:
          volume = {"design": d["volume"], "rho_v": float(A["rho_v"]["median"]), "beta_absr": float(A["beta_absr_per_sd_z"]["median"]),
                    "sd_e": float(A["sd_e"]["median"]), "beta_ru": float(B["beta_ru_per_unit_pos_ret252"]["median"])}
    return {"multiple": multiple, "eps": eps, "dividend": dividend, "analyst": analyst, "sentiment": sentiment, "volume": volume}


def overrides_for(decisions: Dict) -> Dict[str, Dict]:
    """A complete obs_overrides dict for one ARM: every section fully specified (no dependence on a file)."""
    return sections(decisions)
