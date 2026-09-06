# E4.11 - the post-top block re-fitted on the deployed state

`python -m tools.phase4.e4_11_posttop_recal` - PREREG_PHASE_4_ADDENDUM.md section 5.4.

1500 bull-trap seeds per arm, `schedule_mode` pinned to v21 on every arm.

## The two parameters that were stipulated, now fitted

| parameter | shipped (v2 DESIGN) | panel P10 / P50 / P90 | n |
|---|---|---|---|
| `post_top_drop` | U(0.30, 0.50) | 0.061 / 0.169 / 0.414 | 3201 / 398 |
| `post_top_len` | U(10, 30) | 8 / 60 / 187 d | same |

The panel's own share of run-ups reaching -40 % after the top is **0.0% of post-top lengths run beyond the 200-day horizon**, and the share reaching -40 % is **0.110** - the same quantity as the topped share the hazard was adopted against.

## Arms

| arm | half-life | post-top/mania | in panel CI | topped share | in panel CI | hazard fires | realised drop P50 |
|---|---|---|---|---|---|---|---|
| v2_stipulated_ranges_hl50 | 50 | 0.6462 | **True** | 0.0040 | **False** | 0.192 | -0.226 |
| FIT_ranges_hl10 | 10 | 0.7300 | **False** | 0.0073 | **False** | 0.193 | -0.226 |
| FIT_ranges_hl20 | 20 | 0.6589 | **False** | 0.0033 | **False** | 0.193 | -0.204 |
| FIT_ranges_hl30 | 30 | 0.6340 | **True** | 0.0027 | **False** | 0.193 | -0.191 |
| FIT_ranges_hl40 | 40 | 0.6216 | **True** | 0.0027 | **False** | 0.193 | -0.184 |
| FIT_ranges_hl50 | 50 | 0.6295 | **True** | 0.0020 | **False** | 0.193 | -0.180 |
| FIT_ranges_hl70 | 70 | 0.6215 | **True** | 0.0020 | **False** | 0.193 | -0.172 |
| FIT_ranges_hl100 | 100 | 0.6157 | **True** | 0.0013 | **False** | 0.193 | -0.167 |

## Decision

- rule: the half-life is adopted if it puts the post-top/mania variance ratio inside the panel CI; the topped share is an OUTCOME and is reported against the panel CI, not tuned to it
- meeting the variance ratio: **['FIT_ranges_hl30', 'FIT_ranges_hl40', 'FIT_ranges_hl50', 'FIT_ranges_hl70', 'FIT_ranges_hl100']**
- whose topped share is also inside the panel CI: **none**
- adopted: **FIT_ranges_hl30**

- the panel's post-top VARIANCE ratio and its post-top DEPTH are not simultaneously reachable by a single deterministic decay leg at any half-life tested; this is reported as a property of the environment, not resolved by dropping one of them
