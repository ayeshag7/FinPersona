# E4.0c - the level decided conditional on phase

`python -m tools.phase4.e4_0c_phase_levels` - PREREG_PHASE_4_ADDENDUM.md section 2.3.

Generator: 500 seeds x 4 scenarios, seeds 216000+. Panel: analysis set A.
One estimator on both sides; generator CIs cluster by seed, panel CIs by stock.

## Calm level

| side | pooled calm sd | 95 % CI | n |
|---|---|---|---|
| generator | 0.022054 | [0.021652, 0.022482] | 177,964 days |
| panel (drawdown episodes) | 0.021672 | [0.020860, 0.022439] | 1592 episodes / 412 stocks |

Ratio 1.0176; generator inside the panel CI: **True**. The panel's full-sample s_A is 0.021793.

## Crash-side phases, ratio to own calm (tested)

| phase | generator | 95 % CI | panel | 95 % CI | verdict |
|---|---|---|---|---|---|
| deterioration | 2.632 | [2.382, 2.938] | 1.618 | [1.506, 1.746] | **OUTSIDE** |
| panic | 8.564 | [7.505, 9.732] | 7.642 | [6.968, 8.428] | **OUTSIDE** |
| stabilisation | 3.432 | [3.143, 3.741] | 3.109 | [2.851, 3.409] | **OUTSIDE** |

## Bubble-side phases (reported, not tested)

The panel's run-up calm reference has sd 0.041267 against the drawdown family's 0.021672 - it sits at a post-crash trough, which is the contamination PREREG_PHASE_3_ADDENDUM section 1 identified. E4.1 derives a clean reference.

| phase | generator ratio | panel ratio (contaminated ref) |
|---|---|---|
| mania | 1.135 | 0.650 |
| blow-off | 1.176 | 0.839 |
| post-top | 0.817 | 0.405 |

## Verdict

- calm level accepted: **True**
- crash phases outside the panel CI: **['deterioration', 'panic', 'stabilisation']**
- Phase 3's level double-count: **PARTIAL - calm level accepted; 3 crash phase(s) outside the panel CI, handed to the experiment that owns the shape (E4.2/E4.6), not to the level**
- anchor: **KEPT**
