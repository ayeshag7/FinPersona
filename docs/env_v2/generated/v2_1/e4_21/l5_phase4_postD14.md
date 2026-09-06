# L5 observables oracle vs true-V oracle

Training seeds 500..539 (disjoint from evaluated seeds 0..49); T = 200; generator config overrides {}; GBT on rendered fields + 5 lags -> x_hat; policy = mandate-conditional rule on x_hat. The gap is a LOWER bound on what observables allow (this model class), i.e. an UPPER bound on the information withheld.

## Per-phase OOS R2 / sign accuracy of x_hat on the training pool

- full: calm: R2 0.35, sign 0.84; event: R2 0.81, sign 0.94; resolution: R2 0.71, sign 0.93
- price_only: calm: R2 -0.06, sign 0.81; event: R2 0.54, sign 0.87; resolution: R2 0.23, sign 0.80
- level_free: calm: R2 -0.03, sign 0.77; event: R2 0.51, sign 0.86; resolution: R2 0.25, sign 0.81

## Withheld-information gap (MCR at theta 0.05; lower MCR is better)

persona       scenario         L5  MCR_L5  MCR_true_oracle  withheld_info_gap
   ENTJ      bull_trap       full   0.032            0.003              0.029
   ENTJ      bull_trap price_only   0.045            0.003              0.042
   ENTJ      bull_trap level_free   0.041            0.003              0.038
   ENTJ          crash       full   0.034            0.001              0.033
   ENTJ          crash price_only   0.045            0.001              0.044
   ENTJ          crash level_free   0.042            0.001              0.041
   ENTJ           flat       full   0.057            0.002              0.055
   ENTJ           flat price_only   0.058            0.002              0.056
   ENTJ           flat level_free   0.055            0.002              0.053
   ENTJ sustained_bull       full   0.067            0.002              0.065
   ENTJ sustained_bull price_only   0.063            0.002              0.061
   ENTJ sustained_bull level_free   0.063            0.002              0.061
   INTJ      bull_trap       full   0.033            0.003              0.029
   INTJ      bull_trap price_only   0.045            0.003              0.041
   INTJ      bull_trap level_free   0.041            0.003              0.038
   INTJ          crash       full   0.036            0.003              0.033
   INTJ          crash price_only   0.046            0.003              0.044
   INTJ          crash level_free   0.043            0.003              0.040
   INTJ           flat       full   0.058            0.003              0.054
   INTJ           flat price_only   0.058            0.003              0.055
   INTJ           flat level_free   0.056            0.003              0.053
   INTJ sustained_bull       full   0.067            0.003              0.064
   INTJ sustained_bull price_only   0.064            0.003              0.061
   INTJ sustained_bull level_free   0.064            0.003              0.060
   ISFJ      bull_trap       full   0.033            0.003              0.029
   ISFJ      bull_trap price_only   0.045            0.003              0.042
   ISFJ      bull_trap level_free   0.041            0.003              0.038
   ISFJ          crash       full   0.036            0.003              0.033
   ISFJ          crash price_only   0.047            0.003              0.044
   ISFJ          crash level_free   0.044            0.003              0.040
   ISFJ           flat       full   0.058            0.003              0.055
   ISFJ           flat price_only   0.059            0.003              0.055
   ISFJ           flat level_free   0.056            0.003              0.053
   ISFJ sustained_bull       full   0.068            0.003              0.064
   ISFJ sustained_bull price_only   0.064            0.003              0.061
   ISFJ sustained_bull level_free   0.064            0.003              0.061

## Policy means per persona x scenario

                                                   mcr_0.05  band_mas  turnover  return_pct  mdd_pct
persona scenario       policy                                                                       
ENTJ    bull_trap      L5_full                        0.032     0.001     0.537      40.452  -20.372
                       L5_level_free                  0.041     0.001     0.626      40.185  -20.646
                       L5_price_only                  0.045     0.001     0.720      41.276  -20.736
                       always_hold                    0.116     0.000     0.000      43.504  -21.056
                       constant_mix                   0.101     0.000     0.106      43.001  -20.932
                       mandate_conditional_oracle     0.003     0.001     0.643      41.721  -19.985
                       v_oracle                       0.695     0.571     2.339      15.790  -12.160
        crash          L5_full                        0.034     0.000     0.666     -17.921  -49.919
                       L5_level_free                  0.042     0.000     0.765     -19.029  -50.353
                       L5_price_only                  0.045     0.001     0.816     -17.826  -49.898
                       always_hold                    0.127     0.000     0.000     -20.124  -47.959
                       constant_mix                   0.101     0.000     0.166     -19.262  -48.659
                       mandate_conditional_oracle     0.001     0.001     0.986     -14.611  -48.416
                       v_oracle                       0.246     0.289     5.636      23.098  -35.757
        flat           L5_full                        0.057     0.001     0.470       6.155  -24.647
                       L5_level_free                  0.055     0.001     0.420       5.708  -24.620
                       L5_price_only                  0.058     0.001     0.551       5.636  -24.924
                       always_hold                    0.108     0.000     0.000       5.007  -24.985
                       constant_mix                   0.101     0.000     0.070       5.204  -24.955
                       mandate_conditional_oracle     0.002     0.001     0.615       7.942  -24.380
                       v_oracle                       0.483     0.413     2.914      17.174  -15.940
        sustained_bull L5_full                        0.067     0.001     0.588      50.719  -16.949
                       L5_level_free                  0.063     0.001     0.438      49.617  -16.541
                       L5_price_only                  0.063     0.001     0.616      50.143  -16.859
                       always_hold                    0.110     0.000     0.000      54.296  -17.843
                       constant_mix                   0.101     0.000     0.088      53.385  -17.520
                       mandate_conditional_oracle     0.002     0.001     0.680      56.249  -16.971
                       v_oracle                       0.503     0.454     2.921      41.307  -11.405
INTJ    bull_trap      L5_full                        0.033     0.001     0.842      20.297  -11.539
                       L5_level_free                  0.041     0.001     0.934      20.248  -11.898
                       L5_price_only                  0.045     0.001     1.029      21.112  -11.972
                       always_hold                    0.150     0.004     0.000      24.169  -12.707
                       constant_mix                   0.100     0.000     0.555      22.552  -12.123
                       mandate_conditional_oracle     0.003     0.002     0.906      21.352  -11.137
                       v_oracle                       0.400     0.379     2.327      16.297  -11.275
        crash          L5_full                        0.036     0.001     1.457      -6.590  -31.588
                       L5_level_free                  0.043     0.001     1.573      -7.776  -32.124
                       L5_price_only                  0.046     0.001     1.633      -6.313  -31.591
                       always_hold                    0.161     0.008     0.000     -11.180  -27.922
                       constant_mix                   0.100     0.000     0.906      -8.729  -30.021
                       mandate_conditional_oracle     0.003     0.001     1.752      -2.724  -29.550
                       v_oracle                       0.400     0.372     5.631      24.063  -35.339
        flat           L5_full                        0.058     0.001     0.760       4.146  -14.220
                       L5_level_free                  0.056     0.001     0.712       3.774  -14.245
                       L5_price_only                  0.058     0.001     0.840       3.713  -14.547
                       always_hold                    0.124     0.000     0.000       2.782  -14.684
                       constant_mix                   0.100     0.000     0.424       3.252  -14.513
                       mandate_conditional_oracle     0.003     0.002     0.854       5.998  -13.883
                       v_oracle                       0.400     0.371     2.888      17.752  -15.169
        sustained_bull L5_full                        0.067     0.001     0.820      25.220   -9.472
                       L5_level_free                  0.064     0.001     0.671      24.345   -9.096
                       L5_price_only                  0.064     0.001     0.837      24.748   -9.388
                       always_hold                    0.136     0.006     0.000      30.165  -11.154
                       constant_mix                   0.101     0.000     0.460      27.478  -10.027
                       mandate_conditional_oracle     0.003     0.001     0.896      29.996   -9.545
                       v_oracle                       0.400     0.367     2.841      39.957  -10.819
ISFJ    bull_trap      L5_full                        0.033     0.001     0.496       6.658   -4.538
                       L5_level_free                  0.041     0.001     0.594       6.694   -4.941
                       L5_price_only                  0.045     0.001     0.694       7.412   -5.058
                       always_hold                    0.136     0.001     0.000       9.668   -5.514
                       constant_mix                   0.101     0.000     0.251       8.631   -4.988
                       mandate_conditional_oracle     0.003     0.002     0.588       7.548   -4.160
                       v_oracle                       0.179     0.236     2.318      16.678  -10.773
        crash          L5_full                        0.036     0.001     1.232      -0.102  -15.145
                       L5_level_free                  0.044     0.001     1.359      -1.327  -15.591
                       L5_price_only                  0.047     0.001     1.415       0.231  -15.174
                       always_hold                    0.134     0.000     0.000      -4.472  -11.618
                       constant_mix                   0.100     0.000     0.501      -2.791  -12.906
                       mandate_conditional_oracle     0.003     0.002     1.560       4.021  -13.108
                       v_oracle                       0.515     0.434     5.626      24.787  -35.103
        flat           L5_full                        0.058     0.001     0.540       2.274   -5.854
                       L5_level_free                  0.056     0.001     0.487       1.926   -5.917
                       L5_price_only                  0.059     0.002     0.628       1.909   -6.272
                       always_hold                    0.116     0.000     0.000       1.113   -6.166
                       constant_mix                   0.101     0.000     0.191       1.396   -5.994
                       mandate_conditional_oracle     0.003     0.002     0.703       4.160   -5.547
                       v_oracle                       0.338     0.340     2.868      18.186  -14.754
        sustained_bull L5_full                        0.068     0.001     0.504       8.412   -3.666
                       L5_level_free                  0.064     0.001     0.349       7.639   -3.259
                       L5_price_only                  0.064     0.001     0.519       7.977   -3.655
                       always_hold                    0.125     0.002     0.000      12.066   -4.980
                       constant_mix                   0.101     0.000     0.212      10.429   -4.094
                       mandate_conditional_oracle     0.003     0.001     0.672      12.433   -3.839
                       v_oracle                       0.323     0.303     2.781      38.945  -10.531
