# E7.6 — baselines rebuilt from `meta.json` against the seven-column path

0 of 52 cells reproduce their path; the comparison is reported for every cell, with the reproducing flag beside, so a difference is never read as an improvement on a path the agent never saw.

**`cell_baselines(from_meta=True)` could not be built for 52 of 52 cells**, and the reason is E7.6's own finding rather than a defect in the rebuild: the environment the metadata names cannot be constructed. The distinct failures, verbatim:

```
FileNotFoundError: engine 'fw_single' needs an accepted SMM estimate at <repo>\envs\v2\params\fw_single_stock.json; none exists (the attempt was rejected: fw_single_stock.REJECTED.json). Use engine 'ar1_fit' (the documented CAL fallback) explicitly.
```

So the switch is correct and untestable on this pilot: it is tested instead on a freshly generated cell whose configuration the seven run-CSV columns cannot express (`tests/test_v2_1_phase_7.py::test_baselines_same_path_hash`).

