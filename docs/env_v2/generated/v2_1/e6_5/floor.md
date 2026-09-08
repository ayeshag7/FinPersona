# E6.5 — the L1 noise floor derived from the x process

s_x = 0.0656 (the volatility identity, with the jumps), Appendix-B bound B = 0.2005 (day 200) / 0.1773 (window average); panel `docs/env_v2/generated/v2_1/_panels/sep_phase5_after.pkl` (1600 paths, 320,000 rows).

| τ | trivial (Gaussian, x̂ = 0) | trivial (empirical P(\|x\| ≤ τ) [CI]) | informed ceiling at B(day 200) | at B(window avg) |
|---|---|---|---|---|
| 1% | 0.121 | 0.095 [0.092, 0.098] | **0.135** | 0.133 |
| 2% | 0.240 | 0.190 [0.184, 0.196] | **0.267** | 0.263 |
| 5% | 0.554 | 0.426 [0.416, 0.437] | **0.606** | 0.599 |

**Derived rule (τ = 5 %):** within-5 % share ≤ 0.606 + 0.011 = **0.617**. for tau in {1 %, 2 %, 5 %}: a candidate's within-tau share may not exceed the informed ceiling 2*Phi(tau / (s_x*sqrt(1 - B))) - 1 (B = the Appendix-B day-T bound) plus the share's sampling half-width at the panel's n of paths; the trivial line is the generator's own P(|x| <= tau) with its CI, reported beside price itself.

| candidate (source) | within-5 % | above the trivial line | passes the derived ceiling |
|---|---|---|---|
| k * P (price itself) (e5_after L1) | 0.426 | yes | **PASS** |
| k * P * dividend_yield (e5_after L1) | 0.036 | no | **PASS** |
| k * P / reported_PE (e5_after L1) | 0.036 | no | **PASS** |
| k * analyst_fair_value (e5_after L1) | 0.030 | no | **PASS** |
| k*price (e5_7b/final l1ext) | 0.426 | yes | **PASS** |
| k*P/PE (e5_7b/final l1ext) | 0.033 | no | **PASS** |
| k*P*DY (e5_7b/final l1ext) | 0.036 | no | **PASS** |
| k*F (e5_7b/final l1ext) | 0.030 | no | **PASS** |
| k*sqrt(price*P/PE) (e5_7b/final l1ext) | 0.072 | no | **PASS** |
| k*sqrt(price*P*DY) (e5_7b/final l1ext) | 0.074 | no | **PASS** |
| k*sqrt(price*F) (e5_7b/final l1ext) | 0.065 | no | **PASS** |
| lsq(price) (e5_7b/final l1ext) | 0.397 | no | **PASS** |
| lsq(P/PE) (e5_7b/final l1ext) | 0.206 | no | **PASS** |
| lsq(P*DY) (e5_7b/final l1ext) | 0.189 | no | **PASS** |
| lsq(F) (e5_7b/final l1ext) | 0.216 | no | **PASS** |
| lsq(price+P/PE) (e5_7b/final l1ext) | 0.376 | no | **PASS** |
| lsq(price+P*DY) (e5_7b/final l1ext) | 0.343 | no | **PASS** |
| lsq(price+F) (e5_7b/final l1ext) | 0.399 | no | **PASS** |
| lsq(P/PE+P*DY) (e5_7b/final l1ext) | 0.175 | no | **PASS** |
| lsq(P/PE+F) (e5_7b/final l1ext) | 0.201 | no | **PASS** |
| lsq(P*DY+F) (e5_7b/final l1ext) | 0.187 | no | **PASS** |
| lsq(price+P/PE+P*DY) (e5_7b/final l1ext) | 0.323 | no | **PASS** |
| lsq(price+P/PE+F) (e5_7b/final l1ext) | 0.377 | no | **PASS** |
| lsq(price+P*DY+F) (e5_7b/final l1ext) | 0.345 | no | **PASS** |
| lsq(P/PE+P*DY+F) (e5_7b/final l1ext) | 0.175 | no | **PASS** |
| median(valuation candidates) (e5_7b/final l1ext) | 0.043 | no | **PASS** |
| best = k*price (e5_7b/final l1ext (best)) | 0.426 | yes | **PASS** |
