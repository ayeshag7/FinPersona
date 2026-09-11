# E7.1b / E7.1c -- theta_cost and theta_var, derived from files

## theta_cost = 2c/f (primary horizon: one FIT half-life, f = 1/2 -> 4c)

- cost tier **5.0 bp per trade** (c = 0.000500), charged on |traded value|; round trip = 2 trades
- FIT half-life **22.3809 d** [18.75, 32.64] (n = 417)
- band width w = hi - lo cancels: [0.19999999999999996, 0.2, 0.20000000000000007]

**theta_cost = 0.002000** for every persona.

| horizon | f | theta_cost |
|---|---|---|
| one half-life (22.4 d) — **primary** | 0.5000 | **0.002000** |
| one day (sensitivity) | 0.0305 | 0.032791 |
| one day at h = 18.75 | 0.0363 | 0.027553 |
| one day at h = 32.64 | 0.0210 | 0.047590 |
| infinite (sensitivity) | 1.0000 | 0.001000 |

### The numeric check on a synthetic case (PREREG 1.2)

An AR(1)-decaying x on a constant fundamental, held 22 days (f realised = 0.4941); two policies differing by exactly w in risky weight, both through the real `PortfolioV2` at 5.0 bp.

| band width w | closed form at this horizon | numeric break-even | relative error |
|---|---|---|---|
| 0.10 | 0.002024 | 0.002027 | 0.14% |
| 0.20 | 0.002024 | 0.002026 | 0.08% |
| 0.40 | 0.002024 | 0.002025 | 0.05% |

Spread of the numeric break-even across band widths: **1.83e-06** — the cancellation of w is measured, not only algebraic. Worst relative error **0.14%** (within the pre-registered 10 %).

### Cost-tier sensitivity: what tier would put theta_cost on the grid

| grid theta | c required | bp per trade required | multiple of the implemented tier |
|---|---|---|---|
| 0.03 | 0.00750 | 75.0 | 15x |
| 0.05 | 0.01250 | 125.0 | 25x |
| 0.08 | 0.02000 | 200.0 | 40x |
| 0.12 | 0.03000 | 300.0 | 60x |
| 0.20 | 0.05000 | 500.0 | 100x |

## theta_var — one within-run sd of x at T = 200 (read, not re-estimated)

**theta_var = 0.046321**, inside the AR(1) reference band [0.03892, 0.07235] at the FIT half-life (n = 400 reps at T = 200; the generator's own median over n_gen = 500 flat seeds).

Sensitivity: the **stationary** sd s_x = 0.065609 (E6.6's variance identity) — what x's sd would be over an unbounded run, not within a 200-day one.

