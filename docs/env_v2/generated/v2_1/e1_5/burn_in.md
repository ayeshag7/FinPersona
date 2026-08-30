# E1.5 burn-in (PREREG_PHASE_1.md section 6; REG-17)

Reference = (x, sigma^2, n_f) on benchmark day 5000 of 2000 flat paths (seeds 80000-81999) per engine; options: the current 260-day burn-in, A = >= 5 half-lives ({'fw_fallback_hl150': 750, 'fw_hl60': 300, 'fw_index': 3140, 'pruna': 3110, 'ar1': 750}), B = stored long-run state + 60-day warm-up. Two-sample KS per variable with a 1000-resample bootstrap upper limit; pass = every upper limit < 0.1.

| engine | option | burn-in | KS x (upper) | KS sigma^2 (upper) | KS n_f (upper) | sd(x_1)/sd(x_ref) | pass |
|---|---|---|---|---|---|---|---|
| fw_fallback_hl150 | current_260 | 260 (long) | 0.047 (0.077) | 0.026 (0.058) | 0.012 (0.026) | 0.568 | True |
| fw_fallback_hl150 | A_long_750 | 750 (long) | 0.017 (0.050) | 0.036 (0.067) | 0.012 (0.027) | 0.573 | True |
| fw_fallback_hl150 | B_stored_60 | 60 (stored) | 0.023 (0.059) | 0.033 (0.064) | 0.014 (0.030) | 0.828 | True |
| fw_hl60 | current_260 | 260 (long) | 0.046 (0.078) | 0.026 (0.058) | 0.007 (0.027) | 0.506 | True |
| fw_hl60 | A_long_300 | 300 (long) | 0.042 (0.070) | 0.022 (0.057) | 0.021 (0.041) | 0.495 | True |
| fw_hl60 | B_stored_60 | 60 (stored) | 0.023 (0.057) | 0.033 (0.064) | 0.010 (0.030) | 0.666 | True |
| fw_index | current_260 | 260 (long) | 0.172 (0.197) | 0.026 (0.058) | 0.024 (0.036) | 0.513 | False |
| fw_index | A_long_3140 | 3140 (long) | 0.024 (0.056) | 0.022 (0.054) | 0.004 (0.014) | 0.824 | True |
| fw_index | B_stored_60 | 60 (stored) | 0.031 (0.067) | 0.033 (0.064) | 0.009 (0.019) | 0.977 | True |
| pruna | current_260 | 260 (long) | 0.170 (0.194) | 0.026 (0.058) | 0.017 (0.027) | 0.516 | False |
| pruna | A_long_3110 | 3110 (long) | 0.028 (0.062) | 0.020 (0.055) | 0.010 (0.018) | 0.826 | True |
| pruna | B_stored_60 | 60 (stored) | 0.031 (0.067) | 0.033 (0.064) | 0.008 (0.018) | 0.976 | True |
| ar1 | current_260 | 260 (long) | 0.052 (0.082) | 0.026 (0.058) | 0.000 (0.000) | 0.563 | True |
| ar1 | A_long_750 | 750 (long) | 0.018 (0.051) | 0.036 (0.067) | 0.000 (0.000) | 0.572 | True |
| ar1 | B_stored_60 | 60 (stored) | 0.023 (0.056) | 0.033 (0.064) | 0.000 (0.000) | 0.828 | True |

Decision (REG-17): fw_fallback_hl150: A (750 d) -- both pass: A for the default engine (no artefact), B for the slow sensitivities; fw_hl60: B (60 d) -- both pass: A for the default engine (no artefact), B for the slow sensitivities; fw_index: B (60 d) -- both pass: A for the default engine (no artefact), B for the slow sensitivities; pruna: B (60 d) -- both pass: A for the default engine (no artefact), B for the slow sensitivities; ar1: B (60 d) -- both pass: A for the default engine (no artefact), B for the slow sensitivities.
