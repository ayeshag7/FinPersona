# E4.2 - the schedule's ranges from the panel, and the rise time

`python -m tools.phase4.e4_2_schedule` - PREREG_PHASE_4.md section 4.

500 crash seeds per arm, the same seeds in both, seeds 220000+.
Rise time measured by `tools/phase3/episodes.py::rise_decay`, the same code path that measured the panel. Panel target: **30 d [29, 35]** (fast crashes, 642 episodes / 313 stocks).

## Ranges: before and after

| parameter | v2 (DESIGN, stipulated) | v2.1 (FIT, panel P10-P90) |
|---|---|---|
| det_len | U(15, 40) | [3, 26], median 8 |
| panic_len | U(15, 70) | [15, 101], median 39 |
| front_load | fixed 0.50 | [0.088, 0.574], median 0.272 |
| depth -> delta | delta fixed 0.70 | [-0.538, -0.312], median -0.369 |
| delta_end | U(delta, 1) | via rec60 [0.236, 1.037], median 0.569 |

## Results

| arm | rise median | 95 % CI | overlaps [29, 35] | depth | duration | rejection | coverage |
|---|---|---|---|---|---|---|---|
| v2 | 70.0 | [65.0, 74.0] | **False** | -0.537 | 82 | 0.000 | 0.434 |
| v21_uniform | 65.0 | [62.0, 71.0] | **False** | -0.528 | 81 | 0.014 | 0.467 |
| v21_empirical | 58.0 | [52.0, 64.0] | **False** | -0.503 | 76 | 0.040 | 0.558 |

## Truncation forced by T = 200

| arm | panic_len | setup_len | det_len |
|---|---|---|---|
| v2 | 0.052 | 0.000 | 0.000 |
| v21_uniform | 0.108 | 0.000 | 0.000 |
| v21_empirical | 0.082 | 0.000 | 0.000 |

## What actually binds the rise time

| arm | corr(onset lag, rise) | corr(det_len, rise) | corr(panic_len, rise) | drawn det_len | realised det_len |
|---|---|---|---|---|---|
| v2 | 0.737 | 0.109 | 0.153 | 26 | 11 |
| v21_uniform | 0.687 | 0.092 | 0.099 | 13 | 9 |
| v21_empirical | 0.684 | 0.140 | 0.121 | 8 | 9 |

### v2: rise time by how far the onset precedes the scripted event

| onset lag before event | n | rise median | duration median |
|---|---|---|---|
| (-inf, 0] | 173 | 48.0 | 64.0 |
| (0, 10] | 37 | 63.0 | 84.0 |
| (10, 30] | 80 | 79.5 | 89.0 |
| (30, inf] | 74 | 103.5 | 109.5 |

### v21_uniform: rise time by how far the onset precedes the scripted event

| onset lag before event | n | rise median | duration median |
|---|---|---|---|
| (-inf, 0] | 172 | 44.0 | 62.0 |
| (0, 10] | 37 | 54.0 | 72.0 |
| (10, 30] | 76 | 69.0 | 84.5 |
| (30, inf] | 94 | 97.0 | 106.0 |

### v21_empirical: rise time by how far the onset precedes the scripted event

| onset lag before event | n | rise median | duration median |
|---|---|---|---|
| (-inf, 0] | 167 | 32.0 | 54.0 |
| (0, 10] | 36 | 47.0 | 74.5 |
| (10, 30] | 77 | 63.0 | 72.0 |
| (30, inf] | 100 | 88.5 | 101.5 |

## The surface (rise time against the two parameters that set it)

### v2

- rise time changes by **0.44 d per extra deterioration day** (correlation 0.109)

| det_len bin | front_load bin | n | rise median | depth median |
|---|---|---|---|---|

### v21_uniform

- rise time changes by **0.43 d per extra deterioration day** (correlation 0.092)

| det_len bin | front_load bin | n | rise median | depth median |
|---|---|---|---|---|
| (2.999, 7.0] | (0.0877, 0.363] | 48 | 70 | -0.543 |
| (2.999, 7.0] | (0.363, 0.574] | 49 | 59 | -0.509 |
| (7.0, 13.0] | (0.0877, 0.363] | 53 | 63 | -0.543 |
| (7.0, 13.0] | (0.363, 0.574] | 45 | 65 | -0.572 |
| (13.0, 19.0] | (0.0877, 0.363] | 40 | 61 | -0.491 |
| (13.0, 19.0] | (0.363, 0.574] | 52 | 66 | -0.523 |
| (19.0, 26.0] | (0.0877, 0.363] | 49 | 70 | -0.527 |
| (19.0, 26.0] | (0.363, 0.574] | 43 | 75 | -0.513 |

### v21_empirical

- rise time changes by **0.77 d per extra deterioration day** (correlation 0.140)

| det_len bin | front_load bin | n | rise median | depth median |
|---|---|---|---|---|
| (2.999, 5.0] | (0.0908, 0.284] | 61 | 50 | -0.526 |
| (2.999, 5.0] | (0.284, 0.57] | 54 | 56 | -0.510 |
| (5.0, 8.0] | (0.0908, 0.284] | 48 | 56 | -0.487 |
| (5.0, 8.0] | (0.284, 0.57] | 48 | 60 | -0.493 |
| (8.0, 14.0] | (0.0908, 0.284] | 39 | 54 | -0.489 |
| (8.0, 14.0] | (0.284, 0.57] | 43 | 48 | -0.483 |
| (14.0, 26.0] | (0.0908, 0.284] | 42 | 66 | -0.486 |
| (14.0, 26.0] | (0.284, 0.57] | 45 | 72 | -0.535 |
