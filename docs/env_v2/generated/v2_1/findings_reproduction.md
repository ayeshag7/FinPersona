# Phase 0 findings reproduction (v2.1)

Every computational finding of the three v2 reviews recomputed on fresh seeds (PREREG_PHASE_0.md §1–3) on the **unmodified** v2.0 generator (`before`), with n, the 95 % interval and the reviewers' value beside mine. Verdicts: **R** reproduced (PREREG §3), **S** reproduced in substance, **N** not reproduced, **D** documentary. Intervals are percentile cluster bootstraps over paths unless the row says Wilson / IQR / min–max. Produced by `python -m tools.verify_v2_findings`; the per-block numbers are in `findings/*.json`.

Verdict counts over 149 rows: R 97, S 5, N 16, D 31

| Block | Item | Statistic | Mine | n | 95 % interval | Reviewer | Source | Verdict | Note |
|---|---|---|---|---|---|---|---|---|---|
| R10_analyst | 68 | pooled sd(u), full 460-day timeline | 0.335 | 100 | [0.314, 0.355] | 0.306 | LOG §1 (30 crash seeds); PLAN 0.350 | **R** |  |
| R10_analyst | 68 | pooled sd(u), benchmark days | 0.352 | 100 | [0.323, 0.377] | 0.333 | C §D.24 measured 0.333; LOG 0.330; analytic 0.15√5 = 0.335 | **R** |  |
| R10_analyst | 68 | median |u|, benchmark days | 0.247 | 100 | [0.224, 0.272] | 0.222 | LOG §1; B 0.21 | **R** |  |
| R10_analyst | 68 | documented stationary sd | 0.150 | 0 | — | 0.150 | observables.py docstring, spec §6, slide 5 | **D** | analytic implemented value 0.15 × √5 = 0.335 |
| R10_analyst | 68 | crash δ 0.70 envs: pooled sd(u) on benchmark days | 0.339 | 50 | [0.303, 0.370] | 0.330 | LOG §1 | **R** |  |
| R10_analyst | 21 | median |F/V − 1| of the analyst field (all four scenarios) | 0.245 | 200 | [0.228, 0.261] | 0.224 | leakage_audit_v2.md k·analyst median APE | **R** |  |
| R11_iv_lookahead | 25 | crash: share of benchmark days whose stress flag differs between the full-path and a past-only 0.9 quantile | 0.085 | 50 | [0.064, 0.106] | 0.090 | C §A.7 | **R** |  |
| R11_iv_lookahead | 25 | crash: share of flagged days (full-path rule) that are panic days | 0.659 | 50 | [0.586, 0.736] | 0.750 | C §A.7 | **R** |  |
| R12_smm | 35 | REJECTED.json: J | 408.2 | 0 | — | 408.1 | B row 12 | **D** | start-J recorded: False; tickers 10 (survivors); price_scale 100.0 |
| R12_smm | 35 | J-profile over phi (diagonal 1/target² proxy weights): min–max of J | 2.89–3.16 | 7 | — | 2.9–3.2 (flat) | CALIBRATION_REPORT §6 | **D** | phi grid 0.03, 0.06, 0.12, 0.25, 0.5, 1.0, 2.0 |
| R12_smm | 35 | pilot n̄ at every phi of the profile grid (price_scale 100, 20,000 steps, seed 12345) | φ 0.03: 0.9991; φ 0.06: 0.9988; φ 0.12: 0.9985; φ 0.25: 0.9979; φ 0.5: 0.9974; φ 1.0: 0.9970; φ 2.0: 0.9954 | 7 | — | n_f ≈ 1 throughout | B row 12 / C §A.1 | **R** | the profile was computed where chartists never act |
| R13_half_life | 36 | S200: median sample half-life −ln2/ln ACF(1) of x on the whole (calm) window | 20.060 | 50 | [16.131, 24.236] | 26.000 | PLAN 26 d (30 flat); LOG 35 d; C 14 d (calm windows) | **R** | IQR 14–29 d; share >= 60 d 0.00 (Wilson 0.00–0.07); median within-window sd(x) 0.061; median ACF(1) 0.9660 |
| R13_half_life | 36 | S800: median sample half-life −ln2/ln ACF(1) of x on the whole (calm) window | 61.920 | 50 | [55.349, 80.710] | 72.000 | checklist item 9 (20 paths) 72 d; PLAN/LOG 65 d; B 62 d | **R** | IQR 49–90 d; share >= 60 d 0.52 (Wilson 0.39–0.65); median within-window sd(x) 0.121; median ACF(1) 0.9889 |
| R13_half_life | 36 | S5000: median sample half-life −ln2/ln ACF(1) of x on the whole (calm) window | 173.6 | 10 | [120.7, 226.4] | — |  | **D** | IQR 128–199 d; share >= 60 d 1.00 (Wilson 0.72–1.00); median within-window sd(x) 0.171; median ACF(1) 0.9960 |
| R13_half_life | 36 | pure AR(1) hl150_T800: median sample half-life (200 paths) | 59.325 | 200 | [28.892, 142.4] | 62.000 | B row 9 (check_bias.py) | **R** | 5–95 %: 29–142 d; share >= 60 d 0.49 (reviewer 0.54); tolerance 15 % (sampling of 200-path medians) |
| R13_half_life | 36 | pure AR(1) hl150_T200: median sample half-life (200 paths) | 19.657 | 200 | [6.762, 47.966] | 21.000 | B row 9 (check_bias.py) | **R** | 5–95 %: 7–48 d; share >= 60 d 0.01; tolerance 15 % (sampling of 200-path medians) |
| R13_half_life | 36 | pure AR(1) hl150_T2000: median sample half-life (200 paths) | 95.633 | 200 | [57.491, 202.3] | 98.000 | B row 9 (check_bias.py) | **R** | 5–95 %: 57–202 d; share >= 60 d 0.93; tolerance 15 % (sampling of 200-path medians) |
| R13_half_life | 36 | pure AR(1) hl150_T5000: median sample half-life (200 paths) | 123.9 | 200 | [81.170, 206.1] | 127.0 | B row 9 (check_bias.py) | **R** | 5–95 %: 81–206 d; share >= 60 d 0.99; tolerance 15 % (sampling of 200-path medians) |
| R13_half_life | 36 | pure AR(1) hl580_T800: median sample half-life (200 paths) | 84.145 | 200 | [35.408, 217.3] | 84.000 | B row 9 (check_bias.py) | **R** | 5–95 %: 35–217 d; share >= 60 d 0.69; tolerance 15 % (sampling of 200-path medians) |
| R13_half_life | 36 | pure AR(1) hl60_T800: median sample half-life (200 paths) | 39.707 | 200 | [20.496, 71.273] | 41.000 | B row 9 (check_bias.py) | **R** | 5–95 %: 20–71 d; share >= 60 d 0.12; tolerance 15 % (sampling of 200-path medians) |
| R13_half_life | 71 | pull-rate half-life ln2/(μ n̄ φ) at the live parameters | 150.0 | 0 | — | 150.0 | LOG §1 | **R** | φ = 0.4632, n̄ = 0.9976, μ = 0.01 |
| R13_half_life | 71 | cached 20,000-step pilot (seed 12345, sd_e 0.016, raw weights): ACF(1)-implied half-life | 188.5 | 1 | — | 188.5 | LOG §1 | **R** | ACF(1) 0.99633; sd_x 0.1423 (what CALIBRATION_REPORT §1 prints as 0.142) |
| R13_half_life | 71 | five 200,000-step pilots (engine weights, sd_e 0.017): ACF(1) half-life mean [min–max] | 146.6 | 5 | [141.5, 155.4] | 147.0 | LOG §1 (141–154, mean 147); pass-3 142 / 160 | **R** | sd(x) mean 0.1752 [0.1721–0.1800]; mean n_f 0.9981 |
| R13_half_life | 71 | five 200,000-step pilots (engine weights, sd_e 0.016): ACF(1) half-life mean [min–max] | 146.6 | 5 | [141.6, 155.3] | 147.0 | LOG §1 (141–154, mean 147); pass-3 142 / 160 | **R** | sd(x) mean 0.1650 [0.1620–0.1693]; mean n_f 0.9980 |
| R13_half_life | 71 | five 200,000-step pilots (raw weights, sd_e 0.017): ACF(1) half-life mean [min–max] | 146.6 | 5 | [141.5, 155.4] | — |  | **D** | sd(x) mean 0.1335 [0.1311–0.1372]; mean n_f 0.9975 |
| R13_half_life | 71 | five 200,000-step pilots (raw weights, sd_e 0.016): ACF(1) half-life mean [min–max] | 146.6 | 5 | [141.5, 155.4] | — |  | **D** | sd(x) mean 0.1257 [0.1235–0.1291]; mean n_f 0.9973 |
| R13_half_life | 71 | stationary sd(x): 200k pilots, engine weights (sd_e 0.016 / 0.017) | 0.1650 / 0.1752 | 5 | — | 0.162–0.169 (LOG, held) | LOG §1; PREREG §8 prediction 0.167 / 0.177 | **R** |  |
| R13_half_life | 71 | stationary sd(x): 200k pilots, raw weights as pilot_stats measures (sd_e 0.016 / 0.017) | 0.1257 / 0.1335 | 5 | — | 0.131 / 0.140 (pass-3, sd_e 0.017); 0.142 (calibration report, 20k) | PREREG §8 prediction 0.127 / 0.135 | **R** | ratio raw/engine = 0.762 vs w̄ = 0.761 (hypothesis H: the pilot understates the engine's sd by the factor w̄) |
| R13_half_life | 71 | full generator, T = 5000 flat (jumps on): sample sd(x) mean over 10 seeds | 0.196 | 10 | [0.125, 0.403] | — |  | **D** | min–max over seeds; GARCH-t innovations |
| R13_half_life | 71 | full generator, T = 5000 flat (jumps off): sample sd(x) mean over 10 seeds | 0.186 | 10 | [0.127, 0.407] | — |  | **D** | min–max over seeds; GARCH-t innovations |
| R13_half_life | 71 | what a 200,000-step normalisation would change: n̄, w̄, φ (relative to the cached 20k values) | n̄ 0.99734 vs 0.99765; w̄ 0.76154 vs 0.76113; φ 0.46333 vs 0.46319 (+0.031%) | 5 | — | — |  | **D** | deferred to Phase 2: any change moves every path (PREREG §4.5) |
| R14_item10 | 40 | crash: event-window MDD partial R² of δ (controlling D_V) | 0.373 | 150 | [0.295, 0.493] | 0.380 | checklist_v2.md (150 paths) | **R** |  |
| R14_item10 | 40 | crash: event-window MDD spread δ 0.55 vs 0.85 (pp) | 17.271 | 150 | [15.811, 18.756] | 18.000 | checklist_v2.md | **R** | event-window MDD: partial R2 of delta (controlling D_V) = 0.37, spread between delta 0.55 and 0.85 = 17.3 pp, means 0.55: -53.9%, 0.7: -44.1%, 0.85: -36.6%; whole-path MDD (reported): partial R2 0.41, spread 15.9 pp, means 0.55: -57.6%, 0.7: -48.5%, 0.85: -41.6% |
| R15_uncapped | 41 | bull_trap (g_max = 1.0, reject=False): share of runs with peak P/V > 3 | 0.180 | 50 | [0.098, 0.308] | 1.000 | A5 / spec §3: 'without a cap every run reaches P/V > 3' | **N** | topped share 0.86; median peak P/V 2.32; mean attempts 1.00 |
| R15_uncapped | 41 | bull_trap (g_max = 1.0, rejection sampling): share of runs with peak P/V > 3 | 0.180 | 50 | [0.098, 0.308] | — |  | **D** | topped share 0.86; median peak P/V 2.32; mean attempts 1.00 |
| R15_uncapped | 41 | bull_trap (live cap 0.012, rejection sampling): share of runs with peak P/V > 3 | 0.000 | 50 | [0.000, 0.071] | — |  | **D** | topped share 0.62; median peak P/V 1.92; mean attempts 1.02 |
| R16_iv_step | 46 | calm day-to-day sd of log IV (pooled, crash + bull calm days) | 0.080 | 100 | [0.073, 0.086] | 0.089 | C §A.6 (30+30 seeds); LOG 0.086 | **R** |  |
| R16_iv_step | 46 | mean Δlog IV at deterioration → panic | 0.618 | 50 | [0.591, 0.646] | 0.620 | C §A.6 | **R** | z = +7.74 (×1.85) |
| R16_iv_step | 46 | mean Δlog IV at panic → stabilisation | -0.591 | 50 | [-0.615, -0.566] | -0.640 | C §A.6 | **N** | z = -7.41 (×0.55) |
| R16_iv_step | 46 | mean Δlog IV at calm → deterioration | 0.172 | 50 | [0.158, 0.191] | 0.150 | C §A.6 | **R** | z = +2.16 (×1.19) |
| R16_iv_step | 46 | mean Δlog IV at calm → mania | 0.172 | 50 | [0.157, 0.191] | 0.150 | C §A.6 | **R** | z = +2.16 (×1.19) |
| R16_iv_step | 46 | mean Δlog IV at blow-off → post-top | 0.324 | 31 | [0.303, 0.344] | 0.330 | C §A.6 | **R** | z = +4.05 (×1.38) |
| R17_one_shot | 48 | flat: median oracle target switches per run (ISFJ, θ 0.05) | 0.500 | 50 | [0.000, 2.000] | 0 | C §B.15 (30) / LOG §2 (30) / pass-3 (20) | **R** | share of runs with >= 2 switches 0.28 (Wilson 0.17–0.42; pass-3 0.25); IQR shown as the interval |
| R17_one_shot | 48 | flat: share of resolvable steps at a single band edge (mean over runs) | 0.945 | 50 | [0.913, 0.974] | 0.840 | C §B.15: 77–91 % (flat/crash/bull) | **N** |  |
| R17_one_shot | 48 | crash: median oracle target switches per run (ISFJ, θ 0.05) | 1.000 | 50 | [0.000, 1.750] | 1 | C §B.15 (30) / LOG §2 (30) / pass-3 (20) | **R** | share of runs with >= 2 switches 0.26 (Wilson 0.16–0.40; pass-3 0.45); IQR shown as the interval |
| R17_one_shot | 48 | crash: share of resolvable steps at a single band edge (mean over runs) | 0.864 | 50 | [0.811, 0.912] | 0.840 | C §B.15: 77–91 % (flat/crash/bull) | **R** |  |
| R17_one_shot | 48 | bull_trap: median oracle target switches per run (ISFJ, θ 0.05) | 1.000 | 50 | [1.000, 2.000] | 1 | C §B.15 (30) / LOG §2 (30) / pass-3 (20) | **R** | share of runs with >= 2 switches 0.42 (Wilson 0.29–0.56; pass-3 0.3); IQR shown as the interval |
| R17_one_shot | 48 | bull_trap: share of resolvable steps at a single band edge (mean over runs) | 0.763 | 50 | [0.718, 0.811] | 0.840 | C §B.15: 77–91 % (flat/crash/bull) | **R** |  |
| R17_one_shot | 48 | sustained_bull: median oracle target switches per run (ISFJ, θ 0.05) | 2.000 | 50 | [1.000, 3.000] | 2 | C §B.15 (30) / LOG §2 (30) / pass-3 (20) | **R** | share of runs with >= 2 switches 0.52 (Wilson 0.39–0.65; pass-3 0.55); IQR shown as the interval |
| R17_one_shot | 48 | sustained_bull: share of resolvable steps at a single band edge (mean over runs) | 0.810 | 47 | [0.756, 0.862] | — | C §B.15: 77–91 % (flat/crash/bull) | **D** |  |
| R18_blowoff_top | 49 | bull_trap: un-topped share | 0.380 | 50 | [0.259, 0.518] | 0.580 | C §A.11 (seeds 0-29?) | **N** | blow-off label starts on day 154–171 in un-topped runs (reviewer 153–170) |
| R18_blowoff_top | 49 | topped runs: share whose realised maximum of x falls on top_day + 1 | 0.581 | 31 | [0.408, 0.736] | most | C §A.12 (off by one) | **S** | mean (max x − x_top) = +0.0186 (≈ the mania drift g) |
| R19_burn_in | 50 | fw_single (live): sd of x on day 1 across seeds / long-run sd (200k pilot) | 0.831 | 50 | [0.712, 0.929] | — |  | **D** | sd(x_1) 0.1496; pilot sd 0.1800, pilot half-life 155 d; burn-in 260 d = 1.67 half-lives |
| R19_burn_in | 50 | fw_index: sd of x on day 1 across seeds / long-run sd (200k pilot) | 0.608 | 50 | [0.516, 0.692] | 0.600 | C §A.9 (fw_index ≈ 0.6 σ_stat) | **R** | sd(x_1) 0.2197; pilot sd 0.3616, pilot half-life 628 d; burn-in 260 d = 0.41 half-lives |
| R19_burn_in | 50 | pruna: sd of x on day 1 across seeds / long-run sd (200k pilot) | 0.607 | 50 | [0.515, 0.689] | — |  | **D** | sd(x_1) 0.2184; pilot sd 0.3597, pilot half-life 622 d; burn-in 260 d = 0.42 half-lives |
| R1_start_price_rule | 1 | flat: MCR of the 'compare with 100' rule (PortfolioV2, 5 bp) | 0.018 | 50 | [0.011, 0.027] | 0.014 | C §A.2 (12 seeds) | **R** | oracle 0.003, always-hold 0.106, constant-mix 0.100, edge-lo 0.073, edge-hi 0.130, random 0.338 |
| R1_start_price_rule | 1 | flat: MCR of the rule, direct scoring (no execution) | 0.014 | 50 | [0.007, 0.023] | 0.022 | LOG §1 (12 seeds) | **R** | always-hold direct 0.100 |
| R1_start_price_rule | 1 | crash: MCR of the 'compare with 100' rule (PortfolioV2, 5 bp) | 0.009 | 50 | [0.007, 0.013] | 0.007 | C §A.2 (12 seeds) | **R** | oracle 0.003, always-hold 0.132, constant-mix 0.100, edge-lo 0.037, edge-hi 0.167, random 0.326 |
| R1_start_price_rule | 1 | crash: MCR of the rule, direct scoring (no execution) | 0.006 | 50 | [0.003, 0.009] | 0.011 | LOG §1 (12 seeds) | **R** | always-hold direct 0.100 |
| R1_start_price_rule | 1 | bull_trap: MCR of the 'compare with 100' rule (PortfolioV2, 5 bp) | 0.010 | 50 | [0.007, 0.013] | 0.005 | C §A.2 (12 seeds) | **R** | oracle 0.004, always-hold 0.140, constant-mix 0.101, edge-lo 0.126, edge-hi 0.078, random 0.353 |
| R1_start_price_rule | 1 | bull_trap: MCR of the rule, direct scoring (no execution) | 0.006 | 50 | [0.003, 0.009] | 0.007 | LOG §1 (12 seeds) | **R** | always-hold direct 0.100 |
| R1_start_price_rule | 1 | sustained_bull: MCR of the 'compare with 100' rule (PortfolioV2, 5 bp) | 0.110 | 50 | [0.089, 0.129] | 0.098 | C §A.2 (12 seeds) | **R** | oracle 0.002, always-hold 0.101, constant-mix 0.102, edge-lo 0.080, edge-hi 0.126, random 0.332 |
| R1_start_price_rule | 1 | sustained_bull: MCR of the rule, direct scoring (no execution) | 0.107 | 50 | [0.086, 0.127] | 0.083 | LOG §1 (12 seeds) | **R** | always-hold direct 0.100 |
| R1_start_price_rule | 1 | substance: rule within 0.02 of the oracle in flat/crash/bull and > 0.05 above it in sustained bull | yes | 200 | — | yes | C §A.2 / W 1 | **S** | gaps flat +0.015, crash +0.006, bull_trap +0.006, sustained_bull +0.108 |
| R20_multi_asset | 58 | 3-asset crash: mean pairwise correlation of x across assets | 0.546 | 50 | [0.456, 0.632] | 0.550 | C §G.41: 0.46–0.65 (10 seeds) | **R** | min/max over pairs of the seed means: -0.21–0.93 |
| R20_multi_asset | 58 | 3-asset crash: spread-resolvable share (max x − min x >= 0.05) | 0.866 | 50 | [0.842, 0.889] | 0.870 | C §G.41 | **R** |  |
| R20_multi_asset | 58 | 3-asset crash: mean IV / realised-21-day-vol ratio, asset 0 | 1.328 | 50 | [1.282, 1.375] | 1.280 | C §G.41 (10 seeds) | **R** |  |
| R20_multi_asset | 58 | 3-asset crash: mean IV / realised-21-day-vol ratio, asset 2 | 1.412 | 50 | [1.359, 1.464] | 1.060 | C §G.41 (10 seeds) | **N** |  |
| R21_footers | 39 | checklist_v2: CSV pass/fail vs .md footer | CSV 8/7; footer 8/7 | 20 | — | footer 8/7 | W 39 / LOG §5 | **R** | footer correct |
| R21_footers | 39 | checklist_v2_sens_fw_index: CSV pass/fail vs .md footer | CSV 8/7; footer 7/6 | 20 | — | footer 7/6 | W 39 / LOG §5 | **R** | footer wrong |
| R21_footers | 39 | checklist_v2_sens_pruna: CSV pass/fail vs .md footer | CSV 7/8; footer 6/7 | 20 | — | footer 6/7 | W 39 / LOG §5 | **R** | footer wrong |
| R21_footers | 39 | checklist_v2_sens_hl60: CSV pass/fail vs .md footer | CSV 7/8; footer 7/8 | 20 | — | footer 7/8 | W 39 / LOG §5 | **R** | footer correct |
| R21_footers | 39 | checklist_v2_sens_omega_mode: CSV pass/fail vs .md footer | CSV 7/8; footer 6/7 | 20 | — | footer 6/7 | W 39 / LOG §5 | **R** | footer wrong |
| R21_footers | 39 | checklist_v2_sens_panic3: CSV pass/fail vs .md footer | CSV 9/6; footer 8/5 | 20 | — | footer 8/5 | W 39 / LOG §5 | **R** | footer wrong |
| R21_footers | 39 | checklist_v2_sens_panic6: CSV pass/fail vs .md footer | CSV 8/7; footer 7/6 | 20 | — | footer 7/6 | W 39 / LOG §5 | **R** | footer wrong |
| R22_n_table | 30 | checklist item 4: n behind the published statistic | 20 | 20 | — | '50 seeds per scenario' | slide 2 / script | **D** | Decay of ACF|r| (Cont 8) |
| R22_n_table | 30 | checklist item 9: n behind the published statistic | 20 | 20 | — | '50 seeds per scenario' | slide 2 / script | **D** | Mispricing persistence (FW regime) |
| R22_n_table | 30 | checklist item 14: n behind the published statistic | 0 | 0 | — | '50 seeds per scenario' | slide 2 / script | **D** | Value leak |
| R22_n_table | 30 | checklist item 16: n behind the published statistic | 0 | 0 | — | '50 seeds per scenario' | slide 2 / script | **D** | Composite phase clock |
| R22_n_table | 30 | checklist item 18: n behind the published statistic | 0 | 0 | — | '50 seeds per scenario' | slide 2 / script | **D** | Start design applied |
| R22_n_table | 30 | checklist item 19: n behind the published statistic | 0 | 0 | — | '50 seeds per scenario' | slide 2 / script | **D** | Action-space reachability |
| R22_n_table | 30 | hazard calibration seeds | 60 | 60 | — | '50 seeds' |  | **D** |  |
| R22_n_table | 30 | leakage audit (50 seeds -> 400 paths -> MAX_ROWS subsample): steps audited | 30000 | 0 | — | '50 seeds' | leakage_audit_v2.md | **D** | 150 of 400 paths (evaluation/leakage_audit.py MAX_ROWS = 30000); L2 rows after lag dropping: 27,000 |
| R22_n_table | 30 | L5 observables oracle: training / evaluation seeds | 12 / 10 | 10 | — | '50 seeds' | l5_observables_oracle.md | **D** |  |
| R22_n_table | 30 | generator sensitivities: seeds per scenario | 25 | 25 | — | '50 seeds' | checklist_v2_sens_*.md preambles | **D** |  |
| R22_n_table | 44 | pilot scenarios | flat, bull_trap, crash δ 0.70 (3) | 48 | — | 'the four scenarios' (script slide 26) | PILOT_NOTES.md | **D** |  |
| R23_stale_statements | 71 | stale statements found (file:line list in the JSON detail and the report) | 21 | 21 | — | — | W 71, 72 | **D** |  |
| R2_fw_inert | 2 | flat: share of days with n_f > 0.99 | 0.985 | 50 | [0.978, 0.990] | 0.983 | C §A.1 (10 seeds) | **R** | mean n_f 0.9984 |
| R2_fw_inert | 2 | crash: share of days with n_f > 0.99 | 0.990 | 50 | [0.985, 0.994] | 0.987 | C §A.1 (10 seeds) | **R** | mean n_f 0.9989 |
| R2_fw_inert | 2 | bull_trap: share of days with n_f > 0.99 | 0.991 | 50 | [0.987, 0.994] | 0.991 | C §A.1 (10 seeds) | **R** | mean n_f 0.9990 |
| R2_fw_inert | 2 | pilot n̄ at price_scale 100, index set (20,000 steps, seed 12345) | 0.999 | 1 | — | 0.999 | LOG §1 | **R** | live engine (phi 0.463) n̄ 0.9976 |
| R2_fw_inert | 2 | pilot n̄ at price_scale 1, index set (20,000 steps, seed 12345) | 0.827 | 1 | — | 0.827 | LOG §1 / C (0.83) | **R** | chartist share 0.173; SABCEMM DCA-HPM 0.2285 (simulated, own noise) |
| R3_attackers | 3 | random_start / level / calm: R2_x | 0.054 | 200 | [-0.135, 0.179] | 0.217 | C §A.3 price-only calm R2 (24 seeds) | **R** |  |
| R3_attackers | 3 | random_start / level / calm: sign_acc | 0.714 | 200 | [0.653, 0.770] | 0.768 | C §A.3 | **R** |  |
| R3_attackers | 3 | random_start / level / event: R2_x | 0.634 | 200 | [0.565, 0.693] | 0.730 | C §A.3 | **R** |  |
| R3_attackers | 3 | random_start / level / all: MAPE_V | 0.112 | 200 | [0.102, 0.123] | 0.153 | C §A.3 MAPE(V) price-only | **N** |  |
| R3_attackers | 3 | random_start / full / calm: R2_x | 0.653 | 200 | [0.570, 0.722] | 0.779 | C §A.3 full calm R2 | **R** |  |
| R3_attackers | 3 | random_start / full / calm: sign_acc | 0.851 | 200 | [0.807, 0.891] | 0.862 | C §A.3 | **R** |  |
| R3_attackers | 3 | random_start / full / event: R2_x | 0.904 | 200 | [0.884, 0.921] | 0.904 | C §A.3 | **R** |  |
| R3_attackers | 3 | random_start / full / all: MAPE_V | 0.077 | 200 | [0.071, 0.083] | 0.101 | C §A.3 MAPE(V) full | **N** |  |
| R3_attackers | 5 | anchored / level / all: R2_x | 0.849 | 200 | [0.824, 0.871] | 0.840 | C §A.2 level features (OOS R2) | **R** |  |
| R3_attackers | 5 | anchored / level / all: sign_acc | 0.948 | 200 | [0.932, 0.962] | 0.945 | C §A.2 | **R** |  |
| R3_attackers | 5 | anchored / level_free / all: R2_x | 0.493 | 200 | [0.431, 0.549] | 0.400 | C §A.2 level-free | **R** |  |
| R3_attackers | 43 | anchored / level_free / all: sign_acc | 0.736 | 200 | [0.701, 0.774] | 0.710 | C §A.2 level-free sign acc on resolvable steps | **R** |  |
| R3_attackers | 5 | anchored / full / calm: R2_x | 0.814 | 200 | [0.771, 0.843] | 0.898 | leakage_audit_v2.md (150 paths) | **N** |  |
| R3_attackers | 5 | anchored / level / calm: R2_x | 0.721 | 200 | [0.660, 0.766] | 0.787 | leakage_audit_v2.md price-only calm | **R** |  |
| R3_attackers | 5 | anchored / full / calm: MAPE_V | 0.042 | 200 | [0.039, 0.045] | 0.035 | leakage_audit_v2.md MAPE(V) calm | **N** |  |
| R3_attackers | 5 | anchored / full / event: MAPE_V | 0.063 | 200 | [0.058, 0.070] | 0.049 | leakage_audit_v2.md MAPE(V) event | **N** |  |
| R3_attackers | 3 | substance: selectivity of the non-price fields (full − level, calm R2) is small when anchored and large when the start is randomised | anchored +0.093; random-start +0.599 | 200 | — | +0.11 anchored vs +0.56 randomised | C §A.3 / W 3 | **S** |  |
| R3_attackers | 43 | substance: level-free attacker far below the level attacker on the anchored panel (R2 and sign) | level 0.849 / 0.948; level-free 0.493 / 0.736 | 200 | — | 0.84 / 0.945 vs 0.40 / 0.71 | C §A.2 / W 43 | **S** |  |
| R4_flat_bias | 4 | flat: mean x (mean of path means) | -0.068 | 50 | [-0.107, -0.029] | -0.100 | C §A.4 (30 seeds); LOG −0.077 (SE 0.019) | **R** |  |
| R4_flat_bias | 4 | flat: pooled median x | -0.058 | 50 | [-0.113, -0.012] | -0.068 | C §A.4 | **R** |  |
| R4_flat_bias | 4 | flat: P(x < 0) | 0.632 | 50 | [0.522, 0.739] | 0.700 | C §A.4 | **R** |  |
| R4_flat_bias | 4 | flat: mean x on day 1 | -0.068 | 50 | [-0.109, -0.028] | -0.076 | C §A.4 | **R** |  |
| R4_flat_bias | 4 | flat: share of resolvable steps (|x| >= 0.05) that are undervalued | 0.666 | 50 | [0.538, 0.785] | 0.740 | C §A.4 | **R** |  |
| R4_flat_bias | 4 | crash δ 0.70: share of resolvable steps undervalued | 0.839 | 50 | [0.768, 0.901] | 0.840 | C §A.4 | **R** |  |
| R4_flat_bias | 4 | flat, jumps off: mean x | 0.009 | 50 | [-0.026, 0.044] | -0.018 | C §A.4; LOG +0.009 | **R** |  |
| R4_flat_bias | 4 | flat, jumps off: P(x < 0) | 0.466 | 50 | [0.364, 0.576] | 0.500 | C §A.4; LOG 0.46 | **R** |  |
| R4_flat_bias | 4 | analytic stationary mean −(rate × mean jump)/(μ n̄ φ) | -0.087 | 0 | — | -0.087 | LOG §1 | **R** | pull rate 0.00462/day; rate 0.010, mean −0.04 (code) |
| R5_L1_candidates | 5 | L1 median APE: k * P (price itself) | 0.094 | 200 | [0.076, 0.113] | 0.124 | leakage_audit_v2.md (150 paths) | **N** | p5 0.006, p10 0.011, p25 0.028; within 1/2/5 %: 0.09/0.18/0.37 |
| R5_L1_candidates | 5 | L1 median APE: k * P / reported_PE | 0.131 | 200 | [0.120, 0.144] | 0.155 | leakage_audit_v2.md (150 paths) | **N** | p5 0.014, p10 0.026, p25 0.065; within 1/2/5 %: 0.04/0.08/0.19 |
| R5_L1_candidates | 5 | L1 median APE: k * P * dividend_yield | 0.130 | 200 | [0.115, 0.144] | 0.156 | leakage_audit_v2.md (150 paths) | **N** | p5 0.012, p10 0.026, p25 0.066; within 1/2/5 %: 0.04/0.08/0.18 |
| R5_L1_candidates | 5 | L1 median APE: k * analyst_fair_value | 0.240 | 200 | [0.224, 0.258] | 0.224 | leakage_audit_v2.md (150 paths) | **R** | p5 0.021, p10 0.043, p25 0.116; within 1/2/5 %: 0.02/0.05/0.11 |
| R5_L1_candidates | 5 | L1 median APE: k * SMA50 | 0.093 | 200 | [0.071, 0.108] | — |  | **D** | p5 0.005, p10 0.011, p25 0.027; within 1/2/5 %: 0.10/0.19/0.38 |
| R5_L1_candidates | 5 | L1 median APE: mean(k*SMA50, k*P/PE, k*analyst) | 0.107 | 200 | [0.099, 0.117] | 0.092 | B row 5 (64 paths): 9.2 %, 27 % within 5 % | **R** | p5 0.010, p10 0.021, p25 0.051; within 1/2/5 %: 0.05/0.10/0.24 |
| R5_L1_candidates | 5 | substance: the best single candidate is price itself (median APE = median |x|), and a three-term mean beats it | price 0.094 vs three-term 0.107 | 200 | — | 0.124 vs 0.092 | B rows 3, 5 | **N** |  |
| R6_calendar_clock | 6 | crash setup-first: P(calm | day <= 50) | 1.000 | 50 | [0.998, 1.000] | 1.000 | C §C.20 (40 seeds) | **R** | 2500 path-days |
| R6_calendar_clock | 6 | crash setup-first: P(event | day >= 170) | 1.000 | 50 | [0.998, 1.000] | 1.000 | C §C.20 | **R** | 1550 path-days |
| R6_calendar_clock | 6 | crash setup-first: day-only macro-phase accuracy (within scenario) | 0.828 | 50 | [0.792, 0.848] | 0.804 | C §C.20 (40 seeds) | **R** | majority class 0.400 (reviewer 0.40); bootstrap 60 resamples |
| R6_calendar_clock | 6 | bull_trap setup-first: P(calm | day <= 50) | 1.000 | 50 | [0.998, 1.000] | 1.000 | C §C.20 (40 seeds) | **R** | 2500 path-days |
| R6_calendar_clock | 6 | bull_trap setup-first: P(event | day >= 170) | 1.000 | 50 | [0.998, 1.000] | 1.000 | C §C.20 | **R** | 1550 path-days |
| R6_calendar_clock | 6 | bull_trap setup-first: day-only macro-phase accuracy (within scenario) | 0.809 | 50 | [0.781, 0.846] | 0.872 | C §C.20 (40 seeds) | **N** | majority class 0.492 (reviewer 0.54); bootstrap 60 resamples |
| R6_calendar_clock | 6 | mixed set (event-first + setup-first + flat): day-only macro accuracy (checklist item 15 statistic) | 0.535 | 150 | — | 0.648 | checklist_v2.md (470 paths) | **N** | macro-phase accuracy from day alone = 53.5% (mixed set, 150 paths; within-scenario mean 53.5%); |corr(day, phase id)| = 0.47 |
| R7_jumps_kurtosis | 13 | flat, current jumps (N(−0.04, 0.03), rate 0.010): share of paths with excess kurtosis > 1.5 | 0.780 | 50 | [0.648, 0.872] | 0.850 | LOG §2 (40 seeds); pass-3 review 0.70/0.55/0.45 | **R** | median kurtosis 3.46; mean x -0.068 |
| R7_jumps_kurtosis | 13 | flat, mean-zero jumps: share of paths with excess kurtosis > 1.5 | 0.700 | 50 | [0.562, 0.809] | 0.700 | LOG §2 (40 seeds); pass-3 review 0.70/0.55/0.45 | **R** | median kurtosis 2.28; mean x +0.012 |
| R7_jumps_kurtosis | 13 | flat, no jumps: share of paths with excess kurtosis > 1.5 | 0.680 | 50 | [0.542, 0.792] | 0.600 | LOG §2 (40 seeds); pass-3 review 0.70/0.55/0.45 | **R** | median kurtosis 2.17; mean x +0.009 |
| R8_script_share | 16 | crash panic: script share R² of Δx on the scripted drift d_t | 0.063 | 50 | [0.052, 0.073] | — | not quantified by the reviews (W 16 asks for it) | **D** | var(d)/var(Δx) = 0.058 |
| R8_script_share | 16 | crash stabilisation: script share R² of Δx on the scripted drift d_t | 0.028 | 50 | [-0.006, 0.060] | — | not quantified by the reviews (W 16 asks for it) | **D** | var(d)/var(Δx) = 0.063 |
| R8_script_share | 16 | bull post-top: script share R² of Δx on the scripted drift d_t | 0.207 | 50 | [0.132, 0.330] | — | not quantified by the reviews (W 16 asks for it) | **D** | var(d)/var(Δx) = 0.187 |
| R8_script_share | 16 | bull mania: script share R² of Δx on the scripted drift d_t | 0.009 | 50 | [-0.002, 0.022] | — | not quantified by the reviews (W 16 asks for it) | **D** | var(d)/var(Δx) = 0.040 |
| R8_script_share | 47 | bull_trap: share of mania days at the drift cap g_max | 0.372 | 50 | [0.325, 0.416] | 0.380 | C §A.8 (seeds 0-29) | **R** |  |
| R8_script_share | 16 | FW pull per day at x = −0.30: live φ (0.463) / index φ (0.12) | 0.00139 / 0.00036 | 0 | — | 0.00034 (index φ) | C §A.8 | **R** | median scripted panic step |d_t| = 0.0075/day |
| R9_sb_selection | 18 | sustained_bull first attempts: accepted / rejected | 34 / 16 | 50 | [0.208, 0.458] | 33 / 27 (C), 32 / 18 (LOG) | C §A.5, LOG §1 | **R** | rejected share 0.32; interval = Wilson 95 % for the rejected share (reviewer 0.45 / LOG 0.36) |
| R9_sb_selection | 18 | sd: accepted | 0.015 | 34 | [0.014, 0.015] | 0.015 | C §A.5 daily sd | **R** | rejected 0.0235 [0.0197, 0.0280] (n 16); flat 0.0162 [0.0149, 0.0176] |
| R9_sb_selection | 18 | sd: rejected | 0.024 | 16 | [0.020, 0.028] | 0.024 | C §A.5 daily sd | **R** |  |
| R9_sb_selection | 18 | acf1: accepted | -0.031 | 34 | [-0.057, -0.005] | -0.025 | C §A.5 ACF1 (accepted vs flat +0.024) | **R** | rejected 0.0247 [-0.0179, 0.0690] (n 16); flat 0.0071 [-0.0161, 0.0303] |
| R9_sb_selection | 18 | sd20: accepted | 0.041 | 34 | [0.039, 0.043] | 0.044 | C §A.5 20-day return sd (accepted vs flat 0.080) | **R** | rejected 0.0695 [0.0610, 0.0784] (n 16); flat 0.0694 [0.0634, 0.0765] |
| R9_sb_selection | 42 | sustained_bull rejection rate under rejection sampling (rejections / attempts) | 0.405 | 50 | [0.306, 0.512] | 0.398 | checklist_v2.md item 17 (50 seeds); LOG 0.36 | **R** | mean attempts 1.68 |
| R9_sb_selection | 42 | substance: accepted paths are quieter than rejected ones (daily sd) and than flat | yes | 34 | — | yes | C §A.5 / W 42 | **S** | 0.0146 vs 0.0235; relative difference 37.82% |

## Before / after the analyst-error fix (same seeds; only the analyst field changed)

| Block | Statistic | Before | After |
|---|---|---|---|
| R10_analyst | pooled sd(u), full 460-day timeline | 0.335 | 0.156 |
| R10_analyst | pooled sd(u), benchmark days | 0.352 | 0.158 |
| R10_analyst | median |u|, benchmark days | 0.247 | 0.111 |
| R10_analyst | documented stationary sd | 0.150 | 0.150 |
| R10_analyst | crash δ 0.70 envs: pooled sd(u) on benchmark days | 0.339 | 0.151 |
| R10_analyst | median |F/V − 1| of the analyst field (all four scenarios) | 0.245 | 0.112 |
| R3_attackers | random_start / level / calm: R2_x | 0.054 | 0.054 |
| R3_attackers | random_start / level / calm: sign_acc | 0.714 | 0.714 |
| R3_attackers | random_start / level / event: R2_x | 0.634 | 0.634 |
| R3_attackers | random_start / level / all: MAPE_V | 0.112 | 0.112 |
| R3_attackers | random_start / full / calm: R2_x | 0.653 | 0.676 |
| R3_attackers | random_start / full / calm: sign_acc | 0.851 | 0.865 |
| R3_attackers | random_start / full / event: R2_x | 0.904 | 0.910 |
| R3_attackers | random_start / full / all: MAPE_V | 0.077 | 0.071 |
| R3_attackers | anchored / level / all: R2_x | 0.849 | 0.849 |
| R3_attackers | anchored / level / all: sign_acc | 0.948 | 0.948 |
| R3_attackers | anchored / level_free / all: R2_x | 0.493 | 0.493 |
| R3_attackers | anchored / level_free / all: sign_acc | 0.736 | 0.736 |
| R3_attackers | anchored / full / calm: R2_x | 0.814 | 0.841 |
| R3_attackers | anchored / level / calm: R2_x | 0.721 | 0.721 |
| R3_attackers | anchored / full / calm: MAPE_V | 0.042 | 0.039 |
| R3_attackers | anchored / full / event: MAPE_V | 0.063 | 0.059 |
| R3_attackers | substance: selectivity of the non-price fields (full − level, calm R2) is small when anchored and large when the start is randomised | anchored +0.093; random-start +0.599 | anchored +0.120; random-start +0.623 |
| R3_attackers | substance: level-free attacker far below the level attacker on the anchored panel (R2 and sign) | level 0.849 / 0.948; level-free 0.493 / 0.736 | level 0.849 / 0.948; level-free 0.493 / 0.736 |
| R5_L1_candidates | L1 median APE: k * P (price itself) | 0.094 | 0.094 |
| R5_L1_candidates | L1 median APE: k * P / reported_PE | 0.131 | 0.131 |
| R5_L1_candidates | L1 median APE: k * P * dividend_yield | 0.130 | 0.130 |
| R5_L1_candidates | L1 median APE: k * analyst_fair_value | 0.240 | 0.110 |
| R5_L1_candidates | L1 median APE: k * SMA50 | 0.093 | 0.093 |
| R5_L1_candidates | L1 median APE: mean(k*SMA50, k*P/PE, k*analyst) | 0.107 | 0.071 |
| R5_L1_candidates | substance: the best single candidate is price itself (median APE = median |x|), and a three-term mean beats it | price 0.094 vs three-term 0.107 | price 0.094 vs three-term 0.071 |

## Pure AR(1) estimator table (200 Gaussian paths per cell; sample half-life from ACF(1))

| true half-life | T | median | 5–95 % | share >= 60 d |
|---|---|---|---|---|
| 60 | 200 | 18 | 8–39 | 0.01 |
| 60 | 800 | 40 | 20–71 | 0.12 |
| 60 | 2000 | 49 | 30–80 | 0.24 |
| 60 | 5000 | 58 | 44–79 | 0.42 |
| 150 | 200 | 20 | 7–48 | 0.01 |
| 150 | 800 | 59 | 29–142 | 0.49 |
| 150 | 2000 | 96 | 57–202 | 0.93 |
| 150 | 5000 | 124 | 81–206 | 0.99 |
| 580 | 200 | 22 | 9–57 | 0.04 |
| 580 | 800 | 84 | 35–217 | 0.69 |
| 580 | 2000 | 180 | 73–429 | 0.97 |
| 580 | 5000 | 318 | 145–732 | 1.00 |

## Stale statements located (items 71, 72, 44)

| File | Line | What | Text |
|---|---|---|---|
| docs/env_v2/spec/E1_V2_GENERATOR_SPEC.md | 31 | realised half-life 72/70 d | STATIONARY design value; the REALISED half-life on T=800 paths with GARCH-t + jump noise is ~72 d (item 9) **[calib: |
| docs/env_v2/spec/E1_V2_GENERATOR_SPEC.md | 74 | sustained-bull multiplier 0.25 | sustained-bull 0.25) scale the WHOLE conditional variance (`scale_mode="variance"`, regime-switching variance) rather |
| docs/env_v2/spec/CALIBRATION_REPORT.md | 9 | sustained-bull multiplier 0.25 | - GJR-GARCH-t: alpha 0.1, gamma 0.1, beta 0.83 (persistence 0.980), sbar 0.017, df 5.0, panic multiplier 5.0, scale_mode variance; phase multipliers {'calm': 1. |
| docs/env_v2/decisions/DECISION_LOG.md | 11 | half-life 60–120 d | \| 2 \| Mispricing engine \| **FW functional form, parameters re-estimated on single stocks (SMM); index parameters as sensitivity; AR(1) behind a flag** \| Index p |
| docs/env_v2/decisions/DECISION_LOG.md | 29 | realised half-life 72/70 d | ~150-day stationary / ~70-day realised half-life) remains in force and is reported as a design choice. The empirical |
| docs/env_v2/decisions/DECISION_LOG.md | 47 | half-life 60–120 d | \| FW calm half-life (fallback phi) \| 60-120 d window \| 120 d (phi = 0.579 at the realised fundamentalist share n_bar = 0.997) \| sample ACF(1) of x must clear 0. |
| docs/env_v2/decisions/DECISION_LOG.md | 47 | half-life 120 d | \| FW calm half-life (fallback phi) \| 60-120 d window \| 120 d (phi = 0.579 at the realised fundamentalist share n_bar = 0.997) \| sample ACF(1) of x must clear 0. |
| docs/env_v2/decisions/DECISION_LOG.md | 53 | jump rate 0.008 | \| Rare jumps \| optional, 0.004/day, N(-4%, 3%) \| on, 0.008/day, N(-4%, 3%) \| item 2 (kurtosis share) and item 8 \| |
| docs/env_v2/decisions/DECISION_LOG.md | 136 | half-life 120 d | \| R1-D8: reconcile half-life numbers (spec 120 d vs log 150 d vs realised 72 d) and the jump rate (0.008 vs 0.010); SMM non-identification asserted, not shown \| |
| docs/env_v2/decisions/DECISION_LOG.md | 136 | realised half-life 72/70 d | \| R1-D8: reconcile half-life numbers (spec 120 d vs log 150 d vs realised 72 d) and the jump rate (0.008 vs 0.010); SMM non-identification asserted, not shown \| |
| docs/env_v2/generated/e1_calibration_variants.md | 3 | jump rate 0.008 | Generated from the quick-iteration runs during E1 (scratchpad quick_items.py). Final defaults = variant E (df 5, alpha/gamma/beta 0.10/0.10/0.83, panic_mult 5,  |
| docs/env_v2/generated/e1_calibration_variants.md | 34 | jump rate 0.008 | === C_garch_jumps  cfg={'garch': {'alpha': 0.08, 'gamma': 0.1, 'beta': 0.85}, 'jump_rate': 0.008}  (28s) |
| docs/env_v2/generated/e1_calibration_variants.md | 48 | jump rate 0.008 | === D_jumps  cfg={'jump_rate': 0.008}  (28s) |
| docs/env_v2/generated/e1_calibration_variants.md | 62 | jump rate 0.008 | === E  cfg={'garch': {'alpha': 0.1, 'gamma': 0.1, 'beta': 0.83, 'df': 5, 'panic_mult': 5}, 'jump_rate': 0.008}  (22s) |
| docs/env_v2/generated/e1_calibration_variants.md | 90 | jump rate 0.008 | === G  cfg={'garch': {'alpha': 0.12, 'gamma': 0.12, 'beta': 0.8, 'df': 4, 'panic_mult': 5}, 'jump_rate': 0.008}  (22s) |
| docs/env_v2/generated/e1_calibration_variants.md | 104 | jump rate 0.008 | === H  cfg={'garch': {'alpha': 0.1, 'gamma': 0.1, 'beta': 0.83, 'df': 5, 'panic_mult': 5}, 'jump_rate': 0.008, 'lam_panic': 0.25}  (22s) |
| envs/v2/mispricing.py | 95 | half-life ~90 d | half-life ~90 d) at the REALISED fundamentalist share n_bar (fixed point of |
| docs/env_v2/slides/SPEAKER_SCRIPT.md | 87 | realised half-life 72/70 d | **Where the numbers come from.** The persistence of mispricing is described as a half life, which is the number of days it takes for a gap between price and val |
| docs/env_v2/slides/SPEAKER_SCRIPT.md | 328 | four scenarios | **What this is in one line.** A small end to end run with one model, Gemini 2.5 Flash, one seed, 200 days, and 48 runs covering the three personas, four arms an |
| tools/build_slides.py | 519 | realised half-life 72/70 d | "Persistence: stationary half-life ≈ 150 days (≈ 70 days realised), a stated design value", |
| tools/build_slides.py | 670 | realised half-life 72/70 d | ["Mispricing half-life", "0 days", "72 days", "≥ 60 days", P], |

## Attacker table (GBT, GroupKFold by path; 200 paths per panel)

| Panel | Features | Group | R²(x) [CI] | sign acc [CI] | MAPE(V) [CI] | rows |
|---|---|---|---|---|---|---|
| anchored | level (51) | calm | 0.721 [0.660, 0.766] | 0.937 [0.914, 0.959] | 0.049 [0.045, 0.053] | 23995 |
| anchored | level (51) | event | 0.888 [0.854, 0.913] | 0.953 [0.935, 0.970] | 0.080 [0.071, 0.091] | 8501 |
| anchored | level (51) | all | 0.849 [0.824, 0.871] | 0.948 [0.932, 0.962] | 0.058 [0.054, 0.063] | 36000 |
| anchored | level_free (45) | calm | 0.140 [0.043, 0.216] | 0.655 [0.596, 0.716] | 0.084 [0.080, 0.090] | 23995 |
| anchored | level_free (45) | event | 0.637 [0.568, 0.690] | 0.825 [0.783, 0.860] | 0.087 [0.076, 0.097] | 8501 |
| anchored | level_free (45) | all | 0.493 [0.431, 0.549] | 0.736 [0.701, 0.774] | 0.094 [0.088, 0.100] | 36000 |
| anchored | full (111) | calm | 0.814 [0.771, 0.843] | 0.940 [0.915, 0.960] | 0.042 [0.039, 0.045] | 23995 |
| anchored | full (111) | event | 0.939 [0.925, 0.949] | 0.965 [0.951, 0.976] | 0.063 [0.058, 0.070] | 8501 |
| anchored | full (111) | all | 0.907 [0.889, 0.921] | 0.954 [0.940, 0.966] | 0.048 [0.045, 0.051] | 36000 |
| random_start | level (51) | calm | 0.054 [-0.135, 0.179] | 0.714 [0.653, 0.770] | 0.096 [0.085, 0.108] | 23995 |
| random_start | level (51) | event | 0.634 [0.565, 0.693] | 0.843 [0.797, 0.881] | 0.148 [0.130, 0.167] | 8501 |
| random_start | level (51) | all | 0.474 [0.392, 0.540] | 0.778 [0.739, 0.812] | 0.112 [0.102, 0.123] | 36000 |
| random_start | level_free (45) | calm | 0.143 [0.046, 0.218] | 0.657 [0.598, 0.717] | 1.079 [0.843, 1.383] | 23995 |
| random_start | level_free (45) | event | 0.638 [0.570, 0.691] | 0.829 [0.788, 0.863] | 0.796 [0.577, 1.056] | 8501 |
| random_start | level_free (45) | all | 0.495 [0.433, 0.552] | 0.738 [0.704, 0.775] | 0.986 [0.787, 1.209] | 36000 |
| random_start | full (111) | calm | 0.653 [0.570, 0.722] | 0.851 [0.807, 0.891] | 0.071 [0.065, 0.079] | 23995 |
| random_start | full (111) | event | 0.904 [0.884, 0.921] | 0.929 [0.906, 0.951] | 0.095 [0.086, 0.105] | 8501 |
| random_start | full (111) | all | 0.839 [0.808, 0.864] | 0.890 [0.865, 0.916] | 0.077 [0.071, 0.083] | 36000 |

After the analyst fix (full feature set only changes):

| Panel | Features | Group | R²(x) | sign acc | MAPE(V) |
|---|---|---|---|---|---|
| anchored | level | calm | 0.721 | 0.937 | 0.049 |
| anchored | level | event | 0.888 | 0.953 | 0.080 |
| anchored | level | all | 0.849 | 0.948 | 0.058 |
| anchored | level_free | calm | 0.140 | 0.655 | 0.084 |
| anchored | level_free | event | 0.637 | 0.825 | 0.087 |
| anchored | level_free | all | 0.493 | 0.736 | 0.094 |
| anchored | full | calm | 0.841 | 0.951 | 0.039 |
| anchored | full | event | 0.947 | 0.971 | 0.059 |
| anchored | full | all | 0.920 | 0.963 | 0.045 |
| random_start | level | calm | 0.054 | 0.714 | 0.096 |
| random_start | level | event | 0.634 | 0.843 | 0.148 |
| random_start | level | all | 0.474 | 0.778 | 0.112 |
| random_start | level_free | calm | 0.143 | 0.657 | 1.079 |
| random_start | level_free | event | 0.638 | 0.829 | 0.796 |
| random_start | level_free | all | 0.495 | 0.738 | 0.986 |
| random_start | full | calm | 0.676 | 0.865 | 0.067 |
| random_start | full | event | 0.910 | 0.931 | 0.083 |
| random_start | full | all | 0.851 | 0.900 | 0.071 |
