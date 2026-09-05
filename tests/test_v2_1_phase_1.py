"""
Phase 1 (v2.1) tests -- value and price structure (plan section 5.4; PREREG_PHASE_1.md section 10).

  * `test_sigma_V_in_force`, `test_value_params_loader_is_loud`: the generator's sigma_V / mu_V / start mode / jump placement
    / burn-in equal envs/v2/params/value.json, which carries the provenance, and a missing or incomplete file raises;
  * `test_start_price_carries_no_information`: the stored 500-seed E1.1 result passes for the mechanism in force AND a live
    100-seed attacker run (CI lower limit of R2(level) - R2(level-free) <= 0 in every scenario; half-width ~0.05 at this
    size -- a guard, not the evidence, which is generated/v2_1/e1_1/start_price.json);
  * `test_render_scale_invariance`: under mechanism C every ratio field and every return is invariant to k_render;
  * `test_jump_placement_variants`: every placement produces the declared components with E[jump] = 0 where declared;
  * `test_burn_in_stationary`: the KS upper limit of the day-1 state vs the stored E1.5 reference < 0.10 for every engine
    (500 seeds; slow: ~4 min);
  * `test_kalman_bound_tabulated`: the bound regenerated from value.json equals the stored table;
  * `test_level_free_price_only_keys`: the audit's control set contains no level;
  * `test_flat_x_equivalence`: the 95 % interval of E[x] in flat lies inside +/- 0.02 at 100 seeds (E1.4 rule).
"""
import json
import os

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
pytestmark = pytest.mark.filterwarnings("ignore")


def _value():
    return json.load(open(os.path.join(ROOT, "envs", "v2", "params", "value.json"), encoding="utf-8"))


def test_sigma_V_in_force():
    from envs.v2.generator import GenConfig
    from envs.v2 import value_params as VP
    v = _value()
    cfg = GenConfig()
    assert cfg.sigma_V == v["sigma_V"]["value"] == VP.SIGMA_V
    assert cfg.mu_V == v["mu_V"]["value"] == VP.MU_V
    assert cfg.start_price_mode == v["start_price_mode"]["value"] == "both"           # D13 revised to C (30 Aug 2026)
    assert cfg.jump_placement == v["jump"]["value"]["placement"]
    assert cfg.burn_in == VP.burn_in_for(cfg.engine)
    for k in ("sigma_V", "mu_V", "df_V", "start_price_mode", "start_price_range", "jump", "burn_in"):
        assert "label" in v[k] and "source" in v[k] and "date" in v[k], k
        # every pending value resolved at hand-over: a label may be FIT / CAL / DESIGN / LIT or an explicit "D3 PENDING" (a decision
        # referred to the team with the value in force stated), never the stage-1 "PENDING E1.x" placeholder
        assert not str(v[k]["label"]).startswith("PENDING"), (k, v[k]["label"])
    # sigma_V's label states its status: FIT (adopted and applied), "D3 PENDING" (no estimator usable) or
    # "ADOPTED-NOT-YET-APPLIED" (E1.2 adopted a value whose application triggers the execution-order rule; the value in
    # force and the fitted value are both recorded -- DECISION_LOG P1-15)
    assert v["sigma_V"]["label"].startswith(("FIT", "D3 PENDING", "ADOPTED-NOT-YET-APPLIED")), v["sigma_V"]["label"]
    if v["sigma_V"]["label"].startswith("ADOPTED-NOT-YET-APPLIED"):
        f = v["sigma_V"]["fitted"]
        assert f["value"] > 0 and len(f["interval"]) == 2 and f["value"] != v["sigma_V"]["value"], f
    assert v["mu_V"]["label"].startswith("FIT") and v["mu_V"]["interval"] is not None and v["mu_V"]["n"]
    assert v["start_price_range"]["label"].startswith("FIT")


def test_value_params_loader_is_loud(tmp_path):
    from envs.v2.value_params import load_value_params
    with pytest.raises(RuntimeError):
        load_value_params(str(tmp_path / "missing.json"))
    bad = tmp_path / "value.json"
    v = _value(); v.pop("burn_in")
    bad.write_text(json.dumps(v), encoding="utf-8")
    with pytest.raises(RuntimeError):
        load_value_params(str(bad))


def test_level_free_price_only_keys():
    from evaluation import leakage_audit as la
    assert la.CONTROLS["level_free"] == la.LEVEL_FREE_KEYS
    for k in la.LEVEL_FREE_KEYS:
        assert k not in ("price", "SMA20", "SMA50", "SMA60", "SMA200", "MACD", "MACD_signal", "analyst_fair_value"), k
    # run_audit's default control is the level-free set
    import inspect
    assert inspect.signature(la.run_audit).parameters["control"].default == "level_free"
    assert inspect.signature(la.l2_surrogate).parameters["control"].default == "level_free"


def test_render_scale_invariance():
    from envs.synthetic_market import SyntheticMarketEnv
    a = SyntheticMarketEnv("crash", 60, 11, config={"start_price_mode": "normalise"})
    b = SyntheticMarketEnv("crash", 60, 11, config={"start_price_mode": "both"})
    k = b.result.k_render
    assert k != 1.0
    np.testing.assert_allclose(a.data["price"].to_numpy(), b.data["price"].to_numpy())          # hidden path identical
    oa, ob = a.get_observation(), b.get_observation()
    for f in ("reported_PE", "dividend_yield", "RSI14", "trend_strength", "trend_regime", "volume", "volume_ratio",
              "news_sentiment", "implied_volatility", "days_since_eps_announcement"):
        assert oa[f] == ob[f], f
    for f in ("price", "SMA20", "SMA50", "analyst_fair_value"):
        assert abs(ob[f] / oa[f] - k) < 2e-3, (f, oa[f], ob[f], k)     # rendered at 2 dp
    # returns are invariant: a second step
    a.step(); b.step()
    ra = a.get_observation()["price"] / oa["price"]; rb = b.get_observation()["price"] / ob["price"]
    assert abs(ra - rb) < 1e-3


def test_jump_placement_variants():
    """v2.1 Phase 3: a MACHINERY probe at fixed probe values (jump_rate 0.01, jump_sd 0.03 -- v2's CAL,
    overridden explicitly), decoupled from the block in force.  E3.2's fitted jumps are ~17x rarer
    (lambda 0.000583), so the negative-mean placement's stationary offset (lambda mu_J / (1 - rho) ~ -0.0008 at
    h* = 22.4 d) is far below the detectable margin at any affordable seed count -- asserting it at the fitted
    values would be vacuous.  What this test protects is the placement CODE: negmean applies a negative mean,
    the announcement placements put jumps on announcement days, and the mean-zero placements carry no bias."""
    from envs.v2.generator import GenConfig, generate
    seeds = range(200, 240)
    probe = {"jump_rate": 0.01, "jump_sd": 0.03}
    res = {}
    for jp in ("x_negmean", "x_zero", "V_announce", "both"):
        rs = [generate(GenConfig(scenario="flat", seed=s, jump_placement=jp, reject=False, **probe)) for s in seeds]
        res[jp] = {"mean_x": float(np.mean([r.x[0, r.day >= 1].mean() for r in rs])),
                   "n_ann": float(np.mean([r.event_meta["n_ann_jumps"] for r in rs]))}
    assert res["x_negmean"]["n_ann"] == 0 and res["x_zero"]["n_ann"] == 0
    assert res["V_announce"]["n_ann"] > 0 and res["both"]["n_ann"] > 0
    # at the probe values the negmean offset is -0.0004/(1 - rho) ~ -0.013 at h* = 22.4 d: detectable
    others = [res[jp]["mean_x"] for jp in ("x_zero", "V_announce", "both")]
    assert res["x_negmean"]["mean_x"] < min(others) - 0.003, (res["x_negmean"], others)
    for jp in ("x_zero", "V_announce", "both"):
        assert abs(res[jp]["mean_x"]) < 0.04, (jp, res[jp])


def test_flat_x_equivalence():
    """E1.4 E[x] equivalence under the corrected criterion (PREREG_PHASE_1_ADDENDUM.md, new-b): the stored 1,000-seed
    interval of the mean of x in flat markets lies inside +/- 0.02, AND a 100-seed live guard reproduces the stored
    mean within 2 SE. The pre-registered 100/200-seed TOST form is undecidable (half-width 0.029 / 0.020 against a
    0.020 margin) and is not asserted.

    v2.1 Phase 2: this was a strict xfail registered to Phase 2 -- the FW calm engine carried E[x] = +0.0126
    [+0.0038, +0.0214] with mean-zero jumps and +0.0113 with jumps off, failing the margin by its upper limit.
    E2.4 adopted the AR(1)+GJR-GARCH-t engine, which has no such bias: E[x] = -0.00013 [-0.00087, +0.00064] with
    jumps on and -0.00029 [-0.00102, +0.00046] with jumps off, 1,000 flat paths each (e2_4/flat_x.json). The
    marker is removed and the registry entry cleared. Two changes to the assertion itself, both stated: the
    stored reference is now Phase 2's measurement on the engine in force (Phase 1's file describes an engine
    that no longer runs), and the benchmark days are selected by `day >= 1` rather than the hard-coded index 260,
    which was the burn-in of the time and is 750 for the engine adopted here."""
    from envs.v2.generator import GenConfig, generate
    from envs.v2 import value_params as VP
    # v2.1 Phase 3: the stored reference is the measurement on the block in force (e3_4/flat_x_p3.json, seeds
    # FX3 240000+, same 1,000-path design); Phase 2's file describes the old volatility block and stays as the
    # earlier reference. The assertion is unchanged.
    p3 = os.path.join(GEN, "e3_4", "flat_x_p3.json")
    p2 = os.path.join(GEN, "e2_4", "flat_x.json")
    if os.path.exists(p3):
        stored = json.load(open(p3, encoding="utf-8"))["jumps_on"]
    elif os.path.exists(p2):
        stored = json.load(open(p2, encoding="utf-8"))["jumps_on"]
    else:
        name = {"x_negmean": "current_x_negmean", "x_zero": "B_x_zero", "V_announce": "A_V_announce",
                "both": "C_both"}[VP.JUMP["placement"]]
        stored = json.load(open(os.path.join(GEN, "e1_4", f"confirm_{name}.json"), encoding="utf-8"))["full"]
    means = []
    for s in range(16000, 16100):
        r = generate(GenConfig(scenario="flat", seed=s))
        means.append(r.x[0, r.day >= 1].mean())
    means = np.array(means)
    se = means.std(ddof=1) / np.sqrt(len(means))
    assert abs(means.mean() - stored["E_x"]) <= 2 * se, (means.mean(), stored["E_x"], se)      # live guard
    lo, hi = stored["ci95"]
    assert -0.02 <= lo and hi <= 0.02, (stored["E_x"], lo, hi)


def test_kalman_bound_tabulated():
    from tools.phase1.kalman_bound import kalman_bound, verify
    ok, rows = verify()
    assert ok, rows
    stored = json.load(open(os.path.join(GEN, "e1_3", "sweep.json"), encoding="utf-8"))
    v = _value()
    for g in stored["grid"][:8]:
        kb = kalman_bound(g["sigma_V"], g["s_x"], 150.0)
        for k in ("window_avg", "day_T", "steady_state"):
            assert abs(kb[k] - g["kalman"][k]) < 1e-9
    # the bound at the parameters in force is what the audit prints
    kb = kalman_bound(v["sigma_V"]["value"], 0.1752, 150.0)
    assert 0 < kb["window_avg"] < kb["day_T"] < kb["steady_state"] < 1


def test_start_price_carries_no_information():
    """E1.1 rule for the mechanism in force (C since D13 was revised on 30 Aug 2026; B failed it -- PHASE_1_REPORT.md 4.5)."""
    stored = json.load(open(os.path.join(GEN, "e1_1", "start_price.json"), encoding="utf-8"))
    mech = {"normalise": "B", "randomise": "A", "both": "C", "fixed": "fixed"}[_value()["start_price_mode"]["value"]]
    assert stored["mechanisms"][mech]["attacker"]["attacker_pass"], stored["mechanisms"][mech]["attacker"]
    assert not stored["mechanisms"]["fixed"]["attacker"]["attacker_pass"]        # the v2 answer key is detected
    # live guard at 100 seeds x 4 scenarios
    import pandas as pd
    from envs.synthetic_market import SyntheticMarketEnv
    from evaluation.leakage_audit import panel_from_env
    from tools.phase1.e1_1_start_price import attacker_per_scenario, SCENARIOS4
    frames = []
    for sc in SCENARIOS4:
        for s in range(52000, 52100):
            env = SyntheticMarketEnv(sc, 200, s, crash_discount=0.70)
            frames.append(panel_from_env(env, sc, s))
    att = attacker_per_scenario(pd.concat(frames, ignore_index=True), n_boot=200)
    for sc in SCENARIOS4:
        c = att[f"{sc}|all"]
        assert c["delta_ci95"][0] <= 0, (sc, c["delta_level_minus_levelfree"], c["delta_ci95"])


def test_burn_in_stationary():
    """E1.5 (REG-17) under the corrected criterion (PREREG_PHASE_1_ADDENDUM.md section 4): the stored 2,000-path run
    (e1_5/burn_in.json) shows every variable's KS upper limit < 0.10 for the option in force per engine, AND a live guard
    at 500 seeds per engine reproduces day-1 states whose KS point distance to the stored 2,000-path reference is < 0.10
    (the 500-vs-2,000 upper limit under equality is ~0.10 itself, so the point is the decidable statistic here; the
    260-day defect of the slow engines shows as a point of 0.17)."""
    from tools.phase1.e1_5_burn_in import _day1_job, ks_upper, ENGINES, VARS, D0, SEED0, OUT
    from concurrent.futures import ProcessPoolExecutor
    from envs.v2 import value_params as VP
    from envs.v2.mispricing import ENGINE_DEFAULT
    stored = json.load(open(os.path.join(OUT, "burn_in.json"), encoding="utf-8"))
    assert stored["design"]["n_paths"] >= 2000
    # v2.1 Phase 3: the stored 2,000-path E1.5 run is asserted as the record of the decision it made (under the
    # v2 volatility block).  The LIVE guard now runs for the ENGINE IN FORCE against a reference regenerated
    # under the Phase-3 block (tools/phase3/e3_burn_in_guard.py); the legacy sensitivity engines' Phase-1
    # references and stored burn-in states were sampled under v2's GARCH shape and are STALE under the block in
    # force -- a Phase-6/9 sensitivity that runs one of those engines must regenerate them first
    # (PHASE_3_REPORT.md section 7), and their live guards here would compare across blocks, which is not the
    # stationarity question E1.5 asked.
    for eng in ENGINES:
        mode = VP.burn_in_mode_for(eng); days = VP.burn_in_for(eng) if mode == "long" else int(VP.BURN_IN["stored_days"])
        name = f"B_stored_{days}" if mode == "stored" else ("current_260" if days == 260 else f"A_long_{days}")
        opt = stored["engines"][eng]["options"][name]
        assert all(opt[v]["ks_upper95"] < D0 for v in VARS), (eng, name, {v: opt[v]["ks_upper95"] for v in VARS})
    ref = np.load(os.path.join(OUT, f"reference_states_{ENGINE_DEFAULT}.npz"))
    with ProcessPoolExecutor(max_workers=3) as ex:
        d1 = np.array(list(ex.map(_day1_job, [(s, ENGINE_DEFAULT, None, None) for s in range(SEED0, SEED0 + 500)], chunksize=10)))
    for j, v in enumerate(VARS):
        pt, _ = ks_upper(d1[:, j], ref[v], n_boot=1)
        assert pt < D0, (ENGINE_DEFAULT, v, pt)
