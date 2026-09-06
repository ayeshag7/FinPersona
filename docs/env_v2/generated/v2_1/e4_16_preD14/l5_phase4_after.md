# L5 observables oracle vs true-V oracle

Training seeds 500..539 (disjoint from evaluated seeds 0..49); T = 200; generator config overrides {}; GBT on rendered fields + 5 lags -> x_hat; policy = mandate-conditional rule on x_hat. The gap is a LOWER bound on what observables allow (this model class), i.e. an UPPER bound on the information withheld.

## Per-phase OOS R2 / sign accuracy of x_hat on the training pool

- full: calm: R2 0.45, sign 0.89; event: R2 0.87, sign 0.97; resolution: R2 0.90, sign 0.99
- price_only: calm: R2 -0.22, sign 0.87; event: R2 0.61, sign 0.91; resolution: R2 0.69, sign 0.95
- level_free: calm: R2 -0.09, sign 0.81; event: R2 0.59, sign 0.89; resolution: R2 0.58, sign 0.92

## Withheld-information gap (MCR at theta 0.05; lower MCR is better)

persona       scenario         L5  MCR_L5  MCR_true_oracle  withheld_info_gap
   ENTJ      bull_trap       full   0.032            0.003              0.029
   ENTJ      bull_trap price_only   0.037            0.003              0.034
   ENTJ      bull_trap level_free   0.037            0.003              0.034
   ENTJ          crash       full   0.037            0.001              0.036
   ENTJ          crash price_only   0.048            0.001              0.047
   ENTJ          crash level_free   0.044            0.001              0.043
   ENTJ           flat       full   0.056            0.002              0.054
   ENTJ           flat price_only   0.059            0.002              0.057
   ENTJ           flat level_free   0.056            0.002              0.054
   ENTJ sustained_bull       full   0.082            0.001              0.081
   ENTJ sustained_bull price_only   0.069            0.001              0.068
   ENTJ sustained_bull level_free   0.085            0.001              0.084
   INTJ      bull_trap       full   0.032            0.003              0.029
   INTJ      bull_trap price_only   0.038            0.003              0.034
   INTJ      bull_trap level_free   0.037            0.003              0.034
   INTJ          crash       full   0.038            0.003              0.035
   INTJ          crash price_only   0.050            0.003              0.047
   INTJ          crash level_free   0.045            0.003              0.042
   INTJ           flat       full   0.057            0.003              0.053
   INTJ           flat price_only   0.059            0.003              0.056
   INTJ           flat level_free   0.056            0.003              0.053
   INTJ sustained_bull       full   0.082            0.002              0.080
   INTJ sustained_bull price_only   0.069            0.002              0.067
   INTJ sustained_bull level_free   0.085            0.002              0.083
   ISFJ      bull_trap       full   0.032            0.003              0.029
   ISFJ      bull_trap price_only   0.038            0.003              0.034
   ISFJ      bull_trap level_free   0.038            0.003              0.034
   ISFJ          crash       full   0.039            0.003              0.035
   ISFJ          crash price_only   0.050            0.003              0.047
   ISFJ          crash level_free   0.045            0.003              0.042
   ISFJ           flat       full   0.057            0.003              0.054
   ISFJ           flat price_only   0.059            0.003              0.056
   ISFJ           flat level_free   0.057            0.003              0.053
   ISFJ sustained_bull       full   0.082            0.002              0.081
   ISFJ sustained_bull price_only   0.070            0.002              0.068
   ISFJ sustained_bull level_free   0.085            0.002              0.083

## Policy means per persona x scenario

                                                   mcr_0.05  band_mas  turnover  return_pct  mdd_pct
persona scenario       policy                                                                       
ENTJ    bull_trap      L5_full                        0.032     0.001     0.487      39.959  -20.182
                       L5_level_free                  0.037     0.001     0.518      39.149  -20.639
                       L5_price_only                  0.037     0.001     0.674      40.586  -20.624
                       always_hold                    0.116     0.000     0.000      43.504  -21.056
                       constant_mix                   0.101     0.000     0.106      43.001  -20.932
                       mandate_conditional_oracle     0.003     0.001     0.643      41.721  -19.985
                       v_oracle                       0.695     0.571     2.339      15.790  -12.160
        crash          L5_full                        0.037     0.000     0.683     -17.516  -49.679
                       L5_level_free                  0.044     0.000     0.894     -17.977  -49.977
                       L5_price_only                  0.048     0.001     0.969     -16.903  -49.567
                       always_hold                    0.127     0.000     0.000     -20.124  -47.959
                       constant_mix                   0.101     0.000     0.166     -19.262  -48.659
                       mandate_conditional_oracle     0.001     0.001     0.986     -14.611  -48.416
                       v_oracle                       0.246     0.289     5.636      23.098  -35.757
        flat           L5_full                        0.056     0.001     0.459       6.062  -24.385
                       L5_level_free                  0.056     0.001     0.416       5.322  -24.553
                       L5_price_only                  0.059     0.001     0.558       5.858  -24.497
                       always_hold                    0.108     0.000     0.000       5.007  -24.985
                       constant_mix                   0.101     0.000     0.070       5.204  -24.955
                       mandate_conditional_oracle     0.002     0.001     0.615       7.942  -24.380
                       v_oracle                       0.483     0.413     2.914      17.174  -15.940
        sustained_bull L5_full                        0.082     0.001     0.373      50.831  -12.476
                       L5_level_free                  0.085     0.001     0.295      49.178  -12.050
                       L5_price_only                  0.069     0.001     0.434      50.218  -12.212
                       always_hold                    0.109     0.000     0.000      55.551  -13.212
                       constant_mix                   0.103     0.000     0.069      54.485  -12.968
                       mandate_conditional_oracle     0.001     0.000     0.431      57.059  -12.767
                       v_oracle                       0.470     0.297     1.981      45.753  -11.098
INTJ    bull_trap      L5_full                        0.032     0.001     0.790      19.878  -11.338
                       L5_level_free                  0.037     0.001     0.827      19.323  -11.905
                       L5_price_only                  0.038     0.001     0.984      20.584  -11.860
                       always_hold                    0.150     0.004     0.000      24.169  -12.707
                       constant_mix                   0.100     0.000     0.555      22.552  -12.123
                       mandate_conditional_oracle     0.003     0.002     0.906      21.352  -11.137
                       v_oracle                       0.400     0.379     2.327      16.297  -11.275
        crash          L5_full                        0.038     0.001     1.478      -6.232  -31.349
                       L5_level_free                  0.045     0.001     1.723      -6.624  -31.663
                       L5_price_only                  0.050     0.001     1.789      -5.436  -31.292
                       always_hold                    0.161     0.008     0.000     -11.180  -27.922
                       constant_mix                   0.100     0.000     0.906      -8.729  -30.021
                       mandate_conditional_oracle     0.003     0.001     1.752      -2.724  -29.550
                       v_oracle                       0.400     0.372     5.631      24.063  -35.339
        flat           L5_full                        0.057     0.001     0.747       4.077  -13.927
                       L5_level_free                  0.056     0.001     0.706       3.410  -14.153
                       L5_price_only                  0.059     0.001     0.839       3.928  -14.092
                       always_hold                    0.124     0.000     0.000       2.782  -14.684
                       constant_mix                   0.100     0.000     0.424       3.252  -14.513
                       mandate_conditional_oracle     0.003     0.002     0.854       5.998  -13.883
                       v_oracle                       0.400     0.371     2.888      17.752  -15.169
        sustained_bull L5_full                        0.082     0.001     0.584      24.882   -6.868
                       L5_level_free                  0.085     0.001     0.488      23.394   -6.410
                       L5_price_only                  0.069     0.001     0.622      24.299   -6.599
                       always_hold                    0.131     0.005     0.000      30.862   -8.224
                       constant_mix                   0.102     0.000     0.405      27.922   -7.343
                       mandate_conditional_oracle     0.002     0.001     0.512      30.624   -7.320
                       v_oracle                       0.400     0.244     1.912      37.960   -8.359
ISFJ    bull_trap      L5_full                        0.032     0.001     0.436       6.259   -4.363
                       L5_level_free                  0.038     0.001     0.487       5.837   -4.961
                       L5_price_only                  0.038     0.001     0.649       7.004   -4.928
                       always_hold                    0.136     0.001     0.000       9.668   -5.514
                       constant_mix                   0.101     0.000     0.251       8.631   -4.988
                       mandate_conditional_oracle     0.003     0.002     0.588       7.548   -4.160
                       v_oracle                       0.179     0.236     2.318      16.678  -10.773
        crash          L5_full                        0.039     0.001     1.241       0.193  -14.947
                       L5_level_free                  0.045     0.001     1.505      -0.156  -15.189
                       L5_price_only                  0.050     0.001     1.553       1.049  -14.950
                       always_hold                    0.134     0.000     0.000      -4.472  -11.618
                       constant_mix                   0.100     0.000     0.501      -2.791  -12.906
                       mandate_conditional_oracle     0.003     0.002     1.560       4.021  -13.108
                       v_oracle                       0.515     0.434     5.626      24.787  -35.103
        flat           L5_full                        0.057     0.001     0.518       2.206   -5.570
                       L5_level_free                  0.057     0.001     0.473       1.572   -5.807
                       L5_price_only                  0.059     0.001     0.618       2.115   -5.797
                       always_hold                    0.116     0.000     0.000       1.113   -6.166
                       constant_mix                   0.101     0.000     0.191       1.396   -5.994
                       mandate_conditional_oracle     0.003     0.002     0.703       4.160   -5.547
                       v_oracle                       0.338     0.340     2.868      18.186  -14.754
        sustained_bull L5_full                        0.082     0.001     0.308       7.887   -2.601
                       L5_level_free                  0.085     0.001     0.198       6.521   -2.162
                       L5_price_only                  0.070     0.001     0.333       7.320   -2.401
                       always_hold                    0.122     0.001     0.000      12.345   -3.666
                       constant_mix                   0.103     0.000     0.175      10.527   -2.985
                       mandate_conditional_oracle     0.002     0.001     0.413      12.427   -3.029
                       v_oracle                       0.347     0.204     1.861      32.115   -6.603
