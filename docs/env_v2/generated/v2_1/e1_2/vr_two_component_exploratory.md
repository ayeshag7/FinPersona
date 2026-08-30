# E1.2 exploratory two-component fit on the pooled VR curve (NOT pre-registered; no intervals)

log P = log V + x1 + x2; V random walk; x_i AR(1) with sd s_i, half-life h_i. Set A, full sample, 8 moments, stock-bootstrap weights.

| fit | sigma_V/day | s_1 | h_1 (d) | s_2 | h_2 (d) | s_x total | J |
|---|---|---|---|---|---|---|---|
| one component (estimator A) | 0.02047 | 0.024 | 4.9 | - | - | 0.024 | 84.41 |
| two components, free | 0.01933 | 0.010 | 1.4 | 0.060 | 42 | 0.061 | 8.62 |
| h_2 = 256 d (estimator B) | 0.01621 | 0.014 | 2.4 | 0.194 | 256 | 0.194 | 18.61 |
| h_2 = 150 d (engine) | 0.01774 | 0.013 | 2.2 | 0.130 | 150 | 0.131 | 15.45 |

Reading: the VR curve alone prefers a second component of about two months (free fit) and fits worse the longer h_2 is forced (J rises from 8.6 to 15.5 at 150 d and 18.6 at 256 d, against 84.4 for one component); over the 500-day horizon of the curve a component with a one-year half-life is close to a random walk, so sigma_V and s_2 trade off and the curve cannot settle them. This is why the pre-registered decomposition needs estimator B (a level anchor) or C (persistence-carrying moments), and why the recovery study decides which is usable. sigma_V under every two-component fit (0.016-0.019) is 2.7-3.2 x v2's stipulated 0.006.
