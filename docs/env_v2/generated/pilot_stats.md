# Statistics track (v2)

Effective N is models (sign counts and mixed-effects random intercepts by model); Cliff's delta / Hedges g with bootstrap 95% CIs; BH-adjusted q across the metric family per contrast; degeneracy audit beside every contrast.

## Arm contrasts vs static

Persona Scenario    Arm     vs        metric  n_arm  n_ref  mean_arm  mean_ref  cliffs_delta  delta_ci_lo  delta_ci_hi  hedges_g  models_improving  n_models  fallback_share_arm  zero_trade_share_arm  degenerate_rg_share_arm  p_approx  q_bh
   ENTJ     flat memory static      mcr_0.05      2      3     0.184     0.204         0.000       -1.000        1.000    -0.073                 1         1                 0.0                   0.0                      1.0     1.000 1.000
   ENTJ     flat memory static      band_mas      2      3     0.130     0.130         0.167       -1.000        1.000    -0.001                 1         1                 0.0                   0.0                      1.0     0.744 1.000
   ENTJ     flat memory static  point_mas_v2      2      3     0.227     0.222         0.333       -1.000        1.000     0.026                 0         1                 0.0                   0.0                      1.0     0.514 0.899
   ENTJ     flat memory static rg_theta_0.05      2      3    81.667    76.852         0.000       -1.000        1.000     0.184                 1         1                 0.0                   0.0                      1.0     1.000 1.000
   ENTJ     flat memory static    return_pct      2      3    37.503    39.965         0.333       -1.000        1.000    -0.070                 0         1                 0.0                   0.0                      1.0     0.514 0.899
   ENTJ     flat memory static       mdd_pct      2      3    -8.627   -14.099         0.667       -0.333        1.000     0.543                 0         1                 0.0                   0.0                      1.0     0.050 0.175
   ENTJ     flat memory static      turnover      2      3     6.304    12.480        -0.667       -1.000        0.333    -0.448                 1         1                 0.0                   0.0                      1.0     0.050 0.175
   ISFJ     flat memory static      mcr_0.05      2      3     0.258     0.284         0.000       -1.000        1.000    -0.314                 1         1                 0.0                   0.0                      1.0     1.000 1.000
   ISFJ     flat memory static      band_mas      2      3     0.057     0.240        -1.000       -1.000       -1.000    -1.536                 1         1                 0.0                   0.0                      1.0     1.000 1.000
   ISFJ     flat memory static  point_mas_v2      2      3     0.152     0.337        -1.000       -1.000       -1.000    -1.537                 1         1                 0.0                   0.0                      1.0     1.000 1.000
   ISFJ     flat memory static rg_theta_0.05      2      3    57.222    64.630        -0.333       -1.000        1.000    -0.272                 0         1                 0.0                   0.0                      1.0     0.514 1.000
   ISFJ     flat memory static    return_pct      2      3     1.282    25.801        -1.000       -1.000       -1.000    -1.516                 0         1                 0.0                   0.0                      1.0     1.000 1.000
   ISFJ     flat memory static       mdd_pct      2      3    -0.886    -6.681         1.000        1.000        1.000     2.335                 0         1                 0.0                   0.0                      1.0     1.000 1.000
   ISFJ     flat memory static      turnover      2      3     0.533     3.782        -1.000       -1.000       -1.000    -1.229                 1         1                 0.0                   0.0                      1.0     1.000 1.000

## Mixed-effects (metric ~ arm x persona, random intercept by model)

(none)

## Degeneracy audit

           Model               Arm  n  fallback  zero_trade  degenerate_rg
gemini-2.5-flash            memory 11       0.0         0.0            1.0
gemini-2.5-flash placebo_directive  9       0.0         0.0            1.0
gemini-2.5-flash   stateful_memory  3       0.0         0.0            1.0
gemini-2.5-flash            static 20       0.0         0.0            1.0
gemini-2.5-flash           swapped  9       0.0         0.0            1.0
