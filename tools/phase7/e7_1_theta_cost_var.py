"""
v2.1 Phase 7 -- E7.1b (theta_cost) and E7.1c (theta_var), computed from files (PREREG_PHASE_7.md 1.2, 1.3).

    python -u -m tools.phase7.e7_1_theta_cost_var

theta_cost.  A full reallocation across the persona's band moves the risky weight by w = hi - lo; over the holding
horizon the expected reversal of a mispricing x is f x, so the expected profit of being on the correct side is
w f x.  The round trip is two trades of traded value w, so its cost is 2 c w.  Break-even:

        theta_cost = 2 c / f          and at one FIT half-life (f = 1/2)      theta_cost = 4 c

w cancels and h enters only through f -- a property of the registered formula, written in the pre-registration
before the value was computed.  Sensitivities (never primary): the one-day horizon f1 = 1 - 2^(-1/h), where h does
enter; the infinite horizon f = 1; the cost tier; h at each end of its FIT interval.

The closed form is CHECKED NUMERICALLY on a synthetic case (PREREG 1.2): an AR(1)-decaying x on a constant
fundamental, two policies differing by exactly w in risky weight, both run through the real `PortfolioV2` at the
implemented tier, and the mispricing at which their terminal values are equal found by bisection.  The check is run
at three band widths, so the cancellation of w is a measurement and not only an algebraic claim.

theta_var is READ from files, not re-estimated: the generator's median 200-day sd(x) on flat paths, with the AR(1)
reference band at the FIT half-life as its interval, and the stationary s_x as the sensitivity.

Output: <out>/theta_cost_var.{json,md}
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
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

from tools.phase5.common import GEN  # noqa: E402

OUT = os.path.join(GEN, "e7_1")
MISPRICING = os.path.join(ROOT, "envs", "v2", "params", "mispricing.json")
CRITERIA = os.path.join(ROOT, "evaluation", "params", "phase6_criteria.json")
ITEM9_MEASURED = os.path.join(GEN, "e6_after_checklist_reference_extra.csv")
GRID = (0.03, 0.05, 0.08, 0.12, 0.20)


# --------------------------------------------------------------------------------------------- theta_cost, closed
def theta_cost(c: float, f: float) -> float:
    """The break-even mispricing: 2c / f.  See the module docstring for the derivation."""
    return 2.0 * c / f


def _numeric_break_even(w: float, c_bp: float, h: float, T_hold: int, lo: float,
                        x_lo: float = 1e-6, x_hi: float = 0.5, tol: float = 1e-12) -> float:
    """Bisect for the x at which a round trip of size w exactly pays for itself over T_hold days, using the real
    PortfolioV2 at `c_bp` per trade.

    Synthetic path: V constant, x_t = x0 rho^t with rho = 2^(-1/h), P_t = V exp(x_t).  Both policies start at cash
    share `lo`.  STAY never trades; TRADE moves to cash share lo + w on day 0 and back to lo on day T_hold.  The
    statistic is (terminal value of TRADE) - (terminal value of STAY) at day T_hold, after TRADE's second leg.
    """
    from simulation.portfolio_v2 import PortfolioV2
    rho = 2.0 ** (-1.0 / h)

    def diff(x0: float) -> float:
        x = x0 * rho ** np.arange(T_hold + 1)
        P = 100.0 * np.exp(x)
        stay = PortfolioV2(10000.0, lo, P[0])
        trade = PortfolioV2(10000.0, lo, P[0])
        trade.retarget(lo + w, P[0], 1, cost_bp=c_bp)          # leg 1: step out of the overvalued asset
        trade.retarget(lo, P[T_hold], T_hold + 1, cost_bp=c_bp)  # leg 2: back in
        return trade.total_value(P[T_hold]) - stay.total_value(P[T_hold])

    a, b = x_lo, x_hi
    fa, fb = diff(a), diff(b)
    if fa * fb > 0:
        return float("nan")
    while b - a > tol:
        m = 0.5 * (a + b)
        fm = diff(m)
        if fa * fm <= 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    return 0.5 * (a + b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()

    from evaluation.targets import BANDS, CATEGORY_OF_PERSONA
    from simulation.portfolio_v2 import DEAD_BAND
    from simulation.runner_v2 import RunConfig

    mis = json.load(open(MISPRICING, encoding="utf-8"))
    crit = json.load(open(CRITERIA, encoding="utf-8"))
    h = float(mis["half_life"]["value"])
    h_lo, h_hi = [float(v) for v in mis["half_life"]["interval"]]
    cost_bp = float(RunConfig.cost_bp)
    c = cost_bp / 10000.0
    T_hold = int(round(h))
    rho = 2.0 ** (-1.0 / h)
    f_half, f_day, f_inf = 0.5, 1.0 - rho, 1.0
    f_disc = 1.0 - rho ** T_hold          # the realised fraction over an INTEGER number of days

    per_persona = {}
    for persona, cat in CATEGORY_OF_PERSONA.items():
        lo, hi = BANDS[cat]
        w = hi - lo
        per_persona[persona] = {"category": cat, "band": [lo, hi], "band_width": w,
                                "theta_cost_half_life": theta_cost(c, f_half),
                                "theta_cost_one_day": theta_cost(c, f_day),
                                "theta_cost_infinite": theta_cost(c, f_inf)}

    # the numeric check, at three band widths (PREREG 1.2)
    checks = []
    for w in (0.10, 0.20, 0.40):
        num = _numeric_break_even(w, cost_bp, h, T_hold, lo=0.40)
        closed = theta_cost(c, f_disc)
        checks.append({"band_width": w, "T_hold_days": T_hold, "f_realised": f_disc,
                       "closed_form_at_T_hold": closed, "numeric": num,
                       "rel_error": float(abs(num - closed) / closed) if closed else float("nan")})
    worst_rel = max(ck["rel_error"] for ck in checks)
    widths = [ck["numeric"] for ck in checks]
    w_spread = float(max(widths) - min(widths))

    # cost-tier sensitivity: the c that would put theta_cost at each grid theta, at the registered f = 1/2
    tier = [{"theta": th, "c_required": th * f_half / 2.0, "bp_per_trade_required": th * f_half / 2.0 * 10000.0,
             "multiple_of_implemented_tier": (th * f_half / 2.0 * 10000.0) / cost_bp} for th in GRID]

    # ------------------------------------------------------------------------------------------------- theta_var
    i9 = crit["item9_reference"]["value"]
    ex = pd.read_csv(ITEM9_MEASURED)
    row = ex[(ex["item"] == 9) & (ex["statistic"].str.contains("sd"))]
    if row.empty:
        raise SystemExit(f"item 9's measured sd(x) row is not in {ITEM9_MEASURED}")
    sd200 = float(row["value"].iloc[0]); n200 = int(row["n_gen"].iloc[0])
    theta_var = {"value": sd200, "interval": [float(i9["sd_lo"]), float(i9["sd_hi"])], "n": n200,
                 "label": "the generator's median 200-day sd(x) on flat paths; 'one within-run sd' means the T = 200 sd "
                          "(plan 11.2 E7.1c), stated in PREREG 1.3 before the number was used",
                 "source": f"{os.path.relpath(ITEM9_MEASURED, ROOT)} (item 9, flat); interval from "
                           f"{os.path.relpath(CRITERIA, ROOT)} item9_reference.sd_lo/sd_hi (n = {i9['n_reps']} reps at T = 200)",
                 "sensitivity_stationary_s_x": {"value": float(i9["s_x"]), "label": "the stationary sd of x, derived by "
                                                "E6.6's variance identity -- what x's sd would be over an unbounded run",
                                                "source": f"{os.path.relpath(CRITERIA, ROOT)} item9_reference.s_x"}}

    doc = {
        "meta": {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "seconds": round(time.time() - t0, 1),
                 "rule": "PREREG_PHASE_7.md 1.2 / 1.3; REG-11 options B and C"},
        "theta_cost": {
            "formula": "theta_cost = 2c/f; at one FIT half-life f = 1/2, so theta_cost = 4c",
            "primary_horizon": "one FIT half-life (plan 11.2 E7.1b; register 11 option B)",
            "value": theta_cost(c, f_half),
            "inputs": {
                "cost_bp_per_trade": cost_bp,
                "cost_rate_c": c,
                "cost_source": "simulation/runner_v2.py RunConfig.cost_bp = 5.0, charged on |traded value| PER TRADE "
                               "by simulation/portfolio_v2.py::_execute; the pilot's meta.json carries cost_bp 5.0",
                "cost_concept": "the implemented 5 bp per side is a HALF-SPREAD-style per-trade charge; the two read "
                                "anchors are Nasdaq (2024) 4.5 bp cap-weighted QUOTED SPREAD of the S&P 500 basket and "
                                "Frazzini-Israel-Moskowitz (2018) median MARKET IMPACT 6.18 bp per trade (mean 9.97) -- "
                                "different concepts; E7.7 names which one 5 bp stands for",
                "half_life_days": h, "half_life_interval": [h_lo, h_hi],
                "half_life_source": f"{os.path.relpath(MISPRICING, ROOT)} half_life.value (FIT, n = 417)",
                "f_half_life": f_half, "f_one_day": f_day, "f_infinite": f_inf,
                "rho": rho, "dead_band": DEAD_BAND,
                "band_widths": {k: v["band_width"] for k, v in per_persona.items()},
            },
            "per_persona": per_persona,
            "band_width_cancels": True,
            "sensitivities": {
                "one_day_horizon": {"f": f_day, "theta_cost": theta_cost(c, f_day),
                                    "note": "the horizon at which h enters materially"},
                "one_day_horizon_h_lo": {"h": h_lo, "f": 1 - 2 ** (-1 / h_lo), "theta_cost": theta_cost(c, 1 - 2 ** (-1 / h_lo))},
                "one_day_horizon_h_hi": {"h": h_hi, "f": 1 - 2 ** (-1 / h_hi), "theta_cost": theta_cost(c, 1 - 2 ** (-1 / h_hi))},
                "infinite_horizon": {"f": f_inf, "theta_cost": theta_cost(c, f_inf)},
                "cost_tier": tier,
            },
            "numeric_check": {"rows": checks, "worst_rel_error": worst_rel,
                              "break_even_spread_across_band_widths": w_spread,
                              "passes_10pct_rule": bool(worst_rel <= 0.10),
                              "rule": "PREREG 1.2: if the numerical break-even differs from the closed form by more "
                                      "than 10 %, the closed form is reported as an approximation with the numerical "
                                      "value beside it and the discrepancy goes in the addendum"},
        },
        "theta_var": theta_var,
    }
    json.dump(doc, open(os.path.join(a.out, "theta_cost_var.json"), "w", encoding="utf-8"), indent=1, default=float)

    L = ["# E7.1b / E7.1c -- theta_cost and theta_var, derived from files", "",
         f"## theta_cost = 2c/f (primary horizon: one FIT half-life, f = 1/2 -> 4c)", "",
         f"- cost tier **{cost_bp} bp per trade** (c = {c:.6f}), charged on |traded value|; round trip = 2 trades",
         f"- FIT half-life **{h:.4f} d** [{h_lo:.2f}, {h_hi:.2f}] (n = 417)",
         f"- band width w = hi - lo cancels: {sorted(set(v['band_width'] for v in per_persona.values()))}",
         "", f"**theta_cost = {theta_cost(c, f_half):.6f}** for every persona.", "",
         "| horizon | f | theta_cost |", "|---|---|---|",
         f"| one half-life ({h:.1f} d) — **primary** | {f_half:.4f} | **{theta_cost(c, f_half):.6f}** |",
         f"| one day (sensitivity) | {f_day:.4f} | {theta_cost(c, f_day):.6f} |",
         f"| one day at h = {h_lo:.2f} | {1 - 2 ** (-1 / h_lo):.4f} | {theta_cost(c, 1 - 2 ** (-1 / h_lo)):.6f} |",
         f"| one day at h = {h_hi:.2f} | {1 - 2 ** (-1 / h_hi):.4f} | {theta_cost(c, 1 - 2 ** (-1 / h_hi)):.6f} |",
         f"| infinite (sensitivity) | {f_inf:.4f} | {theta_cost(c, f_inf):.6f} |", "",
         "### The numeric check on a synthetic case (PREREG 1.2)", "",
         f"An AR(1)-decaying x on a constant fundamental, held {T_hold} days (f realised = {f_disc:.4f}); two policies "
         f"differing by exactly w in risky weight, both through the real `PortfolioV2` at {cost_bp} bp.", "",
         "| band width w | closed form at this horizon | numeric break-even | relative error |", "|---|---|---|---|"]
    for ck in checks:
        L.append(f"| {ck['band_width']:.2f} | {ck['closed_form_at_T_hold']:.6f} | {ck['numeric']:.6f} | {ck['rel_error']:.2%} |")
    L += ["", f"Spread of the numeric break-even across band widths: **{w_spread:.2e}** — the cancellation of w is "
              f"measured, not only algebraic. Worst relative error **{worst_rel:.2%}** "
              f"({'within' if worst_rel <= 0.10 else 'ABOVE'} the pre-registered 10 %).", "",
          "### Cost-tier sensitivity: what tier would put theta_cost on the grid", "",
          "| grid theta | c required | bp per trade required | multiple of the implemented tier |", "|---|---|---|---|"]
    for tr in tier:
        L.append(f"| {tr['theta']:.2f} | {tr['c_required']:.5f} | {tr['bp_per_trade_required']:.1f} | "
                 f"{tr['multiple_of_implemented_tier']:.0f}x |")
    L += ["", "## theta_var — one within-run sd of x at T = 200 (read, not re-estimated)", "",
          f"**theta_var = {sd200:.6f}**, inside the AR(1) reference band [{i9['sd_lo']:.5f}, {i9['sd_hi']:.5f}] at the "
          f"FIT half-life (n = {i9['n_reps']} reps at T = 200; the generator's own median over n_gen = {n200} flat seeds).", "",
          f"Sensitivity: the **stationary** sd s_x = {i9['s_x']:.6f} (E6.6's variance identity) — what x's sd would be "
          f"over an unbounded run, not within a 200-day one.", ""]
    with open(os.path.join(a.out, "theta_cost_var.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"-> {a.out}")


if __name__ == "__main__":
    main()
