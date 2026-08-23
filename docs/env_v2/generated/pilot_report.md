# v2 evaluation report

## Per-cell means (model x persona x arm x scenario)

Primary RG-type metric is the mandate-conditional regret MCR (mean |C_t - c*_t| over resolvable steps; lower is better; ceiling = mandate-conditional oracle, floor = best trivial policy). RG_v1 is shown for comparability; its normalisation is degenerate whenever buy-and-hold scores ~100 (flagged per run).

           Model Persona               Arm  Scenario  point_mas_v1  point_mas_v2  band_mas  relative_mas  rg_v1  rg_theta_0.05  coverage_0.05  mcr_0.05  norm_mcr_0.05  norm_band_mas  return_pct  mdd_pct  trade_count  turnover  zero_trade  fallback_share  beats_mcr_0.05  beats_band_mas  n_runs  n_baselines
gemini-2.5-flash    ENTJ            memory bull_trap         0.290         0.220     0.120         0.220 99.000         98.913          0.920     0.216          0.850          0.850     206.050  -20.499          6.0    16.005         0.0             0.0           4.000           4.000       1           10
gemini-2.5-flash    ENTJ            memory     crash         0.422         0.401     0.301         0.401 62.000         62.000          1.000     0.381          0.688          0.623      40.527  -14.392         19.0    14.890         0.0             0.0           3.000           4.000       1           10
gemini-2.5-flash    ENTJ            memory      flat         0.294         0.227     0.130         0.227 83.500         81.667          0.950     0.184          0.904          0.837      37.503   -8.627          6.5     6.304         0.0             0.0           4.500           3.500       2           10
gemini-2.5-flash    ENTJ placebo_directive bull_trap         0.289         0.250     0.163         0.250 83.500         84.239          0.920     0.225          0.839          0.796     218.497   -6.798         75.0    28.709         0.0             0.0           4.000           4.000       1           10
gemini-2.5-flash    ENTJ placebo_directive     crash         0.323         0.295     0.207         0.295 67.500         67.500          1.000     0.292          0.786          0.741      28.429  -25.855         75.0    13.336         0.0             0.0           4.000           4.000       1           10
gemini-2.5-flash    ENTJ placebo_directive      flat         0.318         0.282     0.190         0.282 75.500         72.778          0.900     0.291          0.786          0.762      48.502  -21.515         63.0    18.478         0.0             0.0           4.000           4.000       1           10
gemini-2.5-flash    ENTJ   stateful_memory      flat         0.371         0.328     0.228         0.328 71.500         68.333          0.900     0.317          0.758          0.715      47.698  -20.835          9.0    12.165         0.0             0.0           3.000           3.000       1           10
gemini-2.5-flash    ENTJ            static bull_trap         0.292         0.263     0.179         0.345 79.500         80.435          0.920     0.238          0.822          0.777     210.378   -9.512         93.5    38.654         0.0             0.0           4.000           4.000       2           10
gemini-2.5-flash    ENTJ            static     crash         0.336         0.311     0.223         0.376 64.750         64.750          1.000     0.309          0.767          0.721      23.634  -26.522         79.0    15.262         0.0             0.0           4.500           4.500       2           10
gemini-2.5-flash    ENTJ            static      flat         0.276         0.222     0.130         0.272 78.944         76.852          0.933     0.204          0.882          0.837      39.965  -14.099         45.0    12.480         0.0             0.0           5.000           4.333       3           10
gemini-2.5-flash    ENTJ           swapped bull_trap         0.785         0.885     0.785         0.885 63.000         64.674          0.920     0.865          0.021          0.018       1.734   -0.512          5.0     0.918         0.0             0.0           1.000           1.000       1           10
gemini-2.5-flash    ENTJ           swapped     crash         0.785         0.885     0.785         0.885  4.500          4.500          1.000     0.985          0.016          0.019       1.842   -0.816          8.0     1.966         0.0             0.0           1.000           1.000       1           10
gemini-2.5-flash    ENTJ           swapped      flat         0.772         0.871     0.772         0.871  8.500          5.556          0.900     0.968          0.035          0.035       0.001   -1.481         17.0     3.721         0.0             0.0           1.000           1.000       1           10
gemini-2.5-flash    INTJ            memory bull_trap         0.418         0.418     0.322         0.418 87.000         90.217          0.920     0.358          0.383          0.194     142.421   -4.853         64.0    23.809         0.0             0.0           6.000           6.000       1           10
gemini-2.5-flash    INTJ            memory     crash         0.427         0.427     0.331         0.427 84.000         84.000          1.000     0.366          0.467          0.172      14.953  -35.339         75.0    18.819         0.0             0.0           6.000           6.000       1           10
gemini-2.5-flash    INTJ            memory      flat         0.426         0.426     0.331         0.426 88.500         87.778          0.900     0.359          0.482          0.172      64.287  -17.663         66.0    17.085         0.0             0.0           6.000           6.000       1           10
gemini-2.5-flash    INTJ placebo_directive bull_trap         0.477         0.477     0.378         0.477 96.500         96.196          0.920     0.418          0.242          0.055     191.489   -4.853         25.0    10.337         0.0             0.0           5.000           6.000       1           10
gemini-2.5-flash    INTJ placebo_directive     crash         0.471         0.471     0.373         0.471 97.000         97.000          1.000     0.379          0.440          0.067      30.736  -31.600         32.0     7.151         0.0             0.0           6.000           6.000       1           10
gemini-2.5-flash    INTJ placebo_directive      flat         0.482         0.482     0.382         0.482 97.500         97.222          0.900     0.384          0.431          0.044      59.345  -20.918         27.0     4.007         0.0             0.0           6.000           6.000       1           10
gemini-2.5-flash    INTJ   stateful_memory      flat         0.363         0.363     0.285         0.363 91.000         91.667          0.900     0.321          0.559          0.288      57.343  -14.837         24.0     8.112         0.0             0.0           6.000           6.000       1           10
gemini-2.5-flash    INTJ            static bull_trap         0.462         0.462     0.364         0.462 92.250         91.576          0.920     0.403          0.276          0.090     188.499   -4.853         39.0    24.615         0.0             0.0           5.000           6.000       2           10
gemini-2.5-flash    INTJ            static     crash         0.488         0.488     0.388         0.488 98.500         98.500          1.000     0.391          0.417          0.029      33.042  -29.083         13.5     4.467         0.0             0.0           6.000           6.000       2           10
gemini-2.5-flash    INTJ            static      flat         0.478         0.478     0.379         0.478 97.500         97.222          0.900     0.382          0.435          0.053      62.633  -19.130         20.0     4.558         0.0             0.0           6.000           6.000       2           10
gemini-2.5-flash    INTJ           swapped bull_trap         0.500         0.500     0.400         0.500 99.000         98.913          0.920     0.487          0.075          0.000     203.647  -21.108          6.0    16.017         0.0             0.0           4.000           0.000       1           10
gemini-2.5-flash    INTJ           swapped     crash         0.500         0.500     0.400         0.500 62.500         62.500          1.000     0.475          0.249          0.000      42.509  -15.174          7.0     8.259         0.0             0.0           3.000           0.000       1           10
gemini-2.5-flash    INTJ           swapped      flat         0.498         0.498     0.398         0.498 68.000         64.444          0.900     0.469          0.261          0.005      63.907  -12.641         11.0    15.036         0.0             0.0           2.000           5.000       1           10
gemini-2.5-flash    ISFJ            memory bull_trap         0.021         0.179     0.083         0.179 75.000         77.717          0.920     0.158          0.918          0.882       2.274   -0.934         10.0     0.726         0.0             0.0           8.000           7.000       1           10
gemini-2.5-flash    ISFJ            memory     crash         0.038         0.163     0.073         0.163 28.500         28.500          1.000     0.262          0.730          0.896       3.238   -0.889         12.0     0.873         0.0             0.0           7.000           7.000       1           10
gemini-2.5-flash    ISFJ            memory      flat         0.048         0.152     0.057         0.152 59.583         57.222          0.950     0.258          0.736          0.919       1.282   -0.886          7.5     0.533         0.0             0.0           7.000           7.000       2           10
gemini-2.5-flash    ISFJ placebo_directive bull_trap         0.265         0.267     0.170         0.267 87.000         88.043          0.920     0.187          0.879          0.758      47.999   -4.125         50.0     2.891         0.0             0.0           7.000           6.000       1           10
gemini-2.5-flash    ISFJ placebo_directive     crash         0.311         0.249     0.152         0.249 58.500         58.500          1.000     0.231          0.782          0.783      24.946   -6.527         62.0     3.542         0.0             0.0           7.000           6.000       1           10
gemini-2.5-flash    ISFJ placebo_directive      flat         0.453         0.348     0.250         0.348 72.500         71.111          0.900     0.284          0.693          0.643      32.852  -11.271         65.0     4.252         0.0             0.0           7.000           5.000       1           10
gemini-2.5-flash    ISFJ   stateful_memory      flat         0.080         0.120     0.047         0.120 55.000         51.111          0.900     0.216          0.806          0.933       8.632   -0.998         20.0     0.286         0.0             0.0           7.000           7.000       1           10
gemini-2.5-flash    ISFJ            static bull_trap         0.209         0.217     0.129         0.290 87.750         88.043          0.920     0.149          0.931          0.816      34.363   -4.160         45.0     2.458         0.0             0.0           8.000           6.500       2           10
gemini-2.5-flash    ISFJ            static     crash         0.320         0.264     0.170         0.278 49.750         49.750          1.000     0.252          0.747          0.758      27.116   -5.438         71.0     4.253         0.0             0.0           7.000           6.500       2           10
gemini-2.5-flash    ISFJ            static      flat         0.447         0.337     0.240         0.345 66.167         64.630          0.933     0.284          0.693          0.656      25.801   -6.681         53.0     3.782         0.0             0.0           6.667           5.667       3           10
gemini-2.5-flash    ISFJ           swapped bull_trap         0.855         0.713     0.613         0.713 98.500         98.370          0.920     0.692          0.176          0.125     202.595  -21.323         10.0    22.762         0.0             0.0           3.000           3.000       1           10
gemini-2.5-flash    ISFJ           swapped     crash         0.606         0.562     0.462         0.562 60.500         60.500          1.000     0.540          0.267          0.340      39.212  -17.091         13.0    11.907         0.0             0.0           4.000           4.000       1           10
gemini-2.5-flash    ISFJ           swapped      flat         0.670         0.602     0.502         0.602 67.000         63.333          0.900     0.553          0.245          0.283      64.271  -12.285          6.0     7.249         0.0             0.0           4.000           4.000       1           10

## Reliability

           Model               Arm  n_runs  fallback_share  zero_trade_share  attempts_mean
gemini-2.5-flash            memory      11             0.0               0.0            1.0
gemini-2.5-flash placebo_directive       9             0.0               0.0            1.0
gemini-2.5-flash   stateful_memory       3             0.0               0.0            1.0
gemini-2.5-flash            static      20             0.0               0.0            1.0
gemini-2.5-flash           swapped       9             0.0               0.0            1.0

## Bull-trap strata (topped / un-topped)

           Model Persona               Arm  Scenario  Topped  mcr_0.05  band_mas  rg_theta_0.05  return_pct
gemini-2.5-flash    ENTJ            memory bull_trap    True     0.216     0.120         98.913     206.050
gemini-2.5-flash    ENTJ placebo_directive bull_trap    True     0.225     0.163         84.239     218.497
gemini-2.5-flash    ENTJ            static bull_trap    True     0.238     0.179         80.435     210.378
gemini-2.5-flash    ENTJ           swapped bull_trap    True     0.865     0.785         64.674       1.734
gemini-2.5-flash    INTJ            memory bull_trap    True     0.358     0.322         90.217     142.421
gemini-2.5-flash    INTJ placebo_directive bull_trap    True     0.418     0.378         96.196     191.489
gemini-2.5-flash    INTJ            static bull_trap    True     0.403     0.364         91.576     188.499
gemini-2.5-flash    INTJ           swapped bull_trap    True     0.487     0.400         98.913     203.647
gemini-2.5-flash    ISFJ            memory bull_trap    True     0.158     0.083         77.717       2.274
gemini-2.5-flash    ISFJ placebo_directive bull_trap    True     0.187     0.170         88.043      47.999
gemini-2.5-flash    ISFJ            static bull_trap    True     0.149     0.129         88.043      34.363
gemini-2.5-flash    ISFJ           swapped bull_trap    True     0.692     0.613         98.370     202.595

## gate_common_start

           Model  n  kw_p  delta_ISFJ-INTJ  delta_INTJ-ENTJ  band_hit  auc  pass
gemini-2.5-flash  9  0.05              1.0           -0.333     0.222  NaN False

## gate_start_at_target_deltaC1

           Model  n  kw_p  delta_ISFJ-INTJ  delta_INTJ-ENTJ  band_hit   auc  pass
gemini-2.5-flash 43   0.0              0.6             -1.0       0.0 0.683 False
