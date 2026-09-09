# Section 9 checklist under the reference criteria (Phase 6 after)

The same 500-seed SCL paths under the reference criteria (REG-14 B and C; PREREG_PHASE_6.md section 5), reference `e6_1/windows.csv` (12,927 windows); B is decisive only at n_gen >= 500. Re-evaluated from the cached per-path statistics after the criteria file's items block was corrected (per-statistic population overrides; item 4 descriptive).

Populations: flat 500, bull_trap 500, crash 1500, sustained_bull 500 paths (T = 200). B: bootstrap 95 % upper limit of the KS distance < 0.1; C: share inside the reference P10–P90 ≥ 0.8 − the share's half-width; crash windows = MDD ≤ -0.2.

| # | Property | statistics | population | n | B | C | A (v2) |
|---|---|---|---|---|---|---|---|
| 1 | No linear autocorrelation of returns | 2 | all | 3000 | FAIL | FAIL | PASS |
| 2 | Heavy tails | 3 | all | 3000 | FAIL | PASS | FAIL |
| 3 | Volatility clustering | 4 | all | 3000 | FAIL | FAIL | FAIL |
| 4 | Decay of ACF|r| (descriptive) | 5 | all | 3000 | n/a | n/a | n/a |
| 5 | GARCH persistence | 3 | all | 3000 | FAIL | FAIL | PASS |
| 6 | Leverage effect | 2 | all | 3000 | FAIL | FAIL | FAIL |
| 7 | Volume-volatility | 3 | all | 3000 | FAIL | FAIL | PASS |
| 8 | Gain/loss asymmetry in crash | 2 | crash | 1500 | FAIL | PASS | FAIL |
| 20 | Magnitudes | 3 | crash/flat | 500 | FAIL | FAIL | PASS |

## Per statistic (main population)

| # | statistic | pop | n_gen / n_ref | gen P10 / P50 / P90 | ref P10 / P50 / P90 | D (upper) | B | share (thr) | C |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `lb_p_r` | all | 3000 / 12927 | 0.00736 / 0.294 / 0.849 | 0.0237 / 0.392 / 0.867 | 0.100 (0.119) | FAIL | 0.753 (0.786) | FAIL |
| 1 | `abs_acf1_r` | all | 3000 / 12927 | 0.0106 / 0.059 / 0.143 | 0.011 / 0.0585 / 0.151 | 0.029 (0.042) | PASS | 0.818 (0.786) | PASS |
| 2 | `kurtosis` | all | 3000 / 12927 | 0.313 / 1.72 / 6.33 | 0.466 / 2.17 / 10.7 | 0.126 (0.142) | FAIL | 0.809 (0.786) | PASS |
| 2 | `hill` | all | 3000 / 12927 | 2.65 / 3.86 / 6.03 | 2.31 / 3.56 / 5.57 | 0.120 (0.137) | FAIL | 0.828 (0.786) | PASS |
| 2 | `jb_p` | all | 3000 / 12927 | 8.3e-78 / 7.6e-07 / 0.35 | 1.02e-223 / 8.24e-11 / 0.191 | 0.133 (0.149) | FAIL | 0.802 (0.786) | PASS |
| 3 | `lb_p_absr` | all | 3000 / 12927 | 3.08e-21 / 0.0171 / 0.799 | 3.7e-07 / 0.182 / 0.835 | 0.242 (0.260) | FAIL | 0.595 (0.786) | FAIL |
| 3 | `lb_p_r2` | all | 3000 / 12927 | 2.39e-11 / 0.0851 / 0.945 | 3.16e-06 / 0.447 / 0.998 | 0.189 (0.207) | FAIL | 0.717 (0.786) | FAIL |
| 3 | `arch_lm_p` | all | 3000 / 12927 | 2.52e-05 / 0.182 / 0.93 | 0.000155 / 0.395 / 0.982 | 0.124 (0.141) | FAIL | 0.803 (0.786) | PASS |
| 3 | `acf1_absr` | all | 3000 / 12927 | -0.0417 / 0.1 / 0.29 | -0.0256 / 0.0873 / 0.232 | 0.119 (0.138) | FAIL | 0.662 (0.786) | FAIL |
| 4 | `acf1_absr` | all | 3000 / 12927 | -0.0417 / 0.1 / 0.29 | -0.0256 / 0.0873 / 0.232 | 0.119 (0.137) | FAIL | 0.662 (0.786) | FAIL |
| 4 | `acf5_absr` | all | 3000 / 12927 | -0.0437 / 0.0797 / 0.244 | -0.0509 / 0.0427 / 0.172 | 0.188 (0.205) | FAIL | 0.672 (0.786) | FAIL |
| 4 | `acf10_absr` | all | 3000 / 12927 | -0.0524 / 0.066 / 0.221 | -0.062 / 0.0291 / 0.147 | 0.178 (0.197) | FAIL | 0.666 (0.786) | FAIL |
| 4 | `acf20_absr` | all | 3000 / 12927 | -0.0589 / 0.0437 / 0.168 | -0.0715 / 0.00948 / 0.108 | 0.189 (0.206) | FAIL | 0.676 (0.786) | FAIL |
| 4 | `acf50_absr` | all | 3000 / 12927 | -0.0893 / -0.0124 / 0.0696 | -0.0824 / -0.00898 / 0.0697 | 0.025 (0.046) | PASS | 0.781 (0.786) | FAIL |
| 5 | `garch_persistence` | all | 3000 / 12927 | 0.673 / 0.981 / 1 | 0.289 / 0.93 / 1 | 0.267 (0.283) | FAIL | 0.723 (0.786) | FAIL |
| 5 | `garch_alpha` | all | 3000 / 12927 | 0 / 0.0623 / 0.168 | 0 / 0.0579 / 0.27 | 0.121 (0.132) | FAIL | 0.975 (0.786) | PASS |
| 5 | `garch_beta` | all | 3000 / 12927 | 0.489 / 0.891 / 0.997 | 1.2e-10 / 0.825 / 0.995 | 0.258 (0.274) | FAIL | 0.838 (0.786) | PASS |
| 6 | `leverage_corr` | all | 3000 / 12927 | -0.133 / -0.0155 / 0.0876 | -0.147 / -0.0381 / 0.0698 | 0.114 (0.133) | FAIL | 0.781 (0.786) | FAIL |
| 6 | `gjr_gamma` | all | 3000 / 12927 | -0.0616 / 0.046 / 0.188 | -0.101 / 0.0598 / 0.335 | 0.140 (0.153) | FAIL | 0.912 (0.786) | PASS |
| 7 | `volume_absr_spearman` | all | 3000 / 12927 | 0.211 / 0.326 / 0.44 | 0.187 / 0.326 / 0.46 | 0.050 (0.063) | PASS | 0.876 (0.786) | PASS |
| 7 | `logvolume_acf1` | all | 3000 / 12927 | 0.45 / 0.547 / 0.635 | 0.373 / 0.508 / 0.642 | 0.222 (0.238) | FAIL | 0.911 (0.786) | PASS |
| 7 | `logvolume_shapiro_p` | all | 3000 / 12927 | 0.000161 / 0.224 / 0.809 | 2.23e-07 / 0.0037 / 0.422 | 0.402 (0.419) | FAIL | 0.616 (0.786) | FAIL |
| 8 | `skew` | crash | 1500 / 6275 | -0.674 / -0.0266 / 0.602 | -1.41 / -0.135 / 0.608 | 0.137 (0.160) | FAIL | 0.880 (0.780) | PASS |
| 8 | `worst_over_best` | crash | 1500 / 6275 | 0.662 / 1.02 / 1.57 | 0.644 / 1.11 / 2.1 | 0.142 (0.165) | FAIL | 0.879 (0.780) | PASS |
| 20 | `mdd` | crash | 1500 / 6275 | -0.639 / -0.516 / -0.395 | -0.54 / -0.307 / -0.216 | 0.631 (0.649) | FAIL | 0.596 (0.780) | FAIL |
| 20 | `worst_day` | crash | 1500 / 6275 | -0.225 / -0.138 / -0.0916 | -0.205 / -0.0944 / -0.0542 | 0.380 (0.398) | FAIL | 0.849 (0.780) | PASS |
| 20 | `daily_sigma` | flat | 500 / 12927 | 0.0172 / 0.0202 / 0.0262 | 0.0108 / 0.0175 / 0.0341 | 0.422 (0.436) | FAIL | 0.976 (0.765) | PASS |

## E6.8 and item 9 (the criteria without a real-window counterpart)

| # | statistic | pop | value [CI] | reference | criterion | result | n |
|---|---|---|---|---|---|---|---|
| 12 | slope of r_t on z(s_{t-1}) | r_{t-1}, calm rows | all | 0.00055313 | 0.0008 | CI contains the configured b_pred (E6.8) | FAIL | 3000 |
| 13 | sd across seeds of the calm IV mean | all | 6.8059 | 0.0 | non-degenerate: CI excludes 0 (E6.8) | PASS | 2500 |
| 9 | median 200-day ACF(1) of x, flat paths | flat | 0.94502 | [0.9060659079627575, 0.9684235368359597] | inside E6.9's AR(1) reference [P10, P90] at the FIT half-life | PASS | 500 |
| 9 | median 200-day sd(x), flat paths | flat | 0.046321 | [0.03891957285254531, 0.07235255190542306] | inside the AR(1) reference [P10, P90] scaled to s_x | PASS | 500 |

**B: pass 0 / fail 8 / not applicable 1.**

**C: pass 2 / fail 6 / not applicable 1.**
