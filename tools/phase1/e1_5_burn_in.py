"""
E1.5 burn-in (PREREG_PHASE_1.md section 6; REG-17): per engine, the day-1 distribution of (x, GARCH variance, n_f) under
(i) the current 260-day burn-in, (ii) option A = a burn-in of >= 5 half-lives, (iii) option B = the day-1 state drawn from
a stored long-run sample followed by a 60-day warm-up, against the reference distribution on benchmark day 5,000 of
500 flat paths; two-sample KS distance per variable with a 1,000-resample bootstrap upper limit; rule: every variable's
upper limit < 0.10.

    python -m tools.phase1.e1_5_burn_in [--workers 8] [--write-states]
Outputs: docs/env_v2/generated/v2_1/e1_5/burn_in.json, burn_in.md, reference_states_<engine>.npz;
         envs/v2/params/burn_in_states_<engine>.npz (option B artefacts, written with --write-states)
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "1")

OUT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e1_5")
PARAM_DIR = os.path.join(ROOT, "envs", "v2", "params")
SEED0, N = 80000, 500
T_REF = 5000
ENGINES = ("fw_fallback_hl150", "fw_hl60", "fw_index", "pruna", "ar1")
# slowest state variable = x; pull-rate / long-pilot half-lives (PHASE_0 findings block R13/R19): 150 / 60 / 628 / 622 / 150 d
HALF_LIFE = {"fw_fallback_hl150": 150.0, "fw_hl60": 60.0, "fw_index": 628.0, "pruna": 622.0, "ar1": 150.0}
FIVE_HL = {k: int(math.ceil(5 * v / 10.0) * 10) for k, v in HALF_LIFE.items()}     # 750 / 300 / 3140 / 3110 / 750
STORED_WARM = 60
N_BOOT = 1000
D0 = 0.10
VARS = ("x", "sigma2", "n_f")


def _ref_job(args):
    from envs.v2.generator import GenConfig, generate
    seed, eng = args
    r = generate(GenConfig(scenario="flat", seed=seed, T=T_REF, engine=eng, reject=False, burn_in=260, burn_in_mode="long"))
    i = int(np.where(r.day == T_REF)[0][0])
    return (r.x[0, i], r.sigma[0, i] ** 2, r.n_f[0, i], r.x[0, i - 1], r.sigma[0, i - 1] ** 2, r.e[0, i - 1])


def _day1_job(args):
    from envs.v2.generator import GenConfig, generate
    seed, eng, burn, mode = args
    r = generate(GenConfig(scenario="flat", seed=seed, T=200, engine=eng, reject=False, burn_in=burn, burn_in_mode=mode))
    i = int(np.where(r.day == 1)[0][0])
    return (r.x[0, i], r.sigma[0, i] ** 2, r.n_f[0, i])


def ks_upper(a: np.ndarray, b: np.ndarray, n_boot: int = N_BOOT, seed: int = 0):
    rng = np.random.default_rng(seed)
    pt = float(stats.ks_2samp(a, b).statistic)
    vals = np.array([stats.ks_2samp(a[rng.integers(0, len(a), len(a))], b[rng.integers(0, len(b), len(b))]).statistic for _ in range(n_boot)])
    return pt, float(np.percentile(vals, 97.5))


def main():
    global N
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--write-states", action="store_true", help="write envs/v2/params/burn_in_states_<engine>.npz for every engine (needed before option B can run)")
    ap.add_argument("--engines", default=",".join(ENGINES))
    ap.add_argument("--n", type=int, default=500, help="paths per engine (500 pre-registered; 2,000 under PREREG_PHASE_1_ADDENDUM.md section 4)")
    ap.add_argument("--suffix", default="", help="output-name suffix (e.g. _n500 to keep the pre-registered run beside the powered one)")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    engines = a.engines.split(",")
    t0 = time.time()
    N = a.n
    seeds = list(range(SEED0, SEED0 + N))
    out = {"design": {"seeds": [SEED0, SEED0 + N - 1], "n_paths": N, "T_ref": T_REF, "n_boot": N_BOOT, "D0": D0, "five_half_lives": FIVE_HL,
                      "stored_warm_up_days": STORED_WARM, "variables": VARS}, "engines": {}}
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for eng in engines:
            t1 = time.time()
            ref = np.array(list(ex.map(_ref_job, [(s, eng) for s in seeds], chunksize=10)))
            np.savez(os.path.join(OUT, f"reference_states_{eng}.npz"), x=ref[:, 0], sigma2=ref[:, 1], n_f=ref[:, 2], x_prev=ref[:, 3],
                     h=ref[:, 4], e_prev=ref[:, 5], seeds=np.array(seeds))
            if a.write_states:
                np.savez(os.path.join(PARAM_DIR, f"burn_in_states_{eng}.npz"), x=ref[:, 0], x_prev=ref[:, 3], n_f=ref[:, 2], h=ref[:, 4],
                         e_prev=ref[:, 5], seeds=np.array(seeds), source=np.array([f"E1.5 reference: day {T_REF} of {N} flat paths (seeds {SEED0}-{SEED0 + N - 1}), engine {eng}"]))
            res = {"reference": {v: {"mean": float(ref[:, j].mean()), "sd": float(ref[:, j].std())} for j, v in enumerate(VARS)}, "options": {}}
            options = [("current_260", 260, "long"), (f"A_long_{FIVE_HL[eng]}", FIVE_HL[eng], "long")]
            if a.write_states or os.path.exists(os.path.join(PARAM_DIR, f"burn_in_states_{eng}.npz")):
                options.append((f"B_stored_{STORED_WARM}", STORED_WARM, "stored"))
            for name, burn, mode in options:
                d1 = np.array(list(ex.map(_day1_job, [(s, eng, burn, mode) for s in seeds], chunksize=10)))
                o = {"burn_in": burn, "mode": mode, "seconds_per_path": None}
                for j, v in enumerate(VARS):
                    pt, up = ks_upper(d1[:, j], ref[:, j])
                    o[v] = {"ks": pt, "ks_upper95": up, "day1_sd": float(d1[:, j].std()), "day1_mean": float(d1[:, j].mean()),
                            "sd_ratio_vs_ref": float(d1[:, j].std() / ref[:, j].std()) if ref[:, j].std() > 0 else None}
                o["pass"] = bool(all(o[v]["ks_upper95"] < D0 for v in VARS))
                res["options"][name] = o
                print(eng, name, {v: (round(o[v]["ks"], 3), round(o[v]["ks_upper95"], 3)) for v in VARS}, "pass" if o["pass"] else "FAIL", flush=True)
            res["seconds"] = round(time.time() - t1)
            out["engines"][eng] = res
    # REG-17 rule
    dec = {}
    for eng, r in out["engines"].items():
        A_ok = any(k.startswith("A_") and v["pass"] for k, v in r["options"].items())
        B_ok = any(k.startswith("B_") and v["pass"] for k, v in r["options"].items())
        cur_ok = r["options"]["current_260"]["pass"]
        if A_ok and B_ok:
            choice = "A" if eng == "fw_fallback_hl150" else "B"; why = "both pass: A for the default engine (no artefact), B for the slow sensitivities"
        elif A_ok:
            choice, why = "A", "only the long burn-in passes"
        elif B_ok:
            choice, why = "B", "only the stored state passes"
        else:
            choice, why = "current", "neither option passes: current burn-in kept, shortfall stated"
        dec[eng] = {"adopted": choice, "reason": why, "current_passes": cur_ok,
                    "burn_in_days": FIVE_HL[eng] if choice == "A" else (STORED_WARM if choice == "B" else 260)}
    out["decision"] = dec
    out["seconds"] = round(time.time() - t0)
    with open(os.path.join(OUT, f"burn_in{a.suffix}.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    L = ["# E1.5 burn-in (PREREG_PHASE_1.md section 6; REG-17)", "",
         f"Reference = (x, sigma^2, n_f) on benchmark day {T_REF} of {N} flat paths (seeds {SEED0}-{SEED0 + N - 1}) per engine; options: the current "
         f"260-day burn-in, A = >= 5 half-lives ({FIVE_HL}), B = stored long-run state + {STORED_WARM}-day warm-up. Two-sample KS per variable with a "
         f"{N_BOOT}-resample bootstrap upper limit; pass = every upper limit < {D0}.", "",
         "| engine | option | burn-in | KS x (upper) | KS sigma^2 (upper) | KS n_f (upper) | sd(x_1)/sd(x_ref) | pass |", "|---|---|---|---|---|---|---|---|"]
    for eng, r in out["engines"].items():
        for name, o in r["options"].items():
            L.append(f"| {eng} | {name} | {o['burn_in']} ({o['mode']}) | {o['x']['ks']:.3f} ({o['x']['ks_upper95']:.3f}) | {o['sigma2']['ks']:.3f} ({o['sigma2']['ks_upper95']:.3f}) | "
                     f"{o['n_f']['ks']:.3f} ({o['n_f']['ks_upper95']:.3f}) | {o['x']['sd_ratio_vs_ref']:.3f} | {o['pass']} |")
    L += ["", "Decision (REG-17): " + "; ".join(f"{e}: {d['adopted']} ({d['burn_in_days']} d) -- {d['reason']}" for e, d in dec.items()) + "."]
    with open(os.path.join(OUT, f"burn_in{a.suffix}.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print(json.dumps(dec, indent=1), f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
