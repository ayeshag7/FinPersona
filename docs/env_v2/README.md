# docs/env_v2 — the synthetic market environment, v2 and the v2.1 programme

Everything about the rebuilt environment lives here. The v2 design plan it implements is `docs/planning/FinPersona-Bench_Synthetic_Environment_v2_Plan_Aug2026.docx` (research notes in `docs/planning/env_v2_research/`). Code: generator `envs/v2/` (facade `envs/synthetic_market.py`, frozen v1 in `envs/v1/`), harness `agent/` + `simulation/` + `experiments/arms_v2.py`, evaluation `evaluation/`, tools `tools/`, tests `tests/`.

## Layout

| Folder | What is in it | Pushed? |
|---|---|---|
| `spec/` | v2 as built: `E1_V2_GENERATOR_SPEC.md` (blocks, parameters, calibration choices, deviations, validation table), `IO_CONTRACT.md` (observation, portfolio, action, logging), `CALIBRATION_REPORT.md` (parameters in force, checklist, hazard grid, audit tables) | yes |
| `preregistration/` | `PREREGISTRATION.md` (thresholds, feature sets, gates written before the runs) and `PREREGISTRATION_AMENDMENTS.md` (every change after, with what was seen before it) | yes |
| `decisions/` | `DECISIONS_13_1.md` (the eleven plan decisions, signed) and `DECISION_LOG.md` (reasoning, calibration addendum, open issues, review rounds) | yes |
| `v1_baseline/` | The old environment frozen for comparison: `E0_SUMMARY.md` (freeze, Table 2, day-1 gate, re-scoring, v1 checklist and audit) and `E0_V1_GENERATOR_SPEC.md` | yes |
| `status/` | `E1_E4_STATUS.md` (what exists, validation results, open issues) and `PILOT_NOTES.md` (the 48-run Gemini pilot) | yes |
| `generated/` | Machine-written results: checklists, leakage audits, sensitivities, calibration grids, pilot reports, Table 2, rendered prompts. See `generated/README.md` for the groups and the command that regenerates each | yes |
| `reviews/` | The three independent reviews of v2 (`review_A_parameter_provenance.md`, `review_B_claims_vs_evidence.md`, `review_C_methodology_robustness.md`) and the consolidated list `V2_WEAKNESSES.md` (74 items) | no |
| `v2_1/` | The improvement programme: **`V2_1_IMPROVEMENT_PLAN.md` / `.docx` / `.pdf` is the single working document** (the first draft merged with the third-pass corrections and the 27 Aug reviewer edits; every change tagged `[changed: …]` or `[edit 27 Aug]`), `V2_1_ALTERNATIVES_REGISTER.md` (18 open choices with the experiment that decides each), `V2_IMPROVEMENT_PROMPT.md`, `V2_1_PLAN_VERIFICATION_PROMPT.md`, `PHASE_EXECUTION_PROMPT.md` and `DATA_PANEL_PROMPT.md` (the briefs given to the agents); `v2_1/reviews/` holds the plan review, the verification log, the closing note and the review of that verification; `v2_1/archive/` keeps the superseded first draft and the delta document for the audit trail only. Phase pre-registrations and reports (`PREREG_PHASE_k.md`, `PHASE_k_REPORT.md`, `DECK_CORRECTIONS_NOW.md`, `CLAIMS_LEDGER.md`) go here as the phases run; their generated outputs go to `generated/v2_1/` | no |
| `slides/` | The v2 deck (`FinPersona_env_v2_slides.pdf`, built by `tools/build_slides.py`) and the speaker script (`SPEAKER_SCRIPT.md`, `.docx`, `.pdf` via `tools/script_to_docx.py`). Several numbers on the deck are contradicted by the reviews; see `reviews/V2_WEAKNESSES.md` part 6 and `v2_1/V2_1_IMPROVEMENT_PLAN.md` 0.2b before presenting it | no |

"Pushed?" follows the repo `.gitignore`: the specification, pre-registration, decisions, baseline, status and generated results are tracked; reviews, the v2.1 working documents and the slides stay local.

## Reading order

1. What was wrong with v1 and what v2 changed: `v1_baseline/E0_SUMMARY.md`, then `spec/E1_V2_GENERATOR_SPEC.md`.
2. What was decided and why: `decisions/DECISIONS_13_1.md`, `decisions/DECISION_LOG.md`, `preregistration/PREREGISTRATION_AMENDMENTS.md`.
3. What the tests say: `generated/checklist_v2.md`, `generated/leakage_audit_v2.md`, `spec/CALIBRATION_REPORT.md`, `status/PILOT_NOTES.md`.
4. What is still wrong: `reviews/V2_WEAKNESSES.md` (start with Part 1), then the three reviews.
5. What happens next: `v2_1/V2_1_IMPROVEMENT_PLAN.md` (phases, go/no-go, team decisions D1–D17) with `v2_1/V2_1_ALTERNATIVES_REGISTER.md`; the state of verification in `v2_1/reviews/`.

## Status (27 Aug 2026)

v2 is built (E0–E4), audited and piloted; the reviews found it not robust (fixed start price acts as an answer key, the mispricing model's switching is inert, the flat control is biased, fields leak once the anchor is removed, several claims exceed their evidence, an analyst-error bug, wrong sensitivity counts). **Phase 0 of the v2.1 programme is done (29 Aug 2026)**: every computational review finding reproduced on fresh seeds, the analyst-error bug fixed, silent overrides removed, labels corrected, the generator frozen with a manifest, statistical regression tests with a known-defect registry, the test suite clean — see `v2_1/PHASE_0_REPORT.md`, `v2_1/PREREG_PHASE_0.md`, `v2_1/DECK_CORRECTIONS_NOW.md` and `generated/v2_1/`. Phase 0 was reviewed and accepted (`v2_1/reviews/review_of_PHASE_0.md`). **The shared data panel E1.0 is downloaded (29 Aug 2026)**: `datasets/` at the repo root (git-ignored; per-folder READMEs and `_manifests/`), fetch code `tools/e1_0_data/`, report `v2_1/E1_0_DATA_REPORT.md`; the delisted tail is only 4.7 % recoverable from free data. **Phase 1 (value and price structure) is done (29-30 Aug 2026)** — `v2_1/PHASE_1_REPORT.md`, `PREREG_PHASE_1.md`, `PREREG_PHASE_1_ADDENDUM.md`, `PHASE_1_CHANGED_FILES.md`, DECISION_LOG P1-1…P1-15. **Phase 2 (the mispricing engine and its persistence) is done (1 Sep 2026)** — `v2_1/PHASE_2_REPORT.md`, `PREREG_PHASE_2.md`, `PREREG_PHASE_2_ADDENDUM.md`, `PHASE_2_CHANGED_FILES.md`, DECISION_LOG P2-1…P2-12, results in `generated/v2_1/e2_*`. Its headline results: Franke-Westerhoff's units are settled at source (`price_scale = 1`, a LIT bug fix) and the plan's SABCEMM target was a mis-transcription; the engine decision went to **AR(1)+GJR-GARCH-t** under the pre-registered asymmetric rule (no engine accepted, held-out prediction a dead heat, and the FW engine fitted freely on the training period turns its own switching off); the panel implies a mispricing half-life of **5-13 days** and an amplitude of about **2.5 %**, against the environment's 150 days and 17.5 %, which is a first-order input to D3/D8 and to the 16A checkpoint. D10 is needed before Phase 5. **Phase 3 (volatility) is done (2-5 Sep 2026, reviewed and corrected)** — `v2_1/PHASE_3_REPORT.md`,
`PREREG_PHASE_3.md`, `PREREG_PHASE_3_ADDENDUM.md` (three designs corrected in documented steps, plus four post-review extensions),
`PHASE_3_CHANGED_FILES.md`, DECISION_LOG P3-1…P3-17, results in `generated/v2_1/e3_*`. Its headline results: the
volatility block is now fully FIT (`envs/v2/params/volatility.json`) — E3.1's GJR shape (α 0.027, γ 0.058,
β 0.932) with a jump-decomposed diffusive tail (ν 6.65), sbar 0.0151 by an exact variance-accounting identity to
the panel's unconditional sd, jumps re-fitted to rare-and-large (0.0006/day at σ 0.23 — v2's 0.010/0.03 CAL had
no data support), phase multipliers calibrated closed-loop to panel event windows (panic ×7.45 total), the
whole-variance mechanism kept by REG-6's own three-way test, and the IV field rebuilt as a past-only filter with
a constant FIT premium and AR(1) FIT noise — the one-day panic step (weakness 46, z ≈ 7) is gone (z = 0.12,
hard-tested at a derived tolerance) and the onset audit shows IV now carries less phase signal than the price
path itself. The engine refit under the fitted block moves the mispricing to σ_V 0.0146, half-life 22.4 d
[18.7, 32.6] (Phase 2's 7.5 is outside the interval, and 22.4 is inside Phase 2's own [3.81, 23.61]), sd(x)
0.068; the bull-trap rejection rate falls 0.94 → 0.13. **After review (5 Sep 2026)** the phase withdrew one of
its own conclusions and delivered two registered items it had missed (P3-12 … P3-17): measured on a consistent
calm-trained surrogate the calm level-free channel **narrowed rather than closed** (R² 0.421 → 0.349, sign
0.892 → 0.814), so the Appendix-B excess persists at ≈ +0.19 and is Phase 6's to characterise; `sbar` now
carries its registered interval (0.01509 [0.01342, 0.01678]); and the level anchoring is a **confirmed
double-count** — the deployed generator runs +30 % above the 0.0218 its own identity targets, because the
identity pins calm to the panel's all-day average (1.28× the panel's calm) and the multipliers stack on top.
The anchor choice is put to the team before Phase 4 builds the schedule on it. The empirical fast-crash rise time (30 d) is unreachable under any variance mechanism because the schedule
template owns it, the blow-off label's multiplier was found to be dead code since v2, and post-top is
drift-dominated — all three handed to Phase 4 with numbers. Phase 4 has not started.

## Regenerating results

```
python -m tools.gen_table2 --env v2                                  # generated/table2_v2_from_code.*
python -m evaluation.stylized_facts --env v2 --seeds 50 --T 200      # generated/checklist_v2.md
python -m evaluation.leakage_audit  --env v2 --seeds 50 --T 200      # generated/leakage_audit_v2.md
python -m tools.calibrate_hazard --seeds 60                          # generated/hazard_calibration.csv
python -m tools.l5_report                                            # generated/l5_observables_oracle.*
python -m experiments.arms_v2 --models <model> --personas ISFJ INTJ ENTJ --arms static memory placebo_directive wrapper_only swapped trader --scenarios flat bull_trap crash sustained_bull --seeds 42 123 456 789 999 --reps 3
python -m tools.report_v2 --results results_v2                       # generated/report_v2*
python -m tools.stats_v2                                             # generated/stats_v2*
python -m tools.build_slides                                         # slides/ (needs Edge or Chrome)
python -m tools.verify_v2_findings                                  # generated/v2_1/findings_reproduction.md (Phase 0 reproduction, ~11 min)
python -m tools.path_hashes --compare generated/v2_1/path_hashes_before.json generated/v2_1/path_hashes_after.json
python -m tools.freeze_manifest --check                             # the v2 freeze (tests/v2_freeze_manifest.json)
python -m tools.regen_checklist_md --check                          # checklist .md footers vs CSVs
python -m pytest tests/ -q                                          # test_leakage_ci.py is slow; the known-defect registry is printed at the end
```
