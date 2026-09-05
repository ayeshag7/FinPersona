# Prompt: execute Phase 4 of the v2.1 improvement plan (events, schedule, controls and the calendar)

## What this project is

**FinPersona-Bench** asks a question about LLM agents, not about markets: *when an LLM is given a persona with an
investment mandate — a risk band, a target allocation — does it keep to that mandate as market conditions change, or does
it drift?* An agent is run day by day through a multi-day market, sees a rendered snapshot (price, technicals, sentiment,
implied volatility, an analyst estimate, EPS and dividend fields), and allocates between cash and a risky asset. The
score is **mandate-conformity**, not profit: how far the agent's allocation sits outside the persona's band.

For that score to mean anything, the market the agent trades in must satisfy one hard requirement: **the agent must not
be able to deduce the hidden state from what it is shown.** The generator carries a hidden fundamental value `V` and a
mispricing `x`, with price `P = V·e^x`. If `x` can be reconstructed from the visible fields, then a model that appears to
"follow its mandate well" may simply be reading the answer key, and the benchmark measures information leakage rather
than persona adherence. This is why so much of the programme is spent on leakage audits and on making every generator
parameter defensible.

The synthetic environment was built (v1 → v2), then **three independent reviews found v2 not robust**: parameters were
stipulated rather than fitted, several claims were not supported by the evidence cited, and the leakage controls had a
hole. 74 weaknesses were catalogued. The response is the **v2.1 improvement programme**: ten phases, each of which
re-derives one block of the environment from data under a pre-registered protocol.

**The governing rule of the whole programme: every generator parameter is fitted or tested on data, never stipulated.**
A statistic marked "(to verify)" may not appear in a parameter file, a test tolerance, or a slide.

## The document landscape

**The single working document is `docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.md`** (`.docx`/`.pdf` beside it are the same
content). Its shape:

| Section | What it is |
|---|---|
| 0 | What was verified before the plan was written |
| **1** | **The protocol every phase follows** — pre-register, fit or test everything, report failures as failures |
| 2 | Weakness-to-phase map (which of the 74 review findings each phase closes) |
| 3 | Data sources, their substitutes and their biases |
| 4–14 | **Phases 0–10**, one section each. Phase 0 verification/freeze · 1 value and price structure · 2 mispricing engine · 3 volatility · **4 events, schedule and controls (yours, Section 8)** · 5 observables · 6 audits and checklist methodology · 7 targets, action and metrics · 8 harness and statistics · 9 LLM sensitivity · 10 documentation |
| 15 | Cross-phase compute, cost and effort |
| **16 / 16A** | **Order, dependencies, and the go/no-go checkpoint** (written in advance, not to be moved) |
| 17 | Decisions only the team can make |
| A / B / C | Power-analysis formulas · the analytic level-free bound for x · numbers to be recomputed |

Around it:

- `V2_1_ALTERNATIVES_REGISTER.md` — for each contested design choice, the alternatives and **the experiment that would
  decide between them**. **REG-7 (the sustained-bull control), REG-8 (event dynamics), REG-9 (the calendar and the
  ordering mix) and REG-18 (the hazard's horizon scaling) are all yours**; REG-15 (data and survivorship) applies to
  every fit you make.
- `docs/env_v2/README.md` — the layout, the reading order and the regeneration commands.
- `spec/E1_V2_GENERATOR_SPEC.md` and `spec/IO_CONTRACT.md` — v2 as actually built. **Section 3 (event drivers) is the one
  you rewrite**; Section 4 (volatility) was rewritten by Phase 3 and shows the expected form.
- `reviews/review_{A,B,C}_*.md` and `reviews/V2_WEAKNESSES.md` — the three reviews and the 74 findings.
- `preregistration/` — v2's original thresholds and every amendment. **Amendments A4 (the sustained-bull anchoring) and
  A5 (the mania drift cap) are the two Phase 4 revisits with evidence.**
- `decisions/DECISIONS_13_1.md` and `decisions/DECISION_LOG.md` — the signed decisions and the running log; **the P3-*
  entries are the freshest precedent for how yours should read** (including P3-12, a withdrawal of the phase's own
  conclusion after review).
- `generated/` — every machine-written result, `generated/v2_1/` being this programme's.

## Context for this phase

**Phases 0, 1, 2 and 3 are done, reviewed and committed** (Phase 3 at `ceefa2a`, 5 September 2026). E1.0 (the data panel)
is downloaded. You are to execute **Phase 4**: the crash and bubble episode tables, the sampling ranges drawn from them,
the hazard, the mania drift, the sustained-bull control, the event-dynamics formulation, the orderings and the calendar.

Three things make this phase different from the three before it.

**First, Phase 4 arrives with five measured defects already on its desk, four of which are its own.** Phase 3 did not
merely hand over parameters; it ran into the event block four separate times and each time produced a number rather than
an opinion (`PHASE_3_REPORT.md` §5, DECISION_LOG P3-9, P3-14):

- **The schedule template, not the variance mechanism, owns the crash's rise time.** The panel's fast crashes go from
  onset (first −10 %) to peak 21-day realised variance in **30 days [29, 35]**; the generator cannot get below **75.5 d**
  under *any* of REG-6's three variance mechanisms (A 75.5 / B 103 / C 80), because the deterioration length plus the
  panic's build-up is set by `schedule.py`. REG-6's rule therefore returned "none passes" for a reason that is E4.2's to
  fix, not E3.4's.
- **The bubble hazard is stale.** At the new mispricing the topped share is **8 %** against its 40–60 % target
  (checklist item 11; the CAL `(h0, b) = (3e-4, 6.0)` was grid-searched against an engine whose x moved four times as
  far), the median peak P/V in topped seeds is **1.49** against the 1.6–2.5 band, and only 46 % of mania runs are convex.
  E4.3 retires those targets and re-fits — the trigger is now measured.
- **The blow-off multiplier has been dead code since v2.** The label is assigned *ex post* by
  `events.relabel_blowoff`, so no blow-off variance multiplier ever reaches the GARCH driver; Phase 3 surfaced it when
  its calibration knob diverged 2.2 → 9.3 with the realised ratio pinned at ≈ 1.1. The panel says blow-off variance
  should be **1.65× [1.58, 1.71]** unconditional; the achievable value under the current relabel is ≈ 1.19. **E4.8 owns
  the label machinery.**
- **Post-top is drift-dominated.** The scripted reversal leg floors the realised variance ratio at **1.59 (n = 20)**
  against the panel's **1.16 [1.13, 1.20]** whatever the innovation multiplier is set to (Phase 3 drove it to 0.35 and
  the realised value did not move). **E4.8 owns the reversal-leg shape.**

**Second, you own the last non-Phase-6 entry in the known-defect registry.** `tests/test_v2_1_stats.py::test_sustained_bull_selection`
(items 18, 42, strict xfail) is yours, and it is not academic: at the block in force the sustained-bull rejection rate is
**32.9 %** and its coverage is **0.044** with **10 % of runs having no resolvable step at all** — the scenario is
starved by construction, and REG-7/D14 is the decision that fixes or redefines it. Bull-trap rejection is 10.7 %, crash
0.8 %, flat 0.0 % (checklist item 17, criterion < 5 %).

**Third, there is a level decision on the table that may change the environment underneath you.** Phase 3 confirmed a
**level double-count**: the variance identity pins the generator's *calm* to the panel's *all-day* unconditional sd
(0.0218, which is **1.28×** the panel's own crisis-free calm of 0.0170), and the phase multipliers were then re-based to
that same all-day level, so the deployed generator's realised unconditional daily return sd is **0.0284 — +30.5 %** above
its own target (bootstrap half-width 0.0017). Phase 3 reported it and did **not** repair it, because repairing it means
re-choosing the anchor and paying the whole execution-order cascade. **Phase 4 builds the schedule on this level**, so
raise it with the team *before* you fit anything that depends on it (`PHASE_3_REPORT.md` §5.7 lists the three costed
options). If the team has not answered, proceed on the level as handed over and say so in your report's §2.

Do not work from anything in `docs/env_v2/v2_1/archive/`, and do not edit the plan or `V2_1_ALTERNATIVES_REGISTER.md`.

## Read first, in this order

1. `docs/env_v2/README.md` — layout, reading order, regeneration commands.
2. The plan: Section 1 (the protocol every phase follows), Section 3 (data and biases), **Section 8 (Phase 4, in full)**,
   Section 16 (order and dependencies), 16A (the go/no-go checkpoint — written in advance and not to be moved),
   Section 17 (team decisions), Appendix A.
3. `V2_1_ALTERNATIVES_REGISTER.md`: **REG-7** (the control's four definitions and the audits that pick among them),
   **REG-8** (the four event-dynamics formulations and the adoption rule), **REG-9** (the calendar and the ordering mix,
   with the Phase-9 LLM probe already costed), **REG-18** (the hazard's horizon scaling), REG-15 (data and survivorship).
4. **What Phase 3 established — read all four, in this order:**
   - `docs/env_v2/v2_1/PHASE_3_REPORT.md` — the whole report. §3.3 (the episode tables you inherit), §3.4 (the mechanism
     decision and why the schedule owns the rise time), §3.11 (the post-review extensions, including a withdrawn
     conclusion and the confirmed level double-count), §4 (the parameter file and the test-edit table) and §5 (the open
     team decisions) are the ones you inherit directly.
   - `docs/env_v2/v2_1/PREREG_PHASE_3_ADDENDUM.md` — four sections: three designs corrected before the runs they govern,
     and §4's post-review extensions. Read it as the worked example of what to do when a registered rule turns out to be
     unmeetable, and of how a review's pointers are answered with experiments rather than edits.
   - `docs/env_v2/v2_1/PHASE_3_CHANGED_FILES.md` — every file Phase 3 wrote or changed, with what each is.
   - `docs/env_v2/decisions/DECISION_LOG.md`, Phase 3 section, entries **P3-1 … P3-17**. **P3-8** (the multipliers and
     the two structural shortfalls), **P3-9** (the mechanism decision and the rise-time hand-off), **P3-12** (the
     withdrawal — the pattern to imitate when your own reading turns out wrong) and **P3-14** (the level double-count)
     are the four that bind you.
5. Phases 1 and 2 for the parts you build on: `PHASE_1_REPORT.md` §4.4 (E1.5 burn-in) and §4.5 (E1.1 start price);
   `PHASE_2_REPORT.md` §3.8 (the discrimination table you will re-run) and §5 (the coverage trade-off).
6. The data panel: `datasets/README.md` (three caveats), `docs/env_v2/v2_1/E1_0_DATA_REPORT.md` (§1.2–1.3 survivorship
   and ticker reuse, §9.3 the usable panel), `datasets/04_shiller/README.md` and `datasets/01_prices/README.md`, and
   `datasets/_manifests/`.
7. The code: `envs/v2/events.py` and `envs/v2/schedule.py` (the blocks you rewrite), `envs/v2/generator.py`
   (`check_validity`, the rejection loop, `relabel_blowoff`), `envs/v2/params/hazard.json` and `value.json`,
   `envs/v2/volatility_params.py` + `params/volatility.json` (Phase 3's pattern for a loud parameter loader),
   `envs/synthetic_market.py`, `evaluation/*.py`, **`tools/phase3/episodes.py`** (the shared episode estimator — E4.1's
   starting point), `tools/phase3/` and `tools/phase2/` (several tools are directly reusable; listed below), `tests/`,
   `tools/freeze_manifest.py` and `tests/v2_freeze_manifest.json`. `envs/v1/` is frozen and must not be modified.

## Decisions the team has taken

- **D1 (data): C, hybrid** — fit on the free panel, publish every fitted value with its survivor-vs-literature gap, keep
  the fitting code re-runnable on WRDS by a data-path change. WRDS access: `______` (not confirmed unless filled in).
- **D13 (start price): mechanism C** (`start_price_mode = "both"`). Applied and in force.
- **D16 (programme): full programme.** Phase 4 now, in its own session.
- **D4 (which population the events represent — index episodes vs the single-stock panel): `______`.** E4.1 produces
  both tables; E4.2's ranges depend on which one governs. **If this blank is empty, use the single-stock panel as the
  primary and publish the index tables beside it** (the panel has the mass: 1,789 drawdowns against ~15 index crashes),
  state that you did, and flag every parameter whose range would differ under the index tables.
- **D5 (what to do if no event formulation meets the script-share/rejection rule): `______`.** E4.6's rule is
  pre-registered; if nothing qualifies, report the table and stop for this decision rather than choosing.
- **D6 (calendar rendering default — random dates, no date, or "Day-N"): `______`.** REG-9's generator-side test runs
  here; the LLM-side probe is Phase 9. **If this blank is empty, keep "Day-N" as the default** (it preserves v1
  comparability), implement the other two behind the switch, and publish the generator-side audit for all three.
- **D14 (what the sustained-bull control is for): `______`.** This one gates E4.5's adoption: "no mispricing" ⇒ only
  definition C serves it and its scenario clock must be published as a limitation; "rising value with the same
  mispricing" ⇒ A/B/D serve it and the audits pick among them. **If this blank is empty, run all four definitions, report
  the audits for each, and stop for the decision** — do not pick the purpose yourself.
- **The level anchoring (PHASE_3_REPORT §5.7): `______`.** (a) keep the anchor and publish the +30 %; (b) re-anchor to
  the panel's calm (sbar 0.00676) and pay the cascade; (c) keep the calm anchor and re-derive the multipliers so the
  deployed mix lands on 0.0218. **If this blank is empty, proceed on the level as handed over**, say so in §2, and flag
  every Phase-4 number that would move under (b) or (c).
- **D2 (LLM roster/budget) and D10 (dividends):** not taken; nothing in Phase 4 needs them (D10 is needed before Phase 5).

If something you need is not decided here, do every part that does not depend on it, then stop and ask with the options
and the evidence laid out. Never fill a blank with your own preference.

## What Phase 3 hands you (do not redo this work)

- **The volatility block, fully fitted and frozen.** `envs/v2/params/volatility.json` with a loud loader
  (`envs/v2/volatility_params.py`): GJR shape α 0.027 / γ 0.058 / β 0.932 (E3.1 medians) with a jump-decomposed
  diffusive tail **ν 6.65 [6.48, 6.83]**; **sbar 0.01509 [0.01342, 0.01678]** by an exact variance-accounting identity;
  jumps **λ 0.000583 [0.00046, 0.00082]/day at σ_J 0.230 [0.086, 0.241]** (rare-and-large, weakly identified but the
  *conservative* end for leakage); phase multipliers FIT and closed-loop calibrated; `scale_mode = "variance"` kept by
  REG-6's own three-way test with all three mechanisms retained as engine options.
- **The engine, re-identified under that block.** σ_V **0.01457 [0.01275, 0.01527]**, half-life **22.38 d [18.75, 32.64]**,
  realised **sd(x) 0.068**. Phase 2's 7.5 d is outside the new interval; 22.4 d is inside Phase 2's own [3.81, 23.61].
  The move splits into ≈ 9.5 d of block effect and ≈ 5.4 d of identity constraint, at ΔJ ≈ 26 for one restriction.
- **The IV field, rebuilt and clean.** A past-only GJR filter on observed returns, a constant FIT premium (−0.0224) and
  AR(1) FIT noise. The one-day panic step is gone (z = 0.12 against a *derived* tolerance of 2.70) and the onset audit
  shows IV carries **less** phase signal than the price path itself (ΔAUC −0.107 against a +0.032 null). Weaknesses 46
  and 25 are closed and their tests are hard.
- **The episode tables E4.1 needs are largely already computed — and this is your biggest head start.**
  `generated/v2_1/e3_3/` holds `dd_episodes.csv` (**1,789** qualifying drawdowns ≥ 30 %, 417 stocks, with peak/trough
  indices and dates, depth, span, per-window realised variances and rise/decay/stress-spell statistics),
  `ru_episodes.csv` (**3,202** run-ups ≥ 100 % in 504 d over 398 stocks, with top and start dates), `market.csv` (the
  five market-wide windows on all 417 names) and `episodes.json` (medians with 1,000-resample stock-bootstrap CIs).
  **`tools/phase3/episodes.py` is the shared estimator** that produced them and runs identically on generated paths —
  which is what made E3.4's panel-vs-generator comparison like-for-like. **But do not simply reuse the numbers**: E3.3's
  windows were defined to measure *variance*, not depth, duration, front-loading or recovery share. E4.1 needs
  Pagan–Sossounov dating, the ≥ 20 % drawdown family, the front-loading share, the 60/120/200-day recovery shares and
  the LPPLS fits — extend the module, and verify the inherited columns before building on them.
- **The rise/decay numbers the mechanism decision turned on.** Pooled drawdowns: rise **118 d [107, 131]**, decay
  **11 d [11, 12]**. Fast crashes (peak→trough ≤ 126 d, **642 episodes / 313 stocks**): rise **30 d [29, 35]**, decay
  **9 d [9, 10]**, stress spell 33 d. Depth median **−45 % [−46, −44]**. The generator reaches 75.5 d at best. That gap
  is E4.2's.
- **The phase variance multipliers, as total-return ratios with CIs** (unconditional reference): deterioration
  **1.37 [1.31, 1.44]**, panic **7.45 [6.86, 8.13]**, stabilisation **3.11 [2.96, 3.34]**, mania **1.18 [1.12, 1.21]**,
  blow-off **1.65 [1.58, 1.71]**, post-top **1.16 [1.13, 1.20]**. Market windows: 2008Q4 4.58, 2011Q3 3.52, 2018Q4 2.26,
  2020Q1 9.20, 2022H1 1.95. Your event formulation must not break the closed-loop calibration that realises them
  (`e3_4/calibration.json`'s verify block) — if it does, re-run the calibration rather than leaving the multipliers
  nominal.
- **The discrimination baseline on the current state.** `e3_7/discrimination.md` gives the 16A G1 ordering and the
  policy spread per scenario with paired bootstrap intervals: G1 holds in all four scenarios; flat coverage 0.378 with
  0 % undefined; sustained bull 0.044 with **10 % undefined**. **Re-run it after your event block is in force** — the
  schedule, the hazard and the control all move coverage.
- **The leakage baseline you will be measured against.** On the standard evaluation panel: level-free calm R²(x)
  **−0.58** as published (cross-phase-trained) and **+0.349 [0.322, 0.374]** calm-trained, sign accuracy 0.722 / 0.814;
  full-field calm 0.213; **all-phase full-field 0.843** — the event-phase channel, which is *yours and Phase 6's*, now
  dominates the leakage picture. L2b macro-phase selectivity **+12.7 pp** against its 10 pp margin (a registered
  Phase-6 defect). `e3_after/audit_after_levelfree.*`.
- **A decomposition that tells you where your own changes will land.** E3.8 attributes the level-free calm channel block
  by block at the parameters in force: the exact Appendix-B process 0.145, **+0.000 for the GJR innovation**, +0.047 for
  the jumps. The generator's calm-trained 0.349 against the bound's 0.163 leaves **≈ +0.15 for the events and the
  sentiment feedback** — measured on calm rows. Phase 6 owns the gate; narrowing that ≈ 0.15 is the single most useful
  thing your event redesign could hand it.
- **Reusable tools.** `tools/phase3/`: `episodes.py` (the shared estimator), `e3_3_episodes.py` (the panel-side pattern),
  `e3_4_mechanism.py` (closed-loop calibration + multi-arm comparison + a decision rule under two populations — the
  closest template for E4.6's four formulations), `e3_5_audit.py` (an AUC-vs-permutation-null audit, which is exactly
  the shape of E4.7's day-only classifier test), `e3_7_discrimination.py`, `e3_8_decomposition.py`,
  `e3_9_calm_trained.py`, `after_state.py` (**run this at your hand-over**), `apply_e3.py` (the pattern for writing a
  parameter file with provenance), `prereg_power.py`. `tools/phase2/`: `e2_7_discrimination.py`, `e2_8_bound_check.py`.
  `tools/phase1/`: `panel.py` (the exclusion rule and analysis sets), `e1_5_burn_in.py`.
- **Four checklist items are squarely yours** (`e3_after_checklist.md`, 200 seeds, 5/20 passing): **item 8** (gain/loss
  asymmetry in crash: median skew −0.001 and worst-day-larger-than-best in 50 %, against "skew < 0 and ≥ 70 %" — the
  crash scenario currently produces no negative skew at all), **item 10** (delta matters: partial R² 0.29 and a 12.6 pp
  spread against 0.7 / 20 pp), **item 11** (bubble: convex in 46 %, topped 8 %, peak P/V 1.49) and **item 17**
  (conditioning: the rejection rates above). Items 2, 3, 6, 7, 9 and 13 are volatility/observable items whose criteria
  Phase 6 re-derives — do not chase them.

## What to do now: Phase 4, Section 8 of the plan

1. **Pre-register before running anything** — `docs/env_v2/v2_1/PREREG_PHASE_4.md`: the panel and windows, seeds,
   estimators, the exact statistic, the pass/fail or decision rule, the power analysis that sets each sample size, and
   what will be reported if a rule is not met. **Check each criterion is decidable at the sample size you state** —
   simulate the statistic's spread under the null before you commit to the threshold, and keep the script. Phase 1 lost
   time to three criteria that could not be met by any result, Phase 2 to one, and Phase 3 to three (its jump-recovery
   gate, its run-up calm window and its pooled rise-time rule all failed at first measurement); each cost a re-run that
   a five-minute simulation would have prevented.
2. **Raise the level-anchoring decision first** (see "Context", third point). It is the one input that could invalidate
   work done before it, and it costs the team one reading of `PHASE_3_REPORT.md` §5.7.
3. **E4.1 — episode tables.** Index episodes (Mishkin–White, Barro–Ursúa, the Shiller series) *and* single-stock
   episodes from the panel (Pagan–Sossounov dating; drawdowns ≥ 20 % and ≥ 30 %; run-ups ≥ 100 %/2 y): peak-to-trough
   duration, depth, front-loading, recovery shares at 60/120/200 days, deterioration length, and for run-ups the LPPLS
   fit (m, ω, hazard) and peak P/V̂ from the EDGAR proxy. Every quantity with its empirical P10/P50/P90. Extend
   `tools/phase3/episodes.py` rather than starting again, and verify its inherited columns first.
4. **E4.2 — sampling ranges from the tables.** Each schedule parameter drawn from the empirical P10–P90 (FIT), truncated
   only where T = 200 forces it, with the truncation rate reported; the current uniform ranges printed beside so the
   change is visible. **This is where the 30-day rise time is won or lost** — the deterioration length and the panic
   front-loading are the two parameters that set it, and Phase 3 measured the target for you.
5. **E4.3 — the hazard (REG-18).** b from a logit of GSY's crash indicator on the log run-up, h0 from the horizon, with
   the horizon-scaling assumption written down and bracketed {0.5×, 1×, 2×}; REG-18's option C (fit h0 and b directly on
   the panel's own run-ups) decided by which mapping's topped share falls inside the panel's CI. **The 40–60 % topped
   band and the P/V 1.6–2.5 band are retired as targets** — the topped share becomes a reported outcome. Remove the
   calibration tool's arbitrary score and rejection penalty.
6. **E4.4 — mania drift.** κ and the mania length drawn jointly from the LPPLS fits so the drift cap is unnecessary
   (rule: the cap binds on < 5 % of mania days). If the fits do not support a super-exponential drift over 40–100 days,
   **say so** and offer the scripted-drift alternative with its shape FIT from the run-up table. Amendment A5 is
   revisited with evidence.
7. **E4.5 — the sustained-bull control (REG-7, D14).** All four definitions implemented and compared under one
   pre-registration, with the realised x distribution, the accepted-vs-rejected selection statistics (KS upper limit
   < 0.10), the scenario-discrimination audit against a label-permutation null **computed here**, and the baseline-level
   acceptance test in the form REG-7 specifies for each definition. `test_sustained_bull_selection` must end the phase
   either **passing** or **re-registered with a new owner and reason**. Amendment A4 is revisited with evidence.
8. **E4.6 — event dynamics (REG-8).** Four formulations, all implemented, decided by the pre-registered rule: adopt the
   one with the **lowest script share** among those whose depth/duration coverage is ≥ 0.70 and whose rejection rate is
   below the ceiling **you pre-register here from the episode tables**. **Run all four. Never run only the one you
   expect to win** — and note Phase 3's experience that a multi-arm rule can be decided by something outside the block
   it is testing; if that happens here, say which block actually decides it.
9. **E4.7 — orderings and the calendar (REG-9, D6).** The ordering factor added to `experiments/arms_v2.py` and tested;
   the mix and setup range set so the day-only phase classifier is at chance within each scenario against a
   label-permutation null at 200 seeds (computed here, not in Phase 6); the three day-index renderings implemented
   behind a switch with the generator-side audit published for each; the quarter phase of `days_since_eps_announcement`
   randomised per seed.
10. **E4.8 — labels and small fixes.** Blow-off given a dynamic criterion (**this is the fix for the dead multiplier** —
    a label assigned ex post cannot drive the variance); the top day recorded at the realised peak (off-by-one); the
    crash V drift after deterioration tested against the episode table's fundamental-decline shape; the post-top
    reversal leg's shape re-derived so its realised variance ratio can reach the panel's 1.16; the multi-asset shared
    event replaced by per-asset draws with a common-factor loading FIT from the panel's cross-sectional drawdown
    correlation.
11. **Tests, parameter file, freeze** — Section 8.4's tests (`test_schedule_ranges_from_params`,
    `test_sustained_bull_selection` flipped to hard, `test_no_x_selection_in_control`, `test_hazard_params_provenance`,
    `test_script_share_reported`, `test_day_index_rendering_option`, `test_arm_grid_has_ordering_factor`); a new
    `envs/v2/params/events.json` with label / source / date / interval / n on every entry, following
    `volatility.json`'s pattern and its loud loader; rewrite the freeze manifest and the path hashes on the state you
    hand over, and regenerate the checklist and the level-free audit there (`tools/phase3/after_state.py` does all four
    — point it at Phase-4 output names). **Re-run the discrimination table and the bound decomposition**
    (`e3_7_discrimination.py`, `e3_8_decomposition.py`) on the handed-over state.
12. **`PHASE_4_REPORT.md`** under the same six headings Phases 1–3 used, then stop.

## Hard rules (from the plan; not optional)

**On assuming nothing.**

- **Every parameter is fitted or tested on data, never stipulated.** If a value cannot be fitted from the free panel,
  label it DESIGN or CAL with the reason, and say what would settle it.
- **Verify inherited numbers rather than trusting them — including mine.** Phase 1 re-derived Phase 0's constants and
  found two of its own conclusions wrong; Phase 2 found the plan's SABCEMM target inverted and Phase 1's `s_x_fit` wrong
  by a factor of five; **Phase 3 withdrew its own headline leakage conclusion after review, delivered two registered
  items it had missed, and found a confirmed level double-count its own verification design could not see.** Before you
  build on any figure in the Phase-3 report, check it against the file it cites. If a number in a document and a number
  in `generated/` disagree, the generated file wins and the document is corrected.
- **Read sources at first hand.** A paper's number may be quoted beside a fitted value as an anchor, never used as a
  tolerance, and never cited from a secondary source. If you cannot read it at source, say so and do not quote it.
  **Pagan & Sossounov's 25/15-month durations were not read and may not be quoted**; **Hamilton & Susmel (1994) is not
  retrievable and may not be quoted.**
- **State the n and the interval on every number.** A point estimate with no n is not a result. (Phase 3's review caught
  a hand-off statistic quoted without its n = 20; do not repeat it.)

**On experimenting rather than deciding.**

- **When two approaches are defensible, run both and compare — do not choose by argument.** REG-7 names four control
  definitions and REG-8 four event formulations because the questions are empirical.
- **Include the incumbent as a candidate, and the simplest thing that could work.** The tracking gain λ is a candidate
  in E4.6, not a straw man; A4 and A5 are revisited *with evidence*, not overturned by preference.
- **When a result surprises you, design the experiment that distinguishes the explanations.** Phase 3's most useful
  results came from exactly this: the calibration knob that diverged while its realised ratio did not move (the dead
  blow-off label), and the calm-trained refit that separated a regime artefact from a real channel.
- **Report both arms even when one wins decisively.** The losing configuration's numbers are what make the winner
  credible, and Phase 6 and the deck will need them.

**On documenting everything.**

- **Pre-register before running anything, and never move a threshold after seeing data.** If a criterion turns out to be
  wrong, say so, derive the corrected one in a *separate documented step before* the re-run, **disclose what you had
  already seen when you wrote the correction**, and report the result under both the old and the new rule.
  `PREREG_PHASE_3_ADDENDUM.md` is the freshest template, including its §4 post-review extensions.
- **Every run writes a file.** Results go to `docs/env_v2/generated/v2_1/e4_*/` as JSON (machine-readable, with the
  design block: seeds, n, counts) *and* Markdown (the table a human reads). The report cites the file; the file is
  regenerable by the command in its own docstring.
- **Every parameter entry carries label / source / date / interval / n / survivor-vs-literature gap**, and **states what
  the fit is conditional on** where that is not obvious. **No entry ships with `"interval": null`** — Phase 3 shipped
  its most-used parameter that way and the review caught it.
- **Log every decision** in `DECISION_LOG.md` as P4-*, each with the alternative that was rejected and the evidence file
  that decided it. The P3-* entries are the precedent.
- **Record deviations, shortfalls and achieved counts, not intended ones.** If you run 50 replications where 200 were
  pre-registered, the report says 50, states what that costs in power, and marks the verdict undecided if it is.
- **Report failures as failures, with evidence, and withdraw your own conclusions when they turn out wrong.** Phase 1
  withdrew two mid-phase, Phase 2 one after review, Phase 3 one after review plus a correction to the reviewer; that is
  the standard, not an embarrassment.
- **Write the report as you go, not at the end.**

**On the environment and the repository.**

- **Execution order.** Anything that changes the environment after the state is frozen restarts from step 0: re-freeze,
  re-audit, new hashes. **Phase 4 changes the event block, so it will pay this in full** — budget for it. Phase 3's
  measured costs: path hashes 19 s · the 200-seed checklist ≈ 14 min · the SEP level-free audit ≈ 2.5 h · L5 at 40/50
  seeds ≈ 1 h · the freeze 3 s. If your edits are provenance-only, prove it the way P3-17 did: regenerate the path
  hashes and compare (Phase 3's label edits moved 0 of 190 hidden columns).
- **Reproducibility of any offloaded computation.** Phase 1 found a model-fitting result computed on Kaggle that did not
  reproduce locally while a different audit reproduced to three decimals; the cause is still unknown. **Simulation and
  optimisation offload safely; model fits do not.** Before using any number from another machine, reproduce the
  reference row there — **and note that Phase 3 finally exercised this guard: `python -m tools.phase2.e2_3_smm
  --reference-row` on the Kaggle kernel agreed with the committed file to 6.4 × 10⁻¹⁶ across different numpy/scipy
  versions.** Every audit, L5 and surrogate number still comes from the local machine only.
- **Make every long run resumable and serial.** Cache per unit of work, skip what exists, and watch memory.
  `tools/phase2/phase2_chain.py` is the working pattern.
- **Do not modify** `envs/v1/`, the plan, the alternatives register, or anything under `v2_1/archive/`. **`envs/v2/`,
  `evaluation/` and `simulation/` may be touched only where the task is explicitly about them** — for Phase 4 that means
  `events.py`, `schedule.py`, the rejection and relabel logic in `generator.py`, the ordering factor in
  `experiments/arms_v2.py`, the day-index rendering in `synthetic_market.py`, and the tests. Every generator change
  should be a switch with the v2 behaviour behind it, as Phases 1–3 did. Commit messages are one line with no trailer
  (`CLAUDE.md`); commit and push only when asked.

## Compute: where to run what

**The rule that governs all of them: go faster by running independent stages in parallel, never by cutting a
pre-registered sample size.** If compute forces a reduction, fix the reduced design *before* the run, state the achieved
count and its power cost, and mark the verdict undecided if the smaller sample cannot decide it.

### 1. The laptop — the reference environment

An i5-1135G7: **4 physical cores, 8 logical**, 15.7 GB RAM. It is the machine every reported surrogate/audit number must
come from. Phase 3's measured costs are the best guide you have: four concurrent Python processes saturate it (use
`--workers 2–3` with `OMP_NUM_THREADS=2`); memory is what kills it, not CPU. Measured in Phase 3: the SEP level-free
audit ≈ 2.5 h · a 200-seed checklist ≈ 14 min · L5 at 40/50 seeds ≈ 1 h · a constrained SMM cell (200 paths, DE 40,
200 MC replicates, 30 refits) ≈ 77 min · a 30-panel QML recovery grid ≈ 2 h at 3 workers · the calm-trained surrogate on
two stored 1,600-path panels ≈ 23 min · the full test suite ≈ 51 min · 800 generated 200-day paths ≈ 4 min.
**A foreground command in this harness times out at 10 minutes; run anything longer in the background and block on a
condition (`until [ -f <output> ]; do sleep 60; done`) rather than polling.** Two Windows-specific traps Phase 3 hit:
`ProcessPoolExecutor` cannot spawn from a `python - <<EOF` heredoc (write a real module file), and a backgrounded run
whose stdout is buffered can look dead — use `python -u`.

### 2. Kaggle — the default offload, and now a *proven* one

Verified live: client **Kaggle CLI 2.2.4**, account **`ayeshaiq`**, `auth_method: ACCESS_TOKEN`. **The bundle is current**:
`ayeshaiq/finpersona-phase3-bundle` was created and versioned during Phase 3 (`envs/ evaluation/ agent/ simulation/
tools/ tests/ pyproject.toml` plus the `generated/v2_1` inputs a kernel reads) — version it again rather than building a
new one. **`datasets/` must never be uploaded** (third-party data with redistribution restrictions); cache the derived
statistics and ship those, as `e2_3/data_moments.json` and `e3_3/episodes.json` do.

**The cross-machine guard is no longer unproven.** Phase 3 ran `fp-p3-refrow` (the reference row on the kernel) and it
agreed with the committed `e2_3/reference_row.json` to a worst relative difference of **6.4 × 10⁻¹⁶** under
numpy 2.0.2 / scipy 1.16.3 against the laptop's 2.4.6 / 1.18.0. Run it again on your first kernel (it costs ten minutes),
then offload freely. Kernel pattern: `kernel.py` + `kernel-metadata.json` (`kernel_type: script`, `enable_internet:
false`, `dataset_sources: [the bundle]`); the script walks `/kaggle/input` for `pyproject.toml`, copies the repo to
`/tmp/repo`, runs the stage with `PYTHONPATH`, and copies outputs to `/kaggle/working/out`; then `kernels push -p <dir>`,
`kernels status`, `kernels output -p <dir>`. A 4-vCPU kernel ran E3.4's whole four-stage chain (calibration at 60 seeds
× 3 iterations, three 200-seed mechanism arms, a 200-seed flat arm) in **≈ 10 minutes**.

**What to send there**: E4.1's LPPLS fits (embarrassingly parallel by episode), E4.6's four formulations × 200 crash and
200 bull seeds, E4.5's four control definitions × 200 seeds, E4.7's ordering-mix sweeps — all simulation and
optimisation. **What not to send**: anything whose number you will report from a scikit-learn model fit — the leakage
audits, L5, any surrogate R².

### 3. The lab GPU box — do not use until the team says access is confirmed

Status as of 31 Aug 2026: the 2×4090 container at `109130cy78xp1.vicp.fun` port `24761` is reachable but **rejects our
key**. **Do not spend time probing it.** If the team confirms access, check `nproc` and the cgroup memory limit first,
run under `tmux`, pin library versions, and reproduce a reference row before reporting any model-fitting number from it.

## Inherited open items

- **`test_sustained_bull_selection` is yours to close** (items 18, 42, strict xfail) — the last non-Phase-6 entry in the
  known-defect registry. Closing it empties everything but the two Phase-6 leakage gates.
- **The four measured event defects** listed in "Context": the rise time the schedule owns, the stale hazard, the
  ex-post blow-off label, and the drift-dominated post-top.
- **The level anchoring** (+30.5 % on the deployed unconditional) — a team decision that changes what you build on.
- **MCR is undefined on 10 % of sustained-bull runs** and coverage there is 0.044. Phase 7 owns the metric's
  specification, but E4.5's definition is what determines whether the case arises at all.
- **The event-phase leakage channel** — all-phase full-field R²(x) 0.843, and ≈ +0.15 of the calm-trained level-free
  channel attributable to events and sentiment (E3.8). Phase 6 owns the gate; your redesign is what could move it.
- **Legacy engines' stored burn-in states are stale** under the Phase-3 GARCH shape (`params/burn_in_states_*.npz`,
  sampled under v2's shape). Any sensitivity that runs `fw_fallback_hl150` / `fw_hl60` / `fw_index` / `pruna` / `ar1`
  must regenerate them first (`tools/phase1/e1_5_burn_in.py --write-states`); the engine in force is guarded fresh.
- **The L2b phase-clock gate** (+12.7 pp against a 10 pp margin) and the **L2 absolute gate** are registered to Phase 6;
  leave them, but note that the *event* block is now the strongest phase signal in the environment, so E4.6's and
  E4.7's choices are the ones most likely to move L2b.

## My recommendation for how to begin, and why

1. **Put the level-anchoring question to the team in your first message, then start E4.1 while you wait.** It is the one
   decision that can invalidate work done before it, and E4.1 is panel-side — it does not depend on the generator's
   level at all.
2. **Do E4.1 properly before anything else, because four later experiments are defined by its output.** E4.2's ranges,
   E4.3's hazard cross-check, E4.6's depth/duration coverage rule and its rejection ceiling all read from the episode
   tables. Phase 3 handed you the drawdown and run-up families; what it did not compute is exactly what E4.1 adds.
3. **Treat E4.6 as the phase's hardest deliverable, not E4.5.** Four formulations, two of which (B and D) change what
   δ *means* — from a target to a belief shift — and therefore what checklist item 10 is even testing. Budget for the
   re-expression, and write the script-share statistic first: it is the cheapest way to find out that a formulation is
   more scripted than it looks.
4. **Expect the rise-time target to force a schedule change that moves everything downstream.** Getting from 75.5 d to
   30 d means shorter deterioration and more front-loaded panic, which changes depth, duration, rejection rates and the
   phase multipliers' realised ratios. Re-run E3.4's closed-loop calibration afterwards rather than leaving the
   multipliers nominal, and re-check the panic ratio against 7.45 [6.86, 8.13].
5. **Copy Phase 3's discipline on conditionality and on intervals.** Every number you fit is conditional on something
   (the panel, the level anchor, the engine); say so in the label. And no parameter entry ships without an interval —
   Phase 3's review found its most-used parameter with `"interval": null` and the report quoting a *different*
   parameter's interval in that column.
6. **Re-run the two diagnostics at the end** (`e3_7_discrimination.py` and `e3_8_decomposition.py`, plus
   `after_state.py`). They cost about four hours together and they are what tell the team whether your event redesign
   moved the benchmark's discriminating power or its leakage. Phase 3 learned this from Phase 2's review: the phase that
   changes the environment is the phase that should measure what the change did.
7. **Expect at least one pre-registered criterion to be undecidable, and plan the addendum for it.** Four phases in a
   row have had one — Phase 3 had three. Simulating the null at the intended sample size, as runnable code, before
   committing to a threshold, is the cheapest insurance in this programme.

## Deliverable of this request

`PREREG_PHASE_4.md` (before any run), the code and results under `tools/phase4/` and
`docs/env_v2/generated/v2_1/e4_*/`, `envs/v2/params/events.json` with provenance and a loud loader, the tests of
Section 8.4, a refreshed freeze manifest and path hashes with the checklist and level-free audit regenerated on the
handed-over state, the re-run discrimination and decomposition tables, DECISION_LOG entries P4-*,
`PHASE_4_CHANGED_FILES.md`, and **`PHASE_4_REPORT.md`**. Then stop for review — do not begin Phase 5.
