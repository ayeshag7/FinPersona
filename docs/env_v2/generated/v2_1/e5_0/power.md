# E5.0 / PP: inherited numbers verified and the Phase-5 thresholds' decidability

`python -m tools.phase5.prereg_power`, run before any Phase-5 experiment.

## Inherited numbers (PREREG section 1)

| figure | cited | file | ok |
|---|---|---|---|
| L2b acc full | 0.76016 | 0.7601597222222222 | yes |
| L2b acc price-only | 0.656635 | 0.6566354166666667 | yes |
| L2b acc day-only | 0.509229 | 0.5092291666666666 | yes |
| L2b majority | 0.41449 | 0.41448958333333336 | yes |
| L2b selectivity | 0.103524 | 0.10352430555555547 | yes |
| shown fields n | 18 | 18 | yes |
| best full R2 all | 0.8046 | 0.8046368166127957 | yes |
| best full R2 calm | 0.2326 | 0.23261959891956074 | yes |
| best full R2 event | 0.8541 | 0.8540522295417348 | yes |
| best full R2 resolution | 0.7442 | 0.7441994174272093 | yes |
| best level-free R2 all | 0.4458 | 0.4457898431099431 | yes |
| best level-free R2 calm | -0.394 | -0.24948634967807903 | **NO** |
| L1 analyst median APE | 0.6786 | 0.6786295515992399 | yes |
| calm-trained level-free R2 | 0.3213 | 0.321300437443772 | yes |
| calm-trained level-free lo | 0.2935 | 0.2934511575402282 | yes |
| calm-trained level-free hi | 0.3478 | 0.3478489173785924 | yes |
| calm-trained full R2 | 0.4905 | 0.4905368879322394 | yes |
| E3.8 process+GJR+jump stack | 0.203 | 0.20250149275316176 | yes |
| eps clock fixed grid | 0.8728 | 0.8728 | yes |
| eps clock randomised | 0.3958 | 0.3958 | yes |
| eps clock null p95 randomised | 0.3625 | 0.3625333333333333 | yes |
| IV onset dAUC | -0.107 | -0.10748801749630355 | yes |
| IV onset null p95 | 0.032 | 0.032244133501724934 | yes |
| sigma_V in force | 0.01457 | 0.014573291000253476 | yes |
| VP.SIGMA_V | 0.01457 | 0.014573291000253476 | yes |
| coverage flat | 0.378 | 0.37849999999999995 | yes |
| coverage crash | 0.553 | 0.5533 | yes |
| coverage bull_trap | 0.646 | 0.6459 | yes |
| coverage sustained_bull | 0.374 | 0.374 | yes |

Stored panel `docs\env_v2\generated\v2_1\_panels\sep_phase4_after.pkl`: 1600 paths / 320000 rows; regenerated 8 paths with the current generator -> bit-identical on every column.

## Thresholds

| row | rule | verdict |
|---|---|---|
| PP1 | E5.1 KS: bootstrap 95 % upper limit of D(per-path median P/E, EDGAR pooled) < 0.10 | DECIDABLE |
| PP2 | E5.7c: dAUC(field - price reference) <= circular-shift null p95, 200 seeds per scenario | DECIDABLE for an AUC excess of about 0.05 or more; the measured E3.5 null (+0.032) is inside the simulated scale, so the circular-shift null is not degenerate at this n |
| PP3 | test_eps_lag_distribution: draws inside the FIT grid; median nearer the panel P50 than the grid midpoint (the Phase-4 sampler test) | DECIDABLE iff |P50 - midpoint| of the FIT grid exceeds the half-width (about 0.5 d); a symmetric lag distribution would make the median rule vacuous, in which case the range assertion alone stands and the report says so |
| PP4 | E5.5 (i): generator median CI (1600 paths) overlaps the data window-median CI | DECIDABLE for gaps above about 0.03 in ACF(1) and 0.03 in corr(s, r); the data side dominates the width (58 windows), so the reference CI is what limits resolution |
| PP6 |  | DECIDABLE; both statistics resolve differences of 2 pp at the panel's n even under the loose path-level clustering |
| PP5 | E5.4 admissibility: dR2_add(ANALYST) <= the permutation null margin (max of 20 draws) | DECIDABLE if the null's scale is well below 0.014 (the analytic single-day effect at the LIT sd); the measured baseline null (20 draws on the real panel) supersedes this figure |

PP1: null floor p95 of D = 0.0341 (analytic 0.0345); pass rate under D = 0: 1.00; under a true D = 0.101: 0.00.

PP2: null p95 of dAUC = +0.0174 (sd 0.0112); an AUC excess of 0.028 is detected with 80 % power.

PP5: synthetic permutation null of dR2_add for a 6-column block: draws [1e-05, 4e-05, 7e-05, 0.0, 1e-05], max +0.00007, base R2 0.852.
