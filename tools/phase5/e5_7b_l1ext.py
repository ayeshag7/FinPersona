"""
E5.7(b) -- the L1 extended candidate set on a stored panel (PREREG_PHASE_5.md section 10b).

    python -m tools.phase5.e5_7b_l1ext --panel <pkl> --out DIR [--label NAME]

In-sample (the attacker's most favourable case), with the free scalar k fitted as the audit does (log-median-optimal):
  (1) the audit's single-field candidates (evaluation.leakage_audit.l1_algebraic, unchanged);
  (2) pairwise geometric means of the valuation candidates (P/PE, P x DY, F) with price;
  (3) the least-squares best linear combination in logs of up to three candidates;
  (4) the median of the three valuation candidates.
Statistics per candidate: median APE, within-1/2/5 % shares, share above the 1 % floor; the INVERSION SHARE is the
within-5 % share of the best candidate, with a 500-resample path-cluster bootstrap.  No gate (Phase 6 derives it).

Output: <out>/l1ext.{json,md}
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tools.phase5.common import GEN, encode_nm, shown_fields_of, pin_state  # noqa: E402

N_BOOT = 500


def stats(vhat, V, path_idx, n_paths, idx_boot):
    ape = np.abs(vhat - V) / V
    ok = np.isfinite(ape)
    out = {"median_APE": float(np.nanmedian(ape)), "within_1pct": float(np.nanmean(ape <= 0.01)),
           "within_2pct": float(np.nanmean(ape <= 0.02)), "within_5pct": float(np.nanmean(ape <= 0.05)),
           "share_above_floor": float(np.nanmean(ape > 0.01)), "n": int(ok.sum())}
    c5 = np.bincount(path_idx[ok], weights=(ape[ok] <= 0.05).astype(float), minlength=n_paths)
    cn = np.bincount(path_idx[ok], minlength=n_paths).astype(float)
    draws = np.array([c5[ix].sum() / cn[ix].sum() for ix in idx_boot])
    out["within_5pct_ci95"] = [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(a.out, exist_ok=True)
    state = pin_state()
    from evaluation.leakage_audit import l1_algebraic
    panel = encode_nm(pd.read_pickle(a.panel))
    shown = shown_fields_of(panel)
    base_tab = l1_algebraic(panel, shown)
    P = panel["P"].to_numpy(float); V = panel["V"].to_numpy(float)
    path_idx = pd.factorize(panel["scenario"].astype(str) + "-" + panel["seed"].astype(str))[0]
    n_paths = int(path_idx.max()) + 1
    rng = np.random.default_rng(570001)
    idx_boot = rng.integers(0, n_paths, (N_BOOT, n_paths))
    cands = {"price": P}
    if "reported_PE" in panel:
        pe = panel["reported_PE"].to_numpy(float)
        if "reported_PE_nm" in panel:
            pe = np.where(panel["reported_PE_nm"].to_numpy(float) > 0, np.nan, pe)
        cands["P/PE"] = P / np.where(pe > 0, pe, np.nan)
    if "dividend_yield" in panel:
        dy = panel["dividend_yield"].to_numpy(float)
        cands["P*DY"] = P * np.where(dy > 0, dy, np.nan)
    if "analyst_fair_value" in panel:
        cands["F"] = panel["analyst_fair_value"].to_numpy(float)
    logs = {k: np.log(np.where(v > 0, v, np.nan)) for k, v in cands.items()}
    lV = np.log(V)
    rows = {}
    # (1) single candidates with the audit's k (log-median)
    for k, lv in logs.items():
        ok = np.isfinite(lv)
        c = np.nanmedian(lV[ok] - lv[ok])
        rows[f"k*{k}"] = stats(np.exp(lv + c), V, path_idx, n_paths, idx_boot)
    # (2) pairwise geometric means with price
    for k in [k for k in logs if k != "price"]:
        lv = 0.5 * (logs["price"] + logs[k]); ok = np.isfinite(lv)
        c = np.nanmedian(lV[ok] - lv[ok])
        rows[f"k*sqrt(price*{k})"] = stats(np.exp(lv + c), V, path_idx, n_paths, idx_boot)
    # (3) least-squares best linear combination in logs, up to three candidates (in-sample)
    keys = list(logs)
    best = None
    for m in (1, 2, 3):
        for combo in itertools.combinations(keys, m):
            X = np.column_stack([np.ones(len(lV))] + [logs[k] for k in combo])
            ok = np.isfinite(X).all(axis=1)
            b = np.linalg.lstsq(X[ok], lV[ok], rcond=None)[0]
            vhat = np.full(len(lV), np.nan); vhat[ok] = np.exp(X[ok] @ b)
            s = stats(vhat, V, path_idx, n_paths, idx_boot); s["coef"] = [float(v) for v in b]
            rows[f"lsq({'+'.join(combo)})"] = s
            if best is None or s["median_APE"] < best[1]:
                best = (f"lsq({'+'.join(combo)})", s["median_APE"])
    # (4) median of the valuation candidates (each scaled by its own k)
    val = [k for k in ("P/PE", "P*DY", "F") if k in logs]
    if len(val) >= 2:
        scaled = []
        for k in val:
            ok = np.isfinite(logs[k]); c = np.nanmedian(lV[ok] - logs[k][ok]); scaled.append(logs[k] + c)
        med = np.nanmedian(np.column_stack(scaled), axis=1)
        rows["median(valuation candidates)"] = stats(np.exp(med), V, path_idx, n_paths, idx_boot)
    ranked = sorted(rows.items(), key=lambda kv: kv[1]["median_APE"])
    res = {"what": "E5.7(b): L1 extended candidate set (PREREG section 10b), in-sample", "label": a.label,
           "panel": os.path.relpath(a.panel, ROOT), "state": state, "n_rows": int(len(panel)), "n_paths": n_paths,
           "audit_l1": base_tab.to_dict(orient="records"), "extended": rows,
           "best": {"candidate": ranked[0][0], **ranked[0][1]},
           "inversion_share_best_within_5pct": ranked[0][1]["within_5pct"],
           "price_itself": rows.get("k*price"), "seconds": round(time.time() - t0)}
    json.dump(res, open(os.path.join(a.out, "l1ext.json"), "w", encoding="utf-8"), indent=1, default=str)
    L = [f"# E5.7(b) L1 extended candidate set -- {a.label or os.path.basename(a.out)}", "",
         f"Panel `{res['panel']}`, {n_paths} paths / {len(panel)} rows; in-sample; k log-median-optimal; {N_BOOT}-resample path bootstrap on the within-5 % share.", "",
         "| candidate | median APE | within 1 % | within 2 % | within 5 % [CI] | above floor |", "|---|---|---|---|---|---|"]
    for k, s in ranked:
        L.append(f"| {k} | {s['median_APE']:.4f} | {s['within_1pct']:.4f} | {s['within_2pct']:.4f} | {s['within_5pct']:.4f} "
                 f"[{s['within_5pct_ci95'][0]:.4f}, {s['within_5pct_ci95'][1]:.4f}] | {s['share_above_floor']:.4f} |")
    L += ["", f"Best candidate: **{ranked[0][0]}** (median APE {ranked[0][1]['median_APE']:.4f}; inversion share = within-5 % "
              f"{ranked[0][1]['within_5pct']:.4f}); price itself: median APE {rows['k*price']['median_APE']:.4f}, within-5 % "
              f"{rows['k*price']['within_5pct']:.4f}.", ""]
    with open(os.path.join(a.out, "l1ext.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L[:14])); print(f"wrote {a.out}/l1ext.json in {res['seconds']} s")


if __name__ == "__main__":
    main()
