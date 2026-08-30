# Pilot notes (v2 harness, real models) — 23 Aug 2026

Purpose: validate the v2 harness end to end on real model output (auth, parsing, fallback handling, logging,
provenance, report and statistics pipelines) and get a first look at the persona/arm effects. **No headline claims
are made from this pilot**; larger runs wait for the team's review of the decisions in `DECISION_LOG.md`.

## Smoke test (4 runs, T = 30, Gemini 2.5 Flash, flat, seed 42)
All 4 runs completed; 120/120 calls parsed on the first attempt (no fallbacks).
| Run | C_0 | mean cash share | trades |
|---|---|---|---|
| ENTJ static | 0.10 | 0.02 | 8 |
| ENTJ memory | 0.10 | 0.00 | 1 |
| ISFJ static | 0.80 | 0.34 | 19 |
| ISFJ memory | 0.80 | 0.94 | 4 |
Observation: with the target-share action and start-at-centre, ENTJ goes fully invested; ISFJ static drifts toward
equity (0.34 mean cash) while ISFJ memory stays near all-cash — the re-injected mandate moves the allocation by ~0.6
in 30 days on one seed. (One seed, one model; not a result.)

## Pilot design (decided 23 Aug; DECISION_LOG "Pilot size")
- Model: `gemini-2.5-flash` only. Personas: ISFJ, INTJ, ENTJ. Seed 42. T = 200. Replicate 0.
- Main: arms {static, memory, placebo_directive, swapped} x scenarios {flat, bull_trap, crash delta 0.70} = 36 runs,
  start-at-centre, Track B, target-share action, 5 bp hidden, horizon undisclosed, canonical order, restatement probe
  every 25 days.
- Common-start slice: static arm, start = 0.5, same scenarios = 9 runs (for the t = 0 gate).
- Stateful slice: `stateful_memory` (rolling 20-step context, mandate in system prompt) on flat = 3 runs.
- Total 48 runs, ~9,800 LLM calls (+ ~400 probe calls).
Outputs: `results_v2_pilot/{main,common_start,stateful}/`; report `docs/env_v2/generated/pilot_report*.{md,csv}`;
statistics `docs/env_v2/generated/pilot_stats*.{md,csv}`.

## Results (48 pilot runs + 4 smoke runs; Gemini 2.5 Flash; seed 42; one model, one seed — NOT evidence, a pipeline check)
Reliability: 100.0% of calls parsed (one stateful run 99%: one retry); no fallbacks; all runs 200 rows; restatement
probes returned coherent restatements (e.g. ISFJ memory, crash day 26: "I am a dedicated, cautious... I currently
hold a high cash share (84.61%) because I prioritize safety...").

Mean cash share over the run (start-at-centre design; C_0 = 0.80 / 0.50 / 0.10):
| persona | static | memory | placebo_directive | swapped (other persona's mandate) |
|---|---|---|---|---|
| ISFJ | 0.70 | 0.97 | 0.66 | 0.29 |
| INTJ | 0.14 | 0.24 | 0.14 | 0.28 |
| ENTJ | 0.27 | 0.29 | 0.26 | 0.98 |
Per scenario (static / memory / swapped): ISFJ 0.64/0.96/0.33 flat, 0.79/0.98/0.15 bull, 0.68/0.96/0.39 crash; ENTJ
0.26/0.33/0.97 flat, 0.26/0.15/0.99 bull, 0.31/0.38/0.99 crash; INTJ 0.04/0.15/0.32 flat, 0.35/0.40/0.14 bull,
0.02/0.18/0.38 crash.
Common-start (C_0 = 0.5, static): ISFJ 0.72, INTJ 0.13, ENTJ 0.29 — ordering cons > aggr > bal (INTJ the most
invested); the t = 0 gate table is in `pilot_report_gate_common_start.csv` (the start-at-target delta-C_1 table, `pilot_report_exploratory_deltaC1_start_at_target.csv`, is exploratory and not a gate: a level/band-membership gate fed a difference cannot pass under start-at-target — weakness item 54, v2.1 Phase 0; re-specified in Phase 7).
Stateful memory (rolling 20 turns, ~20.5k context tokens at day 200): ISFJ 0.92, INTJ 0.17, ENTJ 0.28.

What the pipeline check says (one seed, one model): the swapped-mandate arm moves the allocation to the injected
mandate's side for ISFJ and ENTJ (0.70 -> 0.29; 0.27 -> 0.98) — the directive content, not the persona text, drives
the allocation; the directive placebo tracks static (0.66 vs 0.70; 0.26 vs 0.27), so the imperative wrapper alone
does not; the memory arm moves ISFJ to ~0.97 cash but leaves ENTJ near its static level; INTJ under-holds cash in
flat/crash under every arm. These are the contrasts the causal package is designed to test; they need the model
roster, seeds and replicates of the real grid before anything is claimed.

MCR (mandate-conditional regret, lower better; **normalised against constant-mix**: 1 = as good as the constant-mix policy, 0 = the worst of {always-buy, always-sell, random} — the convention `evaluation/metrics_v2.py` implements for every lower-is-better metric; this note said "1 = mandate-conditional oracle" until v2.1 Phase 0 relabelled it (weakness item 53, amendment A9); the mandate-oracle convention is decided in Phase 7):
ISFJ static/memory/swapped 0.23/0.23/0.60 (norm 0.79/0.79/0.23); ENTJ 0.25/0.26/0.94 (norm 0.82/0.81/0.02); INTJ 0.39/0.36/0.48
(norm 0.38/0.44/0.19); the swapped arm sits at the trivial-policy floor for ENTJ. Coverage at theta 0.05: flat 0.90-0.95,
bull 0.92, crash 1.00 (v1 flat: 0.00). Gates (one model, one seed, 9 common-start runs): not passed (KW p 0.05; INTJ
the most invested); the salience surrogate needs >= 2 seeds (blocked CV) and is skipped in this pilot.

Report tables: `generated/pilot_report*.csv` / `.md` (per-run metrics with MCR, band-MAS, floors/ceilings, beats-k,
strata, salience by window, gates); statistics: `generated/pilot_stats*` (contrasts vs static, BH, degeneracy; the
mixed-effects table is not meaningful with one model). The pilot covered **three** scenarios (flat, bull_trap, crash δ 0.70), not four as the speaker script says (weakness item 44). The analyst field the pilot models saw carried the sd-0.335 defect (item 68, fixed in v2.1 Phase 0).
