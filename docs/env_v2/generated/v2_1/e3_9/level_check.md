# E3.9c the calm-window mapping and the level double-count check (PREREG_PHASE_3_ADDENDUM.md section 4.3)

(i) **The panel's crisis-free calm daily sd is 0.0170 [0.0163, 0.0176]** (sqrt of the median pre-event 120-day rv_calm over 1592 episodes / 412 stocks) against the full-sample unconditional **0.0218** the identity targets — the full sample is **1.28x** the panel's own calm.

(ii) The **calm-window mapping** (the registered alternative, reported not adopted): sbar would be **0.00676** against the adopted 0.01509 (0.45x); at that sbar the flat arm's pooled daily return sd is 0.0171 [0.0165, 0.0178] and median sd(x) 0.0214.

(iii) **The deployed check** (events on, 200 seeds per scenario over the audit mix): pooled realised daily return sd **0.0284 [0.0267, 0.0302]** against the 0.0218 target — excess **+0.0066** (+30.5 %) against a bootstrap half-width of 0.0017: **double-count CONFIRMED**.

| scenario | pooled sd_r | 95 % CI | median sd(x) |
|---|---|---|---|
| flat | 0.0215 | [0.0209, 0.0222] | 0.0468 |
| crash | 0.0431 | [0.0394, 0.0476] | 0.1204 |
| bull_trap | 0.0225 | [0.0219, 0.0231] | 0.1430 |
| sustained_bull | 0.0201 | [0.0198, 0.0205] | 0.0216 |
