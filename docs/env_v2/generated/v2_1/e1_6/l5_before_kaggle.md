# L5 observables oracle vs true-V oracle

Training seeds 500..539 (disjoint from evaluated seeds 0..49); T = 200; generator config overrides {'start_price_mode': 'fixed', 'sigma_V': 0.006, 'df_V': 5.0, 'mu_V': 0.00025, 'jump_placement': 'x_negmean', 'jump_rate': 0.01, 'jump_mean': -0.04, 'jump_sd': 0.03, 'burn_in': 260, 'burn_in_mode': 'long'}; GBT on rendered fields + 5 lags -> x_hat; policy = mandate-conditional rule on x_hat. The gap is a LOWER bound on what observables allow (this model class), i.e. an UPPER bound on the information withheld.

## Per-phase OOS R2 / sign accuracy of x_hat on the training pool

- full: calm: R2 0.92, sign 0.98; event: R2 0.97, sign 0.99; resolution: R2 0.94, sign 0.98
- price_only: calm: R2 0.85, sign 0.97; event: R2 0.93, sign 0.97; resolution: R2 0.83, sign 0.98
- level_free: calm: R2 0.48, sign 0.78; event: R2 0.71, sign 0.84; resolution: R2 0.42, sign 0.91

## Withheld-information gap (MCR at theta 0.05; lower MCR is better)

persona       scenario         L5  MCR_L5  MCR_true_oracle  withheld_info_gap
   ENTJ      bull_trap       full   0.018            0.002              0.016
   ENTJ      bull_trap price_only   0.016            0.002              0.014
   ENTJ      bull_trap level_free   0.063            0.002              0.061
   ENTJ          crash       full   0.015            0.001              0.015
   ENTJ          crash price_only   0.014            0.001              0.014
   ENTJ          crash level_free   0.043            0.001              0.043
   ENTJ           flat       full   0.030            0.001              0.029
   ENTJ           flat price_only   0.031            0.001              0.030
   ENTJ           flat level_free   0.072            0.001              0.071
   ENTJ sustained_bull       full   0.094            0.001              0.093
   ENTJ sustained_bull price_only   0.104            0.001              0.103
   ENTJ sustained_bull level_free   0.080            0.001              0.080
   INTJ      bull_trap       full   0.019            0.003              0.015
   INTJ      bull_trap price_only   0.017            0.003              0.014
   INTJ      bull_trap level_free   0.064            0.003              0.061
   INTJ          crash       full   0.018            0.003              0.014
   INTJ          crash price_only   0.017            0.003              0.014
   INTJ          crash level_free   0.045            0.003              0.042
   INTJ           flat       full   0.032            0.003              0.028
   INTJ           flat price_only   0.033            0.003              0.030
   INTJ           flat level_free   0.073            0.003              0.070
   INTJ sustained_bull       full   0.094            0.002              0.092
   INTJ sustained_bull price_only   0.103            0.002              0.101
   INTJ sustained_bull level_free   0.082            0.002              0.080
   ISFJ      bull_trap       full   0.019            0.004              0.015
   ISFJ      bull_trap price_only   0.017            0.004              0.014
   ISFJ      bull_trap level_free   0.064            0.004              0.061
   ISFJ          crash       full   0.018            0.003              0.015
   ISFJ          crash price_only   0.017            0.003              0.014
   ISFJ          crash level_free   0.046            0.003              0.042
   ISFJ           flat       full   0.032            0.003              0.029
   ISFJ           flat price_only   0.033            0.003              0.030
   ISFJ           flat level_free   0.074            0.003              0.070
   ISFJ sustained_bull       full   0.094            0.002              0.092
   ISFJ sustained_bull price_only   0.104            0.002              0.102
   ISFJ sustained_bull level_free   0.082            0.002              0.081

## Policy means per persona x scenario

                                                   mcr_0.05  band_mas  turnover  return_pct  mdd_pct
persona scenario       policy                                                                       
ENTJ    bull_trap      L5_full                        0.018     0.001     0.659      78.092  -24.825
                       L5_level_free                  0.063     0.000     1.148      77.602  -26.032
                       L5_price_only                  0.016     0.001     0.643      78.150  -24.741
                       always_hold                    0.117     0.000     0.000      85.972  -26.272
                       constant_mix                   0.101     0.000     0.164      83.495  -25.823
                       mandate_conditional_oracle     0.002     0.001     0.625      78.784  -24.958
                       v_oracle                       0.502     0.458     1.821      24.788  -12.195
        crash          L5_full                        0.015     0.000     0.333     -18.943  -45.406
                       L5_level_free                  0.043     0.000     0.471     -21.413  -46.907
                       L5_price_only                  0.014     0.000     0.317     -19.146  -45.503
                       always_hold                    0.121     0.000     0.000     -19.356  -43.120
                       constant_mix                   0.100     0.000     0.092     -19.067  -43.694
                       mandate_conditional_oracle     0.001     0.000     0.302     -18.972  -45.360
                       v_oracle                       0.145     0.157     1.291      -7.690  -37.135
        flat           L5_full                        0.030     0.000     0.316       8.758  -21.220
                       L5_level_free                  0.072     0.000     0.559       7.033  -22.508
                       L5_price_only                  0.031     0.001     0.287       8.344  -21.152
                       always_hold                    0.105     0.000     0.000       6.986  -20.999
                       constant_mix                   0.100     0.000     0.051       7.090  -21.019
                       mandate_conditional_oracle     0.001     0.001     0.278       8.515  -21.450
                       v_oracle                       0.257     0.244     1.171      11.525  -16.602
        sustained_bull L5_full                        0.094     0.001     0.255      42.070   -8.174
                       L5_level_free                  0.080     0.000     0.470      48.039   -9.031
                       L5_price_only                  0.104     0.001     0.232      41.007   -7.951
                       always_hold                    0.102     0.000     0.000      45.258   -8.789
                       constant_mix                   0.103     0.000     0.045      44.564   -8.651
                       mandate_conditional_oracle     0.001     0.000     0.389      47.973   -8.241
                       v_oracle                       0.385     0.243     1.950      46.121   -6.479
INTJ    bull_trap      L5_full                        0.019     0.001     0.918      36.616  -14.234
                       L5_level_free                  0.064     0.001     1.370      36.257  -15.644
                       L5_price_only                  0.017     0.001     0.894      36.647  -14.129
                       always_hold                    0.156     0.015     0.000      47.762  -17.454
                       constant_mix                   0.101     0.000     0.568      40.360  -15.435
                       mandate_conditional_oracle     0.003     0.002     0.881      37.177  -14.359
                       v_oracle                       0.400     0.394     1.913      24.677  -11.991
        crash          L5_full                        0.018     0.002     0.739      -9.412  -28.974
                       L5_level_free                  0.045     0.001     0.880     -12.299  -30.969
                       L5_price_only                  0.017     0.002     0.721      -9.633  -29.131
                       always_hold                    0.147     0.006     0.000     -10.753  -25.204
                       constant_mix                   0.100     0.000     0.466     -10.050  -26.974
                       mandate_conditional_oracle     0.003     0.002     0.696      -9.404  -28.873
                       v_oracle                       0.400     0.393     1.401      -7.762  -37.062
        flat           L5_full                        0.032     0.002     0.554       5.888  -12.614
                       L5_level_free                  0.073     0.002     0.800       4.223  -14.003
                       L5_price_only                  0.033     0.002     0.520       5.489  -12.533
                       always_hold                    0.111     0.002     0.000       3.881  -12.289
                       constant_mix                   0.100     0.000     0.301       4.205  -12.281
                       mandate_conditional_oracle     0.003     0.002     0.512       5.679  -12.820
                       v_oracle                       0.400     0.393     1.280      11.424  -16.485
        sustained_bull L5_full                        0.094     0.001     0.380      20.935   -4.398
                       L5_level_free                  0.082     0.002     0.616      26.172   -5.271
                       L5_price_only                  0.103     0.001     0.349      19.996   -4.166
                       always_hold                    0.108     0.001     0.000      25.143   -5.342
                       constant_mix                   0.101     0.000     0.227      23.058   -4.859
                       mandate_conditional_oracle     0.002     0.001     0.471      26.333   -4.565
                       v_oracle                       0.400     0.270     1.792      38.474   -5.381
ISFJ    bull_trap      L5_full                        0.019     0.001     0.603      11.931   -5.250
                       L5_level_free                  0.064     0.001     1.045      11.620   -6.850
                       L5_price_only                  0.017     0.001     0.576      11.952   -5.108
                       always_hold                    0.144     0.008     0.000      19.105   -8.528
                       constant_mix                   0.101     0.000     0.299      14.798   -6.473
                       mandate_conditional_oracle     0.004     0.002     0.581      12.391   -5.351
                       v_oracle                       0.324     0.346     1.983      24.594  -11.853
        crash          L5_full                        0.018     0.002     0.638      -2.836  -14.040
                       L5_level_free                  0.046     0.001     0.807      -5.972  -16.442
                       L5_price_only                  0.017     0.002     0.623      -3.051  -14.233
                       always_hold                    0.127     0.000     0.000      -4.301  -10.523
                       constant_mix                   0.100     0.000     0.273      -3.712  -11.592
                       mandate_conditional_oracle     0.003     0.002     0.600      -2.813  -13.919
                       v_oracle                       0.591     0.570     1.484      -7.816  -37.029
        flat           L5_full                        0.032     0.002     0.443       3.470   -5.713
                       L5_level_free                  0.074     0.002     0.709       1.874   -7.061
                       L5_price_only                  0.033     0.002     0.409       3.097   -5.603
                       always_hold                    0.106     0.000     0.000       1.552   -5.146
                       constant_mix                   0.100     0.000     0.152       1.800   -5.092
                       mandate_conditional_oracle     0.003     0.002     0.417       3.294   -5.836
                       v_oracle                       0.507     0.505     1.362      11.348  -16.413
        sustained_bull L5_full                        0.094     0.001     0.230       6.876   -1.593
                       L5_level_free                  0.082     0.002     0.507      11.598   -2.450
                       L5_price_only                  0.104     0.001     0.183       5.998   -1.391
                       always_hold                    0.106     0.000     0.000      10.057   -2.307
                       constant_mix                   0.103     0.000     0.094       8.744   -1.968
                       mandate_conditional_oracle     0.002     0.001     0.395      11.423   -1.840
                       v_oracle                       0.412     0.291     1.673      32.740   -4.886
