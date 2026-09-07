# The discrimination table on the Phase-5 hand-over

the policy-spread table (16A G1's shape) on the Phase-5 hand-over, beside Phase 4's, Phase 3's and Phase 2's, same design (40 training seeds, 50 scored seeds, three personas x four scenarios); the Phase-5 oracle encodes a rendered 'n/m' P/E as the cap plus an indicator, as the audit does

**Rule:** no pass/fail -- G1 is Phase 6's gate; a collapse in any scenario is a finding for the team.

What Phase 5 changed that could move this table:

- the multiple is FIT and wanders (design B): P/E no longer reads x through a constant k
- trailing EPS can be non-positive (the loss chain) and P/E renders 'n/m' on those days
- the analyst field is a price proxy (design C), not V e^u
- sentiment is a returns-only FIT process (design A) with no term in x
- volume has no |x| loading (design A)
- the announcement lags are FIT (P50 19 trading days) and dividends follow a FIT Lintner chain with a payer draw

## Phase 5 hand-over (observables block in force)

| scenario | coverage | runs with NO resolvable step | mandate oracle | best L5 | best trivial | gap oracle->L5 | gap L5->trivial | ordering | both gaps > 0 |
|---|---|---|---|---|---|---|---|---|---|
| flat | 0.362 | 0/150 (0%) | 0.0029 | 0.0627 (level_free) | 0.1006 (constant_mix) | 0.0598 [0.0543, 0.0656] | 0.0379 [0.0321, 0.0434] |  |  |
| crash | 0.543 | 0/150 (0%) | 0.0023 | 0.0427 (level_free) | 0.1003 (constant_mix) | 0.0405 [0.0369, 0.0439] | 0.0576 [0.0542, 0.0611] |  |  |
| bull_trap | 0.636 | 0/150 (0%) | 0.0033 | 0.0413 (level_free) | 0.1008 (constant_mix) | 0.0380 [0.0325, 0.0434] | 0.0595 [0.0540, 0.0650] |  |  |
| sustained_bull | 0.354 | 0/150 (0%) | 0.0029 | 0.0631 (full) | 0.1009 (constant_mix) | 0.0602 [0.0530, 0.0675] | 0.0378 [0.0305, 0.0450] |  |  |

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

## What moved between the Phase-4 and Phase-5 hand-overs

| scenario | coverage P4 | coverage P5 | undefined-MCR share P4 | P5 | gap oracle->L5 P4 | P5 |
|---|---|---|---|---|---|---|
| flat | 0.378 | 0.362 | 0% | 0% | 0.0534 | 0.0598 |
| crash | 0.553 | 0.543 | 0% | 0% | 0.0356 | 0.0405 |
| bull_trap | 0.646 | 0.636 | 0% | 0% | 0.0287 | 0.0380 |
| sustained_bull | 0.044 | 0.354 | 10% | 0% | 0.0676 | 0.0602 |
