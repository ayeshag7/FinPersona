"""
Checklist items 18 (start design applied) and 19 (action-space reachability).

v1 section: documents the v1 facts the plan diagnoses (defects 12-13) as
positive assertions on the frozen tracker, so the baseline is on record and
any "accidental fix" of the frozen code is caught.

v2 section: the contract the new tracker must satisfy (target cash share;
any allocation reachable in one step; SELL feasible at t = 1; start design
applied per cell). Skipped until simulation/portfolio_v2.py exists.
"""
import pytest

from envs.v1.portfolio_tracker_v1 import PortfolioTracker as V1Tracker


def test_v1_everyone_starts_100pct_cash():
    t = V1Tracker(initial_cash=10000.0)
    assert t.cash == 10000.0 and t.holdings_qty == 0.0
    assert t.get_state() == {"cash": 10000.0, "holdings_value": 0.0}


def test_v1_sell_is_noop_on_day_1():
    t = V1Tracker(initial_cash=10000.0)
    v = t.execute_trade("SELL", 1.0, 100.0, "Day-1")
    assert v == 0.0 and t.cash == 10000.0 and t.holdings_qty == 0.0


def test_v1_buy_sell_are_asymmetric_and_ratchet():
    t = V1Tracker(initial_cash=10000.0)
    t.execute_trade("BUY", 0.5, 100.0, "Day-1")        # spends 50% of cash
    assert t.cash == 5000.0 and t.holdings_qty == 50.0
    t.execute_trade("SELL", 0.5, 100.0, "Day-2")       # sells 50% of HOLDINGS (not of value)
    assert t.cash == 7500.0 and t.holdings_qty == 25.0
    # repeated fractional BUYs approach full investment geometrically, never overshoot
    t2 = V1Tracker(10000.0)
    for d in range(50):
        t2.execute_trade("BUY", 0.5, 100.0, f"Day-{d}")
    assert 0 < t2.cash < 1e-6 * 10000.0 and t2.cash > 0


def test_v1_target_allocation_not_reachable_in_one_step_from_cash():
    # from 100% cash, the lowest cash share reachable in one step is 0 (BUY 1.0),
    # but no single action moves cash share UP from a given position by an
    # arbitrary amount: SELL q sells q of holdings, so cash share after the
    # trade depends on the current holdings, not on a target.
    t = V1Tracker(10000.0)
    t.execute_trade("BUY", 1.0, 100.0, "Day-1")
    assert t.cash == 0.0
    t.execute_trade("SELL", 0.25, 100.0, "Day-2")
    assert abs(t.cash / t.total_value - 0.25) < 1e-9  # only because price is unchanged


# ---------------- v2 contract ----------------
v2 = pytest.importorskip("simulation.portfolio_v2", reason="v2 tracker not built yet (E1)")


@pytest.mark.parametrize("start", [0.0, 0.1, 0.5, 0.8, 1.0])
def test_v2_start_design_applied(start):
    t = v2.PortfolioV2(initial_value=10000.0, start_cash_share=start, price=100.0)
    assert abs(t.cash_share(100.0) - start) < 1e-9


@pytest.mark.parametrize("target", [0.0, 0.13, 0.5, 0.87, 1.0])
def test_v2_any_target_reachable_in_one_step(target):
    t = v2.PortfolioV2(initial_value=10000.0, start_cash_share=0.5, price=100.0)
    t.retarget(target, price=100.0, day=1, cost_bp=0.0)
    assert abs(t.cash_share(100.0) - target) < 1e-9


def test_v2_sell_feasible_at_t1_and_labels():
    t = v2.PortfolioV2(initial_value=10000.0, start_cash_share=0.5, price=100.0)
    rec = t.retarget(0.9, price=100.0, day=1, cost_bp=5.0)   # raise cash = SELL
    assert rec["derived_action"] == "SELL" and rec["traded_value"] > 0 and rec["cost_paid"] > 0
    rec = t.retarget(0.905, price=100.0, day=2, cost_bp=5.0)  # inside the 1-point dead band
    assert rec["derived_action"] == "HOLD"
