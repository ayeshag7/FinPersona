"""
v2.1 Phase 7 -- E7.4: the dividend schedule read off the frozen generator (D10 = pay; DECISION_LOG P7-2).

`envs/` is not this phase's to change and no path may move, so the ex-dates are RECOVERED from the environment's
own frame rather than added to it:

    ex-date := a day on which `days_since_eps_announcement == 0`
    amount  := `dps_quarterly` on that day, per share

`days_since_eps_announcement` is `day - last_announcement_day` (`envs/v2/observables.py::earnings_block`), so it is
0 exactly on the quarterly EPS/DPS announcement days and on no other day; `dps_quarterly` on such a day is the DPS
just announced.  A 200-day path carries three of them (~63 trading days apart), and a non-payer seed (the FIT payer
share) carries a DPS of 0 throughout, so it pays nothing.

This identification is the ANNOUNCEMENT day, not a separate ex-date: the generator has no ex-date concept, and
inventing one would be a generator change.  The consequence -- four quarterly payments a year at `dps_quarterly`
each, which is exactly the `4 x DPS / P` that the rendered `dividend_yield` field states -- is what makes the shown
yield real money.  What it does NOT do is drop the price on the ex-date: the generator's price is a price-return
series and is frozen, so a dividend-paying holder is a total-return holder on a price-return path.  Every number
computed with `dividends=True` carries that sentence.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

EX_DATE_COLUMN = "days_since_eps_announcement"
DPS_COLUMN = "dps_quarterly"


def dividend_schedule(env, n_assets: int = 1, n_days: Optional[int] = None) -> np.ndarray:
    """(T, n_assets) dividend per share: `dps_quarterly` on announcement days, 0 elsewhere.

    Raises if the environment's frame does not carry the two columns -- an absent schedule is reported as a
    finding, never silently replaced by zeros (PREREG_PHASE_7.md 5).
    """
    d = env.data
    for c in (EX_DATE_COLUMN, DPS_COLUMN):
        if c not in d.columns:
            raise KeyError(f"the environment's frame has no {c!r}: the ex-dates are not recoverable without an "
                           f"envs/ change, which this phase may not make")
    T = int(n_days if n_days is not None else env.n_days)
    out = np.zeros((T, int(n_assets)), dtype=float)
    for a in range(int(n_assets)):
        g = d[d["asset"] == a].reset_index(drop=True) if "asset" in d.columns else d.reset_index(drop=True)
        since = pd.to_numeric(g[EX_DATE_COLUMN], errors="coerce").to_numpy(dtype=float)[:T]
        dps = pd.to_numeric(g[DPS_COLUMN], errors="coerce").to_numpy(dtype=float)[:T]
        ex = np.isfinite(since) & (since == 0)
        amt = np.where(ex & np.isfinite(dps), dps, 0.0)
        out[: len(amt), a] = amt
    return out


def schedule_summary(sched: np.ndarray) -> dict:
    """What a schedule contains, for the report: how many ex-dates, on which days, how much per share."""
    total = sched.sum(axis=0)
    days = [int(i + 1) for i in np.where(sched.sum(axis=1) > 0)[0]]
    return {"n_ex_dates": len(days), "ex_days": days, "dps_total_per_share": [float(v) for v in total],
            "dps_per_ex_date": [[float(v) for v in sched[i - 1]] for i in days]}
