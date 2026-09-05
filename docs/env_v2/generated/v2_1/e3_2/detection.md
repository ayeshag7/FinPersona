# E3.2 jump detection on the panel (PREREG_PHASE_3.md section 4.1)

Set A residuals (E3.1), 2000-2024, n = 2,622,096 stock-days over 417 stocks; 1000-resample stock bootstrap. The expected share is the no-jump null under each stock's own fitted t(nu); the excess is a LOWER bound on the jump rate (the QML nu absorbed jump mass) as the observed share is an upper bound.

| threshold | observed share | expected t-tail | excess | excess 95 % CI |
|---|---|---|---|---|
| 2.5 | 0.02158 | 0.02306 | -0.00148 | [-0.00161, -0.00136] |
| 3.0 | 0.01141 | 0.01169 | -0.00027 | [-0.00036, -0.00019] |
| 3.5 | 0.00682 | 0.00634 | +0.00048 | [+0.00040, +0.00056] |
| 4.0 | 0.00440 | 0.00366 | +0.00074 | [+0.00066, +0.00082] |
| 4.5 | 0.00305 | 0.00223 | +0.00082 | [+0.00075, +0.00089] |
| 5.0 | 0.00221 | 0.00142 | +0.00079 | [+0.00072, +0.00086] |
| 6.0 | 0.00120 | 0.00065 | +0.00055 | [+0.00051, +0.00060] |

Split at 4 (2009-24): in-window share 0.01342, outside 0.00297 (window share of days 0.145; E1.4's q = 0.4345 held). Sizes at 4: mean -0.0190, sd 0.1263, negative share 0.573 (n = 11,530).

Literature beside (not tolerances): ABD 2007 (index futures, read by the plan's pass): 14.4 % jump share of RV; 27.9 % of days — anchors, never tolerances; Lee & Mykland 2008: beta* = 4.6 at 1 %, intraday.
