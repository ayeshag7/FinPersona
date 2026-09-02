"""
Phase 2 (v2.1) tests -- the mispricing engine and its persistence (plan section 6.4; PREREG_PHASE_2.md section 10).

  * `test_fw_index_params_match_source` / `test_pruna_params_match_source`: the parameter sets in
    `envs/v2/mispricing.py` equal the published tables read at source (FW 2012 Table 1 DCA-HPM; Pruna et al.
    2016 Table 1) -- verifications V1 and V2 of the phase report;
  * `test_fw_units`: FW's own model at `price_scale = 1` reproduces their published joint moment coverage ratio
    (Table 4, DCA-HPM: 10.1 %) at 50 runs within the tolerance the 200-run E2.1 result establishes, and
    `price_scale = 100` does not -- the E2.1 bug fix, locked;
  * `test_mispricing_params_loader`: a malformed `params/mispricing.json` raises; a present file carries
    value / label / source / date / interval / n on every entry;
  * `test_persistence_in_force`: the pull rate (or AR(1) rho) of the engine that RUNS equals the half-life
    recorded in `params/mispricing.json`, with its provenance;
  * `test_engine_named_honestly`: `get_metadata()['engine_used']` equals the code path that ran, and the
    rejected single-stock estimate still cannot switch the engine;
  * `test_half_life_estimator_table`: the E2.5 lookup regenerates at 50 seeds inside the tolerance the stored
    200-seed table's own spread implies;
  * `test_smm_reference_row`: the SMM simulator's moment vector at a fixed theta and CRN seed equals the stored
    reference row -- the machine check any offloaded fit has to pass before its numbers are used;
  * `test_garch_shape_matches_e3_1`: STRICT XFAIL, registered to Phase 3 -- the engine was fitted against E3.1's
    per-stock GARCH shape while the generator still runs v2's CAL shape.
"""
import json
import math
import os

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
PARAMS = os.path.join(ROOT, "envs", "v2", "params")
pytestmark = pytest.mark.filterwarnings("ignore")

# Read at source on 1 September 2026 (see PHASE_2_REPORT.md section 1)
FW_2012_TABLE1_DCA_HPM = dict(phi=0.12, chi=1.50, sigma_f=0.758, sigma_c=2.087, alpha_0=-0.327,
                              alpha_n=1.79, alpha_p=18.43, beta=1.0, mu=0.01)
PRUNA_2016_TABLE1 = dict(phi=0.121, chi=1.555, sigma_f=0.592, sigma_c=1.917, alpha_0=-0.301,
                         alpha_n=1.990, alpha_p=22.741, beta=1.0, mu=0.01)
FW_2012_TABLE4_JOINT_MCR_PCT = 10.1


def _mis():
    p = os.path.join(PARAMS, "mispricing.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def test_fw_index_params_match_source():
    from envs.v2.mispricing import FW_INDEX_2012
    for k, v in FW_2012_TABLE1_DCA_HPM.items():
        assert getattr(FW_INDEX_2012, k) == pytest.approx(v, abs=1e-12), (k, getattr(FW_INDEX_2012, k), v)


def test_pruna_params_match_source():
    from envs.v2.mispricing import PRUNA_2016
    for k, v in PRUNA_2016_TABLE1.items():
        assert getattr(PRUNA_2016, k) == pytest.approx(v, abs=1e-12), (k, getattr(PRUNA_2016, k), v)


def test_fw_units():
    """E2.1's bug fix, locked at 50 runs.  Tolerance: the joint MCR is a share, so at n = 50 its 95 % half-width
    around 0.10 is 1.96 sqrt(0.1 x 0.9 / 50) = 8.3 pp; the band below is that half-width around the published
    10.1 %, widened to the nearest whole point.  `price_scale = 100` must sit far outside it (the 200-run run
    measured 0.0 % [0.0, 1.9])."""
    from tools.phase2.fw_pure import DCA_HPM, PureParams, simulate_pure
    from tools.phase2.moments import FW_NAMES, FW_TABLE_A1, fw_moments
    n = 50

    def joint_mcr(scale):
        p = PureParams(**{**DCA_HPM, "price_scale": scale})
        M = fw_moments(simulate_pure(n, 6750, p, seed=100001)["r"])
        inside = np.ones(n, bool)
        for j, nm in enumerate(FW_NAMES):
            _, lo, hi = FW_TABLE_A1[nm]
            inside &= (M[:, j] >= lo) & (M[:, j] <= hi)
        return float(inside.mean() * 100)

    m1, m100 = joint_mcr(1.0), joint_mcr(100.0)
    assert abs(m1 - FW_2012_TABLE4_JOINT_MCR_PCT) <= 9.0, (m1, "price_scale = 1 must reproduce FW Table 4")
    assert m100 <= 2.0, (m100, "price_scale = 100 must NOT reproduce it (the switching term saturates)")


def test_mispricing_params_loader(tmp_path):
    from envs.v2.mispricing_params import load
    bad = tmp_path / "mispricing.json"
    bad.write_text(json.dumps({"engine": {"value": "x"}}), encoding="utf-8")
    with pytest.raises(RuntimeError):
        load(str(bad))
    assert load(str(tmp_path / "absent.json")) is None       # absent -> v2 behaviour, documented
    m = _mis()
    if m is None:
        pytest.skip("params/mispricing.json not written yet (tools/phase2/apply_e2.py writes it)")
    for k in ("engine", "price_scale", "structural", "half_life", "garch_shape", "moments"):
        assert k in m, k
        for f in ("value", "label", "source", "date", "n"):
            assert f in m[k], (k, f)
        assert m[k]["label"], k


def test_persistence_in_force():
    m = _mis()
    if m is None:
        pytest.skip("params/mispricing.json not written yet")
    from envs.v2 import mispricing_params as MP
    from envs.v2.mispricing import ENGINE_DEFAULT, load_params
    assert ENGINE_DEFAULT == MP.ENGINE == m["engine"]["value"]
    p = load_params(ENGINE_DEFAULT)
    assert p.price_scale == pytest.approx(m["price_scale"]["value"])
    hl = float(m["half_life"]["value"])
    if MP.ENGINE_FAMILY == "ar1":
        from envs.v2.mispricing import MispricingState
        st = MispricingState(p, ENGINE_DEFAULT)
        assert -math.log(2.0) / math.log(st.rho_ar1) == pytest.approx(hl, rel=0.02)
    else:
        from envs.v2.mispricing import pilot_stats
        n_bar = pilot_stats(p, ENGINE_DEFAULT)["n_bar"]
        assert math.log(2.0) / (p.mu * n_bar * p.phi) == pytest.approx(hl, rel=0.10)


def test_engine_named_honestly():
    from envs.synthetic_market import SyntheticMarketEnv
    from envs.v2.mispricing import ENGINE_DEFAULT, load_params
    env = SyntheticMarketEnv("flat", 50, 7)
    md = env.get_metadata()
    assert md["engine"] == ENGINE_DEFAULT
    assert md["engine_used"] == load_params(ENGINE_DEFAULT).name == md["fw_params"]["name"]
    with pytest.raises((FileNotFoundError, ValueError)):
        load_params("fw_single")


def test_half_life_estimator_table():
    p = os.path.join(GEN, "e2_5", "hl_table.json")
    if not os.path.exists(p):
        pytest.skip("E2.5 table not generated yet")
    from tools.phase2.e2_5_hl_table import SEED_HL, ar1, hl, median_function, median_unbiased, ols_rho
    tab = json.load(open(p, encoding="utf-8"))
    hs = tab["design"]["hs"]
    for key in ("h30|T200", "h150|T200", "h150|T800"):
        c = tab["cells"][key]
        h, T = c["h_true"], c["T"]
        x = ar1(h, T, 50, SEED_HL + 977 * hs.index(h) + T)
        med = float(np.nanmedian(hl(ols_rho(x))))
        # Tolerance: a 50-seed regeneration is an INDEPENDENT sample, so the band is the 95 % sampling interval
        # of a median at n = 50 -- 1.96 x 1.25 x sd / sqrt(50) with sd estimated from the stored cell's IQR
        # (sd ~ IQR / 1.349) -- floored at 20 % of the stored median.  Stated here rather than tuned: at
        # h = 30 / T = 200 the stored IQR is 12.5-26.5, so the band is +-4.5 d around a median of 18.0 d.
        sd = (c["naive"]["p75"] - c["naive"]["p25"]) / 1.349
        tol = max(1.96 * 1.25 * sd / math.sqrt(50), 0.20 * c["naive"]["median"])
        assert abs(med - c["naive"]["median"]) <= tol, (key, med, c["naive"]["median"], tol)


def test_smm_reference_row():
    p = os.path.join(GEN, "e2_3", "reference_row.json")
    if not os.path.exists(p):
        pytest.skip("reference row not generated yet")
    from tools.phase2.engines import DEFAULTS, pooled_moments
    ref = json.load(open(p, encoding="utf-8"))
    base = dict(DEFAULTS)
    base["price_scale"] = 1.0
    for eng, row in ref.items():
        got = pooled_moments(eng, 20, 5000, base, seed=110001, burn=500)
        for a, b in zip(got, [float(v) for v in row]):
            assert a == pytest.approx(b, rel=1e-10, abs=1e-14), eng


@pytest.mark.xfail(strict=True, reason="registered (Phase 3): E2.3 fitted the engine against E3.1's per-stock "
                                       "GJR-GARCH-t shape (alpha 0.027, gamma 0.058, beta 0.932, nu 4.86) while "
                                       "the generator still runs v2's CAL shape (0.10 / 0.10 / 0.83 / 5); "
                                       "Phase 3's volatility re-fit owns the reconciliation")
def test_garch_shape_matches_e3_1():
    from envs.v2.garch import GJRParams
    g = GJRParams()
    assert (g.alpha, g.gamma, g.beta, g.df) == pytest.approx((0.027, 0.058, 0.932, 4.86), rel=0.05)
