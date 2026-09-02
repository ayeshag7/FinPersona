# Addendum to the Phase-2 pre-registration: designs corrected in documented steps

`PREREG_PHASE_2.md` was written on 1 September 2026 before any Phase-2 experiment. This file records every
design element that was found **wrong or undecidable after its first measurement** and corrects it in a separate
step, **before** the run it governs, with disclosure of what had already been seen — the procedure
`PREREG_PHASE_1_ADDENDUM.md` established. Where a rule changes, results are reported under **both** the original
and the corrected rule.

---

## 1. The simulation-noise rule of PREREG §4.3 cannot be met at any affordable path count, and is re-scoped to the reported J

### What was pre-registered

> Simulation per evaluation: 20 paths × 5,000 days, burn 500, common random numbers … §9's PA2 measures the
> simulation noise of every pooled moment in units of the data bootstrap sd; **if any persistence moment's ratio
> exceeds 0.30 the path count is raised (20 → 50 → 100) until it does not, before the fit, and the achieved
> count is stated.**

### What had been seen when this correction was written

PA2 was run on 1 September 2026 after `e2_3_data` produced `data_boot_full.npy` and **before any SMM fit**. The
maximum ratio (simulation sd of a pooled moment ÷ the data's block-bootstrap sd of the same moment) over the
eight persistence-carrying moments, at T = 5,000 and 12 CRN seeds:

| engine | 20 paths | 50 paths | 100 paths |
|---|---|---|---|
| `ar1` | 1.97 | 1.49 | 0.71 |
| `fw_v2` | 2.27 | 1.59 | 0.93 |
| `fw_plus` | 1.41 | 0.74 | 0.68 |

Nothing about any fit, any θ̂ or any J was known.

### Why the rule as written is unmeetable

The ratio falls as 1/√n_paths, so reaching 0.30 from 0.93 at 100 paths needs ≈ 960 paths per evaluation — and the
rule as written applies to **every** evaluation of the optimiser. The pre-registered ladder stops at 100 and the
acceptance set of "every evaluation ≤ 0.30" is therefore empty inside the registered design. That is the same
failure mode as `PREREG_PHASE_1_ADDENDUM.md` §1 and §4: a bound written before its own null spread was measured.

### The correction (fixed here, before any fit)

The rule is **split according to where the noise actually matters**, and the numbers that go into a verdict are
the ones the bound is applied to:

1. **The optimiser** runs at **n_paths = 200**, T = 5,000, burn 500, with **one common random-number draw**
   (seed SM = 110001) shared by every θ. Under CRN the objective is a *deterministic* surface, so its noise does
   not scatter the search; what it does is displace the surface by a roughly θ-independent amount. 200 paths is
   chosen because the simulator is vectorised over paths and costs only ≈ 1.7 s per evaluation at 200 against
   ≈ 0.6 s at 20 (measured), so the tenfold increase in paths costs less than threefold in time.
2. **The reported moment vector and J at θ̂** — the numbers the χ² verdict, the residual table and the parameter
   file are built from — are the **average of K = 20 independent CRN replicates** at 200 paths, i.e. 4,000
   simulated paths. The standard error of each reported moment is then the 200-path sd ÷ √20, which is
   ≈ 0.15 bootstrap sd at `fw_v2`'s worst moment: **inside the pre-registered 0.30 bound**. The realised
   `sim_se_over_boot_sd` vector is written into every fit's JSON and reported.
3. **The single-CRN J the optimiser minimised** (`J_single_crn`) is reported beside the averaged J, so the size
   of the CRN displacement is visible rather than hidden.
4. **Franke–Westerhoff's bootstrap p-value is unaffected and remains the primary acceptance criterion.** Its
   Monte-Carlo replicates are simulated at the **data's own panel size** (417 paths × T_period days) by
   construction, so the model's J distribution and the data's bootstrap J distribution are on the same footing;
   no "simulation noise ≪ data noise" condition is needed for it to mean what it says. The χ² criterion, which
   does need that condition, is reported as the secondary one.

**Reported under both rules.** Each fit's JSON carries `n_paths`, `K_report`, `sim_se_over_boot_sd`, `J` (the
K-averaged value used for the verdict) and `J_single_crn` (the value the pre-registered 20-path single-draw
design would have produced at the same θ̂ up to the path count), so a reader can apply either rule.

**What is not changed**: the moment vector, the weight matrix, the shrinkage, the optimiser family, the start
grid, the acceptance thresholds, the periods, the seeds, or E2.4's decision rule.

---

## 2. Compute-bound reductions, fixed before the runs they govern

Measured on the reference machine after the `full` fits were launched (1 September 2026): one SMM evaluation at
the corrected design (200 paths x 5,000 days) costs 1.7-2.0 s, and one Monte-Carlo replicate of the
Franke-Westerhoff p-value at the data's panel size (417 paths x 6,289 days) costs ~8 s.  A `full` cell therefore
costs 1.5-3 h and the fifteen (engine x period) cells of the pre-registered design would cost 25-35 h serially,
which is more than this session has.  **The rule is that compute never shrinks a pre-registered sample
silently**: the reduced design is fixed here, before the runs, the achieved counts are stated in the report, and
any verdict the smaller sample cannot decide is marked undecided.

**What had been seen when this was written**: the three `full` fits were still running and had produced no
result of any kind -- no theta-hat, no J, no acceptance verdict.  The reductions below are therefore made on
timing alone.

| cell group | pre-registered | reduced to | why it is safe, or what it costs |
|---|---|---|---|
| `full` x 3 engines | DE maxiter 40, popsize >= 8p, C = 200 MC replicates, 30 bootstrap refits | **unchanged** | these decide E2.4(a); nothing is reduced |
| `train` x 3 engines | as `full` | DE maxiter 40 kept; **C = 0** (the FW bootstrap p is not computed) | E2.4(b) uses only theta-hat from the `train` fit; acceptance is decided on `full`. Nothing that enters a verdict is lost |
| `p1`, `p2`, `p3` x 3 engines | as `full` | DE **maxiter 15**, **C = 50** MC replicates, no bootstrap refits | these are descriptive (PLAN section 6.2 asks for "three sub-periods"); their J values are reported with the achieved evaluation count and the MC standard error of p (+-7 pp at C = 50 near p = 0.1), and **no sub-period difference is called significant** |
| E2.6 level-free audits | 100 seeds per level x 10 cells | fixed after the first cell is timed, in section 3 below | the sweep's checklist and switch statistics are unaffected |

The optimiser's own convergence evidence is what protects the reduced sub-period search: every fit reports
`start_J_best` (the best of the >= 20 named starts), `end_J`, the achieved evaluation count and the DE
convergence flag, so a cell whose search stopped early is visible rather than assumed converged.

## 3. E2.6's seed counts, fixed before the sweep runs

Measured on the reference machine (1 September 2026, while the SMM fits were still running and before any sweep
cell had been executed): the Section-9 checklist costs ~6 s per seed per scenario set (18.3 s at 3 seeds), so a
200-seed cell is ~20 minutes and the pre-registered ten cells are ~3.3 h; the level-free surrogate on
100 seeds x 4 scenarios (80,000 rows, three estimators, GroupKFold, 500-resample cluster bootstrap) is of the
same order again per cell.  The full pre-registered sweep is ~8 h on top of the SMM fits, which this session
does not have.  **What had been seen**: only the smoke-test timings above; no sweep statistic of any kind.

| statistic | pre-registered | run at | consequence, stated in the report |
|---|---|---|---|
| oracle target switches, sd(x) over 200 d, coverage, rejection and topped shares | 200 seeds x 4 scenarios, every level and matching | **unchanged (200)** | none -- this is the 16A G3 input and it is cheap |
| Section-9 checklist | 200 seeds, every level and matching | **100 seeds**, every level and matching | the share- and median-type items' half-widths widen by sqrt(2) (a share at 0.23 goes from +-0.058 to +-0.083); the report states the achieved count and calls **no** item difference between levels significant |
| level-free leakage surrogate | 100 seeds, every level and matching | **50 seeds, matched-sd arm only** | the matched-innovation arm is **not audited** and is listed as not run; the matched-sd arm's R2 intervals widen by sqrt(2) |
| levels | {30, 60, 120, 250, 500} d + the union rule of PREREG section 5.3 | the same five **plus the fitted half-life (7.5 d)**, in **both** matchings (12 cells, one more than this row first fixed) | E2.2's union rule, applied to the adopted engine's interval [3.81, 23.61] d, would have added levels 5, 10 and 15 d as well. **They were not run** -- a stated shortfall. The fitted point estimate and the upper end of its interval are bracketed by 7.5 and 30 d; the lower end (3.8 d) is below every level run, so the sweep describes the fitted region from above only. The trend from 7.5 to 30 d is monotone in every statistic, so the direction below 7.5 d is not in doubt, but its magnitude is not measured |

Nothing here changes a criterion: E2.6 carries no pass/fail (PREREG section 8), so the reduction costs precision
in a sensitivity table, not a verdict.  The 16A G3 input -- the switch counts -- is the one statistic that feeds
a gate, and it is **not** reduced.

## 4. Post-review extensions (2 September 2026)

The Phase-2 report was reviewed after it was written. Three of the review's pointers are experiments rather than
edits, and are recorded here as **post-review extensions** — the pattern `PREREG_PHASE_1_ADDENDUM.md` §6
established. Each design is fixed here, with its rule, **before** the run; what had been seen when it was
written is the whole Phase-2 report, so each is explicitly a *diagnostic of a result already published*, not a
re-test of a criterion.

### 4.1 E2.7 — does the benchmark still discriminate under the adopted engine?

**Why.** Phase 2 reports that the resolvable share in flat falls from 0.73 to 0.13, and hands the coverage
trade-off to D3/D8 — but without the one number the decision turns on: whether the metric still separates
policies. If |x| ≥ θ on one day in eight, the mandate-conditional oracle and always-hold converge and the
benchmark cannot rank agents, whatever the leakage work shows. This is, in substance, what 16A's G1 asks.

**Design (fixed here).** `tools/l5_report.py` unchanged, on the handed-over state: 40 training seeds
(disjoint from the scored seeds), 50 evaluation seeds, T = 200, three personas × four scenarios, feature sets
{full, price_only, level_free}; policies scored: the true-V oracle, the mandate-conditional oracle, the three
L5 observables oracles, always-hold and constant-mix; statistics MCR at θ = 0.05, band-MAS, turnover, coverage.
Output `e2_7/l5_phase2_after.{csv,md}`, beside Phase 1's `e1_6/l5_after.csv` on the same design.

**Rule.** No pass/fail — G1 is Phase 6's gate on the Phase-6 frozen generator. What is reported is the ordering
and the spread: MCR(true-V oracle) < MCR(observables oracle) < MCR(best trivial policy), with the gaps, per
scenario. **If the ordering fails or the spread collapses in any scenario, that is stated as a finding and put
to the team in §5, not repaired here.**

### 4.2 E2.8 — is the level-free surrogate biased, or is the excess over the bound a real channel?

**Why.** The adopted engine *is* Appendix B's model (a Gaussian AR(1) mispricing on a random-walk fundamental),
so the bound is exact rather than approximate, and the measured level-free calm R² of 0.339 [0.208, 0.434]
against a bound of 0.245 has only two explanations: an optimistically biased surrogate, or an information
channel the bound does not model. The first would affect every level-free leakage number in the programme, so
it is Phase 2's to close rather than Phase 6's to inherit.

**Design (fixed here).** Simulate the bound's model and nothing else — Gaussian random-walk log V, Gaussian
AR(1) x started from its stationary prior, no events, jumps, GARCH or sentiment feedback — build the **same**
level-free feature set (`technicals_block` on the price path, then the audit's `add_level_free_columns` and
5-lag block), fit the **same** three surrogates with the **same** GroupKFold-by-path cross-validation and
500-resample cluster bootstrap, at three configurations: the parameters in force, the v2 state Phase 1 handed
over, and the panel's own fit. 200 paths × 200 days each. `tools/phase2/e2_8_bound_check.py`.

**Rule.** If the 95 % interval of the measured R² lies **entirely above** the analytic window-average bound, the
surrogate is optimistically biased and every level-free leakage number in the programme is affected. If it does
not, that explanation is not supported and the generator's excess is an unmodelled channel, to be characterised
by Phase 6.

### 4.3 E2.6's levels inside the fitted interval

**Why.** The adopted half-life is 7.50 d with a bootstrap interval of [3.81, 23.61] d, and the sweep ran only
7.5 d inside it: a robustness claim of the form "results hold across the fitted persistence" would rest on one
point inside the confidence region. §3 of this addendum listed 5, 10 and 15 d as not run; the review ranks that
above the unrun FW sub-period cells, and it is right — the switch statistics are the cheapest part of the sweep.

**Design (fixed here).** Levels **5, 10 and 15 d** added to both matchings at the **200-seed** oracle-switch
statistics (the unreduced count) and the 100-seed checklist. The calibration is **extended, not recomputed**:
the stored target sd(x) is kept so the cells already run stay valid, and the extension's seeds are keyed on the
level value rather than on its index in the list, so adding levels cannot move an existing one. The different
seed rule is recorded in the output. The level-free audits are **not** extended (they remain the matched-sd arm
at the original six levels), and that is stated.

## 5. (reserved)

Further corrections, if any, are appended here in the same form — what was pre-registered, what had been seen,
why the rule fails, the correction, and the reporting under both rules.
