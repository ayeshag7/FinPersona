# Pre-registration: Phase 6 (audits and checklist methodology — the gates, derived not stated)

**Written before any gated run.** Plan Section 10; protocol Section 1; power formulas Appendix A; the analytic
bound Appendix B; the go/no-go checkpoint 16A. Register entries in force: REG-14 (checklist criteria and the
seed/horizon policy — this phase's contest), REG-15 (data: applies to every reference distribution here), REG-11
(θ: Phase 7's; 16A is computed at θ = 0.05 with the plan's sensitivity set). Weakness items owned: 5, 7 (the
tuned-parameter ledger), 30, 31, 32, 37, 40, 61, 63, 64, 67.

The governing rule of the programme, as it reads for this phase: **no criterion is stated; every criterion is FIT
from E6.1 or DERIVED from a null or a bound, written down here in final form, and none is moved after.** A
criterion that turns out to be wrong goes in `PREREG_PHASE_6_ADDENDUM.md` with the disconfirmation stated as
loudly as any confirmation, and the result is reported under both.

Method rules Phases 4 and 5 learned the expensive way, binding here: **pin the configuration a tool measures**
(P4-19); **measure after the parameter file settles** (P4-45); **verify every cited file exists** (P4-37;
`tools/phase5/e5_cite_check.py` is run on this document); **run the whole test tree** (P4-38); **simulate every
null on the real thing** (P5-16); **a tool's "done" check tests emptiness, not presence** (P5-12); **every long
chain resumable and staged** (rule 14).

---

## 0. Team decisions in force at the time of writing

| Decision | Status | What Phase 6 does |
|---|---|---|
| **D2** L3 roster and budget | **UNDECIDED** (put to the team 8 Sep 2026: Gemini 2.5 Flash, GPT-5 mini, Claude Sonnet 5, Haiku 4.5, Opus 5; 2,000 short calls ≈ $12) | The probe is built (section 9.4) and runs when approved; nothing is spent before. |
| **D10** dividend rendering | **UNDECIDED** (Phase 5 put it to the team 6 Sep) | The audits run on the deployed default (`dividend.field = shown`); the `hidden` arm is one after-state chain (`tools/phase5/e5_after_state.py`) and is reported as an arm if the team asks. |
| **D15** sentiment default | not taken | A is deployed (the rule's selection, P5-13); B-half / B-full are switchable arms. Audits on the deployed A. |
| **D13** start price | mechanism C (`start_price_mode = both`) | In force. |
| **D14** control | A (P4-43) | In force; every audit is on the post-D14 generator. |
| **D6** calendar | "Day-N", quarter grid randomised (P4-29) | In force. |
| θ for 16A | the current 0.05 | The checkpoint row is θ = 0.05; {0.03, 0.08, 0.12, 0.20} are sensitivities; θ's derivation (E7.1, REG-11) is Phase 7's and is not pre-empted. |
| **D5**, κ = 0 | open / blocked (P4-42, P4-44) | Not touched. |
| **D17** | triggered if any of G1–G4 fails | The admissible options are laid out with consequences (section 12); none is chosen here. |

---

## 1. Inherited numbers verified before use

`tools/phase6/prereg_verify.py` reads every figure this document builds on from the file it cites
(`docs/env_v2/generated/v2_1/e6_0/verify.{json,md}`): **59 rows, 0 mismatches** after two accessor corrections
that were the tool's, not the record's (the "+0.026 the eighteen fields add" is FULL − BASE = 0.4322 − 0.4059,
not the sum of per-group add-ones, 0.0198; the onset verdict's key is `all_pass`). The rows that matter most:

| Inherited figure | Value | File |
|---|---|---|
| L2b selectivity, Phase 5 (full − price-only) | **+0.0181** (0.6762 − 0.6582; day-only 0.5080; majority 0.4144) | `e5_after/audit_after_levelfree.pkl` `L2b` |
| L2 absolute verdict, Phase 5 | calm best R²(x) −0.614, event 0.454, MAPE(V) 0.128; max selectivity R²(x) +0.0282; MAPE gain 0.0174; shuffled-V 0.0009 | same, `L2_verdict` |
| Audit population | 1,600 paths, **not subsampled** | same |
| L1: price itself | median APE 0.0626, within-5 % **0.4261** | `e5_after/audit_after_levelfree_L1.csv` |
| Calm-trained level-free R²(x), Phase 5 | **+0.2912 [+0.2637, +0.3179]** (gbt; full-field +0.3950) | `e5_after/calm_trained_phase5.json` |
| BASE\|x\|all (the box's reference row) | 0.40587 | `e5_7a/final/ablation.json` |
| FULL − BASE, all rows; VAL add-one all / calm-trained | +0.0263; +0.0090 / **+0.0509** | same |
| Column-permutation null p95 (P5-16) | ANALYST −0.0057, SENT −0.0024 (negative) | `e5_7a/baseline/ablation.json` |
| E3.8 ladder: exact Gaussian / full stack | 0.1453 [0.1076, 0.1759] vs bound 0.1633 / **0.2025 [0.1409, 0.2625]** vs bound 0.1773 | `e3_8/decomposition.json` |
| σ_V, h, h's interval | 0.014573/day; 22.381 d; [18.75, 32.64] | `envs/v2/params/value.json`, `mispricing.json` |
| sbar, GJR (α, γ, β), jump (λ, σ_J) | 0.015088; (0.027, 0.058, 0.932); (0.000583, 0.2303) | `e3_4/block.json` |
| Onset, non-price rule / rule as registered | all six transitions PASS / 9 failing (transition, field) pairs, all technicals but one | `e5_7c/final/onset.json` |
| L5 coverage flat / crash / bull / SB; ordering oracle < L5 < trivial | 0.362 / 0.543 / 0.636 / 0.354; holds in all four | `e5_l5/discrimination.json` |
| The three PROVISIONAL `audit_bounds` | 0.20; the measured onset rule; 0.10 | `envs/v2/params/observables.json` |

**Rule:** a figure that does not reproduce from its file is a discrepancy and the file's value is used.

---

## 2. What was run before this document, and why (disclosure)

Rule 11 (locate every null and bias before writing the rule that uses it) and 10.3 (criteria FIT from E6.1)
require measurement *before* registration. The following ran before this document and nothing else did. **No
gated measurement** — the final checklist at the registered n, the final audits under the derived gates, L3, 16A
— has been read.

| ran | what it is for | output |
|---|---|---|
| **E6.9** known-answer tests (30 cases, 400 reps; GARCH cases 200; JB re-check 2,000) | the estimators' correctness and their T = 200 bias; the size and power of the rejection rules | `e6_9/known_answers.{json,md}` |
| **E6.1** reference distributions (12,927 windows of 417 names; IV block 166 windows) | the criteria's reference | `e6_1/reference.json`, `e6_1/windows.csv`, `e6_1/iv_reference.{json,md}` |
| **E6.3** pilot on the stored Phase-5 panel (1,600 paths; no new generator run) | cross-seed variance → n per item | `e6_3/power_v2.{json,md}` |
| **E6.2** the three criteria on the stored panel, and B's and C's size and power on known-answer panels | the criteria's known answers; the concordance table | `e6_2/criteria.{json,md}`; `evaluation/params/phase6_criteria.json` |
| **E6.6** the bound at the adopted parameters, the sweep check, the calm-channel ladder (rungs 5 and 6 re-simulate 200 flat paths each — **a generator run, diagnostic, to locate the nonlinear allowance**) | G4's second clause | `e6_6/bound.{json,md}` |
| **E6.5** the floor derivation, on the stored L1 tables and the extended set re-run on the final panel | the L1 rule | `e6_5/floor.{json,md}`, `e5_7b/final/l1ext.json` |
| **E6.6 / E6.7** the target-permutation nulls on the stored panel with the real estimator at n = 1,600 | the L2 and L2b margins | `e6_6/null/null.{json,md}` (**running as this is written**; the location cells below are filled from the file before any gated run and the fill is dated) |

---

## 3. E6.1 — the reference distributions (done)

**Population.** Every non-overlapping 200-day window (T = 200 returns) of every name in analysis set A (417
names with a complete 2000-01-03..2024-12-31 history; `tools/phase1/panel.py`'s exclusion rule): **12,927
windows, 31 per name, 0 errors**; sub-periods 2000-07 (4,170), 2008-12 (2,502), 2013-19 (3,753), 2020-24
(2,502) by the window's midpoint. Every statistic is computed by **the audit's own functions**
(`evaluation.stylized_facts`, imported), so that a generator window and a real window go through one estimator.
The IV block pairs the VIX with the Fama–French value-weighted market (33 windows, 1990–), with the S&P 500
(FRED, 12 windows, 2016–) and with a set-A equal-weight proxy (31), and the five CBOE single-stock VIX indices
with their own stocks (90 windows, 2011–).

**Survivorship, stated per item (REG-15).** Set A is survivor-biased by construction (a complete 2000–2024
history in a `yfinance` panel). The tails, the drawdowns and the loss frequencies are **understated**: the bias
bites hardest on items 2 (kurtosis, Hill), 8 and 20 (MDD, the worst day) and least on items 1, 3, 5, 6, 7 (the
ordinary dynamics). A generator crash deeper than the reference's P10 is not thereby unrealistic; the report
carries the literature's full-universe values beside those rows (REG-15's table). The five single-stock IV
series are five surviving mega-caps chosen by the CBOE; the FF market series carries no survivorship.

**What the reference already says** (`e6_1/reference.json`, scope `all`, n = 12,927): kurtosis P10/P50/P90 =
0.47 / **2.17** / 10.7 (so "> 1.5" holds in ≈ 60 % of real windows, not ≥ 80 %); ACF\|r\|(1) = −0.03 / **0.087** /
0.23 (the v2 band 0.10–0.40 excludes the real median); LB\|r\| p = 0.000 / 0.18 / 0.84; Hill 2.31 / 3.56 / 5.57;
GARCH α+β 0.29 / 0.93 / 1.00; leverage corr −0.15 / −0.038 / +0.07; Spearman(volume, \|r\|) 0.19 / 0.33 / 0.46;
log-volume AC(1) 0.37 / 0.51 / 0.64; Shapiro p on log volume 0.000 / **0.0037** / 0.42 (log-normality is
rejected at 1 % in most real windows); skew −1.04 / −0.07 / +0.75; MDD −0.44 / −0.20 / −0.10 (crash windows,
MDD ≤ −0.20, n = 6,275: −0.54 / −0.31 / −0.22); daily σ 1.08 % / 1.75 % / 3.41 %. Sub-period medians move
little except 2008-12 (persistence 0.97, LB\|r\| p 0.04).

---

## 4. E6.9 — what the known-answer tests found, and how the criteria absorb it

`e6_9/known_answers.md`. Every estimator is consistent where it should be (the Pareto control for Hill, AR(1)
for the ACF, deterministic MDD, GARCH/GJR coefficients at the long horizon, the sizes of LB, ARCH-LM, Shapiro
and JB at nominal — JB's first 400-rep run read 0.0725 [0.051, 0.102] at T = 20,000; the 2,000-rep re-check
reads 0.057 [0.048, 0.068] and 0.0495 at T = 200: a draw). Three failures, each a property of the estimator at
the audit's tuning, and five power rows, decide how the criteria must be written:

| finding | number (T = 200 unless stated) | consequence |
|---|---|---|
| the sample ACF(1) of an AR(1) at the engine's FIT half-life is biased down | median 0.9468 [P10 0.906, P90 0.968] for φ = 0.9695; the implied half-life **12.7 d** for a true 22.4 d; sd(x) at 82 % of stationary | item 9's "ACF(1) ≥ 0.98 / half-life ≥ 60 d" cannot be met by the FIT process on a 200-day window; the criterion is re-stated against E6.9's own T = 200 reference (section 5) |
| the sample kurtosis of a heavy tail has no usable finite-sample distribution | Student-t(5): median 1.77 [0.58, 6.00] for a true 6.0; at T = 20,000 still 5.07 ± 3.0 | item 2's "kurtosis > 1.5 in ≥ 80 %" is stated in units the estimator does not deliver; the like-for-like criteria (B, C) carry the same bias on both sides |
| the Hill index at a 5 % depth misses a Student-t index | 3.19 for a true 4.0 (Pareto control 3.00); closes to 3.91 only at a 0.1 % depth | same: an absolute Hill band is mis-specified; the like-for-like form is immune |
| **the power of item 3's rules against the generator's own fitted GJR shape** | ARCH-LM(5) rejects at 1 % in **23.3 %** [19.4, 27.6] of 200-day windows; LB\|r\| in **27.5 %** [23.4, 32.1]; the same shape's ACF\|r\|(1) median **0.057** [−0.03, 0.19] (0.158 at T = 20,000) | "p < 0.01 in ≥ 80 % of seeds" and "ACF\|r\|(1) in 0.10–0.40" ask the generator to show what its true process cannot at T = 200; the reference (real windows: LB\|r\| rejects in well under half; median ACF\|r\|(1) 0.087) says the same of real stocks |
| LB(10) on returns at the edge of item 1's own ACF band | power 0.27 at φ = 0.15 | item 1's two halves have unequal power; reported, not gated |
| a symmetric GARCH fit on the GJR shape in force | T = 200 median α+β 0.966, **P10 0.72, P90 0.999** | item 5's cross-seed sd of 0.21 (E6.3) is the estimator's on the true process; the band [0.90, 0.995] is decidable only at n ≈ 750 |

---

## 5. E6.2 — the criteria, in final form

### 5.1 The three forms (REG-14), as applied

- **A (v2)**: `evaluation.stylized_facts`' pass rules, unchanged, reported for continuity.
- **B (KS-equivalence)**: the bootstrap (500 resamples of both samples) 95 % upper limit of the two-sample KS
  distance between the generator's cross-seed distribution of the statistic and the reference distribution is
  **< D0 = 0.10**. "The KS test did not reject" is not a criterion.
- **C (band share)**: the generator's share inside the reference **P10–P90** is **≥ 0.80 − 1.96 √(0.8·0.2 / n_gen)**.

Per item the statistics, the generator population and the reference are fixed in `phase6_criteria.json`
(`items`): items 1–7 on every path against every window; item 8 and item 20's MDD and worst day on the **crash**
paths against the **crash windows** (a real window contains a crash when its MDD ≤ −0.20 — a DESIGN definition,
recorded in the file as such); item 20's calm σ on the flat paths against every window. Items 9, 11, 12, 13, 15,
17 have no real-window counterpart and are handled in section 5.4. Item 4 is descriptive (the plan's own rule).

### 5.2 The criteria's known answers (REG-14 (i)) — what B and C can and cannot decide

`e6_2/criteria.md`, "Size and power": the generator sample replaced by a draw from the reference (true D = 0)
and by the reference shifted to a true KS distance of 0.05 and 0.10, 100 simulations each.

- **B at n_gen = 200 has no size**: it passes a sample drawn from the reference itself in only **2–8 %** of
  simulations, because the KS distance's own sampling noise at n = 200 carries its upper limit past 0.10. At
  n_gen = 800 it passes 99–100 % at D = 0 and rejects a true D = 0.10 in 99–100 %; at D = 0.05 it passes
  60–100 % (statistic-dependent). The n = 500 row is being measured as this is written (`e6_2/run2.log`) and
  is entered here before the final checklist runs. **B is the decisive criterion, and it is decisive only at n
  ≥ the count that gives it size.**
- **C has size at every n** (pass rate 0.93–1.00 at D = 0) **but no power against a location shift of D = 0.10
  on most statistics** (pass rate still 0.96–1.00): a shift that moves the KS distance by 0.10 barely moves the
  P10–P90 share. It has power only where the band is narrow relative to the shift (MDD 0.22 → 0.00, the worst
  day 0.41 → 0.00, skew 0.87 → 0.55, leverage 0.81 → 0.78). **C is the band report, not the decision.**

### 5.3 The seed policy, derived

- **The final checklist runs at n = 500 seeds per scenario** (the SCL design, T = 200; 2,000 pooled). The pooled
  population decides B at full size and power; the per-scenario populations decide B at n = 500 **if** the n =
  500 size row passes ≥ 0.90 at D = 0 (entered below), and are otherwise reported under C with B's verdict marked
  *undecidable at this n*. This is REG-14's "the maximum required by the power rule across the criteria used";
  Appendix A's own reading ("with n_gen = 500 the KS sd is ≈ 0.02–0.03") is what the row tests.
- Appendix A's per-item precision table (`e6_3/power_v2.md`, 1,600-path pilot, planned n = 200): every v2
  item's verdict is decidable at 200 except items 5 (persistence: cross-seed sd 0.21, needs ≈ 750 for the
  band's w/5 precision), 3's ACF\|r\|(1) (median 0.091 sits 0.009 from the band edge) and 8's skew (median
  +0.04 against a one-sided 0 with sd 0.74). At n = 500 the first is decidable by the verdict rule (half-width
  0.023 vs 0.020 to the edge — marginal, and stated), the other two remain edge cases and are reported as such.
- **T ∈ {800, 2000} at 100 seeds, flat, for items 4 and 9 only, descriptive** — never as the pass criterion for a
  T = 200 property.
- **The audits**: the SEP design at 200 seeds = **1,600 paths, no subsampling** (the nulls are simulated at this
  n). **16A**: 100 scored seeds per scenario on training-disjoint seeds (section 12).

> **Cell to fill from `e6_2/criteria.json` before the final checklist runs:** B's pass rate at D = 0 for n_gen =
> 500, per statistic — *pending; run2 in progress.* If it is ≥ 0.90 for a statistic, B decides that statistic
> per scenario at 500; otherwise the per-scenario B verdict is "undecidable at n = 500" and only the pooled B decides.

### 5.4 The items without a real counterpart

- **Item 9 (persistence)**: the criterion is *fidelity to the FIT process measured with the same ruler*: on the
  flat paths (whole path calm), the cross-seed median of the 200-day sample ACF(1) of x lies inside the
  **[P10, P90] of E6.9's AR(1) reference at the FIT half-life, 0.906–0.968** (`acf_ar1_engine_persistence_lag1`,
  T = 200, 400 reps), and the median 200-day sd(x) inside the AR(1) reference's [P10, P90] scaled by s_x
  (0.0656 × [2.42, 4.50]/4.07 = **[0.039, 0.073]**). The v2 band (≥ 0.98; 60 d; 0.08–0.20) is reported beside
  it as A; it is contradicted by the engine's own FIT h and by E6.9, and is expected to fail under A.
- **Item 12 (sentiment, E6.8)**: the never-implemented clause "lagged correlation = configured b_pred" is
  implemented as: the OLS coefficient of r_t on the standardised s_{t−1} on calm rows, cluster-bootstrap 95 %
  interval over paths, **contains the configured b_pred** (0.0008, LIT — the test is fidelity to the configured
  value, since Phase 5 found the free source does not reproduce Tetlock's 8.1 bp). The ACF(1) and
  contemporaneous-corr bands of v2 were written for the v2 field and are reported as A only; B/C are not
  applicable (no real single-stock sentiment counterpart in the panel).
- **Item 13 (IV)**: the reference is `e6_1/iv_reference.md`. The like-for-like statistics are the window mean
  IV, IV − RV20 and corr(IV, next-20-day RV). The generator's single stock is judged under **C against the pooled
  single-stock windows** (n = 90): mean IV P10–P90 [21.6, 37.6]; IV − RV20 [+0.3, +7.4]; corr [0.27, 0.75]. The
  never-implemented "non-degenerate across seeds" clause (E6.8): the cross-seed sd of the calm IV mean has a
  bootstrap CI excluding zero. Expected: the corr criterion fails — the generator's IV is a **past-only filter**
  (E3.5, by design, to close the look-ahead) and the pilot reads corr 0.23 against the real 0.55; reported as a
  structural cause, not repaired.
- **Items 11, 15, 17**: generator-defined (P/V shape, phase labels, the sampler); A as stated, reported.

### 5.5 Reporting rules

Results under **all three** forms, on the pooled population and per scenario and on flat only (E6.4), with the
regime-switching contribution quantified as the pooled-minus-flat share; where A and B/C agree the item is
reported once, where they disagree under both with the reading (the concordance table in `e6_2/criteria.md`
is the template). The tuned-parameter ledger (weakness 7) lists items 9, 10, 11, 13, 17, 20 and amendments A1,
A2, A6, A7 with the parameters tuned against them and the pre-amendment results beside the amended ones.

---

## 6. E6.5 — the L1 rule, derived (done)

`e6_5/floor.md`. A candidate carrying nothing about x beyond the price path is V̂ = P e^{−x̂}; its within-τ share is
bounded by **2 Φ(τ / (s_x √(1 − B))) − 1**, with s_x = 0.0656 (the volatility identity with the jumps) and B the
Appendix-B day-200 bound 0.2005: **0.135 / 0.267 / 0.606 at τ = 1 / 2 / 5 %**. The trivial line (x̂ = 0, price
itself) is 0.121 / 0.240 / 0.554 analytic and **0.095 / 0.190 / 0.426** as the generator realises it (its x is
wider-tailed than Gaussian). **Rule:** no candidate's within-5 % share may exceed **0.606 + 0.011 (the share's
cluster-bootstrap half-width at 1,600 paths) = 0.617**. Measured on the final panel: price itself 0.426; the
best of the 27 extended candidates (`e5_7b/final/l1ext.json`) is `lsq(price+F)` at 0.399 — none exceeds price
itself, none approaches the ceiling. **Expected: PASS.** The 1 % hard-coded floor (`NOISE_FLOOR`) stays in the
code behind the `gates="v2"` switch and is reported beside.

---

## 7. E6.6 — the L2 gate

### 7.1 The bound (done; `e6_6/bound.md`)

At the parameters in force (σ_V = 0.014573, h = 22.38 d, s_x = **0.0656** derived from sbar, λ, σ_J — no file
stores a stationary sd(x); the generator's realised flat-path sd is 0.0640, the identity and the realised agree
to 0.002): the level-free ceiling is **0.1773 (window average) / 0.2005 (day 200 = steady state)**. Over h's
interval: 0.130–0.225. **The sweep check passes at 40 of 40 points** (no surrogate CI lower end above either
bound). The window average is the statistic that matches a surrogate scored on every row of a 200-day path
(a reader at day t has t days of history); the day-200 value is reported beside it.

### 7.2 The nonlinear allowance and the ladder (done; rungs 5–6 re-simulated)

| rung | arm | n | level-free R²(x) [CI] | bound | increment |
|---|---|---|---|---|---|
| 1 | exact Gaussian process (the bound's model) | 200 | 0.1453 [0.108, 0.176] | 0.1633 | — |
| 4 | + GJR-t + jumps (the innovation in force) | 200 | 0.2025 [0.141, 0.263] | 0.1773 | +0.0572 over rung 1 |
| 5 | generator flat, feedback OFF | 200 | 0.2204 [0.160, 0.280] | 0.1714 | +0.0179 |
| 6 | generator flat, as deployed | 200 | 0.2217 [0.161, 0.281] | 0.1716 | **+0.0014** (the feedback) |
| 7 | generator, every calm row of the SEP panel | 1,600 | **0.2912 [0.264, 0.318]** | 0.1695 | **+0.0694** (the events' pre-event calm) |

**The allowance** ("measured on a Gaussian control run", Appendix B) is rung 4 − rung 1 = **+0.0572**: the
increment the non-Gaussian innovation adds to the same estimator on the same design. It is the number E3.8 wrote
to disk before this phase; the alternative reading (rung 6 − its bound, +0.050) includes the process-to-generator
step and is not used.

### 7.3 G4's second clause, as it will be read

**Rule.** The level-free surrogate's calm R²(x) on the audit's population (the SEP panel's calm rows, the
calm-trained e3_9 estimator, best of ridge/gbt/mlp, 500-resample cluster bootstrap) is at or below **bound
(window average, at the population's realised s_x) + allowance** *within its CI*, i.e. **the CI's lower end ≤
0.1695 + 0.0572 = 0.2267**.

**Expected outcome, stated now:** **FAIL** — the Phase-5 value is 0.2912 with lower end 0.2637. Under any of the
readings not adopted (day-200 bound 0.1913 + 0.0572 = 0.2485; h at its short end, 0.2151 + 0.0572 = 0.2723) the
lower end still clears the ceiling, so the choice of reading does not decide the verdict. The ladder locates
the excess: **not the fields** (they are outside a level-free reader by construction), **not the feedback**
(+0.0014), but **the events' pre-event calm** (+0.069) — the flat scenario alone (rung 6, lower end 0.161)
passes. This is the finding Phase 4 reported as "the event redesign did not narrow the calm level-free channel"
(P4's SEP audit), now attributed and bounded. It is D5's territory and is laid out for D17 (section 12).

### 7.4 The selectivity gate

**Statistic.** Selectivity = R²(x) of the FULL set (the level-free control + every rendered field) − R²(x) of
the level-free control (BASE), the audit's GBT estimator (`leakage_audit._models()["gbt"]`, 5-fold GroupKFold
by path), on two populations: all rows and calm-trained. Measured on the Phase-5 state: **+0.0263** (all rows)
and **+0.104** (calm-trained: 0.3950 − 0.2912), paired cluster-bootstrap half-widths from `e5_7a/final`.

**Null.** Each path's x series is swapped whole with another path's (the audit's shuffled-V construction),
BOTH feature sets are refitted, 20 draws (`e6_6/null/null.json`, seed 660001). **Rule (the plan's letter):**
selectivity ≤ **null p95 + the sampling half-width**. The null's location is read before this rule is final and
is reported whatever it is (P5-16): the first FULL draws under permutation read R² −0.043 to −0.052 (a random
target is fitted worse by more columns), so the selectivity null is expected to sit **below zero**, and its p95
near zero; a margin built from it will be close to the half-width alone. **Registered sensitivity:** the centred
margin (p95 − null median) + half-width, P5-16's repair, reported beside — not a substitute.

> **Cells to fill from `e6_6/null/null.json` before the final audit runs:** null median, p95 (20 draws; the
> resolution note applies), the derived margin, and the verdict for all rows and calm — *pending; the L2 null is
> running (80 fits; FULL ≈ 345 s each on the laptop).* The expected verdicts, stated now: all rows FAIL if the
> p95 is ≤ +0.015 (the measured +0.026 minus the half-width); calm-trained FAIL under any plausible null.

**Held-out-scenario split (weakness 67).** Train on three scenarios, score the fourth, level-free and full,
every scenario held out once; reported with intervals; no gate (the selectivity gate above is the gate).

**MAPE(V)** reported with intervals as today; no absolute threshold.

### 7.5 The known-defect registry

`test_v2_L2_surrogate_thresholds` is re-expressed as `test_l2_gate_derived` (the gate's margin equals the stored
null percentile plus the stored half-width; the verdict is asserted **as the file holds it**, pass or fail). A
failing derived gate is a strict xfail whose reason names the derived gate and Phase 7/D17 as the owner — the
registry ends the phase either empty or with such entries, never with a "chosen" margin.

---

## 8. E6.7 — the L2b gate and L2c

### 8.1 L2b

**Statistic.** The macro-class accuracy of the FULL set minus the level-free control's (the audit's
`HistGradientBoostingClassifier` 200/0.1/4, 5-fold GroupKFold by path), 288,000 rows, 1,600 paths. Measured on
the Phase-5 state: **+0.0181** (67.62 % − 65.82 %).

**Null.** Each path's macro-label vector is swapped whole with another path's, both feature sets refitted, 20
draws (the same tool and seed). **Rule:** selectivity ≤ null p95 + the paired sampling half-width. The 10 pp
margin (frozen after the result was known, weakness 32) is retired to the `gates="v2"` switch and reported beside.

> **Cells to fill from `e6_6/null/null.json` before the final audit:** null median, p95, the margin, the verdict
> — *pending; the L2b null is running (42 fits).* Expected: the null sits near zero with a p95 of a few tenths
> of a percentage point; whether +1.8 pp clears "p95 + half-width" is open, and the verdict is reported as it falls.

### 8.2 L2c = the onset audit

The addendum §1.3 rule: for every non-price field and all six transitions, ΔAUC_f ≤ the 95th percentile of 500
per-path circular shifts, the reference being the best AUC over the five registered scores and every
price-derived field's score; 200 crash + 200 bull-trap seeds. The Phase-5 final state's run
(`e5_7c/final/onset.json`: PASS at all six) **is** the final state's L2c, since nothing in Phase 6 changes the
generator; the path-hash fixture (`path_hashes_phase5_after.json`, re-checked at the end of the phase) is what
proves the state unchanged. Both verdicts (as registered in Phase 5; non-price) stay in the table.

---

## 9. The L3 LLM probe (built now, run after D2)

**Design.** 200 probes stratified by scenario (4) × macro phase (calm / event / resolution) × seed; each probe is
one rendered day (the same observation the harness renders, mechanism C) with the question "Is this stock
currently over-valued, under-valued or fairly valued relative to its fundamental value?" scored against
sign(x) on resolvable steps (\|x\| ≥ θ = 0.05). Two arms per probe: **normal** and **shuffled-V** (the fields of
another path's day at the same step — the audit's construction — so the answer's link to this path's x is
broken). ≥ 5 models (the D2 roster). **Statistic:** each model's sign accuracy with a Wilson 95 % interval, both
arms. **Rule:** a model's normal-arm accuracy may not exceed **the level-free surrogate's sign accuracy on the
same 200 probes** (the reader the price path entitles, from the after-state audit's `sign_acc_resolvable`,
level-free, calm-trained 0.765 [0.749, 0.779] on the calm population) **+ the Wilson half-width at n = 200**; the
shuffled-V arm must sit at chance within its interval. Cost ≈ $12 at the plan's roster; **nothing runs before D2.**

---

## 10. The switches in `evaluation/` (every change inert when off)

| switch | default (= today's behaviour) | on |
|---|---|---|
| `leakage_audit.run_audit(..., gates="v2")` | the v2 verdicts, bit-identical | `"derived"`: reads `evaluation.criteria` and adds `L2_verdict_derived`, `L2b["pass_derived"]`, the L1 derived rule |
| `leakage_audit.run_audit(..., holdout_scenario=False)` | no split | the held-out-scenario table added |
| `stylized_facts.run_checklist_reference(paths_all, doc)` | a new function; `run_checklist` untouched | the B/C/A table per item and population |
| `observables_params.AUDIT_BOUNDS` | the three PROVISIONAL values | pointed at the derived gates in `phase6_criteria.json` (a documented `envs/v2` change; the entry names Phase 6) |

**Proof of inertness:** `tests/test_leakage_ci.py`'s fixture and its published-value comparisons pass unchanged
under the defaults; `run_audit` on the 8-seed CI panel with `gates="v2"` is compared field by field with the
stored result (`test_audit_switches_inert`); `run_checklist` on the CI paths is bit-identical.

---

## 11. Tests (Section 10.4) — written before the final runs

`tests/test_v2_1_phase_6.py`: `test_checklist_criteria_from_reference` (every reference row in the criteria file
carries n > 0 and its P10 ≤ P50 ≤ P90; D0, p0 and the crash rule as registered), `test_footer_counts`
(`e6_after_checklist.md`'s footer equals its csv), `test_audit_known_answers` (E6.9's convergence verdicts re-read;
the Pareto control within 4 MCSE; the Hill and kurtosis findings recorded, not silenced), `test_no_subsampling_in_published_audit`
(every published audit pickle has `subsampled == False` and `n_paths == 1600`), `test_l2_gate_derived` (each
derived gate's margin equals the stored null p95 + half-width and the verdict is the stored one),
`test_phase6_report_tables_match_files` (every marked block in the report regenerates from its file),
`test_audit_switches_inert`, `test_known_defect_registry_matches_strict_xfails` (existing, re-run).

---

## 12. 16A — computed exactly as written, last

On the frozen generator, θ = 0.05 (the checkpoint) and {0.03, 0.08, 0.12, 0.20} (sensitivities); **100 scored
seeds per scenario**, 40 training seeds, disjoint; cluster-bootstrap 95 % intervals over paths; the policies as
16A lists them: the mandate-conditional true-V oracle; the **level-free observables oracle** (current-day fields
plus a 20-day history, no level features; `tools/phase5/e5_l5.py`'s n/m-aware subclass); the **best simple
level-free rule** from the pre-registered family {price vs SMA50 threshold, RSI14 threshold, analyst-vs-price
threshold}, each with its scale fitted on the training seeds; the trivial policies {always-hold at centre,
constant band edges, random}. Metric: MCR (mandate-conformity regret), per persona × scenario.

- **G1**: MCR(oracle) < MCR(observables oracle) < MCR(best trivial) with non-overlapping intervals between
  adjacent pairs, every scenario. Phase 5's discrimination table has this shape in all four with both gaps' CIs
  above zero (section 1); expected PASS.
- **G2**: the best simple rule's MCR above the observables oracle's, non-overlapping, in ≥ 3 of 4 scenarios.
  Not previously measured; no expectation stated.
- **G3**: the median number of oracle target switches per run ≥ 2 in the three event scenarios and the share
  of runs with ≥ 2 switches ≥ 0.5. **Expected FAIL** at the FIT persistence (the plan's own reading: medians
  0 / 0–1 / 1 / 2); a shorter half-life is not admissible. D17's options are laid out with consequences: (i) a
  longer horizon reported as a factor (T = 400 / 800 with the persistence unchanged — G3 re-computed at each),
  (ii) per-window scoring, (iii) restricting the paper's claim to a one-shot mandate-conflict benchmark. None is
  chosen here.
- **G4**: (a) the level-free observables oracle beats the level-free price-only oracle with non-overlapping
  intervals in every scenario; (b) section 7.3's rule. **(b) expected FAIL** (section 7.3); (a) not previously
  measured.

Every G is reported under the criterion as written; the phase stops for the team after the table.

---

## 13. Compute plan and order (rule 14: every chain resumable, staged, in the background)

1. E6.9, E6.1, E6.3 pilot, E6.2, E6.6 bound/sweep/ladder, E6.5 — **done** (laptop).
2. The nulls — running (laptop; the L2 null's 80 fits ≈ 2.5 h; L2b's 42 ≈ 1 h). The lab box (128 cores,
   `docs/COMPUTE_GPU_ACCESS.md`) takes them in minutes **once** its reproduction check passes (the BASE\|x\|all
   row 0.40587 and `test_smm_reference_row`); the code reaches it only by a pull path that needs a credential on
   the box (the user's call each time); until then every fitted number is the laptop's.
3. The switches and the tests; `phase6_criteria.json`'s `gates` block written from `null.json`; the cells above
   filled and dated.
4. The final checklist at 500 seeds per scenario (SCL), T = 200; T ∈ {800, 2000} at 100 flat seeds for items 4
   and 9 (descriptive); the after-state chain re-run with `gates="derived"` on the 1,600-path panel; the held-out
   split; L5/16A at 100 scored seeds; L3 when D2 lands.
5. The report, the tuned-parameter ledger, CALIBRATION_REPORT rewritten as the E6 appendix, the registry
   re-expressed, the re-freeze and the path hashes, `PHASE_6_CHANGED_FILES.md`, DECISION_LOG P6-*.

---

## 14. What this document leaves pending, and the rule for filling it

Three cells are filled **from files, before any gated run, with the date of the fill**: the n = 500 size row
(5.3), the L2 null's location and margin (7.4), the L2b null's location and margin (8.1). No other number in
this document changes. If a filled cell makes a registered rule undecidable (a null p95 whose 20-draw resolution
straddles the measured statistic), the verdict is reported as *undecided* and the draw count is raised in an
addendum — not the rule.
