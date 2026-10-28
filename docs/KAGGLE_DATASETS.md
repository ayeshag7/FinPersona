# FinPersona on Kaggle

These are all the Kaggle datasets made for FinPersona. They live on the account `ayeshaiq`, and all are private. The
list was checked against Kaggle on 28 Oct 2026.

## Datasets

| Dataset | Last updated | Purpose | Contents |
|---|---|---|---|
| [`finpersona-phase1-bundle`](https://www.kaggle.com/datasets/ayeshaiq/finpersona-phase1-bundle) | 30 Aug 2026 (version 5) | The code bundle the Phase 1 compute kernels read | A copy of the repo's code (`agent/`, `envs/`, `evaluation/`, `simulation/`, `tools/`, `tests/`, `legacy_market_data/`, `pyproject.toml`), plus the generated inputs the kernels read, under `docs/`. 202 files, 78 MB. No third-party `datasets/`. |
| [`finpersona-phase3-bundle`](https://www.kaggle.com/datasets/ayeshaiq/finpersona-phase3-bundle) | 5 Sep 2026 (version 5) | The code bundle the Phase 3 and Phase 4 compute kernels read | The same kind of copy (`agent/`, `envs/`, `evaluation/`, `simulation/`, `tools/`, `tests/`, `experiments/`), with the kernels' inputs under `gen/`. 244 files, 7.8 MB. No third-party `datasets/`. |
| [`finpersona-vllm-pilots`](https://www.kaggle.com/datasets/ayeshaiq/finpersona-vllm-pilots) | 19 Sep 2026 (version 5) | Backup of the September variance pilots (E9.2) | 96 runs each of five models. Four ran on vLLM: Gemma 4 31B, Gemma 4 E4B, Gemma 4 12B and gpt-oss-20b. DeepSeek V4.1 Flash ran through OpenRouter. It holds their per-run files, ledgers and manifests, a README and a provenance file. 1,452 files, 129 MB. |
| [`finpersona-open-headline-stage1`](https://www.kaggle.com/datasets/ayeshaiq/finpersona-open-headline-stage1) | 28 Oct 2026 (version 1) | Backup of the open-weight headline, stage 1 (E9.4) | All nine models' 2,928 runs each (per-run CSV, meta and usage files, plus checkpoints). Their ledgers, manifests, verification and validation reports, cluster job and vLLM logs, and job scripts. The seven B200 pilots (96 runs each). The two pre-registrations, the decision log and the model roster. 81,194 files, 7.6 GB, each at its repo path. On 28 Oct every file was confirmed present at its size. |

Notes on the headline backup:
- **Restoring on Windows:** unzip it into a short folder such as `C:\r` first, then copy it into the repo. Its deepest
  paths are too long to unzip under most other folders.
- **Logs:** Kaggle stores the nine vLLM server logs unzipped, as `.log` rather than `.log.gz`.
- **Download errors:** if downloading the whole dataset gives a 404, Kaggle is still building its archive. Single
  files download fine meanwhile.

## Kaggle kernels

These are compute jobs, not datasets, but their outputs also stay on Kaggle.

- **Phase 1, 29–30 Aug 2026**, reading `finpersona-phase1-bundle`:
  - `fp-p1-audit-before-lf`, `fp-p1-audit-before-level`, `fp-p1-audit-after-lf`, `fp-p1-audit-after-level`;
  - `fp-p1-l5-before`, `fp-p1-l5-after`;
  - `fp-p1-e1-3-sweep`;
  - seven `fp-p1-rec-*` kernels: `h5-10`, `h30-60`, `h120-150`, `h250`, `h500`, `h30-150-250` and `smm`.
- **Phase 3, 2 Sep 2026:** `fp-p3-refrow` (the reference-row check) and `fp-p3-e34`.
- **Phase 4, 5 Sep 2026:** `fp-p4-e46`.

The Phase 3 and Phase 4 kernels read `finpersona-phase3-bundle`.

## Not FinPersona

The account's other 46 datasets belong to other projects:
- **Engineering-reasoning benchmark:** `testset`, the per-model `inference-results*`, `evaluation*`, `gemini-*`,
  `claude-opus-4-7`, `deepseek-v4-pro` and `engtrace-*`.
- **FinMoE:** `finmoe-hf-credentials`.
- **Invoice and cheque images:** `pkg-*`.
- **Two small test-image sets:** `test-images*`.
- **Work from 2024–25:** Urdu OCR, including `train-data`, `validation-data` and `test-data`; CLINC150 embeddings;
  deraining and low-light image sets; carbon-pricing data; ChineseHerbs; CropGrids.
