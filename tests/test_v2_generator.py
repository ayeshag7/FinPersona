"""
v2 generator contract tests (E1): reproducibility, stream separation, price
decomposition, schedule ranges, phase taxonomy, rejection logging, observation
hygiene (no hidden fields, no NaN), multi-asset shape, metadata/provenance.
"""
import concurrent.futures as cf

import math
import numpy as np
import pytest

from envs.synthetic_market import SyntheticMarketEnv, CANONICAL_FIELDS, TABLE2_DEFINITIONS
from envs.v2.generator import GenConfig, generate
from envs.v2.schedule import draw_schedule
from envs.v2.rng import Streams, COMPONENTS

HIDDEN = {"fundamental_value", "x", "phase", "macro_phase", "garch_sigma", "n_f", "hidden_multiple",
          "analyst_error_u", "fvar21", "fw_weight", "trailing_eps", "last_quarter_eps", "dps_quarterly"}


def _path(scenario, seed, **kw):
    r = generate(GenConfig(scenario=scenario, seed=seed, **kw))
    m = r.day >= 1
    return r, r.P[0, m], r.V[0, m], r.x[0, m], r.phase[m]


def test_reproducible_and_thread_safe():
    def build(_):
        e = SyntheticMarketEnv("crash", 120, 7)
        return e.data["price"].to_numpy()
    with cf.ThreadPoolExecutor(6) as ex:
        paths = list(ex.map(build, range(6)))
    for p in paths[1:]:
        np.testing.assert_allclose(p, paths[0])


def test_streams_are_separate_and_append_only():
    s = Streams(3, 0)
    a = s.get("fundamental").random(5); b = s.get("garch").random(5)
    assert not np.allclose(a, b)
    assert Streams(3, 0).get("fundamental").random(5).tolist() == a.tolist()
    assert Streams(3, 1).get("fundamental").random(5).tolist() != a.tolist()  # new attempt -> new draws
    assert COMPONENTS[0] == "fundamental" and "sentiment" in COMPONENTS


def test_price_decomposition_and_start():
    """v2.1 Phase 1 (D13, revised to mechanism C on 30 Aug 2026): the day-1 HIDDEN price is the normalisation constant
    and V_1 = P_1 e^-x_1, exactly as under B -- C adds a per-seed render scale applied at render time only, so the hidden
    path is unchanged. v2's V_1 = 100 (the answer key) is the 'fixed' mechanism, kept behind the switch."""
    r, P, V, x, ph = _path("flat", 1)
    np.testing.assert_allclose(P, V * np.exp(x))
    assert r.cfg.start_price_mode == "both"
    rb, Pb, _, _, _ = _path("flat", 1, start_price_mode="normalise")
    np.testing.assert_allclose(P, Pb)                 # C's hidden path is B's; only the rendered fields differ
    assert r.k_render != 1.0 and rb.k_render == 1.0
    assert abs(P[0] - 100.0) < 1e-9 and abs(V[0] - 100.0 * np.exp(-x[0])) < 1e-9
    rf, Pf, Vf, xf, _ = _path("flat", 1, start_price_mode="fixed")
    assert abs(Vf[0] - 100.0) < 1e-9
    from envs.v2 import value_params as VP
    burn = r.cfg.burn_in if r.cfg.burn_in is not None else VP.BURN_IN["days"].get(r.cfg.engine, VP.BURN_IN["days"]["default"])
    assert len(P) == 200 and r.day[0] == 1 - burn      # v2.1 Phase 1: the burn-in comes from value.json (E1.5)


def test_schedule_ranges():
    """v2's stipulated ranges, pinned to `schedule_mode="v2"`.

    v2.1 Phase 4 replaced these with ranges FIT from the panel, so the draw is only inside the bounds below
    when the v2 switch is pinned -- unpinned, `det_len` reaches 3 against v2's floor of 15 and this test
    failed for that reason (found when the suite was finally run; see PHASE_4_REPORT section 9.11). Pinning is
    the point rather than a workaround: "v2 behaviour is bit-identical behind every switch" is the guarantee
    the phase makes, and this test is now what enforces it for the schedule."""
    rng = np.random.default_rng(0)
    for _ in range(200):
        s = draw_schedule("crash", 200, rng, "setup_first", delta=0.7, schedule_mode="v2")
        assert 50 <= s.setup_len <= 110 and 15 <= s.det_len <= 40 and 15 <= s.panic_len <= 70
        assert 0.10 <= s.D_V <= 0.30 and 0.7 <= s.delta_end <= 1.0
        assert s.setup_len + s.det_len + s.panic_len + 10 <= 200
        b = draw_schedule("bull_trap", 200, rng, "event_first", schedule_mode="v2")
        assert 5 <= b.setup_len <= 20 and 0.02 <= b.kappa <= 0.04 and 10 <= b.post_top_len <= 30
        assert all(-5 <= j <= 5 for j in b.jitter.values())
    f = draw_schedule("flat", 200, rng, schedule_mode="v2")
    assert f.event_start == 201


def test_schedule_ranges_v21_stay_inside_the_fitted_grids():
    """The v2.1 draw is an inverse-CDF sample from an empirical grid, so every draw must land inside that
    grid's own min/max -- read from `events.json` rather than hardcoded, so a re-fit cannot silently
    invalidate the test. Also asserts the two modes genuinely differ, or the pin above proves nothing."""
    ep = pytest.importorskip("envs.v2.events_params")
    if not ep.PRESENT:
        pytest.skip("events.json absent: there is no v2.1 schedule to check")
    lo_hi = {k: (min(v["grid"]), max(v["grid"]))
             for k, v in ep.RANGES.items() if isinstance(v, dict) and "grid" in v}
    rng = np.random.default_rng(0)
    seen_det = set()
    for _ in range(200):
        s = draw_schedule("crash", 200, rng, "setup_first", delta=0.7, schedule_mode="v21")
        seen_det.add(s.det_len)
        for name, val in (("det_len", s.det_len), ("panic_len", s.panic_len)):
            if name in lo_hi and not s.truncated.get(name):
                lo, hi = lo_hi[name]
                # these are drawn as ints, so a fractional grid bound is reached by rounding
                assert math.floor(lo) <= val <= math.ceil(hi),                     f"{name}={val} outside the fitted grid [{lo}, {hi}] even allowing integer rounding"
        assert s.setup_len + s.det_len + s.panic_len + 10 <= 200
    # the modes must differ, or pinning "v2" above would be vacuous
    assert min(seen_det) < 15, "v21 det_len no longer goes below v2's floor; the switch may have stopped taking effect"


@pytest.mark.parametrize("scenario,expected", [
    ("flat", {"calm"}), ("crash", {"calm", "deterioration", "panic", "stabilisation"}),
    ("sustained_bull", {"sustained-bull"})])
def test_phase_taxonomy(scenario, expected):
    r, P, V, x, ph = _path(scenario, 2)
    assert set(ph) == expected


def test_bubble_phases_and_strata():
    topped = 0
    for s in range(8):
        r, P, V, x, ph = _path("bull_trap", s)
        labels = set(ph)
        assert {"calm", "mania", "blow-off"} <= labels
        if r.event_meta["topped"]:
            topped += 1
            assert "post-top" in labels and r.event_meta["top_day"] >= r.schedule.event_start
        else:
            assert "post-top" not in labels
        assert x.max() >= 0.30  # rejection criterion
    assert 0 < topped < 8  # both strata exist


def test_crash_criterion_and_delta_matters():
    mdds = {}
    for d in (0.55, 0.85):
        vals = []
        for s in range(6):
            r, P, V, x, ph = _path("crash", s, delta=d, schedule_mode="v2")
            assert x[ph == "panic"].min() <= -0.10
            vals.append((P / np.maximum.accumulate(P) - 1).min())
        mdds[d] = np.mean(vals)
    assert mdds[0.55] < mdds[0.85] - 0.10


def test_delta_moves_the_drawdown_under_the_centred_depth_draw():
    """P4-40: `crash_discount` is a live factor again, and the switch is inert at the reference delta.

    E4.2 drew the crash depth from the panel UNCONDITIONALLY, which discarded `delta` and made checklist
    item 10 exactly inert -- the 0.55-vs-0.85 drawdown spread was 0.0000 to full float precision. E4.19 showed
    that depth-only failure also dominates the coverage shortfall, so the two were one problem.
    `depth_mode="centred"` shifts the fitted depth distribution so its centre tracks delta, keeping its shape.

    Three properties, all asserted because each could regress independently:
      1. under "unconditional" delta is still inert  (the old behaviour is still reachable)
      2. under "centred" delta moves the drawdown
      3. at the REFERENCE delta the two modes agree bit-for-bit (the switch is inert where it must be)"""
    def mdd(delta, depth_mode):
        vals = []
        for s in range(6):
            r, P, V, x, ph = _path("crash", s, delta=delta, schedule_mode="v21", depth_mode=depth_mode)
            vals.append((P / np.maximum.accumulate(P) - 1).min())
        return float(np.mean(vals))

    assert mdd(0.55, "unconditional") == mdd(0.85, "unconditional"),         "the unconditional draw is no longer inert in delta; P4-40's premise has changed"
    lo, hi = mdd(0.55, "centred"), mdd(0.85, "centred")
    assert lo < hi - 0.02, f"centred depth did not restore the delta effect: {lo} vs {hi}"
    ref = 0.70   # events.json's reference delta -- the shift is defined relative to it
    assert mdd(ref, "centred") == mdd(ref, "unconditional"),         "the centred switch is not inert at the reference delta; it must reproduce the unconditional draw"


def test_rejection_logging():
    r = generate(GenConfig(scenario="bull_trap", seed=5, reject=True))
    assert r.attempts == len(r.rejections) + 1
    r2 = generate(GenConfig(scenario="bull_trap", seed=5, reject=False))
    assert r2.attempts == 1


def test_observation_hygiene():
    env = SyntheticMarketEnv("crash", 200, 11)
    for _ in range(200):
        o = env.get_observation()
        assert set(o.keys()) == set(CANONICAL_FIELDS), set(o.keys()) ^ set(CANONICAL_FIELDS)
        assert not (set(o.keys()) & HIDDEN)
        for k, v in o.items():
            if k != "date":
                assert v == v and np.isfinite(v), (k, v)  # no NaN/inf
        env.step()
    assert env.get_observation() is None
    for c in env.data.columns:
        assert c in TABLE2_DEFINITIONS, f"column {c} lacks a Table 2 definition"


def test_multi_asset_shape_and_options():
    env = SyntheticMarketEnv("flat", 60, 3, n_assets=3, config={"asset_vol_scale": [1.0, 1.0, 0.5]})
    o = env.get_observation()
    assert len(o["assets"]) == 3 and env.data["asset"].nunique() == 3
    env2 = SyntheticMarketEnv("flat", 60, 3, disclose_horizon=True, field_order="randomised")
    o2 = env2.get_observation()
    assert o2["date"] == "Day-1 of 60" and o2["days_remaining"] == 59
    assert list(o2.keys())[:-1] != CANONICAL_FIELDS  # permuted (all but the appended days_remaining)


def test_metadata_and_provenance():
    from simulation.provenance import env_provenance
    a = SyntheticMarketEnv("flat", 50, 1); b = SyntheticMarketEnv("flat", 50, 1); c = SyntheticMarketEnv("flat", 50, 2)
    assert env_provenance(a) == env_provenance(b) and env_provenance(a)["Gen_Config_Hash"] != env_provenance(c)["Gen_Config_Hash"]
    assert env_provenance(a)["Env_Version"] == "v2"
    md = a.get_metadata()
    # v2.1 Phase 2: the engine that runs is whatever params/mispricing.json names (E2.4); the assertion is
    # that the metadata reports the code path that ran, not that it is any particular engine.
    from envs.v2.mispricing import ENGINE_DEFAULT
    assert md["fw_params"]["name"] == ENGINE_DEFAULT == md["engine_used"] and md["schedule"]["T"] == 50 and "attempts" in md


def test_engine_sensitivity_sets_load():
    for eng in ("fw_index", "pruna", "ar1"):
        r = generate(GenConfig(scenario="flat", seed=1, T=60, engine=eng))
        assert np.isfinite(r.x).all()
