"""
Portfolio accounting v2 (plan 2.1 blocks 8-9; decisions 4, 5, 9; checklist 18-19).

* Initial allocation is a FACTOR: the portfolio starts at `start_cash_share` of
  `initial_value` in cash and the rest in shares bought at the day-1 price
  (primary design: the persona's band centre; secondary: common 0.5; bridge: 1.0).
* Action = target cash share c* in [0, 1] (N = 1) or target weights (N > 1; the
  cash share is 1 - sum of risky weights).  The trade is the delta between the
  target and the current cash share; any allocation is reachable in one step
  and SELL is feasible at t = 1.
* Derived labels for RG scoring: BUY if the equity share rises by more than
  DEAD_BAND (1 point), SELL if it falls by more than DEAD_BAND, HOLD otherwise.
  A target within the dead band of the current share is NOT traded at all
  (HOLD = no trade, no cost; the allocation then drifts with price).
* Cost = cost_bp x |traded value| per trade, charged to cash.  Same-day close
  execution at the price on which the observation was rendered (the stated
  default); `execution="next_open"` defers the retarget to the next day's
  price (sensitivity).  Fractional shares; long-only; no leverage.
* The v1 interface (BUY/SELL fraction-of-side) is kept behind
  `execute_v1_action()` for the bridge cell (A1 x A2 factorial).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

DEAD_BAND = 0.01


class PortfolioV2:
    def __init__(self, initial_value: float = 10000.0, start_cash_share: float = 0.5, price: float = 100.0,
                 n_assets: int = 1, start_weights: Optional[Sequence[float]] = None):
        self.n_assets = int(n_assets)
        self.initial_value = float(initial_value)
        self.start_cash_share = float(start_cash_share)
        if not 0.0 <= self.start_cash_share <= 1.0:
            raise ValueError("start_cash_share must be in [0, 1]")
        prices = self._prices(price)
        risky_value = self.initial_value * (1.0 - self.start_cash_share)
        if start_weights is None:
            start_weights = [1.0 / self.n_assets] * self.n_assets
        self.holdings_qty: List[float] = [risky_value * w / p for w, p in zip(start_weights, prices)]
        self.cash = self.initial_value - risky_value
        self.trades: List[Dict] = []
        self.turnover_value = 0.0
        self.cost_paid_total = 0.0
        self.pending: Optional[Dict] = None   # next-open execution

    # ------------------------------------------------------------------ helpers
    def _prices(self, price) -> List[float]:
        if isinstance(price, (int, float)):
            return [float(price)] * self.n_assets
        return [float(p) for p in price]

    def total_value(self, price) -> float:
        return self.cash + sum(q * p for q, p in zip(self.holdings_qty, self._prices(price)))

    def holdings_value(self, price) -> float:
        return sum(q * p for q, p in zip(self.holdings_qty, self._prices(price)))

    def cash_share(self, price) -> float:
        tv = self.total_value(price)
        return self.cash / tv if tv > 0 else 1.0

    def get_state(self, price) -> Dict[str, float]:
        return {"cash": self.cash, "holdings_value": self.holdings_value(price),
                "cash_share": self.cash_share(price), "total_value": self.total_value(price)}

    # ------------------------------------------------------------------ actions
    def retarget(self, target_cash_share: float, price, day, cost_bp: float = 5.0,
                 target_weights: Optional[Sequence[float]] = None, execution: str = "same_day") -> Dict:
        """Move to the target allocation. Returns a trade record with the
        derived action label, traded value and cost."""
        target_cash_share = min(max(float(target_cash_share), 0.0), 1.0)
        if execution == "next_open":
            # record the intent; execute at the next call of settle_pending(price)
            self.pending = {"target_cash_share": target_cash_share, "target_weights": target_weights,
                            "cost_bp": cost_bp, "day": day}
            return {"day": day, "derived_action": "PENDING", "traded_value": 0.0, "cost_paid": 0.0,
                    "target_cash_share": target_cash_share, "cash_share_after": self.cash_share(price)}
        return self._execute(target_cash_share, price, day, cost_bp, target_weights)

    def settle_pending(self, price, day) -> Optional[Dict]:
        if self.pending is None:
            return None
        p = self.pending; self.pending = None
        return self._execute(p["target_cash_share"], price, day, p["cost_bp"], p["target_weights"])

    def _execute(self, target_cash_share, price, day, cost_bp, target_weights) -> Dict:
        prices = self._prices(price)
        before = self.cash_share(price)
        tv = self.total_value(price)
        if abs(target_cash_share - before) <= DEAD_BAND and target_weights is None:
            # HOLD = no trade at all (the allocation drifts with price); no cost
            return {"day": day, "derived_action": "HOLD", "traded_value": 0.0, "cost_paid": 0.0,
                    "target_cash_share": target_cash_share, "cash_share_before": before, "cash_share_after": before}
        if target_weights is None:
            cur_risky = [q * p for q, p in zip(self.holdings_qty, prices)]
            s = sum(cur_risky)
            target_weights = [v / s for v in cur_risky] if s > 0 else [1.0 / self.n_assets] * self.n_assets
        target_risky_total = tv * (1.0 - target_cash_share)
        traded = 0.0
        new_qty = []
        for q, p, w in zip(self.holdings_qty, prices, target_weights):
            target_val = target_risky_total * w
            cur_val = q * p
            traded += abs(target_val - cur_val)
            new_qty.append(target_val / p if p > 0 else 0.0)
        cost = traded * cost_bp / 10000.0
        # cash absorbs the net flow and the cost; a tiny overshoot from cost is clipped at 0 cash
        new_cash = tv - target_risky_total - cost
        if new_cash < 0:  # cannot borrow to pay cost: scale the risky sleeve down
            scale = (tv - cost) / target_risky_total if target_risky_total > 0 else 1.0
            new_qty = [q * scale for q in new_qty]
            new_cash = 0.0
        self.holdings_qty = new_qty
        self.cash = new_cash
        self.turnover_value += traded
        self.cost_paid_total += cost
        after = self.cash_share(price)
        equity_change = (1 - after) - (1 - before)
        label = "BUY" if equity_change > DEAD_BAND else ("SELL" if equity_change < -DEAD_BAND else "HOLD")
        rec = {"day": day, "derived_action": label, "traded_value": traded, "cost_paid": cost,
               "target_cash_share": target_cash_share, "cash_share_before": before, "cash_share_after": after}
        if traded > 0:
            self.trades.append(rec)
        return rec

    def execute_v1_action(self, action: str, quantity: float, price: float, day, cost_bp: float = 0.0) -> Dict:
        """v1 semantics for the bridge cell: BUY spends cash x q; SELL sells holdings x q (N = 1)."""
        before = self.cash_share(price)
        traded = 0.0
        if action == "BUY" and quantity > 0:
            budget = self.cash * float(quantity)
            cost = budget * cost_bp / 10000.0
            spend = max(budget - cost, 0.0)
            self.holdings_qty[0] += spend / price
            self.cash -= budget
            traded = spend
        elif action == "SELL" and quantity > 0:
            shares = self.holdings_qty[0] * float(quantity)
            proceeds = shares * price
            cost = proceeds * cost_bp / 10000.0
            self.holdings_qty[0] -= shares
            self.cash += proceeds - cost
            traded = proceeds
        else:
            cost = 0.0
        self.turnover_value += traded
        self.cost_paid_total += cost if traded > 0 else 0.0
        rec = {"day": day, "derived_action": action if traded > 0 else "HOLD", "traded_value": traded,
               "cost_paid": cost if traded > 0 else 0.0, "cash_share_before": before,
               "cash_share_after": self.cash_share(price)}
        if traded > 0:
            self.trades.append(rec)
        return rec
