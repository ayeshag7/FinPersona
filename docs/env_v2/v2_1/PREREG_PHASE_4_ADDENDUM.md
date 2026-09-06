# Pre-registration addendum, Phase 4

Corrections to `PREREG_PHASE_4.md` made **after** data were seen and **before** the runs they govern, each with
a disclosure of exactly what had been seen at the time of writing, following the pattern of
`PREREG_PHASE_3_ADDENDUM.md`. Every affected result is reported under **both** the original and the corrected
rule.

---

## 1. E4.0b's adoption rule was built on a hypothesis the measurement refuted

### 1.1 What was registered

`PREREG_PHASE_4.md` section 2 registered a specific reading of Phase 3's confirmed level defect:

> `GJRParams.phase_mult` returns `self.mult.get(phase, 1.0)`, so the six event phases carry FIT multipliers and
> **calm falls through to a stipulated `1.0`** [...] each event phase lands at its correct absolute variance;
> calm is the only phase whose level is not measured.

and made clause 1 of the adoption rule conditional on that reading: the fitted calm multiplier is adopted only
if **1.0 lies outside its 95 % CI**.

### 1.2 What was seen before this correction was written

Full disclosure. At the moment of writing this section I had seen, and only seen, the following — all of it in
`docs/env_v2/generated/v2_1/e4_0/level.json` and `level.log`:

| Quantity | Value |
|---|---|
| Fitted calm multiplier, median-referenced family (E4.0a ii) | **1.0102 [0.9791, 1.0561]**, n = 1592 episodes / 412 stocks |
| Generator flat-arm pooled sd vs panel calm (E4.0a i) | 0.02309 [0.0219, 0.0245] vs 0.01703 [0.0163, 0.0176], ratio **1.356**, CIs **disjoint** |
| Deployed pooled sd, equal scenario weights (E4.0a iii) | 0.02737, **+25.6 %** over the 0.02179 target |
| Deployed pooled sd, panel phase weights (E4.0a iii) | 0.02513, **+15.3 %** over target |
| Counterfactual with `mult["calm"] = 1.0102` (E4.0a iv) | equal-mix 0.02809, **+28.9 %** — essentially unchanged, as a multiplier of 1.01 must be |
| The follow-up discriminating check (below) | per-stock ratio of mean-based sd to median-based sd = **1.354 [IQR 1.286, 1.452]**, n = 417 |

I had **not** run any E4.1, E4.2 or later experiment, and no threshold in sections 3–10 of the pre-registration
is touched by this correction.

### 1.3 The result under the rule as registered

**Clause 1 fails.** The calm defect is confirmed like-for-like (the generator's calm and the panel's calm have
disjoint CIs at a ratio of 1.356), but `1.0` lies **inside** the fitted multiplier's CI [0.9791, 1.0561]. The
stipulated `1.0` is **not refuted**. Under `PREREG_PHASE_4.md` section 2 E4.0b, **route (a) stands**: the level
as handed over, with every Phase-4 number flagged that would move under (b) or (c).

That verdict is recorded and stands as the registered outcome. What follows does not overturn it; it explains
why the registered hypothesis was the wrong one and registers the corrected test.

### 1.4 Why the hypothesis was wrong, and what the defect actually is

The registered reading assumed the six event multipliers and the variance identity's anchor refer to the
**same** unconditional quantity. They do not.

- The **anchor** is `s_A = 0.021793`, E3.1's full-sample daily return sd — a **mean**-based statistic
  (per-stock `sqrt(mean r²)`; median over the 417 names = 0.021847, agreeing to 0.2 %).
- The **six multipliers' reference** is `rv_uncond`, the per-stock **median** of rolling-21-day realised
  variance (`tools/phase3/e3_3_episodes.py`: `rv_uncond = float(np.nanmedian(rv21))`, ADDENDUM section 1's
  "corrected reference"). Its square root over the panel is **0.015697–0.016213**.

Realised variance is strongly right-skewed, so its mean exceeds its median. The per-stock ratio of the two
references is **1.354 [IQR 1.286, 1.452]** (n = 417) — and that is, to three digits, the same 1.356 by which
the generator's calm exceeds the panel's calm.

So the defect is a **reference-estimator mismatch**, not an unmeasured calm phase: median-referenced ratios are
applied on top of a mean-anchored base, and **every** phase — calm included — is inflated by the mean/median
RV ratio. Calm's `1.0` is correct *within its own family* (measured: 1.0102), which is precisely why clause 1
could not detect the problem.

**A correction to the Phase-3 report follows from this and is published in `PHASE_4_REPORT.md`.**
`PHASE_3_REPORT.md` section 3.11c and `e3_9/level_check.json` describe 0.01703 as "the panel's **crisis-free
calm**" and read the 1.28 gap as calm-versus-all-day. It is not: 0.01703 is the panel's **median-RV level**,
and the calm windows match it because calm windows *are* typical days. The gap between it and `s_A` is
mean-versus-median, not calm-versus-crisis. Phase 3's *finding* (the deployed generator runs hot, and the
anchor is the cause) stands and is confirmed here; its *mechanism* is corrected.

### 1.5 The corrected rule (E4.0c), registered before the run it governs

**Statistic.** All seven phase multipliers re-measured against the **same** reference the anchor uses: for each
episode, `m_phase = rv_phase / s_A_stock²` where `s_A_stock² = mean r²` over that stock's full sample; median
over episodes with a 1,000-resample **stock** bootstrap; n reported as (episodes, stocks).

**Why this and not a rescale of `sbar`.** Both routes remove the same 1.354. Re-basing the multipliers leaves
`sbar`, the variance identity and the engine identification (σ_V, h, sd(x)) untouched, so it costs one panel
recomputation plus the closed-loop re-calibration Phase 4 owes anyway once the schedule changes; re-anchoring
`sbar` (Phase 3's option (b)) re-identifies the engine and Phase 3 measured that it roughly halves sd(x)
(flat median sd(x) 0.0468 → 0.0214) and undoes the coverage gain. Both are run and both are reported; only the
adoption rule differs.

**Adoption rule.** The re-based multipliers are adopted iff **both**:

1. the **phase ratios are preserved** — for every pair of phases, the ratio of the re-based multipliers equals
   the ratio of the median-referenced ones to within the bootstrap CI (this is an internal-consistency check:
   re-basing is a change of normalisation and must not move a ratio); **and**
2. after **one** closed-loop re-calibration, the deployed pooled sd under **panel phase weights** lies within
   the bootstrap half-width of `s_A = 0.021793`.

Clause 2 is stated on the **panel-weighted** mix, not the equal-weight mix, because E4.0a(iii) measured that
about 10 pp of Phase 3's +30.5 % is a scenario-mix artefact of weighting the four scenarios equally — a
weighting no real all-day panel has. The equal-weight figure is reported beside it.

**If either clause fails**, the phase reports the measured cost and **stops for the team**: which reference the
environment's level should use is a decision about what the environment is for. Phase 4 does not choose it.

**What is reported either way**: flat sd(x) and the four scenarios' coverage before and after, under both
routes, because a lower calm variance lowers sd(x) and therefore coverage, and E4.5's control redesign has to
absorb it.

### 1.6 A sampling fact recorded here because it affects every level statement

The flat arm's pooled sd is **0.02309 [0.0219, 0.0245]** on seeds 214000+ and **0.02150 [0.0209, 0.0222]** on
seeds 213000+ (`e3_9/level_check.json`) — the same generator, the same estimator, two disjoint 200-seed blocks,
differing by 7 % with barely overlapping intervals. **200 seeds does not pin this generator's level to better
than about ±7 %.** Every level figure in Phase 4 is therefore reported with its seed block named, and the
E4.0c adoption test is run at **500 seeds** per scenario rather than 200. This is an increase in the
pre-registered sample decided before the run, and it is affordable: the whole E4.0 arm took 67 s.

---

## 2. Section 1.5's corrected rule is itself withdrawn before it is run, and replaced

### 2.1 Disclosure

Section 1.5 registered a corrected test (re-base all seven multipliers to the anchor's mean-based reference)
and an adoption rule for it. **That rule was never run.** Before running it I made one further check — the
panel's calm measured with the *same pooled-mean aggregator the generator's pooled sd uses*, rather than the
median-across-episodes aggregator Phase 3 used — and it removes the premise of both section 1.5 and section 1.2.

What I had seen when writing this section, in addition to everything listed in section 1.2:

| Quantity | Value |
|---|---|
| Panel calm sd, **pooled mean** across episodes (matched to the generator's estimator) | **0.021672 [0.020853, 0.022479]**, n = 1592 / 412 |
| Panel calm sd, median across episodes (Phase 3's aggregator) | 0.017034 [0.01632, 0.01764] |
| Panel full-sample `s_A` | 0.021793 |
| Generator calm, pooled mean over all 800 base-arm paths | 0.022379 (71,376 calm days) |
| Panel vs generator, **ratio-to-own-calm**, matched estimator | deterioration 1.618 vs 1.221 · panic 7.642 vs 7.957 · stabilisation 3.109 vs 3.098 |
| Panel run-up-episode calm reference | sd **0.041267**, n = 3125 — nearly double the drawdown episodes' calm |

### 2.2 What the matched estimator shows

**There is no calm defect.** Under one estimator applied to both sides, the panel's calm is 0.021672
[0.020853, 0.022479] and the generator's is 0.022379 — a ratio of **1.033**, with the panel's own full-sample
`s_A` at 0.021793 sitting between them. Section 1.2's "ratio 1.356, CIs disjoint" compared a pooled-mean
generator statistic with a median-across-episodes panel statistic; the 1.356 is that aggregator gap, and it is
the same 1.354 mean/median ratio documented in section 1.4.

**The crash-side phase structure is right.** Ratio to own calm, panel vs generator: panic **7.642 vs 7.957**,
stabilisation **3.109 vs 3.098**. Deterioration is the exception — **1.618 panel vs 1.221 generator**, i.e. the
generator's deterioration phase is materially too quiet. That is a new finding and it is E4.2's and E4.6's,
not a level question.

**The bubble-side multipliers are referenced to a denominator that does not describe their own population.**
The run-up episodes' calm windows have sd 0.041267 against the drawdown episodes' 0.021672 — run-ups occur in
volatile names, and E3.3's run-up "calm" window sits at a post-crash trough, which is the contamination
`PREREG_PHASE_3_ADDENDUM.md` section 1 identified and corrected by switching the reference to `rv_uncond`.
That correction was right, but it leaves the mania / blow-off / post-top multipliers expressed against a
median-RV level far below their own population's volatility, so they are **not comparable** with the crash-side
multipliers and cannot be read as "ratio to the generator's calm".

**Consequence for the deployed figure.** Once calm matches and the crash-side ratios match, the generator's
pooled all-day sd necessarily exceeds the panel's all-day sd, because the benchmark *deliberately* runs equal
numbers of crash, bull-trap, sustained-bull and flat scenarios, while the panel is overwhelmingly calm days.
The generator spends 5.3 % of its days in panic at about 8x variance; no real panel does. **Phase 3's
"+30.5 % double count" is therefore two artefacts and no defect**: the calm half is mean-versus-median, and
the deployed half is the benchmark's own scenario mix. The +15.3 % that survives panel phase re-weighting
(section 1.2) is the residue of the same mix plus the deterioration gap, not a level error.

### 2.3 The rule that replaces section 1.5 (E4.0c), registered before it is run

The level question is **not** decidable on a pooled unconditional, because the generator's phase mix is a
design choice and the panel's is a fact about the world. It is decidable **conditional on phase**.

**Statistic.** For each phase, the pooled-mean realised variance on the generator and on the panel, each
divided by its own side's pooled-mean **calm** variance, with 1,000-resample bootstrap CIs (generator
clustered by seed, panel clustered by stock). n reported as (days, paths) and (episodes, stocks).

**Rule.** The generator's volatility level is accepted for a phase iff the generator's ratio-to-own-calm lies
inside the panel's 95 % CI for the same ratio. Additionally the **levels** must agree: the generator's pooled
calm sd must lie inside the panel's pooled calm sd CI.

**Reported, not tested**, for mania / blow-off / post-top: the same ratios, with the explicit statement that
the panel's run-up calm reference is contaminated by post-crash troughs, so the comparison is published as
uninterpretable on this reference and a corrected reference is derived in **E4.1** (which dates the run-up
population properly and can therefore supply a clean pre-run-up window).

**Consequence, registered now.** If the calm levels agree and the crash-side ratios agree, **the anchor is
kept and Phase 3's level double-count is reported as withdrawn**, with this evidence — no re-anchoring, no
cascade, no engine re-identification. Any phase whose ratio falls outside the panel's CI is handed to the
experiment that owns it (deterioration to E4.2/E4.6; the bubble phases to E4.1's corrected reference and E4.8)
and is fixed there as a *shape* problem, not by moving the level.

**This supersedes section 1.5, which is withdrawn unrun.** Section 1.3's verdict under the originally
registered rule — route (a) stands, the level as handed over — is unchanged by any of this, and is now
supported rather than merely defaulted to.

### 2.4 Corrections this forces in documents Phase 4 inherits

Published in `PHASE_4_REPORT.md`, with the generated file that decides each:

1. `PHASE_3_REPORT.md` section 3.11c and section 5.7, and `e3_9/level_check.json`, describe 0.01703 as "the
   panel's **crisis-free calm**" and read the gap to `s_A` as calm-versus-all-day. It is the panel's
   **median-RV level**; the gap is mean-versus-median. The calm windows match the median level because calm
   windows are typical days.
2. `e3_9/level_check.json` sets `"double_count_confirmed": true` on a rule ("the excess exceeds the pooled
   statistic's own bootstrap half-width") that cannot distinguish a level defect from a scenario-mix
   difference. The flag is **withdrawn**; the field is not edited, and the correction is published beside it.
3. `PHASE_3_REPORT.md` section 5.7's three costed options (a)/(b)/(c) rest on the same reading. Option (b)'s
   measured cost (flat sd(x) 0.0468 to 0.0214) remains correct as a fact about re-anchoring; the *reason* to
   re-anchor is withdrawn.

### 2.5 What E4.8's post-top rule becomes

`PREREG_PHASE_4.md` section 10 registered "the post-top realised variance ratio's 95 % CI must contain the
panel's 1.16 [1.13, 1.20]". That target is a ratio to `rv_uncond`, a denominator that does not describe the
run-up population (section 2.2). **The rule is suspended** until E4.1 supplies a clean pre-run-up reference,
at which point the target is recomputed on that reference and the rule is restated in a further addendum
section **before** E4.8 runs. The incumbent's measured floor (1.59, n = 20) and the new measurement are both
reported against **both** references.

---

## 3. "Drawn from the empirical P10-P90" is implemented as the empirical distribution, not as a uniform

### 3.1 Disclosure

`PREREG_PHASE_4.md` section 4 registers that "each schedule parameter is drawn from the panel's empirical
**P10-P90** (FIT)". The first implementation read that as a **uniform** over the interval. What I had seen
when writing this section, all of it in `docs/env_v2/generated/v2_1/e4_2/schedule.json` at a 60-seed smoke
run plus `e4_1/dd30.csv`:

| Quantity | Value |
|---|---|
| v2 arm, median rise time | 70.0 d [59.0, 81.5] - **NOT MET** against the panel's [29, 35] |
| v2.1 uniform arm, median rise time | 71.0 d [57.0, 89.5] - **NOT MET**; the FIT interval alone changed nothing |
| Drawn `det_len` mean, uniform arm | 13.8 (panel median 8) |
| Drawn `panic_len` mean, uniform arm | 53.3 (panel median 39) |
| Panel `det_len` (fast crashes) | P10 3, **P50 8**, P90 25.9 - a uniform on [3, 25.9] has median **14.4** |
| Panel `panic_len` (fast crashes) | P10 15, **P50 39**, P90 100.9 - a uniform on [15, 100.9] has median **57.9** |
| Panel `duration` (fast crashes) | P10 22, **P50 53**, P90 113 - a uniform has median **67.5** |

No E4.3-E4.8 experiment had been run.

### 3.2 Why the uniform reading is wrong

Every one of these parameters is right-skewed. A uniform over [P10, P90] reproduces the fitted *interval* but
replaces the fitted *shape* with a stipulated one, and in doing so mis-centres the parameter by 45-80 %:
`det_len` lands at 14.4 where the panel says 8, `panic_len` at 57.9 where the panel says 39. **The interval
would be FIT and the distribution DESIGN**, which is exactly the split the programme's governing rule forbids
("every generator parameter is fitted or tested on data, never stipulated"). It is also why the FIT interval
on its own moved the rise time by one day: the uniform put the mass back where v2 had it.

### 3.3 The corrected rule, registered before the re-run

**Statistic unchanged.** The rise-time criterion, its estimator, its n and its overlap rule are exactly as
registered in `PREREG_PHASE_4.md` section 4. Only the sampler changes.

**Sampler.** Each FIT schedule parameter is drawn by **inverse-CDF sampling from the panel's own empirical
distribution, truncated to [P10, P90]**: the parameter file stores an equally-spaced quantile grid from
q = 0.10 to q = 0.90 and the generator draws u ~ U(0, 1) and interpolates. This reproduces the panel's
interval *and* its shape, and it degenerates to the uniform when the empirical distribution is flat.

Ranges that are genuinely DESIGN choices rather than episode facts (`setup_frac`, `setup_event_first`) stay
uniform and stay labelled DESIGN.

**Reported under both rules.** E4.2 reports three arms, not two: **v2** (stipulated uniforms), **v21_uniform**
(FIT interval, uniform shape - the rule as originally registered) and **v21_empirical** (FIT interval, FIT
shape - the corrected rule). The uniform arm is kept in the report precisely because it shows that a fitted
interval with a stipulated shape buys nothing.

**If the corrected sampler still does not reach [29, 35]**, the criterion is recorded as NOT MET, the binding
constraint is named, and the phase does not relax it. The candidate constraints are already visible and are
stated now so the diagnosis cannot be fitted after the fact: (i) the 21-day realised-variance window itself
puts a floor of roughly 10-20 days on any measured rise time; (ii) `panic_len` and the panic variance
multiplier jointly set where the RV21 peak falls; (iii) the deterioration phase carries no variance
multiplier above 1.37, so the RV21 peak cannot occur inside it.

---

## 4. E4.6's coverage threshold rests on an arithmetic premise the panel refutes

### 4.1 Disclosure

`V2_1_ALTERNATIVES_REGISTER.md` REG-8 and `V2_1_IMPROVEMENT_PLAN.md` section 8.2 justify E4.6's coverage
threshold this way:

> the share of real episodes inside their own P10-P90 is **0.80 by construction** of the range; the generator
> must reach >= 0.70, a DESIGN margin stated as such.

What I had seen when writing this section: E4.6's full table at 1000 crash and 1000 bull seeds per formulation
(`e4_6/dynamics.md`, run on the Kaggle kernel `fp-p4-e46` after its reference-row guard passed at a worst
relative difference of 0.0), showing coverage 0.323-0.562 across all seven arms with no arm eligible; and the
panel's own self-coverage, **0.643 (n = 642)**, computed by the same code that computes the generator's.

### 4.2 The premise is wrong, and the rule is unmeetable because of it

A P10-P90 interval captures 0.80 of a distribution **in one dimension**. E4.6's box is two-dimensional -- depth
**and** duration jointly. For independent marginals the joint share is 0.80 x 0.80 = 0.64, and the panel
measures exactly that: **0.643**.

So the registered rule asks the generator to place **more** of its episodes inside the panel's own P10-P90 box
than the panel itself does, by about 6 pp. **No generator can meet it, and no result could have.** This is the
fourth phase in a row to hit a criterion of this kind, and it is the one the PP-series did not cover, because
the PP-series checked whether thresholds were *decidable at the stated n*, not whether they were *attainable
in principle*.

### 4.3 What is reported

**Under the registered rule, unchanged: no formulation qualifies, and E4.6 STOPS FOR D5.** That verdict stands
and is what the phase report carries. The table of all seven arms is published whether or not any qualifies,
as the pre-registration requires.

**Beside it, the corrected reference is published**: the panel's self-coverage 0.643 [n = 642], and each arm's
coverage as a fraction of it. Phase 4 does **not** set a corrected threshold and does **not** adopt a
formulation on one. Choosing a new margin after seeing the table is precisely the move the protocol forbids,
and the margin is a DESIGN choice that belongs with D5 in the team's hands. The report states the arithmetic,
gives the measured reference, and asks.

### 4.4 A second statistic that had to be fixed before the table could be read

The adoption rule ranks eligible formulations by the **lowest script share**, so that statistic decides the
phase. The first implementation regressed realised delta-x on a *reconstruction* of the scripted target path
(a constant per-day increment over the panic phase) rather than on the drift the driver actually returned.
That reconstruction cannot represent formulations B and D at all -- they have no target path -- and it
returned 0.004-0.010 for every arm, which is not a measurement of anything.

`PathResult.drift` now records d_t as the driver returns it, and the script share is the R^2 of that recorded
series on realised delta-x over event-phase days. This is a **correction to an instrument, not to a rule**:
the statistic, the threshold and the decision procedure are exactly as registered. The corrected table is what
the report carries; the first table is discarded rather than reported, because a mis-specified regressor
produces a number with no interpretation, not an alternative result.

---

## 5. Three Phase-4 numbers were measured before the state they describe existed, and two parameters were left stipulated

### 5.1 The ordering defect, found by timestamp audit

`envs/v2/params/events.json` was written at **14:47:39**. `e4_3/hazard.json` (14:18:51),
`e4_5/control.json` (14:41:28) and `e4_8/labels.json` (14:45:37) were all produced **before** it, and none of
those three tools pins `schedule_mode`. With `events.json` absent, `events_params.PRESENT` is False and the
generator runs the **v2** ranges — so all three measured a state that is not the one they were then quoted as
describing, in the parameter file and in `PHASE_4_REPORT.md`.

The Phase-4 checklist had already contradicted one instance (topped share 15 % deployed against E4.3's
calibrated 0.108) and the report explained it away as "a different seed block" **without testing the
explanation**. That was an inference presented as a reconciliation, and it was wrong.

### 5.2 What the re-measurement on the deployed state shows (`e4_9/deployed.json`, 500 seeds per scenario)

| quantity | as calibrated (v2 schedule) | deployed | panel target | verdict |
|---|---|---|---|---|
| topped share, panel rule | 0.108 | **0.008 [0.002, 0.018]** | 0.110 [0.0966, 0.1245] | **DOES NOT HOLD** |
| post-top / mania variance | 0.6186 | **0.787 [0.574, 1.100]** | 0.6225 | **DOES NOT HOLD** |
| blow-off / mania variance | — | 0.972 | 1.289 | consistent with the multiplier still at mania's value |
| crash rise time | 58.0 [52, 64] | 60.0 [55, 65] | 30 [29, 35] | consistent with the pinned arm; still NOT MET |
| control C rejection / KS(sd) | 0.358 / 0.474 | 0.336 / 0.408 | — | same direction and magnitude |

So **P4-7's adopted hazard and P4-12's adopted half-life do not hold on the state they were shipped into.**
The crash and control findings do hold and are unaffected.

### 5.3 The cause, measured rather than reasoned

The hazard is not what fails. On the deployed state it **fires on 0.19 of bull-trap paths**, close to its
calibrated rate. What collapses is the **drawdown that follows the top**: only 0.008 of paths reach the −40 %
the panel's rule requires.

The reason is that two schedule parameters were carried over **stipulated** into `events.json` while the panel
holds the data for both:

| parameter | shipped in events.json | panel (n = 3,201 run-ups / 398 stocks) |
|---|---|---|
| `post_top_drop` | U(0.30, 0.50) — **v2 DESIGN, never fitted** | \|post-drop\| P10/P50/P90 = **0.061 / 0.169 / 0.414**; share reaching −40 % = **0.110** |
| `post_top_len` | U(10, 30) — **v2 DESIGN, never fitted** | post-length P10/P50/P90 = **8 / 60 / 187** d |

A drop drawn from U(0.30, 0.50) delivered through a decay leg of half-life 50 over the horizon that remains
after the top completes only a fraction of itself, so the realised drawdown almost never reaches −40 %. The
half-life was fitted to the *variance* ratio under the *v2* drop and length ranges; deployed, the two fight
each other.

**This is a violation of the programme's governing rule inside Phase 4's own parameter file**: the interval
was DESIGN where the panel could supply a FIT, and E4.2's table did not include these two because they were
treated as bubble-side parameters rather than episode facts. They are episode facts.

### 5.4 The corrected procedure, registered before it is run

Everything below is measured on the **deployed** state, with `schedule_mode` pinned explicitly so the failure
cannot recur.

1. **Fit `post_top_drop` and `post_top_len`** from the panel's run-up outcome table by the same inverse-CDF
   empirical-grid sampler §3 registered, over P10–P90, with the truncation rate reported.
2. **Re-search the post-top half-life** on the deployed state against the panel's post-top/mania variance
   ratio **0.6225**, with the drop and length now fitted.
3. **Re-measure the topped share** by the panel's own rule. Under the corrected design the topped share is an
   **outcome of fitted parameters** rather than a statistic the hazard was tuned to reach — which is the right
   way round, and is what PREREG §5 meant by retiring it as a target.
4. **Re-check REG-18's mapping decision** on that state. The adoption rule is unchanged: the mapping whose
   topped share lies inside the panel's CI. If the ranking changes, the mapping changes with it; if no mapping
   qualifies under the corrected design, that is reported and no mapping is adopted.

**Registered consequence.** Steps 2 and 3 are coupled — the leg shape sets both the variance ratio and the
realised drop — so they are calibrated **jointly** and both are reported, whether or not both criteria can be
met at once. If they cannot, that is a statement about the environment (the panel's post-top variance and its
post-top depth are not simultaneously reachable by a single deterministic leg) and it is reported as such,
not resolved by dropping one of them.

### 5.5 What this changes about how the phase reports itself

Every number in `PHASE_4_REPORT.md` that came from `e4_3`, `e4_5` or `e4_8` is re-stated from
`e4_9/deployed.json` or from the corrected calibration, and the "as calibrated" column is kept beside it so
the size of the error is visible rather than erased. The three tools are pinned to an explicit
`schedule_mode` so that a result can no longer be produced against an implicit state.

### 5.6 The outcome of the corrected procedure

**Step 1 — the two stipulated parameters, fitted** (`e4_11/posttop_recal.json`, n = 3,201 run-ups / 398 stocks):

| parameter | shipped (v2 DESIGN) | panel P10 / P50 / P90 |
|---|---|---|
| `post_top_drop` | U(0.30, 0.50) | **0.061 / 0.169 / 0.414** |
| `post_top_len` | U(10, 30) | **8 / 60 / 187** d |

Both are now drawn by the inverse-CDF empirical-grid sampler of §3.

**Step 2 — the half-life, re-searched on the deployed state** (**1,500** bull-trap seeds per arm,
`schedule_mode` pinned):

| arm | post-top / mania | inside the panel CI [0.599, 0.648] | topped share | realised drop P50 |
|---|---|---|---|---|
| v2 stipulated ranges, hl 50 | 0.646 | yes | 0.0040 | −0.226 |
| FIT ranges, hl 10 | 0.730 | no | 0.0073 | −0.226 |
| FIT ranges, hl 20 | 0.659 | no | 0.0033 | −0.204 |
| FIT ranges, hl 30 | 0.634 | yes | 0.0027 | −0.191 |
| **FIT ranges, hl 40** | **0.6216** | **yes** | 0.0027 | −0.184 |
| FIT ranges, hl 50 | 0.630 | yes | 0.0020 | −0.180 |
| FIT ranges, hl 70 | 0.622 | yes | 0.0020 | −0.172 |
| FIT ranges, hl 100 | 0.616 | yes | 0.0013 | −0.167 |

The variance-ratio criterion **is met** by half-lives 30 through 100; **hl 40 is adopted** (0.6216 against the
panel's 0.6225). The topped share is not met at any half-life.

**A sampling lesson recorded because it nearly became a decision.** A first pass of this same search at **400**
seeds put hl 10 inside the CI at 0.617 and every other setting outside, and would have adopted hl 10. At 1,500
seeds hl 10 measures **0.730** and is outside, while 30–100 are all inside. The 400-seed result was noise; the
search was re-run at 1,500 **before** anything was written to the parameter file, which is the only reason the
wrong value was not adopted. A tie-break was also specified explicitly — closest to the panel's point estimate
among the arms inside its CI — rather than left to dictionary order, which had been silently selecting hl 30.

**Step 3 — why the topped share is not met, tested rather than asserted** (`e4_12/horizon.json`, 600 seeds).
The obvious reading — that the drop is still too shallow — is refuted by the generator's own realised drop
(P50 −0.239, **deeper** than the panel's own median of −0.169). The hypothesis tested instead was that the
panel measures every run-up over a full 200 days after its top, whereas a generated path tops *inside* its own
200-day horizon. The falsifier was a window-matched comparison:

| post-top days available | generator | panel, same restriction | CIs overlap |
|---|---|---|---|
| 0–50 | 0.0250 [0, 0.0625] (n = 80) | 0.0294 [0, 0.0882] (n = 34) | **yes** |
| 50–100 | 0.0769 [0, 0.1923] (n = 26) | 0.0357 [0, 0.1071] (n = 28) | **yes** |
| 100–150 | no generator paths | 0.0000 (n = 24) | — |
| 150–201 | no generator paths | **0.1124 [0.1011, 0.1239]** (n = 3,115) | — |

**Within every window bin the two populations share, the generator agrees with the panel.** The panel's
headline 0.110 comes almost entirely from the 3,115 run-ups that have a 150–200 day post-top window, and only
**0.9 %** of generated topped paths have even 120 days left — the median is **29**.

**Step 4 — the consequence for REG-18.** The topped share cannot discriminate between hazard mappings on a
200-day horizon that must also contain the mania, because the statistic is dominated by how much window
remains rather than by the hazard. **P4-7's adoption is therefore withdrawn**: `events.json`'s hazard entry
moves from ADOPTED to **INCUMBENT**, keeping the same values in force, with the withdrawal and its evidence on
the entry. E4.3's apparent success was an artefact of the v2 leg forcing a 30–50 % drop into 10–30 days, which
is precisely the drift-dominated shape Phase 3 flagged and E4.8 removed.

**What would make REG-18 evaluable**, stated so the team can choose rather than inferred: (i) re-express the
criterion window-matched, comparing the generator against the panel restricted to the same available window —
which the table above already does, and under which the incumbent mapping is not rejected; (ii) lengthen T for
the bull-trap scenario so a mania and its aftermath both fit; or (iii) start the mania earlier so more horizon
remains after the top, which is `setup_len` again and therefore couples to E4.2 and E4.7. None of these is
Phase 4's to choose.

### 5.7 What this episode says about the phase's method

Three of the five things this addendum documents were found by testing the phase's own reasoning rather than
by running a new experiment on the environment: §1's level hypothesis, §3's uniform sampler, and §5's ordering
defect. The ordering defect in particular was invisible to every test in `tests/test_v2_1_phase_4.py`, because
those tests check that the *deployed* state matches the *recorded* values — and both sides were consistent;
what was wrong was that the recorded values had been measured somewhere else. The guard that catches this is
not a test but a discipline: **a tool that measures the generator must pin the configuration it measures**,
and `e4_3`, `e4_5` and `e4_8` did not. They now do, and `e4_9` exists to re-measure the whole block on the
deployed state whenever the parameter file changes.

---

## 6. A departure from the pre-registration: two decisions this phase registered to STOP on were taken

**Disclosed because it is a departure, not because it went badly.** `PREREG_PHASE_4.md` registers that Phase 4
will run the experiments for D5 and D14 and **stop** — "ADOPTING is D14, a statement about what the control is
FOR, which the pre-registration forbids Phase 4 from taking on the team's behalf". The phase did stop, and
sections 3.6 and 5 of the report record that. **The team then read the recommendations in report section 5.1
and authorised acting on them (6 Sep 2026), and one of the two was subsequently taken.** That authorisation is
the only reason the adoption is legitimate; without it P4-43 would be a pre-registration violation.

**What was taken, and what was not:**

- **D14 → definition A (P4-43).** Adopted. Weakness items 18 and 42 are closed.
- **D5 → nothing.** Not adopted, and not because the phase ran out of time: testing the recommendation
  showed **both halves of the registered adoption rule are unusable** — the ranking metric is not monotone in
  scriptedness (a fully scripted arm scores below an unscripted one) and the coverage criterion is blocked by
  a depth floor set outside the event block. A rule that cannot rank and a criterion that cannot be met are
  not a basis for adoption, so the phase stopped again, on better-established grounds than the first time.

**Three of the seven recommendations were refuted by the tests run to check them** — κ = 0 (it makes the bull
trap 96.3 % rejected), my D5 noise-floor argument, and my root-cause story for the unmeetable criteria. They
are recorded as refuted in P4-42 and P4-44 rather than quietly dropped, on the same principle as section 1 of
this addendum: **a pre-registration is only worth something if the disconfirmations are reported as loudly as
the confirmations.**

**One consequence was not predicted by anyone and is the strongest argument for the adoption**: definition C's
x-band was not only leaking the hidden state, it was making a quarter of the benchmark unscoreable — median
|x| 0.0143 with 3.5 % of steps resolvable, one run in ten with nothing to score. Under A that is 0.0362 and
35.6 %, and sustained-bull coverage rises 0.044 → 0.374 (P4-46). It was found by re-running the discrimination
table **after** the adoption, which is the discipline section 5.7 of this addendum argues for and which P4-45
records the phase failing to apply to its own sequencing.

