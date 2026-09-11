# E7.8(a) — construct monotonicity of the scripted sweeps (theta = 0.05, half-width 0.1)

A sweep is **monotone** when the sequence of cell means moves in the registered direction with no reversal outside its bootstrap interval; a reversal inside the interval is reported and does not by itself fail the sweep (PREREG 4.1).

## Scoring A_decomposition

| family | swept parameter | target metric | registered direction | means | reversals | outside interval | monotone |
|---|---|---|---|---|---|---|---|
| align | [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0] | `mcr_D` | decreasing | [0.1988, 0.1596, 0.12, 0.1005, 0.0809, 0.0416, 0.0017] | 0 | 0 | **yes** |
| drift | [0.0, 0.002, 0.005, 0.01, 0.02, 0.04] | `band_mas` | increasing | [0.0, 0.0836, 0.2343, 0.316, 0.357, 0.3771] | 0 | 0 | **yes** |
| panic | [0.0, 0.25, 0.5, 0.75, 1.0] | `mdd_pct` | monotone | [-16.1985, -14.8441, -13.2751, -11.4369, -8.8913] | 0 | 0 | **yes** |

## Scoring B_per_window

| family | swept parameter | target metric | registered direction | means | reversals | outside interval | monotone |
|---|---|---|---|---|---|---|---|
| align | [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0] | `mcr_window_D` | decreasing | [0.1937, 0.1566, 0.1187, 0.1004, 0.0819, 0.0444, 0.0069] | 0 | 0 | **yes** |
| drift | [0.0, 0.002, 0.005, 0.01, 0.02, 0.04] | `band_mas` | increasing | [0.0, 0.0836, 0.2343, 0.316, 0.357, 0.3771] | 0 | 0 | **yes** |
| panic | [0.0, 0.25, 0.5, 0.75, 1.0] | `mdd_pct` | monotone | [-16.1985, -14.8441, -13.2751, -11.4369, -8.8913] | 0 | 0 | **yes** |

