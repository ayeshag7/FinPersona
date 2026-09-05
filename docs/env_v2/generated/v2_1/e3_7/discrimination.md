# E3.7 the discrimination table on the Phase-3 hand-over (PREREG_PHASE_3.md section 11)

E3.7: E2.7's policy-spread table (16A G1's shape) on the Phase-3 hand-over, beside Phase 2's, same design (40 training seeds, 50 scored seeds, three personas x four scenarios).

**Rule:** no pass/fail -- G1 is Phase 6's gate; a collapse in any scenario is a finding for the team.

## Phase 3 hand-over (volatility block in force)

| scenario | coverage | runs with NO resolvable step | mandate oracle | best L5 | best trivial | gap oracle->L5 | gap L5->trivial | ordering | both gaps > 0 |
|---|---|---|---|---|---|---|---|---|---|
| flat | 0.378 | 0/150 (0%) | 0.0029 | 0.0551 (full) | 0.1006 (constant_mix) | 0.0523 [0.0464, 0.0588] | 0.0455 [0.0390, 0.0514] | yes | yes |
| crash | 0.585 | 0/150 (0%) | 0.0022 | 0.0301 (full) | 0.1004 (constant_mix) | 0.0279 [0.0250, 0.0309] | 0.0703 [0.0672, 0.0732] | yes | yes |
| bull_trap | 0.637 | 0/150 (0%) | 0.0033 | 0.0262 (full) | 0.1011 (constant_mix) | 0.0229 [0.0195, 0.0269] | 0.0749 [0.0709, 0.0783] | yes | yes |
| sustained_bull | 0.044 | 15/150 (10%) | 0.0015 | 0.0724 (price_only) | 0.1026 (constant_mix) | 0.0709 [0.0607, 0.0805] | 0.0302 [0.0205, 0.0405] | yes | yes |

## Phase 2 hand-over (old GARCH shape, CAL jumps, v2 IV)

| scenario | coverage | runs with NO resolvable step | mandate oracle | best L5 | best trivial | gap oracle->L5 | gap L5->trivial | ordering | both gaps > 0 |
|---|---|---|---|---|---|---|---|---|---|
| flat | 0.128 | 6/150 (4%) | 0.0022 | 0.0727 (price_only) | 0.1017 (constant_mix) | 0.0706 [0.0631, 0.0784] | 0.0289 [0.0211, 0.0363] | yes | yes |
| crash | 0.422 | 0/150 (0%) | 0.0023 | 0.0248 (full) | 0.1004 (constant_mix) | 0.0225 [0.0193, 0.0264] | 0.0756 [0.0717, 0.0789] | yes | yes |
| bull_trap | 0.539 | 0/150 (0%) | 0.0031 | 0.0376 (full) | 0.1005 (constant_mix) | 0.0345 [0.0291, 0.0405] | 0.0630 [0.0569, 0.0683] | yes | yes |
| sustained_bull | 0.031 | 15/150 (10%) | 0.0012 | 0.0857 (full) | 0.1028 (constant_mix) | 0.0844 [0.0749, 0.0943] | 0.0171 [0.0072, 0.0266] | yes | yes |

## The change, scenario by scenario (Phase 2 -> Phase 3)

| scenario | coverage | runs with no resolvable step | gap L5->trivial |
|---|---|---|---|
| flat | 0.128 -> 0.378 | 4% -> 0% | 0.0289 -> 0.0455 |
| crash | 0.422 -> 0.585 | 0% -> 0% | 0.0756 -> 0.0703 |
| bull_trap | 0.539 -> 0.637 | 0% -> 0% | 0.0630 -> 0.0749 |
| sustained_bull | 0.031 -> 0.044 | 10% -> 10% | 0.0171 -> 0.0302 |
