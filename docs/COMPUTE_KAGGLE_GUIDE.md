# Kaggle offload — connection and working guide

The proven compute offload for the v2.1 programme. **Verified live 5 September 2026**: CLI 2.2.4, account
`ayeshaiq`, `auth_method: ACCESS_TOKEN`, token at `~/.kaggle/access_token`. Bundle
`ayeshaiq/finpersona-phase3-bundle` last refreshed 2026-09-05 09:39.

What you get: **4 vCPU / 30 GB / 12 h** per CPU kernel, about **five concurrent sessions**, no weekly CPU quota
(the 30 h/week cap is GPU-only and irrelevant — this codebase is NumPy/SciPy/scikit-learn with no GPU path).
A single Kaggle vCPU is roughly one of the laptop's cores; **the win is concurrency and RAM, not per-core
speed**.

---

## 0. Check the connection

```bash
python -m kaggle --version          # -> Kaggle CLI 2.2.4
python -m kaggle config view        # -> username: ayeshaiq, auth_method: ACCESS_TOKEN
python -m kaggle datasets list --mine -s finpersona
python -m kaggle kernels list --mine
```

If auth fails: the token is a file at `~/.kaggle/access_token` (not the older `kaggle.json` API-key style).
Regenerate from kaggle.com → your avatar → Settings → API → **Create New Token**, and drop the file there.
On Windows the path is `C:\Users\<you>\.kaggle\`.

## The three rules that are not negotiable

1. **Never upload `datasets/`.** Third-party data, several sources forbid redistribution. Ship *derived*
   statistics instead — `e1_2/smm_data_moments.json` and `e2_3/data_moments.json` (moments + block-bootstrap
   draws + weight matrices) are the precedents, and they are the only reason an SMM re-run can go to a kernel
   at all.
2. **Do not offload anything whose reported number comes from a scikit-learn model fit** — leakage audits, L5,
   any surrogate R². Simulation and optimisation offload safely; model fitting does not (see the caveat at the
   bottom — this was learned the hard way).
3. **Prove the reference row on the kernel before you use a single number from it.**
   ```bash
   python -m tools.phase2.e2_3_smm --reference-row     # run this ON the kernel, diff vs the committed file
   ```
   `tests/test_v2_1_phase_2.py::test_smm_reference_row` asserts it to ten significant figures. Phase 3 did this
   first (kernel `fp-p3-refrow`) and got a worst relative difference of **6.4 × 10⁻¹⁶** across all 51 moments —
   that is the standard to meet. If a machine misses it, it runs simulation and optimisation only.

---

## 1. Refresh the bundle

The bundle is a staged copy of the repo minus the data. Stage it in the session scratchpad, never in the repo.

```bash
STAGE=/c/Users/AYESHA~1.GUL/AppData/Local/Temp/claude/<session>/scratchpad/stage
mkdir -p "$STAGE"
cp -r envs evaluation agent simulation tools tests pyproject.toml "$STAGE"/
mkdir -p "$STAGE/docs/env_v2/generated"
cp -r docs/env_v2/generated/v2_1 "$STAGE/docs/env_v2/generated/"   # only the inputs the kernel reads
```

`dataset-metadata.json` in `$STAGE`:

```json
{ "title": "finpersona-phase3-bundle",
  "id": "ayeshaiq/finpersona-phase3-bundle",
  "licenses": [{ "name": "other" }] }
```

Then, for an existing bundle:

```bash
python -m kaggle datasets version -p "$STAGE" --dir-mode zip -m "phase 4 inputs, 5 Sep"
```

or for a brand-new one: `python -m kaggle datasets create -p "$STAGE" --dir-mode zip`.

Give the version a minute or two to finish processing before a kernel that depends on it will see it.

## 2. Write the kernel

One directory per kernel: `kkernels/<name>/kernel.py` + `kernel-metadata.json`.

`kernel-metadata.json`:

```json
{ "id": "ayeshaiq/fp-p4-e48",
  "title": "fp-p4-e48",
  "code_file": "kernel.py",
  "language": "python",
  "kernel_type": "script",
  "is_private": true,
  "enable_gpu": false,
  "enable_internet": false,
  "dataset_sources": ["ayeshaiq/finpersona-phase3-bundle"],
  "competition_sources": [],
  "kernel_sources": [] }
```

`kernel.py` — the pattern that has worked for twelve kernels:

```python
import os, shutil, subprocess, sys

# Kaggle may or may not extract the zip, so FIND the repo rather than assuming a path
root = next(d for d, _, f in os.walk("/kaggle/input") if "pyproject.toml" in f)
shutil.copytree(root, "/tmp/repo", dirs_exist_ok=True)

env = {**os.environ, "PYTHONPATH": "/tmp/repo"}
subprocess.run([sys.executable, "-m", "tools.phase4.e4_8_whatever", "--seeds", "200"],
               cwd="/tmp/repo", env=env, check=True)

os.makedirs("/kaggle/working/out", exist_ok=True)
shutil.copytree("/tmp/repo/docs/env_v2/generated/v2_1/e4_8",
                "/kaggle/working/out/e4_8", dirs_exist_ok=True)
```

Anything not copied into `/kaggle/working/` is lost when the kernel ends.

## 3. Push, watch, pull

```bash
python -m kaggle kernels push   -p kkernels/fp-p4-e48
python -m kaggle kernels status ayeshaiq/fp-p4-e48        # queued / running / complete / error
python -m kaggle kernels output -p kkernels/fp-p4-e48     # downloads /kaggle/working
```

Then copy the results into `docs/env_v2/generated/v2_1/` and let the local resumable chain skip the stages
whose outputs now exist. One kernel per independent slice; merge caches locally —
`tools/phase1/merge_recovery_caches.py` shows the pattern.

## 4. What to send, and what not to

| send | keep local |
|---|---|
| generator simulation at scale (mechanism arms, 200-seed comparisons) | the full-panel leakage audit |
| SMM fits and re-fits | L5 policy tables |
| episode / block bootstraps | any surrogate R² |
| recovery grids, parameter sweeps | anything reported from a `sklearn` fit |

**Precedents.** Phase 1 ran ten kernels (`fp-p1-rec-*`, `fp-p1-l5-after`, `fp-p1-audit-after-*`). Phase 3 ran
`fp-p3-refrow` (the reference-row proof) then `fp-p3-e34` (the three mechanism arms). Phase 4 has `fp-p4-e46`
as of 5 Sep 2026.

## Rough timings

Laptop (4 physical / 8 logical cores, ~5 GB free) vs a 4-vCPU kernel:

| workload | laptop | Kaggle |
|---|---|---|
| full-panel leakage audit | ≈ 2 h | ≈ 1.5 h *(don't offload — see rule 2)* |
| L5 policy table, 40/50 seeds | ≈ 1 h | ≈ 15 min *(don't offload)* |
| one SMM cell | 1.5–3 h | comparable per core |
| 300 SMM fits | — | ≈ 7.7 h |
| 40-point sweep | ≈ 30 min | ≈ 20 min |
| 200-seed checklist | ≈ 12 min | — |

Two heavy local jobs at once hung the laptop twice during Phase 1 — check free RAM before launching a second.

---

## The reproducibility caveat (30 August 2026, learned the hard way)

A surrogate-based number produced on Kaggle **did not reproduce locally**: E1.3 calm R² was **0.41 on Kaggle vs
0.15 locally**, same code, same seeds, same panel. The SEP leakage audit on the same machines *did* reproduce
(0.385 vs 0.383). Thread count and `HistGradientBoosting`'s `early_stopping='auto'` were both tested and ruled
out. **The cause is still unknown.**

Two of the ten Phase-1 kernels — `fp-p1-audit-after-lf` and `fp-p1-l5-after` — are the runs that failed to
reproduce, which is what turned this into rule 2. Note especially that *one reproducing row did not predict the
other*: the audit reproduced and the surrogate did not, on the same machine. So the reference-row check must be
run on **the same kind of panel** as the result it is vouching for.

## Auto-mode permissions

Already allowed in `.claude/settings.local.json`: `python -m kaggle *`, `cp *`, `mkdir *`, and running scripts
by path out of the scratchpad. Shell loops and heredocs are still classified — **put logic in a scratchpad
script and run it by path** rather than inlining it.
