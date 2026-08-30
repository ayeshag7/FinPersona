# E1.3 surrogate determinism check (ADDENDUM section 6.2)

One panel (40 seeds x 4 scenarios at the in-force grid point), identical seeds and features; only the thread count and the early-stopping flag differ. Environment: {'python': '3.13.13', 'sklearn': '1.9.0', 'numpy': '2.4.6'}.

| estimator setting | OMP threads | calm R2(x) | all R2 |
|---|---|---|---|
| early_stopping='auto' (as _models() builds it) | 1 | 0.1214 | 0.5960 |
| early_stopping='auto' (as _models() builds it) | 4 | 0.1214 | 0.5960 |
| early_stopping=False | 1 | 0.1300 | 0.6001 |
| early_stopping=False | 4 | 0.1300 | 0.6001 |

Spread across thread counts: early_stopping='auto' 0.0000; early_stopping=False 0.0000.

A non-zero spread with 'auto' and a zero spread with False identifies the defect: early stopping picks its iteration count from a validation score computed over OpenMP-parallel histogram sums, so the fitted model -- and every R2 derived from it -- depends on the thread count and the library build. The fix for any gate is to construct the estimator with early_stopping=False (or a fixed n_iter) and to pin the library versions.
