# Phase 3 (v2.1): every file written or changed

Nothing committed; everything is in the working tree on `main`. `docs/` and `datasets/` are git-ignored by
design. The report's §6 summarises this list. (Finalised at hand-over.)

## Documents (`docs/env_v2/v2_1/`)

| file | what it is |
|---|---|
| `PREREG_PHASE_3.md` | **new** — the pre-registration, written before any Phase-3 run: seeds, the panel, every window definition, the E3.2 estimator and its recovery gate, E3.3's episode definitions, REG-6's rule restated, the E3.5 construction and its three checks, the engine-refit decision (§9), the PA1–PA7 decidability table (updated in place with the measured rows, as it says) |
| `PREREG_PHASE_3_ADDENDUM.md` | **new** — §1 the run-up calm-window reference corrected to the unconditional level; §2 the fast-crash subpopulation registered as the adoption-governing secondary for E3.4; §3 the E3.2 adoption corrected after BOTH registered paths failed measurably; **§4 the four post-review extensions** (the calm-trained surrogate, `sbar`'s registered interval, the calm-window mapping + level double-count, the jump-size span), each with its rule fixed before its run and a correction to the review's own residual characterisation. Results under both rules throughout |
| `PHASE_3_REPORT.md` | **new** — this phase's report, under the plan's six headings |
| `PHASE_3_CHANGED_FILES.md` | **new** — this file |

## Decisions

| file | what changed |
|---|---|
| `docs/env_v2/decisions/DECISION_LOG.md` | **new Phase-3 section**, entries P3-1 … **P3-17** (P3-12 withdraws this phase's own calm-channel reading; P3-13/14/15 deliver the post-review measurements; P3-16 the six checkable corrections; P3-17 the re-freeze evidence) |
| `docs/env_v2/spec/E1_V2_GENERATOR_SPEC.md` | §4 rewritten (the volatility block as now built, every parameter FIT); §6's IV paragraph replaced by E3.5's construction |
| `docs/env_v2/README.md` | the status paragraph extended with Phase 3's summary |

## Generator and evaluation code

| file | what changed |
|---|---|
| `envs/v2/volatility_params.py` | **new** — the loader for `params/volatility.json` (mispricing_params pattern: absent → v2 CAL, present → governs, malformed → raises; presence enforced by `test_garch_params_in_force`) |
| `envs/v2/garch.py` | `GJRParams` reads its defaults from `volatility_params`; FIT phase multipliers (`mult`), mechanism B's ramped ω (`ramp_days`), mechanism C's two-regime switching (`switching`, drawing from the new `regime` stream); the v2 CAL constants remain the documented fallback and every legacy path is bit-identical when the new fields are absent |
| `envs/v2/observables.py` | **`iv_block_v21`** (E3.5: past-only GJR filter on observed returns, constant FIT premium, AR(1) FIT noise from the day-indexed `iv` stream; no floor, no stress trigger, no whole-path quantile) and `iv_filter_forecast`; the v2 `iv_block` kept for the record with its weakness note |
| `envs/v2/rng.py` | components `regime` (17) and `iv` (18) appended (append-only registry: no existing path changes) |
| `envs/v2/generator.py` | `GenConfig.iv_mode` (None → volatility.json's construction; `"v2"` → legacy); the regime-uniform stream drawn and passed to the GARCH step under `scale_mode="switching"` |
| `envs/synthetic_market.py` | the IV path selection; Table 2 entries for the new IV definition and the hidden `iv_fc21` / `iv_eps` columns |
| `envs/v2/params/volatility.json` | **new** — the volatility block in force with provenance (written by `tools/phase3/apply_e3.py`) |
| `envs/v2/params/value.json` | `sigma_V` from the §9 refit; the jump entry re-fitted (E3.2) |
| `envs/v2/params/mispricing.json` | structural (σ_V, h) from the §9 refit; `garch_shape` now APPLIED; `applied` records sbar's application through volatility.json |

## Phase-2 tools extended (opt-in, Phase-2 defaults bit-identical — `test_smm_reference_row` guards it)

| file | what changed |
|---|---|
| `tools/phase2/engines.py` | engine `ar1c` (free = σ_V, h); opt-in base keys `garch_shape`, `jump_rate` / `jump_sd` (x_zero jumps, drawn after every Phase-2 draw), `sbar_identity` (PREREG §3.4's constraint) |
| `tools/phase2/e2_3_smm.py` | `--base-json`, `--seed-sm/--seed-sb/--seed-mc` (fresh Phase-3 seed blocks); `run_cell` threads them |

## Phase-3 tools (`tools/phase3/`, all new)

| file | what it does |
|---|---|
| `episodes.py` | the shared episode estimator (drawdowns, run-ups, windows, RV, rise/decay) — one code path for panel and generator |
| `prereg_power.py` | the PA rows measurable before the experiments (PA3 pilot) |
| `e3_1_confirm.py` | V1/V2/V3/V5 verifications and the P25/P75 shape sensitivity sets |
| `e3_2_jumps.py` | E3.2: detection, the (ν, λ, σ_J) mixture fit with stock-bootstrap refits, and the 6-cell × 5-replicate recovery gate |
| `e3_3_episodes.py` | E3.3: the episode families, multipliers under both references, rise/decay/spell, the market windows |
| `e3_4_mechanism.py` | E3.4: the closed-loop m_x calibration, mechanism C's derived parameters, the three arms, REG-6's decision under both rules |
| `e3_5_premium.py` | E3.5 panel side: the premium family CV on the five CBOE names, the ε AR(1) |
| `e3_5_audit.py` | E3.5 audits: the onset-detection ΔAUC with its permutation null, and the T_z derivation |
| `e3_6_item73.py` | E3.6: item 5's statistic on calm windows only and on the whole path |
| `e3_7_discrimination.py` | E3.7: E2.7's discrimination table on the Phase-3 hand-over (reuses Phase 2's summariser) |
| `e3_8_decomposition.py` | E3.8: the level-free channel decomposed one volatility block at a time (P2-18's hand-off) |
| `make_block.py` | assembles the block in force for the experiment stages |
| `e3_4_flat_x_p3.py` | FX3: the E[x] guard re-measured at the block in force (seeds 240000+) |
| `e3_burn_in_guard.py` | the E1.5-style burn-in guard for the engine in force under the Phase-3 block (fresh day-5000 reference) |
| `v4_check.py` | V4: the identity's unconditional-sd verification by long simulation |
| `after_state.py` | the Phase-3 hand-over stages (hashes, checklist, SEP audit, freeze) |
| `apply_e3.py` | writes `volatility.json` (+ `--add-tz`), updates `value.json` and `mispricing.json` |
| `e3_9_calm_trained.py` | **post-review** — the level-free surrogate trained on calm rows only, on both phases' stored panels (the estimator the published audit does not use) |
| `e3_9_sbar_interval.py` | **post-review** — PREREG §3.4's registered Monte-Carlo propagation for `sbar`'s interval |
| `e3_9_level_check.py` | **post-review** — the panel's calm sd, the calm-window mapping, and the deployed-unconditional double-count check |
| `e3_9_jump_sensitivity.py` | **post-review** — the jump channel across σ_J's adopted interval, sbar re-derived at each |

## Tests

| file | what changed |
|---|---|
| `tests/test_v2_1_phase_3.py` | **new** — `test_garch_params_in_force`, `test_iv_no_lookahead`, `test_jump_process`, `test_volatility_loader_malformed` |
| `tests/test_v2_1_stats.py` | `test_iv_continuity` flipped **hard** with the derived T_z (weakness 46/25 closed) |
| `tests/test_v2_1_phase_1.py` | `test_flat_x_equivalence` re-pointed at the FX3 measurement on the block in force; `test_jump_placement_variants` converted to a machinery probe at explicit probe values (the fitted λ is 17× rarer, making the old invariant vacuous); `test_burn_in_stationary` live-guards the ENGINE IN FORCE against a fresh reference and documents the legacy engines' stale Phase-1 references |
| `tests/test_docs_numbers.py` | the jump-constants chain: GenConfig == value.json (in force) and the Phase-0 canonical numbers == the entry's recorded v2 CAL `previous` |
| `tests/test_v2_1_phase_2.py` | `test_garch_shape_matches_e3_1` flipped **hard** and strengthened (checks the shape against volatility.json and the file against E3.1; P2-12 closed) |
| `tests/known_defects.py` | both Phase-3 entries cleared; the L2b entry's figure corrected to the audit in force (+12.7 pp, with the Phase-1/2/3 series) |
| `tests/v2_freeze_manifest.json` | rewritten on the handed-over state, then again after the post-review provenance edits — label **"v2.1 Phase 3 freeze (post-review)"**, 23 files, hash `bac2a8a2`; the edits are proven path-neutral (P3-17) |

## Results (`docs/env_v2/generated/v2_1/`)

`e3_0/power.json` (PA1–PA7 + the Kaggle reference-row proof) · `e3_1/confirm.json` ·
`e3_2/{detection,moments,fit,fit_fallback,recovery,adoption,size_decomposition,refit_base}.json`,
`detection.md`, `boot_moments.npy`, `sigma_bins.npz` · `e3_3/{episodes.json,episodes.md,dd_episodes.csv,ru_episodes.csv,market.csv}` ·
`e3_4/{block,calibration,mechanism_c,arms,decision,pi_uncond,v4_uncond_check,burn_in_guard,flat_x_p3}.json`,
`decision.md` · `e3_5/{premium,audit}.{json,md}` · `e3_6/item73.{json,md}` ·
`e3_7/{l5_phase3_after.csv,discrimination.{json,md}}` · `e3_8/decomposition.{json,md}` ·
`e2_3/smm_ar1c_full_p3.json` + `smm_ar1_full_p3u.json` (the unconstrained sensitivity) · `e2_5/hl_at_h22.json` ·
`e1_5/reference_states_ar1_fit.npz` (the fresh burn-in reference) · `e3_after_checklist.{md,csv}` ·
`e3_9/{calm_trained,sbar_interval,level_check,jump_sensitivity}.json` (+ `.md` for three) ·
`path_hashes_phase3_after.json` and `path_hashes_phase3_after_postreview.json` (0 of 190 columns differ) ·
`e3_after/audit_after_levelfree.*` (SEP, local reference machine) ·
`_panels/sep_phase3_after.pkl` (git-ignored, regenerable)

## Not changed

`envs/v1/`, `docs/planning/`, `docs/env_v2/v2_1/archive/`, the plan, the alternatives register, `datasets/`,
`evaluation/`, `agent/`, `simulation/`, the legacy generator engines and their stored burn-in states (see the
report §7 on their staleness under the new shape).
