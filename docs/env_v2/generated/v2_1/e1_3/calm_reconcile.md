# Calm-reference reconciliation (PREREG_PHASE_1_ADDENDUM.md section 6.2)

Grid panel: 800 paths, 160000 rows, 111843 calm rows (generator phase label). SEP-after panel: 1600 paths, 320000 rows, 148697 calm rows.

| reader \ panel | E1.3 grid panel (in-force point) | SEP-after panel |
|---|---|---|
| E1.3 surrogate (calm = generator phase label) | 0.155 [0.090, 0.176] (n 95843) | 0.086 [0.042, 0.122] (n 119663) |
| audit l2_surrogate, level-free (calm = audit phase group) | 0.155 [0.090, 0.176] (n 95843) | 0.086 [0.042, 0.122] (n 119663) |
| E1.3 surrogate, flat scenario only | 0.152 [0.063, 0.170] (n 36000) | 0.067 [0.000, 0.121] (n 36000) |

Reading: a row difference is the panel (composition, hidden vs rendered features); a column difference is the reader (feature construction, calm definition). The Phase-6 reference should be the cell that matches the published audit (audit reader on the SEP).
