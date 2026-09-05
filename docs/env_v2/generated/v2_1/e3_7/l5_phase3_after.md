# L5 observables oracle vs true-V oracle

Training seeds 500..539 (disjoint from evaluated seeds 0..49); T = 200; generator config overrides {}; GBT on rendered fields + 5 lags -> x_hat; policy = mandate-conditional rule on x_hat. The gap is a LOWER bound on what observables allow (this model class), i.e. an UPPER bound on the information withheld.

## Per-phase OOS R2 / sign accuracy of x_hat on the training pool

- full: calm: R2 0.44, sign 0.90; event: R2 0.87, sign 0.96; resolution: R2 0.83, sign 0.98
- price_only: calm: R2 -0.14, sign 0.87; event: R2 0.62, sign 0.90; resolution: R2 0.21, sign 0.87
- level_free: calm: R2 -0.12, sign 0.82; event: R2 0.62, sign 0.90; resolution: R2 0.24, sign 0.87

## Withheld-information gap (MCR at theta 0.05; lower MCR is better)

persona       scenario         L5  MCR_L5  MCR_true_oracle  withheld_info_gap
   ENTJ      bull_trap       full   0.026            0.003              0.023
   ENTJ      bull_trap price_only   0.039            0.003              0.036
   ENTJ      bull_trap level_free   0.038            0.003              0.035
   ENTJ          crash       full   0.029            0.001              0.028
   ENTJ          crash price_only   0.038            0.001              0.037
   ENTJ          crash level_free   0.036            0.001              0.035
   ENTJ           flat       full   0.055            0.002              0.053
   ENTJ           flat price_only   0.059            0.002              0.057
   ENTJ           flat level_free   0.057            0.002              0.055
   ENTJ sustained_bull       full   0.080            0.001              0.079
   ENTJ sustained_bull price_only   0.072            0.001              0.071
   ENTJ sustained_bull level_free   0.084            0.001              0.083
   INTJ      bull_trap       full   0.026            0.003              0.023
   INTJ      bull_trap price_only   0.039            0.003              0.035
   INTJ      bull_trap level_free   0.038            0.003              0.035
   INTJ          crash       full   0.031            0.003              0.028
   INTJ          crash price_only   0.039            0.003              0.036
   INTJ          crash level_free   0.037            0.003              0.034
   INTJ           flat       full   0.055            0.003              0.052
   INTJ           flat price_only   0.059            0.003              0.056
   INTJ           flat level_free   0.057            0.003              0.054
   INTJ sustained_bull       full   0.080            0.002              0.078
   INTJ sustained_bull price_only   0.072            0.002              0.071
   INTJ sustained_bull level_free   0.084            0.002              0.082
   ISFJ      bull_trap       full   0.026            0.003              0.023
   ISFJ      bull_trap price_only   0.039            0.003              0.035
   ISFJ      bull_trap level_free   0.038            0.003              0.035
   ISFJ          crash       full   0.031            0.003              0.028
   ISFJ          crash price_only   0.039            0.003              0.036
   ISFJ          crash level_free   0.037            0.003              0.035
   ISFJ           flat       full   0.056            0.003              0.052
   ISFJ           flat price_only   0.059            0.003              0.056
   ISFJ           flat level_free   0.057            0.003              0.054
   ISFJ sustained_bull       full   0.080            0.002              0.078
   ISFJ sustained_bull price_only   0.073            0.002              0.071
   ISFJ sustained_bull level_free   0.084            0.002              0.083

## Policy means per persona x scenario

                                                   mcr_0.05  band_mas  turnover  return_pct  mdd_pct
persona scenario       policy                                                                       
ENTJ    bull_trap      L5_full                        0.026     0.001     0.488      38.388  -21.599
                       L5_level_free                  0.038     0.001     0.617      38.819  -21.856
                       L5_price_only                  0.039     0.001     0.578      38.481  -22.158
                       always_hold                    0.116     0.000     0.000      42.360  -22.409
                       constant_mix                   0.102     0.000     0.100      41.756  -22.306
                       mandate_conditional_oracle     0.003     0.001     0.630      40.323  -21.121
                       v_oracle                       0.692     0.563     2.369      14.972  -12.392
        crash          L5_full                        0.029     0.000     0.719     -18.179  -50.101
                       L5_level_free                  0.036     0.001     0.731     -19.250  -50.691
                       L5_price_only                  0.038     0.001     0.615     -20.346  -50.996
                       always_hold                    0.131     0.000     0.000     -20.469  -48.459
                       constant_mix                   0.100     0.000     0.161     -19.602  -49.199
                       mandate_conditional_oracle     0.001     0.001     0.765     -17.074  -49.829
                       v_oracle                       0.195     0.260     4.044       8.771  -39.404
        flat           L5_full                        0.055     0.001     0.465       5.797  -24.534
                       L5_level_free                  0.057     0.001     0.501       5.944  -24.460
                       L5_price_only                  0.059     0.001     0.492       5.912  -24.598
                       always_hold                    0.108     0.000     0.000       5.007  -24.985
                       constant_mix                   0.101     0.000     0.070       5.204  -24.955
                       mandate_conditional_oracle     0.002     0.001     0.615       7.942  -24.380
                       v_oracle                       0.483     0.413     2.914      17.174  -15.940
        sustained_bull L5_full                        0.080     0.001     0.377      50.925  -12.518
                       L5_level_free                  0.084     0.001     0.336      49.324  -12.078
                       L5_price_only                  0.072     0.001     0.403      50.074  -12.067
                       always_hold                    0.109     0.000     0.000      55.551  -13.212
                       constant_mix                   0.103     0.000     0.069      54.485  -12.968
                       mandate_conditional_oracle     0.001     0.000     0.431      57.059  -12.767
                       v_oracle                       0.470     0.297     1.981      45.753  -11.098
INTJ    bull_trap      L5_full                        0.026     0.001     0.764      18.665  -12.257
                       L5_level_free                  0.038     0.001     0.915      19.193  -12.562
                       L5_price_only                  0.039     0.001     0.874      18.833  -12.884
                       always_hold                    0.150     0.004     0.000      23.534  -13.389
                       constant_mix                   0.100     0.000     0.513      21.575  -13.012
                       mandate_conditional_oracle     0.003     0.002     0.872      20.398  -11.737
                       v_oracle                       0.400     0.375     2.360      15.644  -11.303
        crash          L5_full                        0.031     0.001     1.501      -6.546  -31.611
                       L5_level_free                  0.037     0.001     1.532      -7.619  -32.340
                       L5_price_only                  0.039     0.001     1.390      -8.791  -32.669
                       always_hold                    0.169     0.008     0.000     -11.371  -28.290
                       constant_mix                   0.100     0.000     0.899      -8.776  -30.365
                       mandate_conditional_oracle     0.003     0.001     1.514      -5.045  -31.070
                       v_oracle                       0.400     0.371     4.022       9.538  -39.165
        flat           L5_full                        0.055     0.001     0.747       3.771  -14.095
                       L5_level_free                  0.057     0.001     0.795       3.961  -14.048
                       L5_price_only                  0.059     0.001     0.784       3.999  -14.198
                       always_hold                    0.124     0.000     0.000       2.782  -14.684
                       constant_mix                   0.100     0.000     0.424       3.252  -14.513
                       mandate_conditional_oracle     0.003     0.002     0.854       5.998  -13.883
                       v_oracle                       0.400     0.371     2.888      17.752  -15.169
        sustained_bull L5_full                        0.080     0.001     0.586      24.960   -6.937
                       L5_level_free                  0.084     0.001     0.527      23.513   -6.443
                       L5_price_only                  0.072     0.001     0.592      24.137   -6.439
                       always_hold                    0.131     0.005     0.000      30.862   -8.224
                       constant_mix                   0.102     0.000     0.405      27.922   -7.343
                       mandate_conditional_oracle     0.002     0.001     0.512      30.624   -7.320
                       v_oracle                       0.400     0.244     1.912      37.960   -8.359
ISFJ    bull_trap      L5_full                        0.026     0.001     0.453       5.659   -4.847
                       L5_level_free                  0.038     0.001     0.615       6.187   -5.081
                       L5_price_only                  0.039     0.001     0.578       5.834   -5.434
                       always_hold                    0.137     0.001     0.000       9.413   -5.744
                       constant_mix                   0.101     0.000     0.239       8.211   -5.386
                       mandate_conditional_oracle     0.003     0.001     0.591       7.218   -4.330
                       v_oracle                       0.181     0.234     2.354      16.148  -10.724
        crash          L5_full                        0.031     0.001     1.286       0.078  -15.023
                       L5_level_free                  0.037     0.001     1.350      -0.945  -15.638
                       L5_price_only                  0.039     0.001     1.194      -2.076  -15.913
                       always_hold                    0.139     0.000     0.000      -4.549  -11.790
                       constant_mix                   0.101     0.000     0.495      -2.835  -13.101
                       mandate_conditional_oracle     0.003     0.002     1.347       1.795  -14.207
                       v_oracle                       0.554     0.455     4.006      10.114  -39.007
        flat           L5_full                        0.056     0.001     0.522       1.915   -5.775
                       L5_level_free                  0.057     0.001     0.567       2.065   -5.765
                       L5_price_only                  0.059     0.002     0.566       2.201   -5.905
                       always_hold                    0.116     0.000     0.000       1.113   -6.166
                       constant_mix                   0.101     0.000     0.191       1.396   -5.994
                       mandate_conditional_oracle     0.003     0.002     0.703       4.160   -5.547
                       v_oracle                       0.338     0.340     2.868      18.186  -14.754
        sustained_bull L5_full                        0.080     0.001     0.309       7.941   -2.714
                       L5_level_free                  0.084     0.001     0.239       6.627   -2.192
                       L5_price_only                  0.073     0.001     0.298       7.147   -2.205
                       always_hold                    0.122     0.001     0.000      12.345   -3.666
                       constant_mix                   0.103     0.000     0.175      10.527   -2.985
                       mandate_conditional_oracle     0.002     0.001     0.413      12.427   -3.029
                       v_oracle                       0.347     0.204     1.861      32.115   -6.603
