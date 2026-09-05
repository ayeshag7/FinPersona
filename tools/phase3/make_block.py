"""
Assemble the Phase-3 volatility block in force for the E3.4/E3.5 experiment stages (PREREG_PHASE_3.md
sections 3, 4, 9): E3.1's shape, E3.2's (nu, lambda, sigma_J), the section-9 refit's (sigma_V*, h*) and the
identity's sbar* -- one JSON the experiment tools read, later formalised into params/volatility.json by apply_e3.

    python -m tools.phase3.make_block [--refit smm_ar1c_full_p3.json] [--no-refit]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")


def identity_sbar(s_A, sigma_V, h, lam, sJ):
    rho = 2.0 ** (-1.0 / h)
    s2 = (s_A ** 2 - sigma_V ** 2) * (1.0 + rho) / 2.0 - lam * sJ ** 2
    if s2 <= 0:
        raise ValueError("identity infeasible")
    return math.sqrt(s2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refit", default="smm_ar1c_full_p3.json")
    ap.add_argument("--no-refit", action="store_true", help="use the Phase-2 (sigma_V, h) pending the refit")
    a = ap.parse_args()
    e31 = json.load(open(os.path.join(GEN, "e3_1", "summary.json"), encoding="utf-8"))["summary"]["A|full"]
    s_A = float(e31["uncond_sd"]["median"])
    # the PUBLISHED 3-dp medians -- exactly the shape E2.3 and the section-9 refit conditioned on
    # (tools/phase2/engines.py GARCH_E31); the full-precision medians differ in the 4th decimal only
    shape = {"alpha": round(float(e31["alpha"]["median"]), 3), "gamma": round(float(e31["gamma"]["median"]), 3),
             "beta": round(float(e31["beta"]["median"]), 3)}
    # ADDENDUM section 3: the adopted triple lives in e3_2/adoption.json (the primary fit's values with
    # recovery-informed widened intervals; both registered arms reported beside)
    jf = json.load(open(os.path.join(GEN, "e3_2", "adoption.json"), encoding="utf-8"))
    nu, lam, sJ = jf["nu"]["value"], jf["lam"]["value"], jf["sJ"]["value"]
    if a.no_refit:
        mis = json.load(open(os.path.join(ROOT, "envs", "v2", "params", "mispricing.json"), encoding="utf-8"))
        sigma_V, h = mis["structural"]["value"]["sigma_V"], mis["structural"]["value"]["h"]
        src = "Phase-2 mispricing.json (pending the section-9 refit)"
    else:
        rf = json.load(open(os.path.join(GEN, "e2_3", a.refit), encoding="utf-8"))
        sigma_V, h = rf["params"]["sigma_V"], rf["params"]["h"]
        src = f"e2_3/{a.refit}"
    block = {"shape": shape, "nu": float(nu), "sigma_V": float(sigma_V), "h": float(h),
             "jump_rate": float(lam), "jump_sd": float(sJ), "s_A": s_A,
             "sbar": identity_sbar(s_A, float(sigma_V), float(h), float(lam), float(sJ)),
             "sources": {"shape_s_A": "e3_1/summary.json (set A full)",
                         "jumps": "e3_2/adoption.json (ADDENDUM section 3)", "engine": src}}
    out = os.path.join(GEN, "e3_4", "block.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(block, fh, indent=1)
    print(json.dumps(block, indent=1))


if __name__ == "__main__":
    main()
