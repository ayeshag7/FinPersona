# E4.14 - item 73: where the crash's fundamental decline falls

`python -m tools.phase4.e4_14_crash_v`

270 fast-crash episodes have EDGAR coverage; 106 of them have a falling V-hat over the episode.

| window | median share of the total log decline | 95 % CI | n |
|---|---|---|---|
| peak -> onset (deterioration) | 0.000 | [0.000, 0.000] | 106 / 96 |
| onset -> trough (panic) | 0.024 | [0.000, 0.156] | 106 / 96 |
| trough -> +60 d (stabilisation) | 0.891 | [0.631, 1.000] | 106 / 96 |

v2's shape asserts 1.0 / 0.0 / 0.0.

**Verdict: v2's SHAPE IS REJECTED on its central claim -- the fundamental proxy shows ZERO decline in the deterioration window (share 0.000 [0.000, 0.000], n = 106/96) where v2 delivers 100 % of D_V there. The MAGNITUDE of the tail is not identified by this proxy (see delag_sensitivity), so no point value is adopted: item 73 closes as TESTED and REJECTED in direction, with the fitted magnitude left open.**
