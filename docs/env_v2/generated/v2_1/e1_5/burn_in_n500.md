# E1.5 burn-in (PREREG_PHASE_1.md section 6; REG-17)

Reference = (x, sigma^2, n_f) on benchmark day 5000 of 500 flat paths (seeds 80000-80499) per engine; options: the current 260-day burn-in, A = >= 5 half-lives ({'fw_fallback_hl150': 750, 'fw_hl60': 300, 'fw_index': 3140, 'pruna': 3110, 'ar1': 750}), B = stored long-run state + 60-day warm-up. Two-sample KS per variable with a 1000-resample bootstrap upper limit; pass = every upper limit < 0.1.

| engine | option | burn-in | KS x (upper) | KS sigma^2 (upper) | KS n_f (upper) | sd(x_1)/sd(x_ref) | pass |
|---|---|---|---|---|---|---|---|
| fw_fallback_hl150 | current_260 | 260 (long) | 0.056 (0.116) | 0.038 (0.100) | 0.018 (0.050) | 1.121 | False |
| fw_fallback_hl150 | A_long_750 | 750 (long) | 0.066 (0.132) | 0.052 (0.114) | 0.012 (0.044) | 1.113 | False |
| fw_fallback_hl150 | B_stored_60 | 60 (stored) | 0.044 (0.114) | 0.042 (0.110) | 0.016 (0.046) | 0.912 | False |
| fw_hl60 | current_260 | 260 (long) | 0.066 (0.128) | 0.038 (0.100) | 0.026 (0.066) | 1.217 | False |
| fw_hl60 | A_long_300 | 300 (long) | 0.054 (0.118) | 0.058 (0.128) | 0.042 (0.082) | 1.172 | False |
| fw_hl60 | B_stored_60 | 60 (stored) | 0.058 (0.124) | 0.042 (0.110) | 0.054 (0.094) | 0.945 | False |
| fw_index | current_260 | 260 (long) | 0.162 (0.214) | 0.038 (0.100) | 0.052 (0.078) | 0.676 | False |
| fw_index | A_long_3140 | 3140 (long) | 0.056 (0.110) | 0.052 (0.118) | 0.012 (0.030) | 1.070 | False |
| fw_index | B_stored_60 | 60 (stored) | 0.052 (0.120) | 0.042 (0.110) | 0.016 (0.034) | 0.877 | False |
| pruna | current_260 | 260 (long) | 0.158 (0.210) | 0.038 (0.100) | 0.038 (0.062) | 0.683 | False |
| pruna | A_long_3110 | 3110 (long) | 0.044 (0.114) | 0.044 (0.116) | 0.010 (0.026) | 1.086 | False |
| pruna | B_stored_60 | 60 (stored) | 0.052 (0.120) | 0.042 (0.110) | 0.020 (0.040) | 0.878 | False |
| ar1 | current_260 | 260 (long) | 0.058 (0.120) | 0.038 (0.100) | 0.000 (0.000) | 1.107 | False |
| ar1 | A_long_750 | 750 (long) | 0.070 (0.130) | 0.052 (0.114) | 0.000 (0.000) | 1.112 | False |
| ar1 | B_stored_60 | 60 (stored) | 0.042 (0.114) | 0.042 (0.110) | 0.000 (0.000) | 0.911 | False |

Decision (REG-17): fw_fallback_hl150: current (260 d) -- neither option passes: current burn-in kept, shortfall stated; fw_hl60: current (260 d) -- neither option passes: current burn-in kept, shortfall stated; fw_index: current (260 d) -- neither option passes: current burn-in kept, shortfall stated; pruna: current (260 d) -- neither option passes: current burn-in kept, shortfall stated; ar1: current (260 d) -- neither option passes: current burn-in kept, shortfall stated.
