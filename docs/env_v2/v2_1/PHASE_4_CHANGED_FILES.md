# Phase 4 — files written or changed

Nothing is committed; everything is in the working tree on `main`. `docs/` and `datasets/` are git-ignored by
design, so their contents live on disk only.

## Pre-registration and reports

| File | What it is |
|---|---|
| `docs/env_v2/v2_1/PREREG_PHASE_4.md` | **new** — the pre-registration, written before any run |
| `docs/env_v2/v2_1/PREREG_PHASE_4_ADDENDUM.md` | **new** — four corrections made after data were seen and before the runs they govern, each with a disclosure of exactly what had been seen: §1–2 the level hypothesis (refuted, replaced, one rule withdrawn unrun), §3 the empirical-vs-uniform sampler, §4 E4.6's coverage arithmetic |
| `docs/env_v2/v2_1/PHASE_4_REPORT.md` | **new** — the phase report under the six standard headings |
| `docs/env_v2/v2_1/PHASE_4_CHANGED_FILES.md` | **new** — this file |
| `docs/env_v2/decisions/DECISION_LOG.md` | **appended** — P4-1 … P4-18, each with the alternative rejected and the evidence file that decided it |

## Generator and harness (every change is a switch with the v2 behaviour behind it)

| File | Change |
|---|---|
| `envs/v2/events_params.py` | **new** — the loud loader for `params/events.json` (the `volatility_params.py` pattern). Raises on a missing entry **or a null interval**. Carries the v2 DESIGN ranges so the repository runs unchanged when the file is absent |
| `envs/v2/params/events.json` | **new** — the Phase-4 parameter file, written by `apply_e4.py`, every entry tagged ADOPTED / INCUMBENT / NOT DONE with label / source / date / interval / n |
| `envs/v2/schedule.py` | **rewritten** — ranges come from `events.json` when present; a range entry is either `[lo, hi]` (uniform) or `{"grid": [...]}` (an empirical quantile grid sampled by inverse CDF); `front_load` and the depth→delta and rec60→delta_end mappings added; per-run `ranges` override for E4.2's sweep; truncation recorded on the `Schedule`. `schedule_mode="v2"` reproduces v2 **bit for bit**, including the bull-trap draw order |
| `envs/v2/events.py` | **rewritten** — REG-8's four dynamics formulations on one code path (A tracking gain, B shifted p*, C scripted no-feedback, D unscripted regime); REG-7's four control definitions; the **real-time blow-off criterion** (the fix for the dead multiplier); the **decay post-top leg**; `realised_top_day`; a parameterised front-loading share; `crash_v_drift` tail-share mechanism (implemented, untested) |
| `envs/v2/generator.py` | `PathResult.drift` records the scripted drift d_t (so E4.6's script share is measured, not reconstructed); `top_day_realised` / `top_day_offset` and the Phase-4 switches in `event_meta`; `check_validity` honours REG-7's per-definition control rule (the x-band is definition C's only); `GenConfig` gains `schedule_mode`, `schedule_ranges`, `events_dynamics`, `control_definition`, `blowoff_mode`, `blowoff_g`, `post_top_mode`, `post_top_half_life`; the hazard defaults to `events.json`'s adopted mapping |
| `envs/v2/observables.py` | E4.7d -- a per-seed quarter-grid shift (`q_phase`) so `days_since_eps_announcement` stops being a deterministic function of the day index. `q_phase = 0` reproduces v2 exactly |
| `envs/synthetic_market.py` | REG-9's three day-index renderings behind `day_index_mode` (`day_n` / `none` / `date`), with the excluded crash windows and the key **omitted** rather than rendered as `None` under `none` |
| `experiments/arms_v2.py` | E4.7a — the **ordering factor** added to `FACTOR_DEFAULTS` and the grid, with a `--orderings` argument. The runner had always supported `ordering`; the grid never varied it, so every LLM cell ever run used `setup_first` |
| `tools/phase4/{e4_3_hazard,e4_5_control,e4_8_labels}.py` | **`schedule_mode` now PINNED.** None of the three pinned it, so all three silently measured the v2 ranges and their numbers were quoted as deployed properties (P4-19). This is the structural fix for that defect |
| `envs/v2/schedule.py` *(second pass)* | **`depth_mode`** (P4-40): `"centred"` shifts the fitted depth distribution so its centre tracks the `crash_discount` arm factor, which the unconditional draw discarded entirely — that is why checklist item 10 was exactly inert. A pure location shift, so the fitted shape survives (IQR 0.1333 either way), and **bit-identical to the old behaviour at the reference δ = 0.70**. Also **`depth_gain`**, implemented and switchable but **NOT adopted** — E4.20's loop does not close (P4-41) |
| `envs/v2/events_params.py` *(second pass)* | the **status-vocabulary guard** (P4-39b): `load` now raises when an entry carries a status `_status_key` does not declare. Two of ten entries were already violating it and nothing checked. Also `DEPTH_MODE` / `DEPTH_GAIN`, and `_SETTINGS` — scalar settings are excluded from the `RANGES` merge, because `list("centred")` would silently become a list of characters, the same failure mode as the `{"grid": …}` entries hitting `list()` in the first pass |
| `envs/v2/params/events.json` *(second pass)* | **D14 taken**: `control.definition` C → **A**, status ADOPTED (P4-43). `schedule_ranges.depth_mode = "centred"` (P4-40). `mania_drift` → TESTED, NOT ADOPTED with κ = 0's 96.3 % rejection recorded (P4-44). `hazard` → `IN FORCE, ADOPTION WITHDRAWN`, plus three new declared status terms (P4-39b) |
| `tests/known_defects.py`, `tests/test_v2_1_{stats,phase_4}.py` | **weakness items 18 and 42 CLOSED** (P4-43): both `test_sustained_bull_selection` strict xfails removed after they XPASSed under definition A, and both registry entries deleted. The registry no longer carries a Phase-4-owned defect |
| `tests/test_docs_numbers.py` | **P4-47** — asserts the report's section-4 parameter table matches `envs/v2/params/events.json` as deployed, and that every status term is declared in `_status_key`. The table had gone stale twice; generating it was an intention, this is a check. Verified by negative control (re-injecting the staleness fails the test) |
| `tests/test_v2_generator.py`, `tests/test_v2_1_phase_0.py` | four tests repaired that had been failing since the main pass, unseen because these files were never run (P4-38); plus `test_delta_moves_the_drawdown_under_the_centred_depth_draw` and `test_schedule_ranges_v21_stay_inside_the_fitted_grids`, which assert the v2.1 behaviour against grids read from `events.json` rather than hardcoded |
| `tools/phase3/episodes.py` | **extended, additively** — Pagan–Sossounov dating and `ps_bear_episodes`; a `depth_thr` argument on `drawdown_episodes` (default unchanged, so every Phase-3 call is bit-identical); `deterioration_length`, `front_loading`, `recovery_shares`, `runup_outcome`, `clean_runup_calm`; the Filimonov–Sornette `lppls_fit` with its stability diagnostic |
| `tests/v2_freeze_manifest.json` | **rewritten five times**, always 25 files: `5e392f3d42a8b751…` (main pass), `3473b174e5172707…` (verification pass), `869e4fbf4b6e64ba…` (completion pass — two stale provenance labels, values byte-identical, P4-38), `6d71a9c1be2be564…` (the depth switch and the status-vocabulary guard), and finally `cb2c7c7330ff5ecf964e06ac62dcdadb119c90553cb1df18a5786f487eb6f268` after D14 was adopted (P4-43). Each re-freeze is deliberate and logged; none was a workaround for a failing check |

## Tools (all new, under `tools/phase4/`)

| File | What it runs |
|---|---|
| `prereg_power.py` | PP1–PP6: every registered threshold's decidability at its stated n, simulated **before** the experiments it protects |
| `e4_0_level.py` | §1's inherited-number verification and E4.0a's decomposition (calm defect, fitted multiplier, scenario-mix, counterfactual) |
| `e4_0c_phase_levels.py` | E4.0c — the level decided conditional on phase, one estimator on both sides |
| `e4_1_episodes.py` | the episode tables: four drawdown families, run-ups, the corrected run-up calm reference, the cross-sectional drawdown share, the Shiller index table |
| `e4_1_lppls.py` | the LPPLS fits over every panel run-up, resumable, with the registered stability diagnostic and E4.4's trigger |
| `e4_2_schedule.py` | the three schedule arms, the rise-time criterion, the truncation rates and the decomposition of what binds the rise time |
| `e4_3_hazard.py` | REG-18's three mappings plus the {0.5×, 1×, 2×} bracket and the v2 incumbent |
| `e4_4_mania.py` | the LPPLS trigger's verdict, the convexity fit, the cap-binding test, amendment A5 |
| `e4_5_control.py` | REG-7's four definitions and their four audits, including the KS null-floor decidability check |
| `e4_6_dynamics.py` | REG-8's four formulations (A at four λ), the script share, coverage and the rejection ceiling |
| `e4_8_labels.py` | the blow-off criterion, the post-top half-life search, the top-day off-by-one, the multi-asset loading |
| `apply_e4.py` | writes `events.json` with provenance and checks the loader accepts it |
| `e4_9_deployed.py` | **the verification pass**: every Phase-4 number re-measured ON THE DEPLOYED STATE with no config overrides. Exists because three tools measured a state that did not yet exist; should be run as the last step of any future phase that writes a parameter file |
| `e4_10_verify_claims.py` | T1-T8: every Phase-4 claim that was INFERRED rather than measured, each tested against a stated falsifier |
| `e4_11_posttop_recal.py` | `post_top_drop` and `post_top_len` fitted from the panel, and the half-life re-searched on the deployed state |
| `e4_12_horizon.py` | the window-matched test of whether the topped share is a horizon property rather than a parameter defect |
| `e4_7_calendar.py` | **E4.7**, the registered deliverable that the first pass left undone: the setup-range sweep (rise time AND the day-only classifier at each setting -- the experiment P4-6 inferred), the ordering audit, the three renderings, and whether `days_since_eps_announcement` carries a clock |
| `e4_13_blowoff_cal.py` | P4-11's outstanding half: the blow-off multiplier's closed loop, written to `events.json` rather than to Phase 3's frozen `volatility.json` |
| `e4_14_crash_v.py` | item 73: where the crash's fundamental decline falls, against the EDGAR value proxy |
| `e4_15_multiasset.py` | what actually drives multi-asset co-drawdown, and whether the per-asset mechanism changes it |
| `e4_16_discrimination.py` | the policy-spread table re-run on the deployed state beside Phases 3 and 2. Takes an **explicit `--out`**: the Phase-3 equivalents hardcode Phase-3 names, which is how this phase overwrote `e3_after_checklist.*` |
| `e4_17_sep_audit.py` | the SEP level-free leakage audit on the deployed state. Builds its **own** panel under its own name -- `tools/phase3/after_state.py --stages audit` caches at `_panels/sep_phase3_after.pkl` and returns it if present, so running that would have audited Phase 3's stored paths and written the answer under Phase 3's name |
| `e4_18_calm_trained.py` | the CALM-TRAINED level-free surrogate, which is the brief's actual quantity. `leakage_audit.py` fits across all phases and masks afterwards (lines 297-300), so E4.17's "calm" row is cross-phase-trained and does not measure it. Imports `tools/phase3/e3_9_calm_trained.py`'s estimator **unchanged** so the comparison cannot drift, and re-runs Phase 3 in the same process as a reproducibility check |
| `e4_19_criteria.py` | **acting on section 5.1**: re-registers the inherited criteria against what the generator can express, and tests the two claims the D5 recommendation rested on. Runs on E4.6's STORED per-path output -- no regeneration, so it cannot drift from what was decided on. Refuted two of my own claims |
| `e4_20_depth_cal.py` | the crash-depth closed loop, the cause E4.19 identified for the coverage shortfall. **The loop does not close**; the tool reports that rather than adopting the best available gain |

## Generated results (`docs/env_v2/generated/v2_1/`)

`e4_0/` power.json+md, level.json, phase_levels.json+md · `e4_1/` episodes4.json, dd20.csv, dd30.csv,
ps_primary.csv, ps_sensitive.csv, runup4.csv, xsec_drawdown_share.csv, index_shiller.csv, lppls_fits.csv,
lppls.json+md · `e4_2/` schedule.json+md, paths_{v2,v21_uniform,v21_empirical,v21_fit}.csv · `e4_3/` hazard.json+md,
paths_*.csv · `e4_4/` mania.json+md · `e4_5/` control.json+md · `e4_6/` dynamics.json+md, crash_*.csv,
bull_*.csv, kaggle_guard.json, kaggle_kernel_summary.json · `e4_8/` labels.json ·
`path_hashes_phase4_after.json` · `e4_after_checklist.{md,csv}` · **verification pass:** `e4_9/`
deployed.json + bull/crash/control_deployed.csv · `e4_10/` verify.json · `e4_11/` posttop_recal.json+md ·
`e4_12/` horizon.json+md

**Completion pass** (verified against disk, after P4-37 found a cited file that was never written): `e4_7/` calendar.json · `e4_13/` blowoff_cal.json+md · `e4_14/` crash_v.json+md, episodes_v.csv · `e4_15/` multiasset.json+md · `e4_16/` discrimination.json+md, decomposition_phase4.json+md, l5_phase4_after.csv+md, audit_after_levelfree.{md,pkl} + _L1/_L2/_L4/_checklist_rows.csv · `e4_18/` calm_trained_phase4.json+md · `_panels/sep_phase4_after.pkl`


**Acting on the section 5.1 recommendations** (verified against disk): `e4_19/` criteria.json+md · `e4_20/` depth_cal.json+md · `e4_21/` the POST-D14 re-measurement -- audit_after_levelfree.{md,pkl} + _L1/_L2/_L4/_checklist_rows.csv, calm_trained_phase4.json+md, l5_phase4_postD14.csv+md, discrimination.json+md · `e4_16_preD14/` the PRE-D14 state, copied before the re-run so the before/after is a comparison and not an overwrite (P4-45) · `_panels/sep_phase4_preD14.pkl` beside the regenerated `sep_phase4_after.pkl`.
**Regenerated, not new:** `e3_after_checklist.{md,csv}` — `tools/phase3/after_state.py` hardcodes Phase-3
output names and its checklist stage overwrote them. The Phase-4 result was saved as `e4_after_checklist.*`
and the Phase-3 file was regenerated with `events.json` removed; it reproduces Phase 3's published figures
exactly (topped 8 %, peak P/V 1.49, bull-trap rejection 10.7 %, crash 0.8 %, sustained-bull 32.9 %, 5/20
passing), which is also an end-to-end confirmation that the v2 path is bit-identical. **The tool still
hardcodes those names and should be parameterised before Phase 5 uses it.**

## Tests

| File | Change |
|---|---|
| `tests/test_v2_1_phase_4.py` | **new** — the seven tests of plan §8.4 plus five more: the parameter file's provenance, the blow-off label reaching the driver, the post-top leg no longer being drift-dominated, the realised top day, the v2 bit-identity of the schedule, and the grid sampler reproducing the panel's shape. **15 passed, 1 xfailed** against the handed-over state, including three guards added by the verification pass: that measurement tools pin the schedule, that post_top_drop/post_top_len are FIT grids rather than stipulated intervals, and that all four switches together reproduce v2 on seeds that actually exercise the post-top leg |
| `tests/known_defects.py` | the sustained-bull entry **re-registered** with `owner: "the team, via D14"` and the E4.5 evidence in its reason; the registry footer now prints it |
| `test_sustained_bull_selection` | **re-registered**, not closed: it carries a strict xfail whose reason names its new owner (the team, via D14) and its evidence (`e4_5/control.json`). The measurement that would close it is done; the adoption is D14's |

## Regression against the handed-over state

`test_v2_1_phase_{1,2,3}.py` + `test_v2_1_stats.py` + `test_provenance_and_freeze.py`: **34 passed, 1 xfailed
in 3:51** — the Phase-4 event block has not broken Phases 1–3, and the rewritten freeze manifest verifies. The
single xfail is the re-registered `test_sustained_bull_selection`. Not run: the leakage-CI, eval,
render-prompt, docs-numbers and stateful/multi-asset suites.

## Kaggle

`ayeshaiq/finpersona-phase3-bundle` versioned twice (code plus the `e4_0`–`e4_2` derived inputs; `datasets/`
never uploaded). Kernel `ayeshaiq/fp-p4-e46`, two versions. The reference-row guard agreed with the committed
`e2_3/reference_row.json` to a worst relative difference of **0.0** under numpy 2.0.2 / scipy 1.16.3; E4.6 then
ran its seven-arm grid at 1,000 + 1,000 seeds in 385 s.
