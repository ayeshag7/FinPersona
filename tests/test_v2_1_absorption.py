"""The absorption ratio reproduces a planted ratio, and both of its registered guards bite.

`PREREG_PHASE_9_STAGE2_E2.md` 3 requires that A's unit test reproduce a planted ratio on synthetic pairs
before it touches a run.  Every cell below is constructed so the true A is known by arithmetic.
"""
import numpy as np
import pandas as pd
import pytest

from tools.phase9.e9_absorption import FLOOR, absorption, guard_counts

SEEDS = list(range(10001, 10061))          # the 60 E2 registers


def _frame(cells):
    """cells: {(persona, scenario): (d_mandate, d_placebo, jitter)} -> a per_run frame.

    `static` sits at 0.5 every seed; `memory` at 0.5 + d_mandate; `placebo_directive` at 0.5 + d_placebo.
    `jitter` is the sd of mean-zero noise added to the memory arm alone, which is what widens the
    denominator's bootstrap interval without moving its estimate.
    """
    rng = np.random.default_rng(0)
    rows = []
    for (persona, scenario), (d_m, d_p, jit) in cells.items():
        for s in SEEDS:
            noise = rng.normal(0.0, jit) if jit else 0.0
            for arm, v in (("static", 0.5),
                           ("memory", 0.5 + d_m + noise),
                           ("placebo_directive", 0.5 + d_p)):
                rows.append({"Model": "m", "Persona": persona, "Scenario": scenario, "Seed": s,
                             "Arm": arm, "band_mas": v})
    return pd.DataFrame(rows)


def test_absorption_reproduces_a_planted_ratio():
    """A = (d_placebo . sign(d_mandate)) / |d_mandate|, on cells where both guards pass."""
    cells = {
        ("ISFJ", "flat"): (0.20, 0.05, 0.0),      # A = +0.25
        ("INTJ", "flat"): (0.40, 0.30, 0.0),      # A = +0.75
        ("ENTJ", "flat"): (0.10, 0.10, 0.0),      # A = +1.00, full absorption
        ("ISFJ", "crash"): (0.20, -0.05, 0.0),    # A = -0.25, placebo moves the WRONG way
    }
    t = absorption(_frame(cells), arm="placebo_directive", n_boot=499)
    got = {(r["Persona"], r["Scenario_Cell"]): round(float(r["A"]), 10) for _, r in t.iterrows()}
    assert got[("ISFJ", "flat")] == pytest.approx(0.25)
    assert got[("INTJ", "flat")] == pytest.approx(0.75)
    assert got[("ENTJ", "flat")] == pytest.approx(1.00)
    assert got[("ISFJ", "crash")] == pytest.approx(-0.25)
    assert bool(t["admitted"].all())


def test_a_negative_mandate_effect_does_not_flip_the_ratio():
    """The alignment is the point: a cell where memory IMPROVES band-MAS and the placebo improves it too
    reproduces the mandate's effect, so A is POSITIVE -- an unsigned ratio would agree here but disagree in
    sign with the positive-mandate cells it is averaged with.  14 of stage 1's 34 usable denominators are
    negative, which is why this case is tested rather than assumed away."""
    t = absorption(_frame({("ENTJ", "flat"): (-0.20, -0.05, 0.0),      # both negative -> A = +0.25
                           ("ENTJ", "crash"): (-0.20, +0.05, 0.0)}),   # placebo opposes -> A = -0.25
                   arm="placebo_directive", n_boot=499)
    got = {r["Scenario_Cell"]: float(r["A"]) for _, r in t.iterrows()}
    assert got["flat"] == pytest.approx(0.25)
    assert got["crash"] == pytest.approx(-0.25)
    assert (t["sign"] == -1).all()


def test_the_floor_excludes_a_tiny_denominator():
    """A denominator of 1.5e-4 -- two of stage 1's real cells -- would give |A| in the tens.  The floor,
    a fifth of the registered Delta, excludes it, and the cell is counted rather than dropped."""
    tiny = 1.5e-4
    t = absorption(_frame({("ENTJ", "flat"): (tiny, 0.0115, 0.0),
                           ("ISFJ", "flat"): (0.20, 0.05, 0.0)}),
                   arm="placebo_directive", n_boot=499)
    row = t[t["Persona"] == "ENTJ"].iloc[0]
    assert abs(float(row["d_arm"]) / abs(float(row["d_mandate"]))) > 70       # what an unguarded A would be
    assert not bool(row["guard_above_floor"])
    assert np.isnan(float(row["A"]))
    assert bool(t[t["Persona"] == "ISFJ"].iloc[0]["admitted"])
    assert guard_counts(t) == {"cells": 2, "admitted": 1, "excluded_ci_includes_0": 0,
                               "excluded_below_floor": 1, "excluded_by_both": 0,
                               "admitted_negative_mandate": 0}


def test_an_uncertain_denominator_is_excluded_even_when_it_is_large():
    """Size is not certainty: a mandate effect of 0.20 whose seed-level differences are swamped by noise has
    a bootstrap interval covering 0, and dividing by it would be dividing by something not shown to differ
    from zero.  The CI guard is independent of the floor."""
    t = absorption(_frame({("ISFJ", "flat"): (0.20, 0.05, 3.0)}), arm="placebo_directive", n_boot=999)
    row = t.iloc[0]
    assert bool(row["guard_above_floor"])              # 0.20 clears the floor
    assert not bool(row["guard_ci_excludes_0"])        # but the interval covers 0
    assert np.isnan(float(row["A"]))
    assert guard_counts(t)["excluded_ci_includes_0"] == 1


def test_the_floor_is_a_fifth_of_the_registered_delta():
    assert FLOOR == pytest.approx(0.05 / 5)
