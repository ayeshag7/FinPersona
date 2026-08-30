"""
Appendix B of the v2.1 plan: the analytic level-free price-only bound on R^2(x).

Model: log P_t = log V_t + x_t, log V a random walk (variance sigma_V^2 per day; the drift is a known constant and drops
out), x_t = rho x_{t-1} + eta_t with rho = 2^(-1/h) and var(eta) = s_x^2 (1 - rho^2). A level-free reader observes only
returns r_t = x_t - x_{t-1} + sigma_V z_t. State (x_t, x_{t-1}); the steady-state Kalman filter gives the minimum-MSE
estimate of x_t from the return history, hence the maximal R^2(x) = 1 - P_filt / s_x^2 any level-free reader of the price
path can reach (linear-Gaussian bound; LOG section 3 reproduced this to three decimals on 27 Aug 2026).

Conventions: the reader starts from the stationary prior and observes T returns r_1 .. r_T inside the window; R^2(t) is
the filtered value after the t-th update; "window average" = mean of R^2(t) over t = 1..T; "day T" = R^2(T); "steady
state" = the fixed point of the Riccati recursion. (PREREG_PHASE_1.md section 8 described day 1 as the prior with T - 1
returns; that convention gave 0.136 / 0.234 where LOG section 3 has 0.137 / 0.235 -- the pre-registered verification
rule "reproduce LOG section 3 to three decimals" selects the T-return convention used here; steady state is identical.)

    python -m tools.phase1.kalman_bound            # verification against LOG section 3 and the E1.3 grid table
"""
from __future__ import annotations

import json
import os
import sys
from typing import Dict, Tuple

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

LOG_TABLE = [  # (sigma_V, s_x, h, window avg, day 200, steady) -- LOG section 3, reproduced independently on 27 Aug 2026
    (0.006, 0.13, 150, 0.137, 0.235, 0.396), (0.006, 0.165, 150, 0.150, 0.260, 0.477),
    (0.010, 0.13, 150, 0.097, 0.161, 0.231), (0.020, 0.13, 150, 0.041, 0.065, 0.082), (0.030, 0.13, 150, 0.021, 0.033, 0.040)]


def kalman_bound(sigma_V: float, s_x: float, h: float, T: int = 200) -> Dict[str, float]:
    rho = 2.0 ** (-1.0 / h)
    q = s_x ** 2 * (1 - rho ** 2)
    F = np.array([[rho, 0.0], [1.0, 0.0]]); Q = np.array([[q, 0.0], [0.0, 0.0]])
    H = np.array([[1.0, -1.0]]); R = sigma_V ** 2
    P = np.array([[s_x ** 2, rho * s_x ** 2], [rho * s_x ** 2, s_x ** 2]])   # stationary prior for (x_t, x_{t-1})
    r2 = []
    def step(P):
        Pm = F @ P @ F.T + Q
        S = float((H @ Pm @ H.T).item()) + R
        K = Pm @ H.T / S
        return (np.eye(2) - K @ H) @ Pm
    for _ in range(T):
        P = step(P)
        r2.append(1 - P[0, 0] / s_x ** 2)
    Pss = P
    for _ in range(20000):
        Pn = step(Pss)
        if abs(Pn[0, 0] - Pss[0, 0]) < 1e-14:
            Pss = Pn; break
        Pss = Pn
    return {"sigma_V": sigma_V, "s_x": s_x, "h": h, "T": T, "window_avg": float(np.mean(r2)), "day_T": float(r2[-1]),
            "steady_state": float(1 - Pss[0, 0] / s_x ** 2)}


def verify(tol: float = 5e-4) -> Tuple[bool, list]:
    rows = []
    ok = True
    for sv, sx, h, a, d, s in LOG_TABLE:
        b = kalman_bound(sv, sx, h)
        good = abs(b["window_avg"] - a) <= tol and abs(b["day_T"] - d) <= tol and abs(b["steady_state"] - s) <= tol
        ok &= good
        rows.append({**b, "log_window_avg": a, "log_day_T": d, "log_steady": s, "match": good})
    return ok, rows


def grid_table(sigmas=(0.004, 0.006, 0.010, 0.015, 0.020), sxs=(0.10, 0.13, 0.165, 0.175, 0.20), hs=(150,), T: int = 200):
    return [kalman_bound(sv, sx, h, T) for h in hs for sv in sigmas for sx in sxs]


if __name__ == "__main__":
    ok, rows = verify()
    for r in rows:
        print(f"sigma_V {r['sigma_V']:.3f} s_x {r['s_x']:.3f}: {r['window_avg']:.3f} / {r['day_T']:.3f} / {r['steady_state']:.3f}"
              f"  (LOG {r['log_window_avg']:.3f} / {r['log_day_T']:.3f} / {r['log_steady']:.3f}) {'OK' if r['match'] else 'MISMATCH'}")
    print("verification", "PASSED" if ok else "FAILED")
    out = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "kalman_bound_verification.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"passed": ok, "tolerance": 5e-4, "rows": rows}, fh, indent=1)
