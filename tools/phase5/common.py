"""
Shared pieces of the Phase-5 tools (PREREG_PHASE_5.md sections 3 and 5.2).

  * pin_state()            -- print the deployed configuration every measuring tool runs under (P4-19: a tool
                              that measures the generator pins and records the state it measures)
  * encode_nm(panel)       -- the "n/m" rendering of an undefined P/E reaches the frozen audit as a NaN (it keeps
                              only numeric observation values) and would drop the row; every Phase-5 audit tool
                              encodes it as the attacker would: the cap value plus an indicator column
  * GROUPS                 -- the per-field-group ablation's groups (PREREG section 3)
  * verify_panel_vs_generator -- the stored panel must be the panel the current generator produces (P4-19)
  * build_panel_parallel   -- the SEP panel design of audit_panel(), built with a process pool, with an optional
                              per-run GenConfig override (the sentiment arms and b_pred = 0 need re-simulation)
"""
from __future__ import annotations

import os
import sys
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
PANELS = os.path.join(GEN, "_panels")
SEP_SEED0, SEP_N = 30000, 200
DELTAS = (0.55, 0.70, 0.85)

GROUPS: Dict[str, List[str]] = {
    "LEVELS": ["price", "SMA20", "SMA50", "MACD", "MACD_signal"],
    "VAL": ["reported_PE", "dividend_yield", "days_since_eps_announcement", "reported_PE_nm"],
    "ANALYST": ["analyst_fair_value"],
    "SENT": ["news_sentiment", "sentiment_MA5", "sentiment_change"],
    "VOL": ["volume", "volume_ratio"],
    "IV": ["implied_volatility"],
}
HIDDEN_COLS = ("scenario", "seed", "day", "phase", "V", "P", "macro", "x")


def pin_state() -> Dict[str, object]:
    """The deployed configuration, printed and returned so every result file can carry it."""
    from envs.v2 import events_params as EP
    from envs.v2 import volatility_params as VOLP
    st = {"events_json": bool(EP.PRESENT), "control": EP.CONTROL_DEF, "dynamics": EP.DYNAMICS,
          "blowoff": EP.BLOWOFF_MODE, "post_top": f"{EP.POST_TOP_MODE}/{EP.POST_TOP_HALF_LIFE}",
          "randomise_eps_quarter": EP.RANDOMISE_EPS_QUARTER, "depth_mode": EP.DEPTH_MODE,
          "volatility_json": bool(VOLP.PRESENT), "iv": "v21" if VOLP.IV is not None else "v2"}
    try:
        from envs.v2 import observables_params as OP
        st["observables_json"] = bool(OP.PRESENT)
        st["observables"] = OP.summary() if OP.PRESENT else "absent (v2 constants)"
    except ImportError:
        st["observables_json"] = False
        st["observables"] = "loader not present (v2 constants)"
    print("[state] " + " | ".join(f"{k}={v}" for k, v in st.items()), flush=True)
    return st


def encode_nm(panel: pd.DataFrame, cap: Optional[float] = None) -> pd.DataFrame:
    """The audit-side encoding of an 'n/m' P/E: NaN -> the cap value, plus `reported_PE_nm` = 1 on those days.

    If the panel has no NaN in reported_PE (the v2 field never renders n/m) the indicator column is NOT added, so
    the baseline's feature set is exactly the audit's 18 fields."""
    out = panel.copy()
    if "reported_PE" not in out.columns:
        return out
    nm = out["reported_PE"].isna()
    if nm.any():
        if cap is None:
            try:
                from envs.v2 import observables_params as OP
                cap = float(OP.PE_CAP)
            except Exception:
                cap = float(np.nanmax(out["reported_PE"].to_numpy(float)))
        out["reported_PE_nm"] = nm.astype(float)
        out["reported_PE"] = out["reported_PE"].fillna(cap)
    return out


def shown_fields_of(panel: pd.DataFrame) -> List[str]:
    return [c for c in panel.columns if c not in HIDDEN_COLS]


# ---------------------------------------------------------------------------------------------- panel building
def _sep_jobs(n: int, seed0: int):
    jobs = []
    for s in range(seed0, seed0 + n):
        jobs += [("flat", s, {}), ("bull_trap", s, {}), ("bull_trap", 1000 + s, {"ordering": "event_first"}),
                 ("sustained_bull", s, {})]
        for d in DELTAS:
            jobs.append(("crash", s, {"crash_discount": d}))
        jobs.append(("crash", 1000 + s, {"ordering": "event_first"}))
    return jobs


def _one_panel_path(args):
    import warnings
    warnings.filterwarnings("ignore")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    from envs.synthetic_market import SyntheticMarketEnv
    from evaluation.leakage_audit import panel_from_env
    scenario, seed, kw, T, config = args
    env = SyntheticMarketEnv(scenario, T, seed, config=(dict(config) if config else None), **kw)
    f = panel_from_env(env, scenario, seed)
    if scenario == "crash" and "crash_discount" in kw:
        f["seed"] = seed * 100 + int(round(kw["crash_discount"] * 100))
    return f


def build_panel_parallel(n: int = SEP_N, T: int = 200, seed0: int = SEP_SEED0, config: Optional[Dict] = None,
                         workers: int = 3) -> pd.DataFrame:
    """audit_panel()'s exact design (same seeds, same event-first seeds, same crash seed encoding), built with a
    process pool.  `config` = GenConfig overrides applied to every path (must be pinned by the caller)."""
    jobs = [(sc, s, kw, T, config) for sc, s, kw in _sep_jobs(n, seed0)]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        frames = list(ex.map(_one_panel_path, jobs, chunksize=4))
    return pd.concat(frames, ignore_index=True)


def verify_panel_vs_generator(panel: pd.DataFrame, n_seeds: int = 2, seed0: int = SEP_SEED0,
                              config: Optional[Dict] = None) -> Dict[str, object]:
    """Regenerate the first `n_seeds` seeds' eight paths with the CURRENT generator and compare every column of the
    stored panel bit for bit.  Returns {ok, n_paths_checked, mismatched_columns}."""
    jobs = [(sc, s, kw, 200, config) for sc, s, kw in _sep_jobs(n_seeds, seed0)]
    fresh = pd.concat([_one_panel_path(j) for j in jobs], ignore_index=True)
    bad = {}
    n = 0
    for (sc, sd), g in fresh.groupby(["scenario", "seed"], sort=False):
        h = panel[(panel["scenario"] == sc) & (panel["seed"] == sd)].sort_values("day")
        g = g.sort_values("day")
        n += 1
        if len(h) != len(g):
            bad[f"{sc}-{sd}"] = "row count"
            continue
        for c in g.columns:
            if c in ("scenario", "phase", "macro"):
                if not (g[c].astype(str).to_numpy() == h[c].astype(str).to_numpy()).all():
                    bad.setdefault(f"{sc}-{sd}", []).append(c)
            else:
                a = g[c].to_numpy(float); b = h[c].to_numpy(float)
                if not np.array_equal(a, b, equal_nan=True):
                    bad.setdefault(f"{sc}-{sd}", []).append(c)
    return {"ok": not bad, "n_paths_checked": n, "mismatches": bad}
