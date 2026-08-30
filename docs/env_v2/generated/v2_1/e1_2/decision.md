# E1.2 decision (PREREG_PHASE_1.md sections 4.4-4.5)

| estimator | data h (d) [CI] | s_x [CI] | sigma_V/day [CI] | nearest cell | median rel. error / RMSE / coverage per cell | usable |
|---|---|---|---|---|---|---|
| A: variance ratios (set A, full sample) | 5 [4, 6] | 0.024 [0.022, 0.026] | 0.0205 [0.0197, 0.0213] | h 5 (data h outside the grid) | (5, 0.012): 0.26 / 0.27 / 0.00 | False |
| B: log(P/V_hat) AR(1), median-unbiased (set A, EPS basic, sector multiple) | 256 [223, 277] | 0.390 [0.361, 0.437] | - | h 250 | (250, 0.006): 0.83 / 0.83 / 0.00; (250, 0.012): 0.83 / 0.83 / 0.00 | False |
| C: SMM on persistence-carrying moments (set A) | 5 [4, 5] | 0.129 [0.125, 0.135] | 0.0196 [0.0189, 0.0204] | h 5 (data h outside the grid) | (5, 0.012): 0.05 / 0.07 / - | True |

**h / s_x:** {"adopted": "C", "h": 4.824109112705985, "h_ci": [4.166130668323864, 5.422012905642471], "s_x": 0.12857809971634016, "s_x_ci": [0.12474117720396251, 0.13459706622814746], "reason": "smallest RMSE among usable estimators whose data interval contains the other usable estimators' points (usable: ['C'])"}

**sigma_V:** {"adopted": "C", "value": 0.019572114532101025, "ci": [0.01892494449362432, 0.020357152969418254], "reason": "the only usable estimator with a sigma_V"}
