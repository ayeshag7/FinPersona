# E4.4 - mania drift, and the cap (amendment A5)

`python -m tools.phase4.e4_4_mania` - PREREG_PHASE_4.md section 6.

## The registered LPPLS route is NOT supported

- rule: supports a super-exponential mania drift iff the stable share >= 0.50 AND the median m is inside (0,1) with a CI excluding 1.0
- stable share **0.329 [0.313, 0.344]** (needs >= 0.50) over 3125 converged fits / 398 stocks
- median m 0.926 [0.900, 0.953] -- the CI excludes 1.0, but m sits close to the exponential boundary
- **met: False** -> the registered fallback is taken

## The fallback's shape, FIT from the run-up table

- kappa **0.00000** (v2 drew U(0.02, 0.04)), from the panel's median convexity ratio 0.665 over 2937 run-ups
- mania length: the panel's run-ups run 126 / 415 / 500 days (P10/P50/P90) against a 200-day horizon, so 84.0% of draws are truncated -- the mania length is a horizon artefact and is reported as one

| arm | kappa | cap binding share | upper 95 % | verdict | convex share | mania days |
|---|---|---|---|---|---|---|
| v2_kappa_uniform | 0.0308 | 0.4761 | 0.4898 | **CAP STILL BINDS** | 0.5166666666666667 | 119 |
| v21_kappa_FIT | 0.0000 | 0.0000 | 0.0000 | **CAP UNNECESSARY** | 0.49 | 122 |

## Amendment A5

- the drift cap cannot be retired on the LPPLS route because that route is not supported by the panel; whether it is needed under the FIT kappa is answered by the cap-binding upper limit in the table
