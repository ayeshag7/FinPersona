# E1.3 override check (ADDENDUM section 6.2)

100 seeds x 4 scenarios per variant; E1.3's reader; 300-resample cluster CI.

| variant | calm R2(x) [CI] | all R2 | median path sd(x) | calm daily sd |
|---|---|---|---|---|
| none (in force) | 0.096 [0.073, 0.155] | 0.221 | 0.094 | 0.0135 |
| garch.sbar 0.017 (the default value, passed explicitly) | 0.096 [0.073, 0.155] | 0.221 | 0.094 | 0.0135 |
| garch.sbar 0.0160 (the grid's s_x = 0.165 row) | 0.104 [0.062, 0.137] | 0.286 | 0.093 | 0.0129 |
| sigma_V 0.006 + df_V 5 (explicit, = in force) | 0.096 [0.073, 0.155] | 0.221 | 0.094 | 0.0135 |
| all three as the grid row | 0.104 [0.062, 0.137] | 0.286 | 0.093 | 0.0129 |
