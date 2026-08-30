# Pre-registration addendum, Phase 1 — a criterion found wrong (protocol Section 1, rule 2)

Written 29 Aug 2026, 22:20 PKT, **after** the first E1.4 generator variant (`current_x_negmean`, the v2 placement) had
finished and **before** the three remaining variants (`B_x_zero`, `A_V_announce`, `C_both`) had finished in the run that
counts (`e1_4/generator_run3.log`). `PREREG_PHASE_1.md` is not edited; this file records the correction, its derivation and
the reporting rule, as the plan's Section 1 requires ("if a pre-registered criterion turns out to be wrong, that is stated,
the empirical reference distribution is derived in a separate documented step, and results are reported under both").

**Disclosure.** An earlier run of the same script (killed with the session, `e1_4/generator_run.log`, 20:19) had printed
point estimates for three variants: E[x] = −0.069 (current), **+0.010** (B_x_zero), and a third line for A_V_announce; their
intervals were not stored. I had therefore seen that the mean-zero variant sits near +0.01 before writing this addendum.
The correction below is derived from the **sampling variability** of the statistic, not from where the point estimates lie,
and it would be needed whatever the remaining variants show; but the reader should weigh the timing.

## 1. The pre-registered rule and why it cannot be met

PREREG §5.3: "on 200 flat paths the 95 % cluster-bootstrap interval of the mean of x (mean over paths of the path mean)
lies inside [−0.02, +0.02]"; power note: "the E[x] SE at 200 seeds ≈ 0.009" (register REG-3, plan §5 E1.4).

Measured on the first variant (200 paths, seeds 70000–70199, T = 200, `e1_4/cache/current_x_negmean.json`):
E[x] = −0.0690, 95 % interval [−0.0881, −0.0476] → **half-width 0.0203**, i.e. sd of the path means ≈ 0.146 and
SE ≈ 0.0103 (the plan's 0.009 was an estimate from a 40-seed pilot).

A TOST-type rule "interval inside ±m" passes only if |x̄| ≤ m − half-width. With m = 0.020 and half-width 0.0203 the
acceptance set is **empty**: a variant with a true mean of exactly zero fails the rule with probability 1 at 200 seeds. The
rule as written is therefore not a test of the variants but a guaranteed failure — a criterion defect, stated as such.

## 2. The corrected criterion, derived before the remaining results are seen

Two readings of the plan's sentence exist; both are reported for every variant:

- **(old) the pre-registered TOST at 200 seeds** — reported as written (it will fail for every variant; the report says so).
- **(new-a) the plan's two-condition wording** — "E[x] = 0 within 2 SE" (|x̄| ≤ 1.96 · SE, a detection test with power ≈ 1
  against the v2 bias of −0.069 at SE 0.0103) **and** |x̄| ≤ 0.02 (the DESIGN margin on the point estimate). This is what
  the plan's §5 text literally says before the LOG §2 note tightened it; it is reported but is not the decisive rule, because
  a point-estimate margin accepts a true bias of up to ≈ 0.02 + 1.96 · SE.
- **(new-b) the TOST at a seed count that gives it power** — the rule's form is kept (95 % interval inside ±0.02) and the
  seed count is derived from the measured sd, following Appendix A's rule (equivalence with 80 % power): the half-width
  plus 0.84 · SE must fit in the margin, SE ≤ 0.02 / (1.96 + 0.84) = 0.0071 → n ≥ (0.146 / 0.0071)² ≈ **420 flat paths**
  for 80 % power at a true mean of 0. Because a true mean of ≈ +0.01 is in play (disclosure above), the confirmatory run
  uses **1,000 flat paths** (SE ≈ 0.0046, half-width ≈ 0.009: the rule passes iff |x̄| ≤ 0.011; power ≈ 0.8 against a true
  mean of +0.007 and ≈ 0.5 against +0.010). Seeds 71000–71999 (`tools/phase1/e1_4_confirm.py`; the path mean of x needs no GARCH fit, so the run is cheap); only the variant selected by the KS rule is run at this
  size; the other variants are reported at 200.

**Decision rule under the correction.** The KS rule (both bootstrap upper limits < 0.10, smaller window distance among
passers) selects the variant exactly as pre-registered. The selected variant is then **adopted provisionally** if it passes
(new-a) at 200 seeds, and **confirmed** if it passes (new-b) at 1,000. If it fails (new-b), it stays in force for the rest
of Phase 1 (something must generate the after-state) and the failure is put to the team as a decision item: the residual
mean of x under mean-zero jumps is then a property of the engine's feedback (Phase 2's question, E2.x), not of jump
placement, and the team decides whether a residual |E[x]| ≈ 0.01 (a third of the smallest θ) is acceptable pending the
engine re-fit. No parameter is tuned to pass the rule (the plan's rule that a criterion is not met by re-tuning stands).

## 3. What is reported

For every variant: E[x] with its 200-seed interval; pass/fail under (old), (new-a); for the selected variant also the
1,000-seed interval and pass/fail under (new-b). The known-defect registry: `test_flat_x_equivalence` is written to the
corrected rule (new-b, asserting the stored 1,000-seed interval, with a 100-seed live guard at (new-a)); the pre-registered
100-seed TOST form is recorded in the report as undecidable (half-width ≈ 0.029 at 100 seeds).

## 4. E1.5 — the burn-in equivalence bound at 500 paths (added 29 Aug 2026, 22:55 PKT, after the pre-registered run)

**Pre-registered (PREREG §6):** per engine and variable (x, σ², n_f), the two-sample KS distance between the day-1 state
of 500 flat paths and the day-5,000 reference of the same 500 paths, 1,000-resample bootstrap upper limit < D0 = 0.10.

**What the run showed (`e1_5/burn_in_n500.md`):** every engine × option fails, including the ≥ 5-half-life burn-in whose
point distances (0.04–0.07) are what two samples of 500 from the *same* distribution produce. Checked by simulation
(`tools/phase1/e1_5_burn_in.ks_upper` on two N(0,1) samples, 20 replicates, 300 bootstrap resamples): at n = 500 per side the
KS point under equality averages 0.055 and the bootstrap upper limit 0.120 — **0 of 20 replicates pass the 0.10 bound**;
at n = 1,000: point 0.041, upper 0.088, 16 of 20 pass; at n = 2,000: point 0.025, upper 0.061, 20 of 20 pass. The rule at
500 paths is therefore a guaranteed failure, not a test; the pre-registered power note ("KS sd ≈ 0.02 at these sizes")
was wrong for a 500-vs-500 comparison (the register's figure was derived for ≈ 1,800 vs 30,000 residuals in E1.4).

**Corrected criterion (new), derived before the powered run:** the same statistic and the same bound D0 = 0.10, at
**2,000 paths per engine** (seeds 80000–81999; the reference is day 5,000 of the same paths), where the bound passes with
probability ≈ 1 at a true distance of 0 and fails at a true distance of 0.10 (upper limit ≈ 0.10 + 0.036); a true distance
of 0.05 passes with probability ≈ 0.8 (upper ≈ 0.086). The decision rule of PREREG §6 / REG-17 is otherwise unchanged
(A for the default engine when both pass, B for the slow engines, "current kept with the shortfall stated" when neither
passes). Reported: both runs, side by side (`burn_in_n500.md` and `burn_in.md`).

**Disclosure.** The 500-path run had been seen: it shows the 260-day burn-in leaving sd(x₁)/sd(x_ref) at 0.68 for
fw_index and pruna (KS x 0.16) and the long burn-in at 1.07–1.09 — so I knew, before setting n = 2,000, that the long
burn-in is the likely outcome for the slow engines; the correction is to the sample size, not to the statistic or bound.

## 5. E1.2 — the recovery study's estimator-C scope (added 29 Aug 2026, 23:35 PKT, before any C cell was run)

**Pre-registered (PREREG §4.4):** estimators A and B at 200 replications per cell, C at 50, over the full grid h ∈ {30,
60, 120, 150, 250, 500} × σ_V ∈ {0.006, 0.012} (600 SMM fits); the data-side SMM interval from 30 bootstrap refits.

**Feasibility measured:** one estimator-C job (a 3-parameter Nelder–Mead SMM with 20 × 5,000-day simulations per
evaluation, ≤ 160 evaluations per start, two starts) takes **310 s** on this machine while the other jobs run (a single
timing, `tools/phase1/e1_2_recovery.cell_job("C", 150, 0.006, 0)`). The pre-registered 600 fits are ≈ 17 h at 3 workers,
the 30 refits ≈ 50 min serial; the remote machine is unavailable for the session. Phase 0's lesson applies: the achieved
count is stated, not the ideal one.

**Achieved design, fixed here:** A and B at the pre-registered 200 replications in all 12 cells (running, unchanged);
**C at 8 replications in the 6 cells h ∈ {30, 150, 250} × σ_V ∈ {0.006, 0.012}** — the cells nearest the three
estimators' own data values (A: h = 5 d, below the grid, nearest 30; the engine: 150; B: 256 → 250) — 48 fits; the
data-side SMM interval from **10** bootstrap refits (stated as such wherever the interval appears). Consequence: C's
usability verdict rests on the median of 8 relative errors per cell (the pre-registered rule needs the median < 0.20; with
8 draws a true median at the boundary is mis-classified with probability ≈ 0.5, so a C verdict within ± 0.05 of the
boundary is reported as undecided rather than usable/unusable), and C's coverage is not measured (as pre-registered).
Cells not run are reported as "not run" in `e1_2/recovery.md`, never filled in.

## 6. Post-review extensions (30 Aug 2026, 04:50 PKT; team decision after reading PHASE_1_REPORT.md)

The team (the project owner) reviewed the Phase-1 report and decided: (i) **D13 revised — mechanism C (`both`)
replaces the provisional B** for Phases 2–6 (B failed E1.1's two rules; A and C passed; C keeps the hidden paths
identical to B's and closes the cross-path field inversion; REG-1's Phase-9 LLM test still decides A vs C finally);
(ii) the recovery study is extended to a decidable scale; (iii) the two "calm" references are reconciled. Designs
fixed here before any run:

**6.1 Recovery study at full scale.** Estimator C at the pre-registered **50 replications in every cell**, and the grid
extended by **h ∈ {5, 10} d** (the values estimators A and C report on the data, below the original grid) for A, B and C.
Seeds for the new cells follow the existing rule (cell index continues after h = 500, so no existing cell's seeds change;
the A/B caches at 200 replications are reused). Usability rule unchanged (median relative error < 0.20; coverage ≥ 0.90
for A, B); the ± 0.05 "undecided" band of §5 no longer applies at 50 replications. Data-side SMM interval from the
pre-registered **30 refits**. Decision rules of PREREG §4.5 re-applied to the full table; the outcome replaces
`e1_2/decision.md` and P1-9 is amended, whichever way it goes. Compute: Kaggle CPU kernels (`fp-p1-rec-*`), one per
subset of h cells, plus one for the data-side refits.

**6.2 Calm-reference reconciliation.** The audit's level-free calm R²(x) on the SEP (0.083 [0.040, 0.119]) and E1.3's
grid surrogate at the parameters in force (0.41 [0.15, 0.53]) differ by the training pool (1,600 mixed SEP paths vs 800
paths of one grid point), the "calm" definition (SEP phase groups vs E1.3's window rule) and the feature construction.
Run: the audit's `l2_surrogate` (level-free control, GBT, GroupKFold by path) on E1.3's in-force panel, and E1.3's
surrogate function on the SEP-after panel, each reported with its calm definition; the reconciliation table names
which factor carries the gap. No parameter changes; the result is handed to Phase 6 as the reference definition to fix.

**6.3 After-state under C.** `start_price_mode = "both"`; hidden paths unchanged (k_render is a render-time scale from
its own RNG stream), so E1.4, E1.5, the checklist and the day-1 states carry over; regenerated: the SEP-after panel,
the two audits (both controls), L5-after, the path hashes, the numbers file, the suite. B's after-state outputs are
kept as `*_B` files for the record; the report's after-rows are re-stated for C beside B's.

**6.2 result and consequence (30 Aug 2026; corrected 22:20 PKT after the before-audit reproduced).** The two readers
are the same estimator: on the same panel they return identical R² (E1.3's `surrogate` and the audit's `l2_surrogate`
with the level-free control: 0.0863 on the SEP-after panel, 0.155 on E1.3's panel; `e1_3/calm_reconcile.md`). So the
0.41-vs-0.08 gap was never a reader difference — it is a panel difference plus a run difference.

The run difference is real but **narrower than first stated, and its cause is not identified**:

- E1.3's in-force grid row does **not** reproduce across machines: 0.407 [0.146, 0.533] on Kaggle against 0.153
  [0.092, 0.173] locally, on a panel proven identical (same 800 paths, 95,863 calm rows, 45 features, and identical
  coverage, item-9 half-life and sd(x) to the digit — `e1_3/repro_point.md`, `sweep_kaggle.json` vs `sweep.json`).
- The SEP-before audit **does** reproduce across the same two machines: 0.385 [0.281, 0.475] on Kaggle against 0.383
  [0.278, 0.473] locally (`e1_6/audit_before_levelfree_kaggle.md` vs `audit_before_levelfree.md`).
- Tested and **refuted** as the mechanism (`e1_3/determinism_check.md`): non-determinism from OpenMP thread count and
  from `HistGradientBoostingRegressor`'s `early_stopping='auto'`. On one panel, thread counts 1 and 4 give bit-identical
  R² both with early stopping on (0.1214) and off (0.1300), so the estimator is deterministic within this environment.
- What remains: a difference between the two library environments that shows in E1.3's setting (800 paths, 45 features,
  R² near the noise floor) and not in the audit's (1,600 paths, 270 features, R² well above it). Not diagnosed here;
  recorded as an open item.

**Consequence, unchanged by the correction:** the local environment is the single reference for every surrogate-based
number; E1.3, both before-audits and the L5 before-row were regenerated on it, and the Kaggle outputs are kept as
`*_kaggle`, record-only and not compared with anything. Mechanism B's after-audits from Kaggle (`*_B`) are likewise
record-only. Phase 6 must pin the estimator's library versions in any gate definition **and** re-test this
reproducibility on the panel the gate will actually use, because the failure was regime-dependent: a single reference
row reproduced (the audit) while another did not (E1.3), so checking one is not sufficient evidence for the other.
