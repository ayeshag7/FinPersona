# Addendum to the Phase-3 pre-registration: designs corrected in documented steps

`PREREG_PHASE_3.md` was written on 2 September 2026 before any Phase-3 experiment. This file records every design
element found **wrong or undecidable after its first measurement** and corrects it in a separate step, **before**
the run it governs, with disclosure of what had already been seen — the procedure `PREREG_PHASE_1_ADDENDUM.md`
and `PREREG_PHASE_2_ADDENDUM.md` established. Where a rule changes, results are reported under **both** the
original and the corrected rule.

---

## 1. The run-up "pre-event calm" window measures a post-crash trough, and the multiplier reference is corrected to the stock's unconditional level

### What was pre-registered

PREREG §5.1: multipliers = RV(window) / RV(pre-event calm) per episode, with pre-event calm for **run-ups**
defined as "the 120 days ending at s", s being the argmin of the 504-day doubling window; and §5.3 adopting the
FIT medians of those ratios.

### What had been seen when this correction was written

The full first run of `tools/phase3/e3_3_episodes.py` under the registered definitions (`e3_3/episodes.md` as
first generated): m_deterioration 1.16 [1.12, 1.23], m_panic 5.43 [4.89, 6.00], m_stabilisation 2.39
[2.23, 2.54] (n = 1,592 episodes / 412 stocks); **m_mania 0.46 [0.44, 0.48], m_blow-off 0.70 [0.66, 0.74],
m_post-top 0.42 [0.40, 0.45]** (n = 3,125 / 394); rise time 118 d [107, 131]; decay half-life 11 d [10, 11];
stress spell 64 d; the market-window table. Nothing further.

### Why the definition as written is wrong

A run-up's start s is the **minimum** of a 504-day window: for the population that doubles, s is
disproportionately a post-crash trough (2003, 2009, 2020), where realised variance is at its episode maximum.
The "calm" reference is therefore not calm — it is the tail end of a crash — and the ratios come out **below 1**
for every run-up window, which would give the generator's mania phase *less* variance than its calm phase.
That contradicts the construct the multiplier exists to express (GSY 2019, read: volatility **rises** in
run-ups that crash) not because the data disagree but because the denominator measures the wrong thing. The
drawdown reference (120 days before a running-max peak) does not have this defect, but for consistency the
corrected reference below is computed for **all six** windows and both variants are published.

### The correction (fixed here, before the re-computation)

The multiplier reference becomes the stock's **unconditional level**: the median of its rolling 21-day RV over
the full 2000–2024 sample. m_phase = RV(window) / median(RV21, full sample), per episode; medians over episodes
with the same stock bootstrap. This is also the semantically consistent denominator for the generator: §3.4
pins the generator's free-running (calm-labelled) level to the panel's **unconditional** sd, so a multiplier
"relative to unconditional" maps onto the generator's calm phase without a hidden level shift, and the
generator-side closed-loop check (§5.3, §6) keeps its pre-event-days denominator, which for a generated path
*is* its free-running level. **Adoption (§5.3) uses the corrected reference; the pre-registered
pre-event-window ratios are published beside in the same table.** The rise time, decay half-life, stress spell
and market-window statistics are unchanged (their calm reference enters only the half-way level of the decay
statistic, which is recomputed under both references and reported; the primary decay number stays the
registered one).

---

## 2. The pooled ≥ 30 % drawdown population is dominated by slow declines, and a fast-crash subpopulation is registered as a SECONDARY comparison for E3.4

### What was pre-registered

PREREG §5.2/§6: the empirical rise time and decay half-life of the pooled ≥ 30 % drawdown population are the
95 % CIs the three mechanisms are judged against.

### What had been seen

The same first run: pooled rise time median **118 d [107, 131], IQR 39–316** — against the plan's two index
examples of ≈ 10 and ≈ 30 days, and against a generator whose scripted crash completes its deterioration and
panic inside L_det + L_panic ≤ 40 + 70 = 110 trading days by construction. PA3's incumbent pilot (rise 55 d
median at 30 seeds) had also been seen.

### Why the rule as written cannot separate the mechanisms

The qualifying population mixes two phenomena: sharp crashes (the scenario the generator's crash template
models) and multi-year secular declines, where the first −10 % day comes years before the volatility peak. The
118-day median is a statement about the population mix, not about how fast volatility rises in a crash; **no
variance mechanism can reach it inside the scripted event's own length**, so under the registered rule the rise
criterion is decided by Phase 4's schedule template, not by the variance mechanism REG-6 is asking about.

### The correction (fixed here, before any E3.4 arm is run)

The **primary rule is unchanged** (REG-6's, on the pooled population — it is reported exactly as registered,
and if no mechanism lands inside its rise CI that is the primary verdict). Added as a **registered secondary
comparison**: the same two statistics on the **fast-crash subpopulation** — episodes whose peak→trough span is
≤ 126 trading days (six months), the crash type the scenario's own template can contain (L_det + L_panic ≤ 110
trading days) — with its episode count and CIs stated, and the mechanism decision reported under **both** the
pooled and the fast-crash CIs. If the two disagree, the fast-crash verdict governs the **adoption** (it is the
population the crash scenario models) and the pooled verdict is published beside as the registered primary —
with this paragraph, written before any mechanism arm ran, as the record of why. The subpopulation threshold
(126 d) was chosen from the generator's template length, not from any panel statistic — the panel's rise/decay
numbers for the subpopulation had **not** been computed when this was fixed.

---

## 3. Both registered E3.2 adoption paths fail in measured ways, and the adoption is corrected to the primary fit's triple with recovery-informed intervals

### What was pre-registered

PREREG §4.3: adopt the mixture fit's (ν, λ, σ_J) if the recovery grid passes (median relative error ≤ 0.20 on
all three parameters over the λ > 0 cells, plus the λ = 0 null cell clean); if it fails, pin ν at E3.1's median
4.86 and fit (λ, σ_J) only, with the double-count documented.

### What had been seen when this correction was written

Everything E3.2 produced: the detection table (`e3_2/detection.md` — excess over the per-stock t-tail
**negative** at |z| ∈ [2.5, 3] and **positive from 3.5 up**, +0.00074 [+0.00066, +0.00082] at 4); the primary
fit (`fit.json`: ν 6.65 [6.48, 6.83], λ 0.00058 [0.00046, 0.00072], σ_J 0.230 [0.223, 0.241] — all interior —
at **J = 790**, with the in-window rate missed by −20 bootstrap sd); a hand grid showing every interior
alternative fits worse; the recovery grid (`recovery.json`: **ν recovers to ±2.4 %; λ ±59 %; σ_J ±28 % —
unusable under the registered rule**; the λ = 0 null cell clean in 5/5); the size-decomposition corroboration
(`size_decomposition.json`: σ_J ≈ 0.086 by moment arithmetic); and the fallback fit (`fit_fallback.json`:
**λ → 3·10⁻¹⁴, σ_J → 3·10⁻⁵, J = 1455** — a degenerate corner).

### Why the registered rules fail

The pooled exceedance curve is inconsistent with ANY single-t-plus-calendar-jump stack, for two reasons the
report's §3.2 documents: cross-sectional ν heterogeneity bends the pooled curve away from every single-ν curve
(thin middle, fat extreme), and the announcement-window elevation (0.0134 vs 0.0030 at |z| > 4) exceeds what a
total-rate-preserving split can deliver under the curve constraint. The **fallback's premise is refuted by its
own result**: pinning ν = 4.86 (the QML *total* tail) over-explains the middle tail (+29 sd at 2.5), so the
optimiser removes the jumps entirely — a conclusion that contradicts the robustly positive extreme-tail excess
(0 excluded at every θ ≥ 3.5). Adopting it would write "no jumps" into the generator because a mis-pinned
nuisance parameter absorbed them.

### The correction (fixed here, before anything is adopted or applied)

Adopt the **primary fit's own triple** — the J-optimum of the registered instrument, internally consistent and
interior — with intervals widened to carry what the recovery and the corroborations measured, and the model
rejection stated on the label:

- **ν = 6.65, interval [6.48, 6.83]** (refit CI; the recovery certifies ν to ±2.4 %). Direction stated: the
  pooled curve is heterogeneity-fattened, so the *typical* stock's diffusive tail is, if anything, thinner
  (larger ν) than 6.65; E3.1's QML median 4.86 is the **total** tail and is recorded beside.
- **λ = 0.00058, interval [0.00046, 0.00082]** — the union of the refit CI and the pre-registered excess-rate
  estimator's CI (the two agree to within a factor 1.3); the recovery's ±59 % is quoted on the label as the
  accuracy of the estimator class, and the (ν, λ) ridge is named as its cause.
- **σ_J = 0.230, interval [0.086, 0.241]** — the union of the refit CI and the moment-arithmetic size
  decomposition; **weakly identified** (a factor ≈ 2.7 across estimators; recovery ±28 %), stated wherever
  quoted. What is robust is the joint statement: *rare (≈ 0.15/year) and very large (several σ)*.

Both registered arms' complete numbers are published beside the adoption (fit.json, fit_fallback.json,
recovery.json), the corroboration table carries all three λ readings and both σ_J readings, and the report
flags the identification problem for the WRDS re-run (D1 = C): separating diffusive tails from jumps at the
single-name daily level needs the delisted tail and announcement-timestamped data this panel lacks.

---

## 4. Post-review extensions (5 September 2026)

The Phase-3 report was reviewed against the artefacts after it was written. Four of the review's findings are
experiments or registered deliverables rather than edits, and are recorded here as **post-review extensions** —
the pattern `PREREG_PHASE_2_ADDENDUM.md` §4 established. Each design is fixed here, with its rule, **before**
the run. **What had been seen when this was written**: the whole Phase-3 report, every generated file it cites,
and the review itself (which quotes the artefacts). Each is therefore explicitly a *diagnostic of a result
already published*, not a re-test of a criterion. The review's numbers were verified against the files before
this was written; one of its characterisations is corrected in §4.4.

### 4.1 The calm-trained level-free surrogate (review point 1)

**Why.** The report's header and §4 say the calm level-free channel "is gone" and that "there is nothing left
in returns and ratios for a calm-day reader to key on", citing a calm R²(x) that went from +0.34 to negative.
Two things in the phase's own files qualify that claim, both checked before this was written:

1. In the same rows of `e3_after/audit_after_levelfree_L2.csv`, **sign accuracy on resolvable steps is 0.722
   [0.702, 0.741]** (ridge; gbt 0.713, mlp 0.695) against Phase 2's 0.827 — the level-free calm reader lost the
   magnitude and **kept the direction**, and 0.722 with a CI floor of 0.702 is above the plan's own L2 sign
   threshold of 0.70. For a mandate-conformity benchmark the directional call is the one that matters.
2. `evaluation/leakage_audit.py::l2_surrogate` calls `_oos_predictions(X, y, groups, model)` on **all** rows
   (GroupKFold by path) and only then masks by phase group, so the published calm R² is a **cross-phase-trained**
   model scored against calm-only variance. A large negative value there is substantially a train/eval regime
   artefact, not a measure of what a calm-day reader can extract. §3.10 of the report states this reconciliation
   correctly (E3.8's calm-trained arms give 0.145–0.203 at the parameters in force); the header and §4 do not.

**Design (fixed here).** On the **stored** hand-over panel `e3_after/audit_after_levelfree.pkl` — no
regeneration, the same 1,600 paths — restrict to calm rows **before fitting**, then run the audit's own
machinery unchanged: the same level-free feature construction (`_prepare(..., control="level_free")`), the same
three estimators, the same GroupKFold-by-path cross-validation (held-out seeds), the same 500-resample cluster
bootstrap over paths. Report R²(x) and sign accuracy on resolvable steps for the level-free and full sets, and
the same statistics on the **Phase-2** stored panel (`e2_6_after/audit_after_levelfree.pkl`) so the before/after
comparison is like-for-like under the corrected estimator. `tools/phase3/e3_9_calm_trained.py`.

**Rule.** No pass/fail — the gate is Phase 6's. What is reported is the pair (R², sign accuracy) under both
trainings, before and after, and **whichever way it comes out, the report's header and §4 are rewritten to the
statistic the estimator actually supports**, with the sign column beside the R² column. If the calm-trained
level-free R² is materially positive, the claim "the calm price channel is closed" is **withdrawn** and
replaced by the measured statement.

### 4.2 `sbar`'s interval, a registered deliverable that was not produced (review point 2a)

**Why.** PREREG §3.4 registered: *"Interval: Monte-Carlo propagation — the 30 constrained-refit draws of
(σ_V, h) (§9), the 1,000 stock-bootstrap draws of s_A, and the 200 refit draws of (λ, σ_J) (§4), combined by
resampling; the identity's failure region (σ_V ≥ s_A) is reported if any draw enters it."* It was not produced:
`volatility.json`'s `sbar` entry carries `"interval": null`, and the report's §4 table puts **s_A's** interval in
that column. `sbar` is the block's most-used number and the only entry in the file without an uncertainty. Every
input draw is already on disk.

**Design (fixed here).** Exactly the registered propagation, no substitutions: 20,000 resamples; each draw takes
one of the 30 `bootstrap_refits` (σ_V, h) pairs from `e2_3/smm_ar1c_full_p3.json`, one s_A from a 1,000-resample
stock bootstrap of the per-stock unconditional sds in `e3_1/garch_fits.csv` (set A, full, converged — the same
bootstrap E3.1 published), and one (λ, σ_J) from the 200 refit draws in `e3_2/fit.json`; sbar is the identity
evaluated at that draw. Report the 2.5/97.5 percentiles, the share of draws entering the failure region
(σ_V ≥ s_A, or the identity's radicand ≤ 0), and state explicitly how (σ_V, h) are resampled — the refit stored
only per-parameter percentiles, not the paired draws, so the pairing available on disk is used and the
limitation is named.
`tools/phase3/e3_9_sbar_interval.py`; written into `volatility.json`'s `sbar.interval` with its provenance.

**Rule.** Descriptive. If more than 1 % of draws enter the failure region, that share is reported on the
parameter file's label rather than hidden, and the interval is reported as a truncated one.

### 4.3 The calm-window mapping, and the level double-count it also settles (review points 2b and 3)

**Why.** Two registered items converge on one measurement.

- PREREG §3.4 registered, as a labelled alternative to be **reported beside** the adopted identity: *"the
  calm-window mapping — sbar set so the generator's calm sd matches E3.3's pre-event calm daily sd (the panel's
  crisis-free reference), with its sd(x) and coverage consequences measured in the E3.4 flat arm"*. Report §3.1
  says both alternatives "are reported"; the SMM one is (§3.7's unconstrained fit), **the calm-window one does
  not exist in the report or in any generated file**. That sentence is wrong as written.
- Review point 3: the identity pins the generator's free-running (calm-labelled) return sd to the panel's
  **full-sample** unconditional sd 0.0218, which already averages the panel's own crisis days; ADDENDUM §1 then
  re-bases the multipliers to that same unconditional level. If the panel's *calm* days are quieter than its
  all-day average, the generator's calm is louder than the panel's calm **and** its with-events unconditional
  exceeds 0.0218 — a level double-count. PREREG §3.4 names this worry and assigns it to E3.4's rise/decay rule,
  which is a **shape** test and cannot detect a level error; V4 verifies the free run, not the deployed mix.

**Design (fixed here).** Three measurements, all on data already generated or cheap to generate:
(i) the panel's crisis-free calm daily sd = √(median over episodes of `rv_calm`) from `e3_3/dd_episodes.csv`
(the pre-event 120-day windows, the registered "crisis-free reference"), with a 1,000-resample bootstrap over
stocks, reported beside E3.1's 0.0218;
(ii) the **calm-window mapping's** sbar — the identity re-evaluated with s_A replaced by (i) — with the sd(x)
it implies, measured on 200 flat paths at that sbar with everything else at the block in force (seeds 212000+,
disjoint from every Phase-3 block), beside the adopted mapping's own flat-arm numbers;
(iii) the **deployed** unconditional check: the generator's realised daily return sd **with events on**, over
the scenario mix the audits use (flat / crash δ 0.70 / bull_trap / sustained_bull, 200 seeds each, seeds
213000+), pooled, against the 0.0218 target — the number V4 could not see.
`tools/phase3/e3_9_level_check.py`.

**Rule.** Descriptive; no parameter changes in this phase. If (iii) exceeds 0.0218 by more than the pooled
statistic's own bootstrap half-width, the double-count is **confirmed and reported as a defect of the level
anchoring**, with its size, on the parameter file's label and in the report's §5 for Phase 4 (which builds the
schedule on this level) — it is not repaired here, because repairing it means re-choosing the anchor and
re-running the whole execution-order cascade, which is a decision for the team with this number in hand.

### 4.4 What the jump size at the top of its interval costs (review point 5)

**Why.** The recovery gate failed (λ ±59 %, σ_J ±28 % against the registered ≤ 0.20) and the registered fallback
was degenerate, so §3 adopted the primary triple with widened intervals. That correction's outcome equals what
the passing branch would have given, so the gate was **overridden, not satisfied** — and the third option
(carry the jump block as a *sensitivity* rather than a point in force) was not weighed. That would be pedantic
if the block were inert; it is not: at σ_J = 0.230, λσ_J² is ≈ 12 % of the x-innovation variance and enters the
identity, and E3.8 attributes **+0.047** of level-free calm R² to the jump arm — the only volatility channel it
finds readable. At the interval's other end (σ_J = 0.086, the moment-arithmetic read) the jump variance is ≈ 7×
smaller and that channel should largely disappear.

**Design (fixed here).** At σ_J ∈ {0.086 (interval floor, moment arithmetic), 0.230 (adopted), 0.241 (interval
ceiling)}, holding λ and everything else at the block in force: (a) the identity's sbar and the jump share of
x-innovation variance, by arithmetic; (b) E3.8's **jump arm** re-run at each (the same 200 paths × 200 days,
same features, estimators, cross-validation and bootstrap as `e3_8_decomposition.py`), reporting level-free calm
R²(x) with its CI. `tools/phase3/e3_9_jump_sensitivity.py`.

**Rule.** Descriptive; **the adopted point does not move** (it is the registered instrument's optimum and the
block in force is frozen). What the run buys is the label: the parameter file and the report state the measured
span of the jump channel across the adopted interval, **and state which way the adopted value errs** — if the
channel is larger at 0.230 than at 0.086, then 0.230 is the *conservative* end for leakage (it overstates the
channel rather than hiding it) and the label says so, which is the one thing the current "weakly identified"
label does not say.

**A correction to the review, recorded here because it was found while checking it.** The review states that
the identity constraint left "every vAC, every long-horizon VR and every acfSMA worse". Verified against
`smm_ar1_full_p3u.json` and `smm_ar1c_full_p3.json`: the **vAC residuals improved** under the constraint
(vAC1 −6.23 → −5.76, vAC5 −5.21 → −4.77, vAC10 −5.06 → −4.61, vAC25 −4.70 → −4.24, vAC50 −4.76 → −4.37,
vAC100 −3.75 → −3.57), as did VR60 (−1.80 → −1.45). What actually paid for the volatility level is the
**long-horizon variance ratios** (VR120 −2.77 → −3.16, VR250 −2.60 → −3.38, VR500 −1.48 → −2.18) and **every
acfSMA** (−3.97 → −4.90, −2.96 → −4.25, −1.09 → −2.09), with VR20 also worse (2.85 → 3.34). The review's
substance — that ΔJ ≈ 26 for one restriction measures a real tension between the panel's volatility level and
its persistence structure inside this model class — stands; the moments that pay are the long-memory ones, not
the clustering ones.

## 5. (reserved)

Further corrections, if any, are appended here in the same form — what was pre-registered, what had been seen,
why the rule fails, the correction, and the reporting under both rules.
