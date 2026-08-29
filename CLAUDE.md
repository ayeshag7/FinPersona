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
- `docs/` is intentionally git-ignored and untracked. Files live on disk only —
  do not re-add them, and do not treat their absence from `git status` as a problem.
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
