# Phase 5 — files written or changed

Nothing is committed; everything is in the working tree on `main`. `docs/` and `datasets/` are git-ignored by
design, so their contents live on disk only. **Verified against disk by `tools/phase5/e5_cite_check.py` before
the phase was called done** *(pending)*.

## Pre-registration and reports

| File | What it is |
|---|---|
| `docs/env_v2/v2_1/PREREG_PHASE_5.md` | **new** — the pre-registration, written before any run; two pre-run corrections recorded in place (section 4.2, section 1) |
| `docs/env_v2/v2_1/PHASE_5_REPORT.md` | **new** — the phase report, written as results land |
| `docs/env_v2/v2_1/PHASE_5_CHANGED_FILES.md` | **new** — this file |
| `docs/env_v2/decisions/DECISION_LOG.md` | **appended** — P5-1 … |

## Generator and harness (every change is a switch with the v2 behaviour behind it)

| File | Change |
|---|---|
| `envs/v2/observables_params.py` | **new** — the loud loader for `params/observables.json` (the `events_params.py` pattern): raises on a missing entry, a null interval or an undeclared status; `resolve(obs_mode, overrides)` gives one run its section dicts (None = the pure v2 path); `FP_OBS_MODE=v2` forces v2 for a process; carries the v2 DESIGN constants (`V2`) |
| `envs/v2/observables.py` | **rewritten** — every block takes `params`; with `params=None` (or a section at design `"v2"`) the committed code runs verbatim (`_earnings_block_v2` is the committed function, kept whole). New: the FIT multiple (designs A/B), the loss chain and the "n/m" P/E (NaN in the frame), the FIT lag grid, Lintner-at-quarterly dividends with a payer draw, analyst designs A/C, sentiment designs A/B/C with a past-only trailing standardisation, volume designs A/B with past-only standardisation; `grid_draw` (the inverse-CDF sampler) |
| `envs/v2/generator.py` | `GenConfig.obs_mode` / `obs_overrides`; `_simulate_once` resolves the observable designs once and passes them to `announcement_schedule` and `SentimentState`; `PathResult.obs_params`; `event_meta["observables"]` |
| `envs/synthetic_market.py` | the Table 2 definitions name the design in force (`_obs_design`, read from the file); the blocks receive `params`; `rendered_fields` (CANONICAL minus the hidden fields under D10 `hidden` / analyst design B); `reported_PE` rendered as the string `'n/m'` when undefined; `pe_nm` hidden column; Table 2 definitions and rounding updated; metadata carries the designs and the rendered field list |
| `envs/v2/params/observables.json` (cited as `params/observables.json` in the phase documents, the Phase-4 convention) | **new** — written by `tools/phase5/apply_e5.py` from `e5_arms/decisions.json`; every entry carries label / source / date / interval / n / status (the `_status_key` vocabulary); multiple B, eps v21, dividend v21 (field shown; D10 both carried), analyst C PROVISIONAL, sentiment A PROVISIONAL (D15), volume A, audit_bounds PROVISIONAL |

## Tools (all new, under `tools/phase5/`)

| File | What it runs |
|---|---|
| `common.py` | the deployed-state pin, the audit-side "n/m" encoding, the field groups, the parallel SEP builder and the panel-vs-generator check |
| `prereg_power.py` | the inherited-number verification, the stored-panel check and PP1–PP6 |
| `e5_7a_ablation.py` | E5.7(a): the per-field-group ablation on a stored panel (add-one / drop-one, x / log V / L2b, all / calm, paired cluster bootstrap, permutation null margins) |
| `e5_1_multiple.py` | E5.1's P/E cross-section, persistence, dispersion decomposition, design grids |
| `fetch_8k.py` | EDGAR 8-K Item 2.02 dates for set A (into `datasets/`, never committed) |
| `e5_2_eps.py` | E5.2's seasonal residual, loss chain, n/m frequency, announcement and filing lags |
| `e5_2_clock.py` | the residual clock re-measured with E4.7's `eps_clock` unchanged, plus the interior-days variant |
| `e5_3_dividends.py` | E5.3's payer share, payout, quarterly Lintner, crash cuts |
| `e5_5_sentiment.py` | E5.5's deconvolution, loadings, reverse regression, valuation link, AAII, window references and window fits |
| `e5_6_volume.py` | E5.6's volume AR(1), \|r\| elasticity, run-up ratio |
| `e5_params.py` | the FIT sections assembled from the result files (one function for the arms and the parameter file) |
| `e5_panels.py` | the SEP design rendered under pinned overrides, with the fast renderer verified bit for bit against `panel_from_env` |
| `e5_arms.py` | the design arms: panels, per-arm statistics (KS, n/m share, item-12, item-7), ablation launch |
| `e5_7b_l1ext.py` | E5.7(b): the L1 extended candidate set |
| `e5_7c_onset.py` | E5.7(c): the onset-detection audit per field with the circular-shift null |
| `e5_l5.py` | L5 with an oracle subclass that encodes "n/m" as the audit does (the frozen oracle otherwise unchanged) |
| `e5_after_state.py` | the hand-over chain under Phase-5 names: panel, SEP audit, calm-trained comparison, checklist, path hashes, freeze |
| `e5_decide.py` | applies the registered decision rules (sections 4-9, with the addendum's readings) to the arm files on disk; the cross-arm paired CIs are drawn on the ablation tool's own resample indices; writes `e5_arms/decisions.{json,md}`, the input of `apply_e5.py` |
| `apply_e5.py` | writes `observables.json` with provenance and the status vocabulary, from `e5_decide.py`'s decisions file |
| `e5_arms_table.py` | the arms table of the report's section 3.8(d), generated from the arm files into a marked block (no number transcribed) |
| `e5_param_table.py` | the parameter table of the report's section 4, generated from `observables.json` into a marked block (the P4-47 test reads the status from it) |
| `e5_discrimination.py` | the discrimination table on the Phase-5 L5 csv beside Phases 4, 3 and 2 (`tools/phase2/e2_7_discrimination.summarise` unchanged; explicit `--out`) |

## Tests

| File | Change |
|---|---|
| `tests/test_v2_1_phase_5.py` | **new** — the five tests of plan §9.4, the inertness test, the n/m rendering/encoding test, the hidden-field test, the report-table consistency test |
| `tests/test_leakage_ci.py` | the `v2_audit` fixture encodes an undefined P/E as the cap plus the `reported_PE_nm` indicator (the registered audit-side convention, PREREG section 10d) before `run_audit`; without it the NaN APEs of the `k·P/reported_PE` candidate counted as inversions inside L1's floor (share above the floor 0.887 against price's 0.906 − 0.01) and `test_v2_L1_no_algebraic_inversion` failed on a candidate whose median APE is 0.64 |
| `tests/test_v2_generator.py` | the field-hygiene test reads the environment's `rendered_fields` (a hidden field is absent by design) and accepts the string `'n/m'` for an undefined P/E; `pe_nm` added to the hidden columns |

## Generated results (`docs/env_v2/generated/v2_1/`)

`e5_0/` power.{json,md} · `e5_1/` multiple.{json,md}, pe_panel_monthly.csv, ar1_by_stock.csv · `e5_5/` sentiment.{json,md},
sf_fed_raw_daily.csv · `e5_6/` volume.{json,md}, volume_by_stock.csv · `path_hashes_phase5_before.json` (HEAD worktree),
`path_hashes_phase5_v2check.json` · `e5_7a/baseline/` · `e5_7b/<arm>/` · `e5_7c/<arm>/` · `e5_arms/{arms.json,stats.json,decisions.json,decisions.md,<arm>/}` · `e5_2/` eps.{json,md}, clock/ · `e5_3/` dividends.{json,md} · `_panels/sep_phase5_*.pkl` (arm panels; regenerable)
**Final state (measured after `observables.json` settled):** `_panels/sep_phase5_after.pkl` (+ `sep_phase5_verify_manifest.json`) · `e5_after/audit_after_levelfree.md`, `e5_after/audit_after_levelfree.pkl`, `e5_after/audit_after_levelfree_L1.csv`, `e5_after/audit_after_levelfree_L2.csv`, `e5_after/audit_after_levelfree_L4.csv`, `e5_after/audit_after_levelfree_checklist_rows.csv` · `e5_after/calm_trained_phase5.{json,md}` · `e5_after_checklist.{md,csv}` · `path_hashes_phase5_after.json`, `path_hashes_phase5_compare.json` · `e5_7c/final/onset.{json,md}` · `e5_7a/final/ablation.{json,md}` · `e5_l5/l5_phase5_after.{csv,md}`, `e5_l5/discrimination.{json,md}` · `e5_final_chain.log` · `e5_tests_pass1.log`, `e5_tests_pass1b.log`, `e5_tests_leakage_ci.log`, `e5_tests_pass2.log` (the test-tree runs) · `tests/v2_freeze_manifest.json` re-frozen (27 files, `bdd429eb…`) · `docs/env_v2/generated/table2_v2_from_code.{md,json,tex}` and the rendered prompts regenerated · `docs/COMPUTE_GPU_ACCESS.md` (the lab box's status on 7 Sep)
