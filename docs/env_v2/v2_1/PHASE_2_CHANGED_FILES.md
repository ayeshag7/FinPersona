# Phase 2 (v2.1): every file written or changed

Nothing committed; everything is in the working tree on `main`. `docs/` and `datasets/` are git-ignored by design.
The report's §6 summarises this list. Phase 2 is complete; nothing here is provisional.

## Documents (`docs/env_v2/v2_1/`)

| file | what it is |
|---|---|
| `PREREG_PHASE_2.md` | **new** — the pre-registration, written before any Phase-2 run: seeds, the 17-moment vector, the block-bootstrap weight matrix and its shrinkage, the three engines and their free parameters, the optimiser and its ≥ 20 named starts, both acceptance criteria, E2.4's asymmetric rule with its consequences fixed in advance, E2.5/E2.6 designs, the decidability table |
| `PREREG_PHASE_2_ADDENDUM.md` | **new** — §1 the simulation-noise rule (unmeetable as written), §2 the compute-bound reductions, §3 E2.6's seed counts, **§4 the three post-review extensions** (E2.7 discrimination, E2.8 the exact-bound check, E2.6's levels inside the fitted interval). Each states what had been seen and fixes its rule before its run |
| `PHASE_2_REPORT.md` | **new** — this phase's report, under the plan's six headings |
| `PHASE_2_CHANGED_FILES.md` | **new** — this file |
| `PHASE_1_REPORT.md` | **changed** — three "[Phase 2 correction]" markers on the `s_x` figure (§4.2, §5 table, §6.1); no other Phase-1 number is touched |

## Decisions

| file | what changed |
|---|---|
| `docs/env_v2/decisions/DECISION_LOG.md` | **new Phase-2 section** with entries P2-1 … P2-19; one "[Phase 2 correction]" marker inside P1-15 |

## Generator and evaluation code

| file | what changed |
|---|---|
| `envs/v2/mispricing_params.py` | **new** — the loud-ish loader for `params/mispricing.json`: absent → the v2 engine and units, unchanged; present → it governs; malformed → raises |
| `envs/v2/mispricing.py` | the engine that runs is read from `params/mispricing.json` (`ENGINE_DEFAULT = MP.ENGINE`, falling back to v2's `fw_fallback_hl150`); `fitted_params()` builds the adopted engine (and `<engine>_hl<d>` sensitivities by rescaling φ at the fitted n̄); `ar1_rho()` / `is_ar1()` generalise the AR(1) branch and give the Phase-2 AR(1) engines the **exact** ρ = 2^(−1/h) while v2's `ar1` keeps its historical first-order ρ; the fitted engine keeps the unit-mean weight constant the SMM fitted it with instead of re-deriving it from a fresh pilot. **The legacy engines are unchanged**, including `price_scale = 100` (P2-2) |
| `envs/v2/params/mispricing.json` | **new** — the engine in force and its structural parameters, each entry with label / source / date / interval / n / survivor-vs-literature gap; the `structural` and `half_life` labels state what the fit is conditional on (P2-16) |
| `envs/v2/params/value.json` | `s_x_fit` corrected (P2-6) with the previous value recorded; `sigma_V` applied from E2.3 (D3 = (b)) and labelled **FIT, conditional on the engine**, with both Phase-1 estimates and the fit's other conditions recorded (P2-16) |
| `simulation/runner_v2.py` | `RunConfig.engine` now defaults to `ENGINE_DEFAULT` instead of the literal `"fw_fallback_hl150"`, so the runner cannot silently run a different engine from the one `params/mispricing.json` names |

## Phase-2 tools (`tools/phase2/`, all new)

| file | what it does |
|---|---|
| `fw_pure.py` | Franke & Westerhoff's own DCA-HPM, transcribed with their equation numbers; the published parameter sets read at source |
| `moments.py` | FW's nine moments (with their three-lag smoothing and Hill convention) plus the eight persistence-carrying ones; the joint stock × block bootstrap |
| `engines.py` | the three REG-4 candidates in one vectorised scaffolding, with their free-parameter sets and bounds |
| `prereg_power.py` | PA1–PA5, the decidability check behind every criterion |
| `e2_1_fw_repro.py` | E2.1: both conventions, both arms, the pre-registered diagnostic |
| `e2_3_data.py` | E2.3's data side: the moment targets and the weight matrices, cached so no third-party data has to move |
| `e2_3_smm.py` | E2.3: the SMM fits, the profiles, both acceptance criteria, the bootstrap refits, the machine reference row |
| `e2_2_persistence.py` | E2.2: the three estimators assembled, REG-5's rule, the sweep levels |
| `e2_4_engine.py` | E2.4: acceptance, held-out prediction, the decision, and (c)'s equivalence run |
| `e2_4_flat_x.py` | verification V7: the inherited E[x] known defect re-measured on the adopted engine |
| `e2_7_discrimination.py` | E2.7 (post-review): the policy spread — 16A G1's shape — on the handed-over state beside Phase 1's, with paired cluster-bootstrap gaps and the share of runs on which MCR is undefined |
| `e2_8_bound_check.py` | E2.8 (post-review): the level-free surrogate run on the EXACT process the Appendix-B bound describes, to separate a biased surrogate from an unmodelled channel |
| `e2_5_hl_table.py` | E2.5: the half-life estimator lookup, with the Andrews median function regenerated per horizon |
| `e2_6_sweep.py` | E2.6: the persistence sweep, both matchings, oracle switches, checklist, level-free surrogate |
| `v6_s_x_correction.py` | verification V6b and the `s_x_fit` correction, with its evidence |
| `apply_e2.py` | writes `params/mispricing.json` and applies the fitted σ_V to `value.json` |
| `after_state.py` | the hand-over state: path hashes, checklist, level-free audit, freeze |
| `phase2_chain.py` | the resumable stage runner |
| `phase2_numbers.py` | every Phase-2 number the documents cite, collected into `phase2_numbers.json` |

## Tests

| file | what changed |
|---|---|
| `tests/test_v2_1_phase_2.py` | **new** — the Section-6.4 tests |
| `tests/known_defects.py` | a Phase-3 entry added (the engine was fitted against E3.1's GARCH shape while the generator runs v2's CAL shape); **both Phase-2 entries cleared** — E[x] is fixed (P2-10) and `test_fundamentalist_share` is removed with a note (P2-11) |
| `tests/test_v2_1_stats.py` | `test_fundamentalist_share` removed with a note in its place; `test_half_life_consistency` re-pointed (analytic for the AR(1) engine, the 200,000-step pilot kept on the FW sensitivity); the SABCEMM figure corrected |
| `tests/test_v2_1_phase_1.py` | `test_flat_x_equivalence` hard again and re-pointed at Phase 2's measurement and at `day >= 1`; `test_jump_placement_variants`' magnitude threshold made relative to the other placements |
| `tests/test_v2_1_phase_0.py`, `tests/test_v2_generator.py`, `tests/test_docs_numbers.py` | engine assertions read the engine in force from the parameter file; the canonical φ is checked against `fw_fallback_hl150` by name, which is what it describes |
| `tests/v2_freeze_manifest.json` | rewritten on the handed-over state, label "v2.1 Phase 2 freeze", 21 files |

## Results (`docs/env_v2/generated/v2_1/`)

`e2_0/` (power.json, chain.log) · `e2_1/` (fw_repro.json, fw_repro.md) · `e2_2/` (persistence.json, persistence.md,
s_x_correction.json) · `e2_3/` (data_moments.json, data_moments.md, data_boot_*.npy, weight_*.npy,
reference_row.json, smm_*_*.json) · `e2_4/` (decision.json, decision.md, engine_diagnostics.json, flat_x.json, kalman_bound_phase2.json) · `e2_5/` (hl_table.json, hl_table.md,
andrews_median_T*.npz, hl_at_fitted.json, v4_engine_half_life_check.json) · `e2_6/` (sweep.json, sweep.md, checklist_*.csv/md) ·
`e2_4/bound_check.{json,md}` · `e2_7/` (l5_phase2_after.{csv,md}, discrimination.{json,md}) · `e2_3/weight_calibration.json` · `e2_6_after/audit_after_levelfree.*` (the SEP level-free audit on the handed-over state) · `e2_after_checklist.{md,csv}` · `path_hashes_phase2_after.json` · `phase2_numbers.json` · `_panels/sep_phase2_after.pkl` (git-ignored, regenerable)

## Not changed

`envs/v1/`, `docs/planning/`, `docs/env_v2/v2_1/archive/`, the plan, the alternatives register, `datasets/`,
`evaluation/`, `agent/`, and every legacy generator engine (`fw_fallback_hl*`, `fw_index`, `pruna`, `ar1`,
`fw_hl*`) with its stored burn-in states and its `price_scale = 100` convention. `simulation/` is changed in
exactly one line (`runner_v2.py`'s engine default), because a hard-coded engine name there would defeat
`test_engine_named_honestly`.
