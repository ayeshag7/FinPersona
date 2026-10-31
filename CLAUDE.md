# FinPersona — working agreements

## Git commit messages

**One line. No body. No trailers.**

- A single descriptive subject line — long is fine, but it stays on one line.
- **Never** append `Co-Authored-By:` or any other trailer.
- No bullet lists, no "Adds…/Changes…" paragraphs, no explanatory body.

```
Ignore datasets/ (E1.0 panel: third-party data, re-downloadable via tools/e1_0_data/)
```

Match the existing history — `git log --oneline -10` shows the house style.

## Git behaviour

- Work stays on `main`. **Do not create branches.**
- Commit only when asked, in that message. Never push unless asked.
- `docs/` **is tracked** — 1,571 files, and documents there belong in commits.
  Three narrower rules apply, and the middle one bites silently:
  - `docs/env_v2/generated/v2_1` is matched by `.gitignore:69`, but **1,326 files
    under it are tracked anyway**, force-added. A *new* file there — a manifest, a
    ledger, a stats directory — is dropped from `git add` without a word and the
    commit looks complete. Add it with `git add -f`, then check `git show --stat`.
    This has already cost one commit (`bc46d12` exists only to repair `340c4e2`).
  - The compute guides and the model-cost files are genuinely never committed:
    this repo is public and they carry cluster and account detail. `tools/cluster/`
    and `compute and storage guides/` are the same, and `tools/hf_backup.py`
    refuses to upload them too.
  - `.gitattributes` pins generated JSON, JSONL and CSV to LF, so a sha256
    recorded in a pre-registration survives a Windows checkout.
- `datasets/` is git-ignored: third-party data, several sources forbid
  redistribution. Re-downloadable via `tools/e1_0_data/`.

## Environment v2.1 programme

The synthetic market environment is being rebuilt under
`docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.md`. Its governing rule: every generator
parameter is **fitted or tested on data**, never stipulated. Phase reports carry
a citation table; a statistic marked "(to verify)" may not appear in a parameter
file, test tolerance or slide.

Do not edit the plan, `V2_1_ALTERNATIVES_REGISTER.md`, or anything under
`docs/env_v2/v2_1/archive/` without being asked.

Do not modify `envs/`, `evaluation/`, `agent/` or `simulation/` unless the task
is explicitly about them.

## Reporting

Report failures as failures, with evidence. Never substitute a dataset, a source
or a result silently. Numbers carry their `n`.
