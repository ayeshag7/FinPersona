# E4.1 LPPLS fits on the panel's run-ups

`python -m tools.phase4.e4_1_lppls` - PREREG_PHASE_4.md section 3.

3125 of 3202 run-ups converged over 398 stocks at 20 restarts each.

| statistic | all episodes | stable only |
|---|---|---|
| m (median) | 0.926 [0.900, 0.953] | 0.990 |
| omega (median) | 4.81 [4.67, 4.97] | 5.42 |
| R2 (median) | 0.931 [0.929, 0.933] | - |
| stable share | 0.329 [0.313, 0.344] | - |

## The registered E4.4 trigger

- rule: supports a super-exponential mania drift iff the stable share >= 0.50 AND the median m is inside (0,1) with a CI excluding 1.0
- stable share 0.329 [0.313, 0.344] (needs >= 0.50)
- median m 0.926 [0.900, 0.953] (CI must exclude 1.0: True)
- **met: False**

- consequence: E4.4 reports the LPPLS route as UNSUPPORTED and uses the scripted-drift alternative with its shape FIT from the run-up table -- the registered fallback, not a relaxed rule
