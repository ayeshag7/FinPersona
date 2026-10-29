# docs/

Everything in here is tracked and pushed. The `.gitignore` entries that name paths under `docs/` stop *new* files
appearing — under `env_v2/generated/v2_1/`, and the compute and model-cost guides that stay local — but the files
already tracked stay tracked.

| Folder | Contents |
|---|---|
| `env_v2/` | **The synthetic environment, and the largest thing in here.** `spec/` (the generator as built, with each phase's rewrite inline), `preregistration/`, `decisions/` (the running decision log, P0-1 … P9-19), `v1_baseline/`, `status/` (23 Aug 2026 snapshots, kept as history), `generated/` (machine-written results, including 1,295 files of v2.1 phase outputs), `reviews/` (the three v2 reviews and the 74-item weakness list), `v2_1/` (the improvement plan, the alternatives register, and the pre-registration, report and changed-files list of each of the ten phases), `history/` (the whole story in one 63-page document), `slides/` (the v2 deck and speaker script, both predating v2.1). Index, reading order and current status in `env_v2/README.md` |
| `paper/` | Current COLM paper (PDF), post-rebuttal PDF, extracted text, May rebuttal |
| `reviews/cycle1/` | First review cycle: consolidated report, synthetic-market audit |
| `reviews/cycle2/` | Second review cycle: verification and red-team report, reviewer A/B/C notes, literature review parts 1–3, novelty positioning, position and revision-plan update, related-work update. The area-chair report's GO conditions still govern what the paper may claim |
| `planning/` | Revision plan, environment v2 plan (+ `env_v2_research/` notes and fact-checks), experiment execution order, experiment tracker (xlsx) |
| `mech_interp/` | Mechanistic-interpretability report and the results-and-design-changes document. The working constraints for the M-series are `MECH_INTERP_BRIEF.md` at the repo root |

At this level: `REPO_GUIDE.md` is the map of the codebase, and `KAGGLE_DATASETS.md` and `COMPUTE_KAGGLE_GUIDE.md`
cover the private Kaggle datasets that back up what GitHub does not hold and the compute that produced them.
