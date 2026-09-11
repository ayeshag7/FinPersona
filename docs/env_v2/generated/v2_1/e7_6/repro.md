# E7.6 — do the pilot's paths regenerate under the v2.1 switches?

52 pilot runs (`C:\Users\ayesha.gull01\FinPersona\results_v2_pilot`), every one recorded with `env_version = ['v2']` and `engine = ['fw_single']`. Each environment is rebuilt from its own `meta.json` and the regenerated path compared with the columns the run logged, at a tolerance of 1e-09.

- **paths that reproduce under the recorded engine: 0 of 52**
- environments that could be CONSTRUCTED at all under the recorded engine: 0 of 52
- under the documented CAL fallback engine: constructed 52 of 52, reproducing 0 of 52
- `Gen_Config_Hash` recomputed from the stored metadata matches the stored value in 52 of 52

The generator's own refusal, verbatim:

```
FileNotFoundError: engine 'fw_single' needs an accepted SMM estimate at <repo>\envs\v2\params\fw_single_stock.json; none exists (the attempt was rejected: fw_single_stock.REJECTED.json). Use engine 'ar1_fit' (the documented CAL fallback) explicitly.
```

Under the fallback engine the path is constructible but distant: the worst absolute difference against the run's logged price / V / x has median **37.5** and minimum **37.5** over 52 runs, and the regenerated day-1 price takes the values [100.0] against the pilot's 100.0. So the non-reproduction is a measured distance, not only a missing file.

| scenario | seed | n runs | worst abs diff, fallback engine (price / V / x) |
|---|---|---|---|
| bull_trap | 42 | 15 | 81.68 |
| crash | 42 | 15 | 37.5 |
| flat | 42 | 22 | 38.18 |

The 27 keys the pilot's `gen_config` carries are restored exactly; the 23 `GenConfig` fields v2.1 added after the pilot are not in the record and take today's defaults. That is what the test measures. Guessing values the record does not hold would be a different experiment.

