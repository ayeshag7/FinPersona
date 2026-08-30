"""
Bull-trap contract of the v2 generator (rewritten in v2.1 Phase 0, item 0.5).

The v1 form of this test asserted that the fundamental value stays flat (|V_1 - V_50| < 1) in a bull trap;
that was true of v1's plateau and is false by design in v2, where V grows at mu_V throughout (spec section 1).
The v1 assertion is kept as an E0 record in tests/test_provenance_and_freeze.py::test_v1_bull_trap_value_plateau_frozen.
The assertion that carries over: the price leaves the value (max x >= 0.30, the bull-trap rejection criterion).
"""
import numpy as np

from envs.synthetic_market import SyntheticMarketEnv


def test_bull_trap_generation():
    env = SyntheticMarketEnv(scenario="bull_trap", n_days=200, seed=42, start_price=100.0)
    df = env.data
    V = df["fundamental_value"].to_numpy(float); P = df["price"].to_numpy(float); x = df["x"].to_numpy(float)
    assert abs(P[0] - 100.0) < 1e-9                       # v2.1 Phase 1 (D13, provisional B): P_1 = start price, V_1 = P_1 e^-x_1 (v2 had V_1 = 100)
    assert np.isfinite(P).all() and (P > 0).all()
    assert x.max() >= 0.30                                 # the price leaves the value: rejection criterion
    assert np.allclose(P, V * np.exp(x))                   # log P = log V + x
    # V is a drifting random walk, not a plateau: it moves over the run and does so by far less than the price
    assert abs(V[-1] / V[0] - 1) > 1e-6 and (P.max() / P[0]) > (V.max() / V[0])
