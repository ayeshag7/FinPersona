"""
Phase 0 statistical regression tests (v2.1 plan, Section 4, item 0.4; PREREG_PHASE_0.md §6 fixes every
seed block, statistic, tolerance and its derivation).

Strict xfails document defects reserved for a later phase (registry: tests/known_defects.py); the phase that
fixes a defect flips the test to a hard test and removes the registry entry. Hard tests:
`test_analyst_error_sd` (the Phase-0 fix) and `test_half_life_consistency`.
"""
import math

import numpy as np
import pytest

from envs.v2.generator import GenConfig, generate, check_validity

pytestmark = pytest.mark.filterwarnings("ignore")


def _paths(scenario, seeds, **kw):
    return [generate(GenConfig(scenario=scenario, seed=s, **kw)) for s in seeds]


def _bench_x(r):
    return r.x[0, r.day >= 1]


# ---------------------------------------------------------------------------------------------------
def test_flat_x_unbiased():
    """SFLAT100 (seeds 16000-16099): |mean of path means| <= 1.96 SE (cluster by seed). Size 5 %; power vs the
    -0.087 bias ~ 1 (SE ~ 0.013). Hard since v2.1 Phase 1 (E1.4: jump placement x_zero; the v2 -4 %/day jump mean no
    longer enters x). The residual engine mean (~ +0.012 at 1,000 seeds) is below this test's resolution; it is the
    subject of test_v2_1_phase_1.py::test_flat_x_equivalence (registered, Phase 2)."""
    means = np.array([_bench_x(r).mean() for r in _paths("flat", range(16000, 16100))])
    se = means.std(ddof=1) / math.sqrt(len(means))
    assert abs(means.mean()) <= 1.96 * se, f"mean x {means.mean():+.4f}, SE {se:.4f}, z {means.mean() / se:+.2f}"


def test_analyst_error_sd():
    """SANALYST (seeds 15000-15099): pooled sd of the analyst log error over the 460-day timeline within +/-10 %
    of the documented stationary sd (0.15). Tolerance derivation (PREREG §4.1): 9,200 AR(1) updates at rho 0.95 ->
    effective n ~ 236 -> relative SE of the sd ~ 4.6 %, so 10 % ~ 2.2 SE; the sqrt(5) defect (+124 %) is detected
    with power ~ 1."""
    from envs.v2 import observables as obs
    from envs.v2.rng import Streams
    day = np.arange(460) - 260 + 1
    V = np.ones(460)
    u = np.concatenate([obs.analyst_block(day, V, Streams(s, 0).get("analyst", 0))["analyst_error_u"] for s in range(15000, 15100)])
    sd = float(u.std())
    assert abs(sd / obs.ANALYST_SD - 1.0) <= 0.10, f"pooled sd(u) = {sd:.4f} vs documented {obs.ANALYST_SD} (implemented sqrt(5) defect gives 0.335)"


@pytest.mark.xfail(strict=True, reason="known defect 46 (registry): the phase multiplier enters the IV forecast "
                                       "deterministically (one-day step z ~ 7); fixed in Phase 3 (E3.5)")
def test_iv_continuity():
    """SIV30 (crash delta 0.70, seeds 17000-17029): z = mean change in log IV at deterioration->panic and
    panic->stabilisation divided by the calm day-to-day sd of log IV must be <= 3 (DESIGN-provisional; Phase 3
    replaces it by the 95th percentile of the realised-variance change-point statistic)."""
    from envs.synthetic_market import SyntheticMarketEnv
    steps = {("deterioration", "panic"): [], ("panic", "stabilisation"): []}
    calm = []
    for s in range(17000, 17030):
        d = SyntheticMarketEnv("crash", 200, s, crash_discount=0.70).data
        ph = d["phase"].to_numpy(dtype=object)
        dl = np.diff(np.log(d["implied_volatility"].to_numpy(float)))
        calm.append(dl[(ph[:-1] == "calm") & (ph[1:] == "calm")])
        for (a, b) in steps:
            idx = np.where((ph[:-1] == a) & (ph[1:] == b))[0]
            if len(idx):
                steps[(a, b)].append(dl[idx[0]])
    sd = float(np.concatenate(calm).std())
    z = {k: float(np.mean(v)) / sd for k, v in steps.items()}
    assert all(abs(v) <= 3.0 for v in z.values()), f"z at transitions {z} (calm sd {sd:.3f})"


# `test_fundamentalist_share` was REMOVED here in v2.1 Phase 2, as PREREG_PHASE_2.md section 6 fixed in advance
# for the case the AR(1) engine is adopted.  Its content was: on 30 flat paths, the share of days with n_f > 0.99
# must be below 0.50, i.e. the Franke-Westerhoff switching must not be inert (weakness items 2 and 11); it was a
# strict xfail because at `price_scale = 100` the misalignment term saturated and n_f exceeded 0.99 on ~98 % of
# days.  E2.4 adopted `ar1_fit` (AR(1)+GJR-GARCH-t): the engine that runs has no fundamentalist/chartist
# population at all, so the statistic has no referent and a test of it would be theatre.  What replaces it:
#   * E2.1 (`tests/test_v2_1_phase_2.py::test_fw_units`) locks the units bug fix that made the switching inert,
#     by reproducing Franke & Westerhoff's own published moment coverage ratio at `price_scale = 1`;
#   * `e2_4/engine_diagnostics.json` records the realised chartist share of every FITTED FW engine (0.043 for
#     `fw_v2` on the full sample, 0.0004 on the training period, 0.235 for `fw_plus`), which is the number the
#     removed test was trying to protect;
#   * the registry entry for items 2 and 11 is cleared (DECISION_LOG P2-7).


def test_half_life_consistency():
    """SPILOT (seeds 9001-9005): five 200,000-step calm pilots of the live engine (Gaussian innovations sd 0.017,
    engine weight normalisation). The mean ACF(1)-implied half-life must agree with the pull-rate half-life
    ln2/(mu n_bar phi) within 8 d (PREREG §6: Bartlett SE of ACF(1) at rho 0.9954 over 200,000 steps is 2.2e-4,
    i.e. 7.0 d per pilot and 3.1 d for the mean of five; 8 d ~ 2.6 SE, size ~ 1 %; the withdrawn 188-d figure
    is rejected with power ~ 1). Hard test from Phase 0 (plan 0.4, LOG §1)."""
    from envs.v2 import mispricing_params as MP
    from envs.v2.mispricing import ENGINE_DEFAULT, MispricingState, load_params, long_pilot_stats, pilot_stats
    p = load_params(ENGINE_DEFAULT)
    if MP.PRESENT and MP.ENGINE_FAMILY == "ar1":
        # v2.1 Phase 2: the engine that runs is an AR(1), whose analytic half-life is -ln2/ln(rho) exactly; the
        # 200,000-step pilot is run on the FW sensitivity `fw_fallback_hl150` instead, where the pull-rate vs
        # ACF(1) agreement is the thing worth locking (the check Phase 0 wrote this test for).
        st = MispricingState(p, ENGINE_DEFAULT)
        analytic = -math.log(2) / math.log(st.rho_ar1)
        assert abs(analytic - float(MP.HALF_LIFE)) <= 0.01, (analytic, MP.HALF_LIFE)
        p = load_params("fw_fallback_hl150")
        engine = "fw_fallback_hl150"
    else:
        engine = ENGINE_DEFAULT
    ps = pilot_stats(p, engine)
    pull_hl = math.log(2) / (p.mu * ps["n_bar"] * p.phi)
    hls = [long_pilot_stats(p, engine, n_steps=200_000, sd_e=0.017, seed=s)["half_life"] for s in (9001, 9002, 9003, 9004, 9005)]
    mean_hl = float(np.mean(hls))
    print(f"[{engine}] pull-rate half-life {pull_hl:.1f} d; pilots {[round(h, 1) for h in hls]} (mean {mean_hl:.1f} d)")
    assert abs(mean_hl - pull_hl) <= 8.0, f"ACF(1) half-life {mean_hl:.1f} d vs pull rate {pull_hl:.1f} d"


@pytest.mark.xfail(strict=True, reason="known defects 18, 42 (registry): rejection sampling keeps the quiet "
                                       "sub-population of sustained-bull draws; the control is redefined in Phase 4 (E4.5, D14)")
def test_sustained_bull_selection():
    """SSB50 (seeds 18000-18049, first attempts): accepted and rejected first-attempt paths must have the same daily
    sd of log returns within 10 % (DESIGN-provisional; Phase 4 replaces it by the KS-distance upper-limit bound)."""
    acc, rej = [], []
    for r in _paths("sustained_bull", range(18000, 18050), reject=False):
        sd = float(np.diff(np.log(r.P[0, r.day >= 1])).std())
        (acc if check_validity(r) is None else rej).append(sd)
    assert len(acc) >= 5 and len(rej) >= 5, (len(acc), len(rej))
    sa, sr = float(np.mean(acc)), float(np.mean(rej))
    assert abs(sa - sr) / sr <= 0.10, f"daily sd accepted {sa:.4f} vs rejected {sr:.4f} ({(sr - sa) / sr:.1%} quieter)"
