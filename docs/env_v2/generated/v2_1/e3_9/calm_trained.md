# E3.9a the level-free calm channel under a CALM-TRAINED surrogate (PREREG_PHASE_3_ADDENDUM.md section 4.1)

the published audit fits on all rows (GroupKFold by path) and masks by phase group afterwards; here the panel is restricted to calm rows BEFORE the fit, everything else identical. Best model per cell; R2(x) / sign accuracy on resolvable steps (|x| >= 0.05), 500-resample cluster bootstrap over paths. The plan's own L2 sign threshold is 0.70.

| state | feature set | published (cross-phase-trained) | calm-trained |
|---|---|---|---|
| phase2 | level-free | +0.339 [+0.208, +0.434] / sign 0.827 [0.812, 0.840] | +0.421 [+0.298, +0.523] / sign 0.892 [0.880, 0.905] |
| phase2 | full field set | +0.346 [+0.206, +0.446] / sign 0.842 [0.825, 0.858] | +0.626 [+0.564, +0.682] / sign 0.942 [0.931, 0.953] |
| phase3 | level-free | -0.582 [-0.716, -0.470] / sign 0.722 [0.702, 0.741] | +0.349 [+0.322, +0.374] / sign 0.814 [0.801, 0.828] |
| phase3 | full field set | +0.213 [+0.141, +0.270] / sign 0.834 [0.819, 0.848] | +0.550 [+0.518, +0.579] / sign 0.906 [0.896, 0.915] |
