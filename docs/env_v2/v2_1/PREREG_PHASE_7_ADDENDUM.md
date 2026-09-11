# Addendum to `PREREG_PHASE_7.md` — what came out the wrong way, and what was added after the fact

*Written 10 September 2026, as each item landed. The pre-registration's rule 1: "if a rule later proves wrong,
that goes in an addendum with the disconfirmation stated as loudly as any confirmation, and results are reported
under both." Every item below is either a stated expectation that was disconfirmed, a registered construction that
could not be implemented as written, or a reading added after a number was seen. Nothing here re-specifies a rule
after the fact; where a rule stands unchanged despite an awkward result, that is said.*

---

## 1. θ_info **is** reached on calm rows — expectation 1 disconfirmed

**Registered expectation (PREREG 11.1):** "θ_info is reached near θ = 0.05 on pooled rows and **not reached on
calm rows at any θ**." The pooled half is confirmed exactly. **The calm half is wrong.**

| population | sign accuracy at θ = 0.05 | first sustained crossing of 0.80 | accuracy there | coverage | n resolvable |
|---|---|---|---|---|---|
| pooled, all rows | 0.8005 [0.7908, 0.8102] | **θ = 0.05** | 0.8005 | 0.597 | 171,916 |
| pooled, calm rows | 0.6849 [0.6638, 0.7067] | **θ = 0.20** | 0.8797 [0.8040, 0.9434] | 0.009 | 1,089 |

Where the expectation came from and why it was wrong: Phase 6 measured the calm sign accuracy on the grid
{0.03, 0.05, 0.08} and read 0.685 at θ = 0.05 with no sign of a crossing; the execution prompt carried that
forward as "not reached on calm rows at any θ you will find". This phase's registered grid runs to 0.30, and the
crossing is there — at a θ where the calm population has fallen from 119,336 resolvable rows to 1,089 and 0.9 % of
calm steps are scored at all.

**The rule is not re-specified.** REG-11's failure mode ("θ_info not reached ⇒ θ_cost alone primary") is not
invoked, because θ_info *is* reached; D7 was put to the team with this table and the team recorded **co-primary as
registered** (DECISION_LOG P7-4). The calm value is reported as the calm population's value with its coverage and
n beside it every time, and is not primary.

### 1a. An unregistered sensitivity, added after the sweep was read

`theta_info_ci_lower` — the same locator applied to the **lower end of the bootstrap interval** instead of the
point estimate — was added to `tools/phase7/e7_1_theta_info.py` after the sweep was read, because the registered
locator is satisfied on the calm population at a θ where n has fallen by two orders of magnitude and a point
estimate on 1,089 rows is not the same statement as one on 171,916. It agrees with the registered value on the
calm population (0.20 either way) and moves the pooled value from 0.05 to 0.06. **It is a sensitivity, reported
beside; it replaces the registered value nowhere and enters no parameter file.**

---

## 2. E7.8's ceiling needed a policy family the registered sweep set did not contain

**Registered construction (PREREG 4.2):** "hold the directional probability fixed at p = 0.5 and vary **only** the
drift rate d over its sweep; the |r| between MCR and band-MAS across those cells is the collinearity floor."

The three registered scripted families carry a drift rate (`drift`) and a directional probability (`align`) in
**separate** families; neither carries both, so the construction as written was not computable on the sweep set as
first built. A fourth family, `ceil_d*` — the `align` target at p = 0.5 plus the `drift` displacement — was added
to `tools/phase7/e7_panel.py` and the panel rebuilt, **before any ceiling number was read**. This implements the
registered construction exactly rather than substituting the nearest available family (the `drift` cells, which
have no directional component at all and would have given a different, unregistered floor).

Cost of the fix: one panel rebuild (13 min). Consequence for the registered rule: none — the rule's text is
unchanged and the number it needs now exists.

### 2a. A second unregistered sensitivity on the correlation

The cell set the rule is applied to is 50 policies, 24 of them scripted, one family of which varies the drift rate
precisely to move band-MAS. `|r|` on the **16A policy set alone** (312 cells, the population the paper's claims are
about) was computed after the registered number was read and is reported beside it: **0.9812** against the full
set's 0.9758 under scoring A, and 0.9872 against 0.9827 under per-window. It is *higher*, so the collinearity is
not an artefact of the scripted sweeps. It does not enter the adoption rule.

---

## 3. The `align` policy's reference θ is a property of the policy, not of the scoring

PREREG 4.1 defines `align(p)` as "with probability p the policy moves to the oracle's band edge, else to the
opposite edge" without naming the θ at which that oracle target is computed. It is fixed at **θ = 0.05**, the
Phase-6 checkpoint value (`tools/phase7/e7_panel.ALIGN_REF_THETA`), so that the swept family is one family across
every θ it is *scored* at rather than a different family per scoring θ. Recorded here because the
pre-registration's text does not say it.

---

## 4. `e6_16a/runs.csv` does not carry per-day allocations

The execution prompt describes it as "every run's per-day allocations — re-score these under every scoring you
propose before you write a line of new simulation". It is 14,400 rows of one MCR per
(scenario, seed, persona, policy) at five θ values, with no allocation series: no re-scoring at a different θ, no
decomposition and no per-window rule can be computed from it.

The trajectories were therefore regenerated (`tools/phase7/e7_panel.py`), reusing the pickled oracles and the
fitted `rules.json` unchanged, and **proved identical to Phase 6's own MCR before anything was computed from
them**: worst |difference| **9.98 × 10⁻¹⁷** over 51,450 comparisons (`e7_panel/verify_vs_16a.json`).

A first build stored the cash shares as float32 and the same check read 3 × 10⁻⁸ — storage precision, not a
construction difference, but the panel is what every downstream number comes from, so it was rebuilt at float64
rather than the tolerance being widened. Recorded because "we relaxed the tolerance" and "we fixed the storage"
are not the same event.

---

## 5. E7.6's outcome is stronger than expectation 4

**Registered expectation (PREREG 11.4):** "the pilot's paths do not regenerate under the v2.1 switches". They do
not — but not for the registered reason (23 GenConfig fields added after the pilot taking today's defaults).
**The engine the pilot ran on cannot be constructed at all**: `fw_single`'s SMM estimate was rejected in Phase 2,
and the generator raises `FileNotFoundError: engine 'fw_single' needs an accepted SMM estimate … none exists (the
attempt was rejected: fw_single_stock.REJECTED.json)` for 52 of 52 runs.

Under the documented CAL fallback engine the paths are constructible and 37.5–81.7 price units from the logged
ones. `Gen_Config_Hash` recomputed from the stored metadata matches in 52 of 52, so the provenance record is
intact; it is the generator that moved.

Consequence, as pre-registered: the pilot is re-scored on its logged columns only, **no baseline is rebuilt on any
pilot cell**, and no normalised value is recomputed.

---

## 6. G3 fails at every θ under per-window scoring

Not a disconfirmation of a registered expectation — PREREG 11.5 expected only that the θ profile (PASS at
0.03–0.05, FAIL at ≥ 0.08) would be confirmed, and it is, with the crossing located between 0.05 and 0.0656. What
the phase adds is that REG-12's option B, which 16A itself names as an admissible response to a G3 failure, makes
G3 fail **at every θ including 0.05** (bull-trap median 1 switch, share 0.39). It is recorded here because a
reader of 16A's text would reasonably expect per-window scoring to help G3, and the measurement says the opposite.

---

## 7. `PILOT_NOTES.md`'s prose disagrees with the table it was written from

The re-score reproduces `generated/pilot_report_per_run.csv` run by run (52 of 52, worst 2.2 × 10⁻¹⁶). Against
that table, the note's prose figures for ISFJ static (0.23 vs 0.2514), ENTJ static (0.25 vs 0.2101) and ENTJ
memory (0.26 vs 0.2414) — and their normalised values — do not agree; INTJ's three cells and all three `swapped`
cells do, to rounding. The four cells that disagree are exactly the four whose n is 4 rather than 3, because the
published arm means average the T = 30 smoke runs in with the T = 200 runs. Both constructions are now published
(`e7_pilot/pilot_rescore.md`) and the note is corrected to its own table.

---

## 8. The v2.1 ceiling is 0.0028, not 0 "by construction"

PREREG 2.2 says the ceiling is "the mandate-conditional oracle (0 by construction on resolvable steps)". Measured
on the panel at θ = 0.05 it is **0.0028**, not 0: the oracle is *executed* through `PortfolioV2`, so its realised
cash share is not its target — a target within the 1-point dead band is not traded at all, and between trades the
allocation drifts with the price. The phrase "0 by construction" is true of the oracle's *target series* and false
of the trajectory the oracle actually produces, which is what MCR reads.

Nothing is re-specified: the ceiling is the mandate-conditional oracle's realised MCR, which is what
`floors_and_ceilings_v21` takes and what the pre-registration names. The 0 is corrected to 0.0028 wherever it is
quoted, and the reason is the dead band and the drift, both of which are DESIGN entries in
`evaluation/params/scoring.json`.

The relabelling's magnitude, on the same cells (`e7_rescore/normalisation.{csv,json}`): the level-free observables
oracle's normalised MCR moves from **1.067** under the v2 convention — *above 1*, because the v2 "ceiling" is
constant-mix and the oracle beats it — to **0.919** under the v2.1 convention. A published figure above 1 under a
convention that the note described as "1 = mandate-conditional oracle" is exactly the mislabelling P0-2 found;
this is its size.

---

## 10. The registered locator is silent on an unmeasurable grid point, and the two readings differ on one cell

**Found on 10 September 2026, after the report was written, while checking whether any experiment was still
missing.** The registered rule is "the smallest grid value at which the accuracy is ≥ 0.80 and **stays ≥ 0.80 at
every larger grid value**". It does not say what to do when a larger grid value has **no accuracy to compare** —
`sign_acc` is left NaN wherever fewer than 10 resolvable rows remain, which happens at the top of the grid on thin
populations. Two readings follow from the same sentence:

| reading | bull-trap calm | every other cell |
|---|---|---|
| **skip an unmeasurable point** (it carries no evidence either way) — **PRIMARY** | θ_info = **0.15** (accuracy 0.850 on n = 246, and 0.938 / 0.923 at the two larger measurable values) | unchanged |
| an unmeasurable point breaks the chain | **not reached** | unchanged |

The difference is caused by **two rows** at θ = 0.30. It affects **bull-trap calm only**, in both feature sets, and
**neither co-primary value moves**: pooled all rows stays 0.05 and pooled calm stays 0.20 under both readings.

**Why this is recorded rather than quietly settled.** The first implementation skipped unmeasurable points; a later
edit — made while adding the interval columns, not while looking at a result — changed it to the other reading, and
the published per-scenario table silently changed with it. Both readings are now computed by the same function and
**both are stored per cell** (`theta_info`, `theta_info_unmeasurable_breaks_chain`), with the affected cells named
in the file's own `note` field. The primary is the skipping reading, on the argument that a cell with two rows must
not be allowed to decide the answer — an argument about evidence, not about which value is more convenient, and one
that would have been made the same way before the numbers were seen.

---

## 11. What was confirmed

For symmetry with the above, the registered expectations that held:

| # | expectation | outcome |
|---|---|---|
| 1a | θ_info reached near 0.05 on pooled rows | **confirmed exactly**: the crossing is at θ = 0.05, 0.8005 [0.791, 0.810] |
| 2 | θ_cost far below the smallest grid θ; the band width cancels; every persona the same | **confirmed**: 0.0020 for all three personas; spread across w ∈ {0.10, 0.20, 0.40} of 1.8 × 10⁻⁶; a 25× cost tier would be needed to reach 0.05 |
| 3 | θ_var ≈ 0.046, between the grid's 0.03 and 0.05 | **confirmed**: 0.046321, inside the AR(1) reference band [0.0389, 0.0724] |
| 5 | G3's θ profile: PASS at 0.03–0.05, FAIL at ≥ 0.08 | **confirmed and refined**: the crossing is between 0.05 (PASS) and 0.0656 (FAIL) |
| 6 | at least one rule would be undecidable or come out the wrong way | **confirmed** — items 1, 2 and 5 above |
