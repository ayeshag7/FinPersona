# Phase 5 decisions (tools/phase5/e5_decide.py)

Pending: none

Design: `{"width": "P10-P90", "eps": "v21", "dividend": "v21", "dividend_field": "shown", "analyst_field": "shown", "multiple": "B", "analyst": "C", "analyst_sd": 0.5639913617919751, "sentiment": "A", "sentiment_link": "full", "volume": "A"}`

Status: `{"multiple": "ADOPTED", "eps": "ADOPTED", "dividend": "ADOPTED", "analyst": "PROVISIONAL", "sentiment": "PROVISIONAL", "volume": "ADOPTED"}`

## E5.1 -- the multiple (PREREG 4.3; ADDENDUM 5)

| arm | KS vs truncated data (upper 95 %) | KS vs untruncated | qualifies | dR2_add(VAL) x, all [paired CI] | calm | inversion share |
|---|---|---|---|---|---|---|
| multiple_A_P10-P90 | 0.095 pass | 0.112 fail | True | +0.0254 [+0.0134, +0.0367] | +0.0202 [+0.0100, +0.0309] | 0.4163 [0.4057, 0.4263] |
| multiple_B_P10-P90 | 0.152 fail | 0.082 pass | True | +0.0114 [+0.0027, +0.0204] | +0.0388 [+0.0272, +0.0508] | 0.4163 [0.4057, 0.4263] |

Paired dR2_add(VAL) A - B (x, P-all): **+0.0139 [+0.0014, +0.0256]** -> rule: B iff the CI lies above zero, else A -> **B**

## E5.2 / E5.3 -- EPS and dividends (no contest; D10 both variants)

dR2_add(VAL) x, all: shown +0.0897 [+0.0747, +0.1045]; hidden +0.0515 [+0.0399, +0.0628]; paired shown - hidden +0.0382 [+0.0292, +0.0480]. n/m share rendered 0.06193125 vs data 0.08477005610385356.

## E5.4 -- the analyst (PREREG 7.3)

Permutation null margin, ANALYST (x, P-all): -0.00574 (max -0.00567, 20 draws)

| arm | dR2_add(ANALYST) x, all [paired CI] | calm | inside null margin | onset (non-price rule) | worst group excess (transition, vs null p95) | admissible |
|---|---|---|---|---|---|---|
| analyst_A_sd0.300 | +0.0013 [-0.0024, +0.0048] | +0.0187 [+0.0056, +0.0303] | False | FAIL crash:calm->deterioration:analyst_fair_value | +0.021 at crash:calm->deterioration (p95 +0.001) | False |
| analyst_A_sd0.450 | +0.0018 [-0.0017, +0.0051] | +0.0175 [+0.0056, +0.0293] | False | FAIL crash:calm->deterioration:analyst_fair_value | +0.018 at crash:calm->deterioration (p95 +0.001) | False |
| analyst_A_sd0.564 | +0.0020 [-0.0015, +0.0053] | +0.0142 [+0.0012, +0.0268] | False | FAIL crash:calm->deterioration:analyst_fair_value | +0.017 at crash:calm->deterioration (p95 +0.001) | False |
| analyst_A_sd0.600 | +0.0017 [-0.0016, +0.0050] | +0.0126 [+0.0006, +0.0249] | False | FAIL crash:calm->deterioration:analyst_fair_value | +0.018 at crash:calm->deterioration (p95 +0.002) | False |
| analyst_C | -0.0017 [-0.0046, +0.0014] | +0.0145 [+0.0031, +0.0244] | - | PASS | -0.037 at bull_trap:blow-off->post-top (p95 +0.032) | - |

Verdict: **no A arm admissible -> C provisional**

## E5.5 -- sentiment (PREREG 8.3; ADDENDUM 3; D15 is the team's)

| design | meets rule (i) | dR2_add(SENT) x, all [paired CI] | calm | paired minus A | onset (SENT fields, non-price rule) |
|---|---|---|---|---|---|
| A | True | -0.0007 [-0.0012, -0.0002] | +0.0029 [-0.0005, +0.0064] | - | PASS |
| B-full | True | +0.0813 [+0.0731, +0.0883] | +0.0212 [+0.0151, +0.0274] | +0.0819 [+0.0740, +0.0890] | PASS |
| B-half | True | +0.0205 [+0.0168, +0.0236] | +0.0056 [+0.0010, +0.0109] | +0.0211 [+0.0176, +0.0242] | PASS |
| C | False | -0.0009 [-0.0021, +0.0003] | +0.0073 [+0.0006, +0.0146] | - | PASS |

Verdict (the rule's selection; D15 is the team's): **A**

## E5.6 -- volume (PREREG 9.3; ADDENDUM 2)

Run-up log ratio -0.0150 [-0.03198314965052025, -0.001463636866971473] (n = 3019): clause 1 by the letter True, in the premise's direction False; clause 2 (B's onset) True.

dR2_add(VOL) x, all: A +0.0042 [+0.0026, +0.0059]; B +0.0036 [+0.0021, +0.0051]; paired A - B +0.0006 [+0.0002, +0.0011].

Verdict: letter **B**, ADDENDUM section 2 reading **A** (adopted)

