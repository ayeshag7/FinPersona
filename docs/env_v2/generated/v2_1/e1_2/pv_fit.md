# E1.2 estimator B: log(P/V_hat) AR(1) with Andrews' median-unbiased correction (PREREG_PHASE_1.md section 4.2)

Set A, monthly 2009-06-30 .. 2024-12-31, EDGAR quarterly EPS (dedup on (concept, start, end), earliest filing; Q4 = FY - 3Q where needed), V_hat = EPS_ttm x median trailing P/E (sector where >= 5 names, else market); a stock needs >= 60 consecutive valid months. Medians over stocks with a 1000-resample bootstrap. sigma_V here is the sd of delta log V_hat and is OVERSTATED by the measurement noise in V_hat. Survivor caveat: set A (REG-15).

| EPS concept | multiple | n stocks | undefined months | h (days), median-unbiased: median [CI]; IQR | h OLS | s_x | sigma_V/day (dlog V_hat) | rho_MU at grid top |
|---|---|---|---|---|---|---|---|---|
| EarningsPerShareBasic | sector | 367 | 19.5% | 256 [223, 277]; 152-626 | 167 [153, 185]; 116-259 | 0.390 [0.361, 0.437]; 0.268-0.577 | 0.03406 [0.03148, 0.03678]; 0.02257-0.05207 | 15.0% |
| EarningsPerShareBasic | market | 367 | 19.5% | 290 [268, 350]; 175-756 | 187 [176, 201]; 130-302 | 0.404 [0.369, 0.441]; 0.281-0.589 | 0.03263 [0.02983, 0.03540]; 0.01987-0.05051 | 18.8% |
| EarningsPerShareDiluted | sector | 366 | 19.5% | 259 [227, 286]; 155-596 | 168 [156, 184]; 117-263 | 0.395 [0.374, 0.437]; 0.275-0.579 | 0.03409 [0.03176, 0.03665]; 0.02272-0.05151 | 14.2% |
| EarningsPerShareDiluted | market | 366 | 19.5% | 294 [266, 353]; 177-780 | 186 [174, 196]; 130-303 | 0.408 [0.374, 0.450]; 0.286-0.595 | 0.03234 [0.03035, 0.03521]; 0.01972-0.05056 | 17.8% |
