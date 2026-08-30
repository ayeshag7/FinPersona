# L5 observables oracle vs true-V oracle

Training seeds 500..539 (disjoint from evaluated seeds 0..49); T = 200; generator config overrides {}; GBT on rendered fields + 5 lags -> x_hat; policy = mandate-conditional rule on x_hat. The gap is a LOWER bound on what observables allow (this model class), i.e. an UPPER bound on the information withheld.

## Per-phase OOS R2 / sign accuracy of x_hat on the training pool

- full: calm: R2 0.84, sign 0.95; event: R2 0.95, sign 0.98; resolution: R2 0.94, sign 0.98
- price_only: calm: R2 0.45, sign 0.84; event: R2 0.78, sign 0.90; resolution: R2 0.71, sign 0.95
- level_free: calm: R2 0.34, sign 0.80; event: R2 0.74, sign 0.86; resolution: R2 0.39, sign 0.87

## Withheld-information gap (MCR at theta 0.05; lower MCR is better)

persona       scenario         L5  MCR_L5  MCR_true_oracle  withheld_info_gap
   ENTJ      bull_trap       full   0.029            0.003              0.026
   ENTJ      bull_trap price_only   0.044            0.003              0.041
   ENTJ      bull_trap level_free   0.051            0.003              0.048
   ENTJ          crash       full   0.026            0.001              0.025
   ENTJ          crash price_only   0.042            0.001              0.041
   ENTJ          crash level_free   0.052            0.001              0.051
   ENTJ           flat       full   0.044            0.002              0.042
   ENTJ           flat price_only   0.077            0.002              0.075
   ENTJ           flat level_free   0.083            0.002              0.081
   ENTJ sustained_bull       full   0.068            0.001              0.067
   ENTJ sustained_bull price_only   0.089            0.001              0.088
   ENTJ sustained_bull level_free   0.067            0.001              0.066
   INTJ      bull_trap       full   0.030            0.003              0.026
   INTJ      bull_trap price_only   0.044            0.003              0.041
   INTJ      bull_trap level_free   0.051            0.003              0.048
   INTJ          crash       full   0.028            0.003              0.025
   INTJ          crash price_only   0.044            0.003              0.041
   INTJ          crash level_free   0.054            0.003              0.051
   INTJ           flat       full   0.045            0.003              0.041
   INTJ           flat price_only   0.078            0.003              0.074
   INTJ           flat level_free   0.084            0.003              0.081
   INTJ sustained_bull       full   0.068            0.002              0.066
   INTJ sustained_bull price_only   0.089            0.002              0.087
   INTJ sustained_bull level_free   0.068            0.002              0.065
   ISFJ      bull_trap       full   0.030            0.004              0.026
   ISFJ      bull_trap price_only   0.044            0.004              0.041
   ISFJ      bull_trap level_free   0.051            0.004              0.048
   ISFJ          crash       full   0.028            0.003              0.025
   ISFJ          crash price_only   0.044            0.003              0.041
   ISFJ          crash level_free   0.054            0.003              0.051
   ISFJ           flat       full   0.045            0.003              0.041
   ISFJ           flat price_only   0.078            0.003              0.074
   ISFJ           flat level_free   0.084            0.003              0.081
   ISFJ sustained_bull       full   0.068            0.002              0.066
   ISFJ sustained_bull price_only   0.090            0.002              0.088
   ISFJ sustained_bull level_free   0.068            0.002              0.066

## Policy means per persona x scenario

                                                   mcr_0.05  band_mas  turnover  return_pct  mdd_pct
persona scenario       policy                                                                       
ENTJ    bull_trap      L5_full                        0.029     0.001     0.576      58.917  -25.550
                       L5_level_free                  0.051     0.001     1.040      58.200  -25.992
                       L5_price_only                  0.044     0.001     0.752      58.102  -25.804
                       always_hold                    0.116     0.000     0.000      68.213  -27.215
                       constant_mix                   0.102     0.000     0.140      65.920  -26.834
                       mandate_conditional_oracle     0.003     0.001     0.587      60.478  -25.406
                       v_oracle                       0.618     0.566     1.863      12.223   -9.267
        crash          L5_full                        0.026     0.001     0.370     -28.520  -48.616
                       L5_level_free                  0.052     0.001     0.736     -28.960  -49.091
                       L5_price_only                  0.042     0.001     0.558     -28.219  -48.449
                       always_hold                    0.125     0.000     0.000     -27.931  -46.316
                       constant_mix                   0.100     0.000     0.079     -28.086  -47.179
                       mandate_conditional_oracle     0.001     0.001     0.353     -27.494  -47.935
                       v_oracle                       0.253     0.271     1.789     -11.349  -34.178
        flat           L5_full                        0.044     0.001     0.380       4.472  -18.924
                       L5_level_free                  0.083     0.001     0.954       4.077  -19.622
                       L5_price_only                  0.077     0.001     0.619       3.995  -18.898
                       always_hold                    0.103     0.000     0.000       3.664  -19.410
                       constant_mix                   0.100     0.000     0.040       3.789  -19.391
                       mandate_conditional_oracle     0.002     0.001     0.297       5.070  -18.715
                       v_oracle                       0.495     0.464     1.366       8.615   -9.455
        sustained_bull L5_full                        0.068     0.001     0.372      42.584   -8.216
                       L5_level_free                  0.067     0.001     0.764      42.442   -8.326
                       L5_price_only                  0.089     0.001     0.348      39.810   -7.989
                       always_hold                    0.105     0.000     0.000      44.484   -8.882
                       constant_mix                   0.103     0.000     0.043      43.818   -8.718
                       mandate_conditional_oracle     0.001     0.000     0.422      47.043   -8.482
                       v_oracle                       0.411     0.272     1.959      42.718   -7.123
INTJ    bull_trap      L5_full                        0.030     0.001     0.773      26.093  -14.620
                       L5_level_free                  0.051     0.001     1.215      25.537  -15.207
                       L5_price_only                  0.044     0.001     0.947      25.446  -14.938
                       always_hold                    0.154     0.011     0.000      37.896  -17.707
                       constant_mix                   0.101     0.000     0.478      31.086  -16.135
                       mandate_conditional_oracle     0.003     0.001     0.774      27.117  -14.441
                       v_oracle                       0.400     0.391     1.767      12.392   -9.045
        crash          L5_full                        0.028     0.002     0.698     -16.375  -31.307
                       L5_level_free                  0.054     0.002     1.083     -16.994  -32.017
                       L5_price_only                  0.044     0.002     0.874     -16.299  -31.221
                       always_hold                    0.155     0.010     0.000     -15.517  -26.800
                       constant_mix                   0.100     0.000     0.388     -16.257  -29.605
                       mandate_conditional_oracle     0.003     0.002     0.675     -15.107  -30.377
                       v_oracle                       0.400     0.392     1.676     -11.250  -34.138
        flat           L5_full                        0.045     0.002     0.531       2.994  -10.777
                       L5_level_free                  0.084     0.001     1.114       2.598  -11.553
                       L5_price_only                  0.078     0.002     0.769       2.529  -10.760
                       always_hold                    0.110     0.000     0.000       2.036  -11.313
                       constant_mix                   0.100     0.000     0.228       2.281  -11.245
                       mandate_conditional_oracle     0.003     0.002     0.446       3.575  -10.539
                       v_oracle                       0.400     0.392     1.253       8.728   -9.303
        sustained_bull L5_full                        0.068     0.001     0.498      21.717   -4.460
                       L5_level_free                  0.068     0.001     0.856      21.569   -4.571
                       L5_price_only                  0.089     0.001     0.459      19.285   -4.202
                       always_hold                    0.115     0.001     0.000      24.714   -5.506
                       constant_mix                   0.102     0.000     0.237      22.766   -4.898
                       mandate_conditional_oracle     0.002     0.001     0.500      25.896   -4.816
                       v_oracle                       0.400     0.273     1.991      37.477   -5.840
ISFJ    bull_trap      L5_full                        0.030     0.001     0.485       7.342   -5.214
                       L5_level_free                  0.051     0.001     0.933       6.891   -5.901
                       L5_price_only                  0.044     0.001     0.666       6.805   -5.606
                       always_hold                    0.141     0.006     0.000      15.158   -8.376
                       constant_mix                   0.101     0.000     0.247      11.225   -6.825
                       mandate_conditional_oracle     0.004     0.002     0.493       8.121   -4.938
                       v_oracle                       0.237     0.260     1.695      12.519   -8.939
        crash          L5_full                        0.028     0.002     0.614      -6.536  -14.936
                       L5_level_free                  0.054     0.001     1.020      -7.316  -15.963
                       L5_price_only                  0.044     0.002     0.777      -6.658  -15.010
                       always_hold                    0.131     0.000     0.000      -6.207  -11.089
                       constant_mix                   0.100     0.000     0.221      -6.586  -12.923
                       mandate_conditional_oracle     0.003     0.002     0.589      -5.118  -13.784
                       v_oracle                       0.510     0.482     1.592     -11.175  -34.116
        flat           L5_full                        0.045     0.002     0.409       1.676   -4.310
                       L5_level_free                  0.084     0.001     1.008       1.300   -5.141
                       L5_price_only                  0.078     0.001     0.647       1.237   -4.356
                       always_hold                    0.106     0.000     0.000       0.814   -4.722
                       constant_mix                   0.100     0.000     0.109       0.981   -4.624
                       mandate_conditional_oracle     0.003     0.002     0.334       2.256   -3.974
                       v_oracle                       0.329     0.338     1.168       8.813   -9.202
        sustained_bull L5_full                        0.068     0.001     0.341       7.726   -1.689
                       L5_level_free                  0.068     0.001     0.679       7.606   -1.824
                       L5_price_only                  0.090     0.001     0.292       5.560   -1.417
                       always_hold                    0.110     0.000     0.000       9.885   -2.431
                       constant_mix                   0.103     0.000     0.104       8.674   -1.978
                       mandate_conditional_oracle     0.002     0.001     0.427      11.229   -2.028
                       v_oracle                       0.392     0.273     2.014      33.546   -5.100
