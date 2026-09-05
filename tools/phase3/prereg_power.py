"""
PREREG_PHASE_3.md section 10: the decidability rows that can be measured before the experiments they protect.

    python -m tools.phase3.prereg_power [--stages pa3]

PA3  generator pilot on the INCUMBENT state (30 crash seeds, delta 0.70, seeds 780001-780030): the cross-seed
     spread of the E3.4 statistics (rise time, decay half-life) measured with the shared estimator of
     tools/phase3/episodes.py, and the implied 95 % half-width of the median at the registered n = 200.
     Consequence rule (fixed): if the n = 200 half-width exceeds the empirical CI width of E3.3 (PA4), the
     mechanism verdict is undecidable and is reported so.

PA1/PA2 are measured by the E3.2 recovery run, PA4 on the panel (a data fact), PA5/PA6 inside E3.5's runs and
PA7 at the section-9 launch; each writes into the same power.json.

Output: docs/env_v2/generated/v2_1/e3_0/power.json (+ .md table)
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

from tools.phase3.episodes import drawdown_episodes, rise_decay, _rv  # noqa: E402

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e3_0")
PA3_SEEDS = range(780001, 780031)
N_TARGET = 200


def measure_crash_path(seed: int, config=None, engine=None, delta: float = 0.70):
    """Rise/decay of one generated crash path with the SHARED estimator (calm ref = pre-event days)."""
    from envs.synthetic_market import SyntheticMarketEnv
    kw = {}
    if config:
        kw["config"] = config
    if engine:
        kw["engine"] = engine
    env = SyntheticMarketEnv("crash", 200, seed, crash_discount=delta, **kw)
    d = env.data[env.data["asset"] == 0]
    p = d["price"].to_numpy(float)
    logp = np.log(p)
    r = np.diff(logp)
    ev_start = int(env.schedule.event_start)
    rv_calm = _rv(r, 0, max(ev_start - 1, 0), min_n=30)
    eps = drawdown_episodes(p)
    if not eps or not np.isfinite(rv_calm):
        return {"seed": seed, "qualifies": False, "rv_calm": float(rv_calm) if np.isfinite(rv_calm) else None}
    ep = min(eps, key=lambda e: e["depth"])                 # the deepest episode = the scripted crash
    rd = rise_decay(ep, p, r, rv_calm)
    out = {"seed": seed, "qualifies": rd is not None, "depth": ep["depth"], "rv_calm": float(rv_calm)}
    if rd:
        out.update(rd)
    # realised panic/calm RV ratio on the hidden phase labels (E3.3's closed-loop verification target)
    ph = d["phase"].to_numpy(dtype=object)
    pan = np.where(ph[1:] == "panic")[0]                    # r-indices of returns into panic days
    if len(pan) >= 10 and np.isfinite(rv_calm) and rv_calm > 0:
        out["m_panic_realised"] = float(np.mean(r[pan] ** 2) / rv_calm)
    return out


def pa3(n_seeds: int = 30):
    t0 = time.time()
    rows = [measure_crash_path(s) for s in PA3_SEEDS][:n_seeds]
    ok = [x for x in rows if x.get("qualifies")]
    rise = np.array([x["rise"] for x in ok], float)
    dec = np.array([x["decay_half_life"] for x in ok if x["decay_half_life"] is not None], float)
    cens = float(np.mean([x["decay_half_life"] is None for x in ok])) if ok else float("nan")

    def half_width_median(v, n):
        if len(v) < 5:
            return float("nan")
        return float(1.96 * 1.2533 * np.std(v, ddof=1) / np.sqrt(n))
    out = {
        "design": {"seeds": [min(PA3_SEEDS), min(PA3_SEEDS) + n_seeds - 1], "scenario": "crash", "delta": 0.70,
                   "state": "incumbent (v2.1 Phase-2 hand-over), mechanism A with the CAL multipliers",
                   "estimator": "tools/phase3/episodes.py (shared with E3.3/E3.4)"},
        "n_run": len(rows), "n_qualifying": len(ok), "censored_share_decay": cens,
        "rise": {"median": float(np.median(rise)) if len(rise) else None, "sd": float(np.std(rise, ddof=1)) if len(rise) > 1 else None,
                 "p25_75": [float(np.percentile(rise, 25)), float(np.percentile(rise, 75))] if len(rise) else None,
                 "half_width_median_at_200": half_width_median(rise, N_TARGET)},
        "decay": {"median": float(np.median(dec)) if len(dec) else None, "sd": float(np.std(dec, ddof=1)) if len(dec) > 1 else None,
                  "p25_75": [float(np.percentile(dec, 25)), float(np.percentile(dec, 75))] if len(dec) else None,
                  "half_width_median_at_200": half_width_median(dec, N_TARGET)},
        "m_panic_realised_median": float(np.median([x["m_panic_realised"] for x in ok if "m_panic_realised" in x]))
        if any("m_panic_realised" in x for x in ok) else None,
        "seconds": round(time.time() - t0),
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="pa3")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "power.json")
    power = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    for s in a.stages.split(","):
        if s == "pa3":
            power["PA3"] = pa3()
            print(json.dumps(power["PA3"], indent=1))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(power, fh, indent=1)
    print("->", path)


if __name__ == "__main__":
    main()
