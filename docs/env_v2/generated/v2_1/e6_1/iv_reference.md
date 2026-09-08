# E6.1 (IV block) — the item-13 reference from real implied-volatility histories

200-day windows; `item13_iv`'s constructions (rv20 = next-20-day realised sd, annualised %, corr over defined days). Generated 2026-09-08T16:22:18Z. **Survivorship / representativeness:** the five single-stock IV indices are five surviving mega-caps chosen by the CBOE (2011-2026), a small and selected sample; the FRED index pair is exact but ten years; the set-A proxy is equal-weighted and survivor-biased, so its realised vol is not the S&P 500's -- the three are reported side by side with their n

| pair | n windows | IV mean P10/P50/P90 | RV20 mean P50 | realised σ (ann. %) P50 | corr(IV, next-20d RV) P10/P50/P90 | IV−RV20 P10/P50/P90 | IV ACF(1) P50 | max |Δlog IV| P50 |
|---|---|---|---|---|---|---|---|---|
| index:VIX vs FF value-weighted US market (1990-) | 33 | 13.07 / 18.63 / 25.43 | 14.12 | 15.34 | 0.11 / 0.44 / 0.70 | +1.36 / +3.13 / +6.57 | 0.919 | 0.283 |
| index:VIX vs S&P 500 (FRED, 2016-) | 12 | 12.91 / 17.50 / 25.26 | 13.07 | 14.32 | 0.13 / 0.41 / 0.61 | +1.50 / +3.53 / +6.31 | 0.904 | 0.386 |
| index:VIX vs set-A equal-weight proxy (2000-2024) | 31 | 13.04 / 18.63 / 25.45 | 14.62 | 15.77 | -0.03 / 0.47 / 0.69 | -0.55 / +3.17 / +6.50 | 0.920 | 0.283 |
| single:VXAPL vs AAPL | 18 | 23.97 / 29.27 / 37.01 | 24.65 | 26.97 | 0.25 / 0.50 / 0.69 | +1.17 / +4.50 / +7.73 | 0.922 | 0.333 |
| single:VXAZN vs AMZN | 18 | 28.48 / 32.99 / 39.95 | 30.00 | 32.46 | 0.52 / 0.68 / 0.77 | +1.10 / +4.92 / +7.52 | 0.945 | 0.378 |
| single:VXGOG vs GOOG | 18 | 22.37 / 26.77 / 33.53 | 24.84 | 27.18 | 0.28 / 0.59 / 0.68 | -0.58 / +3.19 / +5.59 | 0.923 | 0.386 |
| single:VXGS vs GS | 18 | 23.70 / 27.92 / 38.30 | 23.55 | 24.89 | 0.07 / 0.33 / 0.58 | -0.40 / +4.95 / +8.39 | 0.930 | 0.216 |
| single:VXIBM vs IBM | 18 | 19.72 / 23.27 / 28.81 | 19.74 | 21.43 | 0.37 / 0.54 / 0.73 | +1.83 / +3.51 / +6.40 | 0.927 | 0.397 |
| single:pooled | 90 | 21.61 / 28.36 / 37.56 | 24.40 | 26.77 | 0.27 / 0.55 / 0.75 | +0.33 / +4.14 / +7.37 | 0.925 | 0.357 |

## By the window's realised-volatility tercile (low ≈ the real analogue of calm, high ≈ panic; a DESIGN mapping)

| pair | tercile | n | IV mean P10/P50/P90 | IV−RV20 P50 | corr P50 |
|---|---|---|---|---|---|
| index:VIX vs FF value-weighted US market (1990-) | low | 11 | 12.6 / 14.4 / 16.1 | +3.1 | 0.25 |
| index:VIX vs FF value-weighted US market (1990-) | mid | 11 | 16.3 / 18.6 / 22.1 | +4.3 | 0.60 |
| index:VIX vs FF value-weighted US market (1990-) | high | 11 | 22.5 / 24.9 / 31.2 | +1.6 | 0.52 |
| index:VIX vs S&P 500 (FRED, 2016-) | low | 4 | 12.7 / 13.6 / 16.6 | +4.2 | 0.25 |
| index:VIX vs S&P 500 (FRED, 2016-) | mid | 4 | 16.1 / 19.0 / 22.5 | +5.2 | 0.52 |
| index:VIX vs S&P 500 (FRED, 2016-) | high | 4 | 17.5 / 22.5 / 26.9 | +1.6 | 0.43 |
| index:VIX vs set-A equal-weight proxy (2000-2024) | low | 11 | 12.6 / 14.4 / 15.3 | +2.5 | 0.15 |
| index:VIX vs set-A equal-weight proxy (2000-2024) | mid | 10 | 16.5 / 18.8 / 22.6 | +4.1 | 0.64 |
| index:VIX vs set-A equal-weight proxy (2000-2024) | high | 10 | 22.8 / 25.1 / 32.5 | +4.0 | 0.56 |
| single:VXAPL vs AAPL | low | 6 | 22.4 / 24.4 / 29.0 | +5.6 | 0.47 |
| single:VXAPL vs AAPL | mid | 6 | 27.0 / 29.4 / 31.9 | +4.8 | 0.47 |
| single:VXAPL vs AAPL | high | 6 | 29.3 / 34.9 / 39.7 | +1.5 | 0.54 |
| single:VXAZN vs AMZN | low | 6 | 24.5 / 30.3 / 32.6 | +6.3 | 0.68 |
| single:VXAZN vs AMZN | mid | 6 | 31.4 / 34.0 / 39.3 | +3.7 | 0.76 |
| single:VXAZN vs AMZN | high | 6 | 33.5 / 38.0 / 43.3 | +1.7 | 0.57 |
| single:VXGOG vs GOOG | low | 6 | 19.8 / 23.6 / 25.4 | +4.4 | 0.60 |
| single:VXGOG vs GOOG | mid | 6 | 25.4 / 28.1 / 31.1 | +3.7 | 0.58 |
| single:VXGOG vs GOOG | high | 6 | 28.0 / 32.1 / 36.3 | +0.8 | 0.47 |
| single:VXGS vs GS | low | 6 | 22.3 / 23.8 / 24.8 | +4.3 | 0.26 |
| single:VXGS vs GS | mid | 6 | 26.1 / 27.9 / 33.3 | +5.0 | 0.30 |
| single:VXGS vs GS | high | 6 | 29.5 / 36.4 / 40.7 | +3.2 | 0.51 |
| single:VXIBM vs IBM | low | 6 | 19.0 / 20.1 / 22.1 | +4.7 | 0.57 |
| single:VXIBM vs IBM | mid | 6 | 20.9 / 23.9 / 25.6 | +3.5 | 0.46 |
| single:VXIBM vs IBM | high | 6 | 23.5 / 28.4 / 31.3 | +2.2 | 0.54 |

The v2 item-13 bands (calm IV 25–35 %, panic 60–100 %, corr 0.4–0.8, IV−RV +3..+8 calm / +10..+25 panic) are to be read against these rows; the generator's single stock is compared with the single-stock pairs, its index-like properties with the VIX pairs, and the criterion in force is the pre-registration's.
