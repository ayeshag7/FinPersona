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
invested); the t = 0 gate table is in `pilot_report_gate_common_start.csv`. The start-at-target delta-C_1 table (`pilot_report_exploratory_deltaC1_start_at_target.csv`) was kept as "exploratory" until v2.1 Phase 7 **removed it** (E7.5, DECISION_LOG P7-7): a level/band-membership test fed a difference cannot separate personas under start-at-target whatever the agent does, so its verdict carries no information about the agent, and labelling it exploratory invited it to be read as weak evidence. The file remains on disk as the record of a withdrawn table.
Stateful memory (rolling 20 turns, ~20.5k context tokens at day 200): ISFJ 0.92, INTJ 0.17, ENTJ 0.28.

**What the corrected covariate changes for the stateful paragraph (v2.1 Phase 8, E8.1; `PREREG_PHASE_8.md` 1.7;
`docs/env_v2/generated/v2_1/e8_1/pilot_offsets.json`).** The three stateful runs cannot be read as evidence about
the mandate receding from the model's view, because it never did:

1. **The mandate was never more than ~436 tokens from the generation point.** The memory arm re-injects the mandate
   block into the current turn, and only the format instructions follow it: 409 in chars/4, 436 o200k tokens,
   constant from day 1 to day 200. The logged `Mandate_Offset_Tokens` (15,261 / 15,909 / 16,546 at day 200 for ENTJ
   / INTJ / ISFJ) is the distance to the *system-prompt* copy — through 20 replayed copies — so it overstates the
   attendable distance 37–40 times.
2. **The context carried 22 copies of the mandate at a full window** (the system copy, one in each of the 20
   retained turns, the current turn's), and the replayed ones were 9.0 % of the day-200 context. A stateless memory
   run carries one. So "stateful memory" here differs from the static stateful arm by 22 copies, not by the passage
   of time.
3. **The two columns are in different units.** `Context_Tokens` is the provider's count; `Mandate_Offset_Tokens` is
   chars/4 (on the same day-200 context, chars/4 gives 16,706 against the provider's 20,454 for ENTJ).
4. **`stateful_static` was never run**, so the budget parity the decay contrast needs was never checkable on the
   pilot; Phase 8 builds both arms itself in `tests/test_v2_1_phase_8.py`.

The allocations above are unchanged — nothing is re-scored — but they are allocations of a model that saw its
mandate in every turn. The corrected harness (`harness_version="v2_1"`) logs the nearest-copy offset, the
system-copy offset, the copy count and the counting method; the covariate on real stateful runs arrives with the
main grid.

What the pipeline check says (one seed, one model): the swapped-mandate arm moves the allocation to the injected
mandate's side for ISFJ and ENTJ (0.70 -> 0.29; 0.27 -> 0.98) — the directive content, not the persona text, drives
the allocation; the directive placebo tracks static (0.66 vs 0.70; 0.26 vs 0.27), so the imperative wrapper alone
does not; the memory arm moves ISFJ to ~0.97 cash but leaves ENTJ near its static level; INTJ under-holds cash in
flat/crash under every arm. These are the contrasts the causal package is designed to test; they need the model
roster, seeds and replicates of the real grid before anything is claimed.

MCR (mandate-conditional regret, lower better). **Re-scored in v2.1 Phase 7 (E7.2); the figures below replace the
ones this note carried until 10 September 2026, and the correction is recorded in DECISION_LOG P7-14 and
`PREREG_PHASE_7_ADDENDUM.md` section 7.** Three things changed:

1. **Three prose figures did not match the table they were written from.** Phase 7's re-score reproduces
   `generated/pilot_report_per_run.csv` run by run — 52 of 52 runs, worst absolute difference 2.2 x 10^-16 — and
   against that table this note's ISFJ static (0.23), ENTJ static (0.25) and ENTJ memory (0.26) were wrong; INTJ's
   three cells and all three `swapped` cells agreed to rounding. The values below are the table's.
2. **The published arm means include the four T = 30 smoke runs**, which sit in the ISFJ and ENTJ static and
   memory cells (n = 4 there against n = 3 elsewhere). Both constructions are given.
3. **MCR is now decomposed** into a band-violation term B and a directional term D (MCR = B + D on resolvable
   steps), which is what makes the arms distinguishable.

| persona | arm | n (as published / T = 200 only) | MCR as published | MCR, T = 200 only | B (band violation) | D (directional) | share of resolvable steps outside the band |
|---|---|---|---|---|---|---|---|
| ISFJ | static | 4 / 3 | 0.2514 | 0.2141 | 0.1586 | 0.0555 | 0.874 |
| ISFJ | memory | 4 / 3 | 0.2342 | 0.2310 | 0.0764 | 0.1545 | 0.841 |
| ISFJ | swapped | 3 / 3 | 0.5949 | 0.5949 | 0.5155 | 0.0794 | 1.000 |
| INTJ | static | 3 / 3 | 0.3925 | 0.3925 | 0.3756 | 0.0168 | 0.989 |
| INTJ | memory | 3 / 3 | 0.3610 | 0.3610 | 0.3266 | 0.0344 | 0.937 |
| INTJ | swapped | 3 / 3 | 0.4771 | 0.4771 | 0.3993 | 0.0779 | 0.998 |
| ENTJ | static | 4 / 3 | 0.2101 | 0.2743 | 0.2049 | 0.0694 | 0.333 |
| ENTJ | memory | 4 / 3 | 0.2414 | 0.3218 | 0.2403 | 0.0816 | 0.305 |
| ENTJ | swapped | 3 / 3 | 0.9396 | 0.9396 | 0.7792 | 0.1603 | 0.998 |

What the decomposition says that MCR alone did not: **INTJ's regret is almost entirely band violation** (static:
0.3756 of 0.3925, and it is outside its band on 98.9 % of resolvable steps) — INTJ under-holds cash and is simply
out of mandate, not wrongly directed. **ISFJ's memory arm is the opposite** (B 0.0764, D 0.1545): inside the band,
on the wrong side of the oracle. Under MCR alone those two look comparable; they are different failures.

**Normalised MCR is NOT recomputed and the old values are withdrawn from use.** A normalised value needs per-cell
baselines simulated on the cell's own price path, and v2.1 Phase 7 (E7.6) found that **none of the 52 pilot paths
regenerates**: the pilot ran on engine `fw_single`, whose SMM estimate Phase 2 rejected, so the generator refuses
to build it (0 of 52 environments constructible) and the documented fallback engine gives a path 37-82 price units
away. The published `norm_mcr` figures — ISFJ 0.79/0.79/0.23, ENTJ 0.82/0.81/0.02, INTJ 0.38/0.44/0.19 against the
table's 0.7501/0.7799/0.2293, 0.8708/0.8366/0.0241 and 0.3756/0.4440/0.1953 — were **normalised against constant-mix**
as the ceiling (not against the mandate-conditional oracle, as this note said before v2.1 Phase 0 relabelled it;
weakness item 53, amendment A9), on a generator that no longer exists. They are kept here for the record only. Phase 7 adopted the corrected convention (ceiling = the
mandate-conditional oracle, floor = the worst trivial policy); on the Phase-6 policy panel that convention moves
the level-free observables oracle's normalised MCR from 1.067 — *above 1*, under the constant-mix ceiling — to
0.919.

Coverage at theta 0.05: flat 0.90-0.95, bull 0.92, crash 1.00 (v1 flat: 0.00). The theta in force is now
co-primary (theta_info 0.05 and theta_cost 0.0020; `evaluation/params/scoring.json`), and the pilot is re-scored at
nine theta values and three half-widths in `generated/v2_1/e7_pilot/pilot_rescore.csv`. Gates (one model, one seed,
9 common-start runs): not passed (KW p 0.05; INTJ the most invested). The start-at-target delta-C_1 table is
**removed** in Phase 7 (E7.5): it is ill-posed under start-at-target and cannot separate personas whatever the
agent does. The gate's null — the arms in which no persona text is shown — is **not computable on this pilot**,
which has no such arm at common start. The salience surrogate needs >= 2 seeds (blocked CV) and is skipped.

Report tables: `generated/pilot_report*.csv` / `.md` (per-run metrics with MCR, band-MAS, floors/ceilings, beats-k,
strata, salience by window, gates); statistics: `generated/pilot_stats*` (contrasts vs static, BH, degeneracy; the
mixed-effects table is not meaningful with one model). The pilot covered **three** scenarios (flat, bull_trap, crash δ 0.70), not four as the speaker script says (weakness item 44). The analyst field the pilot models saw carried the sd-0.335 defect (item 68, fixed in v2.1 Phase 0).
