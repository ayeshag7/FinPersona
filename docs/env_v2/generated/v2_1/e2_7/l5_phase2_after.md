# L5 observables oracle vs true-V oracle

Training seeds 500..539 (disjoint from evaluated seeds 0..49); T = 200; generator config overrides {}; GBT on rendered fields + 5 lags -> x_hat; policy = mandate-conditional rule on x_hat. The gap is a LOWER bound on what observables allow (this model class), i.e. an UPPER bound on the information withheld.

## Per-phase OOS R2 / sign accuracy of x_hat on the training pool

- full: calm: R2 0.38, sign 0.90; event: R2 0.80, sign 0.93; resolution: R2 0.67, sign 0.98
- price_only: calm: R2 0.26, sign 0.91; event: R2 0.61, sign 0.87; resolution: R2 -0.21, sign 0.82
- level_free: calm: R2 0.40, sign 0.90; event: R2 0.63, sign 0.86; resolution: R2 -0.27, sign 0.82

## Withheld-information gap (MCR at theta 0.05; lower MCR is better)

persona       scenario         L5  MCR_L5  MCR_true_oracle  withheld_info_gap
   ENTJ      bull_trap       full   0.037            0.003              0.034
   ENTJ      bull_trap price_only   0.045            0.003              0.042
   ENTJ      bull_trap level_free   0.056            0.003              0.053
   ENTJ          crash       full   0.023            0.000              0.023
   ENTJ          crash price_only   0.030            0.000              0.029
   ENTJ          crash level_free   0.028            0.000              0.027
   ENTJ           flat       full   0.074            0.001              0.073
   ENTJ           flat price_only   0.072            0.001              0.071
   ENTJ           flat level_free   0.074            0.001              0.073
   ENTJ sustained_bull       full   0.085            0.001              0.085
   ENTJ sustained_bull price_only   0.088            0.001              0.087
   ENTJ sustained_bull level_free   0.098            0.001              0.097
   INTJ      bull_trap       full   0.038            0.003              0.035
   INTJ      bull_trap price_only   0.045            0.003              0.042
   INTJ      bull_trap level_free   0.056            0.003              0.053
   INTJ          crash       full   0.026            0.003              0.022
   INTJ          crash price_only   0.032            0.003              0.029
   INTJ          crash level_free   0.030            0.003              0.027
   INTJ           flat       full   0.075            0.003              0.072
   INTJ           flat price_only   0.073            0.003              0.070
   INTJ           flat level_free   0.074            0.003              0.072
   INTJ sustained_bull       full   0.085            0.001              0.084
   INTJ sustained_bull price_only   0.087            0.001              0.086
   INTJ sustained_bull level_free   0.097            0.001              0.096
   ISFJ      bull_trap       full   0.038            0.003              0.034
   ISFJ      bull_trap price_only   0.045            0.003              0.042
   ISFJ      bull_trap level_free   0.057            0.003              0.053
   ISFJ          crash       full   0.026            0.003              0.022
   ISFJ          crash price_only   0.032            0.003              0.029
   ISFJ          crash level_free   0.030            0.003              0.027
   ISFJ           flat       full   0.075            0.003              0.072
   ISFJ           flat price_only   0.073            0.003              0.071
   ISFJ           flat level_free   0.075            0.003              0.072
   ISFJ sustained_bull       full   0.086            0.002              0.085
   ISFJ sustained_bull price_only   0.088            0.002              0.086
   ISFJ sustained_bull level_free   0.098            0.002              0.097

## Policy means per persona x scenario

                                                   mcr_0.05  band_mas  turnover  return_pct  mdd_pct
persona scenario       policy                                                                       
ENTJ    bull_trap      L5_full                        0.037     0.001     1.045      25.774  -31.994
                       L5_level_free                  0.056     0.001     1.077      25.796  -32.449
                       L5_price_only                  0.045     0.001     0.979      25.553  -32.229
                       always_hold                    0.113     0.000     0.000      19.933  -33.706
                       constant_mix                   0.101     0.000     0.232      21.715  -33.397
                       mandate_conditional_oracle     0.003     0.001     1.208      27.391  -31.371
                       v_oracle                       0.680     0.509     4.791      42.514  -17.330
        crash          L5_full                        0.023     0.000     0.383     -17.770  -40.104
                       L5_level_free                  0.028     0.000     0.371     -18.349  -40.645
                       L5_price_only                  0.030     0.000     0.401     -18.719  -40.755
                       always_hold                    0.128     0.000     0.000     -18.704  -38.766
                       constant_mix                   0.101     0.000     0.076     -18.536  -39.227
                       mandate_conditional_oracle     0.000     0.000     0.480     -16.952  -39.903
                       v_oracle                       0.085     0.163     2.326      -2.061  -30.742
        flat           L5_full                        0.074     0.001     0.301       5.163  -19.710
                       L5_level_free                  0.074     0.000     0.236       5.021  -20.159
                       L5_price_only                  0.072     0.001     0.324       5.214  -20.182
                       always_hold                    0.107     0.000     0.000       4.262  -20.325
                       constant_mix                   0.102     0.000     0.047       4.422  -20.290
                       mandate_conditional_oracle     0.001     0.001     0.488       7.112  -19.661
                       v_oracle                       0.396     0.314     2.283      15.178  -15.005
        sustained_bull L5_full                        0.085     0.001     0.298      48.206  -10.359
                       L5_level_free                  0.098     0.001     0.237      47.674  -10.409
                       L5_price_only                  0.088     0.001     0.303      48.290  -10.556
                       always_hold                    0.104     0.000     0.000      51.631  -11.190
                       constant_mix                   0.103     0.000     0.059      50.723  -10.966
                       mandate_conditional_oracle     0.001     0.000     0.351      53.856  -10.891
                       v_oracle                       0.394     0.230     1.606      46.865   -9.539
INTJ    bull_trap      L5_full                        0.038     0.001     1.722      21.495  -18.877
                       L5_level_free                  0.056     0.001     1.768      21.417  -19.280
                       L5_price_only                  0.045     0.001     1.639      21.101  -18.996
                       always_hold                    0.140     0.003     0.000      11.074  -21.752
                       constant_mix                   0.100     0.000     1.068      17.192  -20.261
                       mandate_conditional_oracle     0.003     0.001     1.775      22.395  -18.077
                       v_oracle                       0.400     0.336     4.711      41.539  -15.926
        crash          L5_full                        0.026     0.001     0.776      -8.997  -24.820
                       L5_level_free                  0.030     0.001     0.772      -9.599  -25.482
                       L5_price_only                  0.032     0.001     0.800      -9.951  -25.639
                       always_hold                    0.166     0.003     0.000     -10.391  -22.386
                       constant_mix                   0.100     0.000     0.458      -9.947  -23.797
                       mandate_conditional_oracle     0.003     0.001     0.821      -7.806  -24.452
                       v_oracle                       0.400     0.324     2.418      -0.132  -29.158
        flat           L5_full                        0.075     0.001     0.530       3.523  -11.108
                       L5_level_free                  0.074     0.001     0.479       3.424  -11.556
                       L5_price_only                  0.073     0.001     0.571       3.649  -11.636
                       always_hold                    0.119     0.000     0.000       2.368  -11.849
                       constant_mix                   0.101     0.000     0.324       2.847  -11.686
                       mandate_conditional_oracle     0.003     0.001     0.631       5.450  -11.038
                       v_oracle                       0.400     0.309     2.373      16.777  -12.250
        sustained_bull L5_full                        0.085     0.001     0.501      24.029   -5.576
                       L5_level_free                  0.097     0.001     0.451      23.599   -5.646
                       L5_price_only                  0.087     0.001     0.519      24.174   -5.803
                       always_hold                    0.115     0.003     0.000      28.684   -6.975
                       constant_mix                   0.102     0.000     0.361      26.218   -6.176
                       mandate_conditional_oracle     0.001     0.001     0.433      29.232   -6.322
                       v_oracle                       0.400     0.246     1.611      39.201   -7.475
ISFJ    bull_trap      L5_full                        0.038     0.001     1.123      12.221   -7.630
                       L5_level_free                  0.057     0.001     1.179      12.172   -7.975
                       L5_price_only                  0.045     0.001     1.036      11.735   -7.708
                       always_hold                    0.128     0.001     0.000       4.430  -10.331
                       constant_mix                   0.101     0.000     0.521       8.223   -8.694
                       mandate_conditional_oracle     0.003     0.002     1.146      12.299   -6.787
                       v_oracle                       0.190     0.206     4.651      40.808  -14.928
        crash          L5_full                        0.026     0.001     0.626      -2.809  -11.456
                       L5_level_free                  0.030     0.001     0.626      -3.417  -12.143
                       L5_price_only                  0.032     0.001     0.654      -3.755  -12.322
                       always_hold                    0.138     0.000     0.000      -4.156   -9.246
                       constant_mix                   0.100     0.000     0.233      -3.820  -10.146
                       mandate_conditional_oracle     0.003     0.002     0.735      -1.416  -11.007
                       v_oracle                       0.636     0.444     2.487       1.314  -28.251
        flat           L5_full                        0.075     0.001     0.344       1.862   -4.329
                       L5_level_free                  0.075     0.001     0.302       1.795   -4.781
                       L5_price_only                  0.073     0.001     0.396       2.007   -4.905
                       always_hold                    0.112     0.000     0.000       0.947   -4.943
                       constant_mix                   0.102     0.000     0.142       1.214   -4.800
                       mandate_conditional_oracle     0.003     0.001     0.545       3.847   -4.383
                       v_oracle                       0.403     0.306     2.441      17.976  -10.560
        sustained_bull L5_full                        0.086     0.001     0.247       7.928   -1.999
                       L5_level_free                  0.098     0.001     0.188       7.526   -2.079
                       L5_price_only                  0.088     0.001     0.268       8.062   -2.246
                       always_hold                    0.109     0.001     0.000      11.474   -3.112
                       constant_mix                   0.103     0.000     0.139       9.863   -2.509
                       mandate_conditional_oracle     0.002     0.001     0.359      12.260   -2.709
                       v_oracle                       0.404     0.258     1.616      33.454   -6.299
