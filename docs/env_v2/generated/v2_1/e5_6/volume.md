# E5.6 volume fits (PREREG_PHASE_5.md section 9.1)

Set A, 417 stocks, 2000-01-03..2024-12-31; log volume minus its trailing 252-day mean (DESIGN: no shares outstanding in the panel). Medians over stocks with a 1000-resample stock bootstrap. set A is survivor-only (REG-15); volume dynamics of delisted names are absent.

- design A: rho_v 0.5259 [0.5224, 0.5286] (IQR 0.5044-0.5557); beta(|r|/sigma) 0.2027 [0.1983, 0.2060] (IQR 0.1795-0.2240); residual sd 0.3469 [0.3389, 0.3509] (IQR 0.3128-0.3768); sd of detrended log volume 0.4645 [0.4572, 0.4718] (IQR 0.4296-0.5026)
- design B adds beta_ru on max(ret_252, 0): rho_v 0.5231 [0.5196, 0.5258] (IQR 0.5035-0.5530); beta(|r|/sigma) 0.2028 [0.1977, 0.2065] (IQR 0.1793-0.2244); **beta_ru -0.0123 [-0.0202, -0.0056] (IQR -0.0511-0.0358)**; residual sd 0.3468 [0.3390, 0.3505] (IQR 0.3125-0.3767)

| sub-period | n stocks | rho_v | beta | sd_e | beta_ru |
|---|---|---|---|---|---|
| 2000-07 | 417 | 0.5107 | 0.2324 | 0.3727 | 0.0972 |
| 2008-12 | 417 | 0.5474 | 0.1930 | 0.3324 | -0.0637 |
| 2013-19 | 417 | 0.5139 | 0.2032 | 0.3216 | -0.0816 |
| 2020-24 | 417 | 0.5176 | 0.1632 | 0.3161 | -0.0602 |

Run-up turnover ratio (3019 episodes / 394 stocks; 3202 episodes index-checked, 0 mismatches): median log ratio -0.0150 [-0.03198314965052025, -0.001463636866971473] = ratio 0.985 [0.9685229018910759, 0.9985374337270837]; per unit log run-up -0.0182 (median run-up size 2.23x); CI excludes 1: **True**. GSY 2019 (read): turnover elevated in all run-ups, whether or not they crash -- a run-up feature, not a crash predictor.

v2 incumbent: rho 0.65, +0.25 |r|, +1.2 |x| (dominated: no read source), noise 0.30. Lo & Wang (read): weekly turnover AC(1) 0.91/0.87 at the market level, sanity range only.

