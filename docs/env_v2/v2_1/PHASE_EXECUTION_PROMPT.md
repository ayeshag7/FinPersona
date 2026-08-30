# Prompt: execute the v2.1 improvement plan, phase by phase, starting with Phase 0

## Context

FinPersona-Bench evaluates whether LLM trading agents keep to a persona's mandate over a multi-day synthetic market. The market environment was rebuilt once (v1 → v2). Three independent reviews found v2 not robust (a fixed start price that acts as an answer key, a mispricing model whose trader switching is inert, a flat control biased by jumps, fields that leak the hidden state once the anchor is removed, claims that exceed their evidence, an analyst-error bug, wrong sensitivity counts, and about 200 numeric choices of which only a dozen trace to published statistics). A ten-phase improvement plan was written, independently verified and corrected, and reviewed again. It is now the approved working document and you are to execute it.

**The working document is `docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.md`** (same content as the `.docx`/`.pdf` beside it). Every change it contains is tagged `[changed: reason]` or `[edit 27 Aug]` with a pointer to its evidence. Do not work from anything in `docs/env_v2/v2_1/archive/`.

## Read before doing anything, in this order

1. `docs/env_v2/README.md` (layout of the documentation tree and reading order).
2. `docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.md` in full, especially Section 1 (the protocol every phase follows), Section 4 (Phase 0), Section 16 (dependencies) and 16A (the go/no-go checkpoint), Section 17 (team decisions D1–D17), and Appendices A–B.
3. `docs/env_v2/v2_1/V2_1_ALTERNATIVES_REGISTER.md` (the 18 choices that are decided by experiment, not by preference; you will need REG-1, REG-3, REG-5 in Phase 1 and later ones as the phases come).
4. `docs/env_v2/reviews/V2_WEAKNESSES.md` (the 74 items the plan closes; the plan's Section 2 maps each to a phase) and the three reviews in `docs/env_v2/reviews/`.
5. `docs/env_v2/v2_1/reviews/V2_1_PLAN_VERIFICATION_LOG.md` (what was verified, what was wrong, which citations may and may not be quoted) and `review_of_pass3_verification.md` (the last review, including the numbers that could not be reproduced).
6. The environment itself: `envs/v2/*.py`, `envs/synthetic_market.py`, `envs/v2/params/*.json`; harness `agent/`, `simulation/`, `experiments/arms_v2.py`; evaluation `evaluation/*.py`; tools `tools/*.py`; tests `tests/`; specification `docs/env_v2/spec/`, decisions `docs/env_v2/decisions/`, pre-registration `docs/env_v2/preregistration/`, results `docs/env_v2/generated/`. The frozen v1 is `envs/v1/` and must not be modified.

## Decisions the team has taken (fill in before starting; leave blank if not yet taken)

- D1 (data): free substitutes now / pause for WRDS / hybrid — `______`
- D2 (LLM roster and budget tier for Phases 6, 8, 9) — `______`
- D10 (dividends paid into cash vs field removed; needed before Phase 5) — `______`
- D13 (start-price mechanism; provisional B = normalise the price, pending REG-1's Phase-9 test) — `______`
- D16 (full programme vs the minimal path first) — `______`
- Any other D-item already decided — `______`

If a decision you need is blank, do every part of the phase that does not depend on it, then stop and ask with the options and the evidence laid out (the register gives them). Never fill a blank with your own preference.

## What to do now: Phase 0 (Verification and freeze; no design changes)

Follow the plan's Section 4 exactly. In summary:

1. Write the pre-registration `docs/env_v2/v2_1/PREREG_PHASE_0.md` before running anything (what will be recomputed, with which seeds and statistics; which bugs will be fixed and what the test tolerance is; what counts as "reproduced").
2. Reproduction script `tools/verify_v2_findings.py` and its output `docs/env_v2/generated/v2_1/findings_reproduction.md` (every computational finding, with n, interval and the reviewers' value beside yours).
3. The bug fixes of 0.2 (analyst-error √5 scaling; sensitivity footers; MCR normalisation labels; day-1 gate input restricted to common-start cells; silent overrides made loud; the half-life and stale-number statements; item 73's small items; scenario counts and seed counts). Phase 0 makes code match documentation; it does not change any path's distribution by design. Anything that would is deferred and listed.
4. `docs/env_v2/v2_1/DECK_CORRECTIONS_NOW.md` (0.2b): the one-page note of numbers on the current slides that are wrong, so nobody presents them.
5. The freeze (0.3): `tests/test_v2_freeze.py` with the SHA-256 manifest over `envs/v2/**`, the facade, the params and the evaluation modules; `simulation/provenance.py` hashing the manifest.
6. The statistical regression tests (0.4) with the known-defect registry `tests/known_defects.py`; note that `test_half_life_consistency` is a hard test (it passes at 200,000 steps), and that the stationary sd(x) statement must use the reproduced 0.13–0.14, not the unreproduced 0.165, unless you reproduce 0.165 and say how.
7. The clean suite (0.5) and the execution-order rule (0.6).
8. `docs/env_v2/v2_1/PHASE_0_REPORT.md` under the six protocol headings, plus DECISION_LOG entries, corrected spec/calibration/PILOT_NOTES, and the list of every file you changed.

Then **stop** and wait for review. Do not start Phase 1.

## Hard rules (unchanged from the plan; they are not optional)

1. **Do not assume anything.** Every parameter, threshold, range and design choice traces to a read source (with URL/date and the read-and-correct / read-and-wrong / not-retrievable status) or to a stated experiment. "It was in the plan", "conventional", "reasonable" are not justifications. Numbers marked "(to verify)" may not enter a parameter file, a test tolerance or a slide.
2. **Do not make arbitrary suggestions.** Where evidence cannot settle a choice, present the alternatives with the discriminating experiment (the register's format) and stop.
3. **Research, experiment, test, then decide.** Pre-registration is written before data are seen and not moved afterwards; if a criterion is wrong, say so, derive the new one in a separate documented step, and report under both.
4. **Report failures as failures.** Every number with its n and an interval; before/after comparisons like for like; every tuned parameter labelled CAL where it appears; the provenance labels LIT / FIT / CAL / DESIGN (ESTIMATE only for effort numbers).
5. **Verify before you cite the repository's own documents**; several numbers are stale (the plan's Appendix C lists them).
6. **Scale of evidence** comes from the power rules in Appendix A, not from habit. Generator runs are free; **no paid API call in Phase 0**, and in later phases no paid call before the grid and its cost (at the prices in the plan's 0.4, with the 1.3× tokenizer factor for Claude 5 models) have been approved in that phase's pre-registration.
7. **Go/no-go 16A** is evaluated after Phase 6 exactly as written; G3 may not be passed by shortening the persistence below its fitted value.
8. **Git.** Stay on `main`; create no branches. **Do not commit, amend, reset, stash or push under any circumstances unless the user asks in that message.** Leave changes in the working tree and list every file you wrote or changed at the end of each phase. Do not modify `envs/v1/`, the v2 design plan in `docs/planning/`, or anything in `docs/env_v2/v2_1/archive/`.
9. Use the scratchpad directory for temporary files; deliverables go under `docs/env_v2/v2_1/` (documents), `docs/env_v2/generated/v2_1/` (results), `tests/` (tests), `envs/v2/params/` (parameter files with provenance).
10. When blocked on something only the user can decide, do everything that does not depend on it first, then ask.

## Deliverable of this request

Phase 0 complete as above, ending with `PHASE_0_REPORT.md`, the deck-corrections note, the findings reproduction, a green test suite with the known-defect registry printed, and the list of changed files. Stop there.
