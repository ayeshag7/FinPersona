"""
E1.4 generator side and the rule (PREREG_PHASE_1.md section 5.3): 200 flat paths per jump-placement variant, GJR-GARCH-t
residuals per path, announcement windows (10 trading days ending on the announcement day), two-sample KS distances to the
panel's window / other-day residual distributions with bootstrap upper limits, the kurtosis split, the E[x]
equivalence rule, and the flat-path kurtosis share (checklist item 2, reported).

    python -m tools.phase1.e1_4_generator [--workers 8]
Outputs: docs/env_v2/generated/v2_1/e1_4/generator_split.json, generator_split.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "1")

OUT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e1_4")
SEED0, N = 70000, 200
WINDOW = 10
N_BOOT = 1000
VARIANTS = {"current_x_negmean": {"jump_placement": "x_negmean"}, "B_x_zero": {"jump_placement": "x_zero"},
            "A_V_announce": {"jump_placement": "V_announce"}, "C_both": {"jump_placement": "both"}}
E_X_MARGIN = 0.02
D0 = 0.10


def _job(args):
    import warnings
    warnings.filterwarnings("ignore")
    from arch import arch_model
    from envs.v2.generator import GenConfig, generate
    seed, cfg_over = args
    r = generate(GenConfig(scenario="flat", seed=seed, T=200, **cfg_over))
    m = r.day >= 1
    days = r.day[m]; P = r.P[0, m]; x = r.x[0, m]
    ret = np.diff(np.log(P))
    d_ret = days[1:]
    z = np.full(len(ret), np.nan)
    try:
        res = arch_model(100 * ret, mean="Constant", vol="GARCH", p=1, o=1, q=1, dist="t").fit(disp="off", show_warning=False)
        z = np.asarray(res.std_resid, float)
    except Exception:
        pass
    ann_days = sorted(set(int(a) for a in r.ann[0].values()))
    win = np.zeros(len(d_ret), bool)
    for a in ann_days:
        win |= (d_ret > a - WINDOW) & (d_ret <= a)
    kurt = float(stats.kurtosis(ret))
    n_vj = int(np.sum([1 for a in r.ann_jumps[0]]))
    return {"seed": seed, "z": z.astype(np.float32), "r": ret.astype(np.float32), "win": win, "mean_x": float(x.mean()),
            "kurt": kurt, "n_ann_jumps": n_vj}


def ks_boot(a_vals, a_cl, b_vals, b_cl, n_boot=N_BOOT, seed=0):
    """Two-sample KS distance with a bootstrap over clusters on both sides -> (point, upper 95 %)."""
    rng = np.random.default_rng(seed)
    ua = np.unique(a_cl); ub = np.unique(b_cl)
    ia = {g: np.where(a_cl == g)[0] for g in ua}; ib = {g: np.where(b_cl == g)[0] for g in ub}
    point = float(stats.ks_2samp(a_vals, b_vals).statistic)
    vals = np.empty(n_boot)
    for b in range(n_boot):
        sa = np.concatenate([a_vals[ia[g]] for g in ua[rng.integers(0, len(ua), len(ua))]])
        sb = np.concatenate([b_vals[ib[g]] for g in ub[rng.integers(0, len(ub), len(ub))]])
        vals[b] = stats.ks_2samp(sa, sb).statistic
    return point, float(np.percentile(vals, 97.5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    a = ap.parse_args()
    t0 = time.time()
    panel = pd.read_parquet(os.path.join(OUT, "panel_residuals_split.parquet"))
    panel = panel[np.isfinite(panel["z"])]
    pz = panel["z"].to_numpy(float); pc = pd.factorize(panel["ticker"])[0]; pw = panel["in_window"].to_numpy(bool)
    # subsample the panel residual pool to 200 stocks x full for the bootstrap cost (cluster resampling over stocks is kept)
    out = {"design": {"seeds": [SEED0, SEED0 + N - 1], "T": 200, "window_days": WINDOW, "n_boot": a.n_boot, "D0": D0, "E_x_margin": E_X_MARGIN,
                      "panel": {"n_stocks": int(len(np.unique(pc))), "n_days": int(len(pz)), "window_share": float(pw.mean())}}, "variants": {}}
    cache_dir = os.path.join(OUT, "cache"); os.makedirs(cache_dir, exist_ok=True)
    for name, over in VARIANTS.items():
        t1 = time.time()
        cache = os.path.join(cache_dir, f"{name}.json")   # resumable: a variant already computed is loaded, not re-run
        if os.path.exists(cache):
            out["variants"][name] = json.load(open(cache, encoding="utf-8")); print(name, "loaded from cache", flush=True); continue
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            rows = list(ex.map(_job, [(s, over) for s in range(SEED0, SEED0 + N)], chunksize=5))
        z = np.concatenate([r["z"] for r in rows]); cl = np.concatenate([np.full(len(r["z"]), i) for i, r in enumerate(rows)])
        w = np.concatenate([r["win"] for r in rows]); ok = np.isfinite(z)
        z, cl, w = z[ok], cl[ok], w[ok]
        jump = np.abs(z) > 4
        res = {"n_paths": len(rows), "n_days": int(len(z)), "window_share": float(w.mean()),
               "q_share_of_jumps_in_window": float(jump[w].sum() / max(jump.sum(), 1)), "n_jumps": int(jump.sum()),
               "jump_rate_in_window": float(jump[w].mean()), "jump_rate_outside": float(jump[~w].mean()),
               "excess_kurtosis_in": float(stats.kurtosis(z[w])), "excess_kurtosis_out": float(stats.kurtosis(z[~w])),
               "n_ann_jumps_mean_per_path": float(np.mean([r["n_ann_jumps"] for r in rows]))}
        for lab, sel_p, sel_g in (("window", pw, w), ("other", ~pw, ~w)):
            pt, up = ks_boot(pz[sel_p], pc[sel_p], z[sel_g], cl[sel_g], n_boot=a.n_boot)
            res[f"ks_{lab}"] = pt; res[f"ks_{lab}_upper95"] = up
        res["ks_pass"] = bool(res["ks_window_upper95"] < D0 and res["ks_other_upper95"] < D0)
        mx = np.array([r["mean_x"] for r in rows])
        rng = np.random.default_rng(1)
        bm = np.array([mx[rng.integers(0, N, N)].mean() for _ in range(a.n_boot)])
        res["E_x"] = float(mx.mean()); res["E_x_ci95"] = [float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5))]
        res["E_x_pass"] = bool(-E_X_MARGIN <= res["E_x_ci95"][0] and res["E_x_ci95"][1] <= E_X_MARGIN)
        ku = np.array([r["kurt"] for r in rows])
        res["share_kurt_gt_1p5"] = float((ku > 1.5).mean()); res["median_kurt"] = float(np.median(ku))
        res["seconds"] = round(time.time() - t1)
        out["variants"][name] = res
        json.dump(res, open(cache, "w", encoding="utf-8"), indent=1)
        print(name, json.dumps({k: v for k, v in res.items() if not isinstance(v, list)}), flush=True)
    # rule (REG-3): both KS upper limits < D0 and E[x] equivalence; among passers the smaller window distance; else C
    passers = [k for k, v in out["variants"].items() if v["ks_pass"] and v["E_x_pass"] and k != "current_x_negmean"]
    if passers:
        adopt = min(passers, key=lambda k: out["variants"][k]["ks_window"]); reason = "both KS upper limits < 0.10 and E[x] inside +/- 0.02" + (" (smallest window distance among passers)" if len(passers) > 1 else "")
    else:
        c_ok = out["variants"]["C_both"]["E_x_pass"]
        adopt = "C_both" if c_ok else None
        reason = ("no variant meets the KS rule; C (the most flexible) carried forward with the shortfall stated (REG-3)" if c_ok
                  else "no variant meets the KS rule and C fails the E[x] rule: none adopted, team asked")
    out["decision"] = {"adopted": adopt, "reason": reason, "passers": passers}
    out["seconds"] = round(time.time() - t0)
    with open(os.path.join(OUT, "generator_split.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    L = ["# E1.4 generator side and the rule (PREREG_PHASE_1.md section 5.2-5.3)", "",
         f"200 flat paths (seeds {SEED0}-{SEED0 + N - 1}, T = 200) per variant, GJR-GARCH-t residuals per path; window = the {WINDOW} trading days "
         f"ending on each EPS announcement day; KS distances to the panel's window / other-day residual pools (E1.4 panel side, "
         f"{out['design']['panel']['n_stocks']} stocks) with a {a.n_boot}-resample bootstrap over stocks and paths; rule: both upper limits < {D0} and the "
         f"95 % interval of E[x] inside +/- {E_X_MARGIN}.", "",
         "| variant | window share | q (jumps in window) | rate in / out | kurtosis in / out | KS window (upper) | KS other (upper) | KS pass | E[x] [CI] | E[x] pass | kurt > 1.5 share | median kurt |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, v in out["variants"].items():
        L.append(f"| {k} | {v['window_share']:.3f} | {v['q_share_of_jumps_in_window']:.3f} | {v['jump_rate_in_window']:.4f} / {v['jump_rate_outside']:.4f} | "
                 f"{v['excess_kurtosis_in']:.1f} / {v['excess_kurtosis_out']:.1f} | {v['ks_window']:.3f} ({v['ks_window_upper95']:.3f}) | {v['ks_other']:.3f} ({v['ks_other_upper95']:.3f}) | "
                 f"{v['ks_pass']} | {v['E_x']:+.4f} [{v['E_x_ci95'][0]:+.4f}, {v['E_x_ci95'][1]:+.4f}] | {v['E_x_pass']} | {v['share_kurt_gt_1p5']:.2f} | {v['median_kurt']:.2f} |")
    L += ["", f"**Decision (pre-registered rule): {out['decision']['adopted']} -- {out['decision']['reason']}.**",
          f"Panel: window share {out['design']['panel']['window_share']:.3f}; q 0.43, rate ratio 4.5, kurtosis in/out 16.2 / 15.0 (e1_4/panel_split.md)."]
    with open(os.path.join(OUT, "generator_split.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("decision:", out["decision"], f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
