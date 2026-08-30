# Prompt: independent verification and correction of the v2.1 improvement plan, with alternatives

## Context

FinPersona-Bench tests whether LLM trading agents keep to a persona's mandate over a multi-day synthetic market. The environment was rebuilt once (v1 → v2). Three independent reviews then found that v2 is not robust, and a consolidated list of 74 weaknesses was written. A first agent produced an improvement plan, `docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.docx` (also `.md` and `.pdf`), that takes v2 to v2.1 in ten phases. A second reviewer read that plan and found it sound in direction but flagged eleven points, including places where the plan decides things that should be decided by evidence, a start-price fix that has a cleaner alternative, missing effort estimates, unverified facts and citations, and no go/no-go checkpoint. That review is `docs/env_v2/v2_1/reviews/review_of_V2_1_IMPROVEMENT_PLAN.md`.

You are the third, independent pass. Your job is (1) to verify the plan, (2) to correct what is wrong, and (3) wherever the plan makes a choice that the evidence does not yet settle, to replace the single choice with two or three concrete alternative approaches, each with the experiment that would decide between them, so that the team decides from results rather than from anyone's preference. You are not asked to pick; you are asked to make the choice decidable.

## Documents to read first (current paths; the docs tree was reorganised on 26 Aug 2026)

- The plan under review: `docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.md` (same content as the .docx/.pdf).
- The review of the plan: `docs/env_v2/v2_1/reviews/review_of_V2_1_IMPROVEMENT_PLAN.md`.
- The weakness list the plan must close: `docs/env_v2/reviews/V2_WEAKNESSES.md`; the three underlying reviews: `docs/env_v2/reviews/review_A_parameter_provenance.md`, `review_B_claims_vs_evidence.md`, `review_C_methodology_robustness.md`.
- The prompt that produced the plan and the hard rules: `docs/env_v2/v2_1/V2_IMPROVEMENT_PROMPT.md` (its file paths are stale; use the ones here).
- The original v2 design plan: `docs/planning/FinPersona-Bench_Synthetic_Environment_v2_Plan_Aug2026.pdf`; the execution order and revision plan in `docs/planning/`; research notes in `docs/planning/env_v2_research/`; earlier review cycles in `docs/reviews/cycle1/` and `docs/reviews/cycle2/`.
- v2 as built: `envs/v2/*.py`, `envs/synthetic_market.py`, `envs/v2/params/*.json`; harness `agent/`, `simulation/`, `experiments/arms_v2.py`; evaluation `evaluation/*.py`; tools `tools/*.py`; tests `tests/`; documentation `docs/env_v2/*.md`; generated results `docs/env_v2/generated/`; the frozen v1 in `envs/v1/`.
- The deck and script that currently describe v2 (and contain claims the reviews contradict): `docs/env_v2/slides/`.

## Part 1. Verify

Check, and record the outcome of each check in a verification log:

1. Every number in the plan's Section 0 (findings reproduced) and Table 1: re-run them from the code with your own seeds and state your values beside the plan's.
2. The weakness-to-phase map (Table 2): every item 1–74 assigned; no item that a phase claims to close is actually left open by that phase's experiments.
3. Every formula (Appendix A power rules, Appendix B Kalman bound): re-derive; check the worked numbers.
4. Every citation: confirm the paper exists, that it reports the statistic the plan attributes to it, and at what level (index / industry / firm; monthly / daily). Mark each as read-and-correct, read-and-wrong (with the correction), or not-retrievable. Do not carry forward any number that you could not read at the source.
5. Every "checked today" fact: data sources reachable (yfinance, EDGAR company-facts, SF Fed sentiment, Shiller, FRED, CBOE single-stock VIX files, the FW 2012 PDF), package availability, and current API prices for the models named (read the provider pages; do not quote prices from memory).
6. Every compute and cost estimate: recompute from the stated per-run token counts and the verified prices.
7. Every experiment's design: is it actually decidable with the stated seeds and statistics (power), does it depend on a result from a later phase, is the pre-registered rule well-posed (could it be met trivially or never), does the ordering of phases hold.
8. Internal consistency: places where one section contradicts another (the review found one in E1.1).

## Part 2. Correct

Produce a corrected plan, `docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.md`, that keeps the original's structure and numbering, marks every change with a short tag "[changed: reason]" so the diff is auditable, and incorporates the eleven points of the plan review where you agree with them. Where you disagree with the review, say so with the evidence; do not drop a point silently. Add per-phase analyst-effort estimates and a dependency diagram showing which phases can run in parallel. Add a go/no-go checkpoint with a pre-registered meaningfulness criterion for the benchmark.

## Part 3. Alternatives where the choice is not settled

For every one of the following, and for any other place where the plan picks a single approach that evidence has not yet justified, write an alternatives entry with exactly this structure:

- **The question** in one sentence.
- **Option A / B / (C)**: the mechanism, what it assumes, what it costs (effort, compute, API), and the known literature that supports or undercuts it (read, not recalled).
- **What would show which option is right**: a pre-registered experiment or data analysis that discriminates between the options, with seeds/horizon/statistic/decision rule and its power, and what is reported if no option wins.
- **What each option does to the rest of the plan** (downstream phases, comparability with v1/v2 results, the paper's claims).

At minimum cover:

1. Removing the start-price answer key: randomise the price level; normalise the price and randomise the value; randomise both; something else.
2. The value process: smooth fundamental (v2's rationale) vs a fitted larger σ_V vs two environments as a factor (the plan's D3).
3. Where jumps belong and how they are shaped (in V at announcement dates; in x mean-zero; both).
4. The mispricing engine: working Franke–Westerhoff with verified units vs AR(1)+GARCH vs a third published behavioural model (state candidates).
5. How the mispricing persistence is estimated (variance ratios; P/V-proxy AR(1) with median-unbiased correction; SMM with persistence-carrying moments) and what to do if they disagree.
6. How regime volatility enters (scale the whole variance; scale ω with a ramp; a fitted regime-switching model) and how implied volatility is built without a phase step or look-ahead.
7. The sustained-bull control: same mispricing process with no band; band on V only; anchored x as in v2; a control defined differently (state it). Include what each does to the control's purpose.
8. Event dynamics: tracking gain; shifted perceived fundamental with a regime pull; scripted drift with rejection; an unscripted regime-switching model without error correction.
9. The calendar: random calendar dates; no date; "Day-N" as a disclosed arm; and the ordering mix that makes time and phase separable.
10. Observables that currently read the hidden state: the P/E multiple (fixed draw; time-varying AR(1); tied to a fitted cross-section), sentiment (returns-only; returns plus a slow valuation link; survey-style), volume (|r| only; plus turnover in run-ups), the analyst estimate (literature sd with sensitivity; drop the field; make it a lagged smoothed price proxy).
11. The resolvability threshold θ: information-based; cost-based; within-run-variance-based; co-primary reporting.
12. The regret metric: decomposition into band violation and directional agreement; per-window scoring; a different ceiling/floor convention.
13. The target bands: practitioner categories; utility-consistent bands from the environment's own (μ, σ); both as a factor.
14. Checklist criteria: pre-registered numeric thresholds; equivalence to real 200-day windows (KS bound); percentile bands from the reference distribution; and the seed/horizon policy (T = 200 only; T = 200 plus longer horizons reported separately).
15. Data: the free substitutes (survivor panel from yfinance, EDGAR, SF Fed, Shiller, FRED) vs pausing for WRDS access vs a hybrid (fit now, re-fit later), with the survivorship consequences quantified where possible.
16. The LLM sensitivity grid: which six parameters, which tiers, which models, and whether the stateful arms are included.

Where you find that an option is clearly dominated by the evidence you gathered, say so and why, but still record it so the reasoning is visible.

## Hard rules

1. Do not assume anything. Every parameter, threshold, range and design choice must trace to a read source or a stated experiment. "It was in the plan", "conventional" and "reasonable" are not justifications.
2. Do not make arbitrary suggestions. If evidence cannot settle a choice, present the alternatives with the discriminating experiment, and stop.
3. Research, then experiment, then test, then decide. Pre-registered criteria are written before data are seen and are not moved afterwards; if a criterion is wrong, say so and derive a new one in a separate documented step, reporting results under both.
4. Report every number with its sample size and an interval where one exists; report failures as failures; before/after comparisons must be like for like.
5. Verify before you cite the repository's own documents; several existing numbers are stale or wrong (`V2_WEAKNESSES.md` part 6).
6. You may run generator code and local analyses freely. Do not call paid APIs. If a check needs the network (source PDFs, data portals, price pages), do it, and record the URL and date.
7. Git: stay on `main`; create no branches. Do not commit, amend, reset, stash or push under any circumstances in this task. List every file you write or change at the end. Do not modify the frozen v1 code, the original plan document or the v2 design plan.
8. Use the scratchpad directory for temporary files; put deliverables under `docs/env_v2/`.

## Deliverables

1. `docs/env_v2/v2_1/reviews/V2_1_PLAN_VERIFICATION_LOG.md`: every check from Part 1 with outcome and evidence.
2. `docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.md`: the corrected plan with change tags, effort estimates, dependency diagram and the go/no-go checkpoint.
3. `docs/env_v2/v2_1/V2_1_ALTERNATIVES_REGISTER.md`: the alternatives entries from Part 3, one per question, in the fixed structure, plus a one-page summary table (question, options, discriminating experiment, cost, which phase runs it).
4. A short closing note listing what you could not verify and why, and the decisions that remain the team's.
