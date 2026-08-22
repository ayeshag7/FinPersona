"""
v2 generator contract tests (E1): reproducibility, stream separation, price
decomposition, schedule ranges, phase taxonomy, rejection logging, observation
hygiene (no hidden fields, no NaN), multi-asset shape, metadata/provenance.
"""
import concurrent.futures as cf

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
    r, P, V, x, ph = _path("flat", 1)
    np.testing.assert_allclose(P, V * np.exp(x))
    assert abs(V[0] - 100.0) < 1e-9
    assert len(P) == 200 and r.day[0] == 1 - r.cfg.burn_in


def test_schedule_ranges():
    rng = np.random.default_rng(0)
    for _ in range(200):
        s = draw_schedule("crash", 200, rng, "setup_first", delta=0.7)
        assert 50 <= s.setup_len <= 110 and 15 <= s.det_len <= 40 and 15 <= s.panic_len <= 70
        assert 0.10 <= s.D_V <= 0.30 and 0.7 <= s.delta_end <= 1.0
        assert s.setup_len + s.det_len + s.panic_len + 10 <= 200
        b = draw_schedule("bull_trap", 200, rng, "event_first")
        assert 5 <= b.setup_len <= 20 and 0.02 <= b.kappa <= 0.04 and 10 <= b.post_top_len <= 30
        assert all(-5 <= j <= 5 for j in b.jitter.values())
    f = draw_schedule("flat", 200, rng)
    assert f.event_start == 201


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
            r, P, V, x, ph = _path("crash", s, delta=d)
            assert x[ph == "panic"].min() <= -0.10
            vals.append((P / np.maximum.accumulate(P) - 1).min())
        mdds[d] = np.mean(vals)
    assert mdds[0.55] < mdds[0.85] - 0.10


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
    assert md["fw_params"]["name"].startswith("fw_single") and md["schedule"]["T"] == 50 and "attempts" in md


def test_engine_sensitivity_sets_load():
    for eng in ("fw_index", "pruna", "ar1"):
        r = generate(GenConfig(scenario="flat", seed=1, T=60, engine=eng))
        assert np.isfinite(r.x).all()
