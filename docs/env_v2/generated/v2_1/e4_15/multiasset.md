# E4.15 - what drives multi-asset co-drawdown

`python -m tools.phase4.e4_15_multiasset`

60 seeds per arm, 3 assets, `schedule_mode` pinned to v21.

| arm | co-drawdown share | 95 % CI | all three together |
|---|---|---|---|
| crash_shared_event_v2 | 0.3998 | [0.3666, 0.4329] | 0.2313 |
| crash_per_asset_load1.0 | 0.3998 | [0.3666, 0.4329] | 0.2313 |
| crash_per_asset_load0.5 | 0.4005 | [0.3696, 0.4313] | 0.2002 |
| crash_per_asset_load0.0 | 0.4001 | [0.3724, 0.4269] | 0.1732 |
| crash_no_common_factor | 0.3829 | [0.3535, 0.4138] | 0.1976 |
| flat_no_event | 0.0531 | [0.0352, 0.0722] | 0.0000 |
| flat_no_common_factor | 0.0625 | [0.0428, 0.0836] | 0.0000 |

Panel: mean over all days **0.236**, p90 0.480, max 0.890 (417 names).

## Findings

- **v2_loading_is_not_1.0**: REFUTED
- **per_asset_events_change_it**: NO -- the mechanism is implemented and switchable but does not move the statistic, because every asset is in the SAME SCENARIO and crashes whether or not it shares the schedule
- **what_does_drive_it**: the scripted EVENT drives it: 0.400 in crash against 0.053 in flat. The common fundamental factor is not the cause -- removing it leaves 0.383.
- **population_mismatch**: P4-16 compared the generator's CRASH-conditional share with the panel's ALL-DAY mean. Those are different populations. The panel's all-day mean sits between the generator's flat and crash arms, and the panel's p90 (0.480) is ABOVE the generator's crash arm (0.400).

**Consequence.** The per-asset mechanism stays implemented and switchable, labelled NOT ADOPTED, because measurement shows it does not do what P4-16 said it would. Making the generator's cross-sectional co-movement match the panel's would require SCENARIO heterogeneity across assets -- some assets not in an event at all -- which is a design change to the multi-asset extension and belongs with the Phase-9 multi-asset sensitivities, not with Phase 4's event block.
