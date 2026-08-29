"""
Phase 0 (v2.1) "no distribution change" fixture: hash every column of `env.data` for a fixed set of
configurations, so that the code changes of Phase 0 can be shown to leave every hidden and rendered path
bit-identical except the analyst columns (the one declared fix).

Usage:
    python -m tools.path_hashes --out docs/env_v2/generated/v2_1/path_hashes_before.json
    python -m tools.path_hashes --out docs/env_v2/generated/v2_1/path_hashes_after.json
    python -m tools.path_hashes --compare before.json after.json

Configurations (PREREG_PHASE_0.md §7): seeds 0-9 x {flat, bull_trap, sustained_bull, crash 0.55/0.70/0.85}
setup-first; seeds 0-4 x {crash 0.70, bull_trap} event-first; seeds 0-4 x engines {fw_index, pruna, ar1, fw_hl60}
(flat); seeds 0-4 of the 3-asset crash (vol scale [1, 1, 0.5], rho 0.3). T = 200 throughout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ANALYST_COLS = ("analyst_fair_value", "analyst_error_u")


def configs():
    out = []
    for s in range(10):
        for sc in ("flat", "bull_trap", "sustained_bull"):
            out.append({"scenario": sc, "n_days": 200, "seed": s})
        for d in (0.55, 0.70, 0.85):
            out.append({"scenario": "crash", "n_days": 200, "seed": s, "crash_discount": d})
    for s in range(5):
        for sc in ("crash", "bull_trap"):
            out.append({"scenario": sc, "n_days": 200, "seed": s, "ordering": "event_first"})
        for eng in ("fw_index", "pruna", "ar1", "fw_hl60"):
            out.append({"scenario": "flat", "n_days": 200, "seed": s, "engine": eng})
        out.append({"scenario": "crash", "n_days": 200, "seed": s, "n_assets": 3,
                    "config": {"asset_vol_scale": [1.0, 1.0, 0.5], "rho_common": 0.3}})
    return out


def _col_hash(series) -> str:
    """Numeric columns: exact bytes; every other dtype (object, pandas 3 `str`, bool): the joined string values.
    (An object/str array's .tobytes() would hash pointer values, which are not reproducible.)"""
    arr = series.to_numpy()
    if arr.dtype.kind in "iuf":
        payload = np.ascontiguousarray(arr).tobytes()
    else:
        payload = "".join(str(v) for v in series.tolist()).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:24]


def hash_config(kw: dict) -> dict:
    from envs.synthetic_market import SyntheticMarketEnv
    env = SyntheticMarketEnv(**kw)
    d = env.data
    cols = {c: _col_hash(d[c]) for c in d.columns}
    return {"config": kw, "n_rows": int(len(d)), "attempts": int(env.attempts),
            "engine_params": env.result.params.name, "columns": cols}


def build(out_path: str):
    rows = [hash_config(kw) for kw in configs()]
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({"configs": rows}, fh, indent=1)
    print(f"{len(rows)} configurations hashed -> {out_path}")


def compare(before_path: str, after_path: str) -> dict:
    a = json.load(open(before_path, encoding="utf-8"))["configs"]
    b = json.load(open(after_path, encoding="utf-8"))["configs"]
    assert len(a) == len(b), "different configuration counts"
    changed_non_analyst, changed_analyst, unchanged_analyst = [], [], []
    for ra, rb in zip(a, b):
        assert ra["config"] == rb["config"]
        for c, h in ra["columns"].items():
            hb = rb["columns"].get(c)
            if c in ANALYST_COLS:
                (changed_analyst if hb != h else unchanged_analyst).append((ra["config"], c))
            elif hb != h:
                changed_non_analyst.append((ra["config"], c))
        if ra["n_rows"] != rb["n_rows"] or ra["attempts"] != rb["attempts"]:
            changed_non_analyst.append((ra["config"], "n_rows/attempts"))
    return {"n_configs": len(a), "changed_non_analyst": changed_non_analyst,
            "changed_analyst": len(changed_analyst), "unchanged_analyst": len(unchanged_analyst)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--compare", nargs=2, default=None)
    a = ap.parse_args()
    if a.compare:
        r = compare(*a.compare)
        print(json.dumps({k: (v if not isinstance(v, list) else v[:20]) for k, v in r.items()}, indent=1, default=str))
        print("NON-ANALYST CHANGES:", len(r["changed_non_analyst"]))
        sys.exit(1 if r["changed_non_analyst"] else 0)
    build(a.out or os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "path_hashes_before.json"))
