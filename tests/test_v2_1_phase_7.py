"""
v2.1 Phase 7 regression tests (plan Section 11.4; PREREG_PHASE_7.md 9, 10).

Two kinds of test:

* **the section's own** -- `test_theta_in_force_with_provenance`, `test_mcr_decomposition_identity`,
  `test_floor_ceiling_signs`, `test_gate_common_start_only`, `test_baselines_same_path_hash`,
  `test_dividends_paid`, `test_trader_band_free`;
* **the inertness of every switch** -- each of the seven switches in PREREG 9 must reproduce the pre-Phase-7
  behaviour when off.  The v2 code path is the one every published number was computed on, so "off" has to mean
  bit for bit, and these are the tests that say so.

    python -m pytest tests/test_v2_1_phase_7.py -q
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
pytestmark = pytest.mark.filterwarnings("ignore")

from evaluation import scoring as SC                       # noqa: E402
from evaluation import scoring_params as SP                # noqa: E402
from evaluation import targets as TG                       # noqa: E402
from evaluation.metrics_v2 import (THETAS, floors_and_ceilings, oracle_target,  # noqa: E402
                                   score_run, thetas_in_force)


def _gen(rel):
    p = os.path.join(GEN, rel)
    if not os.path.exists(p):
        pytest.skip(f"{rel} not generated in this working tree")
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _synthetic_run(n=60, seed=0, persona="ISFJ"):
    """A run frame in the run-CSV column convention, with an x path that crosses every theta in both directions."""
    rng = np.random.default_rng(seed)
    x = np.concatenate([np.linspace(-0.3, 0.3, n // 2), rng.normal(0, 0.1, n - n // 2)])
    V = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.005, n)))
    P = V * np.exp(x)
    C = np.clip(rng.random(n), 0, 1)
    pv = 10000.0 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    return pd.DataFrame({"Day": np.arange(1, n + 1), "Cash_Share": C, "Price": P, "Fundamental_Value": V, "x": x,
                         "Portfolio_Value": pv, "Cash": pv * C, "Holdings_Value": pv * (1 - C),
                         "Action": np.where(np.diff(np.concatenate([[C[0]], C])) > 0.01, "SELL", "HOLD"),
                         "Traded_Value": np.abs(np.diff(np.concatenate([[C[0]], C]))) * pv,
                         "Cost_Paid": 0.0, "Parse_Status": "ok", "Start_Cash_Share": TG.centre(persona)})


# ===========================================================================================  Section 11.4 tests
def test_theta_in_force_with_provenance():
    """The scoring parameter file carries every registered field, is readable through the loud loader, and does
    NOT yet carry a theta in force -- which must raise, not default (PREREG 1.4, 10; P6-12's lesson)."""
    if not SP.PRESENT:
        pytest.skip("evaluation/params/scoring.json absent (v2 constants remain in force)")
    doc = SP.load()
    for blk in SP.REQUIRED:
        assert blk in doc, f"scoring.json is missing the registered block {blk!r}"
        for f in SP.PROVENANCE_FIELDS:
            assert f in doc[blk], f"scoring.json block {blk!r} is missing {f!r}"
        assert doc[blk]["status"] in doc["_status_key"], f"{blk}: undeclared status"
        assert doc[blk]["interval"] is not None and doc[blk]["n"] is not None
        assert doc[blk]["date"] and doc[blk]["source"]

    # the three derived thetas are present with their inputs, and each matches its own result file
    tcv = _gen("e7_1/theta_cost_var.json")
    assert doc["theta_cost"]["value"] == pytest.approx(tcv["theta_cost"]["value"], rel=0, abs=0)
    assert doc["theta_var"]["value"] == pytest.approx(tcv["theta_var"]["value"], rel=0, abs=0)
    ti = _gen("e7_1/theta_info.json")
    loc = {(r["scope"], r["population"], r["feature_set"]): r for r in ti["located"]}
    assert doc["theta_info"]["value"]["pooled_all"] == loc[("pooled", "all", "full")]["theta_info"]
    assert doc["theta_info"]["value"]["pooled_calm"] == loc[("pooled", "calm", "full")]["theta_info"]

    # the cost tier in the file is the cost tier the simulator charges
    from simulation.runner_v2 import RunConfig
    from simulation.portfolio_v2 import DEAD_BAND
    assert doc["cost_tier"]["value"] == RunConfig.cost_bp
    assert doc["dead_band"]["value"] == DEAD_BAND
    assert doc["half_width"]["value"] == TG.HALF_WIDTH

    # theta_in_force is written only after D7 and D8.  Both were recorded on 10 Sep 2026 (DECISION_LOG P7-4,
    # P7-5), so the block is present and carries the co-primary pair with its provenance; before that the loader
    # raised rather than defaulting, and `test_scoring_params_absent_keeps_v2_thetas` still exercises that path.
    tif = SP.theta_in_force()
    for f in SP.PROVENANCE_FIELDS:
        assert f in tif, f"theta_in_force is missing {f!r}"
    assert tif["status"] in doc["_status_key"]
    v = tif["value"]
    assert set(v["thetas"]) == {doc["theta_cost"]["value"], doc["theta_info"]["value"]["pooled_all"]},         "the thetas in force are not the co-primary pair D7 recorded"
    assert v["reported_per_population"]["calm"] == doc["theta_info"]["value"]["pooled_calm"]
    assert "coverage" in v["calm_caveat"] and "1,089" in v["calm_caveat"]
    assert "theta-conditional" in v["g3_is_theta_conditional"] or "theta >= 0.066" in v["g3_is_theta_conditional"]
    # the v2 module constant does NOT move; only the v2_1 path reads the file
    assert tuple(THETAS) == (0.03, 0.05, 0.08)
    assert tuple(thetas_in_force()) == tuple(sorted(v["thetas"]))


def test_mcr_decomposition_identity():
    """B + D reconstructs MCR on every step, D >= 0, and the degenerate cases behave (PREREG 2.1)."""
    for seed in range(12):
        for persona in ("ISFJ", "INTJ", "ENTJ", "TRADER"):
            df = _synthetic_run(seed=seed, persona=persona)
            C = df["Cash_Share"].to_numpy(float); x = df["x"].to_numpy(float)
            for th in (0.002, 0.03, 0.05, 0.08, 0.12, 0.2):
                t = SC.regret_terms(C, x, th, persona, prev_target=float(C[0]))
                if not np.isfinite(t["mcr"]):
                    continue
                assert t["mcr"] == pytest.approx(t["mcr_B"] + t["mcr_D"], abs=1e-12), \
                    f"MCR != B + D at theta={th}, persona={persona}"
                assert t["mcr_D"] >= -1e-12, "D is negative: the oracle target left the band"
                assert t["mcr_B"] >= -1e-12

    # per-step identity, including the degenerate placements
    c2, hw = SC.centre_and_hw("ISFJ")
    lo, hi = c2 - hw, c2 + hw
    C = np.array([lo, hi, c2, 0.0, 1.0, lo - 0.3, hi + 0.3])
    for tgt_val in (lo, hi, c2):
        tgt = np.full(len(C), tgt_val)
        B, D = SC.decompose(C, tgt, c2, hw)
        assert np.allclose(B + D, np.abs(C - tgt), atol=1e-12)
        assert (D >= -1e-12).all()
    # a zero half-width is the point-target limit and still reconstructs
    B, D = SC.decompose(C, np.full(len(C), c2), c2, 0.0)
    assert np.allclose(B + D, np.abs(C - c2), atol=1e-12)


def test_oracle_target_series_matches_loop():
    """The vectorised oracle used by every Phase-7 re-score is the v2 loop, exactly (rule 12: one construction)."""
    rng = np.random.default_rng(7)
    for _ in range(150):
        n = int(rng.integers(3, 250))
        x = rng.normal(0, 0.09, n)
        th = float(rng.choice([0.002, 0.03, 0.05, 0.08, 0.12, 0.2, 0.4]))
        persona = str(rng.choice(["ISFJ", "INTJ", "ENTJ", "TRADER"]))
        pt = float(rng.random())
        lo, hi = TG.band(persona)
        a = SC.oracle_target_series(x, th, lo, hi, pt)
        b = oracle_target(x, th, persona, prev_target=pt)
        assert np.array_equal(a, b), "the vectorised oracle differs from metrics_v2.oracle_target"
    # a path that never crosses: the target stays at the clipped seed
    x = np.zeros(20)
    assert np.allclose(SC.oracle_target_series(x, 0.05, 0.7, 0.9, 0.2), 0.7)


def test_regret_terms_batch_matches_scalar():
    """The batch scorer the panel re-score uses reproduces the per-run functions (rule 12)."""
    rng = np.random.default_rng(11)
    for _ in range(25):
        n = 200
        x = rng.normal(0, 0.08, n)
        C = rng.random((8, n))
        th = float(rng.choice([0.002, 0.03, 0.05, 0.12, 0.2]))
        persona = str(rng.choice(["ISFJ", "INTJ", "ENTJ"]))
        pv = C[:, 0]
        bt = SC.regret_terms_batch(C, x, th, persona, pv)
        for r in range(8):
            sc = SC.regret_terms(C[r], x, th, persona, prev_target=float(pv[r]))
            wn = SC.regret_terms_window(C[r], x, th, persona, prev_target=float(pv[r]))
            for k in ("mcr", "mcr_B", "mcr_D", "oracle_switches", "share_target_lo", "share_target_hi",
                      "share_agent_outside", "coverage"):
                assert float(bt[k][r]) == pytest.approx(float(sc[k]), abs=1e-12, nan_ok=True), k
            for k in ("mcr_window", "mcr_window_B", "mcr_window_D", "window_switches"):
                assert float(bt[k][r]) == pytest.approx(float(wn[k]), abs=1e-12, nan_ok=True), k


def test_floor_ceiling_signs():
    """One function decides every orientation; the v2_1 convention puts the oracle at the ceiling and the worst
    trivial policy at the floor, for BOTH orientations (PREREG 2.2, weakness 53)."""
    # lower-is-better: 0 is the oracle (best), 0.4 the worst trivial
    base = {
        "mandate_conditional_oracle": {"mcr": 0.0, "band_mas": 0.0, "return_pct": 12.0, "mdd_pct": -3.0},
        "always_hold": {"mcr": 0.15, "band_mas": 0.05, "return_pct": 4.0, "mdd_pct": -20.0},
        "always_buy": {"mcr": 0.40, "band_mas": 0.30, "return_pct": 9.0, "mdd_pct": -35.0},
        "always_sell": {"mcr": 0.25, "band_mas": 0.20, "return_pct": 0.0, "mdd_pct": 0.0},
        "random": {"mcr": 0.30, "band_mas": 0.22, "return_pct": 1.0, "mdd_pct": -18.0},
        "band_lo": {"mcr": 0.10, "band_mas": 0.0, "return_pct": 6.0, "mdd_pct": -12.0},
        "band_hi": {"mcr": 0.12, "band_mas": 0.0, "return_pct": 2.0, "mdd_pct": -6.0},
        "constant_mix": {"mcr": 0.11, "band_mas": 0.0, "return_pct": 3.0, "mdd_pct": -9.0},
    }
    fc = SC.floors_and_ceilings_v21(base, "ISFJ")
    assert fc["mcr"]["ceiling"] == 0.0 and fc["mcr"]["floor"] == 0.40          # worst = LARGEST for lower-better
    assert fc["return_pct"]["ceiling"] == 12.0 and fc["return_pct"]["floor"] == 0.0   # worst = SMALLEST for higher
    assert fc["mdd_pct"]["ceiling"] == -3.0 and fc["mdd_pct"]["floor"] == -35.0

    # normalise: 1.0 at the ceiling and 0.0 at the floor, whichever way the metric points
    for m in ("mcr", "band_mas", "return_pct", "mdd_pct"):
        f, c = fc[m]["floor"], fc[m]["ceiling"]
        assert SC.normalise_metric(c, f, c, m) == pytest.approx(1.0)
        assert SC.normalise_metric(f, f, c, m) == pytest.approx(0.0)
        mid = SC.normalise_metric((f + c) / 2, f, c, m)
        assert 0.0 < mid < 1.0
    # an unregistered metric must raise rather than be given a silent orientation
    with pytest.raises(KeyError):
        SC.normalise_metric(1.0, 0.0, 2.0, "not_a_registered_metric")
    # a degenerate pair is flagged, not silently normalised
    bad = dict(base); bad["mandate_conditional_oracle"] = {"mcr": 0.9}
    assert SC.floors_and_ceilings_v21(bad, "ISFJ")["mcr"]["degenerate"] is True


def test_trader_band_free():
    """(0, 1) in EVERY place that computes a band for the arms with no mandate (E7.7, weakness item 73)."""
    from evaluation.baselines_v2 import baseline_policies
    from evaluation.observables_oracle import ObservablesOracle
    for p in ("NONE", "TRADER"):
        assert TG.band(p) == (0.0, 1.0)
        assert TG.half_width(p) == 0.5
        assert TG.centre(p) == 0.5                      # unchanged
        assert TG.band_mas(0.0, p) == 0.0 and TG.band_mas(1.0, p) == 0.0
        assert SC.band_of(p) == (0.0, 1.0)
        # the oracle's targets are the band edges 0 and 1
        t = oracle_target(np.array([0.2, -0.2]), 0.05, p, prev_target=0.5)
        assert t[0] == 1.0 and t[1] == 0.0
        # the baseline policy set's mandate oracle uses the same edges
        pol = baseline_policies(p, 0.5)["mandate_conditional_oracle"][0]
        assert pol(0, {"x": 0.2}, {"cash_share": 0.5}, {}) == 1.0
        assert pol(0, {"x": -0.2}, {"cash_share": 0.5}, {}) == 0.0
        # and so does the L5 surrogate policy
        o = ObservablesOracle(theta=0.05)
        s = o.policy(p, np.array([0.2, -0.2]), 0.5)
        assert s[0] == 1.0 and s[1] == 0.0
    # the seven mandated personas are untouched -- the prompts that quote a band cannot have moved
    assert TG.band("ISFJ") == (0.70, 0.90) and TG.band("INTJ") == (0.40, 0.60) and TG.band("ENTJ") == (0.00, 0.20)
    for p in TG.V1_POINT_TARGETS:
        assert TG.half_width(p) == TG.HALF_WIDTH


def test_jfe_ordering_check_withdrawn():
    """E7.3: the JFE spread is not derivable from Table 7, so the ordering check may not run and the constant
    carries its withdrawal reason (PREREG 3.3)."""
    assert TG.jfe_ordering_check_available() is False
    assert hasattr(TG, "JFE_SPREAD_WITHDRAWN") and not hasattr(TG, "JFE_SPREAD")
    assert "Table 7" in TG.JFE_SPREAD_WITHDRAWN_REASON


def test_dividends_paid():
    """E7.4 / D10: the DPS is credited to cash on the generator's own ex-dates, the portfolio identity holds at
    every step, and nothing else moves cash."""
    from envs.synthetic_market import SyntheticMarketEnv
    from simulation.dividends import dividend_schedule
    from simulation.portfolio_v2 import PortfolioV2
    env = SyntheticMarketEnv("flat", 200, 7)
    d = env.data[env.data["asset"] == 0].reset_index(drop=True)
    P = d["price"].to_numpy(float)
    sched = dividend_schedule(env, n_assets=1, n_days=len(P))
    assert sched.shape == (len(P), 1)
    ex_days = np.where(sched[:, 0] != 0)[0]
    assert len(ex_days) >= 2, "a 200-day path should carry at least two quarterly ex-dates"
    # the ex-dates are exactly the announcement days, and the amount is that day's dps_quarterly
    since = d["days_since_eps_announcement"].to_numpy(float)
    assert set(ex_days.tolist()) == set(np.where(since == 0)[0].tolist())
    assert np.allclose(sched[ex_days, 0], d["dps_quarterly"].to_numpy(float)[ex_days])

    # buy and hold, no trading after day 1: cash grows by exactly the dividends
    port = PortfolioV2(10000.0, 0.5, P[0], dividends=True)
    qty = port.holdings_qty[0]
    cash0 = port.cash
    expected = 0.0
    for t in range(len(P)):
        if sched[t, 0] != 0:
            port.pay_dividend(float(sched[t, 0]), t + 1)
            expected += qty * float(sched[t, 0])
        assert port.total_value(P[t]) == pytest.approx(port.cash + port.holdings_qty[0] * P[t], abs=1e-9)
    assert port.holdings_qty[0] == qty, "paying a dividend must not change the share count"
    assert port.cash - cash0 == pytest.approx(expected, abs=1e-9)
    assert port.dividends_paid_total == pytest.approx(expected, abs=1e-9)
    assert len(port.dividend_records) == len(ex_days)

    # the same path with dividends off is the v2 behaviour exactly
    off = PortfolioV2(10000.0, 0.5, P[0], dividends=False)
    for t in range(len(P)):
        off.pay_dividend(float(sched[t, 0]), t + 1)
    assert off.cash == 10000.0 * 0.5 and off.dividends_paid_total == 0.0


def test_dividends_switch_inert_on_baselines():
    """Every baseline's metrics are identical with dividends=False -- the default (PREREG 9)."""
    from envs.synthetic_market import SyntheticMarketEnv
    from evaluation.baselines_v2 import baseline_metrics
    from simulation.dividends import dividend_schedule
    env = SyntheticMarketEnv("flat", 200, 7)     # seed 7 is a PAYER; a 60-day path can carry no ex-date at all
    assert dividend_schedule(env, 1, 200).sum() > 0, "seed 7 was expected to be a dividend payer"
    a = baseline_metrics(env, "INTJ", 0.5, random_seeds=2)
    b = baseline_metrics(env, "INTJ", 0.5, random_seeds=2, dividends=False)
    assert set(a) == set(b)
    for pol in a:
        for k, v in a[pol].items():
            if isinstance(v, (int, float)) and not isinstance(v, bool) and np.isfinite(v):
                assert b[pol][k] == pytest.approx(v, abs=0, rel=0), f"{pol}.{k} moved with dividends=False"
    # and dividends=True does move the money metrics (the switch is not a no-op when on)
    c = baseline_metrics(env, "INTJ", 0.5, random_seeds=2, dividends=True)
    assert c["always_hold"]["return_pct"] > a["always_hold"]["return_pct"]

    # a NON-payer seed pays nothing even with the switch on -- the FIT payer share is a per-seed draw, so
    # "dividends on" does not mean "every path receives cash", and the report says so
    env0 = SyntheticMarketEnv("flat", 200, 3)
    assert dividend_schedule(env0, 1, 200).sum() == 0, "seed 3 was expected to be a non-payer"
    d0 = baseline_metrics(env0, "INTJ", 0.5, random_seeds=2, dividends=True)
    e0 = baseline_metrics(env0, "INTJ", 0.5, random_seeds=2, dividends=False)
    assert d0["always_hold"]["return_pct"] == pytest.approx(e0["always_hold"]["return_pct"], abs=0, rel=0)


def test_score_run_v2_inert():
    """`score_run(scoring="v2")` returns the v2 dictionary bit for bit; "v2_1" only ADDS keys (PREREG 9)."""
    df = _synthetic_run(seed=5)
    a = score_run(df, "ISFJ")
    b = score_run(df, "ISFJ", scoring="v2")
    c = score_run(df, "ISFJ", scoring="v2_1")
    assert a.keys() == b.keys()
    for k in a:
        assert (a[k] == b[k]) or (isinstance(a[k], float) and np.isnan(a[k]) and np.isnan(b[k]))
    assert set(a).issubset(set(c)), "the v2_1 scoring dropped a v2 key"
    for k in a:
        assert (c[k] == a[k]) or (isinstance(a[k], float) and np.isnan(a[k]) and np.isnan(c[k])), \
            f"the v2_1 scoring changed the v2 key {k!r}"
    assert any(k.startswith("v21_") for k in c)
    with pytest.raises(ValueError):
        score_run(df, "ISFJ", scoring="v3")


def test_score_run_v2_1_decomposition_matches_v2_mcr():
    """The added decomposition is a decomposition OF the v2 MCR, not of a different statistic."""
    df = _synthetic_run(seed=9)
    c = score_run(df, "ISFJ", scoring="v2_1")
    inforce = tuple(thetas_in_force())
    assert inforce, "no thetas in force"
    for th in inforce:
        # the decomposition reconstructs itself at every theta in force
        assert c[f"v21_mcr_{th}"] == pytest.approx(c[f"v21_mcr_B_{th}"] + c[f"v21_mcr_D_{th}"], abs=1e-12)
    for th in set(inforce) & set(THETAS):
        # and where a theta in force is also a v2 theta, it is the SAME statistic the v2 path computes
        assert c[f"v21_mcr_{th}"] == pytest.approx(c[f"mcr_{th}"], abs=1e-12)


def test_floors_and_ceilings_v2_inert():
    """`floors_and_ceilings(convention="v2")` is unchanged; "v2_1" is the new convention (PREREG 9)."""
    base = {"mandate_conditional_oracle": {"mcr_0.05": 0.0, "band_mas": 0.0, "rg_v1": 90.0, "return_pct": 10.0,
                                           "mdd_pct": -2.0, "point_mas_v1": 0.1, "point_mas_v2": 0.1,
                                           "relative_mas": 0.1, "rg_theta_0.05": 90.0, "rg_action_0.05": 90.0},
            "constant_mix": {"mcr_0.05": 0.11, "band_mas": 0.0, "rg_v1": 50.0, "return_pct": 3.0, "mdd_pct": -9.0,
                             "point_mas_v1": 0.2, "point_mas_v2": 0.0, "relative_mas": 0.0,
                             "rg_theta_0.05": 50.0, "rg_action_0.05": 50.0},
            "always_hold": {"mcr_0.05": 0.15, "band_mas": 0.05, "rg_v1": 40.0, "return_pct": 4.0, "mdd_pct": -20.0,
                            "point_mas_v1": 0.3, "point_mas_v2": 0.1, "relative_mas": 0.0,
                            "rg_theta_0.05": 40.0, "rg_action_0.05": 40.0},
            "always_buy": {"mcr_0.05": 0.40, "band_mas": 0.30, "rg_v1": 30.0, "return_pct": 9.0, "mdd_pct": -35.0,
                           "point_mas_v1": 0.8, "point_mas_v2": 0.4, "relative_mas": 0.4,
                           "rg_theta_0.05": 30.0, "rg_action_0.05": 30.0},
            "always_sell": {"mcr_0.05": 0.25, "band_mas": 0.20, "rg_v1": 20.0, "return_pct": 0.0, "mdd_pct": 0.0,
                            "point_mas_v1": 0.2, "point_mas_v2": 0.3, "relative_mas": 0.3,
                            "rg_theta_0.05": 20.0, "rg_action_0.05": 20.0},
            "random": {"mcr_0.05": 0.30, "band_mas": 0.22, "rg_v1": 33.0, "return_pct": 1.0, "mdd_pct": -18.0,
                       "point_mas_v1": 0.5, "point_mas_v2": 0.25, "relative_mas": 0.25,
                       "rg_theta_0.05": 33.0, "rg_action_0.05": 33.0},
            "buy_day1_hold": {"mcr_0.05": 0.35, "band_mas": 0.28, "rg_v1": 35.0, "return_pct": 8.0, "mdd_pct": -30.0,
                              "point_mas_v1": 0.7, "point_mas_v2": 0.35, "relative_mas": 0.35,
                              "rg_theta_0.05": 35.0, "rg_action_0.05": 35.0}}
    a = floors_and_ceilings(base, "ISFJ")
    b = floors_and_ceilings(base, "ISFJ", convention="v2")
    assert a == b
    assert a["mcr_0.05"]["ceiling"] == 0.11, "the v2 convention's MCR ceiling is constant-mix; it moved"
    c = floors_and_ceilings(base, "ISFJ", convention="v2_1")
    # the v2_1 convention resolves an orientation through `scoring.orientation`, so it applies to the v2 key
    # names (`mcr_0.05`) as well as to the v2_1 ones (`mcr`) -- one sign table, whatever the key is called
    assert c["mcr_0.05"]["ceiling"] == 0.0, "the v2_1 convention's ceiling is the mandate oracle"
    assert c["mcr_0.05"]["floor"] == 0.40, "the v2_1 convention's floor is the WORST trivial policy"
    assert SC.orientation("mcr_0.05") is False and SC.orientation("v21_mcr_0.12") is False
    assert SC.orientation("return_pct") is True
    with pytest.raises(ValueError):
        floors_and_ceilings(base, "ISFJ", convention="v3")


def test_portfolio_next_open_logs_pre_and_post(monkeypatch):
    """Weakness 60: under next-open execution the record no longer calls the PRE-trade share 'after'."""
    from simulation.portfolio_v2 import PortfolioV2
    p = PortfolioV2(10000.0, 0.5, 100.0)
    rec = p.retarget(0.9, 100.0, 1, execution="next_open")
    assert rec["pending"] is True
    assert rec["cash_share_before"] == pytest.approx(0.5) and rec["cash_share_after"] == pytest.approx(0.5)
    settled = p.settle_pending(100.0, 2)
    assert settled["cash_share_before"] == pytest.approx(0.5)
    assert settled["cash_share_after"] == pytest.approx(0.9, abs=1e-3)
    assert settled["cash_share_after"] != settled["cash_share_before"]


def test_gate_common_start_only():
    """E7.5: the day-1 gate exists for common-start rows only and the delta-C_1 table is gone (weakness 54)."""
    # `gate_tables` is the gate on its own; `salience_tables` calls it after the salience surrogate, which is a
    # separate measurement with its own permutation null and is not what this test is about.
    from tools.report_v2 import gate_tables
    template = {"Target_Cash_Share": 0.5, "Decode_Replicate": 0, "Mandate_Block": "mandate", "Price": 100.0,
                "Portfolio_Value": 10000.0, "x": 0.0, "RSI14": 50.0, "trend_strength": 0.0}
    rng = np.random.default_rng(3)
    rows = []
    for design, personas in (("common", ("ISFJ", "INTJ", "ENTJ")), ("target", ("ISFJ", "INTJ", "ENTJ"))):
        for persona in personas:
            for seed in range(4):
                for day in (1, 2):
                    rows.append({**template, "Model": "m", "Persona": persona, "Arm": "static", "Scenario": "flat",
                                 "Seed": seed, "Day": day, "Start_Design": design,
                                 "Start_Cash_Share": 0.5 if design == "common" else TG.centre(persona),
                                 "Cash_Share": float(np.clip(TG.centre(persona) + rng.normal(0, 0.02), 0, 1)),
                                 "Parse_Status": "ok", "Crash_Discount": 0.7, "Cost_bp": 5.0,
                                 "Target_Cash_Share": float(TG.centre(persona)), "Mandate_Block": "mandate",
                                 "Price": 100.0, "Portfolio_Value": 10000.0, "x": 0.0,
                                 "RSI14": 50.0, "trend_strength": 0.0})
    df = pd.DataFrame(rows)
    out = gate_tables(df)
    assert "gate_common_start" in out
    assert "exploratory_deltaC1_start_at_target" not in out, "the ill-posed delta-C_1 table is still produced"
    assert "gate_removed_note" in out and "ill-posed" in out["gate_removed_note"]["reason"].iloc[0]
    # the null is reported either way -- as a table when the arms exist, as NOT COMPUTABLE when they do not
    assert "gate_common_start_null" in out
    assert out["gate_common_start_null"]["status"].iloc[0] == "NOT COMPUTABLE"
    assert "no persona text" in out["gate_common_start_null"]["reason"].iloc[0]

    # with a no-persona arm present the null IS computed
    extra = []
    for persona in ("NONE", "TRADER"):
        for seed in range(4):
            extra.append({**template, "Model": "m", "Persona": persona, "Arm": "numerical_only", "Scenario": "flat",
                          "Seed": seed, "Day": 1, "Start_Design": "common", "Start_Cash_Share": 0.5,
                          "Cash_Share": float(rng.random()), "Parse_Status": "ok",
                          "Crash_Discount": 0.7, "Cost_bp": 5.0, "Target_Cash_Share": 0.5,
                          "Mandate_Block": "none", "Price": 100.0, "Portfolio_Value": 10000.0, "x": 0.0,
                          "RSI14": 50.0, "trend_strength": 0.0})
    out2 = gate_tables(pd.concat([df, pd.DataFrame(extra)], ignore_index=True))
    assert "status" not in out2["gate_common_start_null"].columns
    assert out2["gate_common_start_null"]["arm_population"].iloc[0].startswith("null")


def test_baselines_same_path_hash(tmp_path):
    """E7.6 / weakness 56: the baselines are built on the run's OWN path -- the environment rebuilt from
    `meta.json` reproduces the run's price series exactly, and the run-CSV path cannot express it."""
    import hashlib
    from envs.synthetic_market import SyntheticMarketEnv
    from tools.phase7.e7_6_baselines import env_from_meta
    from tools.report_v2 import cell_baselines, _BASE_CACHE

    # a cell whose configuration the seven run-CSV columns CANNOT express: a non-default b_pred
    env = SyntheticMarketEnv("crash", 60, 11, crash_discount=0.55, b_pred=0.0)
    d = env.data[env.data["asset"] == 0].reset_index(drop=True)
    meta = {"env_metadata": env.get_metadata(), "run_config": {"persona": "INTJ"}, "provenance": {}}
    run = pd.DataFrame({"Day": np.arange(1, len(d) + 1), "Cash_Share": 0.5, "Price": d["price"].values,
                        "Fundamental_Value": d["fundamental_value"].values, "x": d["x"].values,
                        "Portfolio_Value": 10000.0, "Cash": 5000.0, "Holdings_Value": 5000.0,
                        "Action": "HOLD", "Traded_Value": 0.0, "Cost_Paid": 0.0, "Parse_Status": "ok",
                        "Scenario": "crash", "Seed": 11, "Crash_Discount": 0.55, "Ordering": "setup_first",
                        "Persona": "INTJ", "Start_Cash_Share": 0.5, "Cost_bp": 5.0, "Model": "m", "Arm": "static"})
    csvp = tmp_path / "run.csv"
    run.to_csv(csvp, index=False)
    with open(str(csvp).replace(".csv", ".meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, default=str)
    run["__file"] = str(csvp)

    def phash(series):
        return hashlib.sha256(np.ascontiguousarray(np.asarray(series, float)).tobytes()).hexdigest()[:24]

    run_hash = phash(run["Price"])
    from_meta_env = env_from_meta(meta)
    assert phash(from_meta_env.data[from_meta_env.data["asset"] == 0]["price"]) == run_hash, \
        "the environment rebuilt from meta.json is not the run's own path"
    # the seven-column path cannot express b_pred and so builds a different path
    seven = SyntheticMarketEnv("crash", 60, 11, crash_discount=0.55, ordering="setup_first")
    assert phash(seven.data[seven.data["asset"] == 0]["price"]) != run_hash

    _BASE_CACHE.clear()
    a = cell_baselines(run, from_meta=True)
    b = cell_baselines(run, from_meta=False)
    assert set(a) == set(b)
    assert a["mandate_conditional_oracle"]["mcr_0.05"] != b["mandate_conditional_oracle"]["mcr_0.05"], \
        "the two baseline constructions agree, so this cell does not exercise the defect"
    _BASE_CACHE.clear()


def test_pilot_paths_do_not_reproduce_and_it_is_recorded():
    """E7.6's first finding, asserted against its own result file: the pilot ran on an engine whose SMM estimate
    Phase 2 rejected, so no pilot path regenerates and no pilot baseline may be rebuilt on one."""
    r = _gen("e7_6/repro.json")
    assert r["n_runs"] == 52
    assert r["n_path_reproduces"] == 0
    assert r["n_regen_ok_as_recorded"] == 0
    assert r["recorded_engines"] == ["fw_single"]
    assert any("fw_single" in e and "REJECTED" in e for e in r["regen_error_as_recorded"])
    # the provenance record itself is intact -- it is the generator that moved
    assert r["n_gen_config_hash_matches"] == r["n_runs"]


def test_scoring_params_absent_keeps_v2_thetas(tmp_path, monkeypatch):
    """With the parameter file absent, every consumer keeps its v2 constant -- the switch has v2 behind it."""
    import importlib
    from evaluation import scoring_params as sp
    monkeypatch.setattr(sp, "PRESENT", False)
    monkeypatch.setattr(sp, "_DOC", None)
    import evaluation.metrics_v2 as M
    importlib.reload  # no reload needed: thetas_in_force reads sp.PRESENT at call time
    assert tuple(M.thetas_in_force()) == tuple(M.THETAS)
    with pytest.raises(sp.ScoringParamsError):
        sp.block("theta_cost")


def test_phase7_report_tables_match_files():
    """Rule 14: every report table is generated from its file and read back (`--check` exits 1 when stale)."""
    report = os.path.join(ROOT, "docs", "env_v2", "v2_1", "PHASE_7_REPORT.md")
    if not os.path.exists(report):
        pytest.skip("PHASE_7_REPORT.md not written yet")
    from tools.phase7.e7_report_tables import main as rt
    assert rt(["--check"]) == 0, "a PHASE_7_REPORT.md table differs from the file it is generated from"


def test_scoring_params_file_is_the_one_the_tools_measured():
    """P4-19: every Phase-7 result records the parameter file it was computed under."""
    if not SP.PRESENT:
        pytest.skip("scoring.json absent")
    assert SP.SHA256 == SP.file_sha256()
    assert len(SP.SHA256) == 64
