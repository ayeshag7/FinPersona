"""
v2.1 Phase 3 regression tests (PREREG_PHASE_3.md section 11; PLAN section 7.4).

  * test_garch_params_in_force: envs/v2/params/volatility.json exists, carries provenance, and the running
    GJRParams equal it (the loud-loader contract; its absence cannot persist past the hand-over).
  * test_iv_no_lookahead: the E3.5 construction is past-only -- altering the return path strictly after day t0
    leaves IV on days <= t0 bit-identical (20 seeds, t0 in {40, 100, 160}), and the environment's rendered IV
    is exactly that construction on its own returns with the day-indexed 'iv' stream.
  * test_jump_process: the jump stream the generator draws realises the FIT rate and size at 500 seeds.
  * test_volatility_loader_malformed: a malformed volatility.json raises (the hazard.json convention).

`test_iv_continuity` (hard, tolerance T_z from volatility.json) lives in tests/test_v2_1_stats.py;
`test_garch_shape_matches_e3_1` (now passing) in tests/test_v2_1_phase_2.py.
"""
import json
import math
import os

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARAMS = os.path.join(ROOT, "envs", "v2", "params")
pytestmark = pytest.mark.filterwarnings("ignore")

NLA_SEEDS = range(250000, 250020)
JP_SEEDS = range(251000, 251500)


def _vol():
    p = os.path.join(PARAMS, "volatility.json")
    assert os.path.exists(p), "volatility.json must exist once Phase 3 is applied (PREREG section 11)"
    return json.load(open(p, encoding="utf-8"))


def test_garch_params_in_force():
    from envs.v2.garch import GJRParams
    from envs.v2 import volatility_params as VOLP
    v = _vol()
    assert VOLP.PRESENT
    g = GJRParams()
    sh = v["garch_shape"]["value"]
    assert (g.alpha, g.gamma, g.beta, g.df) == (sh["alpha"], sh["gamma"], sh["beta"], sh["df"])
    assert g.sbar == v["sbar"]["value"]
    mech = v["mechanism"]["value"]
    assert g.scale_mode == mech["scale_mode"]
    assert g.mult == mech["mult"]
    for key in ("garch_shape", "sbar", "jumps", "phase_multipliers", "mechanism", "iv"):
        e = v[key]
        assert e["label"] and e["source"] and e["date"], f"{key} lacks provenance"
    # the applied jump block flows into the generator's defaults through value.json
    from envs.v2.generator import GenConfig
    cfg = GenConfig()
    j = v["jumps"]["value"]
    assert cfg.jump_rate == j["jump_rate_x"] and cfg.jump_sd == j["jump_sd"]
    assert cfg.jump_placement == j["placement"] == "x_zero"


def test_volatility_loader_malformed(tmp_path):
    from envs.v2 import volatility_params as VOLP
    bad = tmp_path / "volatility.json"
    bad.write_text(json.dumps({"garch_shape": {"value": {}}}), encoding="utf-8")
    with pytest.raises(RuntimeError):
        VOLP.load(str(bad))


def test_iv_no_lookahead():
    """PREREG 7.2(1). Unit: iv_block_v21 is a past-only function of the return path. Wiring: the environment's
    rendered IV equals iv_block_v21 of its own full return path with its own 'iv' stream."""
    from envs.v2.observables import iv_block_v21
    from envs.v2.rng import Streams
    from envs.synthetic_market import SyntheticMarketEnv
    from envs.v2 import volatility_params as VOLP
    ivp = VOLP.IV
    assert ivp is not None
    rng0 = np.random.default_rng(9)
    for i, seed in enumerate(NLA_SEEDS):
        rng = np.random.default_rng(seed)
        n = 400
        ret = 0.02 * rng.standard_normal(n)
        for t0 in (40, 100, 160):
            ret2 = ret.copy()
            ret2[t0 + 1:] += 0.01
            iv1 = iv_block_v21(ret, np.random.default_rng(777), ivp)["implied_volatility"]
            iv2 = iv_block_v21(ret2, np.random.default_rng(777), ivp)["implied_volatility"]
            assert np.array_equal(iv1[:t0 + 1], iv2[:t0 + 1]), f"seed {seed}, t0 {t0}: IV before t0 moved"
            assert not np.array_equal(iv1[t0 + 1:], iv2[t0 + 1:])
    env = SyntheticMarketEnv("crash", 120, 250000, crash_discount=0.70)
    d = env._full[env._full["asset"] == 0]
    P = d["price"].to_numpy(float)
    ret = np.concatenate([[0.0], np.diff(np.log(P))])
    st = Streams(250000, env.attempts - 1)
    iv = iv_block_v21(ret, st.get("iv", 0), VOLP.IV)["implied_volatility"]
    np.testing.assert_allclose(d["implied_volatility"].to_numpy(float), iv, rtol=0, atol=0)


def test_jump_process():
    """PLAN 7.4: realised rate and mean |size| of the jump stream at 500 seeds inside the FIT intervals.
    The draws replicate envs/v2/generator.py's x_zero branch exactly (stream 'jump', same call sequence)."""
    from envs.v2.rng import Streams
    from envs.v2.generator import GenConfig
    v = _vol()
    j = v["jumps"]["value"]
    ci = v["jumps"]["interval"]
    cfg = GenConfig()
    L = cfg.burn_in + cfg.T
    n_days = 0
    n_jumps = 0
    ssq = 0.0
    for seed in JP_SEEDS:
        rj = Streams(seed, 0).get("jump", 0)
        mask = rj.random(L) < cfg.jump_rate
        sizes = rj.normal(0.0, cfg.jump_sd, L)[mask]
        n_days += L
        n_jumps += int(mask.sum())
        ssq += float((sizes ** 2).sum())
    rate = n_jumps / n_days
    sd = math.sqrt(ssq / max(n_jumps, 1))
    lo, hi = ci["lam"]
    assert lo <= rate <= hi, f"realised jump rate {rate:.5f} outside the FIT interval [{lo:.5f}, {hi:.5f}]"
    lo, hi = ci["sJ"]
    assert lo <= sd <= hi, f"realised jump size sd {sd:.4f} outside the FIT interval [{lo:.4f}, {hi:.4f}]"
    assert n_jumps > 50, "the 500-seed panel produced too few jumps to test"
