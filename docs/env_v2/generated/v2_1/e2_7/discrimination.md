# E2.7 does the benchmark still discriminate? (post-review extension; PREREG_PHASE_2_ADDENDUM.md section 4.1)

E2.7: the policy spread (16A G1's shape) on the handed-over state, beside Phase 1's, on the same L5 design (40 training seeds, 50 scored seeds, three personas x four scenarios).

**Rule:** no pass/fail -- G1 is Phase 6's gate on the Phase-6 frozen generator; the ordering, the gaps and their cluster-bootstrap intervals are reported, and a collapse in any scenario is stated as a finding for the team rather than repaired here.

MCR at theta = 0.05, averaged over three personas and 50 scored seeds; intervals are a 2000-resample cluster bootstrap over seeds, with every policy resampled on the same seeds so the gaps are paired.

## Phase 2 hand-over (engine ar1_fit, sigma_V 0.0122)

| scenario | coverage | runs with NO resolvable step | mandate oracle | best L5 | best trivial | gap oracle->L5 | gap L5->trivial | ordering | both gaps > 0 |
|---|---|---|---|---|---|---|---|---|---|
| flat | 0.128 | 6/150 (4%) | 0.0022 | 0.0727 (price_only) | 0.1017 (constant_mix) | 0.0706 [0.0631, 0.0784] | 0.0289 [0.0211, 0.0363] | yes | yes |
| crash | 0.422 | 0/150 (0%) | 0.0023 | 0.0248 (full) | 0.1004 (constant_mix) | 0.0225 [0.0193, 0.0264] | 0.0756 [0.0717, 0.0789] | yes | yes |
| bull_trap | 0.539 | 0/150 (0%) | 0.0031 | 0.0376 (full) | 0.1005 (constant_mix) | 0.0345 [0.0291, 0.0405] | 0.0630 [0.0569, 0.0683] | yes | yes |
| sustained_bull | 0.031 | 15/150 (10%) | 0.0012 | 0.0857 (full) | 0.1028 (constant_mix) | 0.0844 [0.0749, 0.0943] | 0.0171 [0.0072, 0.0266] | yes | yes |

## Phase 1 hand-over (engine fw_fallback_hl150, sigma_V 0.006)

| scenario | coverage | runs with NO resolvable step | mandate oracle | best L5 | best trivial | gap oracle->L5 | gap L5->trivial | ordering | both gaps > 0 |
|---|---|---|---|---|---|---|---|---|---|
| flat | 0.743 | 0/150 (0%) | 0.0030 | 0.0568 (full) | 0.1002 (constant_mix) | 0.0538 [0.0453, 0.0636] | 0.0434 [0.0337, 0.0517] | yes | yes |
| crash | 0.811 | 0/150 (0%) | 0.0026 | 0.0326 (full) | 0.0999 (constant_mix) | 0.0300 [0.0263, 0.0339] | 0.0673 [0.0634, 0.0709] | yes | yes |
| bull_trap | 0.821 | 0/150 (0%) | 0.0033 | 0.0368 (full) | 0.1013 (constant_mix) | 0.0335 [0.0289, 0.0386] | 0.0644 [0.0594, 0.0689] | yes | yes |
| sustained_bull | 0.050 | 9/150 (6%) | 0.0017 | 0.0709 (level_free) | 0.1027 (constant_mix) | 0.0692 [0.0604, 0.0781] | 0.0318 [0.0230, 0.0405] | yes | yes |

## The change, scenario by scenario

| scenario | coverage before -> after | runs with no resolvable step | gap L5->trivial before -> after |
|---|---|---|---|
| flat | 0.743 -> 0.128 | 0% -> 4% | 0.0434 -> 0.0289 |
| crash | 0.811 -> 0.422 | 0% -> 0% | 0.0673 -> 0.0756 |
| bull_trap | 0.821 -> 0.539 | 0% -> 0% | 0.0644 -> 0.0630 |
| sustained_bull | 0.050 -> 0.031 | 6% -> 10% | 0.0318 -> 0.0171 |
