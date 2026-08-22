# docs/env_v2 — environment v2 rebuild working directory

Source of truth: `../FinPersona-Bench_Synthetic_Environment_v2_Plan_Aug2026.docx` (v3, 22 Aug 2026).
Implementation order E0 → E1 → E2 → E3 → E4 (plan Section 13). Section 13.1 decisions signed 22 Aug 2026
(`DECISIONS_13_1.md`, reasoning in `DECISION_LOG.md`); calibration choices and open issues in the DECISION_LOG addendum;
logged amendments in `PREREGISTRATION_AMENDMENTS.md`. Status: **E0-E4 built**; see `E1_E4_STATUS.md`.

## Documents
| File | What |
|---|---|
| `E0_SUMMARY.md` | E0 results (freeze, Table 2, gate on v1, re-scoring, v1 checklist + audit baselines) |
| `E0_V1_GENERATOR_SPEC.md` | the frozen v1 generator, block by block (incl. the seed-reproducibility defect found in E0) |
| `E1_V2_GENERATOR_SPEC.md` | the v2 generator as built: blocks, parameters, calibration choices, deviations, validation table |
| `E1_E4_STATUS.md` | what exists for E1-E4, validation results, open issues, what is next |
| `CALIBRATION_REPORT.md` | E6 draft: parameters in force, checklist table, hazard grid, Section 5 audit tables |
| `IO_CONTRACT.md` | v1 as-is and v2 contract (observation, portfolio, action, logging) |
| `PREREGISTRATION.md` / `PREREGISTRATION_AMENDMENTS.md` | thresholds, feature sets, casualties, spine; logged amendments |
| `DECISIONS_13_1.md` / `DECISION_LOG.md` | the eleven decisions (signed) and the reasoning; E1 addendum with open issues |

## Code map (v2)
| Layer | Files |
|---|---|
| Generator | `envs/v2/{rng,schedule,garch,mispricing,events,generator,observables}.py`, `envs/v2/params/`, facade `envs/synthetic_market.py`; frozen v1 in `envs/v1/` |
| Calibration tools | `tools/calibrate_hazard.py` (bubble top), `tools/calibrate_fw.py` (single-stock SMM; fallback documented), `tools/gen_table2.py` |
| Audits | `evaluation/stylized_facts.py` (Section 9), `evaluation/leakage_audit.py` (Section 5), CI in `tests/test_leakage_ci.py` |
| Harness (E3/E5) | `agent/v2_agent.py`, `agent/stateful_agent.py`, `agent/v2_prompts.py`, `agent/render.py`, `agent/llm_factory.py`, `simulation/runner_v2.py`, `simulation/portfolio_v2.py`, `experiments/arms_v2.py`, `simulation/provenance.py` |
| Evaluation (E4) | `evaluation/targets.py`, `evaluation/metrics_v2.py`, `evaluation/baselines_v2.py`, `evaluation/salience.py`, `tools/report_v2.py`, `tools/stats_v2.py`; v1 re-scoring `evaluation/rescore_v1.py`, `evaluation/baselines.py`; gate `evaluation/separability_gate.py` |
| Tests | `tests/test_provenance_and_freeze.py`, `test_render_prompt_frozen.py`, `test_action_space.py`, `test_v2_generator.py`, `test_v2_harness.py`, `test_eval_v2.py`, `test_stateful_multiasset.py`, `test_stats_v2.py`, `test_leakage_ci.py` |

## Generated artefacts (`generated/`)
E0: `table2_v1_from_code.*`, `rendered_prompt_v1_*.txt`, `E0_SEPARABILITY_GATE_V1.md`, `E0_RESCORE_V1.md`, `checklist_v1.md`,
`leakage_audit_v1.md`, `e0_*.csv`. E1/E2: `checklist_v2.md`, `leakage_audit_v2.md`, `hazard_calibration.csv`,
`e1_calibration_variants.md`, `table2_v2_from_code.*`, `rendered_prompt_v2_*.txt`. E4: `report_v2*.{md,csv}` (after runs).

## How to run
```
python -m tools.gen_table2 --env v2
python -m evaluation.stylized_facts --env v2 --seeds 50 --T 200
python -m evaluation.leakage_audit  --env v2 --seeds 20 --T 200
python -m tools.calibrate_hazard --seeds 60
python -m experiments.arms_v2 --models <model> --personas ISFJ INTJ ENTJ --arms static memory placebo_directive wrapper_only swapped trader --scenarios flat bull_trap crash sustained_bull --seeds 42 123 456 789 999 --reps 3
python -m experiments.arms_v2 ... --bridge            # 100%-cash / v1-interface bridge cell
python -m tools.report_v2 --results results_v2
python -m pytest tests/ -q                           # tests/test_leakage_ci.py is slow (audits)
```
