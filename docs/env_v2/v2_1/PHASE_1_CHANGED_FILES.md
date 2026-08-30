# Phase 1 (v2.1): every file written or changed

Session of 29–31 August 2026 (Phase 1 plus the team's post-review extensions). Companion to
`PHASE_1_REPORT.md` §7. Nothing under `envs/v1/`, `docs/planning/`, `docs/env_v2/v2_1/archive/`, the plan, the
alternatives register or `datasets/` was touched.

## 1. Documents (`docs/env_v2/v2_1/`)

| file | status | what it is |
|---|---|---|
| `PREREG_PHASE_1.md` | unchanged since it was written | the pre-registration, fixed before any run |
| `PREREG_PHASE_1_ADDENDUM.md` | new | §1–2 E1.4's E[x] criterion (undecidable at 200 seeds) corrected; §3 reporting rule; §4 E1.5's burn-in KS bound (undecidable at 500 paths) corrected; §5 estimator-C scope; §6 the post-review extensions, the D13 revision and the reproducibility finding |
| `PHASE_1_REPORT.md` | new | the phase report under the six protocol headings |
| `PHASE_1_CHANGED_FILES.md` | new | this file |
| `docs/env_v2/decisions/DECISION_LOG.md` | appended | Phase 1 section, entries P1-1 … P1-15 |

## 2. Generator and evaluation code

| file | status | change |
|---|---|---|
| `envs/v2/generator.py` | modified | start-price mechanisms `fixed`/`randomise`/`normalise`/`both`; jump placements `x_negmean`/`x_zero`/`V_announce`/`both`; per-engine burn-in days and mode resolved from `value.json`; stored-state burn-in; announcement days shared by the V jump and the EPS field; `k_render` on the result |
| `envs/v2/value_params.py` | **new** | loud loader for `params/value.json` (missing or incomplete file raises), `burn_in_for`, `burn_in_mode_for` |
| `envs/v2/params/value.json` | **new** | every Phase-1 parameter with provenance (label / source / date / interval / n / survivor gap) |
| `envs/v2/params/burn_in_states_<engine>.npz` (×5) | **new** | E1.5 option-B day-1 states for the five engines |
| `envs/v2/rng.py` | modified | streams `announce`, `start_price`, `init_state` |
| `envs/v2/events.py` | modified | announcement-day machinery for the EPS field and V jumps |
| `envs/v2/observables.py` | modified | announcement-day EPS field; render-scale handling |
| `envs/synthetic_market.py` | modified | mechanism C's render scale on price-denominated fields; `audit_panel(seed0=…)` |
| `evaluation/leakage_audit.py` | modified | level-free control (new default), `--no-subsample`, APE percentiles in L1, cluster-bootstrap intervals on L2, stored-panel CLI, audit title |
| `evaluation/observables_oracle.py` | modified | level-free feature set for L5 |
| `tools/l5_report.py` | modified | `--feature-sets`, `--out`, `--config` |

## 3. Phase-1 tools (`tools/phase1/`, all new)

`panel.py` (exclusion rule, analysis sets, loaders) · `e3_1_garch.py` · `e1_2_vr.py` (estimator A) · `e1_2_pv.py`
(estimator B) · `e1_2_misc.py` (μ_V, df_V, start-price range, V̂ noise) · `calm_sim.py` · `e1_2_recovery.py`
(estimator C and the recovery study; cached cells, `--ab-hs`, `--c-hs`, `--n-boot-refits`, cached data moments, grid
extended to h = 5 and 10) · `merge_recovery_caches.py` · `apply_e1_2.py` · `e1_2_two_component.py` (exploratory) ·
`e1_4_panel.py` · `e1_4_generator.py` · `e1_4_confirm.py` · `apply_e1_4.py` · `e1_5_burn_in.py` · `apply_e1_5.py` ·
`e1_1_start_price.py` · `e1_3_sweep.py` · `e1_3_calm_reconcile.py` · `e1_3_override_check.py` ·
`e1_3_repro_point.py` · `e1_3_determinism_check.py` · `kalman_bound.py` · `before_state.py` (`FROZEN_CFG`,
`frozen_check`) · `phase1_chain.py` (resumable stage runner) · `phase1_numbers.py`.

## 4. Tests

| file | status | change |
|---|---|---|
| `tests/test_v2_1_phase_1.py` | **new** | σ_V in force, loud loader, start-price attacker, render-scale invariance, jump placements, E[x] equivalence, burn-in stationarity, Kalman table, level-free key set |
| `tests/known_defects.py` | modified | registry now: E[x] equivalence → Phase 2; L2b selectivity → Phase 6. Removed: the L1 entry (its registered failure disappeared) and the start-price entry (mechanism C passes) |
| `tests/test_v2_1_stats.py` | modified | `test_flat_x_unbiased` promoted to a hard test |
| `tests/test_leakage_ci.py` | modified | L1 hard again; L2b repointed at the published 1,600-path audit with the 8-seed panel as a live guard |
| `tests/test_v2_generator.py` | modified | start-price assertions for mechanism C; burn-in read from `value.json` |
| `tests/test_env_logic.py` | modified | `P₁ = 100` under the mechanism in force (was `V₁ = 100`) |
| `tests/test_docs_numbers.py` | modified | burn-in and jump placement now read from `phase1_numbers.json` |
| `tests/v2_freeze_manifest.json` | modified | rewritten deliberately on the handed-over state (19 files; `value.json` and `value_params.py` added) |

## 5. Results (`docs/env_v2/generated/v2_1/`)

- `e1_0_analysis_sets.{csv,json}` — the panel exclusion rule and sets A (417) / B (155).
- `e3_1/` — per-stock GJR-GARCH-t fits, residuals, summary.
- `e1_2/` — `vr_fit` (A), `pv_fit` (B), `smm_fit` (C, 30 refits), `recovery` (all 32 cells), `recovery_diagnostics`,
  `decision`, `misc_fits`, `calm_sim_equivalence`, `andrews_median_table.npz`, `smm_data_moments`,
  `vr_two_component_exploratory`, per-stock CSVs, `cache/` (one file per recovery cell).
- `e1_4/` — `panel_split` (announcement windows on the panel), `panel_residuals_split.parquet`, `generator_split`
  (the four placements), `confirm_B_x_zero`, `confirm_jumps_off`.
- `e1_5/` — `burn_in` (2,000 paths), `burn_in_n500` (the pre-registered run, undecidable),
  `reference_states_<engine>.npz`, `day1_states_{before,after}.npz`.
- `e1_1/start_price.{json,md}` — the four mechanisms, attacker and rule-100 tests, L1 candidates.
- `e1_3/` — `sweep` (local reference environment), `sweep_kaggle.*` (record-only), `calm_reconcile`,
  `override_check`, `repro_point`, `determinism_check`.
- `e1_6/` — `audit_{before,after}_{levelfree,level}.*` (all four on the reference environment) with `*_kaggle` and
  `*_B` kept record-only, `l5_{before,after}.{csv,md}`, `frozen_equivalent_check.json`.
- `e1_6_checklist_{before,after}.{csv,md}`, `kalman_bound_verification.json`,
  `path_hashes_phase1_{before,after,afterB}.json`, `phase1_numbers.json`.
- `_panels/` — the stored SEP panels (before / after / afterB), the four E1.1 mechanism panels, the pre-patch
  `s11_fixedOLD_prepatch_*`, and the run and test logs. **These are large intermediates** (~1.2 GB of `.pkl`);
  they are regenerable with `tools/phase1/before_state.py` and are what makes `docs/` too large to push to GitHub
  as-is (five files exceed the 100 MB per-file limit).

## 6. Not changed

`envs/v1/`, `docs/planning/`, `docs/env_v2/v2_1/archive/`, `V2_1_IMPROVEMENT_PLAN.*`,
`V2_1_ALTERNATIVES_REGISTER.md`, `datasets/` (third-party data, git-ignored, re-downloadable via `tools/e1_0_data/`).
