# E5.7(b) L1 extended candidate set -- epsdiv_v21_hidden

Panel `docs\env_v2\generated\v2_1\_panels\sep_phase5_epsdiv_v21_hidden.pkl`, 1600 paths / 320000 rows; in-sample; k log-median-optimal; 500-resample path bootstrap on the within-5 % share.

| candidate | median APE | within 1 % | within 2 % | within 5 % [CI] | above floor |
|---|---|---|---|---|---|
| k*price | 0.0644 | 0.0925 | 0.1844 | 0.4163 [0.4057, 0.4263] | 0.9074 |
| lsq(price+F) | 0.0663 | 0.0871 | 0.1718 | 0.4006 [0.3895, 0.4114] | 0.9130 |
| lsq(price+P/PE+F) | 0.0664 | 0.0818 | 0.1597 | 0.3737 [0.3871, 0.4100] | 0.8563 |
| lsq(price+P/PE) | 0.0667 | 0.0814 | 0.1611 | 0.3704 [0.3837, 0.4057] | 0.8566 |
| lsq(price) | 0.0668 | 0.0865 | 0.1704 | 0.3947 [0.3842, 0.4056] | 0.9135 |
| k*sqrt(price*P/PE) | 0.1171 | 0.0449 | 0.0895 | 0.2171 [0.2204, 0.2417] | 0.8932 |
| lsq(F) | 0.1279 | 0.0421 | 0.0839 | 0.2082 [0.1982, 0.2175] | 0.9579 |
| lsq(P/PE+F) | 0.1287 | 0.0387 | 0.0771 | 0.1901 [0.1937, 0.2121] | 0.8993 |
| lsq(P/PE) | 0.1311 | 0.0417 | 0.0829 | 0.2029 [0.2073, 0.2257] | 0.8964 |
| k*P/PE | 0.2188 | 0.0216 | 0.0440 | 0.1142 [0.1148, 0.1296] | 0.9165 |
| k*sqrt(price*F) | 0.3922 | 0.0109 | 0.0217 | 0.0551 [0.0476, 0.0621] | 0.9891 |
| median(valuation candidates) | 0.4239 | 0.0104 | 0.0208 | 0.0524 [0.0467, 0.0588] | 0.9896 |
| k*F | 0.6786 | 0.0055 | 0.0124 | 0.0299 [0.0252, 0.0345] | 0.9945 |

Best candidate: **k*price** (median APE 0.0644; inversion share = within-5 % 0.4163); price itself: median APE 0.0644, within-5 % 0.4163.

