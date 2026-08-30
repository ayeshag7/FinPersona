# Review of Phase 0 (verification and freeze), 29 Aug 2026

Reviewer: Claude (this session). I re-ran the checks that can be re-run and read the three deliverables (`PREREG_PHASE_0.md`, `PHASE_0_REPORT.md`, `DECK_CORRECTIONS_NOW.md`), the registry, the changed code and the regenerated results.

## Verdict

Phase 0 was executed as the plan specifies and can be accepted. It stayed inside its remit (no design change; 0 non-analyst path-column changes across 95 hashed configurations), it pre-registered before running (`PREREG_PHASE_0.md` 00:40, first run 00:56, results 01:26), it disclosed every deviation, it registered rather than fixed the one thing it could not fix, and it found four things the plan got wrong. Nothing was committed, stashed or pushed; `main` is still at `b61fe07`; `envs/v1/`, `docs/planning/` and `v2_1/archive/` are untouched (mtimes unchanged).

## What I re-ran and confirmed

| Claim | My check | Outcome |
|---|---|---|
| Suite green: 103 passed, 1 skipped, 8 xfailed | fast suite (`--ignore=tests/test_leakage_ci.py`): 96 passed, 1 skipped, 4 xfailed, 0 failed in 9 min; known-defect registry printed | confirmed |
| Freeze manifest matches | `python -m tools.freeze_manifest --check` → manifest OK | confirmed |
| No distribution change except the analyst field | `python -m tools.path_hashes --compare …` → 0 non-analyst changes, 190 analyst changes | confirmed |
| Analyst √5 removed; engine named `fw_fallback_hl150` and `fw_single` raises; hazard loader loud | read `observables.py:129-134`, `mispricing.py:48,163-177`, `generator.py:45-67` | confirmed |
| sd(x) discrepancy resolved by the weight normalisation | `MispricingState` at 200,000 steps: w_norm 1.0 → sd(x) 0.131; w_norm 0.761 → 0.172 (sd_e 0.017) and 0.162 (sd_e 0.016) | confirmed to two decimals; my 27 Aug "not reproduced" is withdrawn — both published numbers were right, and the plan's Appendix B reference row is now s_x ≈ 0.175 (plan annotated) |
| The legacy v1 plateau assertion never held | frozen v1 bull trap: seed 42 V 100.6 → 93.9 by day 50; seeds 0 and 1 also move | confirmed |
| Re-run audit: k·analyst now beats price itself under L1 | `leakage_audit_v2.md` L1 table: k·analyst median APE 0.101 vs price 0.124; A6 rule still passes at 50 seeds | confirmed; the CI-seed failure is correctly registered, not fixed |
| Regenerated results on the frozen state | `checklist_v2.md`, `leakage_audit_v2.md`, `l5_observables_oracle.md`, `table2_v2_from_code.*` all rewritten 29 Aug 01:17–01:36 | confirmed |
| No stale numbers left in the tracked documents | grep for 188 d / 0.335 / √5 outside "was/withdrawn/Phase 0" contexts | none found |
| Decision log Phase 0 section and amendment A9 exist | `DECISION_LOG.md` §"Phase 0 of the v2.1 programme"; `PREREGISTRATION_AMENDMENTS.md` row A9 | confirmed |

## Findings that change later phases (all sound, all new inputs)

1. **sd(x) of the engine is 0.175, not 0.13.** The 27 Aug hold is resolved by the weight normalisation. Phase 1's Kalman bound and E1.3's s_x sweep must use ≈ 0.175 as the reference; the plan has been annotated accordingly ([resolved 29 Aug] in the reviewer-edits paragraph, Table 0.1 row 71, Phase 0's 0.2, Appendix B and C).
2. **The corrected analyst field is a stronger V channel than the buggy one** (median error 11 % instead of 22 %; the three-term formula reaches 7 %; selectivity of the fields rises to +0.62 with the start price randomised). This makes Phase 5's REG-10d decision (keep with a literature sd ≈ 45 %, drop, or replace by a price-derived proxy) more consequential, and it is the reason the A6 CI test now fails at 8 seeds. Registering it for Phase 6 rather than moving the rule was the right call.
3. **Amendment A5's justification was false** ("without a cap every run reaches P/V > 3": 18 % do). Phase 4's E4.4 (mania drift, cap) starts from that fact.
4. **The multi-asset IV inconsistency has the opposite sign** to reviewer C's numbers (asset 2's IV/RV is 1.41, not 1.06). Phase 3/9 input.
5. **The 200,000-step re-normalisation of w̄/n̄ was deferred to Phase 2** because it moves every path by +0.03 % in φ. Correct under the no-design-change rule; Phase 2 must not forget it.

## Pointers before Phase 1

1. **Pre-register the compute-feasible bootstrap counts.** The pre-registration said 2,000 resamples; the sklearn statistics used 500, the classifier 60. Disclosed, and no verdict depended on it, but future pre-registrations should state the number that will actually be run.
2. **Like-for-like panels.** Seven of the 16 N rows are panel-composition differences (the audit's 150-path mix vs Phase 0's 50 × 4 scenarios). Phase 1's level-free audit should either use the published audit's composition or declare a new standard panel once, so that before/after rows on the slides are like for like (the plan's own rule).
3. **The "structural" reading of items 2 and 3 is now doubly undermined** (Phase 0: the jump/kurtosis coupling is smaller than the log said, 0.10 not 0.25; review B: real 200-day windows fail the criteria more often). Phase 6's reference distributions are the fix; nothing to do now.
4. **Two things happened during Phase 0 that the report does not cover.** (a) The agent's session overlapped with the 27 Aug merge of the plan (the plan md, the register and the verification prompt carry a 01:21 timestamp from the agent's session while the report's §8 does not list them as changed); while preparing this review I regenerated the plan md from the archived first draft plus the merge script, which reproduces the 01:09 version exactly and matches the docx/pdf, but any edit the agent made to the plan md at 01:21 (if there was one) is not preserved. Ask the agent what, if anything, it changed in those three files at 01:21; the register and the verification prompt were not regenerated and are as the agent left them. (b) The plan now carries the sd(x) resolution; the docx and pdf are rebuilt from it.
5. **D13 wording in the plan.** With sd(x) ≈ 0.175 and the anchored/level-free numbers of Phase 0 (level R² 0.85 vs level-free 0.49), the case for the provisional mechanism B is unchanged; approve it explicitly so Phase 1 can start.
6. **Housekeeping.** `docs/env_v2/README.md` and `generated/README.md` were updated by the agent and are consistent with the restructure. Nothing to fix.

## Decisions Phase 1 needs from the team (unchanged)

D1 (free substitutes / WRDS / hybrid — REG-15 gives the survivorship rule), D13 (approve provisional B), D16 (full programme vs the minimal path), and, before Phase 5, D10 (dividends). E1.0 also needs a historical-constituent source, since the Wikipedia table is gone; the agent should propose two candidates with their coverage before downloading.
