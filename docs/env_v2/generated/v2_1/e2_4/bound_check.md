# E2.8 does the level-free surrogate exceed an EXACT Appendix-B bound? (post-review extension; PREREG_PHASE_2_ADDENDUM.md section 4)

E2.8 (post-review extension, PREREG_PHASE_2_ADDENDUM.md section 4): is the level-free surrogate optimistically
biased, or is the excess over the Appendix-B bound a real channel?

**Rule (fixed before the run):** if the 95 % interval of the measured level-free R2(x) lies entirely above the analytic window-average bound, the surrogate is optimistically biased (explanation a); otherwise (a) is not supported and the generator's excess is an unmodelled channel (explanation b).

Design: Gaussian random-walk log V + Gaussian AR(1) x from its stationary prior; no events, jumps, GARCH or sentiment feedback. Features: technicals_block on the price path, then the audit's own add_level_free_columns and 5-lag block -- identical to the SEP audit. Estimators: evaluation.leakage_audit.l2_surrogate, control='level_free', GroupKFold by path, 500-resample cluster bootstrap. 200 paths x 200 days per case, seeds from 160000.

| configuration | sigma_V | s_x | h | bound (window avg) | bound (steady state) | measured level-free R2(x) | best model | interval entirely above the bound? |
|---|---|---|---|---|---|---|---|---|
| in force (Phase 2: sigma_V 0.0122, s_x 0.0386, h 7.5) | 0.0122 | 0.0386 | 7.50 | 0.245 | 0.256 | 0.241 [0.214, 0.268] | ridge | no |
| the v2 state Phase 1 handed over (0.006, 0.175, 150) | 0.0060 | 0.1750 | 150.00 | 0.153 | 0.497 | 0.091 [0.044, 0.126] | ridge | no |
| the panel's own fit (estimator C corrected: 0.0196, 0.0250, 4.82) | 0.0196 | 0.0250 | 4.82 | 0.094 | 0.096 | 0.085 [0.070, 0.100] | ridge | no |

**Verdict: surrogate not shown to be biased (explanation a not supported).**

Per-model level-free R2(x) in each case (the audit reports the best; the spread is shown so a single estimator's behaviour is visible):

| configuration | gbt | mlp | ridge |
|---|---|---|---|
| in force (Phase 2: sigma_V 0.0122, s_x 0.0386, h 7.5) | 0.228 | 0.211 | 0.241 |
| the v2 state Phase 1 handed over (0.006, 0.175, 150) | 0.058 | 0.039 | 0.091 |
| the panel's own fit (estimator C corrected: 0.0196, 0.0250, 4.82) | 0.076 | 0.038 | 0.085 |
