# E4.5 - the sustained-bull control, four definitions (REG-7)

`python -m tools.phase4.e4_5_control` - PREREG_PHASE_4.md section 7.

500 seeds per definition, 500 flat seeds for the discrimination audit.
**D14 is open: no definition is adopted here.** The audits are delivered so the team can state the control's purpose on numbers.

The v2 `V_T/V_1 >= 1.2` threshold was stipulated; the FIT replacement is **1.3233** (P10 of the 200-day-equivalent price growth of run-ups that did NOT top within 200 days (E4.1 runup4.csv, topped == False); log-scaled from the 504-day window, n = 2849 / 398).

| definition | rejection | sd(x) median | path-mean x P10/P50/P90 | selection (KS) | classifier acc | null p95 | at chance |
|---|---|---|---|---|---|---|---|
| A | 0.162 | 0.0467 | [-0.04, 0.004, 0.04] | TESTED | 0.5359906626707437 | 0.5389745351092091 | **True** |
| B | 0.162 | 0.0467 | [-0.04, 0.004, 0.04] | TESTED | 0.5359906626707437 | 0.5389745351092091 | **True** |
| C | 0.358 | 0.0234 | [-0.007, 0.001, 0.007] | TESTED | 0.6058220319953185 | 0.6064793581883382 | **True** |
| D | 0.162 | 0.0467 | [-0.04, 0.004, 0.04] | TESTED | 0.5359906626707437 | 0.5389745351092091 | **True** |

## Selection audit detail

### A

- status: **TESTED** - UNDECIDABLE at n_acc = 419 / n_rej = 81: the equivalence bound 0.1 is below the null floor 0.200
- rejected paths: 81 of 500
- rejection reasons: {'sustained_bull': 81}

| field | KS | bootstrap 95 % upper | passes (< 0.10) |
|---|---|---|---|
| sd_r | 0.0814 | 0.1856 | False |
| acf1 | 0.0603 | 0.1818 | False |
| iv_mean | 0.1874 | 0.2857 | False |

### B

- status: **TESTED** - UNDECIDABLE at n_acc = 419 / n_rej = 81: the equivalence bound 0.1 is below the null floor 0.200
- rejected paths: 81 of 500
- rejection reasons: {'sustained_bull': 81}

| field | KS | bootstrap 95 % upper | passes (< 0.10) |
|---|---|---|---|
| sd_r | 0.0814 | 0.1856 | False |
| acf1 | 0.0603 | 0.1818 | False |
| iv_mean | 0.1874 | 0.2857 | False |

### C

- status: **TESTED** - UNDECIDABLE at n_acc = 321 / n_rej = 179: the equivalence bound 0.1 is below the null floor 0.157
- rejected paths: 179 of 500
- rejection reasons: {'sustained_bull': 179}

| field | KS | bootstrap 95 % upper | passes (< 0.10) |
|---|---|---|---|
| sd_r | 0.4744 | 0.5490 | False |
| acf1 | 0.1017 | 0.1913 | False |
| iv_mean | 0.4339 | 0.5110 | False |

### D

- status: **TESTED** - UNDECIDABLE at n_acc = 419 / n_rej = 81: the equivalence bound 0.1 is below the null floor 0.200
- rejected paths: 81 of 500
- rejection reasons: {'sustained_bull': 81}

| field | KS | bootstrap 95 % upper | passes (< 0.10) |
|---|---|---|---|
| sd_r | 0.0814 | 0.1856 | False |
| acf1 | 0.0603 | 0.1818 | False |
| iv_mean | 0.1874 | 0.2857 | False |
