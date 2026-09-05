# Prompt: execute Phase 3 of the v2.1 improvement plan (volatility: GARCH, jumps, regime variance and implied volatility)

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
| 4–14 | **Phases 0–10**, one section each. Phase 0 verification/freeze · 1 value and price structure · 2 mispricing engine · **3 volatility (yours, Section 7)** · 4 events and schedule · 5 observables · 6 audits and checklist methodology · 7 targets, action and metrics · 8 harness and statistics · 9 LLM sensitivity · 10 documentation |
| 15 | Cross-phase compute, cost and effort |
| **16 / 16A** | **Order, dependencies, and the go/no-go checkpoint** (written in advance, not to be moved) |
| 17 | Decisions only the team can make |
| A / B / C | Power-analysis formulas · the analytic level-free bound for x · numbers to be recomputed |

Around it:

- `V2_1_ALTERNATIVES_REGISTER.md` — for each contested design choice, the alternatives and **the experiment that would
  decide between them**. **REG-6 (regime variance mechanism and the IV construction) is yours**; REG-15 (data and
  survivorship) applies to every fit you make.
- `docs/env_v2/README.md` — the layout, the reading order and the regeneration commands.
- `spec/E1_V2_GENERATOR_SPEC.md` and `spec/IO_CONTRACT.md` — v2 as actually built. **Section 4 (volatility) is the one
  you rewrite**; Section 2 (mispricing) was rewritten by Phase 2 and shows the expected form.
- `reviews/review_{A,B,C}_*.md` and `reviews/V2_WEAKNESSES.md` — the three reviews and the 74 findings.
- `preregistration/` — v2's original thresholds and every amendment to them. **Amendment A3 (whole-variance scaling) is
  the one Phase 3 revisits with evidence.**
- `decisions/DECISIONS_13_1.md` and `decisions/DECISION_LOG.md` — the signed decisions and the running log; **the P0-*,
  P1-* and P2-* entries are the precedent for how yours should read.**
- `generated/` — every machine-written result, `generated/v2_1/` being this programme's.

## Context for this phase

**Phases 0, 1 and 2 are done, reviewed and committed** (Phase 2 at `b563e9d`, 2 September 2026). E1.0 (the data panel) is
downloaded. You are to execute **Phase 3**: fit the volatility block — the GJR-GARCH-t parameters, the jump rate and
size, the phase variance multipliers, *how* the regime enters the variance, and an implied-volatility construction that
is neither a phase marker nor a look-ahead.

Two things make this phase different from the two before it.

**First, Phase 3 is the phase that closes a loop.** Phase 2's engine was fitted *conditional on* the GARCH shape E3.1
measured (α 0.027, γ 0.058, β 0.932, ν 4.86) while the generator still runs v2's CAL shape (0.10 / 0.10 / 0.83 / 5).
That mismatch is a **registered known defect owned by you** (`tests/known_defects.py`,
`tests/test_v2_1_phase_2.py::test_garch_shape_matches_e3_1`, strict xfail). When you put a fitted volatility block in
force you change the shape the engine's σ_V, half-life and `sbar` were identified against — so **Phase 3 must decide,
and pre-register, whether the Phase-2 SMM is re-run on the new volatility block.** Treat that decision as a first-class
deliverable, not an afterthought: it is the analogue of Phase 1's σ_V hand-over, and Phase 2's tooling
(`tools/phase2/e2_3_smm.py`, `engines.py`, `moments.py`, the cached data moments and weight matrices) makes the re-run a
re-launch rather than a rebuild.

**Second, you own the field the reviews called the worst leak.** Implied volatility currently jumps by a factor of 1.9
on the first panic day (z ≈ 7 against the calm day-to-day sd of log IV), because the phase multiplier enters the
conditional variance and the 21-day forecast deterministically. That is weakness 46, it is `test_iv_continuity`'s strict
xfail, and E3.5 is where it is fixed.

Do not work from anything in `docs/env_v2/v2_1/archive/`, and do not edit the plan or `V2_1_ALTERNATIVES_REGISTER.md`.

## Read first, in this order

1. `docs/env_v2/README.md` — layout, reading order, regeneration commands.
2. The plan: Section 1 (the protocol every phase follows), Section 3 (data and biases), **Section 7 (Phase 3, in full)**,
   Section 16 (order and dependencies), 16A (the go/no-go checkpoint — written in advance and not to be moved),
   Section 17 (team decisions), Appendix A.
3. `V2_1_ALTERNATIVES_REGISTER.md`: **REG-6** (the variance mechanism and the IV construction — its decision rule is
   already written, including the power calculation), REG-15 (data and survivorship).
4. **What Phase 2 established — read all four, in this order:**
   - `docs/env_v2/v2_1/PHASE_2_REPORT.md` — the whole report. §3.2 (the SMM and what the models miss), §4 (the parameter
     files and what is conditional on what), §5 (the open team decisions) and §7 (what was not done) are the ones you
     inherit directly.
   - `docs/env_v2/v2_1/PREREG_PHASE_2_ADDENDUM.md` — four sections: three designs corrected before the runs they govern,
     and §4's post-review extensions. Read it as the worked example of what to do when a criterion turns out to be
     unmeetable at its stated sample size, and of how a review's pointers are answered with experiments rather than edits.
   - `docs/env_v2/v2_1/PHASE_2_CHANGED_FILES.md` — every file Phase 2 wrote or changed, with what each is.
   - `docs/env_v2/decisions/DECISION_LOG.md`, Phase 2 section, entries **P2-1 … P2-19**. **P2-9** (`sbar` recorded, not
     applied), **P2-12** (the GARCH shape mismatch), **P2-16** (σ_V is engine-conditional) and **P2-18** (the level-free
     surrogate is unbiased, so the generator's excess is a real channel) are the four that bind you.
5. Phase 1 and Phase 0, for the parts you build on: `PHASE_1_REPORT.md` §4.1 (E3.1, run inside Phase 1 because Phase 2
   needed it) and §4.3 (E1.4, where jumps belong); `PHASE_0_REPORT.md`; `generated/v2_1/findings_reproduction.md`.
6. The data panel: `datasets/README.md` (three caveats), `docs/env_v2/v2_1/E1_0_DATA_REPORT.md` (§1.2–1.3 survivorship
   and ticker reuse, §9.3 the usable panel), the per-folder READMEs — especially **`datasets/05_implied_vol/README.md`**,
   which is the input to E3.5 and is marked "fully satisfied", and `datasets/_manifests/`.
7. The code: `envs/v2/garch.py` (the block you re-fit), `envs/v2/observables.py::iv_block` and the `IV_PREMIUM` /
   `IV_PREMIUM_STRESS` / `IV_FLOOR` constants (the block you rebuild), `envs/v2/generator.py`, `envs/v2/mispricing.py`
   and `mispricing_params.py` (Phase 2's pattern for a loud parameter loader), `envs/v2/params/*.json`,
   `envs/synthetic_market.py`, `evaluation/*.py`, `tools/phase1/` and **`tools/phase2/`** (several tools are directly
   reusable — listed below), `tests/`, `tools/freeze_manifest.py` and `tests/v2_freeze_manifest.json`. `envs/v1/` is
   frozen and must not be modified.

## Decisions the team has taken

- **D1 (data): C, hybrid** — fit on the free panel, publish every fitted value with its survivor-vs-literature gap, keep
  the fitting code re-runnable on WRDS by a data-path change. WRDS access: `______` (not confirmed unless filled in).
- **D13 (start price): mechanism C** (`start_price_mode = "both"`). Applied and in force.
- **D16 (programme): full programme.** Phase 3 now, in its own session.
- **D3 (σ_V, h, s_x): applied as option (b)** — σ_V entered Phase 2's SMM as a free parameter and the fitted value
  (0.01220 [0.01066, 0.01419]) is in `value.json`, labelled **FIT, conditional on the engine and on E3.1's GARCH shape**,
  with a note that it is expected to move again at Phase 3. **The team has not yet answered Phase 2's §5.1** — whether to
  keep the fitted environment, keep v2's, or run both as a factor, given that the fitted mispricing is ±2–3 % at a
  5–13-day half-life. That answer is `______`. **If this blank is empty, proceed on the environment as handed over and
  say so in your report's §2**; do not re-tune the engine to change coverage, and flag anything in Phase 3 whose value
  would differ under the alternative.
- **D2 (LLM roster/budget) and D10 (dividends):** not taken; nothing in Phase 3 needs them (D10 is needed before Phase 5).

If something you need is not decided here, do every part that does not depend on it, then stop and ask with the options
and the evidence laid out. Never fill a blank with your own preference.

## What Phase 2 hands you (do not redo this work)

- **The engine.** `ar1_fit` = AR(1)+GJR-GARCH-t, half-life **7.50 d [3.81, 23.61]**, σ_V **0.01220 [0.01066, 0.01419]**,
  `price_scale = 1`, in `envs/v2/params/mispricing.json` with full provenance and a loud loader
  (`envs/v2/mispricing_params.py`). It was adopted by a pre-registered asymmetric rule after **no engine was accepted**
  on either criterion and the held-out prediction was a dead heat; the Franke–Westerhoff engine, fitted freely on
  2000–2016, **turns its own switching off**. `e2_4/decision.md`, `engine_diagnostics.json`.
- **`sbar` is fitted and deliberately NOT applied — it is yours.** E2.3 returned **0.00870 [0.00659, 0.01298]** against
  v2's CAL 0.017, and Phase 2 recorded it under `mispricing.json → applied.sbar_fitted_not_applied` rather than writing
  it, because the unconditional x-innovation scale is a volatility parameter and PLAN §7 gives it to you (E3.1 adopts the
  per-stock median unconditional sd; E3.4 decides how the regime enters). **Reconciling E2.3's 0.0087, E3.1's
  unconditional daily sd of 0.0218 and the 0.017 in force is a Phase-3 deliverable**, and the three are not the same
  quantity — say which is which before you adopt one.
- **E3.1 is already run** (inside Phase 1, because E1.4 and Phase 2 needed it): per-stock GJR-GARCH(1,1)-t fits on set A
  (417 names) and set B (155), full sample and four sub-periods, with 1,000-resample stock bootstraps —
  `generated/v2_1/e3_1/summary.{md,json}`, `garch_fits.csv`, **`residuals.parquet`** (the standardised residuals E3.2's
  jump detection runs on). Set-A full-sample medians: α 0.027 [0.025, 0.030], γ 0.058 [0.055, 0.061], β 0.932
  [0.928, 0.935], ν 4.86 [4.73, 5.02], persistence 0.991, unconditional daily sd 0.0218 [0.0210, 0.0225]. Sub-period
  persistence runs 0.946 (2013–19) to 0.994 (2000–07). **Phase 3 confirms and documents this fit — it does not redo it —
  and decides which of the medians, P25 and P75 sets goes into force and which are sensitivities.**
- **The jump placement is settled and the size is not.** E1.4 chose `jump_placement = "x_zero"` by a pre-registered KS
  rule; the **rate (0.010/day) and size sd (0.03) are still CAL** from v2's E1 calibration and are explicitly labelled
  "Phase 3 re-fits" in `value.json`. E1.4 also fitted the announcement/non-announcement split from the panel
  (`p_ann` 0.2737, `lam_res` 0.005655, from q = 0.4345 [0.412, 0.456] on n = 7,492 jump days) — **that split is FIT and
  you keep it; what you fit is the rate and the size distribution.**
- **The E[x] defect is closed and must stay closed.** On the adopted engine E[x] in flat markets is −0.00013
  [−0.00087, +0.00064] with jumps on. If your jump re-fit moves the mean of x, `test_flat_x_equivalence` will catch it —
  it is a hard test again.
- **The leakage baseline you will be measured against.** On the standard evaluation panel the handed-over state gives
  level-free calm R²(x) **0.339 [0.208, 0.434]**, full-field calm **0.346**, all-phase full-field 0.731, and L2b
  macro-phase selectivity **+15.4 pp** against its 10 pp margin (a registered Phase-6 defect). `e2_6_after/`.
- **A result that tells you what to expect from your own changes.** E2.8 showed the level-free surrogate is **not
  biased**: on the exact Appendix-B process it measures 0.241 against an analytic bound of 0.245. The generator's 0.339
  is therefore a **real channel worth ≈ +0.10 of R²**, contributed by the four blocks the exact process lacks — the
  scripted events and their drift, **the jumps**, **the GJR innovation** and the sentiment feedback. **Phase 3 changes
  two of those four.** You are in a position to decompose part of that +0.10 almost for free, by re-running
  `tools/phase2/e2_8_bound_check.py` with one block added at a time. Phase 6 owns the gate; the decomposition is a
  cheap, high-value thing for you to hand it.
- **The discrimination baseline.** `e2_7/discrimination.md` gives the 16A G1 ordering and the policy spread on the
  handed-over state, per scenario, with paired bootstrap intervals. **Re-run it after your volatility block is in force**
  — the panic multiplier and the jump size both move sd(x) and therefore coverage.
- **Reusable tools.** `tools/phase2/`: `moments.py` (FW's nine plus the persistence moments, the joint stock × block
  bootstrap), `e2_3_data.py` (the cached data moments and weight matrices — no third-party data has to move),
  `e2_3_smm.py` (the SMM, both acceptance criteria, profiles, refits, the machine reference row), `engines.py`,
  `e2_6_sweep.py` (the sweep pattern, with a calibration that can be extended), `e2_7_discrimination.py`,
  `e2_8_bound_check.py`, `after_state.py` (hashes, checklist, level-free audit, freeze — **run this at your hand-over**),
  `apply_e2.py` (the pattern for writing a parameter file with provenance), `phase2_chain.py` (resumable stage runner),
  `phase2_numbers.py`. `tools/phase1/`: `panel.py` (the exclusion rule and analysis sets), `e3_1_garch.py` (the fits
  themselves), `e1_4_panel.py` (the panel-side jump work E3.2 extends), `kalman_bound.py`.

## What to do now: Phase 3, Section 7 of the plan

1. **Pre-register before running anything** — `docs/env_v2/v2_1/PREREG_PHASE_3.md`: the panel and windows, seeds,
   estimators, the exact statistic, the pass/fail or decision rule, the power analysis that sets each sample size, and
   what will be reported if a rule is not met. **Check each criterion is decidable at the sample size you state** —
   simulate the statistic's spread under the null before you commit to the threshold, and keep the script. Phase 1 lost
   time to three criteria that could not be met by any result and Phase 2 to one; each cost a re-run that a five-minute
   simulation would have prevented.
2. **Decide and pre-register the engine-refit question** (see "Context", first point). The options are: (a) re-run
   Phase 2's SMM on the new volatility block and adopt the new (σ_V, h, sbar); (b) keep Phase 2's engine and record the
   conditioning as a permanent caveat; (c) run both as a sensitivity. Whichever you choose, the known-defect entry
   `test_garch_shape_matches_e3_1` must end the phase either **passing** or **re-registered with a new owner and reason**.
3. **E3.1 — confirm and document.** The fits exist; what Phase 3 adds is the adoption decision (median vs P25/P75), the
   sub-period story, the survivor gap stated beside the literature (Engle 2001's portfolio α 0.077 / β 0.905 is *not* a
   per-stock anchor and the report must say why), and the reconciliation of the three "volatility scale" numbers above.
4. **E3.2 — jumps.** Lee–Mykland-type detection at a pre-registered threshold on E3.1's standardised residuals; rate per
   year, mean and sd of jump sizes, negative share, and the announcement-day split (E1.4's `q` is the target). Adopt the
   FIT rate and size distribution for the `x_zero` placement E1.4 chose. Andersen–Bollerslev–Diebold's 14.4 % jump share
   and 27.9 % of days are **index-level anchors printed beside**, never tolerances.
5. **E3.3 — phase variance multipliers from event windows**, on the panel's own episodes: single-stock drawdowns ≥ 30 %,
   run-ups ≥ 100 % over two years, and the market-wide crash windows; realised variance in windows defined relative to
   the trough/peak, divided by the pre-event calm variance; medians with bootstrap CIs and the episode count stated. The
   plan's two index examples are not a sample.
6. **E3.4 — how the regime enters the variance (REG-6).** Three mechanisms — whole-variance scaling (v2, amendment A3),
   ω-scaling with a FIT ramp, and a fitted two-regime switching-variance model — decided by the empirical **rise time and
   decay half-life** measured in E3.3, under the rule REG-6 already states: adopt the mechanism whose rise time and decay
   half-life both fall inside the empirical 95 % CI; if two do, the one with fewer free parameters; if none does, report
   all three against the CI and keep A as the documented shortfall. **Run all three. Never run only the option you
   expect to win.**
7. **E3.5 — implied volatility without a step or a look-ahead.** Build IV_t = √(252·σ̂²_{t+1..t+21})·(1 + π_t)·e^{ε_t}
   with σ̂² from a GJR-GARCH filter run on the **observed returns only**, π_t FIT from the five CBOE single-stock VIX
   histories (`datasets/05_implied_vol/cboe/VX{APL,AZN,GOG,GS,IBM}`, 2011–2026) against those names' realised variance,
   and ε_t FIT from the residual of the IV–RV regression. Pre-registered checks: (i) a code test that no field uses
   information from t+1 onwards; (ii) the onset-detection audit **in REG-6's corrected form** — IV's change-point
   detectability at phase transitions is compared against *the same filter's* 21-day realised-variance forecast, so the
   premium's legitimate rise through returns is not counted as a leak, with the label-permutation null as the yardstick.
   The `IV_PREMIUM_STRESS` decile trigger and the whole-path quantile are **removed**.
8. **E3.6 — item 73.** Checklist item 5 (GARCH persistence recoverable) computed on calm windows only *and* on the whole
   path, both reported.
9. **Tests, parameter file, freeze** — Section 7.4's tests (`test_garch_params_in_force`, `test_iv_no_lookahead`,
   `test_iv_continuity` flipped to **hard** with the tolerance E3.5 derives, `test_jump_process`); a new
   `envs/v2/params/volatility.json` with label / source / date / interval / n on every entry, following
   `mispricing.json`'s pattern and its loud loader; rewrite the freeze manifest and the path hashes on the state you hand
   over, and regenerate the checklist and the level-free audit there (`tools/phase2/after_state.py` does all four).
10. **`PHASE_3_REPORT.md`** under the same six headings Phases 1 and 2 used, then stop.

## Hard rules (from the plan; not optional)

**On assuming nothing.**

- **Every parameter is fitted or tested on data, never stipulated.** If a value cannot be fitted from the free panel,
  label it DESIGN or CAL with the reason, and say what would settle it.
- **Verify inherited numbers rather than trusting them — including mine.** Phase 1 re-derived Phase 0's constants and
  found two of its own conclusions wrong; Phase 2 found the plan's SABCEMM target inverted, Phase 1's `s_x_fit` wrong by
  a factor of five, and — after review — withdrew its own first reading of the sub-period acceptance. Before you build on
  any figure in the Phase-2 report, check it against the file it cites. If a number in a document and a number in
  `generated/` disagree, the generated file wins and the document is corrected.
- **Read sources at first hand.** A paper's number may be quoted beside a fitted value as an anchor, never used as a
  tolerance, and never cited from a secondary source. If you cannot read it at source, say so and do not quote it.
  **Hamilton & Susmel (1994) is specifically flagged as not retrievable and may not be quoted.**
- **State the n and the interval on every number.** A point estimate with no n is not a result.

**On experimenting rather than deciding.**

- **When two approaches are defensible, run both and compare — do not choose by argument.** REG-6 names three variance
  mechanisms because the question is empirical.
- **Include the incumbent as a candidate, and the simplest thing that could work.** v2's whole-variance scaling is a
  candidate in E3.4, not a straw man; A3 is revisited *with evidence*, not overturned by preference.
- **When a result surprises you, design the experiment that distinguishes the explanations.** Phase 2's most useful
  results came from exactly this: the FW engine collapsing to an AR(1) on the training window, and the surrogate run on
  the exact process to separate a biased estimator from a real channel.
- **Report both arms even when one wins decisively.** The losing configuration's numbers are what make the winner
  credible, and Phase 6 and the deck will need them.

**On documenting everything.**

- **Pre-register before running anything, and never move a threshold after seeing data.** If a criterion turns out to be
  wrong, say so, derive the corrected one in a *separate documented step before* the re-run, **disclose what you had
  already seen when you wrote the correction**, and report the result under both the old and the new rule.
  `PREREG_PHASE_2_ADDENDUM.md` is the template, including its disclosure paragraphs and its §4 post-review extensions.
- **Every run writes a file.** Results go to `docs/env_v2/generated/v2_1/e3_*/` as JSON (machine-readable, with the
  design block: seeds, n, counts) *and* Markdown (the table a human reads). The report cites the file; the file is
  regenerable by the command in its own docstring.
- **Every parameter entry carries label / source / date / interval / n / survivor-vs-literature gap**, and — Phase 2's
  addition — **states what the fit is conditional on** where that is not obvious.
- **Log every decision** in `DECISION_LOG.md` as P3-*, each with the alternative that was rejected and the evidence file
  that decided it. The P2-* entries are the precedent.
- **Record deviations, shortfalls and achieved counts, not intended ones.** If you run 50 replications where 200 were
  pre-registered, the report says 50, states what that costs in power, and marks the verdict undecided if it is.
- **Report failures as failures, with evidence, and withdraw your own conclusions when they turn out wrong.** Phase 1
  withdrew two mid-phase and Phase 2 withdrew one after review; that is the standard, not an embarrassment.
- **Write the report as you go, not at the end.**

**On the environment and the repository.**

- **Execution order.** Anything that changes the environment after the state is frozen restarts from step 0: re-freeze,
  re-audit, new hashes. **Phase 3 changes the volatility block, so it will pay this in full** — budget for it. Phase 2's
  `tools/phase2/after_state.py` runs the four stages; the SEP level-free audit is the expensive one (≈ 2 h).
- **Reproducibility of any offloaded computation.** Phase 1 found a model-fitting result computed on Kaggle that did not
  reproduce locally (calm R² 0.41 vs 0.15 on identical code, seeds and panel) while a different audit on the same two
  machines reproduced to three decimals; the cause is still unknown. **Before using any number from a machine other than
  the one you report from, reproduce a known reference row on that machine, on the same kind of panel the result will
  use.** Simulation and optimisation offload safely; model fits do not. Phase 2 sidestepped the question entirely by
  running everything locally — that is available to you and is the stronger choice where the cost allows.
- **Make every long run resumable and serial.** Cache per unit of work, skip what exists, and watch memory.
  `tools/phase2/phase2_chain.py` and `tools/phase1/phase1_chain.py` are the working pattern.
- **Do not modify** `envs/v1/`, the plan, the alternatives register, or anything under `v2_1/archive/`. **`envs/v2/`,
  `evaluation/` and `simulation/` may be touched only where the task is explicitly about them** — for Phase 3 that means
  `garch.py`, the IV block in `observables.py`, the jump parameters in `generator.py`/`value.json`, and the tests. Every
  generator change should be a switch with the v2 behaviour behind it, as Phases 1 and 2 did. Commit messages are one
  line with no trailer (`CLAUDE.md`); commit and push only when asked.

## Compute: where to run what

Three machines are in play. **The rule that governs all of them: go faster by running independent stages in parallel,
never by cutting a pre-registered sample size.** If compute forces a reduction, fix the reduced design *before* the run,
state the achieved count and its power cost in the report, and mark the verdict undecided if the smaller sample cannot
decide it.

### 1. The laptop — the reference environment, and what Phase 2 measured on it

An i5-1135G7: **4 physical cores, 8 logical**, 15.7 GB RAM of which typically ~5 GB is free. It is the machine every
reported surrogate/audit number must come from. Phase 2's measured costs, which are the best guide you have:

- **Four concurrent Python processes saturate it.** Each got ~97 % of a core with four running; adding a fifth cost about
  30 % throughput across the board. Use `--workers 2–3` with `OMP_NUM_THREADS=2`.
- **Memory is the thing that kills it, not CPU.** The SEP level-free audit (1,600 paths, 320,000 rows) peaks at ~1.5 GB;
  two of those at once hung the machine twice during Phase 1. Check free RAM before launching a second heavy job.
- Measured: one SMM cell 1.5–3 h · the full-panel block bootstrap (500 resamples × 6 periods) ≈ 40 min · the SEP
  level-free audit ≈ 2 h · a 200-seed checklist ≈ 12 min · a 100-seed level-free surrogate ≈ 15 min · the L5 policy
  table at 40/50 seeds ≈ 1 h · 200 runs × 6,750 steps of a pure simulator, seconds.
- A foreground command in this harness times out at 10 minutes; run anything longer in the background and block on a
  condition (`until [ -f <output> ]; do sleep 60; done`) rather than polling.

### 2. Kaggle — the default offload, use it freely

**Verified live on 2 September 2026** (`python -m kaggle config view`, `datasets list --mine`, `kernels list --mine`):
client **Kaggle CLI 2.2.4** (pip package `kaggle`), account **`ayeshaiq`**, `auth_method: ACCESS_TOKEN` with the token at
`~/.kaggle/access_token`. **Not verifiable from the CLI and carried forward unchecked**: the CPU kernel limits
(4 vCPU / 30 GB / 12 h), the five concurrent sessions, and the absence of a weekly CPU quota (the 30 h/week limit is
GPU-only and irrelevant — the code is NumPy/SciPy/scikit-learn with no GPU path). Treat those four as the previous
phases recorded them, not as facts this prompt confirmed.

- **The bundle is stale — refresh it before you use it.** `ayeshaiq/finpersona-phase1-bundle` exists (18.1 MB) but was
  last updated **2026-08-30 08:01**, which is *before* all of Phase 2. It contains none of `tools/phase2/`,
  `envs/v2/mispricing_params.py`, `params/mispricing.json`, the applied `value.json`, or the `e2_*` inputs a Phase-3
  kernel would need. Either version it (`python -m kaggle datasets version -p <stage> --dir-mode zip -m "…"`) or make a
  `finpersona-phase3-bundle`. The staged copy is `envs/ evaluation/ agent/ simulation/ tools/ tests/ pyproject.toml`
  plus the `docs/env_v2/generated/v2_1` inputs the kernel reads.
- **`datasets/` must never be uploaded** — third-party data with redistribution restrictions. Cache the derived
  statistics and ship those instead; `e1_2/smm_data_moments.json` and `e2_3/data_moments.json` (moments + the
  block-bootstrap draws + the weight matrices) are the precedents, and they are why a Phase-2 SMM re-run can go to a
  kernel at all.
- **The kernel pattern is proven.** `kernel.py` + `kernel-metadata.json` (`kernel_type: script`,
  `enable_internet: false`, `dataset_sources: [the bundle]`); the script copies the repo to `/tmp/repo` — locate it by
  walking `/kaggle/input` for `pyproject.toml`, since Kaggle may or may not extract the zip — runs the stage with
  `PYTHONPATH`, and copies outputs to `/kaggle/working/out`. Then `kernels push -p <dir>`, `kernels status`,
  `kernels output -p <dir>`. Ten Phase-1 kernels ran this way (`fp-p1-rec-*`, `fp-p1-l5-after`, `fp-p1-audit-after-*`),
  most recently 2026-08-30 09:37.
- **What to send there**: E3.3's episode bootstrap, E3.4's three-mechanism generator comparison at 200 seeds per
  mechanism, any re-run of the Phase-2 SMM, E3.5's premium simulations — all simulation and optimisation, which offload
  safely. One kernel per independent slice; merge the caches locally (`tools/phase1/merge_recovery_caches.py` shows the
  pattern).
- **What not to send**: anything whose number you will report from a scikit-learn model fit — the leakage audits, L5,
  any surrogate R². Two of the ten Phase-1 kernels above (`fp-p1-audit-after-lf`, `fp-p1-l5-after`) are **the very runs
  that did not reproduce locally**, which is what turned this into a rule.
- **The reproduction check exists but has never been exercised cross-machine.** Phase 2 built it —
  `python -m tools.phase2.e2_3_smm --reference-row` writes `e2_3/reference_row.json` (the pooled 17-moment vector of all
  three engines at a fixed θ and CRN seed, to full precision) and `tests/test_v2_1_phase_2.py::test_smm_reference_row`
  asserts it to ten significant figures — but Phase 2 then ran everything locally, so **the file has only ever been
  checked against the machine that wrote it.** Before you use a single number from a Kaggle fit, run that command *on
  the kernel* and diff it against the committed file. If it differs, that machine may run simulation and optimisation
  only. This is the cheapest possible guard and it is currently unproven; proving it is worth ten minutes of your first
  kernel.
- Observed Kaggle timings, from **Phase-1 workloads** on the 4-vCPU kernel and kept only as a rough laptop-vs-Kaggle
  ratio (they are not Phase-3 workloads): full-panel leakage audit ≈ 1.5 h, L5 ≈ 15 min, a 40-point sweep ≈ 20 min,
  300 SMM fits ≈ 7.7 h. Against the laptop's measured numbers above, a single Kaggle vCPU is roughly comparable to one
  of the laptop's cores; the win is the five concurrent sessions and the 30 GB, not per-core speed.

### 3. The lab GPU box — do not use until the team says access is confirmed

Status as of 31 Aug 2026: the replacement 2×4090 container at `109130cy78xp1.vicp.fun` port `24761` is reachable but
**rejects our key**; the owner has been asked to add the public key. **Do not spend time probing it.** If the team
confirms access, check `nproc` and the cgroup memory limit first, run under `tmux`, pin library versions to the laptop's
(Python 3.13, numpy 2.4.6, pandas 3.0.3, scipy 1.18.0, scikit-learn 1.9.0) and reproduce a reference row before reporting
any model-fitting number from it. Never upload `datasets/`.

## Inherited open items

- **The GARCH shape mismatch is yours to close** (`test_garch_shape_matches_e3_1`, strict xfail, items [12]).
- **`sbar` is yours to adopt** — fitted at 0.00870 by E2.3, measured at 0.0218 by E3.1, running at 0.017.
- **`test_iv_continuity` is yours to make pass** (items 46, 25), with the tolerance derived in E3.5, not chosen.
- **The bull-trap rejection rate is 0.94** under the adopted engine (0.06 before), because the scenario's acceptance
  condition was calibrated against a mispricing four times larger. It is **Phase 4's** to re-derive, but Phase 3, 4 and 5
  all run on it in the meantime. Phase 2's report raises whether Phase 3 should run on a temporarily relaxed condition;
  if you think it should, say so and put it to the team rather than changing the event block yourself.
- **The +0.10 of level-free R² the generator adds over the exact Appendix-B process** is unattributed among four blocks,
  two of which are yours. Decomposing it is cheap (`tools/phase2/e2_8_bound_check.py` with one block added at a time) and
  is the single most useful thing you can hand Phase 6.
- **MCR is undefined on runs with no resolvable step** (4 % of flat, 10 % of sustained-bull runs). Phase 7's, but your
  panic multiplier and jump size move coverage, so re-measure it when you re-run the discrimination table.
- **The L2b phase-clock gate** (+15.4 pp against a 10 pp margin) and the **L2 absolute gate** are registered to Phase 6;
  leave them, but note that E3.5 is the field most likely to move L2b, since IV is currently the clearest phase marker.

## My recommendation for how to begin, and why

1. **Settle the engine-refit question in the pre-registration, before any fit.** It determines whether E3.1's adoption is
   the end of a thread or the start of a loop, and it is the one thing that could double the phase's compute. My reading:
   fit the volatility block first, then re-run Phase 2's SMM **once** on the adopted block and report both engines — the
   tooling makes it a re-launch, and leaving σ_V and the half-life conditional on a shape you have just replaced would
   hand Phase 6 a parameter file whose provenance no longer holds.
2. **Do E3.3 before E3.4.** The mechanism decision is *defined* by E3.3's rise time and decay half-life; running the
   generator comparison first would invite reading the rule backwards from the arms.
3. **Treat E3.5 as the phase's hardest deliverable, not E3.4.** It is the only part that has to be *designed* rather than
   fitted: a filter that is past-only by construction, a premium fitted on five names, a noise term, and an audit that
   compares IV against the same filter's RV forecast rather than against nothing. Budget accordingly, and write the
   no-look-ahead test first — it is the cheapest way to find out that a construction leaks.
4. **Copy Phase 2's discipline on conditionality.** Every number you fit will be conditional on something (the panel, the
   engine, the placement); say so in the label. Phase 2's σ_V is the cautionary example: three estimates on the same
   panel with non-overlapping intervals, because each was conditional on a different engine.
5. **Re-run the two Phase-2 diagnostics at the end** (`e2_7_discrimination.py` and `e2_8_bound_check.py`, plus
   `after_state.py`). They cost about three hours together and they are what tell the team whether your volatility block
   moved the benchmark's discriminating power or its leakage. Phase 2 learned this from its own review: the phase that
   changes the environment is the phase that should measure what the change did.
6. **Expect at least one of your pre-registered criteria to be undecidable, and plan the addendum for it.** Three phases
   in a row have had one. Simulating the null at the intended sample size, as runnable code, before committing to a
   threshold, is the cheapest insurance in this programme.

## Deliverable of this request

`PREREG_PHASE_3.md` (before any run), the code and results under `tools/phase3/` and
`docs/env_v2/generated/v2_1/e3_*/`, `envs/v2/params/volatility.json` with provenance and a loud loader, the tests of
Section 7.4, a refreshed freeze manifest and path hashes with the checklist and level-free audit regenerated on the
handed-over state, DECISION_LOG entries P3-*, `PHASE_3_CHANGED_FILES.md`, and **`PHASE_3_REPORT.md`**. Then stop for
review — do not begin Phase 4.
