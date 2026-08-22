"""Statistics track on a synthetic per-run table (model-level sign counts, effect sizes, BH, mixed-effects)."""
import numpy as np
import pandas as pd

from tools.stats_v2 import arm_contrasts, bh_adjust, cliffs_delta, hedges_g, run_stats


def _per_run(effect=0.1, n_models=6, n_seeds=3, rng=np.random.default_rng(0)):
    rows = []
    for m in range(n_models):
        base_m = rng.normal(0.3, 0.05)
        for p in ("ISFJ", "ENTJ"):
            for sc in ("flat",):
                for s in range(n_seeds):
                    for arm, shift in (("static", 0.0), ("memory", -effect if p == "ISFJ" else +effect)):
                        rows.append({"Model": f"m{m}", "Persona": p, "Arm": arm, "Scenario": sc, "Seed": s,
                                     "Decode_Replicate": 0, "Crash_Discount": 0.7,
                                     "mcr_0.05": base_m + shift + rng.normal(0, 0.02), "band_mas": 0.1 + shift + rng.normal(0, 0.02),
                                     "point_mas_v2": 0.2, "rg_theta_0.05": 70.0, "return_pct": 1.0, "mdd_pct": -5.0,
                                     "turnover": 1.0, "fallback_share": 0.0, "zero_trade": False, "degenerate_rg_v1": True})
    return pd.DataFrame(rows)


def test_effect_sizes_and_bh():
    assert cliffs_delta([1, 2, 3], [0, 0, 0]) == 1.0 and abs(hedges_g([1, 2, 3], [1, 2, 3])) < 1e-12
    q = bh_adjust(np.array([0.01, 0.04, 0.03, 0.5]))
    assert q[3] == 0.5 and q[0] <= 0.04 and (q >= np.array([0.01, 0.04, 0.03, 0.5])).all()


def test_contrasts_and_mixedlm(tmp_path):
    d = _per_run()
    con = arm_contrasts(d, n_boot=200)
    isfj = con[(con.Persona == "ISFJ") & (con.metric == "mcr_0.05")].iloc[0]
    entj = con[(con.Persona == "ENTJ") & (con.metric == "mcr_0.05")].iloc[0]
    assert isfj["models_improving"] == 6 and entj["models_improving"] == 0     # bidirectional by construction
    assert isfj["cliffs_delta"] < -0.5 and entj["cliffs_delta"] > 0.5
    assert isfj["delta_ci_hi"] < 0 < entj["delta_ci_lo"]
    t = run_stats(d, str(tmp_path / "stats"))
    assert (tmp_path / "stats.md").exists() and len(t["contrasts"]) and "q_bh" in t["contrasts"]
    me = t["mixedlm"]
    assert len(me) and (me["term"] != "ERROR").all()
    inter = me[(me.metric == "mcr_0.05") & me.term.str.contains(r"Arm\[T.memory\]:Persona")]
    assert len(inter) == 1 and inter["p"].iloc[0] < 0.05                     # the arm x persona interaction
