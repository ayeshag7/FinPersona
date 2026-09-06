# E4.18 the calm-trained level-free channel, Phase 3 vs Phase 4

the published audit is cross-phase-trained (leakage_audit.py:297-300); the brief's quantity is the calm-TRAINED level-free R2(x), Phase 3 = +0.349 [0.322, 0.374], of which E3.8 attributed ~0.20 to the process+GJR+jump stack, leaving ~+0.15 for events and sentiment.

Best model per cell; R2(x) / sign accuracy on resolvable steps, 500-resample cluster bootstrap over paths. CIs that overlap are not a detected change.

| state | feature set | published (cross-phase-trained) | calm-trained |
|---|---|---|---|
| phase3 | level-free | -0.5819 [-0.7162, -0.4702] / sign 0.722 [0.702, 0.741] (ridge) | +0.3493 [+0.3218, +0.3743] / sign 0.814 [0.801, 0.828] (gbt) |
| phase3 | full field set | +0.2125 [+0.1414, +0.2695] / sign 0.834 [0.819, 0.848] (gbt) | +0.5501 [+0.5180, +0.5791] / sign 0.906 [0.896, 0.915] (gbt) |
| phase4 | level-free | -0.4618 [-0.5842, -0.3595] / sign 0.708 [0.688, 0.727] (ridge) | +0.3213 [+0.2935, +0.3478] / sign 0.786 [0.772, 0.799] (gbt) |
| phase4 | full field set | +0.2260 [+0.1621, +0.2816] / sign 0.824 [0.809, 0.838] (gbt) | +0.4905 [+0.4607, +0.5203] / sign 0.857 [0.844, 0.870] (gbt) |

## The brief's quantity

- calm-trained level-free R2(x): +0.3493 [+0.3218, +0.3743] -> +0.3213 [+0.2935, +0.3478], delta -0.0280 -- CIs OVERLAP: no detected change
- calm-trained full field set R2(x): +0.5501 [+0.5180, +0.5791] -> +0.4905 [+0.4607, +0.5203], delta -0.0596 -- CIs OVERLAP: no detected change
