# E1.3 grid rows reproduced locally (ADDENDUM section 6.2)

Local environment: {'python': '3.13.13', 'numpy': '2.4.6', 'pandas': '3.0.3', 'sklearn': '1.9.0', 'scipy': '1.18.0'}. Same seeds, same run_point, 200 seeds x 4 scenarios.

| point | calm R2 local [CI] | calm R2 Kaggle [CI] | all R2 local / Kaggle | cov flat 0.05 local / Kaggle | item 9 hl local / Kaggle | sd_x5000 local / Kaggle |
|---|---|---|---|---|---|---|
| sV 0.006 t5 sx 0.165 | 0.153 [0.092, 0.173] | 0.407 [0.146, 0.533] | 0.398 / 0.592 | 0.76 / 0.76 | 68 / 68 | 0.163 / 0.163 |
| sV 0.02 t5 sx 0.165 | 0.066 [-0.136, 0.149] | 0.305 [-0.066, 0.473] | 0.297 / 0.494 | 0.75 / 0.75 | 67 / 67 | 0.162 / 0.162 |
| sV 0.006 gaussian sx 0.1 | 0.152 [0.045, 0.196] | 0.376 [0.092, 0.522] | 0.603 / 0.705 | 0.62 / 0.62 | 71 / 71 | 0.101 / 0.101 |
