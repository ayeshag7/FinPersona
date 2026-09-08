# Pre-registration addendum, Phase 6

Each section is a disclosure written **after** the named result was read and **before** any rule that depends on it is
applied further, in the form Phase 4 and Phase 5 used: what had been seen, why the registered rule is wrong or
incomplete, and what is done — with the disconfirmation stated as loudly as any confirmation and every result reported
under both the rule as registered and the reading recorded here. Nothing in `PREREG_PHASE_6.md` is edited to fit a
result; its pending cells are filled from files with the date of the fill.

---

## 1. The target-permutation null of the L2 selectivity sits entirely below zero, so the registered margin (p95 + half-width) is negative and cannot be passed by any information-bearing field; the centred sensitivity was registered and is reported beside

### 1.1 Disclosure

Written 9 September 2026 after `e6_6/null/null.json` (the L2 null, 20 draws on both populations, the real estimator
on the real 1,600-path panel) had been read and before the L2b null, the gates block, the final audit or 16A were read.
What had been seen:

| population | measured selectivity [paired CI] | half-width | null draws | null median | null p95 | margin as registered (p95 + hw) | verdict as registered |
|---|---|---|---|---|---|---|---|
| all rows | **+0.0263** [+0.0106, +0.0402] | 0.0148 | 20, all in [−0.063, −0.034] | **−0.0470** | **−0.0343** | **−0.0195** | FAIL |
| calm-trained | **+0.1088** [+0.0849, +0.1307] | 0.0229 | 20, all in [−0.099, −0.046] | **−0.0692** | **−0.0542** | **−0.0313** | FAIL |

Under permutation the BASE (level-free control, 45 columns) fits the random target at R² ≈ −0.004 and the FULL set
(141 columns) at ≈ −0.047 (all rows) / ≈ −0.069 (calm): every one of the 40 draws of the difference is negative.

### 1.2 Why the registered null is wrong in location, not in width

The registered statistic is a *difference* of two out-of-sample R² values from feature sets of different size. Under a
target permutation neither set carries information, and the larger set pays a larger out-of-sample overfitting penalty
(the GBT spends splits on 96 more noise columns), so the difference's null is centred at **the penalty difference**,
not at zero — the same defect P5-16 found in the column-permutation null, whose location was the cost of noise columns.
The prereg (7.4) anticipated a null "below zero, with its p95 near zero" and registered the centred margin as the
sensitivity; the measured location is further below zero than anticipated, so the plan's letter gives a *negative*
margin — a rule that no field can pass whatever it carries. That is a mis-specified criterion, and the phase's own
rule (10.3; PREREG 14) is that a mis-specified criterion is disclosed and reported under both forms, not re-specified.

The width is right: the null's spread (max − min ≈ 0.03 all rows, 0.05 calm) and the paired half-width (0.015 / 0.023)
are the scales the statistic actually fluctuates on.

### 1.3 The reading, stated now, before the remaining gates are read

- **As registered (the plan's letter):** FAIL on both populations. Written to `phase6_criteria.json` (`gates.l2_all`,
  `gates.l2_calm`, `margin`, `pass`) exactly so, and asserted so by `test_l2_gate_derived`.
- **The registered sensitivity (centred: p95 − median + half-width):** all rows **+0.0275 → PASS by 0.0012**
  (0.0263 ≤ 0.0275; the sampling half-width is 0.0148, so this is inside one half-width of the margin — *undecided
  at 20 draws* is the honest label, and the prereg's section 14 rule applies: the draw count is raised, not the
  rule); calm-trained **+0.0379 → FAIL** (0.1088 exceeds it by 0.071, five half-widths). Written beside as
  `centred_margin` / `pass_centred`.
- **What the calm-trained failure is:** the fields' calm-trained contribution that Phase 5 measured (full-field
  0.3950 − level-free 0.2912 = 0.104; the largest carrier VAL at +0.051, the wandering multiple as a slow signal,
  IV +0.019, LEVELS +0.023) is above any margin this null can give. It is information about x that a calm-day reader
  can take from the fields and cannot take from the price path. It is reported as a FAIL of the derived gate, and it is
  D17's (a Phase-5 field decision or D3) — not this phase's to repair.
- **Consequence for the registry:** `test_v2_L2_surrogate_thresholds` is re-expressed as the derived gate; the
  entry stays, its reason names the derived margin and the centred sensitivity's two readings, and its owner is Phase 7 /
  D17. The registry is not emptied by this phase.

### 1.4 What is done

The draw count of the all-rows null is raised from 20 to 40 in the same tool with the same seed stream (the first 20
draws unchanged) to resolve the centred all-rows reading, which sits within a half-width of its margin; the calm-trained
and L2b verdicts do not depend on it. No margin, statistic, estimator or population is changed. The negative registered
margin is recorded in the criteria file as measured.
