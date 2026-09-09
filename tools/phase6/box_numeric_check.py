"""
v2.1 Phase 6 -- the cross-machine NUMERIC check of the generator (P6-1's reference-row rule, the form it needs on a
machine of another platform).

`tools/path_hashes.py` hashes every column's bytes, so a last-bit difference in a transcendental function between
two platforms' numpy/libm builds shows as "changed" without saying by how much; the first box run reported 1,877
non-analyst column changes across 95 configurations with no magnitude.  This tool stores the VALUES of a small set
of configurations on the laptop (`--write`) and, on another machine, regenerates them and reports the maximum
relative difference per column and the share of exactly equal values (`--check`).  The standard is the one the
Kaggle reference row met in Phase 3 (worst relative difference 6.4e-16 over 51 moments): a machine whose columns
agree to 1e-9 relative is running the same generator; one that does not is not, whatever the hashes say.

    python -m tools.phase6.box_numeric_check --write            # laptop: docs/env_v2/generated/v2_1/e6_0/path_values_reference.json
    python -m tools.phase6.box_numeric_check --check [--tol 1e-9]   # the box: exit 1 above tol
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
REF = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e6_0", "path_values_reference.json")


def configs():
    """One configuration per family of tools/path_hashes.configs(): the four scenarios (crash at delta 0.70),
    an event-first crash, the fw_index engine and the 3-asset crash -- seed 0 throughout, T = 200."""
    return [{"scenario": "flat", "n_days": 200, "seed": 0},
            {"scenario": "bull_trap", "n_days": 200, "seed": 0},
            {"scenario": "sustained_bull", "n_days": 200, "seed": 0},
            {"scenario": "crash", "n_days": 200, "seed": 0, "crash_discount": 0.70},
            {"scenario": "crash", "n_days": 200, "seed": 0, "ordering": "event_first"},
            {"scenario": "flat", "n_days": 200, "seed": 0, "engine": "fw_index"},
            {"scenario": "crash", "n_days": 200, "seed": 0, "n_assets": 3,
             "config": {"asset_vol_scale": [1.0, 1.0, 0.5], "rho_common": 0.3}}]


def values(kw: dict) -> dict:
    from envs.synthetic_market import SyntheticMarketEnv
    env = SyntheticMarketEnv(**kw)
    d = env.data
    cols = {}
    for c in d.columns:
        arr = d[c].to_numpy()
        if arr.dtype.kind in "iuf":
            cols[c] = [float(v) for v in arr]                    # json keeps 17 significant digits: exact for float64
        else:
            cols[c] = [str(v) for v in d[c].tolist()]
    return {"config": kw, "n_rows": int(len(d)), "attempts": int(env.attempts), "columns": cols}


def write(path: str):
    t0 = time.time()
    doc = {"meta": {"platform": platform.platform(), "python": sys.version.split()[0], "numpy": np.__version__,
                    "date": time.strftime("%Y-%m-%d"), "n_configs": len(configs())},
           "configs": [values(kw) for kw in configs()]}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    print(f"{len(doc['configs'])} configurations' values -> {os.path.relpath(path, ROOT)} ({os.path.getsize(path) / 1e6:.1f} MB, {time.time() - t0:.0f} s)")


def check(path: str, tol: float) -> int:
    ref = json.load(open(path, encoding="utf-8"))
    print(f"reference: {ref['meta']}")
    print(f"this machine: {platform.platform()}, python {sys.version.split()[0]}, numpy {np.__version__}")
    worst = []
    n_exact = n_vals = 0
    for r in ref["configs"]:
        got = values(r["config"])
        if got["n_rows"] != r["n_rows"] or got["attempts"] != r["attempts"]:
            print(f"  {r['config']}: n_rows/attempts differ ({got['n_rows']}/{got['attempts']} vs {r['n_rows']}/{r['attempts']})")
            worst.append((float("inf"), str(r["config"]), "n_rows/attempts"))
            continue
        for c, ref_vals in r["columns"].items():
            g = got["columns"].get(c)
            if g is None:
                worst.append((float("inf"), str(r["config"]), f"{c} missing")); continue
            if isinstance(ref_vals[0], str):
                same = sum(1 for a, b in zip(g, ref_vals) if a == b); n_exact += same; n_vals += len(ref_vals)
                if same != len(ref_vals):
                    worst.append((float("inf"), str(r["config"]), f"{c} ({len(ref_vals) - same} strings differ)"))
                continue
            a = np.asarray(g, float); b = np.asarray(ref_vals, float)
            both_nan = np.isnan(a) & np.isnan(b)
            rel = np.abs(a - b) / np.maximum(np.maximum(np.abs(a), np.abs(b)), 1e-300)
            rel[both_nan] = 0.0
            n_exact += int(np.sum((a == b) | both_nan)); n_vals += len(b)
            worst.append((float(np.nanmax(rel)) if len(rel) else 0.0, str(r["config"]), c))
    worst.sort(reverse=True)
    print(f"\n{n_vals} values compared; exactly equal {n_exact} ({n_exact / max(n_vals, 1):.4%}); tolerance {tol:g}")
    print("worst columns (max relative difference):")
    for w, cfg, c in worst[:15]:
        print(f"  {w:.3e}  {c:28s} {cfg}")
    bad = [w for w in worst if w[0] > tol]
    print(f"\n{'SAME GENERATOR' if not bad else 'NOT THE SAME GENERATOR'}: {len(bad)} of {len(worst)} columns above {tol:g}")
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--ref", default=REF)
    ap.add_argument("--tol", type=float, default=1e-9)
    a = ap.parse_args(argv)
    if a.write:
        write(a.ref); return 0
    if a.check:
        return check(a.ref, a.tol)
    ap.error("--write or --check")


if __name__ == "__main__":
    raise SystemExit(main())
