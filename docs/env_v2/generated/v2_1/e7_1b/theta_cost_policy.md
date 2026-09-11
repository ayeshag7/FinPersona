# E7.1b part 2 — theta_cost tested as a policy rule

The mandate-conditional oracle **acting** at each candidate theta, on 100 seeds x 4 scenarios x 3 personas, at 5.0 bp per trade and again at 0 bp. The oracle knows x exactly, so this is the most favourable case for a low threshold — which is the case theta_cost's derivation assumes. Cluster-bootstrap 95 % intervals over seeds.

| acting theta | label | net return % | gross return % (0 bp) | cost drag pp | trades per run | turnover | MCR at its own theta |
|---|---|---|---|---|---|---|---|
| 0.002 | theta_cost | **14.075** [11.745, 16.801] | 14.229 | 0.154 | 30.0 | 2.84 | 0.0028 |
| 0.03 | grid | **13.960** [11.445, 16.401] | 14.020 | 0.061 | 22.2 | 1.11 | 0.0029 |
| 0.032791 | theta_cost_one_day | **14.019** [11.584, 16.775] | 14.077 | 0.058 | 21.8 | 1.07 | 0.0028 |
| 0.046321 | theta_var | **14.029** [11.479, 16.596] | 14.075 | 0.045 | 19.7 | 0.85 | 0.0028 |
| 0.05 | grid|theta_info_all | **13.968** [11.651, 16.698] | 14.011 | 0.043 | 19.1 | 0.81 | 0.0028 |
| 0.065609 | theta_var_stationary | **13.870** [10.973, 16.474] | 13.904 | 0.034 | 16.5 | 0.64 | 0.0026 |
| 0.08 | grid | **13.734** [11.113, 16.347] | 13.761 | 0.027 | 14.4 | 0.52 | 0.0026 |
| 0.12 | grid | **13.378** [10.648, 15.911] | 13.396 | 0.019 | 10.3 | 0.34 | 0.0023 |
| 0.2 | grid|theta_info_calm | **13.002** [10.717, 15.789] | 13.012 | 0.010 | 6.0 | 0.19 | 0.0024 |

**Derived theta_cost = 0.0020. Best acting theta by net return = 0.002** (by gross return 0.002). Acting at theta_cost costs 30 trades a run against 30 at the best, a cost drag of 0.154 pp, and gives up 0.000 pp of net return against the best acting threshold.

