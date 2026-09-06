# Phase 4 report — events, schedule, controls and the calendar (v2.1)

Executed under `PREREG_PHASE_4.md` and its addendum. Nothing is committed; everything is in the working tree
on `main`. Section 8 of `V2_1_IMPROVEMENT_PLAN.md`; REG-7, REG-8, REG-9, REG-15, REG-18.

**One-line summary.** The event block is re-fitted from the panel and four of the five measured defects Phase 4
inherited are closed or explained; a verification pass (section 8) then tested the phase's own inferred claims
and overturned four of them, including two adopted parameters that had been measured before the state they
describe existed; two pre-registered criteria turned out to be unmeetable by any result and
are reported as such; two decisions (D5, D14) are handed back to the team with the numbers they need; and
**Phase 3's headline level defect is withdrawn** — under a matched estimator the generator's calm matches the
panel's, and the "+30.5 %" was an aggregator mismatch plus the benchmark's own scenario mix.

**Then a completion pass (section 9) executed every item section 7 had listed as not done, and its
headline is a negative result.** The brief asked whether the event redesign would narrow the calm
level-free channel — "the single most useful thing your event redesign could hand" Phase 6. Measured
directly, with Phase 3 re-run under the same estimator in the same process as a control: **it did not**
(calm-trained level-free R²(x) 0.3493 [0.3218, 0.3743] → 0.3594 [0.3282, 0.3859], CIs overlapping, the
point estimate moving the wrong way). The events-and-sentiment share stands at ≈ 0.15, where Phase 3
left it. The pass also **calibrated the blow-off multiplier**, **rejected v2's crash V-drift shape in
direction**, showed the **rise-time criterion can be met** at a shorter setup, and found a **second
provenance defect** (P4-37): a cited evidence file that had never been written, whose stdout-sourced
numbers proved unreproducible.

---

## 0. Current state, and how to read this report

This report was written in four passes, and later passes overturn earlier ones. **Nothing has been deleted**;
corrections are made in place with the original recorded, because several of the overturned claims are
themselves findings about how the phase went wrong. Read it in this order:

| pass | sections | what it is |
|---|---|---|
| main | 1–7 | the registered experiments, as executed |
| verification | 8 | tested the phase's own inferred claims; **overturned four**, including two adopted parameters |
| completion | 9.1–9.13 | executed everything section 7 listed as not done; **found two provenance defects and six failing tests** |
| acting on 5.1 | 9.12–9.14 | the team authorised acting on the recommendations; **three did not survive their own tests** |

**State markers matter.** Sections 9.5 and 9.9 describe the generator **before D14 was taken**; section 9.14
carries the post-D14 re-measurement and says why. Where a number was superseded, the superseding section is
named at the point of use.

### What is settled

- The event block is re-fitted from the panel and deployed; `schedule_mode="v2"` reproduces v2 bit for bit.
- **All 22 test files pass** — 148 passed, 1 skipped, 4 xfailed, 0 failed. Every xfail is registered.
- **Weakness items 18 and 42 are CLOSED** (P4-43) — the phase's only retired defects, not re-registered ones.
- Decisions **P4-1 … P4-45**, each with the alternative rejected and the evidence file that decided it.

### What is deliberately not settled

Seven items in section 5 are team decisions the pre-registration forbids this phase from taking, and two of
them are now **costed** rather than open: κ = 0 needs the bull-trap validity threshold re-expressed at the
same time (P4-44), and D5 cannot be decided on **either** half of its registered rule — the ranking metric is
not monotone in scriptedness (§9.12) and the coverage criterion is blocked by a depth floor set outside the
event block entirely (§9.13).

### The three method defects this phase found in itself

All the same shape — **a number whose provenance was assumed rather than checked**:

1. **P4-19** — three results measured before the parameter file they described existed. Fix: tools pin their
   configuration; `e4_9_deployed.py` re-measures the block on the deployed state.
2. **P4-37** — a cited evidence file that had never been written; the numbers came from stdout and proved
   unreproducible. Fix: assert every cited path exists (59 artefacts and 36 source files now verified).
3. **P4-38** — nine of twenty-two test files had never been run; six tests were failing, four since the main
   pass. Fix: run the whole tree, not the suites the phase remembers writing.

**P4-45 is the fourth and it is the same lesson applied to sequencing rather than to a tool**: two long audits
were run and *then* invalidated by adopting a parameter change. Measure after the parameter file settles.

### The finding with the longest reach

**The generator cannot produce a panel-median crash.** Realised depth has a structural floor near −0.46
against the panel's −0.3693; the closed loop does not converge, rejection is 0.000 at every gain so it is not
selection, and the decomposition attributes it to `D_V` — a **stipulated** uniform labelled DESIGN — plus a
panic-phase mispricing excursion that belongs to Phase 3's frozen volatility block. No Phase-4 formulation
choice could have changed this, which is why D5's coverage criterion was never winnable (§9.13).


---

## 1. Literature review and the citation table

| Statistic | Source | Status | Used for |
|---|---|---|---|
| Crash probability 20 / 53 / 80 % after 50 / 100 / 150 % net-of-market run-ups; industry level, monthly, crash = 40 % drawdown within two years | Greenwood, Shleifer & You (2019, *JFE*) | **read-and-correct** — a logit through the three points reproduces them to 0.197 / 0.539 / 0.797 | E4.3's hazard slope `b` = 5.419 |
| 15 US stock-market crashes of 20 % or more, 20th century, with dates and magnitudes | Mishkin & White (2002, NBER w8992) | **not retrievable in this phase** | **nothing.** No number from it appears in any table, tolerance or parameter file |
| 232 country-index crashes at −25 % or worse, 30 countries, annual | Barro & Ursúa (NBER w14760 / *Research in Economics* 71(3)) | **not retrievable in this phase** | **nothing** |
| The turning-point dating algorithm | Pagan & Sossounov (2003, *JAE*) | algorithm applied; **their 25/15-month durations were not read and are not quoted** | E4.1's `ps_primary` / `ps_sensitive` families, with this phase's own daily censoring constants at two settings |
| The linearised LPPLS calibration | Filimonov & Sornette (2013, *Physica A*) | method applied | E4.1's LPPLS stage |
| Shiller monthly real price, 1871–2026 | `datasets/04_shiller` | held on disk, computed **at first hand** here | the index episode table published beside the panel (D4) |

The index table is this phase's own computation, not a quotation. It yields **12** episodes of 20 % or more and
**6** of 30 % or more over 155 years of monthly data — which is the empirical case for D4, not an argument for
it: no P10/P90 on depth, duration, front-loading or recovery is estimable at that n, and a monthly series
cannot produce a deterioration length in trading days at all.

---

## 2. Pre-registration, the level as handed over, and four corrections

`PREREG_PHASE_4.md` was written before any run. `tools/phase4/prereg_power.py` simulated every registered
threshold's decidability at its stated n **before** the experiments it protects (`e4_0/power.json`), and on its
evidence the pre-registration raised E4.6 from the plan's 200 seeds to 500 (power against a true 0.65 rises
from 0.47 to 0.78) and fixed the label-permutation null to permute **seed** labels rather than day labels (the
day-level null's p95 is 0.503, which would call almost any classifier a leak).

Four corrections were made after data were seen and **before** the runs they govern, each with a disclosure of
exactly what had been seen (`PREREG_PHASE_4_ADDENDUM.md`):

1. **§1–2 — the level hypothesis was wrong and the corrected test replaced it.** Reported under both rules.
2. **§3 — "drawn from the empirical P10–P90" is the empirical distribution, not a uniform over it.** Both arms
   are run and both are reported.
3. **§4 — E4.6's coverage threshold rests on an arithmetic premise the panel refutes.** The registered verdict
   stands; the corrected reference is published beside it and no new threshold is set.
4. **§2.5 — E4.8's post-top target was suspended** until E4.1 supplied an uncontaminated reference, then
   restated.

**The level as handed over is KEPT** (route (a) under the registered rule, and now positively supported rather
than defaulted to — see §3.1). No Phase-4 number is conditional on a re-anchoring.

---

## 3. Experiments and results

### 3.1 E4.0 — the level, and a withdrawn inheritance

The registered rule asked whether calm's stipulated multiplier of 1.0 was refuted. It is **not**: measured in
its own family, `m_calm` = **1.0102 [0.9791, 1.0561]** (n = 1592 episodes / 412 stocks). Under the rule as
registered, route (a) stands.

The measurement then explained why the hypothesis was wrong, and the corrected test (addendum §2.3) settles the
question on the only comparison that can settle it — **conditional on phase, one estimator on both sides**:

| | generator (v2 state) | **generator (deployed)** | 95 % CI (deployed) | panel | 95 % CI |
|---|---|---|---|---|---|
| **calm sd** | 0.022007 | **0.022054** | [0.021652, 0.022482] | **0.021672** | [0.020860, 0.022439] |
| deterioration / own calm | 1.414 | **2.632** | [2.382, 2.938] | 1.618 | [1.506, 1.746] |
| panic / own calm | 8.594 | 8.564 | [7.505, 9.732] | 7.642 | [6.968, 8.428] |
| stabilisation / own calm | 3.418 | 3.432 | [3.143, 3.741] | 3.109 | [2.851, 3.409] |

The deployed column was added by the verification pass (section 8): E4.0 itself did not pin `schedule_mode`,
so its own numbers were taken under v2. **The calm finding survives** — ratio 1.0176, inside the panel CI —
and the anchor stays kept. **Deterioration flips sign**: too *cold* under v2 (1.414) and too *hot* deployed
(2.632 against the panel's 1.618), because the fitted `det_len` (median 8 d against v2's 27) compresses the
same fundamental decline `D_V` into a third of the days. That is a direct, measured consequence of E4.2 and
it replaces section 3.1's original reading of this row.

Generator: 500 seeds × 4 scenarios (177,687 calm days), clustered by seed. Panel: 1,592 episodes / 412 stocks,
clustered by stock. The panel's own full-sample `s_A` (0.021793) sits between the two calm figures.

**The calm level is accepted** (ratio 1.015). Phase 3's 1.28× compared a *median-across-episodes* panel
statistic with a *pooled-mean* generator statistic; the per-stock ratio of those two aggregators is **1.354
[IQR 1.286, 1.452]** (n = 417) — the whole of the gap, and the same number as the 1.356 Phase 3 read as a
defect. The deployed "+30.5 %" is the benchmark's own scenario mix: equal weight on flat / crash / bull-trap /
sustained-bull puts 5.3 % of days in panic at ~8× variance, which no all-day panel has; under the panel's own
phase-day weights the excess falls to **+15.3 %**.

**Corrections this forces to Phase 3's documents** (published here, the files not edited):

- `PHASE_3_REPORT.md` §3.11c/§5.7 and `e3_9/level_check.json` describe 0.01703 as "the panel's **crisis-free
  calm**". It is the panel's **median-RV level**; calm windows match it because calm windows are typical days.
  The gap to `s_A` is mean-versus-median, not calm-versus-crisis.
- `e3_9/level_check.json` sets `"double_count_confirmed": true` on a rule that cannot distinguish a level
  defect from a scenario-mix difference. **The flag is withdrawn.**
- §5.7's option (b) remains correct as a *fact* about re-anchoring (it halves flat sd(x) from 0.0468 to
  0.0214); the *reason* to pay for it is withdrawn.

Under the strict point-in-interval rule all three crash phases sit outside the panel's CI. Panic and
stabilisation are slightly hot and their own CIs overlap the panel's. **Deterioration is the substantive one,
and on the deployed state it is too LOUD, not too quiet**: 2.632 [2.382, 2.938] against 1.618 [1.506, 1.746],
with disjoint intervals. Compressing `D_V` from a 27-day median deterioration into an 8-day one raises the
per-day variance of that phase by more than the panel supports. Either `D_V` should be re-fitted alongside
`det_len` (it is still the v2 DESIGN range U(0.10, 0.30), and the panel can supply it through the
fundamental-decline share the item-73 test would measure), or the decline should be spread past the
deterioration phase using the `crash_v_drift` tail-share mechanism that is implemented but untested. Both are
shape questions for E4.2/E4.6 and neither is a level question.

### 3.2 E4.1 — the episode tables

Verified before use: all 40 sampled inherited episode rows reproduce exactly on indices and to 1e-10 on depth;
every inherited figure matches the generated file it cites (`e4_0/level.json` `verification`).

| family | episodes | stocks |
|---|---|---|
| drawdowns ≥ 20 % | 3,078 | 417 |
| drawdowns ≥ 30 % | **1,789** | 417 (reproduces Phase 3 exactly) |
| **dd30_fast** (≤ 126 d, the T = 200 population) | **642** | **313** (reproduces Phase 3's fast-crash n) |
| Pagan–Sossounov bear, primary / sensitive censoring | 1,975 / 4,535 | 417 |
| run-ups ≥ 100 % in 504 d | 3,202 | 398 |
| Shiller index episodes ≥ 20 % / ≥ 30 % | 12 / 6 | — |

`dd30_fast` also reproduces Phase 3's rise time exactly: **30 d [29, 35]**. The quantities E4.2 draws from:

| quantity | P10 | P50 | P90 | v2 drew |
|---|---|---|---|---|
| deterioration length | 3 | **8 [7, 9]** | 25.9 | U(15, 40) |
| panic length | 15 | **39 [35, 43]** | 100.9 | U(15, 70) |
| depth | −0.538 | −0.369 | −0.312 | delta fixed 0.70 |
| front-loading | 0.088 | **0.272** | 0.574 | fixed 0.50 |
| recovery at 60 d | 0.236 | 0.569 | 1.037 | delta_end ~ U(delta, 1) |

Also fitted here: the run-up **topped share 0.110 [0.0966, 0.1245]** (n = 3,201 / 398), which decides E4.3;
the **cross-sectional drawdown share** (mean 0.236, p90 0.480, max 0.890 over 417 names), which E4.8 needs; and
a **corrected run-up calm reference** — E3.3's window sits at a post-crash trough (sd 0.0413 against the
drawdown family's 0.0217), so the bubble-side multipliers were expressed against a denominator describing
neither population.

**LPPLS**, 3,125 of 3,202 run-ups converged over 398 stocks at 20 restarts each: median m **0.926 [0.900,
0.953]**, ω 4.81 [4.67, 4.97], R² 0.931, **stable share 0.329 [0.313, 0.344]**.

### 3.3 E4.2 — the schedule, and the rise time (criterion NOT MET)

Three arms at the same 500 crash seeds, measured with the same `rise_decay` estimator used on the panel and on
the **matched population** (≥ 30 % depth, duration ≤ 126 d):

| arm | rise median | 95 % CI | overlaps [29, 35] | duration | rejection |
|---|---|---|---|---|---|
| v2 (stipulated uniforms) | 70.0 | [65, 74] | no | 82 | 0.000 |
| v2.1 FIT interval, **uniform** shape | 65.0 | [62, 71] | no | 81 | 0.014 |
| v2.1 FIT interval, **empirical** shape | **58.0** | [52, 64] | **no** | 76 | 0.040 |

**The criterion is NOT MET and is not relaxed.** What binds is not the deterioration length:

| arm | corr(onset lag, rise) | corr(det_len, rise) | corr(panic_len, rise) |
|---|---|---|---|
| v2 | 0.737 | 0.109 | 0.153 |
| v2.1 empirical | **0.684** | **0.140** | 0.121 |

The episode's running peak falls a median of **38 days before** the scripted event, so ordinary calm-phase
noise dates the onset. Conditioning on where the onset falls:

| onset lag before the event | n | rise median | duration median |
|---|---|---|---|
| ≤ 0 | **167** | **32.0** | **54.0** |
| 0–10 | 36 | 47.0 | 74.5 |
| 10–30 | 77 | 63.0 | 72.0 |
| > 30 | 100 | 88.5 | 101.5 |

On the third of paths whose onset coincides with the scripted event the generator reproduces the panel almost
exactly — rise **32 d** against 30 [29, 35], duration **54 d** against 53. **The schedule is right; the
pre-event calm setup is what inflates the measurement.** `setup_len` is E4.7's parameter, and the rise-time
question is handed there. Phase 3's diagnosis ("the deterioration length plus the panic build-up") is corrected:
it is `schedule.py`, but through `setup_len`, not `det_len`.

Truncation forced by T = 200: `panic_len` on 8.2 % of draws, `setup_len` and `det_len` on 0.0 %.

### 3.4 E4.3 — the hazard (REG-18 decided, uniquely)

The panel's topped share makes REG-18's rule decidable (n = 3,201 ≫ its 30-episode fallback threshold).

| mapping | b | h0 | topped share | 95 % CI | inside the panel's [0.0966, 0.1245] |
|---|---|---|---|---|---|
| **A — no horizon scaling** | 5.419 | 6.712e-04 | **0.108** | [0.081, 0.135] | **YES** |
| B — scaled ×0.5 / ×1 / ×2 | 5.419 | — | 0.022 / 0.034 / 0.048 | — | no |
| C — panel-fitted | 1.074 | 6.416e-04 | 0.036 | [0.020, 0.052] | no |
| v2 incumbent | 6.0 | 3.0e-04 | 0.064 | [0.043, 0.085] | no |

**Mapping A was adopted** as the unique qualifying arm on this measurement — **and that adoption is
withdrawn in section 8.3**: the measurement was taken before `events.json` existed, and on the deployed state
the topped share is 0.008 [0.002, 0.016]. The entry is now INCUMBENT. The **40–60 % topped band and the P/V 1.6–2.5 band are
retired as targets**; peak P/V is reported as an outcome (median 1.49–1.50, unchanged across arms). `h0` is
solved from a hazard-off pilot, not stipulated; the calibration tool's arbitrary score and rejection penalty
are not used.

A measured fact for REG-18's transfer assumption: the industry-level slope (5.419) is **5.1× steeper** than the
single-stock one (1.074). Mapping C under-fires because the generator's manias reach a peak run-up of 1.63×
where the panel's run-ups reach 2.23×.

### 3.5 E4.4 — the mania drift (registered route unsupported)

The registered trigger fails: **stable share 0.329 [0.313, 0.344]** against the required ≥ 0.50. The m clause
passes (0.926 [0.900, 0.953], excluding 1.0) but sits close to the exponential boundary. The registered
fallback — the scripted drift with its shape FIT from the run-up table — returns **κ = 0**: the panel's run-ups
**decelerate**, with a median last-third-to-first-third log-gain ratio of **0.665** over 2,937 run-ups.

Two independent measurements therefore contradict a super-exponential mania. **κ = 0 is reported, not
applied**: the run-up definition selects on a local maximum at the top, which mechanically flattens the final
segment, and that selection must be settled before adopting a value that changes what the bull-trap scenario
is. Amendment **A5** is revisited on this evidence — the cap cannot be retired on the LPPLS route because the
route is unsupported, and under κ = 0 it is "unnecessary" only because nothing compounds.

### 3.6 E4.5 — the control (all four audited, none adopted)

500 seeds per definition, generated with rejection **off** so accepted and rejected populations are both
observable — v2's internal retry loop hid the rejected paths that the selection audit needs.

| definition | rejection | sd(x) | path-mean x P10/P50/P90 | KS sd_r | KS IV | classifier | null p95 | at chance |
|---|---|---|---|---|---|---|---|---|
| A | 0.162 | 0.0467 | −0.040 / 0.004 / 0.040 | 0.081 | 0.187 | 0.5360 | 0.5390 | yes |
| B | 0.162 | 0.0467 | −0.040 / 0.004 / 0.040 | 0.081 | 0.187 | 0.5360 | 0.5390 | yes |
| **C (incumbent)** | 0.358 | 0.0234 | −0.007 / 0.001 / 0.007 | **0.474** | **0.434** | 0.6058 | 0.6065 | yes |
| D | 0.162 | 0.0467 | −0.040 / 0.004 / 0.040 | 0.081 | 0.187 | 0.5360 | 0.5390 | yes |

**The substantive finding**: the anchored incumbent C selects massively on volatility and IV; A/B/D barely do.
That is weakness items 18 and 42, measured.

**The registered equivalence bound is UNDECIDABLE at these rejection counts.** Two samples drawn from the
*same* distribution at n = 419/81 give a bootstrap 95 % upper limit of **0.200** (0.157 at C's 321/179), so the
0.10 bound could not be met by any result. The remedy is more seeds, and the required count was **measured, not extrapolated** (section 8.4, T4):
about **4,000** seeds, not the 2,000 first stated. The comparison between definitions carries the finding.

The discrimination null **refits the classifier** on each permuted seed labelling rather than shortcutting to
the majority rule; all four definitions are at chance.

The stipulated `V_T/V_1 ≥ 1.2` threshold has a FIT replacement of **1.3233** (P10 of the 200-day-equivalent
growth of 2,849 non-crashing run-ups), recorded but **not applied** while the definition itself is undecided.

**D14 is open, so no definition is adopted.** `test_sustained_bull_selection` ends this phase **re-registered**
with its owner (the team, via D14) and its reason on the test itself.

### 3.7 E4.6 — event dynamics (all four run; STOP for D5)

1,000 crash and 1,000 bull seeds per formulation, on the Kaggle kernel after its reference-row guard passed at
a worst relative difference of **0.0**.

| formulation | script share | coverage | 95 % CI | rejection crash / bull | rise | depth |
|---|---|---|---|---|---|---|
| A, λ = 0.02 | 0.047 | 0.474 | [0.439, 0.509] | 0.061 / 0.113 | 60 | −0.523 |
| A, λ = 0.05 | 0.062 | 0.480 | [0.445, 0.515] | 0.044 / 0.113 | 59 | −0.522 |
| A, λ = 0.10 | 0.080 | 0.520 | [0.485, 0.555] | 0.027 / 0.113 | 59 | −0.514 |
| A, λ = 0.25 | 0.130 | **0.562** | [0.527, 0.597] | 0.012 / 0.113 | 58 | −0.509 |
| B — shifted p* | 0.039 | 0.521 | [0.486, 0.556] | 0.126 / 0.113 | 60 | −0.501 |
| C — scripted, no feedback | **0.014** | 0.462 | [0.427, 0.496] | 0.086 / 0.113 | 56 | −0.528 |
| D — unscripted regime | 0.030 | 0.323 | [0.288, 0.359] | 0.048 / 0.113 | 57 | −0.558 |

**No formulation qualifies; the phase stops for D5.** Rejection is below the ceiling (0.357) everywhere, so
coverage alone binds, and no arm's CI straddles 0.70 at this n.

**The rule's premise is arithmetically wrong** (addendum §4). REG-8 justifies the 0.70 threshold as a margin
below "0.80 by construction", but a P10–P90 box on *two* quantities captures ≈ 0.64, and **the panel's own
self-coverage is 0.643** (n = 642). The registered rule asks the generator to beat the panel by 6 pp. Phase 4
reports the verdict and the arithmetic and does **not** set a corrected threshold: that is a DESIGN margin and
it belongs with D5.

The script share is measured from the **recorded** drift (`PathResult.drift`) after the first implementation
was found to be regressing on a reconstruction that cannot represent B or D. Its validity check is that it is
now monotone in λ (0.047 → 0.130), which a mis-specified regressor was not.

### 3.8 E4.8 — the labels and the small fixes

**Blow-off.** Under the ex-post arm the driver sees **zero** blow-off days on every path — the dead-code defect
measured directly rather than inferred. The dynamic criterion (drift `g` above a FIT threshold of **0.00984
[0.00590, 0.02080]**, from 3,202 run-ups) puts the label on the path the driver produces: 100 % of paths,
median 62 blow-off days. Two things are recorded rather than claimed: `volatility.json` carries blow-off at
mania's value (1.345) where `e3_4/calibration.json` records 9.318, and **Phase 3's own label discloses this**;
and with the label alive the realised blow-off/mania ratio is **0.984** against the panel's **1.289**, so the
multiplier still needs its closed loop re-run.

**Post-top.** Phase 3 measured the linear leg as drift-dominated, flooring at 1.59 (n = 20). The decay shape
removes the floor; searched over half-lives 5–160 d at 400 seeds each, **half-life 50 realised 0.6186** against the panel's **0.6225** on the corrected reference — **on the v2
schedule.** On the deployed state that setting realises 0.860 and the half-life was re-searched with
`post_top_drop` and `post_top_len` now FIT (section 8.2); Phase 3's drift-dominated floor of 1.59 is broken
under every setting tested, which is the part that stands.

**Top day.** `top_day_realised` is recorded beside the hazard firing; the offset is non-zero on **89 %** of
topped paths, median **−2 days**.

**Multi-asset.** The FIT common-factor loading is **0.236** (p90 0.480, max 0.890). v2's realised loading was
stated as 1.0 from reading the code; **measured** (section 8.4, T7) it is **0.364**.
The value is fitted; at the end of the main pass **the replacement mechanism was not implemented**.
*Superseded by section 9.3:* it is now implemented and switchable but **NOT ADOPTED**, and the loading
was re-measured at 60 seeds as **0.3998 [0.3666, 0.4329]** — T7's 0.364 was a different design and the
two are not the same estimate. `events.json`'s `multi_asset` entry carries the corrected label.

### 3.9 The state handed over

- v2 behaviour is bit-identical behind every switch: the 12-path digest is `f37972fbce86ee4f2a34ccbd` under
  `schedule_mode="v2"` after each of the five code changes, matching HEAD.
- With `events.json` applied the digest is `19d23eeebcd53984ee693626` and the 95-configuration path hashes show
  **1,288 non-analyst column changes**.
- Freeze manifest rewritten: 25 files, hash `5e392f3d…`. *Superseded twice since:* the verification pass
  re-froze to `3473b174…` and the completion pass to **`869e4fbf4b6e64ba…`** (section 9.11), always at
  25 files.
- Checklist regenerated at 200 seeds on the Phase-4 state: **5 pass / 10 fail / 5 n/a** (`e4_after_checklist.md`).
- Tests against the handed-over state: `test_v2_1_phase_4.py` **12 passed, 1 xfailed**; `test_v2_1_phase_{1,2,3}`
  + `test_v2_1_stats` + `test_provenance_and_freeze` **34 passed, 1 xfailed** (3:51), so the event block has not
  broken Phases 1–3. The one xfail is `test_sustained_bull_selection`, re-registered with its new owner (D14)
  and its evidence in `tests/known_defects.py`.

**After the completion pass**, re-verified: `test_v2_1_phase_4.py` + `test_provenance_and_freeze.py`
**24 passed, 1 xfailed**; `test_v2_1_phase_{1,2,3}` + `test_v2_1_stats` **26 passed, 1 xfailed** — the
same 34 + 1 as above. No parameter *value* changed in the pass: the only edits to `events.json` were
two stale provenance **labels** (`calendar` still said the quarter randomisation was NOT DONE while its
value was `true`; `multi_asset` still said "not implemented"), applied under an assertion that every
`value` block stayed byte-identical, and mirrored in `tools/phase4/apply_e4.py` so a regeneration
reproduces them.

Of the four checklist items that are Phase 4's:

| item | Phase 3 | Phase 4 | reading |
|---|---|---|---|
| 8 — gain/loss asymmetry in crash | skew −0.001, worst>best 50 % | skew −0.004, worst>best 48 % | unchanged FAIL |
| 10 — delta matters | partial R² 0.29, spread 12.6 pp | **partial R² 0.00, spread 0.0 pp** | **worse, and now structurally inert — see §5** |
| 11 — bubble | topped 8 %, P/V 1.49, convex 46 % | topped **15 %**, P/V 1.48, convex 46 % | topped moves toward the panel's 11 % |
| 17 — conditioning | SB 32.9 %, bull-trap 10.7 %, crash 0.8 % | SB 32.9 %, bull-trap 13.0 %, crash 3.8 % | SB unchanged — definition C is still in force because D14 is open |

---

## 4. Decisions taken and the parameter file

`envs/v2/params/events.json`, written by `tools/phase4/apply_e4.py`, read by `envs/v2/events_params.py` (a loud
loader that raises on a missing entry **or a null interval**). Every entry carries label / source / date /
interval / n, states what the fit is conditional on, and is tagged **ADOPTED**, **INCUMBENT** or **NOT DONE**.

| entry | status | value |
|---|---|---|
| `schedule_ranges` | ADOPTED | FIT empirical quantile grids for det_len / panic_len / front_load / depth / rec60, sampled by inverse CDF; **`depth_mode="centred"`** (P4-40) so the draw tracks the `crash_discount` arm factor |
| `hazard` | **IN FORCE, ADOPTION WITHDRAWN** | mapping A, b 5.419, h0 6.712e-04 — adoption **WITHDRAWN** (P4-7); in force pending REG-18's re-expression (P4-39) |
| `blowoff` | ADOPTED | dynamic, g threshold 0.00984, **multiplier 2.0764 CALIBRATED** (realised 1.3136, panel 1.2895) |
| `post_top` | ADOPTED | decay, **half-life 40.0** (re-fitted at 1500 seeds; the 10 adopted at 400 seeds was noise) |
| `calendar` | ADOPTED | day_n (D6); three renderings behind the switch; eps quarter grid randomised per seed |
| `control` | ADOPTED | **A** — D14 TAKEN (P4-43). C selected on the hidden state (KS 0.4404 vs its own null floor 0.1024); A is below its floor. **Weakness items 18 and 42 CLOSED**, and sustained-bull coverage rose 0.044 → 0.374 (P4-46) |
| `dynamics` | **INCUMBENT** | A at λ 0.10 — D5 still open; **both halves of its adoption rule are unusable** (§9.12, §9.13) |
| `crash_v_drift` | **TESTED, REJECTED** | v2 flat-after-deterioration in force while its central claim is **rejected**: 0.000 [0.000, 0.000] of the decline falls in deterioration where v2 puts 100 %; magnitude not identified, so no value adopted |
| `multi_asset` | **TESTED, NOT ADOPTED** | loading 0.2365 FIT; mechanism implemented and switchable, refuted three ways (realised 0.3998; per-asset draws move it 0.0003), not adopted |
| `mania_drift` | **TESTED, NOT ADOPTED** | κ = 0 **tested and blocked** (P4-44): the deceleration evidence stands, but κ = 0 makes the bull trap **96.3 % rejected** — it needs the stipulated `x.max() >= 0.30` criterion re-expressed jointly |

**This table is generated from `envs/v2/params/events.json` as deployed, not written by hand.**
It has been regenerated after each adoption; the version before D14 showed `control` as INCUMBENT C.
Statuses above are read from the file, so they cannot drift from it.

Decisions **P4-1 … P4-46** are in `docs/env_v2/decisions/DECISION_LOG.md`, each with the alternative rejected and
the evidence file that decided it.

---

## 5. Decisions the team must take

1. **D5 — event dynamics.** No formulation meets the registered coverage rule, and the rule's own premise is
   arithmetically wrong: it asks the generator to beat the panel's self-coverage of 0.643 by 6 pp. The team
   needs to set the corrected margin (Phase 4 will not set it after seeing the table) and then the adoption
   rule picks: at any margin ≤ 0.462 the lowest script share is **C** (0.014); at a margin between 0.47 and
   0.52 it is **B** (0.039); at 0.56 it is **A at λ 0.25** (0.130). `e4_6/dynamics.md`.
2. **D14 — the sustained-bull control.** All four definitions are audited. C selects hard (KS 0.474 on daily
   sd, 0.434 on IV); A/B/D do not (0.081, 0.187). Adopting A, B or D closes weakness items 18 and 42 and lets
   `test_sustained_bull_selection` pass; keeping C keeps the scenario clock and the 32.9 % rejection. The
   audits cannot supply the *purpose*, which is what D14 is. `e4_5/control.md`.
3. **Checklist item 10 is now structurally inert, and that is a design question.** E4.2 draws `delta` from the
   panel's **depth** distribution, so the `crash_discount` arm factor no longer changes anything: the partial
   R² of delta falls from 0.29 to **0.00** and the 0.55-vs-0.85 spread from 12.6 pp to **0.0 pp**. Either
   severity stays a controlled factor (draw depth *around* `crash_discount`) or it becomes a random draw and
   item 10 is re-expressed — REG-8 already anticipated the re-expression for formulations B and D ("a statement
   about D_V and the belief shift, not about a target"). This is the largest single consequence of E4.2 and it
   needs a decision before Phase 6 re-derives the checklist criteria.
4. **κ = 0.** Two independent measurements contradict a super-exponential mania. Adopting κ = 0 would make the
   bull-trap a linear-drift run-up; not adopting it leaves a stipulated κ in a programme that forbids
   stipulated parameters. The blocking question was whether the deceleration is real or an artefact of
   defining a run-up by a local maximum at its top. **That experiment has since been run (section 8):
   re-dated on a rule that does not select on the endpoint, the deceleration is REAL and stronger — 0.342
   [0.318, 0.368] against the endpoint-selected 0.621.** The caveat that justified withholding κ = 0 is
   refuted, so what remains is purely the adoption decision, which is the team's.
5. **The rise time is not met, and the fix is E4.7's `setup_len`.** Shortening the calm setup would close most
   of the gap (the conditional result is 32 d), but `setup_len` is also what REG-9's day-only classifier
   constrains. **The joint experiment has since been run (section 9.1) and the trade-off does NOT bind:** the
   relationship is monotone across four arms, a 13-day median setup gives rise time **37.0 [34, 41]**, which
   meets [29, 35], and the day-only classifier stays below its own seed-permutation null at **every** setting.
   A setup range therefore exists that satisfies both criteria. It was **not written into `events.json`**,
   because a 13-day setup leaves far less pre-event baseline than the current 50–110 and changes what the
   benchmark's calm phase is — a design change the team owns, now with the measurement in hand.
6. **Two registered criteria were unmeetable.** E4.6's coverage threshold (above) and E4.5's KS equivalence
   bound (undecidable at n_rej = 81; the null floor is 0.200). Both need re-registering with the team before
   the phase that inherits them relies on them. **A third joins them from the verification pass:** REG-18's
   topped-share criterion is horizon-dominated and **not evaluable** on a 200-day scenario that must also
   contain the mania, so no hazard mapping can be adopted by it (section 8.3).
7. **The hazard's status word does not describe what is deployed (P4-39, section 9.11).** `hazard.json` holds
   v2's (h0 3e-4, b 6.0) and `events.json` holds E4.3's (h0 6.712e-4, b 5.419), which is what `GenConfig()`
   uses. The entry is marked `INCUMBENT`, whose own `_status_key` reads "the v2 behaviour stays" — but E4.3's
   value is in force, deliberately ("The values below stay in force as the INCUMBENT and the criterion needs
   re-expressing"). **No parameter was changed:** reverting would move a measured outcome (v2's hazard gives a
   topped share of 0.064, outside the panel CI). The team owns whether the vocabulary gains a term for "in
   force, adoption withdrawn" or the value reverts — it is tied to item 6's REG-18 re-expression.

### 5.1 Phase 4's recommendations — and what happened when they were acted on

**Status, 6 Sep 2026.** The team authorised acting on these under the standing rule that nothing may rest on
inference. Each was tested before it was acted on, and **three did not survive their own test**:

| item | recommendation | outcome |
|---|---|---|
| 1 — D5 | adopt B | **reasoning refuted, not adopted.** The metric is not monotone in scriptedness and coverage is blocked by a depth floor set outside the event block (§9.12, §9.13). Both halves of the rule are unusable |
| 2 — D14 | adopt A | **ADOPTED** (P4-43). Weakness items 18 and 42 closed; both xfails removed |
| 3 — item 10 | draw depth around `crash_discount` | **ADOPTED** (P4-40). Spread 0.0000 → −0.0814, inert at the deployed δ |
| 4 — κ = 0 | adopt it | **REFUTED** (P4-44). It makes the bull trap 96 % rejected |
| 5 — setup range | re-express window-matched | **premise partly refuted** — the family is already window-matched (§9.12); not done |
| 6 — three criteria | re-register together | **done for two** (§9.12): the coverage premise is refuted, the KS bound is costed at n_rej ≈ 400 |
| 7 — hazard status | add the term | **ADOPTED** (P4-39b), and the loader now enforces the vocabulary |

The original text follows, corrected in place where a test overturned it.


The pre-registration forbids this phase from taking these decisions, and none is taken. What follows is a
recommendation per item with the evidence behind it, so the team is choosing against a position rather than
from a blank page. Where the evidence does not settle it, that is said.

**1. D5 — adopt B (shifted p\*), but fix item 3 first.** *This item was rewritten after E4.19 tested the
claims it originally rested on (section 9.12). The original argument was wrong; the conclusion survives on
different evidence, and the sequencing changed.*

What was claimed and what the test found:

- *Claimed:* the ranking metric has a noise floor, so B and C are indistinguishable from unscripted.
  **REFUTED** — with intervals, every arm separates from the unscripted arm D.
- *Claimed:* correcting the 0.70 threshold to the panel's self-coverage still rejects every arm.
  **CONFIRMED** — the best arm reaches 0.562 [0.527, 0.597] against the panel's 0.6433 [0.6074, 0.6791],
  significantly below.
- *Claimed (item 6):* these targets were adopted without checking the generator could express them.
  **REFUTED for coverage** — `dd30_fast` is already restricted to the episodes that fit a 200-day horizon.

The test also found a defect worse than the one alleged: **C, which is fully scripted with no feedback, scores
significantly BELOW the arm that has no script at all** (−0.0162 [−0.0185, −0.0140]). The metric is not
monotone in scriptedness, so "adopt the lowest script share" is not a rule that can be applied — it would
prefer a fully scripted formulation *because* it is scripted. The rule needs replacing, not re-thresholding.

On the corrected evidence the choice still lands on **B**, by pairwise tests rather than by eye: **D is
eliminated** (worst coverage against every arm, and 32.3 % of its paths have no measurable episode at all);
**A at λ 0.25 is dominated** — its coverage advantage over B is **not** significant (+0.0410 [−0.0130,
+0.0903]) while its script share is the highest of all seven and separable from every other arm; **C is beaten
by B on coverage** (+0.0594 [+0.0115, +0.1068], separable), which is the part of my original argument that was
wrong — I called them tied. B ties the best coverage arms (A at λ 0.1: −0.0013 [−0.0501, +0.0488]) at a
quarter of A at λ 0.25's script share.

**But do item 3 first.** The coverage shortfall is a **depth** problem in every arm — depth-only failure runs
4–7× duration-only failure — and depth is exactly what item 3 is about. D5 and item 3 are one problem, not
two, and the arm ranking may move once the depth draw is fixed. Adopting a formulation against a coverage
statistic that is dominated by a known-broken depth draw is deciding on evidence that is about to change.

**2. D14 — adopt A, B or D; do not keep C.** This is the one item where the measurement is unambiguous about
the *mechanism* even though it cannot supply the *purpose*: C selects on the hidden state (accepted-vs-rejected
KS 0.474 on daily sd, 0.434 on IV) where A/B/D do not (0.081, 0.187), because C carries an x-band and they do
not. A control that selects on x is a control that leaks x, which is the thing the benchmark exists to hide.
The counter-argument — C preserves the scenario clock and the 32.9 % rejection — is a statement about
convenience, not about validity. **Recommend A**, the simplest of the three, unless the team wants the
sustained-bull scenario to retain a specific rejection rate, in which case B. Note the registered KS
equivalence bound is undecidable at n_rej = 81 (null floor 0.200), so this rests on the *comparison* between
definitions, which is large and consistent, not on the bound.

**3. Checklist item 10 — make severity a controlled factor again.** `delta`'s effect is now **exactly zero**
(identical drawdown to full float precision), so the `crash_discount` arm factor is dead. Of the two routes
REG-8 anticipates, **draw the depth *around* `crash_discount` rather than replacing it** — centre the panel's
empirical depth distribution on the arm's severity instead of sampling it unconditionally. That keeps E4.2's
fitted dispersion (the reason the change was made) *and* restores the factor, where re-expressing item 10
merely accepts the loss. This is the largest single consequence of E4.2 and it should be settled before
Phase 6 re-derives the checklist criteria.

**4. κ = 0 — adopt it.** Both measurements say the mania decelerates, and the objection that justified
withholding it has been tested and refuted: removing the endpoint selection makes the deceleration *stronger*
(0.342 [0.318, 0.368] against the endpoint-selected 0.621), not weaker. Keeping a stipulated κ in a programme
whose governing rule forbids stipulated parameters needs a reason, and there is no longer one on the evidence.
The cost is real and should be stated plainly: the bull-trap becomes a linear-drift run-up, which is a less
dramatic scenario. That is a consequence to accept, not a reason to keep an unsupported parameter.

**5. The setup range — do not adopt 13 days; re-express the rise-time criterion instead.** The experiment
succeeded: 13 d gives rise time 37.0 [34, 41], meeting [29, 35], with the day-only classifier below its null at
every setting. But the criterion it satisfies was fitted on panel episodes with no constraint that the run-up
fit inside a 200-day window, and a 13-day setup leaves almost no pre-event baseline — the calm phase is what
the benchmark measures conformity *against*. This is the same horizon problem that made REG-18 unevaluable
(item 6): a 200-day scenario that must contain setup, event and resolution cannot also reproduce a panel
statistic estimated on unconstrained windows. **Recommend re-expressing the rise-time target
window-matched**, exactly as E4.12 did for the topped share, before trading away the calm baseline to hit a
number the horizon may not admit.

**6. The unmeetable criteria — re-register all three together, window-matched.** E4.6's coverage threshold,
E4.5's KS bound and REG-18's topped share failed for three different reasons (a wrong premise, absent power, a
dominated horizon), but all three share one root: **a panel statistic was adopted as a generator target
without checking the generator could express it on a 200-day window.** Recommend a single re-registration pass
that, for each inherited target, states the window it was estimated on and the window the generator has — and
rejects any target where those differ without a matched comparison. That is one piece of work, not three, and
it is cheaper than discovering the next one the way these three were discovered.

**7. The hazard status (P4-39) — add the vocabulary term; do not revert the value.** Reverting to v2's hazard
to satisfy a status word would change the generator on a labelling technicality and move a measured outcome
in the wrong direction (v2's gives a topped share of 0.064, outside the panel CI, against E4.3's 0.108).
**Recommend adding a status term** — "IN FORCE, ADOPTION WITHDRAWN" — for a value that is deployed on evidence
that no longer supports *adoption* but is still better than the alternative on the measured outcome. Phase 4
needed that term three times (`hazard`, `crash_v_drift`, `multi_asset`) and had it none of them, which is why
the labels drifted from the values. Tie the resolution to item 6's REG-18 re-expression, since the criterion
that would settle the adoption is the one being re-expressed.

**Order of work — revised by E4.19.** The original advice was "item 6 first". E4.19 ran item 6's analysis
and found its premise refuted for the coverage criterion, so the order is now: **item 3 first** (the depth
draw), because it is the lever behind both the dead `crash_discount` factor *and* the coverage shortfall;
then re-run E4.6 and decide **item 1** on the new table; then items 2, 4 and 7, which are independent of the
depth draw. Item 5's rise-time re-expression and item 6's KS re-registration are now costed rather than
open — see section 9.12.

---

## 6. Files written or changed

Nothing committed; everything is in the working tree on `main`. `docs/` and `datasets/` are git-ignored by
design. The complete list, with what each file is, is `PHASE_4_CHANGED_FILES.md`.

---

## 7. What was not done, and who owns it

| Not done | Why | Owner |
|---|---|---|
| **E4.7's day-only classifier audit** and the ordering-mix sweep | The renderings and the ordering factor are implemented and tested; the 200-seed classifier audit against the permutation null was not run | Phase 4 re-open — it is the experiment that also settles the rise time (§5.5) |
| The **quarter-phase randomisation** of `days_since_eps_announcement` | not implemented | Phase 4 re-open |
| **The SEP level-free leakage audit** (≈ 2.5 h), **L5** (≈ 1 h), and the **re-run discrimination and decomposition** tables | Budget. These are the diagnostics that would say whether the event redesign moved the benchmark's discriminating power or its leakage — and the event-phase channel is the one this phase changed, so they matter | Phase 4 re-open, before Phase 6 |
| **The crash V-drift shape test** (item 73) | Needs the EDGAR value proxy through each episode (monthly, 2009+); the mechanism is implemented and switchable but untested | Phase 4 re-open or Phase 5 |
| **The multi-asset per-asset event draws** | The loading is FIT (0.236); the mechanism is not implemented | Phase 4 re-open |
| **The blow-off multiplier's closed loop** | The label now reaches the driver, but the multiplier still sits at mania's value, so the realised ratio is 0.984 against the panel's 1.289 | Phase 4 re-open — one calibration run |
| The **remainder of the test suite** (the ≈ 51 min full run) | Run against the Phase-4 state and passing: `test_v2_1_phase_4.py` (**12 passed, 1 xfailed**) and `test_v2_1_phase_{1,2,3}.py` + `test_v2_1_stats.py` + `test_provenance_and_freeze.py` (**34 passed, 1 xfailed in 3:51**) — so the Phase-4 block has not broken Phases 1–3, and the freeze manifest verifies. **Not** run: the leakage-CI, eval, render-prompt, docs-numbers and stateful/multi-asset suites | Phase 4 re-open, before hand-over is accepted |

**Status after the completion pass (section 9).** Every row above except the last has since been executed;
the table is left as written because it recorded the state at the end of the main pass. Dispositions:
E4.7's classifier audit and ordering sweep -> section 9.1 and 9.4; the quarter-phase randomisation ->
section 9.2 (implemented, adopted, proved inert when off); the SEP audit -> section 9.5; L5, discrimination
and decomposition -> section 9.8; the crash V-drift test -> section 9.7 (**rejected in direction**); the
multi-asset per-asset draws -> section 9.3 (implemented, **not adopted**); the blow-off closed loop ->
section 9.6 (**calibrated**, 2.0764). The last row is now closed too: the leakage-CI, eval,
render-prompt, docs-numbers and stateful/multi-asset suites were run and **all pass** --
`test_eval_v2` + `test_render_prompt_frozen` + `test_docs_numbers` + `test_stateful_multiasset`
**23 passed** (3:07), and `test_leakage_ci` **7 passed, 4 xfailed** (15:01). The four xfails are exactly
the registered known defects -- two permanent v1 baselines and the two v2 gates owned by Phase 6
(`test_v2_L2_surrogate_thresholds`, `test_v2_L2b_phase_clock_selectivity`) -- so nothing failed
unexpectedly. **Section 7 has no open rows left.**

**Where that 15 minutes goes, measured.** `--durations` attributes 874 s of the 901 s to two fixture
setups (`v2_audit` 657.8 s, `v1_audit` 216.5 s); all eleven tests' assertions together cost ~18 s. The
suite is **already scoped small** -- `N_SEEDS_CI = 8`, `T_CI = 200`, roughly 6 400 rows, and both
fixtures are `scope="module"` so each audit runs once rather than per test. The cost is inside
`run_audit`, which fits 2 feature sets x 3 models x 2 targets plus the shuffled-V control and the two
classifiers, each over 5 sequential GroupKFold folds (`leakage_audit.py:232-237`). Those folds and fits
are independent and joblib is installed, so the available win is **inside** the audit, not in pytest:
`pytest-xdist` is not installed here, and even with it the module-scoped fixtures would only let the v1
and v2 audits overlap (874 s -> ~658 s, about 1.4x) while risking exactly the oversubscription the
module's own comment warns about. Parallelising the folds is a change to `evaluation/`, which is frozen
and outside this phase's remit -- recorded here as a costed hand-off, not made.

**One incident, recorded.** `tools/phase3/after_state.py` hardcodes Phase-3 output names, so running its
checklist stage overwrote `e3_after_checklist.{md,csv}` with Phase-4 numbers. The Phase-4 result was copied to
`e4_after_checklist.{md,csv}` and the Phase-3 file was regenerated by removing `events.json` and re-running,
which reproduces it because the v2 path is bit-identical. The brief warned to point the tool at Phase-4 output
names and this pass did not; the tool still hardcodes them and should be parameterised before Phase 5 uses it.

---

## 8. Verification pass: testing the phase's own claims

Every quantitative statement in sections 1–7 was audited and split into *measured* (backed by a generated
file) and *inferred* (reasoning **about** one). The inferred ones were then tested, each against a stated
falsifier (`e4_10/verify.json`, `e4_9/deployed.json`, `e4_11/posttop_recal.json`, `e4_12/horizon.json`).

Four of them survived. **Four did not, and one of the failures invalidated two adopted parameters.**

### 8.1 The ordering defect — three results measured on a state that did not yet exist

A timestamp audit found that `events.json` was written at 14:47:39 while `e4_3/hazard.json` (14:18),
`e4_5/control.json` (14:41) and `e4_8/labels.json` (14:45) all predate it — and none of those three tools pins
`schedule_mode`, so all three ran under the **v2** schedule and were then quoted as deployed properties. The
Phase-4 checklist had already contradicted one instance (topped 15 % deployed vs 0.108 calibrated) and section
3.9 explained it away as "a different seed block" **without testing that explanation**.

Re-measured on the deployed state at 500 seeds per scenario (`e4_9`):

| quantity | as calibrated | deployed | panel | verdict |
|---|---|---|---|---|
| topped share | 0.108 | **0.008 [0.002, 0.016]** | 0.110 [0.097, 0.124] | **does not hold** |
| post-top / mania | 0.6186 | **0.860 [0.641, 1.169]**, n = 79 | 0.6225 [0.599, 0.648] | **does not hold** |
| crash rise | 58.0 [52, 64] | 60.0 [55, 65] | 30 [29, 35] | holds; criterion still NOT MET |
| control C rejection / KS(sd) | 0.358 / 0.474 | 0.336 / 0.408 | — | holds in direction and size |

### 8.2 The cause: two parameters left stipulated in Phase 4's own parameter file

The hazard is not what fails — it **fires** on 0.19 of deployed paths. What collapses is the drawdown after
the top, because `post_top_drop` (U(0.30, 0.50)) and `post_top_len` (U(10, 30)) shipped as **v2 DESIGN ranges
while the panel holds the data for both**: |post-drop| P10/P50/P90 = 0.061 / 0.169 / 0.414 and post-length
8 / 60 / 187 d (n = 3,201 / 398). Both are now FIT by the same inverse-CDF sampler (`e4_11`), and the half-life re-searched on the deployed
state at **1,500 seeds per arm**: half-lives 30–100 all put the post-top/mania ratio inside the panel's
[0.599, 0.648], and **hl 40 is adopted** at **0.6216** against the panel's 0.6225. A first pass of the same
search at 400 seeds put hl **10** inside at 0.617 and everything else outside; at 1,500 seeds hl 10 measures
**0.730** and is outside. The 400-seed result was sampling noise, and the only reason it was not adopted is
that the search was re-run before the parameter file was written.

### 8.3 Why the topped share still cannot be met — tested, not asserted

The obvious reading (the drop is too shallow) is refuted by the generator's own realised drop, **P50 −0.239,
deeper than the panel's median −0.169**. The hypothesis tested instead was the horizon, with a window-matched
falsifier (`e4_12`, 600 seeds):

| post-top days available | generator | panel, same restriction | CIs overlap |
|---|---|---|---|
| 0–50 | 0.0250 [0, 0.063] (n = 80) | 0.0294 [0, 0.088] (n = 34) | **yes** |
| 50–100 | 0.0769 [0, 0.192] (n = 26) | 0.0357 [0, 0.107] (n = 28) | **yes** |
| 150–201 | *no generator paths* | **0.1124 [0.101, 0.124]** (n = 3,115) | — |

**Within every window the two populations share, the generator agrees with the panel.** The panel's 0.110
comes from run-ups with a 150–200 day post-top window; only **0.9 %** of generated topped paths have even 120
days left, median **29**. REG-18's criterion is dominated by remaining horizon, not by the hazard, so it
cannot discriminate between mappings on a 200-day horizon that must also contain the mania.

**Consequence: P4-7's adoption is withdrawn.** The hazard entry moves from ADOPTED to **INCUMBENT** with the
same values in force and the withdrawal on the entry. E4.3's apparent success was an artefact of the v2 leg
forcing a 30–50 % drop into 10–30 days.

### 8.4 The other claims tested

| # | claim | verdict |
|---|---|---|
| **T1** | the panel's run-ups decelerate, so a super-exponential mania is contradicted (§3.5) | **STANDS, and my caveat was wrong.** Removing the endpoint constraint makes the deceleration *stronger*: original 0.621 → top−21 d 0.406 → top−42 d 0.358 → **end not selected on price at all 0.342 [0.318, 0.368]** (n = 3,186 / 398). The reason given for withholding κ = 0 does not survive its own test. |
| **T3** | item 10 is inert *because* E4.2 draws delta from the panel's depth (§3.9) | **CONFIRMED.** v2: partial R² 0.229, spread −11.5 pp, corr(crash_discount, delta drawn) = **1.000**. v21: partial R² −0.000, spread 0.00, corr = **0.000**. |
| **T4** | "about 2,000 seeds" would make E4.5's KS bound decidable (§3.6) | **WRONG, corrected.** Measured floor: n_rej 81 → 0.211; 162 → 0.145; 324 → **0.103**; 648 → 0.075. The bound becomes attainable at about **4,000 seeds**, not 2,000. |
| **T5** | the deployed excess is the benchmark's scenario mix (§3.1) | **INCOMPLETE, corrected.** Panel-weighted, calm carries 62.2 % of the variance on 78.4 % of the days, but **post-top carries 12.1 % on 7.2 %** — the largest disproportionate contributor, and precisely the leg §8.2 re-fits. The residual is the mix **plus** a named, now-corrected level error. |
| **T6** | adopting A/B/D closes weakness items 18 and 42 (§5.2) | **NOT ESTABLISHED at this n.** Against a null computed at each definition's own achieved n, every definition exceeds its p95 — but by 0.0042 for A/B/D against **0.0762 for C**, a factor of 18. At n_rejected = 44 the test has almost no power in either direction (T4: ~4,000 seeds needed). What is measured is that C's selection is an order of magnitude larger, and that A/B/D carry no x-band, so any residual is rejection on V growth. The first version of this test compared against a stipulated 0.20 and would have called every definition a selector — an unfounded threshold, replaced. |
| **T7** | v2's multi-asset extension implies a loading of 1.0 (§3.8) | **WRONG AS STATED, corrected.** Measured on 3-asset paths: realised cross-sectional drawdown share **0.364** (all three together on 0.202 of days) against the panel's 0.236. The direction stands — the generator's assets co-move more than the panel's — but 1.0 was read off the code, not measured. |
| **T8** | the 1.354 mean-vs-median RV ratio (§3.1) | **PERSISTED.** 1.3541 [1.3401, 1.3668], IQR [1.286, 1.452], n = 417 stocks, now in `e4_10/verify.json` rather than only in an unsaved session script. |

### 8.5 What this says about the method

Three of the five things the addendum documents were found by testing the phase's own reasoning, not by a new
experiment on the environment. The ordering defect in particular was invisible to every test in
`tests/test_v2_1_phase_4.py`, because those tests check that the deployed state matches the recorded values —
and both sides were consistent. What was wrong is that the recorded values had been measured somewhere else.

The guard is not a test but a discipline: **a tool that measures the generator must pin the configuration it
measures.** `e4_3`, `e4_5` and `e4_8` did not; `e4_9` now exists to re-measure the whole block on the deployed
state whenever the parameter file changes, and should be run as the last step of any future phase that writes
one.

---

## 9. Completion pass: the items section 7 listed as not done

Executed under the same rule as the rest of the phase — measured on the deployed state with `schedule_mode`
pinned, nothing claimed that is not tested. Tools: `e4_7_calendar.py`, `e4_13_blowoff_cal.py`,
`e4_14_crash_v.py`, `e4_15_multiasset.py`.

### 9.1 E4.7 — the setup range, and the rise time resolved

Section 3.3 recorded the rise-time criterion as NOT MET and section 8 noted that P4-6's identification of
`setup_len` as the binding lever rested on a **conditional** — the paths whose onset coincides with the event
give rise 32 d — which selects on an outcome and therefore cannot establish causation. E4.7 sweeps the cause
directly, at 200 crash seeds per arm, and measures at each setting **both** quantities the setup range trades
off between:

| median setup | rise time | 95 % CI | meets [29, 35] | day-only classifier | null p95 | acceptable |
|---|---|---|---|---|---|---|
| 58 d | 48.0 | [42, 52] | no | 0.7911 | 0.8005 | yes |
| 40 d | 44.0 | [39, 51] | no | 0.7996 | 0.8089 | yes |
| 26 d | 41.0 | [38, 45] | no | 0.8167 | 0.8241 | yes |
| **13 d** | **37.0** | **[34, 41]** | **yes** | 0.8425 | 0.8502 | yes |

The relationship is **monotone across all four arms**, so shortening the setup does cause the rise time to
fall — P4-6's inference is confirmed by experiment rather than by conditioning. And the trade-off REG-9 exists
to protect does **not** bind: the day-only macro-phase classifier is below its own seed-permutation null at
every setting, so a setup range exists that meets E4.2's criterion **and** stays at chance on the clock test.

**Not written into `events.json`.** A 13-day median setup leaves far less pre-event baseline than the current
50–110, which changes what the benchmark's calm phase is and how much history an agent sees before an event.
That is a design change with consequences beyond the rise time, so the value is reported with its measurement
and the decision is the team's.

### 9.2 E4.7 — `days_since_eps_announcement` does carry a clock

REG-9(c) asks for the quarter phase to be randomised per seed; the premise had never been measured. It is
now — and the first version of the test was invalid in a way worth recording, because it is the same class of
error as the ordering defect in section 8. It asked whether the field predicts the raw **day index**, with a
null that permuted **seed** labels, and returned R² exactly equal to its null (0.0363 against 0.0363). Every
path shares the same day axis, so permuting seeds cannot break a relation that is identical across seeds —
which is precisely the relation being tested for. The null was degenerate by construction.

Corrected statistic: accuracy at predicting which third of the quarter a day falls in, from the field value
alone, pooled across seeds, against a null that shuffles each path's field series **in time**.

| quarter grid | accuracy | null p95 | chance | carries a clock |
|---|---|---|---|---|
| v2, fixed across seeds | **0.8728** | 0.3627 | 0.333 | **yes** |
| randomised per seed (E4.7d) | **0.3958** | 0.3625 | 0.333 | marginally |

Randomising removes **93 %** of the excess over chance. It is adopted because it strictly dominates; the
3.3 pp residual is reported rather than explained away.

`envs/v2/observables.py` is under the freeze manifest, so the switch was proved inert when off:
`q_phase = 0` reproduces the committed `announcement_schedule` and `earnings_block` **exactly on 50 of 50**
random inputs, and `q_phase = 17` genuinely differs. `tests/test_v2_1_phase_4.py::test_quarter_phase_switch_preserves_v2`
locks both halves of that.

### 9.3 The multi-asset block — P4-16 refuted three ways

**Numbers corrected, and how the error was found.** This section first carried figures taken from the tool's
stdout, and `e4_15/multiasset.{json,md}` — the file it cited — **was never on disk**. That was noticed while
compiling the file list for `PHASE_4_CHANGED_FILES.md`: the directory did not exist. Re-running
`tools/phase4/e4_15_multiasset.py` produced the file and **different numbers** (crash 0.352 → 0.400, flat
0.042 → 0.053). The tool is deterministic — two independent runs agree on every arm to all digits — and
nothing it depends on changed: every file under `envs/` predates the tool's own mtime, and the 17:07 rewrite
of `events.json` leaves crash prices **bit-identical** (tested directly for `blowoff_mult`, `post_top_half_life`
and `blowoff_mode`). So the earlier figures cannot be reproduced by this tool and their provenance is unknown.
**The file-backed numbers below supersede them.** The three conclusions are unchanged; only the magnitudes move.

| configuration | co-drawdown share | 95 % CI | all three together |
|---|---|---|---|
| crash, v2 shared event | 0.3998 | [0.3666, 0.4329] | 0.2313 |
| crash, per-asset events at loading 1.0 | 0.3998 | [0.3666, 0.4329] | 0.2313 |
| crash, per-asset events at loading 0.5 | 0.4005 | [0.3696, 0.4313] | 0.2002 |
| crash, per-asset events at loading 0.0 | 0.4001 | [0.3724, 0.4269] | 0.1733 |
| crash, common fundamental factor removed | 0.3829 | [0.3535, 0.4138] | 0.1976 |
| **flat, no scripted event at all** | **0.0531** | [0.0352, 0.0722] | 0.0000 |
| panel, all days, 417 names | 0.2365 | p90 0.480, max 0.890 | — |

60 seeds per arm, 3 assets, 200 days, `schedule_mode` pinned to `v21`, 2000-resample bootstrap.

1. v2's realised loading is **not 1.0**; it is **0.3998 [0.3666, 0.4329]**.
2. The proposed fix **does not work**: per-asset draws move the mean share by **0.0003** (0.3998 → 0.4001 at
   loading 0.0), because every asset is in the same scenario and crashes whether or not it shares a schedule.
   The loading-1.0 arm reproduces the shared-event arm to **all sixteen digits**, which is the check that the
   mechanism is wired correctly — it is, and it still does not help. It does move *co-incidence*: all three
   assets are simultaneously in drawdown on 23.1 % of days when they share the event and 17.3 % when they do
   not, so the loading controls synchrony without controlling the marginal share it was named after.
3. The comparison was **not population-matched**: the panel's 0.2365 is an all-day mean over 417 names, the
   generator's 0.40 is conditional on a crash scenario. The panel's all-day mean sits between the generator's
   flat and crash arms, and the panel's p90 (0.480) is *above* the generator's crash arm.

The scripted event is what drives the co-movement (0.3998 against **0.0531** with no event, CIs far apart),
and the common fundamental factor is not (0.3829 without it, CI overlapping the shared-event arm). Matching
the panel would need **scenario heterogeneity across assets**, which is a design change to the multi-asset
extension and belongs with the Phase-9 multi-asset sensitivities. The mechanism ships implemented and
switchable, labelled **NOT ADOPTED**.

### 9.4 E4.7 — the orderings and the three renderings

REG-9's rule: within each scenario, the day-only macro-phase classifier's accuracy must be at or below the
95th percentile of a **seed**-label permutation null, plus 1 pp. 200 seeds per arm, 200 permutations, the
classifier refitted on each permutation. Permuting *day* labels instead would give a null of about 0.503 and
call almost any classifier a leak (`e4_0/power.json` PP4).

**Orderings** — all three acceptable:

| ordering | crash (acc / null) | bull-trap (acc / null) |
|---|---|---|
| setup_first | 0.7679 / 0.7806 (−1.28 pp) | 0.8234 / 0.8389 (−1.55 pp) |
| event_first | 0.8410 / 0.8460 (−0.50 pp) | 0.8027 / 0.8209 (−1.82 pp) |
| phase_free | 1.0000 / 1.0000 (0.00 pp) | 1.0000 / 1.0000 (0.00 pp) |

**`phase_free` is vacuous, not passing.** That ordering carries no event, so every day is calm, the classifier
has a single class, and accuracy and null are both 1.0 by construction. It is recorded as uninformative rather
than as evidence.

**Renderings** — a rendering changes only what is shown, not the path, so all three were evaluated on one
generated path set per scenario:

| scenario | `day_n` | `none` | `date` |
|---|---|---|---|
| crash | 0.7682 / 0.7711 (**−0.29 pp**) | 0.3861 / 0.4011 (−1.50 pp) | 0.3833 / 0.3953 (−1.20 pp) |
| bull-trap | 0.8250 / 0.8228 (**+0.22 pp**) | 0.3853 / 0.3966 (−1.13 pp) | 0.3862 / 0.4020 (−1.58 pp) |

All three are acceptable under REG-9's rule, but they are not equal. **`day_n` is the only arm that exceeds
its own null anywhere** — by +0.22 pp in bull-trap — and it passes there only because of the rule's 1 pp
margin; in crash its margin is −0.29 pp, an order of magnitude tighter than either alternative. `none` and
`date` sit 1.1–1.6 pp below their nulls in both scenarios.

This is the generator-side half of D6 and it does not overturn the decision: Day-N is acceptable, and its
comparability with v1 is a real asset. It does say that Day-N is the marginal option of the three, so the
Phase-9 LLM probe — which is what could actually unseat it — is worth running rather than treating as a
formality. All three renderings remain implemented behind the switch.

### 9.5 E4.17 — the SEP level-free leakage audit on the deployed state

> **State marker.** Everything in this section was measured **before D14 was taken** (P4-43 adopted
> control definition A). Adopting A changes 60/60 sustained-bull paths, and those rows carry the `calm`
> label — about 27 % of the calm population — so these numbers describe the **pre-D14** generator. They
> are kept, not overwritten, because the before/after is itself a result: see section 9.14 and
> `e4_16_preD14/` (this section's panel and audit) against `e4_21/` (post-D14).

The brief's closing item, and the only audit that can see the event redesign at all. E4.16's decomposition
re-run reproduces Phase 3 to four decimals — correctly, because its arms are synthetic AR(1)/GJR processes
with no event block, so the redesign cannot enter it. The full generator's audit is where it can.

`tools/phase4/e4_17_sep_audit.py`, 1600 paths / 320 000 rows / 288 000 modelled rows per state, level-free
control, no subsampling, 4618 s on the reference machine. It builds its own panel under its own name:
`tools/phase3/after_state.py --stages audit` caches at `_panels/sep_phase3_after.pkl` and **returns that file
if it exists**, so running it would have audited Phase 3's stored paths and written the answer under Phase 3's
name — the same hardcoded-path trap as P4-19.

**First, the check that the audit is measuring what it claims.** `flat` and `sustained_bull` carry no scripted
event, so a *pure event* redesign must leave them bit-identical. They are: 40 000 rows each, `median_abs_x`
equal to every stored digit (0.03865703715190238 and 0.013800843219900032), and every coverage column
equal. Nothing outside the event block moved.

**Second, the caveat that governs every phase-group comparison below.** The redesign changed the panel's
composition, because the fitted schedule is much shorter than v2's stipulated one:

| phase | rows P3 | rows P4 |
|---|---|---|
| deterioration | 22 157 | 7 902 |
| mania | 39 225 | 22 399 |
| blow-off | 19 418 | 33 048 |
| stabilisation | 53 585 | 66 667 |
| post-top | 3 139 | 6 325 |

So the `event` group loses 14.7 % of its rows (111 857 → 95 420) and `resolution` gains 28.7 %
(56 724 → 72 992). **Those two groups are not population-matched and their R² is not comparable across the two
states.** Only `all` (288 000 both) and `calm` (119 419 → 119 588, +0.14 %) are.

**The matched comparisons** — best model per cell, 500-resample cluster bootstrap over paths:

| group | feature set | Phase 3 | Phase 4 | verdict |
|---|---|---|---|---|
| all | full | +0.8432 [0.8355, 0.8508] | +0.8211 [0.8108, 0.8303] | CIs disjoint — **a real fall of 0.022** |
| all | level-free | +0.5174 [0.5026, 0.5322] | +0.4458 [0.4299, 0.4619] | CIs disjoint — a real fall of 0.072 |
| calm | full | +0.2125 [0.1414, 0.2695] | +0.2260 [0.1621, 0.2816] | CIs overlap — **no detected change** |
| calm | level-free | −0.5819 [−0.7162, −0.4702] | −0.4618 [−0.5842, −0.3595] | CIs overlap — no detected change |

The shuffled-V control sits at zero in both states (−0.0016, −0.0015), so none of this is spurious fitting.
The L2 verdict is unchanged in kind: `calm_pass_absolute` false and `event_pass_absolute` true in both, overall
**FAIL** in both. Worst-group selectivity falls 0.7945 → 0.6878 and the MAPE(V) gain 0.0577 → 0.0481.

**Third, L2b — and this is the result that matters most, because the obvious reading of it is wrong.**

| | Phase 3 | Phase 4 | change |
|---|---|---|---|
| accuracy, full fields | 0.782507 | 0.782618 | **+0.01 pp** |
| accuracy, price only | 0.655715 | 0.675191 | +1.95 pp |
| accuracy, day only | 0.489000 | 0.510347 | +2.13 pp |
| majority class | 0.414649 | 0.415236 | +0.06 pp |
| **selectivity (full − price)** | **0.126792** | **0.107427** | **−1.94 pp** |

Selectivity narrowed by 1.94 pp against a 10 pp margin — and **it is still a FAIL** (0.1074 > 0.10). But the
narrowing is *not* the non-price fields leaking less. **The full-field accuracy did not move at all** (+0.01 pp,
on n = 288 000). The entire narrowing is the price-only baseline rising 1.95 pp. Selectivity is a difference,
and only its subtrahend moved. Reporting this as "Phase 4 reduced the field leak" would be false; what the
numbers say is that macro phase became *more* readable from price alone, which closed the gap from the wrong
side. The day-only classifier moved the same way (+2.13 pp), which is consistent with a shorter, more regular
fitted schedule making the phase boundaries more predictable from the clock — but that mechanism is **not
established here**, only the two accuracies are.

**A note on reading these two files.** The paragraph beginning "Interpretation (v2.1 Phase 0): the price-only
strength is dominated by the fixed start price…" appears verbatim in both markdown outputs. It is hardcoded
prose in `evaluation/leakage_audit.py:564`, not a computed result, and it must not be quoted as a Phase-4
finding. Only the tables and the numeric verdict lines are evidence.


### 9.6 E4.13 — the blow-off multiplier's closed loop (CALIBRATED)

Section 7 listed this as the one open calibration: P4-11 made the blow-off label reach the driver, but the
multiplier still sat at mania's value, so the realised blow-off/mania ratio was 0.984 against the panel's
target. `tools/phase4/e4_13_blowoff_cal.py` closes the loop against the corrected panel reference
**1.2895 [1.2146, 1.3713]** (n = 3125 run-ups, 394 stocks).

| | multiplier | realised blow-off/mania | 95 % CI | inside the panel CI |
|---|---|---|---|---|
| incumbent (mania's value) | 1.3451 | 1.0160 | [0.9375, 1.0965] | **no** |
| **calibrated** | **2.0764** | **1.3136** | [1.2139, 1.4119] | **yes** |

Six iterations (1.3451 → 1.6859 → 1.9008 → 2.0064 → 2.0531 → 2.0701), verified at 1200 seeds. The multiplier
is **not** the ratio it produces — 2.0764 buys 1.3136 — which is exactly why it had to be solved rather than
stipulated. Verdict **CALIBRATED**; `blowoff_mult = 2.076425364749724` is in `events.json` and is the value
every audit in this section ran against.

### 9.7 E4.14 — item 73: v2's crash V-drift shape is rejected in direction

The plan's item 73 asserts that a crash's fundamental decline is delivered **entirely in the deterioration
window** — a 1.0 / 0.0 / 0.0 split across deterioration, panic and stabilisation. It had never been tested.
`tools/phase4/e4_14_crash_v.py` tests it against the EDGAR value proxy on the 270 fast-crash episodes with
coverage, 106 of which have a falling V-hat over the episode.

| window | median share of the total log decline | 95 % CI | n |
|---|---|---|---|
| peak → onset (deterioration) | **0.000** | [0.000, 0.000] | 106 / 96 |
| onset → trough (panic) | 0.024 | [0.000, 0.156] | 106 / 96 |
| trough → +60 d (stabilisation) | 0.891 | [0.631, 1.000] | 106 / 96 |

**The central claim is rejected.** v2 puts 100 % of the fundamental decline in deterioration; the proxy finds
**zero** there, with a CI of zero width at the median. The decline shows up after the trough.

**No replacement value is adopted.** The magnitude of the tail is not identified by this proxy — it moves
across the de-lag sensitivity (0.508–0.891) because EDGAR filings are monthly and dated by filing rather than
by the fact they report, so *when* the proxy declines is partly an artefact of the reporting lag. The
direction is identified (the share before onset is **0.000 at every de-lag**); the magnitude is not. Item 73
therefore closes as **TESTED and REJECTED in direction, magnitude left open** — the mechanism ships
implemented and switchable, unadopted, and a value would need a proxy with a known reporting lag.

### 9.8 E4.16 — discrimination and decomposition on the deployed state

> **State marker.** Pre-D14 (P4-43). Section 9.15 carries the post-D14 re-run, where sustained-bull
> coverage rises 0.044 → 0.374 and the other three scenarios are unchanged to three decimals.

**Discrimination** (`e4_16/discrimination.md`, 40 training seeds, 50 scored seeds, three personas, four
scenarios, 2000-resample bootstrap). No pass/fail — G1 is Phase 6's gate; the finding to look for is a
collapse.

| scenario | coverage P3 → P4 | best L5 P3 → P4 | gap L5→trivial P3 → P4 |
|---|---|---|---|
| flat | 0.378 → 0.378 | 0.0551 → 0.0563 | 0.0455 → 0.0443 |
| crash | 0.585 → **0.553** | 0.0301 → 0.0378 | 0.0703 → **0.0625** |
| bull_trap | 0.637 → **0.646** | 0.0262 → 0.0320 | 0.0749 → **0.0688** |
| sustained_bull | 0.044 → 0.044 | 0.0724 → 0.0691 | 0.0302 → 0.0336 |

**There is no collapse.** In all four scenarios both gaps stay strictly positive with CIs excluding zero — L5
sits between the mandate oracle and the best trivial policy everywhere, which is the property the table
exists to check. `flat` and `sustained_bull` are unchanged to three decimals, again as they must be: no
scripted event.

But the two event scenarios did **weaken modestly**. L5's advantage over the best trivial policy narrows by
0.78 pp in crash (0.0703 → 0.0625) and 0.61 pp in bull-trap (0.0749 → 0.0688), and best-L5 loss rises in both.
Coverage moves in opposite directions — crash down 3.2 pp, bull-trap up 0.9 pp — consistent with the fitted
schedule shortening deterioration and lengthening blow-off. This is reported, not explained: no experiment
here isolates which of the five changes did it. The trend across hand-overs is **not monotone and not
comparable across coverage**: Phase 2's crash gap is the *largest* of the three (0.0756 against Phase 3's
0.0703 and Phase 4's 0.0625) while its bull-trap gap is the *smallest* (0.0630 against 0.0749 and 0.0688).
Phase 2 reached those on coverage of only 0.422 and 0.539, against Phase 4's 0.553 and 0.646 — a gap
measured over fewer resolvable cells is not the same quantity, so the three hand-overs should not be read
as a ranking.

**Decomposition** (`e4_16/decomposition_phase4.md`) reproduces Phase 3 **to four decimals**:

| arm | level-free calm R²(x) [95 % CI] | delta over exact |
|---|---|---|
| exact (the bound's model) | 0.145 [0.108, 0.176] | +0.000 |
| + GJR-t innovation | 0.145 [0.096, 0.184] | +0.000 |
| + jumps (fitted λ, σ_J) | 0.192 [0.105, 0.288] | +0.047 |
| **+ GJR-t + jumps (the Phase-3 x innovation)** | **0.203 [0.141, 0.262]** | **+0.057** |

That it is unchanged is **correct, not a null result**: this tool's arms are synthetic AR(1)/GJR processes
with no event block, so a pure event redesign cannot enter it by construction. It is re-run to confirm exactly
that — and it does. Its value to Phase 4 is the 0.203 baseline, which is what makes §9.9's arithmetic possible.


### 9.9 E4.18 — the brief's own question, answered: the event redesign did NOT narrow the calm channel

> **State marker.** Measured **before D14** (P4-43), like section 9.5. The calm-trained figures below are
> the pre-D14 generator's; section 9.14 carries the post-D14 re-measurement. **The verdict there is the
> same — no detected narrowing — but the point estimate flips from +0.0101 to −0.0280 against Phase 3.**

The brief calls narrowing the events-and-sentiment share of the calm level-free channel "the single most
useful thing your event redesign could hand" Phase 6. Section 9.5 does **not** answer that question, and it is
worth being precise about why, because the number that looks like the answer is the wrong one.

`evaluation/leakage_audit.py` fits one model across **all** phases and only then masks by phase group
(lines 297–300). Its "calm" row is therefore a **cross-phase-trained** model scored against calm-only
variance — a large negative number there is substantially a train/eval regime artefact. The brief's quantity
is the **calm-TRAINED** figure, Phase 3's **+0.349 [0.322, 0.374]**, and only `tools/phase3/e3_9_calm_trained.py`
computes it. That tool hardcodes the Phase-2 and Phase-3 panels, so `tools/phase4/e4_18_calm_trained.py`
imports its estimator **unchanged** — no reimplementation, so the comparison cannot drift on the estimator —
and points it at the Phase-4 panel.

**Phase 3 was re-run in the same process rather than quoted**, as a check that the comparison is sound. It
reproduces the stored `e3_9/calm_trained.json` on **all six cells**: full/ridge 0.2648 → 0.265, full/gbt
0.5501 → 0.550, full/mlp 0.4590 → 0.459, level-free/ridge 0.2172 → 0.217, **level-free/gbt 0.3493 → 0.349**,
level-free/mlp 0.2978 → 0.298.

| state | feature set | published (cross-phase-trained) | **calm-trained** |
|---|---|---|---|
| phase3 | level-free | −0.5819 [−0.7162, −0.4702] / sign 0.722 | **+0.3493 [+0.3218, +0.3743]** / sign 0.814 |
| phase4 | level-free | −0.4618 [−0.5842, −0.3595] / sign 0.708 | **+0.3594 [+0.3282, +0.3859]** / sign 0.812 |
| phase3 | full field set | +0.2125 [+0.1414, +0.2695] / sign 0.834 | +0.5501 [+0.5180, +0.5791] / sign 0.906 |
| phase4 | full field set | +0.2260 [+0.1621, +0.2816] / sign 0.824 | +0.5435 [+0.5114, +0.5743] / sign 0.899 |

**The answer is no.** Calm-trained level-free R²(x) moves **+0.3493 → +0.3594, a delta of +0.0101 with CIs
that overlap almost completely** — no detected change, and the point estimate moves the *wrong way*. The
full-field figure moves −0.0066, also with overlapping CIs. Sign accuracy on resolvable steps is flat in both
(0.814 → 0.812 level-free, 0.906 → 0.899 full).

Combined with §9.8's decomposition, which is unchanged by construction, the arithmetic is:

| | Phase 3 | Phase 4 |
|---|---|---|
| calm-trained level-free R²(x), full generator | 0.3493 | 0.3594 |
| less the process + GJR + jump stack (E3.8) | 0.203 | 0.203 |
| **= the events-and-sentiment share** | **≈ 0.146** | **≈ 0.156** |

**Phase 4 did not reduce the ≈ 0.15 the brief asked about.** That is a real negative result, not a
measurement failure: the estimator is identical on both sides, Phase 3 reproduces exactly, the panels are the
same size (1600 paths), and the shuffled-V control sits at zero. It is consistent with §9.5's L2b finding,
where the full-field channel also did not move.

**What this says for Phase 6.** The redesign changed *which* events happen and *when* — schedule, hazard,
blow-off, post-top, calendar — and none of that touched how much a calm-day reader can recover from the
level-free fields. That is evidence the calm channel is carried by the **fields themselves and the sentiment
feedback**, not by the event schedule that generates them, which is what Phase 5 (field redesign) exists to
address. Phase 4 can hand Phase 6 the measurement and the tool, but not the narrowing.


### 9.10 Hand-off notes, and one expectation of mine that measurement refuted

**The audit's thread cap (`evaluation/leakage_audit.py:43–49`).** The module unconditionally caps native
thread pools at 2 and documents why: HistGradientBoosting and MLP collapse under oversubscription when other
sklearn jobs run concurrently ("100x slowdowns observed"). E4.17 ran **alone** for 4618 s, so on an 8-core
machine the cap left cores idle, and I expected raising it would roughly halve the audit.

**Measured, it does not.** One GBT fit, 60 000 rows × 45 level-free columns, on this 8-core machine:

| thread limit | fit time |
|---|---|
| 2 (the shipped cap) | 10.6 s, 10.2 s on a repeat |
| 4 | **7.7 s** |
| 8 | 8.4 s |

So 2 → 4 buys about **1.3×**, not 2×, and 8 threads is *worse* than 4 — the oversubscription the comment warns
about starts biting within a single fit. Whether even that 1.3× moves total wall-clock is **untested**: the
audit also spends time on the MLP, the ridge, the cluster bootstraps and panel generation, and no measurement
here attributes the 4618 s across them. The note for whoever revisits this: the cap is **correctly justified**
and the gain from making it adaptive is **smaller than it looks** — my "would likely halve it" was wrong, and
is recorded here as refuted rather than dropped. `evaluation/` is outside Phase 4's remit and the file is
frozen, so nothing was changed.

**The two provenance defects this phase found, together.** P4-19 (results measured before the parameter file
existed) and P4-37 (a cited evidence file that was never written) are the same failure in two forms: a number
whose provenance was assumed rather than checked. Neither was caught by a test, and P4-37 was caught by
accident. `tools/phase4/e4_9_deployed.py` addresses the first. The second wants a cheap check no one has
written: **before a report is accepted, assert that every file path it cites exists.**


### 9.11 The rest of the test tree — run at last, and six failures that had been hiding

Section 7's last row named five suites. That row was **too narrow**: eleven of the twenty-two test files had
been run, and **nine had not**. Running them produced **six failures**, none of which any earlier pass had
seen, because the files that assert them had not been executed since Phase 4 changed the generator.

| failure | cause | class |
|---|---|---|
| `test_v2_freeze::test_generator_matches_frozen_manifest` | `events.json` hash moved | **mine** — the label fix in §9.10's neighbourhood |
| `test_v2_freeze::test_env_code_hash_is_the_manifest_hash` | same | **mine** |
| `test_v2_1_phase_0::test_known_defect_registry_matches_strict_xfails` | Phase 4 added a strict xfail to its own suite and never registered it | Phase-4 bookkeeping |
| `test_v2_1_phase_0::test_hazard_loader_is_loud` | `GenConfig().hazard_h0` is 0.000671 (events.json) while the test asserted `hazard.json`'s 0.0003 | Phase-4 consequence |
| `test_v2_generator::test_schedule_ranges` | unpinned draw returns v2.1's fitted ranges; `det_len` reaches 3 against v2's floor of 15 | Phase-4 consequence |
| `test_v2_generator::test_crash_criterion_and_delta_matters` | `delta` no longer moves the drawdown | Phase-4 consequence |

**The two freeze failures are mine and were fixed by re-freezing deliberately**, which is what the failure
message instructs. Only `envs/v2/params/events.json` differed, and only in two provenance **label** strings —
the edit was applied under an assertion that every `value` block stayed byte-identical. Manifest re-written:
**25 files, hash `869e4fbf4b6e64ba…`** (was `3473b174e5172707…`).

**Three of the four others are the ordering defect in a new costume.** `test_schedule_ranges` and
`test_crash_criterion_and_delta_matters` both call the generator **without pinning `schedule_mode`**, so they
silently measured the v2.1 state while asserting v2's constants — exactly P4-19's failure, this time in the
test suite rather than in a tool. Verified rather than assumed:

- schedule: pinned `v2` gives **0/200** violations of the v2 bounds; unpinned/`v21` gives **158/200**, with
  `det_len` spanning 3–26 against v2's 15–40.
- delta: pinned `v2`, mean max-drawdown is **−0.6347** at δ=0.55 against **−0.5226** at δ=0.85; under `v21`
  the two are **identical to full float precision** (−0.5299021470933106 both), confirming checklist item 10's
  documented structural inertness — E4.2 draws the depth from the panel, so the `crash_discount` arm factor
  has *exactly* no effect.

Both tests now pin `v2` — which is not a workaround but the guarantee the phase makes ("v2 behaviour is
bit-identical behind every switch"), now enforced — and each gained a companion asserting the v2.1 behaviour:
`test_schedule_ranges_v21_stay_inside_the_fitted_grids` checks every draw lands inside its **own** empirical
grid, read from `events.json` rather than hardcoded so a re-fit cannot invalidate it, and asserts the two modes
genuinely differ so the pin cannot become vacuous; `test_delta_is_inert_under_the_v21_schedule` asserts the
inertness so that if the arm factor ever regains an effect, someone is told.

**The hazard failure is a real inconsistency, and it is a labelling one, not a wrong value.** Phase 4 gave the
hazard a **second parameter file**: `hazard.json` holds v2's (h0 3e-4, b 6.0) and `events.json` holds E4.3's
(h0 6.712e-4, b 5.419). `envs.v2.generator.HAZARD_H0` still reports the former while `GenConfig()` defaults to
the latter — both deliberately, since `test_v2_1_phase_4.py`'s digest probe builds its v2 baseline from those
module constants. What is inconsistent is the **status word**: the entry is marked `INCUMBENT`, whose own
`_status_key` reads "the v2 behaviour stays" — but the value in force is E4.3's, not v2's. The entry's
`adoption_withdrawn` text says plainly what was meant: *"The values below stay in force as the INCUMBENT and
the criterion needs re-expressing."* So the intent is documented and the value is deliberate; the vocabulary
does not have a term for "in force, adoption withdrawn, pending a re-expressed criterion". **No parameter was
changed** — reverting to v2's hazard would move an outcome the phase measured (v2's incumbent gives a topped
share of 0.064, outside the panel CI, per the entry's own `outcome_not_target`). The test now asserts the
override chain explicitly so neither file can drift unnoticed, and **the status vocabulary is a question for
the team**, logged as P4-38.

**What this says about the method, again.** §9.10 recommended asserting that every cited file exists. This
section adds the sibling: **a phase that changes the generator must run the whole test tree, not the suites it
remembers writing.** Four of these six failures dated from the main pass; none was caught by the phase's own
suite, because Phase 4's tests test Phase 4's changes, and what broke were older tests encoding the behaviour
those changes replaced.


**The whole tree, after the fixes — all 22 files, zero failures.** Run in three stages (a laptop battery
killed an earlier single-run attempt at 47 %, so the stages bank partial results):

| stage | files | result | time |
|---|---|---|---|
| A | the 17 fast files | **112 passed, 1 skipped, 1 xfailed** | 2:09 |
| B | `test_v2_1_phase_{1,2,3}` + `test_v2_1_stats` | **26 passed, 1 xfailed** | 3:10 |
| C | `test_leakage_ci` | **7 passed, 4 xfailed** | 11:13 |
| **total** | **22 of 22** | **145 passed, 1 skipped, 6 xfailed, 0 failed** | 16:32 |

All **six** xfails are registered in `tests/known_defects.py` and reconcile exactly: two permanent v1
baselines, the two v2 gates owned by Phase 6 (`test_v2_L2_surrogate_thresholds`,
`test_v2_L2b_phase_clock_selectivity`), and the two copies of `test_sustained_bull_selection` — the second of
which this pass registered (P4-38).

**A timing note that supports §9.10's finding.** Stage B took **3:10** here against **18:39** when the same
four files were run earlier in the pass. Same machine, same tests. The earlier run was competing with this
phase's own concurrent jobs, so a large part of that cost was self-inflicted scheduling rather than the
suites — which is the practical half of the thread-cap measurement in §9.10: on this box the audit code is
already thread-limited, so what actually destroys wall-clock is running independent heavy jobs at the same
time, not the cap.


### 9.12 E4.19 — the inherited criteria re-registered, and two of my own claims tested

Section 5.1 recommended acting on seven items. Two of the claims underneath the D5 recommendation were read
off point estimates with no interval, and the root-cause story behind item 6 was a hypothesis. This section
tests all three on the **stored** per-path output of E4.6 and the panel episode table — no regeneration, so
nothing can drift from what was decided on. `tools/phase4/e4_19_criteria.py`, 2000-resample bootstrap,
clustered on the seed.

**The tool reproduces E4.6's coverage exactly** (0.474 / 0.480 / 0.520 / 0.562 / 0.521 / 0.462 / 0.323) once
it matches the registered estimand: E4.6 conditions coverage on the path *having a measurable episode*
(`e4_6_dynamics.py:197-199`). A first version of this tool counted unmeasurable paths as failures and got
0.434 for A at λ 0.25 against E4.6's 0.562 — the reconciliation is recorded because it is the reason to trust
the rest.

**Item 6's root-cause hypothesis is REFUTED for the coverage criterion.** The claim was that these targets
were adopted without checking the generator could express them. For coverage that is not what happened:
`dd30_fast` is **already** restricted to peak-to-trough duration ≤ 126 d — "the sub-population that FITS a
200-day benchmark horizon", in its own selection string — so the box was window-matched on duration before
Phase 4 touched it. Its self-coverage recomputed here is **0.6433 [0.6074, 0.6791]** (n = 642), reproducing
E4.6's 0.643. The 0.70 threshold sits above it because a P10–P90 box on **two correlated quantities** cannot
capture 0.80, not because of the horizon.

**Claim (b) — that correcting the threshold still rejects every arm — is CONFIRMED.** The best arm, A at
λ 0.25, reaches 0.562 [0.527, 0.597]; its upper bound sits below the panel's lower bound of 0.6074, so it is
**significantly below** the panel's own self-coverage. Every other arm is lower.

**Claim (a) — my noise-floor argument — is REFUTED.** I claimed C and B were indistinguishable from the
unscripted arm D. With intervals, **every arm is separable from D**: B by +0.0091 [+0.0074, +0.0112] and C by
−0.0162 [−0.0185, −0.0140]. The metric has resolution; my reading of it was wrong, and it was wrong in the
specific way this phase keeps finding — a point estimate compared by eye without its interval.

**But the test found a worse defect than the one I alleged.** C — *fully scripted, no feedback* — scores
**significantly BELOW the arm that has no script at all**. A metric whose stated meaning is "the share of the
realised path the script explains" cannot rank a fully scripted formulation below an unscripted one. It is
**not monotone in scriptedness**, so it is invalid as the ranking device the adoption rule makes it, and no
re-thresholding repairs that. The rule needs replacing, not re-tuning.

**And the coverage shortfall is a DEPTH problem, not a duration problem.** Decomposed, for every arm:

| arm | coverage | no measurable episode | fail depth only | fail duration only | fail both |
|---|---|---|---|---|---|
| A_lam0.02 | 0.474 | 0.211 | **0.369** | 0.084 | 0.074 |
| A_lam0.05 | 0.480 | 0.221 | **0.356** | 0.081 | 0.083 |
| A_lam0.1 | 0.520 | 0.221 | **0.318** | 0.086 | 0.076 |
| A_lam0.25 | 0.562 | 0.228 | **0.282** | 0.083 | 0.073 |
| B_shifted_pstar | 0.521 | 0.221 | **0.306** | 0.108 | 0.065 |
| C_scripted_no_feedback | 0.462 | 0.201 | **0.395** | 0.076 | 0.066 |
| D_unscripted_regime | 0.323 | 0.323 | **0.487** | 0.066 | 0.123 |

Depth-only failure runs 4–7× duration-only failure in every arm. **This is the same lever as item 3**: E4.2's
depth draw is what made `crash_discount` inert, and it is also what is costing coverage. The two items the
recommendation treated separately are one problem. A further 20–32 % of paths have **no measurable episode at
all**, which the registered statistic conditions away rather than counts.

**Pairwise coverage differences, because overlapping CIs are a conservative test and not a verdict:**

| comparison | difference | 95 % CI | separable |
|---|---|---|---|
| A_lam0.25 − B_shifted_pstar | +0.0410 | [−0.0130, +0.0903] | no |
| A_lam0.1 − B_shifted_pstar | −0.0013 | [−0.0501, +0.0488] | no |
| B_shifted_pstar − C_scripted_no_feedback | +0.0594 | [+0.0115, +0.1068] | **yes** |
| A_lam0.25 − C_scripted_no_feedback | +0.1003 | [+0.0518, +0.1501] | **yes** |
| B_shifted_pstar − D_unscripted_regime | +0.1977 | [+0.1465, +0.2495] | **yes** |

**The joint window constraint is real but second-order.** Measured over 4000 deployed draws: setup_len
p10/p50/p90 = 56 / 81 / 104, leaving a median headroom of **109 d** against the panel box's duration p90 of
113 d. **87.1 %** of the panel's target episodes fit alongside a median setup and **73.5 %** alongside a p90
setup — so the constraint does bite for the longest quarter of setups, but it cannot explain a shortfall that
is 4–7× larger in depth than in duration.

**E4.5's KS bound is now costed rather than described.** The null floor — the 95th percentile of the
two-sample KS statistic when both samples come from one distribution — is **0.159** at the achieved
n_acc/n_rej = 419/81, against a registered bound of 0.10, so the bound was undecidable as reported. The floor
falls below 0.10 at **n_rej ≈ 400** (0.073; at 200 it is still 0.105). E4.5 achieved 81, so the bound needs
roughly **five times** the rejections, which at its observed rejection rate is the concrete number the
re-registration needs.


### 9.13 E4.20 — item 3 acted on, and the depth floor that blocks D5

**Item 3 is done and adopted.** `depth_mode = "centred"` is in `events.json`. E4.2 drew the crash depth from
the panel **unconditionally**, which discarded `delta` entirely (`schedule.py`, the v21 branch) and is why
checklist item 10 became exactly inert. The fix shifts the fitted depth distribution so its centre tracks the
arm's severity, keeping its shape. Three properties, each measured, each now asserted by
`test_delta_moves_the_drawdown_under_the_centred_depth_draw`:

| property | measurement |
|---|---|
| inert at the reference δ = 0.70 | centred and unconditional agree **bit-for-bit** (−0.524091 both) |
| the arm factor is alive | 0.55-vs-0.85 drawdown spread **0.0000 → −0.0814** |
| the fitted shape is preserved | IQR of the drawn δ **0.1333 either way**; a pure location shift |

The restoration is partial and the number is stated rather than rounded up: v2's spread was −0.1121, so the
centred v21 draw recovers **73 %** of it. And the upper clip bites for shallow crashes — 0 % of draws hit it
at δ ≤ 0.70, **21.7 %** at δ = 0.85, 61 % at δ = 0.95 — so the factor is live over the severities the arm grid
actually uses and saturates above them.

**Then the same experiment found why D5 cannot be decided on coverage, and it is not the formulation.**
E4.19 showed depth-only failure dominates in all seven arms. E4.20 asks whether that is a calibration miss and
closes a loop on it, exactly as E4.13 did for the blow-off. **The loop does not close:**

| | depth_gain | realised depth p50 | 95 % CI | share inside the panel's depth box |
|---|---|---|---|---|
| uncalibrated | 1.0 | −0.5134 | [−0.5211, −0.5057] | 0.588 |
| best available | 0.2078 | −0.4614 | [−0.4695, −0.4550] | 0.727 |
| **panel target** | — | **−0.3693** | — | — |

Verified at 1200 seeds disjoint from the 400 used to fit. The realised depth **saturates near −0.451**: gain
0.45 gives −0.4510 and gain 0.23 gives −0.4510, so below a point the target has no effect at all.

**The floor is structural, and three candidate causes were tested.** It is **not** rejection sampling —
`check_validity` rejects crashes shallower than −20 %, but the measured rejection share is **0.000 at every
gain**, so no selection is operating. Decomposing the drawdown into its two factors (P = V·e^x):

| gain | realised MDD | Δlog V | Δx | min x in panic |
|---|---|---|---|---|
| 1.00 | −0.5114 | −0.3163 | −0.3921 | −0.3129 |
| 0.45 | −0.4687 | −0.3330 | −0.2787 | −0.1999 |
| 0.05 | −0.4685 | −0.3360 | −0.2785 | −0.1948 |

Two terms neither of which Phase 4 controls. **Δlog V ≈ −0.34 is the fundamental decline**, set by `D_V`,
a **stipulated** uniform [0.10, 0.30] that `events.json` correctly labels *DESIGN, unchanged from v2*.
**Δx saturates at −0.279** even when the scripted discount is essentially switched off, so the residual is the
panic-phase mispricing excursion — Phase 3's volatility block, which is frozen. Sweeping `D_V` confirms it is
*a* lever but not a sufficient one:

| D_V range | realised MDD p50 | share in the panel's depth box |
|---|---|---|
| [0.10, 0.30] (deployed) | −0.4601 | 0.724 |
| [0.05, 0.20] | −0.4159 | **0.752** |
| [0.02, 0.12] | −0.3912 | 0.716 |
| [0.00, 0.06] | −0.3805 | 0.652 |

Even with the fundamental decline switched off almost entirely, the median crash is −0.3805 against the
panel's −0.3693, and the box share **peaks at 0.752 and then falls** as the distribution narrows.

**`depth_gain` is therefore implemented, switchable and NOT ADOPTED.** Adopting 0.2078 would scale the fitted
depth distribution to a fifth of its fitted value to chase a realised statistic it still misses — it would
hollow out E4.2's central achievement and buy a number that is not the target. The honest statement is that
**the generator cannot produce a panel-median crash**, that closing the gap requires `D_V` (DESIGN, a team
parameter) and the panic-phase volatility multiplier (Phase 3, frozen) to move together, and that this is a
cross-phase calibration outside Phase 4's remit.

**What this settles for D5.** No dynamics formulation can meet the coverage criterion, because the criterion
is dominated by a depth floor that is common to all seven arms and is set outside the event block entirely.
Coverage is therefore not a criterion that discriminates between formulations, and D5 should not be decided on
it — which, with §9.12's finding that the script-share metric is not monotone in scriptedness, means **both**
halves of the registered adoption rule are unusable and the rule needs replacing rather than re-thresholding.


### 9.14 The post-D14 re-measurement — and a sequencing error of mine that caused it

**Why this section exists.** P4-43 adopted control definition A. That changes which sustained-bull paths
survive rejection, and the change is total: **60 of 60 sustained-bull paths differ** under A against C, while
flat, crash and bull-trap are **bit-identical** — correct, since the criterion is sustained-bull-only. In the
audit panel every sustained-bull row carries the `calm` macro label (40 000 rows, ≈ 27 % of the calm
population), so sections 9.5 and 9.9 stopped describing the deployed generator the moment D14 was taken.

**This is P4-19 again, and this time the tool was innocent.** The tools pinned their configuration correctly.
What went wrong is the *order I did the work in*: I ran the 77-minute SEP audit and the 40-minute calm-trained
comparison, and only then adopted the parameter change that invalidated both. The phase had already written
the lesson down — measure after the parameter file settles — and it was applied to the tools without being
applied to the sequencing. Recorded as P4-45 because a method defect that costs two hours of recomputation is
worth the same treatment as one that costs a wrong number.

The pre-D14 state is preserved rather than overwritten (`_panels/sep_phase4_preD14.pkl`,
`e4_16_preD14/`), because the before/after is a result in its own right.

**And it is a good result: adopting A reduced the leakage, on the channel that matters.**

| | pre-D14 | post-D14 | change |
|---|---|---|---|
| accuracy, full fields | 0.782618 | **0.760160** | **−2.25 pp** |
| accuracy, price only | 0.675191 | 0.656635 | −1.86 pp |
| accuracy, day only | 0.510347 | 0.509229 | −0.11 pp |
| majority class | 0.415236 | 0.414490 | −0.07 pp |
| **L2b selectivity** | 0.107427 | **0.103524** | −0.39 pp — still **FAIL** vs the 10 pp margin |
| **worst-group selectivity R²(x)** | 0.687764 | **0.482106** | **−0.206** |
| calm best R²(x) | +0.225975 | +0.232620 | +0.007 |
| shuffled-V control | −0.001518 | −0.002487 | at zero in both |

**Read this against section 9.5, because the two look similar and are opposite.** There, selectivity narrowed
by 1.94 pp while full-field accuracy did not move at all — the gap closed because the *price-only baseline
rose*, which is the wrong side, and P4-34 records that the obvious reading of it was false. Here the
**full-field channel itself falls 2.25 pp**, and worst-group selectivity R²(x) drops by **0.206**. Removing a
control that selected on the hidden state reduced what the non-price fields reveal about it. That is the
direction the benchmark wants, and it is measured rather than argued.

It does **not** clear the gate: selectivity is 0.1035 against a 0.10 margin, so `test_v2_L2b_phase_clock_selectivity`
remains a registered defect owned by Phase 6. The calm channel is essentially unmoved (+0.007, well inside its
interval), which is consistent with section 9.9's negative result — the calm channel was never the control's.

`shown_fields` is identical across the two audits (18 fields), so the estimator is unchanged and the
comparison is like-for-like rather than a re-specification.


**The calm-trained channel, re-measured post-D14 — the point estimate flips direction, the verdict does not.**

| calm-trained | Phase 3 | Phase 4 pre-D14 | Phase 4 post-D14 |
|---|---|---|---|
| level-free R²(x) | +0.3493 [0.3218, 0.3743] | +0.3594 [0.3282, 0.3859] | **+0.3213 [0.2935, 0.3478]** |
| full field set R²(x) | +0.5501 [0.5180, 0.5791] | +0.5435 [0.5114, 0.5743] | **+0.4905 [0.4607, 0.5203]** |

Against Phase 3 the level-free delta is now **−0.0280** where it was **+0.0101**, and the full-field delta is
**−0.0596**. **In both cases the CIs still overlap, so the verdict of section 9.9 is unchanged: no detected
narrowing.** What changed is that the point estimate now moves in the direction the brief wanted rather than
against it. The pre-D14 and post-D14 Phase-4 figures also overlap each other ([0.3282, 0.3859] against
[0.2935, 0.3478]), so **D14's effect on this channel is itself not separable** — the honest statement is a
consistent downward nudge across three quantities, none of them individually significant.

Carried through the decomposition (E3.8's 0.203 arm, unchanged by construction), the events-and-sentiment
share reads **0.146 → 0.118**. That is the number Phase 6 inherits, and it should be quoted with its
overlapping interval, not as a reduction.

**So section 9.9's answer stands and is now better supported.** The event redesign did not narrow the calm
level-free channel. Adopting a control that no longer selects on the hidden state moved three related
quantities down together without any of them clearing its own interval, which is what a small real effect and
a null look like alike at this n — and section 9.5's L2b channel, where the effect *was* large enough to
separate (−2.25 pp on full-field accuracy, −0.206 on worst-group selectivity), is where D14 actually showed up.


### 9.15 The post-D14 discrimination table — D14 repaired the sustained-bull scenario

`e4_21/discrimination.{json,md}`, re-run on the post-D14 state against the same design (40 training seeds,
50 scored seeds, three personas, four scenarios, 2000-resample bootstrap). The pre-D14 table is preserved in
`e4_16_preD14/`.

| scenario | coverage | best L5 | gap L5→trivial | runs with NO resolvable step |
|---|---|---|---|---|
| flat | 0.378 → 0.378 | 0.0563 → 0.0559 | 0.0443 → 0.0448 | 0 % → 0 % |
| crash | 0.553 → 0.553 | 0.0378 → 0.0352 | 0.0625 → 0.0652 | 0 % → 0 % |
| bull_trap | 0.646 → 0.646 | 0.0320 → 0.0325 | 0.0688 → 0.0683 | 0 % → 0 % |
| **sustained_bull** | **0.044 → 0.374** | 0.0691 → 0.0636 | 0.0336 → 0.0373 | **10 % → 0 %** |

Three scenarios are unchanged to three decimals, exactly as they must be — the control criterion is
sustained-bull-only. In all four, both gaps stay strictly positive with CIs excluding zero, so L5 still sits
between the mandate oracle and the best trivial policy everywhere.

**The fourth row is the result.** Sustained-bull coverage rises **8.5×**, and the share of runs with **no
scoreable step at all** goes from **10 % to zero**. The mechanism is measured, not inferred: definition C's
x-band clamps mispricing to [−0.10, 0.15], which held the median |x| at **0.0143** and left only **3.5 %** of
steps resolvable at θ = 0.05; under A the median is **0.0362** and **35.6 %** of steps are resolvable — a
tenfold increase.

**This reframes what D14 was.** It was posed as a leakage question — does the control select on the hidden
state — and section 9.14 answers that (worst-group selectivity −0.206). But the same band that leaked was
also making the scenario nearly unscoreable: a quarter of the benchmark's cells had coverage 0.044 and one run
in ten produced nothing to score. **The best L5 policy in sustained-bull also changes, from `price_only` to
`level_free`**, which is the ordering the rest of the table already had. So C was costing the benchmark twice,
and only one of those costs was the one D14 was framed around.

`test_sustained_bull_selection` passing (P4-43) is the leakage half. This is the usability half, and it was not
predicted — it was found by re-running the table after the adoption, which is the practice P4-45 exists to
enforce.

