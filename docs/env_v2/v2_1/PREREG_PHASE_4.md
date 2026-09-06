# Pre-registration: Phase 4 (events, schedule, controls and the calendar)

**Written before any Phase-4 run.** Plan Section 8; protocol Section 1; power formulas Appendix A.
Register entries in force: REG-7 (control), REG-8 (event dynamics), REG-9 (calendar/orderings),
REG-15 (data), REG-18 (hazard horizon).

Nothing below is moved after data are seen. If a criterion turns out to be wrong it is corrected in a
separate documented step *before* the re-run, with a disclosure of what had already been seen, and the
result is reported under both the old and the new rule (`PREREG_PHASE_3_ADDENDUM.md` is the template).

---

## 0. Team decisions in force at the time of writing

| Decision | Status | What Phase 4 does |
|---|---|---|
| **D1** data | C, hybrid | Fit on the free panel; publish the survivor-vs-literature gap; keep every fit re-runnable on WRDS by a data-path change. |
| **D4** event population | **Single-stock panel primary** (team, 5 Sep 2026) | E4.1 produces both tables; E4.2's ranges are drawn from the panel. Index tables published beside, and every parameter flagged whose range would differ under them. |
| **D6** calendar default | **"Day-N" kept** (team, 5 Sep 2026) | All three renderings implemented behind a switch; the generator-side audit published for all three; Phase 9's LLM probe revisits. |
| **D13** start price | mechanism C (`start_price_mode="both"`) | In force, unchanged. |
| **D14** control purpose | **Deliberately left open** (team, 5 Sep 2026) | All four definitions implemented and audited under this pre-registration; the phase reports the audits and **stops for the adoption decision**. Phase 4 does not pick the purpose. |
| **Level anchoring** | **Route (c) preferred, contingent on E4.0** (team, 5 Sep 2026) | E4.0 decides it by the rule in section 2. If E4.0's rule is not met, the level as handed over stands and every affected number is flagged. |
| **D5** if no event formulation qualifies | not taken | E4.6 reports the table and stops. |
| **D2, D10** | not taken | Not needed in Phase 4. |

---

## 1. Inherited numbers verified before use

Following `PHASE_3_REPORT.md` section 1.1. No Phase-4 experiment builds on a Phase-3 figure until the figure
has been checked against the generated file it cites. Where a document and a generated file disagree, the
generated file wins and the document is corrected in the Phase-4 report.

Checked before use, each against its own file:

| Inherited figure | Cited value | File it must come from |
|---|---|---|
| Fast-crash rise time (onset to RV21 peak) | 30 d [29, 35], n = 642 episodes / 313 stocks | `e3_3/episodes.json`, `e3_3/dd_episodes.csv` |
| Generator's best achievable rise time | 75.5 d (mech. A), 103 (B), 80 (C) | `e3_4/mechanism.json` |
| Six phase variance multipliers and CIs | det 1.37, panic 7.45, stab 3.11, mania 1.18, blow-off 1.65, post-top 1.16 | `e3_3/episodes.json`, `e3_4/calibration.json` |
| Topped share at the engine in force | 8 % | `e3_after_checklist.csv` item 11 |
| Sustained-bull rejection / coverage / undefined | 32.9 % / 0.044 / 10 % | `e3_after_checklist.csv` item 17, `e3_7/discrimination.*` |
| Bull-trap, crash, flat rejection | 10.7 %, 0.8 %, 0.0 % | `e3_after_checklist.csv` item 17 |
| Realised post-top variance ratio | 1.59, n = 20 | `e3_4/` mechanism arms |
| Engine in force | sigma_V 0.01457, h 22.38 d, sd(x) 0.068 | `e2_3/smm_ar1c_full_p3.json`, `e3_9/level_check.json` |
| Panel calm reference | 0.01703 [0.01632, 0.01764], n = 1592 / 412 | `e3_9/level_check.json` `i_panel_calm` |
| Deployed unconditional | 0.02843 [0.02675, 0.03024], +30.5 % | `e3_9/level_check.json` `iii_deployed_unconditional` |

Also verified before extension: the inherited `e3_3/dd_episodes.csv` and `ru_episodes.csv` columns E4.1 builds
on (`peak`, `trough`, `depth`, `peak_date`, `trough_date`, `rise`, `calm_over_uncond`), by recomputing them
from the panel for a random sample of 40 episodes with a fixed seed and requiring exact agreement on the
integer indices and agreement to 1e-10 on the floats. **Rule:** any column that does not reproduce is
recomputed for the whole table and the discrepancy is reported; E4.1 does not build on an unreproduced column.

---

## 2. E4.0 - the level anchoring, decided by measurement

**Why this is first.** Phase 4 builds the schedule on the generator's volatility level. Phase 3 reported a
confirmed level double-count (+30.5 % on the deployed unconditional) and left the anchor to the team. The
team's answer (5 Sep 2026) is to prefer route (c) *contingent on Phase 4 separating two things Phase 3's own
diagnostic could not separate*. This section registers that separation and the rule that decides the anchor.

**The reading being tested.** `envs/v2/garch.py::GJRParams.phase_mult` returns `self.mult.get(phase, 1.0)`.
The six event phases carry FIT multipliers; **calm falls through to a stipulated `1.0`**. Because the six are
ratios *to the panel's unconditional* applied to a base that equals the panel's unconditional, each event
phase lands at its correct absolute variance; calm is the only phase whose level is not measured. The
hypothesis is therefore: *the deployed excess is driven by calm's unmeasured multiplier, and the residual is
a scenario-mix artefact of pooling four scenarios with equal weight.*

### E4.0a Decomposition

| Part | Statistic | n | Rule |
|---|---|---|---|
| (i) **Calm defect, like-for-like** | Generator flat-scenario pooled sd of daily log returns vs the panel's calm reference; ratio with 1,000-resample bootstrap CIs on both sides (paths clustered by seed; panel clustered by stock) | 200 seeds x 200 d; panel n = 1592 episodes / 412 stocks | **Confirmed** iff the two 95 % CIs are disjoint. |
| (ii) **Fitted calm multiplier** | m_calm = median over panel drawdown episodes of `rv_calm / rv_uncond`, 1,000-resample **stock** bootstrap | same panel | Reported with its CI and n. The parameter is FIT if `1.0` lies **outside** the CI; otherwise the stipulated 1.0 is not refuted and route (a) stands. |
| (iii) **Scenario-mix artefact** | Deployed pooled sd recomputed under (a) E3.9's equal scenario weights and (b) the panel's own phase-day weights from E4.1 | 200 seeds/scenario | Reported as a difference, no pass/fail. Quantifies how much of the +30.5 % is *not* a generator defect. |
| (iv) **Counterfactual** | Re-run the 4-scenario panel with `mult["calm"]` set to the fitted value: pooled sd, flat sd, flat median sd(x), and the six realised event ratios | 200 seeds/scenario | See adoption rule. |

### E4.0b Adoption rule (pre-registered)

The fitted calm multiplier is **adopted** iff **both**:

1. (i) is confirmed **and** 1.0 lies outside (ii)'s 95 % CI; **and**
2. under (iv), after **one** closed-loop re-calibration of the kind `e3_4_mechanism.py` already performs
   (60 seeds x 3 iterations, 200-seed verify), all six realised event variance ratios lie inside their
   E3.3 95 % CIs.

If 1 holds and 2 fails, the phase **reports the measured cost and stops for the team** rather than choosing:
the fitted calm multiplier and the six fitted event ratios cannot both be honoured, and which to keep is a
decision about what the environment is for, not a measurement.

If 1 fails, route (a) stands: the level as handed over, stated in the report's section 2, with every Phase-4
number flagged that would move under (b) or (c).

**What is reported either way**: flat sd(x) and the four coverage figures before and after, because lowering
calm variance lowers sd(x) and therefore coverage, and E4.5's control redesign has to absorb that.

**Power.** The calm comparison is between a 200-seed x 200-day generator sample (about 40,000 daily returns,
clustered) and 1,592 panel episodes over 412 stocks. Phase 3 already measured both with disjoint intervals;
E4.0 re-measures under the same estimator to confirm the comparison is like-for-like (calm-vs-calm), which is
the part Phase 3's `double_count_confirmed` rule did not establish.

---

## 3. E4.1 - episode tables

**Populations.** (a) **Single-stock panel** (primary, D4): analysis set A, 417 names, Adj Close ffilled,
2000-2024, `tools/phase1/panel.py`'s exclusion rule unchanged. (b) **Index episodes**: Mishkin and White
(2002, NBER w8992; read) 15 US crashes of 20 % or more; Barro and Ursua (NBER w14760 / *Research in
Economics* 71(3)) country-index annual crashes of -25 % or worse; the Shiller monthly series for the
cumulative-decline shapes.

**Pagan and Sossounov dating.** The algorithm is applied to the panel as the plan directs. **Their 25/15-month
durations were not read from the paper and are not quoted anywhere in this phase** - the algorithm's censoring
constants are stated as this phase's own choices, scaled to daily data, and their effect is reported by
running the whole table at two censoring settings.

**Episode families.** Drawdowns of 20 % or more and of 30 % or more (the latter is the inherited family,
re-verified per section 1); run-ups of 100 % or more in 504 trading days (inherited, re-verified).

**Quantities, each with empirical P10 / P50 / P90 and a 1,000-resample stock-bootstrap CI on each quantile,
n stated as (episodes, stocks):**

| Quantity | Definition |
|---|---|
| Peak-to-trough duration | trough - peak, trading days |
| Depth | P_trough / P_peak - 1 |
| **Deterioration length** | peak to first day P at or below 0.9 x P_peak (the existing `onset`; **this is E4.2's rise-time lever**) |
| **Front-loading** | share of the total log decline completed in the first third of peak-to-trough |
| Recovery share at 60 / 120 / 200 d | (P_{trough+k} - P_trough) / (P_peak - P_trough), k in {60,120,200} |
| Run-up length | top - start |
| Run-up size | P_top / P_start |
| **Post-top drop and length** | trough after top within 200 d, and its depth |
| **LPPLS (m, omega, and the fitted hazard)** | Filimonov and Sornette (2013) linearised calibration on each run-up window |
| Peak P/V-hat | P_top over the EDGAR value proxy at the top |
| Cross-sectional drawdown correlation | share of names in a drawdown on the same day; the common-factor loading E4.8 needs |

**LPPLS protocol, registered before fitting.** Windows: [start, top] per run-up episode. Search: the
Filimonov-Sornette linearisation over t_c in (top, top + 63], m in (0,1), omega in [1,20], with 20 random
restarts per episode and a fixed seed. **Stability is a reported diagnostic, not a filter**: an episode's fit
is labelled *stable* iff the interquartile range of m across restarts is below 0.10 and of omega below 2.0.
The population statistics are reported over **all** episodes and over stable ones separately.
**Rule (E4.4's trigger):** the LPPLS route supports a super-exponential mania drift iff the stable share is at
least 0.50 **and** the median m is inside (0,1) with a CI excluding 1.0. If it is not met, E4.4 reports the
failure and falls back to the scripted-drift alternative with its shape FIT from the run-up table - as the
plan directs, and *not* by relaxing this rule.

**Compute.** LPPLS is embarrassingly parallel by episode, so it goes to Kaggle. The cross-machine reference
row is re-run on the first kernel of this phase before any offloaded number is used.

---

## 4. E4.2 - sampling ranges from the tables

Each schedule parameter is drawn from the panel's empirical **P10-P90** (FIT), truncated only where T = 200
forces it, with **the truncation rate reported per parameter**. The current uniform ranges are printed beside.

| Schedule parameter | Current (DESIGN) | Drawn from |
|---|---|---|
| `setup_len` (setup_first) | U(0.25T, 0.55T) | E4.7's mix requirement, not the episode table (it is a rendering choice, not an episode fact) - see section 9 |
| `det_len` | U(15, 40) | deterioration-length P10-P90 |
| `panic_len` | U(15, 70) | (peak-to-trough duration minus deterioration length) P10-P90 |
| `D_V` | U(0.10, 0.30) | fundamental-decline share of depth (E4.8's shape test) |
| `delta` | 0.70 fixed | depth P10-P90 net of D_V |
| `delta_end` | U(delta, 1.0) | recovery-share-at-60d P10-P90 |
| front-loading | fixed 0.5-in-first-third | front-loading P10-P90 |
| `kappa`, mania length | U(0.02, 0.04) | jointly from the LPPLS fits (E4.4) |
| `post_top_len`, `post_top_drop` | U(10,30), U(0.30,0.50) | post-top length and drop P10-P90 |
| `mu_bull` | U(0.0015, 0.0025) | non-crashing run-up drift (E4.5) |

**The rise-time criterion.** Phase 3 measured the target: fast crashes (peak-to-trough at most 126 d,
n = 642 / 313) go from onset to RV21 peak in **30 d [29, 35]**; the generator reaches 75.5 d at best under any
REG-6 mechanism, and Phase 3 established that the schedule template, not the variance mechanism, owns the gap.

- **Statistic:** the generator's median onset-to-RV21-peak rise time, measured by the *same*
  `tools/phase3/episodes.py::rise_decay` estimator used on the panel, on crash-scenario paths.
- **n:** 500 crash seeds (the SE of a median at this n is about 1.5 d from Phase 3's spread).
- **Rule:** the schedule is accepted iff the generator's median rise time's 95 % bootstrap CI **overlaps the
  panel's fast-crash CI [29, 35]**. If no admissible parameterisation reaches it, the report states the best
  achieved value with its CI, says which constraint binds, and the criterion is recorded as **not met** -
  it is not relaxed.
- **Registered in advance:** the rise time is a *joint* function of `det_len` and the panic front-loading, so
  the two are searched together over the FIT P10-P90 box, and the report publishes the whole surface, not
  the winning cell.

---

## 5. E4.3 - the hazard (REG-18)

Three mappings from GSY's two-year industry crash probabilities to a daily single-stock hazard:

- **A** cumulative hazard over the mania length equals the GSY probability at the peak run-up (no time scaling);
- **B** scaled by mania length over two years;
- **C** h0 **and** b fitted directly on the panel's own run-ups of 100 % or more (E4.1), GSY used only as the
  industry-level cross-check.

b under A/B from a logit of GSY's crash indicator on the log run-up, using their 20 / 53 / 80 % points at
50 / 100 / 150 % net-of-market run-ups (read). The horizon scaling is **DESIGN** and is bracketed
{0.5x, 1x, 2x} in the sensitivity table.

- **Statistic:** the generator's topped share within 200 days.
- **n:** 500 bull-trap seeds per mapping (binomial SE about 2.2 pp).
- **Rule (REG-18):** adopt the mapping whose topped share lies inside the **panel's** topped-share CI from
  E4.1's run-up table. **If the panel has fewer than 30 run-up episodes with a resolvable 200-day outcome**,
  the CI will not be narrower than the A-B difference; in that case all three are reported and the
  {0.5x, 1x, 2x} bracket is kept as the sensitivity, as REG-18 directs - no mapping is adopted by preference.
- **Retired as targets, reported as outcomes:** the 40-60 % topped band and the P/V 1.6-2.5 band. Checklist
  item 11 is re-expressed accordingly.
- **Removed:** `tools/calibrate_hazard.py`'s arbitrary score and rejection penalty.
- The **uncapped** mania run is included in the report (item 41).

---

## 6. E4.4 - mania drift

kappa and the mania length drawn **jointly** from E4.1's LPPLS fits so that the drift cap is unnecessary.

- **Statistic:** the share of mania days on which `g` hits `g_max`.
- **n:** 500 bull-trap seeds; the share is clustered by seed, so the CI is a seed bootstrap.
- **Rule:** the cap is unnecessary iff the **upper** 95 % bootstrap limit of the binding share is below 0.05.
- **Convexity** is tested on the pre-cap segment only (the fraction of mania runs whose log-price second
  difference is positive over the run), reported with its CI.
- **Fallback, registered now:** if E4.1's LPPLS stability rule (section 3) is not met, the super-exponential
  route is reported as unsupported and the scripted-drift alternative is used with its shape FIT from the
  run-up table. Amendment **A5** (the mania drift cap) is revisited with this evidence.

---

## 7. E4.5 - the sustained-bull control (REG-7)

**All four definitions implemented and run.** No definition is adopted in this phase: D14 is open and the
purpose is the team's. What Phase 4 delivers is the four audits, per definition, so the team decides on
numbers.

- **A** same mispricing process as flat, no x-band; validity on V only (V_T/V_1 at or above a **FIT**
  threshold from the non-crashing run-up table - the current `1.2` is stipulated and is replaced by a fitted
  value).
- **B** band on V only, mania driver switched off.
- **C** the anchored x of v2 (`LAM_SB = 0.15`), recorded for completeness.
- **D** rendered-matched: the flat x-distribution with a rising V, no phase multiplier, same jumps.

**n = 500 seeds per definition.**

| Audit | Statistic | Rule |
|---|---|---|
| (i) Realised x | path-mean x P10/P50/P90; realised sd(x) | reported |
| (ii) **Selection** | two-sample KS distance between accepted and rejected paths on daily sd, ACF(1) and IV | **bootstrap 95 % upper limit below 0.10** (equivalence, per protocol section 1 - never "the test did not reject") |
| (iii) **Discrimination** | accuracy of a day-level classifier of sustained-bull vs flat on demeaned, level-free returns | **at or below the 95th percentile of a label-permutation null**, computed **here** (1,000 permutations) |
| (iv) **Acceptance at baseline** | REG-7's per-definition form: under **C**, "the mandate-conditional oracle and constant-mix have the same regret within the CI while band-MAS differs"; under **A/B/D**, "the oracle's regret gap over constant-mix in the control equals its gap in flat within the CI" | reported per definition |

**Registered in advance - the vacuous-KS case.** Under A, B and D the x-band is removed, so the rejection
rate may be near zero and there may be no rejected sample to compare. **If fewer than 30 paths are rejected**,
(ii) is reported as *"no selection is possible by construction; the KS test is vacuous at n_rej = k"* and is
**not** counted as a pass. This is stated now because it is the expected outcome for A/B/D and must not look
like a result obtained after the fact.

**`test_sustained_bull_selection`** (items 18, 42, strict xfail) ends this phase either **passing** or
**re-registered with a new owner and a stated reason**. Amendment **A4** (sustained-bull anchoring) is
revisited with this evidence.

**Power.** At 500 seeds x 200 days the classifier's accuracy SE is below 1 pp, so a 5 pp departure from chance
is detected. The KS equivalence at D0 = 0.10 has about 0.8 power against a true 0.05 at these n (Appendix A).

---

## 8. E4.6 - event dynamics (REG-8)

**Four formulations, all implemented and all run.** (i) tracking gain lambda (the incumbent; lambda swept over
{0.02, 0.05, 0.10, 0.25}); (ii) shifted perceived fundamental p* with a regime-specific pull phi_regime FIT
from the panel's crash-window decay; (iii) scripted drift with no feedback plus rejection; (iv) unscripted
regime switching without error correction.

**n = 500 crash seeds and 500 bull seeds per formulation** (and per lambda for (i)).

*Deviation from the plan's 200, stated as a deviation:* the plan and REG-8 register 200 seeds, at which a
share has SE about 3.2 pp and the coverage rule's 0.70 threshold cannot be distinguished from a true 0.65
(power about 0.5). Appendix A's share formula gives **n about 534** for 80 % power against a true 0.65 at
p0 = 0.70; 500 is taken as the achievable count and its power against that alternative (**0.78**) is stated.
This is an *increase* in the pre-registered sample, decided before any run, and is affordable because these
are simulation-only stages (Phase 3 measured 800 200-day paths at about 4 min locally, and a 4-vCPU Kaggle
kernel ran E3.4's whole four-stage chain in about 10 min).

| Statistic | Definition |
|---|---|
| **Script share** | R-squared of the scripted drift d_t on realised delta-x over event-phase days (0 for (iv) by construction) |
| **Coverage** | share of paths whose peak-to-trough depth **and** duration fall inside E4.1's P10-P90 |
| **Rejection rate** | share of attempts rejected by `check_validity` |
| Checklist items 10 and 20; the level-free leakage statistics | as defined by their own tools |

**Rejection ceiling, pre-registered here from the episode tables (not in Phase 6).** The ceiling is registered
as a *formula on E4.1's output*, fixed now, evaluated when E4.1 completes:

> **ceiling = 1 minus (the share of real panel episodes that fall inside their own P10-P90 on depth and
> duration jointly).** By construction of a P10-P90 box on two quantities this share is about 0.64 for
> independent marginals and is measured exactly in E4.1; the ceiling is its complement, i.e. a generator may
> reject no more often than the real world "rejects" its own episodes under the same box.

**Adoption rule (REG-8, unchanged).** Adopt the formulation with the **lowest script share** among those whose
coverage is at least **0.70** (a DESIGN margin below the 0.80 that the P10-P90 box gives by construction,
labelled as DESIGN) and whose rejection rate is below the ceiling. **If none qualifies, report the table and
stop for D5.**

**Registered in advance:** any formulation whose coverage 95 % CI straddles 0.70 is reported as **undecided**,
not as a pass or a fail. Phase 3's experience is noted: a multi-arm rule can be decided by something outside
the block it tests; if that happens here the report says which block actually decided it.

**Re-expression, registered now.** (ii) and (iv) change what delta *means* - from a target discount to a
belief shift - so checklist item 10 ("severity matters") becomes a statement about D_V and the belief shift,
not about a target. The re-expressed item is defined **before** the runs and reported for all four
formulations under both the old and the new expression.

---

## 9. E4.7 - orderings and the calendar (REG-9, D6)

(a) **Ordering factor** added to `experiments/arms_v2.py` (`simulation/runner_v2.py` already supports it) and
tested by `test_arm_grid_has_ordering_factor`.

(b) **The mix and setup range.** Statistic: the accuracy of a **day-index-only** macro-phase classifier within
each scenario. **n = 200 seeds** - REG-9's registered count, kept because its rule's margin ("+1 pp") *is* the
sampling half-width at 200 seeds; a 500-seed replication is reported as a secondary.
**Rule:** a mix is acceptable iff accuracy is at or below the 95th percentile of a label-permutation null
(1,000 permutations) **+ 1 pp**, in every scenario.

(c) **Three day-index renderings** implemented behind a switch - random calendar date, no date, "Day-N"
(default per D6) - with the generator-side audit published **for all three**. Random dates exclude start
dates that place the window inside 1987, 2000-02, 2008-09 or 2020, as REG-9 requires.

(d) The quarter phase of `days_since_eps_announcement` randomised per seed.

---

## 10. E4.8 - labels and small fixes

| Fix | Registered statistic and rule |
|---|---|
| **Blow-off given a dynamic criterion** | The label must be assignable *in real time* so the multiplier can drive the GARCH. Criterion: drift `g` above a **FIT** threshold from the run-up table's blow-off windows. **Rule:** the realised blow-off variance ratio's CI must contain the panel's **1.65 [1.58, 1.71]**; the ex-post relabel is kept behind a switch and reported beside (its achievable value is about 1.19). |
| **Top day off-by-one** | The top day is recorded at the **realised** price peak. Reported as the distribution of (recorded minus realised) top day before and after; the fix is correct iff the after distribution is a point mass at 0. |
| **Crash V drift after deterioration** (item 73) | Currently `mu_V = 0` in panic and stabilisation. Tested against E4.1's fundamental-decline shape (EDGAR value proxy through the episode). **Rule:** the shape adopted is the one whose fitted V-path over the episode lies inside the panel's P10-P90 envelope on at least 0.70 of days; both are reported. |
| **Post-top reversal leg** | Re-derived so its realised variance ratio can reach the panel's **1.16 [1.13, 1.20]**. Phase 3 established the leg is drift-dominated (floors at 1.59, n = 20, whatever the innovation multiplier). **Rule:** the new shape is accepted iff the realised ratio's 95 % CI contains 1.16 at 500 seeds; if no admissible shape reaches it, the report states the floor achieved and the criterion is recorded as not met. |
| **Multi-asset shared event** | Replaced by per-asset event draws with a common-factor loading **FIT** from E4.1's cross-sectional drawdown correlation. |

---

## 11. What is re-run on the handed-over state

Phase 4 changes the event block, so it pays the execution-order rule in full: re-freeze, re-audit, new hashes.

`tools/phase3/after_state.py` (path hashes, the 200-seed checklist, the freeze, the level-free audit) pointed
at Phase-4 output names; plus `e3_7_discrimination.py` and `e3_8_decomposition.py` re-run on the handed-over
state, because the schedule, the hazard and the control all move coverage and the event-phase channel is the
one this phase changes. Measured Phase-3 costs are budgeted: path hashes 19 s, checklist about 14 min, the SEP
level-free audit about 2.5 h, L5 at 40/50 seeds about 1 h, freeze 3 s.

---

## 12. Compute and the offload rule

**Simulation and optimisation offload to Kaggle; model fits do not.** Every audit, L5 and surrogate R-squared
comes from the laptop. The cross-machine reference row
(`python -m tools.phase2.e2_3_smm --reference-row`) is re-run on the first Phase-4 kernel before any offloaded
number is used; Phase 3 measured agreement to 6.4e-16 across numpy/scipy versions. `datasets/` is never
uploaded; derived statistics are cached and shipped, as `e3_3/episodes.json` does.

Offloaded: E4.1's LPPLS fits, E4.3's three mappings x 500 seeds, E4.4's sweep, E4.5's four definitions x 500
seeds, E4.6's four formulations (plus 4 lambda) x 500 crash and 500 bull seeds, E4.7's ordering-mix sweeps.
Local only: every leakage audit, the level-free surrogate, L5, the discrimination and decomposition re-runs.

---

## 13. What is reported if a rule is not met

Under every rule above: the achieved value with its n and CI, the constraint that binds, and the verdict
**not met** - never a moved threshold. If a criterion turns out to be undecidable at the achieved sample, the
verdict is **undecided** and the power that would decide it is stated. Deviations, shortfalls and achieved
counts are reported, not intended ones.

Four phases in a row have had at least one undecidable criterion (Phase 3 had three). The null-simulation
script that checks each threshold is decidable at the stated n before it is committed is
`tools/phase4/prereg_power.py`, and it is kept.
