# E4.16 the discrimination table on the Phase-4 hand-over

E4.16: the policy-spread table (16A G1's shape) on the Phase-4 hand-over, beside Phase 3's and Phase 2's, same design (40 training seeds, 50 scored seeds, three personas x four scenarios).

**Rule:** no pass/fail -- G1 is Phase 6's gate; a collapse in any scenario is a finding for the team.

What Phase 4 changed that could move this table:

- the schedule's ranges are FIT (det_len median 8 d against v2's 27; depth from the panel)
- the hazard is E4.3's mapping A (h0 6.7e-4, b 5.42) rather than v2's CAL
- the blow-off label reaches the driver and its multiplier is calibrated (2.0764)
- the post-top leg is an exponential decay (half-life 40) rather than a linear ramp
- the eps quarter grid is randomised per seed

## Phase 4 hand-over (event block in force)

| scenario | coverage | runs with NO resolvable step | mandate oracle | best L5 | best trivial | gap oracle->L5 | gap L5->trivial | ordering | both gaps > 0 |
|---|---|---|---|---|---|---|---|---|---|
| flat | 0.378 | 0/150 (0%) | 0.0029 | 0.0563 (level_free) | 0.1006 (constant_mix) | 0.0534 [0.0478, 0.0592] | 0.0443 [0.0386, 0.0500] |  |  |
| crash | 0.553 | 0/150 (0%) | 0.0023 | 0.0378 (full) | 0.1004 (constant_mix) | 0.0356 [0.0322, 0.0389] | 0.0625 [0.0592, 0.0659] |  |  |
| bull_trap | 0.646 | 0/150 (0%) | 0.0033 | 0.0320 (full) | 0.1008 (constant_mix) | 0.0287 [0.0244, 0.0333] | 0.0688 [0.0642, 0.0731] |  |  |
| sustained_bull | 0.044 | 15/150 (10%) | 0.0015 | 0.0691 (price_only) | 0.1026 (constant_mix) | 0.0676 [0.0577, 0.0771] | 0.0336 [0.0240, 0.0435] |  |  |

## Phase 3 hand-over (volatility block)

| scenario | coverage | runs with NO resolvable step | mandate oracle | best L5 | best trivial | gap oracle->L5 | gap L5->trivial | ordering | both gaps > 0 |
|---|---|---|---|---|---|---|---|---|---|
| flat | 0.378 | 0/150 (0%) | 0.0029 | 0.0551 (full) | 0.1006 (constant_mix) | 0.0523 [0.0464, 0.0588] | 0.0455 [0.0390, 0.0514] |  |  |
| crash | 0.585 | 0/150 (0%) | 0.0022 | 0.0301 (full) | 0.1004 (constant_mix) | 0.0279 [0.0250, 0.0309] | 0.0703 [0.0672, 0.0732] |  |  |
| bull_trap | 0.637 | 0/150 (0%) | 0.0033 | 0.0262 (full) | 0.1011 (constant_mix) | 0.0229 [0.0195, 0.0269] | 0.0749 [0.0709, 0.0783] |  |  |
| sustained_bull | 0.044 | 15/150 (10%) | 0.0015 | 0.0724 (price_only) | 0.1026 (constant_mix) | 0.0709 [0.0607, 0.0805] | 0.0302 [0.0205, 0.0405] |  |  |

## Phase 2 hand-over

| scenario | coverage | runs with NO resolvable step | mandate oracle | best L5 | best trivial | gap oracle->L5 | gap L5->trivial | ordering | both gaps > 0 |
|---|---|---|---|---|---|---|---|---|---|
| flat | 0.128 | 6/150 (4%) | 0.0022 | 0.0727 (price_only) | 0.1017 (constant_mix) | 0.0706 [0.0631, 0.0784] | 0.0289 [0.0211, 0.0363] |  |  |
| crash | 0.422 | 0/150 (0%) | 0.0023 | 0.0248 (full) | 0.1004 (constant_mix) | 0.0225 [0.0193, 0.0264] | 0.0756 [0.0717, 0.0789] |  |  |
| bull_trap | 0.539 | 0/150 (0%) | 0.0031 | 0.0376 (full) | 0.1005 (constant_mix) | 0.0345 [0.0291, 0.0405] | 0.0630 [0.0569, 0.0683] |  |  |
| sustained_bull | 0.031 | 15/150 (10%) | 0.0012 | 0.0857 (full) | 0.1028 (constant_mix) | 0.0844 [0.0749, 0.0943] | 0.0171 [0.0072, 0.0266] |  |  |

## What moved between the Phase-3 and Phase-4 hand-overs

| scenario | coverage P3 | coverage P4 | undefined-MCR share P3 | P4 |
|---|---|---|---|---|
| flat | 0.378 | 0.378 | 0% | 0% |
| crash | 0.585 | 0.553 | 0% | 0% |
| bull_trap | 0.637 | 0.646 | 0% | 0% |
| sustained_bull | 0.044 | 0.044 | 10% | 10% |
