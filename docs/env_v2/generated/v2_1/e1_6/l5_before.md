# L5 observables oracle vs true-V oracle

Training seeds 500..539 (disjoint from evaluated seeds 0..49); T = 200; generator config overrides {'start_price_mode': 'fixed', 'sigma_V': 0.006, 'df_V': 5.0, 'mu_V': 0.00025, 'jump_placement': 'x_negmean', 'jump_rate': 0.01, 'jump_mean': -0.04, 'jump_sd': 0.03, 'burn_in': 260, 'burn_in_mode': 'long'}; GBT on rendered fields + 5 lags -> x_hat; policy = mandate-conditional rule on x_hat. The gap is a LOWER bound on what observables allow (this model class), i.e. an UPPER bound on the information withheld.

## Per-phase OOS R2 / sign accuracy of x_hat on the training pool

- full: calm: R2 0.92, sign 0.98; event: R2 0.97, sign 0.99; resolution: R2 0.94, sign 0.98
- price_only: calm: R2 0.85, sign 0.97; event: R2 0.93, sign 0.97; resolution: R2 0.83, sign 0.98
- level_free: calm: R2 0.48, sign 0.79; event: R2 0.71, sign 0.84; resolution: R2 0.42, sign 0.91

## Withheld-information gap (MCR at theta 0.05; lower MCR is better)

persona       scenario         L5  MCR_L5  MCR_true_oracle  withheld_info_gap
   ENTJ      bull_trap       full   0.018            0.002              0.015
   ENTJ      bull_trap price_only   0.017            0.002              0.014
   ENTJ      bull_trap level_free   0.063            0.002              0.060
   ENTJ          crash       full   0.015            0.001              0.014
   ENTJ          crash price_only   0.015            0.001              0.014
   ENTJ          crash level_free   0.042            0.001              0.041
   ENTJ           flat       full   0.030            0.001              0.029
   ENTJ           flat price_only   0.030            0.001              0.029
   ENTJ           flat level_free   0.071            0.001              0.070
   ENTJ sustained_bull       full   0.099            0.001              0.098
   ENTJ sustained_bull price_only   0.104            0.001              0.104
   ENTJ sustained_bull level_free   0.079            0.001              0.078
   INTJ      bull_trap       full   0.018            0.003              0.015
   INTJ      bull_trap price_only   0.018            0.003              0.014
   INTJ      bull_trap level_free   0.064            0.003              0.060
   INTJ          crash       full   0.017            0.003              0.014
   INTJ          crash price_only   0.017            0.003              0.014
   INTJ          crash level_free   0.044            0.003              0.041
   INTJ           flat       full   0.032            0.003              0.028
   INTJ           flat price_only   0.032            0.003              0.029
   INTJ           flat level_free   0.073            0.003              0.070
   INTJ sustained_bull       full   0.099            0.002              0.097
   INTJ sustained_bull price_only   0.103            0.002              0.101
   INTJ sustained_bull level_free   0.080            0.002              0.078
   ISFJ      bull_trap       full   0.019            0.004              0.015
   ISFJ      bull_trap price_only   0.018            0.004              0.014
   ISFJ      bull_trap level_free   0.064            0.004              0.060
   ISFJ          crash       full   0.018            0.003              0.014
   ISFJ          crash price_only   0.017            0.003              0.014
   ISFJ          crash level_free   0.044            0.003              0.041
   ISFJ           flat       full   0.032            0.003              0.029
   ISFJ           flat price_only   0.032            0.003              0.029
   ISFJ           flat level_free   0.073            0.003              0.070
   ISFJ sustained_bull       full   0.100            0.002              0.098
   ISFJ sustained_bull price_only   0.104            0.002              0.102
   ISFJ sustained_bull level_free   0.080            0.002              0.079

## Policy means per persona x scenario

                                                   mcr_0.05  band_mas  turnover  return_pct  mdd_pct
persona scenario       policy                                                                       
ENTJ    bull_trap      L5_full                        0.018     0.001     0.663      78.076  -24.820
                       L5_level_free                  0.063     0.000     1.040      77.928  -25.994
                       L5_price_only                  0.017     0.001     0.646      78.184  -24.787
                       always_hold                    0.117     0.000     0.000      85.972  -26.272
                       constant_mix                   0.101     0.000     0.164      83.495  -25.823
                       mandate_conditional_oracle     0.002     0.001     0.625      78.784  -24.958
                       v_oracle                       0.502     0.458     1.821      24.788  -12.195
        crash          L5_full                        0.015     0.000     0.326     -18.999  -45.414
                       L5_level_free                  0.042     0.000     0.460     -21.136  -46.793
                       L5_price_only                  0.015     0.000     0.289     -19.406  -45.555
                       always_hold                    0.121     0.000     0.000     -19.356  -43.120
                       constant_mix                   0.100     0.000     0.092     -19.067  -43.694
                       mandate_conditional_oracle     0.001     0.000     0.302     -18.972  -45.360
                       v_oracle                       0.145     0.157     1.291      -7.690  -37.135
        flat           L5_full                        0.030     0.001     0.305       8.707  -21.245
                       L5_level_free                  0.071     0.000     0.520       7.283  -22.469
                       L5_price_only                  0.030     0.000     0.304       8.314  -21.230
                       always_hold                    0.105     0.000     0.000       6.986  -20.999
                       constant_mix                   0.100     0.000     0.051       7.090  -21.019
                       mandate_conditional_oracle     0.001     0.001     0.278       8.515  -21.450
                       v_oracle                       0.257     0.244     1.171      11.525  -16.602
        sustained_bull L5_full                        0.099     0.001     0.259      42.214   -8.195
                       L5_level_free                  0.079     0.000     0.425      48.261   -9.048
                       L5_price_only                  0.104     0.001     0.232      40.960   -7.937
                       always_hold                    0.102     0.000     0.000      45.258   -8.789
                       constant_mix                   0.103     0.000     0.045      44.564   -8.651
                       mandate_conditional_oracle     0.001     0.000     0.389      47.973   -8.241
                       v_oracle                       0.385     0.243     1.950      46.121   -6.479
INTJ    bull_trap      L5_full                        0.018     0.001     0.918      36.596  -14.225
                       L5_level_free                  0.064     0.001     1.279      36.529  -15.607
                       L5_price_only                  0.018     0.001     0.893      36.681  -14.195
                       always_hold                    0.156     0.015     0.000      47.762  -17.454
                       constant_mix                   0.101     0.000     0.568      40.360  -15.435
                       mandate_conditional_oracle     0.003     0.002     0.881      37.177  -14.359
                       v_oracle                       0.400     0.394     1.913      24.677  -11.991
        crash          L5_full                        0.017     0.002     0.729      -9.484  -28.983
                       L5_level_free                  0.044     0.001     0.873     -11.988  -30.824
                       L5_price_only                  0.017     0.002     0.686      -9.971  -29.218
                       always_hold                    0.147     0.006     0.000     -10.753  -25.204
                       constant_mix                   0.100     0.000     0.466     -10.050  -26.974
                       mandate_conditional_oracle     0.003     0.002     0.696      -9.404  -28.873
                       v_oracle                       0.400     0.393     1.401      -7.762  -37.062
        flat           L5_full                        0.032     0.002     0.539       5.831  -12.611
                       L5_level_free                  0.073     0.002     0.763       4.454  -13.953
                       L5_price_only                  0.032     0.002     0.534       5.456  -12.640
                       always_hold                    0.111     0.002     0.000       3.881  -12.289
                       constant_mix                   0.100     0.000     0.301       4.205  -12.281
                       mandate_conditional_oracle     0.003     0.002     0.512       5.679  -12.820
                       v_oracle                       0.400     0.393     1.280      11.424  -16.485
        sustained_bull L5_full                        0.099     0.001     0.388      21.065   -4.424
                       L5_level_free                  0.080     0.002     0.579      26.366   -5.324
                       L5_price_only                  0.103     0.001     0.351      19.963   -4.152
                       always_hold                    0.108     0.001     0.000      25.143   -5.342
                       constant_mix                   0.101     0.000     0.227      23.058   -4.859
                       mandate_conditional_oracle     0.002     0.001     0.471      26.333   -4.565
                       v_oracle                       0.400     0.270     1.792      38.474   -5.381
ISFJ    bull_trap      L5_full                        0.019     0.001     0.606      11.911   -5.275
                       L5_level_free                  0.064     0.001     0.958      11.846   -6.797
                       L5_price_only                  0.018     0.001     0.577      11.989   -5.132
                       always_hold                    0.144     0.008     0.000      19.105   -8.528
                       constant_mix                   0.101     0.000     0.299      14.798   -6.473
                       mandate_conditional_oracle     0.004     0.002     0.581      12.391   -5.351
                       v_oracle                       0.324     0.346     1.983      24.594  -11.853
        crash          L5_full                        0.018     0.002     0.628      -2.921  -14.052
                       L5_level_free                  0.044     0.001     0.795      -5.656  -16.269
                       L5_price_only                  0.017     0.002     0.587      -3.434  -14.353
                       always_hold                    0.127     0.000     0.000      -4.301  -10.523
                       constant_mix                   0.100     0.000     0.273      -3.712  -11.592
                       mandate_conditional_oracle     0.003     0.002     0.600      -2.813  -13.919
                       v_oracle                       0.591     0.570     1.484      -7.816  -37.029
        flat           L5_full                        0.032     0.002     0.430       3.413   -5.684
                       L5_level_free                  0.073     0.002     0.666       2.084   -7.021
                       L5_price_only                  0.032     0.002     0.420       3.060   -5.645
                       always_hold                    0.106     0.000     0.000       1.552   -5.146
                       constant_mix                   0.100     0.000     0.152       1.800   -5.092
                       mandate_conditional_oracle     0.003     0.002     0.417       3.294   -5.836
                       v_oracle                       0.507     0.505     1.362      11.348  -16.413
        sustained_bull L5_full                        0.100     0.001     0.236       6.979   -1.627
                       L5_level_free                  0.080     0.002     0.474      11.775   -2.509
                       L5_price_only                  0.104     0.001     0.183       5.967   -1.387
                       always_hold                    0.106     0.000     0.000      10.057   -2.307
                       constant_mix                   0.103     0.000     0.094       8.744   -1.968
                       mandate_conditional_oracle     0.002     0.001     0.395      11.423   -1.840
                       v_oracle                       0.412     0.291     1.673      32.740   -4.886
