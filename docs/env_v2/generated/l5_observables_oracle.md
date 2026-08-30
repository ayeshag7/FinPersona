# L5 observables oracle vs true-V oracle

Training seeds 500..511 (disjoint from evaluated seeds 0..9); T = 200; GBT on rendered fields + 5 lags -> x_hat; policy = mandate-conditional rule on x_hat. The gap is a LOWER bound on what observables allow (this model class), i.e. an UPPER bound on the information withheld.

## Per-phase OOS R2 / sign accuracy of x_hat on the training pool

- full: calm: R2 0.95, sign 0.99; event: R2 0.97, sign 1.00; resolution: R2 0.93, sign 0.99
- price_only: calm: R2 0.90, sign 0.97; event: R2 0.91, sign 0.98; resolution: R2 0.80, sign 0.98

## Withheld-information gap (MCR at theta 0.05; lower MCR is better)

persona       scenario         L5  MCR_L5  MCR_true_oracle  withheld_info_gap
   ENTJ      bull_trap       full   0.021            0.002              0.019
   ENTJ      bull_trap price_only   0.028            0.002              0.026
   ENTJ          crash       full   0.019            0.001              0.018
   ENTJ          crash price_only   0.028            0.001              0.027
   ENTJ           flat       full   0.033            0.001              0.032
   ENTJ           flat price_only   0.039            0.001              0.038
   ENTJ sustained_bull       full   0.087            0.001              0.086
   ENTJ sustained_bull price_only   0.080            0.001              0.079
   INTJ      bull_trap       full   0.022            0.003              0.018
   INTJ      bull_trap price_only   0.029            0.003              0.026
   INTJ          crash       full   0.021            0.003              0.018
   INTJ          crash price_only   0.030            0.003              0.027
   INTJ           flat       full   0.034            0.003              0.031
   INTJ           flat price_only   0.040            0.003              0.037
   INTJ sustained_bull       full   0.088            0.002              0.085
   INTJ sustained_bull price_only   0.080            0.002              0.078
   ISFJ      bull_trap       full   0.022            0.003              0.019
   ISFJ      bull_trap price_only   0.029            0.003              0.026
   ISFJ          crash       full   0.021            0.003              0.018
   ISFJ          crash price_only   0.030            0.003              0.027
   ISFJ           flat       full   0.035            0.003              0.031
   ISFJ           flat price_only   0.041            0.003              0.037
   ISFJ sustained_bull       full   0.087            0.002              0.086
   ISFJ sustained_bull price_only   0.082            0.002              0.080

## Policy means per persona x scenario

                                                   mcr_0.05  band_mas  turnover  return_pct  mdd_pct
persona scenario       policy                                                                       
ENTJ    bull_trap      L5_full                        0.021     0.001     0.675      60.270  -35.194
                       L5_price_only                  0.028     0.000     0.730      63.518  -34.889
                       always_hold                    0.120     0.000     0.000      66.122  -36.668
                       constant_mix                   0.101     0.000     0.208      65.559  -36.145
                       mandate_conditional_oracle     0.002     0.001     0.649      62.111  -35.186
                       v_oracle                       0.483     0.450     1.710      21.318  -18.454
        crash          L5_full                        0.019     0.000     0.474     -18.725  -47.595
                       L5_price_only                  0.028     0.000     0.432     -19.416  -47.579
                       always_hold                    0.121     0.000     0.000     -20.146  -45.635
                       constant_mix                   0.100     0.000     0.139     -19.216  -46.243
                       mandate_conditional_oracle     0.001     0.000     0.371     -19.444  -48.065
                       v_oracle                       0.175     0.181     1.490      -7.549  -39.228
        flat           L5_full                        0.033     0.001     0.278       8.196  -23.059
                       L5_price_only                  0.039     0.000     0.336       8.293  -23.306
                       always_hold                    0.106     0.000     0.000       6.742  -22.546
                       constant_mix                   0.100     0.000     0.077       7.166  -22.701
                       mandate_conditional_oracle     0.001     0.001     0.198       7.825  -23.479
                       v_oracle                       0.256     0.254     0.737       8.315  -19.480
        sustained_bull L5_full                        0.087     0.001     0.372      39.753   -9.359
                       L5_price_only                  0.080     0.001     0.358      37.335   -9.088
                       always_hold                    0.102     0.000     0.000      40.230  -10.153
                       constant_mix                   0.103     0.000     0.042      39.711   -9.996
                       mandate_conditional_oracle     0.001     0.000     0.373      42.554   -9.324
                       v_oracle                       0.417     0.312     2.013      39.719   -6.437
INTJ    bull_trap      L5_full                        0.022     0.001     1.064      30.356  -21.018
                       L5_price_only                  0.029     0.001     1.113      33.211  -20.637
                       always_hold                    0.161     0.016     0.000      36.734  -24.694
                       constant_mix                   0.101     0.000     0.749      33.863  -22.139
                       mandate_conditional_oracle     0.003     0.002     1.032      31.867  -21.030
                       v_oracle                       0.400     0.396     1.793      21.613  -18.395
        crash          L5_full                        0.021     0.002     1.035      -7.074  -30.275
                       L5_price_only                  0.030     0.001     0.977      -7.877  -30.215
                       always_hold                    0.147     0.007     0.000     -11.192  -26.911
                       constant_mix                   0.100     0.000     0.663      -8.695  -28.763
                       mandate_conditional_oracle     0.003     0.002     0.924      -7.781  -30.792
                       v_oracle                       0.400     0.396     1.580      -7.256  -39.160
        flat           L5_full                        0.034     0.002     0.594       6.136  -14.134
                       L5_price_only                  0.040     0.002     0.634       6.155  -14.479
                       always_hold                    0.112     0.004     0.000       3.746  -13.133
                       constant_mix                   0.099     0.000     0.391       4.807  -13.574
                       mandate_conditional_oracle     0.003     0.002     0.522       5.794  -14.550
                       v_oracle                       0.400     0.396     0.817       8.508  -19.424
        sustained_bull L5_full                        0.088     0.001     0.496      20.797   -5.028
                       L5_price_only                  0.080     0.001     0.467      18.673   -4.760
                       always_hold                    0.107     0.001     0.000      22.350   -6.140
                       constant_mix                   0.101     0.000     0.220      20.759   -5.627
                       mandate_conditional_oracle     0.002     0.001     0.447      23.456   -5.024
                       v_oracle                       0.400     0.314     1.686      33.240   -5.717
ISFJ    bull_trap      L5_full                        0.022     0.001     0.714      10.385   -8.148
                       L5_price_only                  0.029     0.001     0.771      12.795   -7.651
                       always_hold                    0.145     0.008     0.000      14.694  -12.228
                       constant_mix                   0.101     0.000     0.415      12.927   -9.381
                       mandate_conditional_oracle     0.003     0.002     0.690      11.609   -8.125
                       v_oracle                       0.338     0.355     1.855      21.834  -18.395
        crash          L5_full                        0.021     0.002     0.865      -0.587  -14.201
                       L5_price_only                  0.030     0.002     0.811      -1.313  -14.056
                       always_hold                    0.126     0.000     0.000      -4.477  -11.368
                       constant_mix                   0.100     0.000     0.401      -2.744  -12.415
                       mandate_conditional_oracle     0.003     0.002     0.783      -1.299  -14.756
                       v_oracle                       0.569     0.557     1.648      -7.036  -39.160
        flat           L5_full                        0.035     0.002     0.481       3.648   -6.678
                       L5_price_only                  0.041     0.002     0.538       3.725   -7.057
                       always_hold                    0.106     0.000     0.000       1.498   -5.502
                       constant_mix                   0.100     0.000     0.231       2.326   -5.650
                       mandate_conditional_oracle     0.003     0.002     0.428       3.381   -6.964
                       v_oracle                       0.508     0.503     0.877       8.653  -19.424
        sustained_bull L5_full                        0.087     0.001     0.365       7.981   -1.738
                       L5_price_only                  0.082     0.000     0.309       6.046   -1.511
                       always_hold                    0.105     0.000     0.000       8.940   -2.634
                       constant_mix                   0.103     0.000     0.096       7.947   -2.277
                       mandate_conditional_oracle     0.002     0.002     0.385      10.127   -1.939
                       v_oracle                       0.387     0.315     1.441      28.380   -5.298
