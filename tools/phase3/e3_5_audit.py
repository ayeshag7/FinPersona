"""
E3.5 audits (PREREG_PHASE_3.md section 7.2, on the APPLIED state): the onset-detection audit in REG-6's
corrected form, and the derivation of the iv-continuity tolerance T_z.

    python -m tools.phase3.e3_5_audit [--seeds 200] [--workers 3]

Design (fixed in the pre-registration): 200 crash seeds (delta 0.70, seeds 220000+).
 (ii)  onset detection: per day, score_IV = |dlog IV| vs score_ref = |dlog sqrt(252 fc)| (the SAME filter's
       forecast, the legitimate-information yardstick); labels 1 on days [tau, tau+5) after the
       deterioration->panic transition, 0 on calm days; ddAUC = AUC(IV) - AUC(ref) must not exceed the 95th
       percentile of a 500-draw circular-shift permutation null (rng 221001). calm->deterioration reported too.
 (iii) T_z: per seed and transition, z = dlog at the transition day / pooled calm sd of dlog (same construction
       as test_iv_continuity); T_z = P95 over seeds of the REFERENCE z; the IV z distribution published beside.

Output: docs/env_v2/generated/v2_1/e3_5/audit.{json,md}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e3_5")
SEED0 = 220000
SEED_PERM = 221001
N_PERM = 500
TRANS = (("deterioration", "panic"), ("panic", "stabilisation"), ("calm", "deterioration"))


def one(seed):
    from envs.synthetic_market import SyntheticMarketEnv
    env = SyntheticMarketEnv("crash", 200, seed, crash_discount=0.70)
    d = env.data[env.data["asset"] == 0]
    ph = d["phase"].to_numpy(dtype=object)
    iv = d["implied_volatility"].to_numpy(float)
    fc = d["iv_fc21"].to_numpy(float)
    dl_iv = np.diff(np.log(iv))
    dl_ref = np.diff(np.log(np.sqrt(252.0 * fc)))
    calm_pair = (ph[:-1] == "calm") & (ph[1:] == "calm")
    steps = {}
    for a, b in TRANS:
        idx = np.where((ph[:-1] == a) & (ph[1:] == b))[0]
        if len(idx):
            steps[f"{a}->{b}"] = {"iv": float(dl_iv[idx[0]]), "ref": float(dl_ref[idx[0]])}
    # day-level rows for the AUC: transition = deterioration->panic
    idx = np.where((ph[:-1] == "deterioration") & (ph[1:] == "panic"))[0]
    tau = int(idx[0]) if len(idx) else None
    lab = np.full(len(dl_iv), -1, dtype=np.int8)          # -1 = excluded
    lab[calm_pair] = 0
    if tau is not None:
        lab[tau:tau + 5] = 1
    return {"seed": seed, "steps": steps, "dl_iv": dl_iv.astype(np.float32), "dl_ref": dl_ref.astype(np.float32),
            "lab": lab, "calm_iv": dl_iv[calm_pair].astype(np.float32), "calm_ref": dl_ref[calm_pair].astype(np.float32)}


def auc(scores, labels):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(labels, scores))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        rows = list(ex.map(one, range(SEED0, SEED0 + a.seeds), chunksize=4))
    calm_sd_iv = float(np.concatenate([r["calm_iv"] for r in rows]).std())
    calm_sd_ref = float(np.concatenate([r["calm_ref"] for r in rows]).std())
    tz = {}
    for a_, b_ in TRANS:
        key = f"{a_}->{b_}"
        z_iv = [r["steps"][key]["iv"] / calm_sd_iv for r in rows if key in r["steps"]]
        z_ref = [r["steps"][key]["ref"] / calm_sd_ref for r in rows if key in r["steps"]]
        tz[key] = {"n": len(z_iv),
                   "z_iv_mean": float(np.mean(z_iv)), "z_iv_p95_abs": float(np.percentile(np.abs(z_iv), 95)),
                   "z_ref_mean": float(np.mean(z_ref)), "z_ref_p95": float(np.percentile(z_ref, 95)),
                   "T_z": float(np.percentile(z_ref, 95))}
    # onset AUC: pooled day-level, per-path circular-shift null
    sc_iv = np.concatenate([np.abs(r["dl_iv"]) for r in rows])
    sc_ref = np.concatenate([np.abs(r["dl_ref"]) for r in rows])
    lab = np.concatenate([r["lab"] for r in rows])
    keep = lab >= 0
    auc_iv = auc(sc_iv[keep], lab[keep])
    auc_ref = auc(sc_ref[keep], lab[keep])
    d_auc = auc_iv - auc_ref
    rng = np.random.default_rng(SEED_PERM)
    null = []
    lens = [len(r["lab"]) for r in rows]
    for _ in range(N_PERM):
        labs = []
        for r in rows:
            L = len(r["lab"])
            s = int(rng.integers(10, L - 10))
            labs.append(np.roll(r["lab"], s))
        lp = np.concatenate(labs)
        k = lp >= 0
        if lp[k].max() == 0 or lp[k].min() == 1:
            continue
        null.append(auc(sc_iv[k], lp[k]) - auc(sc_ref[k], lp[k]))
    null = np.asarray(null)
    p95 = float(np.percentile(null, 95))
    out = {"design": {"seeds": [SEED0, SEED0 + a.seeds - 1], "n_perm": int(len(null)), "seed_perm": SEED_PERM,
                      "label": "1 on days [tau, tau+5) after deterioration->panic; 0 on calm-calm day pairs",
                      "scores": "|dlog IV| vs |dlog sqrt(252 iv_fc21)| (the same filter's forecast)"},
           "calm_sd": {"dlog_iv": calm_sd_iv, "dlog_ref": calm_sd_ref},
           "transitions": tz,
           "onset_auc": {"auc_iv": auc_iv, "auc_ref": auc_ref, "delta_auc": d_auc,
                         "null_p95": p95, "null_mean": float(null.mean()),
                         "pass": bool(d_auc <= p95)},
           "seconds": round(time.time() - t0)}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "audit.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    L = ["# E3.5 audits: onset detection (REG-6 corrected form) and the continuity tolerance (PREREG 7.2)", "",
         f"{a.seeds} crash seeds (delta 0.70, seeds {SEED0}+); calm day-to-day sd of dlog IV {calm_sd_iv:.4f}, "
         f"of dlog ref {calm_sd_ref:.4f}.", "",
         "| transition | n | mean z_IV | mean z_ref | T_z = P95(z_ref) |", "|---|---|---|---|---|"]
    for k, v in tz.items():
        L.append(f"| {k} | {v['n']} | {v['z_iv_mean']:+.2f} | {v['z_ref_mean']:+.2f} | {v['T_z']:.2f} |")
    L += ["", f"Onset AUC: IV {auc_iv:.3f} vs same-filter RV forecast {auc_ref:.3f}; dAUC {d_auc:+.4f} vs "
          f"permutation-null P95 {p95:+.4f} -> **{'pass' if d_auc <= p95 else 'FAIL'}** "
          f"({len(null)} circular-shift draws)."]
    with open(os.path.join(OUT, "audit.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
