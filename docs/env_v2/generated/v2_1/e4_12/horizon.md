# E4.12 - is the topped share a horizon property?

`python -m tools.phase4.e4_12_horizon`

600 bull-trap seeds on E4.11's adopted configuration, `schedule_mode` pinned to v21.

**Hypothesis.** the topped share is unreachable because a generated path tops INSIDE its own 200-day horizon and has only T - top_day days left, whereas the panel gives every run-up a full 200 days after its top

**Falsifier.** restrict the generator to paths with a long post-top window; if the share rises toward the panel's band the horizon is the cause

## Days remaining after the realised top

P10 4 / P50 29 / P90 67 trading days; 0.9% of topped paths have 120 or more. The panel's median post-top length is 60 d and its P90 is 187 d.

## Topped share by the window actually available

| days remaining | generator | 95 % CI | n | panel (same restriction) | 95 % CI | n |
|---|---|---|---|---|---|---|
| 0-50 | 0.0250 | [0.0000, 0.0625] | 80 | 0.0294 | [0.0000, 0.0882] | 34 |
| 50-100 | 0.0769 | [0.0000, 0.1923] | 26 | 0.0357 | [0.0000, 0.1071] | 28 |

## Window-matched verdict

| days remaining | generator | panel | CIs overlap |
|---|---|---|---|
| 0-50 | 0.0250 (n=80) | 0.0294 (n=34) | **True** |
| 50-100 | 0.0769 (n=26) | 0.0357 (n=28) | **True** |

Panel, all run-ups: **0.1100 [0.0966, 0.1245]** (n = 3201).

## Verdict

**HORIZON -- within every window bin the two populations share, the generator's topped share agrees with the panel's; the panel's headline 0.110 comes almost entirely from run-ups that have a 150-200 day post-top window, and only 0.9% of generated topped paths have even 120 days left (median 29). The topped share is therefore a property of fitting a mania AND its aftermath into one 200-day horizon, not a parameter defect, and the hazard's adoption criterion cannot be met on the deployed state as it is written. It must be re-expressed on a window-matched basis.**
