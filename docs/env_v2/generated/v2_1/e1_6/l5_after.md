# L5 observables oracle vs true-V oracle

Training seeds 500..539 (disjoint from evaluated seeds 0..49); T = 200; generator config overrides {}; GBT on rendered fields + 5 lags -> x_hat; policy = mandate-conditional rule on x_hat. The gap is a LOWER bound on what observables allow (this model class), i.e. an UPPER bound on the information withheld.

## Per-phase OOS R2 / sign accuracy of x_hat on the training pool

- full: calm: R2 0.84, sign 0.97; event: R2 0.95, sign 0.98; resolution: R2 0.93, sign 0.98
- price_only: calm: R2 0.48, sign 0.87; event: R2 0.74, sign 0.89; resolution: R2 0.26, sign 0.83
- level_free: calm: R2 0.34, sign 0.79; event: R2 0.74, sign 0.86; resolution: R2 0.39, sign 0.87

## Withheld-information gap (MCR at theta 0.05; lower MCR is better)

persona       scenario         L5  MCR_L5  MCR_true_oracle  withheld_info_gap
   ENTJ      bull_trap       full   0.036            0.003              0.034
   ENTJ      bull_trap price_only   0.055            0.003              0.052
   ENTJ      bull_trap level_free   0.051            0.003              0.048
   ENTJ          crash       full   0.031            0.001              0.030
   ENTJ          crash price_only   0.055            0.001              0.054
   ENTJ          crash level_free   0.053            0.001              0.052
   ENTJ           flat       full   0.056            0.002              0.054
   ENTJ           flat price_only   0.085            0.002              0.083
   ENTJ           flat level_free   0.086            0.002              0.084
   ENTJ sustained_bull       full   0.081            0.001              0.080
   ENTJ sustained_bull price_only   0.075            0.001              0.074
   ENTJ sustained_bull level_free   0.071            0.001              0.070
   INTJ      bull_trap       full   0.037            0.003              0.033
   INTJ      bull_trap price_only   0.055            0.003              0.052
   INTJ      bull_trap level_free   0.051            0.003              0.048
   INTJ          crash       full   0.033            0.003              0.030
   INTJ          crash price_only   0.057            0.003              0.054
   INTJ          crash level_free   0.055            0.003              0.051
   INTJ           flat       full   0.057            0.003              0.054
   INTJ           flat price_only   0.086            0.003              0.082
   INTJ           flat level_free   0.087            0.003              0.084
   INTJ sustained_bull       full   0.081            0.002              0.079
   INTJ sustained_bull price_only   0.076            0.002              0.074
   INTJ sustained_bull level_free   0.071            0.002              0.069
   ISFJ      bull_trap       full   0.037            0.004              0.033
   ISFJ      bull_trap price_only   0.055            0.004              0.052
   ISFJ      bull_trap level_free   0.052            0.004              0.048
   ISFJ          crash       full   0.033            0.003              0.030
   ISFJ          crash price_only   0.057            0.003              0.054
   ISFJ          crash level_free   0.055            0.003              0.051
   ISFJ           flat       full   0.057            0.003              0.054
   ISFJ           flat price_only   0.086            0.003              0.082
   ISFJ           flat level_free   0.087            0.003              0.084
   ISFJ sustained_bull       full   0.081            0.002              0.079
   ISFJ sustained_bull price_only   0.076            0.002              0.074
   ISFJ sustained_bull level_free   0.071            0.002              0.069

## Policy means per persona x scenario

                                                   mcr_0.05  band_mas  turnover  return_pct  mdd_pct
persona scenario       policy                                                                       
ENTJ    bull_trap      L5_full                        0.036     0.001     0.547      58.774  -25.523
                       L5_level_free                  0.051     0.001     1.052      58.468  -25.961
                       L5_price_only                  0.055     0.000     0.739      59.406  -25.781
                       always_hold                    0.116     0.000     0.000      68.213  -27.215
                       constant_mix                   0.102     0.000     0.140      65.920  -26.834
                       mandate_conditional_oracle     0.003     0.001     0.587      60.478  -25.406
                       v_oracle                       0.618     0.566     1.863      12.223   -9.267
        crash          L5_full                        0.031     0.001     0.410     -27.497  -47.985
                       L5_level_free                  0.053     0.000     0.734     -29.177  -49.291
                       L5_price_only                  0.055     0.000     0.491     -29.625  -49.332
                       always_hold                    0.125     0.000     0.000     -27.931  -46.316
                       constant_mix                   0.100     0.000     0.079     -28.086  -47.179
                       mandate_conditional_oracle     0.001     0.001     0.353     -27.494  -47.935
                       v_oracle                       0.253     0.271     1.789     -11.349  -34.178
        flat           L5_full                        0.056     0.001     0.280       4.216  -18.808
                       L5_level_free                  0.086     0.001     0.923       3.785  -19.699
                       L5_price_only                  0.085     0.000     0.492       4.248  -19.613
                       always_hold                    0.103     0.000     0.000       3.664  -19.410
                       constant_mix                   0.100     0.000     0.040       3.789  -19.391
                       mandate_conditional_oracle     0.002     0.001     0.297       5.070  -18.715
                       v_oracle                       0.495     0.464     1.366       8.615   -9.455
        sustained_bull L5_full                        0.081     0.001     0.345      41.863   -8.263
                       L5_level_free                  0.071     0.001     0.728      42.420   -8.185
                       L5_price_only                  0.075     0.001     0.433      42.428   -8.417
                       always_hold                    0.105     0.000     0.000      44.484   -8.882
                       constant_mix                   0.103     0.000     0.043      43.818   -8.718
                       mandate_conditional_oracle     0.001     0.000     0.422      47.043   -8.482
                       v_oracle                       0.411     0.272     1.959      42.718   -7.123
INTJ    bull_trap      L5_full                        0.037     0.001     0.742      26.015  -14.551
                       L5_level_free                  0.051     0.001     1.232      25.760  -15.164
                       L5_price_only                  0.055     0.001     0.939      26.444  -14.960
                       always_hold                    0.154     0.011     0.000      37.896  -17.707
                       constant_mix                   0.101     0.000     0.478      31.086  -16.135
                       mandate_conditional_oracle     0.003     0.001     0.774      27.117  -14.441
                       v_oracle                       0.400     0.391     1.767      12.392   -9.045
        crash          L5_full                        0.033     0.002     0.738     -15.299  -30.536
                       L5_level_free                  0.055     0.001     1.080     -17.244  -32.262
                       L5_price_only                  0.057     0.001     0.835     -17.746  -32.364
                       always_hold                    0.155     0.010     0.000     -15.517  -26.800
                       constant_mix                   0.100     0.000     0.388     -16.257  -29.605
                       mandate_conditional_oracle     0.003     0.002     0.675     -15.107  -30.377
                       v_oracle                       0.400     0.392     1.676     -11.250  -34.138
        flat           L5_full                        0.057     0.002     0.430       2.706  -10.641
                       L5_level_free                  0.087     0.001     1.079       2.309  -11.628
                       L5_price_only                  0.086     0.001     0.654       2.753  -11.576
                       always_hold                    0.110     0.000     0.000       2.036  -11.313
                       constant_mix                   0.100     0.000     0.228       2.281  -11.245
                       mandate_conditional_oracle     0.003     0.002     0.446       3.575  -10.539
                       v_oracle                       0.400     0.392     1.253       8.728   -9.303
        sustained_bull L5_full                        0.081     0.001     0.473      21.126   -4.497
                       L5_level_free                  0.071     0.001     0.818      21.539   -4.455
                       L5_price_only                  0.076     0.001     0.547      21.578   -4.637
                       always_hold                    0.115     0.001     0.000      24.714   -5.506
                       constant_mix                   0.102     0.000     0.237      22.766   -4.898
                       mandate_conditional_oracle     0.002     0.001     0.500      25.896   -4.816
                       v_oracle                       0.400     0.273     1.991      37.477   -5.840
ISFJ    bull_trap      L5_full                        0.037     0.001     0.454       7.321   -5.112
                       L5_level_free                  0.052     0.001     0.950       7.079   -5.866
                       L5_price_only                  0.055     0.001     0.659       7.641   -5.620
                       always_hold                    0.141     0.006     0.000      15.158   -8.376
                       constant_mix                   0.101     0.000     0.247      11.225   -6.825
                       mandate_conditional_oracle     0.004     0.002     0.493       8.121   -4.938
                       v_oracle                       0.237     0.260     1.695      12.519   -8.939
        crash          L5_full                        0.033     0.002     0.645      -5.407  -14.050
                       L5_level_free                  0.055     0.001     1.019      -7.595  -16.228
                       L5_price_only                  0.057     0.001     0.764      -8.142  -16.408
                       always_hold                    0.131     0.000     0.000      -6.207  -11.089
                       constant_mix                   0.100     0.000     0.221      -6.586  -12.923
                       mandate_conditional_oracle     0.003     0.002     0.589      -5.118  -13.784
                       v_oracle                       0.510     0.482     1.592     -11.175  -34.116
        flat           L5_full                        0.057     0.001     0.304       1.379   -4.150
                       L5_level_free                  0.087     0.001     0.969       0.997   -5.252
                       L5_price_only                  0.086     0.001     0.551       1.457   -5.177
                       always_hold                    0.106     0.000     0.000       0.814   -4.722
                       constant_mix                   0.100     0.000     0.109       0.981   -4.624
                       mandate_conditional_oracle     0.003     0.002     0.334       2.256   -3.974
                       v_oracle                       0.329     0.338     1.168       8.813   -9.202
        sustained_bull L5_full                        0.081     0.001     0.317       7.223   -1.744
                       L5_level_free                  0.071     0.001     0.645       7.572   -1.763
                       L5_price_only                  0.076     0.001     0.390       7.629   -1.807
                       always_hold                    0.110     0.000     0.000       9.885   -2.431
                       constant_mix                   0.103     0.000     0.104       8.674   -1.978
                       mandate_conditional_oracle     0.002     0.001     0.427      11.229   -2.028
                       v_oracle                       0.392     0.273     2.014      33.546   -5.100
