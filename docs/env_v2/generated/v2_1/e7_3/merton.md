# E7.3 — the Merton table on the environment's own fitted risk and return

Measured on the frozen v2.1 generator, 500 seeds per scenario (seeds 40000..), T = 200, 252 trading days a year, dividends paid into cash on the generator's own ex-dates. Cluster-bootstrap 95 % intervals over paths (500 resamples). Risk-free rate **0**: cash does not accrue in this environment.

## The environment's own (mu, sigma)

| scenario | mu (total return) | sigma (total return) | mu (price only) | sigma (price only) | realised dividend yield | payer share |
|---|---|---|---|---|---|---|
| flat (primary) | 0.0874 [0.0618, 0.1151] | 0.3468 [0.3381, 0.3556] | 0.0548 | 0.3456 | 0.03421 | 0.908 |
| bull_trap | 0.5289 [0.5058, 0.5541] | 0.3834 [0.3727, 0.3968] | 0.5006 | 0.3826 | 0.03300 | 0.904 |
| crash | -0.3211 [-0.3503, -0.2931] | 0.6591 [0.6305, 0.6935] | -0.3580 | 0.6583 | 0.03209 | 0.906 |
| sustained_bull | 0.6209 [0.5973, 0.6406] | 0.3464 [0.3381, 0.3552] | 0.5902 | 0.3454 | 0.04002 | 0.904 |

The v2 documents' price-only drift of 6.5 %/yr and annual sigma of about 28 % are **superseded**: on the frozen generator the flat scenario's price-only figures are 0.0548 and 0.3456.

## Merton cash shares (flat, total return)

| gamma | risky share w* | cash share 1 - w* | cash share, unclipped | 95 % interval |
|---|---|---|---|---|
| 2 | 0.363 | **0.637** | 0.637 | [0.497, 0.756] |
| 3 | 0.242 | **0.758** | 0.758 | [0.664, 0.837] |
| 4 | 0.182 | **0.818** | 0.818 | [0.748, 0.878] |
| 6 | 0.121 | **0.879** | 0.879 | [0.832, 0.919] |
| 8 | 0.091 | **0.909** | 0.909 | [0.874, 0.939] |
| 10 | 0.073 | **0.927** | 0.927 | [0.899, 0.951] |

## Where each persona's practitioner band sits (reading A, the scored default; D9 / P7-3)

| persona | category | practitioner cash band | gammas whose Merton cash share falls inside it | nearest gamma to the band centre | Merton cash there |
|---|---|---|---|---|---|
| ISFJ | conservative | 0.70–0.90 | [3, 4, 6] | 4 | 0.818 |
| INTJ | balanced | 0.40–0.60 | — | 2 | 0.637 |
| ENTJ | aggressive | 0.00–0.20 | — | 2 | 0.637 |

## The JFE ordering check

**Not run.** Jiang, Peng & Yan (2024, JFE) Table 7 gives trait coefficients on the equity-to-wealth ratio, not a conservative-minus-aggressive spread; no spread is derivable from it without a persona-to-trait mapping and a trait-score scale that the paper does not supply. v2.1 Phase 7 E7.3 withdrew the constant and removed the ordering check rather than keep an unsourced number.

