# E4.0 / PP: decidability of the Phase-4 thresholds

Simulated before the experiments they protect (`python -m tools.phase4.prereg_power`).

| Row | Rule | Registered n | Verdict |
|---|---|---|---|
| PP1 | E4.6 coverage >= 0.70 (DESIGN margin), one-sided alpha 0.05 | 500 | DECIDABLE |
| PP2 | REG-18: generator topped share inside the panel's topped-share CI | see json | CONDITIONAL: decidable only if the panel yields enough resolvable run-ups; REG-18's own fallback (report all three, keep the {0.5x,1x,2x} bracket) is pre-registered for n_panel < 30 and is the expected branch |
| PP3 | E4.4 cap binds on < 5 % of mania days (upper 95 % bootstrap limit) | 500 | DECIDABLE |
| PP4 | accuracy <= 95th percentile of a label-permutation null (+1 pp for E4.7) | see json | DECIDABLE for a 5 pp departure at 500 seeds. These two rows BRACKET the null rather than estimate it: the day-level row assumes days are independent (too tight) and the seed-level row assumes a seed contributes one independent bit (too loose). The true null lies between and is computed empirically, by permuting seed labels on the real runs, inside E4.5(iii) and E4.7(b) |
| PP5 | generator median rise-time 95 % CI overlaps the panel fast-crash CI [29, 35] | see json | UNDERPOWERED under Appendix A's 'half-width <= band/5' convention: at a cross-seed sd of 25 d the n = 500 half-width is about 2.8 d against the band/5 = 1.2 d. The rule as registered is an OVERLAP rule, not a band/5 rule, and is decidable at n = 500; the band/5 convention would need n > 2600. Registered consequence: the overlap rule stands and the half-width is reported beside it, so a marginal overlap is visible as marginal |
| PP6 | post-top realised variance ratio 95 % CI contains 1.16 | see json | DECIDABLE |

## PP1 - E4.6 coverage

Appendix A requires n = 534 for 80 % power against a true 0.65 at p0 = 0.70.

| n | SE at p0 | power vs true 0.65 |
|---|---|---|
| 200 | 0.0324 | 0.47 |
| 500 | 0.0205 | 0.78 |

## PP3 - E4.4 cap binding

| true binding share | mean upper 95 % limit | share passing |
|---|---|---|
| 0.0 | 0.0000 | 1.00 |
| 0.01 | 0.0110 | 1.00 |
| 0.02 | 0.0214 | 1.00 |
| 0.05 | 0.0523 | 0.04 |
| 0.08 | 0.0828 | 0.00 |

## PP4 - the permutation null

| n seeds | null p95 (clustered by seed) | null p95 (day-level, naive) | detectable departure |
|---|---|---|---|
| 200 | 0.5600 | 0.5043 | 8.78 pp |
| 500 | 0.5360 | 0.5026 | 5.51 pp |

registered consequence: the permutation is over SEED labels, not day labels, because days within a path share a schedule draw and are dependent; permuting day labels gives a p95 of about 0.503, which would call almost any classifier a leak. REG-9's '+1 pp' margin is the day-level sampling half-width at 200 seeds and is small next to the seed-clustered null's own spread, so the null percentile -- not the margin -- is what decides the rule

## PP5 - E4.2 rise time

UNDERPOWERED under Appendix A's 'half-width <= band/5' convention: at a cross-seed sd of 25 d the n = 500 half-width is about 2.8 d against the band/5 = 1.2 d. The rule as registered is an OVERLAP rule, not a band/5 rule, and is decidable at n = 500; the band/5 convention would need n > 2600. Registered consequence: the overlap rule stands and the half-width is reported beside it, so a marginal overlap is visible as marginal

## PP6 - E4.8 post-top

Phase 3 measured the incumbent floor at 1.59 with n = 20 -- an n the review caught being quoted without it.  At n = 500 the half-width is small enough that a floor at 1.59 is distinguishable from 1.16 at any plausible spread, so the rule is decidable; what is NOT decidable in advance is whether an admissible shape exists, which is why the pre-registration states the 'not met' branch explicitly
