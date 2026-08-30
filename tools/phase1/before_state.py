"""
v2.1 Phase 1: generate the BEFORE panels from the frozen v2 generator (Phase 0 freeze) before any generator change
(PREREG_PHASE_1.md section 11). Run at the Phase-0 freeze only; the stored outputs are the record.

    python -m tools.phase1.before_state sep       # SEP panel (200 seeds, audit composition) -> scratch pickle
    python -m tools.phase1.before_state s11       # E1.1 'fixed' mechanism: 500 seeds x 4 scenarios -> scratch pickle
    python -m tools.phase1.before_state s15       # E1.5 day-1 states at burn-in 260, 5 engines x 500 seeds -> generated
    python -m tools.phase1.before_state checklist # SCL checklist (200 seeds, seed0 40000) -> generated/v2_1/e1_6_checklist_before
    python -m tools.phase1.before_state hashes    # path_hashes_phase1_before.json
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
SCRATCH = os.environ.get("PHASE1_SCRATCH", os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "_panels"))
SEP_SEED0, SEP_N = 30000, 200
S11_SEED0, S11_N = 50000, 500
S15_SEED0, S15_N = 80000, 500
SCL_SEED0, SCL_N = 40000, 200
ENGINES = ("fw_fallback_hl150", "fw_hl60", "fw_index", "pruna", "ar1")
SCENARIOS4 = ("flat", "crash", "bull_trap", "sustained_bull")


def _env_panel(kw):
    from envs.synthetic_market import SyntheticMarketEnv
    from evaluation.leakage_audit import panel_from_env
    kw = dict(kw)
    env = SyntheticMarketEnv(**kw)
    pan = panel_from_env(env, env.scenario, env.seed)
    return pan, env.data.copy(), float(getattr(env.result, "k_render", 1.0))


def sep(tag: str = "before"):
    from envs.synthetic_market import audit_panel
    t0 = time.time()
    panel = audit_panel(SEP_N, 200, seed0=SEP_SEED0)
    os.makedirs(SCRATCH, exist_ok=True)
    panel.to_pickle(os.path.join(SCRATCH, f"sep_{tag}.pkl"))
    print(f"SEP {tag}: {panel[['scenario', 'seed']].drop_duplicates().shape[0]} paths, {len(panel)} rows, {time.time() - t0:.0f} s")


def s11(tag: str = "fixed", workers: int = 6, config=None):
    """E1.1 panel for one mechanism: 500 seeds x 4 scenarios; panels and env.data stored (the rule-100 test needs data)."""
    t0 = time.time()
    jobs = []
    for sc in SCENARIOS4:
        for s in range(S11_SEED0, S11_SEED0 + S11_N):
            kw = {"scenario": sc, "n_days": 200, "seed": s}
            if sc == "crash":
                kw["crash_discount"] = 0.70
            if config:
                kw["config"] = dict(config)
            jobs.append(kw)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        res = list(ex.map(_env_panel, jobs, chunksize=4))
    panel = pd.concat([r[0] for r in res], ignore_index=True)
    data = {(j["scenario"], j["seed"]): r[1] for j, r in zip(jobs, res)}
    kr = {(j["scenario"], j["seed"]): r[2] for j, r in zip(jobs, res)}
    os.makedirs(SCRATCH, exist_ok=True)
    panel.to_pickle(os.path.join(SCRATCH, f"s11_{tag}_panel.pkl"))
    pd.to_pickle(data, os.path.join(SCRATCH, f"s11_{tag}_data.pkl"))
    pd.to_pickle(kr, os.path.join(SCRATCH, f"s11_{tag}_krender.pkl"))
    print(f"S11 {tag}: {len(jobs)} paths, {len(panel)} rows, {time.time() - t0:.0f} s")


def _day1_state(kw):
    from envs.v2.generator import GenConfig, generate
    r = generate(GenConfig(**kw))
    i = int(np.where(r.day == 1)[0][0])
    return (r.x[0, i], r.sigma[0, i] ** 2, r.n_f[0, i])


def s15(tag: str = "before", workers: int = 6, burn_in=None):
    """Day-1 (x, sigma^2, n_f) per engine at 500 flat seeds under the burn-in in force (or `burn_in` per engine)."""
    t0 = time.time()
    out = {}
    for eng in ENGINES:
        jobs = [{"scenario": "flat", "T": 200, "seed": s, "engine": eng, "reject": False,
                 **({"burn_in": int(burn_in[eng])} if burn_in else {})} for s in range(S15_SEED0, S15_SEED0 + S15_N)]
        with ProcessPoolExecutor(max_workers=workers) as ex:
            st = np.array(list(ex.map(_day1_state, jobs, chunksize=10)))
        out[eng] = st
        print(f"  {eng}: sd(x_1) {st[:, 0].std():.4f}, mean sigma2 {st[:, 1].mean():.2e}, mean n_f {st[:, 2].mean():.4f}")
    os.makedirs(os.path.join(GEN, "e1_5"), exist_ok=True)
    np.savez(os.path.join(GEN, "e1_5", f"day1_states_{tag}.npz"), **out, seeds=np.arange(S15_SEED0, S15_SEED0 + S15_N))
    print(f"S15 {tag}: {time.time() - t0:.0f} s")


def checklist(tag: str = "before"):
    from envs.synthetic_market import checklist_paths
    from evaluation.stylized_facts import run_checklist, to_markdown
    t0 = time.time()
    paths = checklist_paths(SCL_N, 200, seed0=SCL_SEED0)
    df = run_checklist(paths)
    out = os.path.join(GEN, f"e1_6_checklist_{tag}.md")
    pre = (f"Generator v2 ({tag}); {SCL_N} seeds per scenario (crash: per delta), T = 200, seeds from {SCL_SEED0} (SCL, PREREG_PHASE_1.md "
           "section 2). Items 14 and 16 come from the leakage audit; 18 and 19 are unit tests.")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(to_markdown(df, f"Section 9 validation checklist, standard checklist panel ({tag})", pre))
    df.to_csv(out.replace(".md", ".csv"), index=False)
    print(df[["item", "property", "pass"]].to_string(index=False))
    print(f"checklist {tag}: {time.time() - t0:.0f} s -> {out}")


# The frozen-equivalent GenConfig for runs that must generate under the Phase-0 freeze after the generator changed
# (L5 before-row): every hidden column (price, fundamental_value, x, phase, garch_sigma, n_f, ...) reproduces the stored
# Phase-1 before-hashes on all 95 manifest configurations (frozen_check below); the rendered EPS / dividend fields differ
# only in the announcement-lag draw, which moved to its own RNG stream ("announce") -- same distribution, different draw.
FROZEN_CFG = {"start_price_mode": "fixed", "sigma_V": 0.006, "df_V": 5.0, "mu_V": 0.00025, "jump_placement": "x_negmean",
              "jump_rate": 0.010, "jump_mean": -0.04, "jump_sd": 0.03, "burn_in": 260, "burn_in_mode": "long"}


def frozen_check(tag: str = "before"):
    """Verify FROZEN_CFG against path_hashes_phase1_<tag>.json column by column; writes e1_6/frozen_equivalent_check.json."""
    from tools.path_hashes import hash_config
    ref = json.load(open(os.path.join(GEN, f"path_hashes_phase1_{tag}.json"), encoding="utf-8"))
    rows = []
    for entry in ref["configs"]:
        kw = dict(entry["config"]); kw["config"] = dict(FROZEN_CFG, **kw.get("config", {}))
        h = hash_config(kw)
        rows.append({"config": entry["config"], "differ": [c for c, v in entry["columns"].items() if h["columns"].get(c) != v]})
    hidden = ("price", "fundamental_value", "x", "phase", "garch_sigma", "n_f")
    out = {"frozen_cfg": FROZEN_CFG, "n_configs": len(rows),
           "hidden_columns_identical": int(sum(not any(c in r["differ"] for c in hidden) for r in rows)),
           "all_columns_identical": int(sum(not r["differ"] for r in rows)),
           "differing_columns": sorted({c for r in rows for c in r["differ"]}), "rows": rows}
    os.makedirs(os.path.join(GEN, "e1_6"), exist_ok=True)
    with open(os.path.join(GEN, "e1_6", "frozen_equivalent_check.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"frozen check: hidden columns identical on {out['hidden_columns_identical']}/{len(rows)}; all columns on {out['all_columns_identical']}; differing: {out['differing_columns']}")


def hashes(tag: str = "before"):
    from tools.path_hashes import build
    build(os.path.join(GEN, f"path_hashes_phase1_{tag}.json"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("task", choices=["sep", "s11", "s15", "checklist", "hashes", "frozen_check"])
    ap.add_argument("--tag", default=None)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--config", default=None, help="JSON GenConfig overrides for s11 (e.g. the start-price mechanism)")
    a = ap.parse_args()
    if a.task == "sep":
        sep(a.tag or "before")
    elif a.task == "s11":
        import json as _json
        s11(a.tag or "fixed", a.workers, config=_json.loads(a.config) if a.config else None)
    elif a.task == "s15":
        s15(a.tag or "before", a.workers)
    elif a.task == "checklist":
        checklist(a.tag or "before")
    elif a.task == "frozen_check":
        frozen_check(a.tag or "before")
    else:
        hashes(a.tag or "before")
