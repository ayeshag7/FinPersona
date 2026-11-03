# Stage 2 — operational state

**Written 31 October 2026; last updated 2 November 2026.** A running record of what is on the cluster, what runs next and what has
already been decided, so that none of it lives only in a chat session. Scientific results belong in
`E2_RESULTS.md` and `DECISION_LOG.md`; this file is the operations log beside them.

Cluster paths, the account and the host are deliberately **not** in this file — the repository is public, and
they live in `tools/cluster/` and `compute and storage guides/`, both git-ignored. Job IDs are meaningless
outside the scheduler and are kept.

---

## 1. The allocation

Four B200s for the week from **29 Oct 2026**, approved by Lingfei Qian, about **300 GPU-hours**. The allocation
runs to **5 Nov**.

**The four-GPU limit is an agreement, not a scheduler limit.** The QOS carries `GrpTRES=gres/gpu=16`, and on
31 Oct another group member held 8 B200s on job 48337514. Nothing in SLURM stops us running more than four. What
keeps us at four is the `%4` in our own array submissions. **Never submit a stage without either a dependency on
the running array or a matching `%4`** — SLURM will start it, and we will be using GPUs we were not given.

## 2. What is on the cluster

| job | what | state at 09:00 UTC 2 Nov |
|---|---|---|
| 48276232 | **E2 causal**, 7 tasks | done 30 Oct, five models read, Llama 3.1 8B deferred |
| 48312120 | **E5 sensitivity**, 12 tasks `0-11%4` | **all twelve `COMPLETED 0:0`**, last ended 1 Nov 07:13 UTC |
| 48377825 | **Llama 3.1 8B re-run** for E2, array task 5 only | **`COMPLETED 0:0`** 1 Nov 09:08 UTC, 1,080/1,080 ok |
| 48378572 | **pack E5**, CPU-only | **`COMPLETED 0:0`** 1 Nov 09:27 UTC, six archives, 4.4 G |
| 48758054 | **E3 slice**, 12 tasks `0-11%4` | **all twelve `COMPLETED 0:0`**, last ended 1 Nov 23:03 UTC |
| 48943106 | **E5 repair**, sens array task 6 alone | **`COMPLETED 0:0`** 2 Nov 08:38 UTC — see below |
| 48943107 | **E4 track_a**, 10 tasks `0-9%4` | **running** from 2 Nov 08:40 UTC |
| 48943713 | **verify + score** all four stage-2 manifests, CPU | queued on `afterany:48943107` |
| 48944660 | **push run archives to Hugging Face**, CPU | queued on `afterany:48943713` |

**The GPUs idled 9.4 h on the night of 1–2 Nov.** E3 ended 23:03 UTC with nothing queued behind it, because the
repair and E4 had not been submitted when the session's tunnel expired. `ControlPersist 8h` means the master exits
8 h after its last use and removes its socket, and it cannot be re-established without the account holder's Duo.
**Submit the whole chain in one go, with dependencies, rather than leaving a stage to be queued by hand later.**

**`sacct` prints local time, the logs print UTC**, and 1 Nov 2026 is the day US Eastern leaves daylight saving,
so the offset became −5 h that morning. Every pair above was checked to agree: task 11 `End=02:13:54` against
the log's `07:13:52Z`, the pack job `04:27:14` against `09:27:13Z`. Times in this file are UTC.

The projection was 1 Nov ~08:00 UTC and the array ended 07:13; the chain behind it fired unattended.

### One run of 103,680 went missing; it was re-run and E5 is now complete

E5 first finished **103,679 of 103,680**. Eleven tasks ended `non-ok so far 0`; task 6 ended `non-ok so far 1`. The
run is

```
sens_jump_rate__high|vllm_meta-llama_llama-3.1-8b-instruct__ISFJ__static__crash_d0.7__seed10052__rep0
            -> failed (449s, fallbacks 0, errors 0)      31 Oct 14:19 UTC
```

Three independent counts agree on *exactly one*, which is worth more than any single one of them:

* the six checkpoints hold 17,280 lines each **except** llama 3.1 8B at **17,279**, and seed 10052 is the one
  gap in an otherwise complete `ISFJ__static__crash` run of seeds at that level;
* the packaging job archived **54,782** entries for every model and **54,780** for llama — short by exactly the
  two entries, `.csv` and `.meta.json`, that one absent run would contribute, its directory and its quarantined
  usage file still being present;
* the run directory holds 5 of its 6 runs, the sixth being the quarantined
  `..._rep0.failed.20261031T141927.usage.json` — renamed rather than left to pass as a good run, and usage-only,
  so it died before producing a result.

**It was not retried, and an earlier note in this file saying the runner would retry it was wrong.** The runner
builds `pending` once, at start-up, from the manifest minus the checkpoint minus keys already at `MAX_ATTEMPTS`;
that list was consumed and the task exited `rc=0`. A retry needs the runner **re-invoked**. The ledger records
one non-ok attempt for the key, so `tries = 1 < 3` and a re-submission of sens array task 6 will take it as a
`pending` list of one — `done_keys` additionally requires all three files to exist and be non-empty, so there is
no way for the half-written run to be mistaken for a good one.

**This is not a run that can be written off.** Seed 10052 in `crash` is one of the **61 paths of 240** on which
`jump_rate__high` actually changes the market, so it falls in the *primary* verdict set that section 2 of E5's
pre-registration reads the level on, not merely in the 240-path sensitivity beside it. For ISFJ × crash the
primary set is 16 paths; losing this one takes it to 15 and breaks the `static`/`memory` seed pair on it. The
same cell succeeded at three other levels in the same task (897 s, 932 s, 928 s) against this attempt's 449 s,
so there is no sign of a systematically bad cell — one failure, one re-run.

**Repaired on 2 Nov** by re-submitting the same array task — `--export=ALL,STAGE=sens --array=6-6` — which needs
no special tooling because the runner rebuilds `pending` from the manifest minus the checkpoint. It reported
`17280 runs in the manifest, 17279 done, 1 pending, 0 abandoned`, ran the one run `ok (197s, fallbacks 0,
errors 0)`, and took the checkpoint to **17,280**. E5 is **103,680 of 103,680**. Three numbers agree again: the
repaired archive holds **54,783** entries, which is the other models' 54,782 plus the quarantined `.failed` file
that is still on disk beside the good run.

**The packaged copy had to be replaced, and this is the trap worth remembering.** `pack_stage.sbatch` had already
written `outbox/sens/..._llama-3.1-8b-instruct.tgz` at 54,780 entries, and nothing about that file says it is
short. It was moved to `superseded_archives/..._llama-3.1-8b-instruct.INCOMPLETE_17279of17280.tgz` — renamed to
say so, not deleted — the repair job's own archive put in its place, and the one line of `outbox/sens/MD5SUMS`
patched from the hash the job recorded, so no 4.4 GB of login-node hashing was needed.

Queued next, neither submitted: **E3** `--export=ALL,STAGE=slice --array=0-11%4` and **E4**
`--export=ALL,STAGE=track_a --array=0-9%4`. Both rosters are in the batch script and md5-matched on the cluster.

## 3. Cost: planned against measured

`e9_4/selection/cost.csv` sized every shard plan. E5 is running **ahead** of it — each model is taking 0.74–0.80
of its projection:

| model | E5 planned GPU-h | measured / projected |
|---|---|---|
| gpt-oss-20b | 40.3 | **22.5** (task 0, done) |
| Phi-4 | 33.0 | **26.4** (task 1, done) |
| OLMo 3.1 32B | 63.4 | **50.9** (tasks 2+3, done) |
| Ministral 3 14B | 41.7 | ~32 (tasks 4+5) |
| Llama 3.1 8B | 31.1 | ~23 (tasks 6+7) |
| Gemma 4 E4B | 15.7 | ~12 (tasks 8–11) |
| **total** | **225.2** | **~167** |

Programme total projects to about **242 GPU-h** of the ~300: E2 14.2 + E5 ~167 + E3 39.2 + E4 18.8 + the Llama
re-run 2.6. Utilisation on E2 measured **89.5 %**; E5 is running at roughly 94 % because the `%4` backfills as
soon as a task ends. There is unavoidable tail idle of about 6 GPU-h while the last Gemma 4 E4B shards finish,
because the Llama re-run waits on the whole array.

## 4. The packaging bug, and which jobs carry the fix

`stage2_b200.sbatch` packaged with the glob `$SUBDIR/*/$SLUG` — one wildcard level against a tree that is
`$SUBDIR/<setting>/<config_tag>/<slug>/<scenario>/<seed>/`. It matched **nothing**. Every task archived its
checkpoint and its ledger, printed "packaged" and exited 0, because nothing read `tar`'s status. E2 left 1.6 GB
of runs behind this way (`DECISION_LOG` P9-28).

Fixed in `stage2_b200.sbatch`: find the model directory at any depth, and fail loudly below 100 entries.
**But SLURM spools a batch script at submit time**, so:

* **48312120 (E5) carries the broken version** — confirmed on 31 Oct: every one of its four finished tasks wrote
  a **2-entry** archive and logged `Cannot stat`. The runs themselves are intact on the cluster filesystem.
  `pack_stage.sbatch` (48378572) exists to repair exactly this, after the fact, on CPU.
* **48377825 (Llama) and anything submitted from now on carry the fix**, E3 and E4 included.

E5's tree measures ~292 KB per run over 3 files, so about **30 GB raw across ~311,000 files**; it gzips at
**0.159**, so expect roughly **4.8 GB in six archives**. Group storage stood at 990 G of a 2 T quota.

## 5. Getting to the cluster

The tunnel needs the account holder's password and Duo, so it cannot be re-established unattended, and it has
dropped repeatedly. What works:

* `ssh -f -N <host>` — **no `-M`**. A master already exists in most failure cases and `-M` wastes the Duo prompt
  on `already exists, disabling multiplexing`.
* `ssh -O check` **lies in two ways**: it reports a live master whose TCP connection is dead, and it reports
  `Connection refused` for an orphaned socket file whose process is gone. Clear with `ssh -O exit` or by removing
  the control sockets, then reconnect.
* **Multiplexed sessions never work under Git Bash.** MSYS's emulated Unix sockets cannot pass file descriptors,
  so `mux_client_request_session` always resets. `ssh -O proxy <host>` passes no descriptors and works; feed it
  commands on stdin. `scp` fails for the same reason — move files by base64 through the proxy channel instead.
* **The login node kills expensive commands.** `du -sh` over the run tree and a glob over ~100,000 metadata files
  both ended in `Connection closed by remote host`. Sample instead, or cap with `-maxdepth`.

## 6. What is settled, and what is open

**Settled and recorded.** E2 read on five models (`E2_RESULTS.md`, P9-30); the ledger `setting` filter (P9-27);
the packaging bug and the backup access-rule drift (P9-28); the Llama re-run under deviation 1 (P9-29); E5's
twelve levels verified to reach the generator, and `engine_used` recorded as a lossy label (P9-31).

**The path-change measurement now records identities, not just counts.** `e9_4/e5_path_change.json` held only
`changed: 61 of 240`, which states how much of a `jump_rate` verdict is real but does not let the analysis *read*
the verdict on those paths — which section 2 of E5's pre-registration requires. `tools/phase9/e9_5_path_change.py`
now also records `changed_paths` as `Scenario_Cell|Seed` strings, the same key `stats_v2.seed_level_pairs` builds
as `Path`; all 61 and all 41 join to the 240 stage-1 path keys with no orphans. Re-running it reproduced the
pre-registration's table exactly — `jump_rate__high` 61/240 (flat 16, bull_trap 13, crash 16, sustained_bull 16),
`jump_rate__low` 41/240 (10, 10, 10, 11), the other ten levels 240/240.

**An ambiguity in E5's registered analysis, awaiting a decision.** Section 3 says `run_stats_v21` is called per
model per level "on a frame holding only that level's rows beside the stage-1 default's". It cannot be done as
written: `seed_level_pairs` groups on (Model, Persona, Scenario_Cell, Seed, Arm) and averages everything else,
`Setting` included, and E5's seeds 10001–10060 **are** the headline's first 60, so every key appears twice. On a
constructed frame where the level's true effect is 1.000 and the default's is 0.000, it returns **0.500** from 5
pairs instead of 10 — silently, which is the failure that same paragraph warns about for the twelve-settings
case. `question_families()` holds only (arm, reference) pairs, so nothing there rescues it. The coherent reading
is the level's rows alone for the sign and R5, with the default entering only for the level × arm interaction, as
a per-seed difference of differences on the common seeds. **Not acted on**: the pre-registration is not edited
without being asked, and this likely wants a numbered deviation under its section 8.

**Open, and none of it blocks the runs.**

* **`sizing_open.json`: the registered sha256 no longer verifies from a clean checkout.** This is explained
  now, and it is the `.gitattributes` rule doing the opposite of its purpose. `PREREG_PHASE_9_STAGE1_OPEN.md`
  registers the file at `d24f92de…`, which is its sha256 **with CRLF**: 6,559 bytes, 166 CRLF. The stage-1
  checkouts, taken before the rule, still hold exactly that and hash `d24f92de…`. `bc46d12` then added
  `docs/env_v2/generated/**/*.json text eol=lf`, which renormalised the stored blob to 6,393 bytes at 0 CRLF
  and `bf4370d9…`; the stage-2 checkout and git's own blob both hash that. **So a clean clone produces a file
  that does not match its pre-registration.** This working copy still matches only because it has not been
  re-checked-out since the rule landed — one `git checkout --` or `git add --renormalize` of that path converts
  it and the agreement disappears. CLAUDE.md describes the rule as making "a sha256 recorded in a
  pre-registration survive a Windows checkout"; for a hash registered *before* the rule, on CRLF bytes, it does
  the reverse. Needs a decision: re-register `bf4370d9…` under a numbered deviation, exempt the one path, or
  record both values and the command that reproduces each. **Not edited without being asked.**
* No `backup_identifiers.txt`, so the backup scrubber runs on generic markers only. Adequate for what has been
  uploaded; populating it is the account holder's call.
* `_write_stage2` re-verifies the manifest fingerprint but not the cells behind it.

## 7. Scoring runs on the cluster, not the laptop

Measured, not assumed: pulling through the ControlMaster's proxy channel runs at **150 KB/s** (the E2 Llama
archive, 50,249,250 bytes in 326 s, md5 matching the cluster's). At that rate E5's six archives are **8.5 h** and
E3's twelve another **1.2 h**, and unpacking E5 needs ~30 GB against the laptop's 51 GB free. So `verify` and
`score` run where the runs already are, and only their outputs come back.

The cluster venv has numpy 2.5.3, pandas 3.0.6, scipy 1.18.1 and scikit-learn 1.9.1, and `evaluation.metrics_v2`,
`tools.stats_v2`, `tools.phase9.e9_4_grid` and `envs.synthetic_market` all import. **`statsmodels` is not
installed there**, but `tools/stats_v2.py` imports it *inside* the three functions that fit the mixed model, so
`verify` and `score` never reach it. The split is therefore clean: scoring on the cluster, the registered stats on
the laptop, the scored `per_run.csv` the thing that travels.

`stage_score(only=...)` writes **`per_run_<key>.csv`**, not `per_run.csv`, so a restricted pass cannot overwrite
the full one; `stage_verify` likewise writes `verify_<key>.json`.

**That naming rule did not protect the cluster, because the cluster did not have it.** `repo_s2` is checked
out at `bc46d12`, one commit behind the `stage_score(only=...)` signature and the `per_run_<key>.csv` stem,
which landed locally in `5d8127d` and were never deployed. In `bc46d12`, `stage_score()` takes no argument and
the dispatch calls it with none, so `--only` restricted `verify` and did nothing at all to `score`. The job
scored every manifest on each of its four passes, printed `scored 133200 runs` four times, and wrote
**`per_run.csv`** rather than `per_run_causal_open.csv` each time.

**That overwrote the stage-1 scoring the file had held** — 17,568 + 8,784 + 814 = 27,166 runs, generated
29 Oct. Nothing is lost: the committed local `per_run.csv` carries those same 27,166 headline rows, and the
stage-1 runs are still on disk in the two other checkouts, so the block can be re-scored from either. The
result is usable as it stands — one file, 133,200 rows, all four stage-2 manifests at six models each, every
one verified `pass` and `complete`.

**The lesson is the checkout, not the flag.** A guard that exists in the working copy is not a guard on the
cluster. This section asserted safe-by-construction a few hours before the job proved otherwise; check which
commit the cluster is on before trusting a protection to be there. Both were checked for what they would carry into
a public repository before the job was queued: `per_run.csv` has 21 columns and no path column, and neither it nor
`verify*.json` holds a single cluster string. **A run's `meta.json` does**, which is why that check was worth
making — it records the absolute path it was written to.

## 8. The run archives go to Hugging Face from the cluster

The archives are **9.1 GB** in `outbox/` and far more unpacked, and the account holder chose to push them to
the private dataset repo **directly from the cluster** rather than stream them through the laptop.

**This is a deliberate exception to the rule that no credential goes on the shared account**, and it is recorded
as an exception rather than quietly taken. The cost the project already pays for that rule is visible in
`stage2_b200.sbatch`: Llama 3.1 8B is served from an open mirror, every file checked against Meta's, rather than
from Meta's gated repository — a workaround whose only purpose is to avoid needing an HF *read* token on the
cluster. A *write* token is strictly more dangerous than the read token that workaround avoids.

What limits the exposure:

* the token is **fine-grained, created for this push alone and revoked after it verifies**. It is *not* scoped
  to the one dataset repository: a `whoami` scope check before the push ran showed it scoped to the whole user
  namespace, carrying `repo.write` and `repo.contribute.write` over every repository in the account plus
  `inference.endpoints.write`, `inference.serverless.write`, `job.write`, `user.webhooks.write`,
  `user.billing.read` and a global `post.write`, where the push needs read and write on the contents of one
  dataset repo. **The account holder granted that deliberately and chose to proceed**, with the token removed
  once the push verifies. It is recorded here because the scope, not the token type, is what bounds the
  exposure, and a later reader should not infer a narrow token from the words "fine-grained". The check that
  established this is `whoami`, which reads back the granted scopes without printing token material, and it is
  worth running on any token placed here;
* it is placed by the account holder with `hf auth login`, which writes `~/.cache/huggingface/token` at mode 600.
  **It is never passed through `--export`**, so it does not enter the job environment that SLURM records, and it
  was never handled by, or visible to, anything that wrote this file;
* `hf_push_runs.py` reads it only through `huggingface_hub`'s own cache lookup, prints no token material, and
  **refuses the upload outright if the repository is not private** — which matters because the archives carry the
  cluster path inside each run's `meta.json` and so are not publishable as they stand;
* before any of this there was **no token anywhere on the cluster**: `~/.cache/huggingface/token`,
  `~/.huggingface/token` and `HF_TOKEN` were all checked and all absent.

### What is uploaded, and what is held back

The outbox is not only stage 2 — it also holds the headline runs, the earlier pilots and the re-packed E2
archives. All of that is run data and all of it goes up, under `cluster_runs/` with the outbox layout preserved.
Two classes of file do not.

* **The two code bundles.** They hold `tools/cluster/` sbatch scripts, which carry cluster and account detail and
  do not go to Hugging Face even privately. `tools/hf_backup.py` refuses them for the same reason.
* **Eighteen archives that hold no runs at all.** They were written before the packaging bug of section 4 was
  fixed, so each contains exactly two entries — a checkpoint and a ledger — and **zero run CSVs**, while being
  named exactly like a real run archive. Six are E2 causal, twelve are E5 sensitivity. The good copies of both
  are already in the outbox, re-packed into `repack/` and `sens/`, and those are uploaded. Filing the empty ones
  beside the real ones would have put something that looks like a result next to the result.

The gate is therefore the contents, not the name or the size: every `.tgz` is listed before upload and one
carrying no run CSV is excluded. **Nothing is dropped silently.** Every file in the outbox gets a row in
`cluster_runs/MANIFEST.tsv` — size, md5, entry count, run-CSV count, outcome — and that manifest is uploaded
last, so the exclusions are part of the record rather than an absence someone has to notice.

The repository held **14.27 GiB across 7,749 files** before this and the free tier allows 100 GB of private
storage, so there is room. The largest single archive is 1.04 GB, well inside any per-file cap.

### A sharded model has two archives and only one of them is complete

When a model is split across GPUs, every shard writes into the **same** results directory, and every shard
packages that whole directory when *it* finishes. So the shard that finishes last captures the complete cell
and the earlier ones capture a snapshot of however much had landed by then.

E4's OLMo 3.1 32B is the worked example. Task 2 holds **1,440 run CSVs** — the whole cell — and task 3 holds
**1,373**, because it packaged twenty-two seconds earlier. Both are uploaded, and neither filename says which
is which; the sizes are close enough (71.7 MB against 68.9 MB) to be no guide either.

**Read the run-CSV count in `cluster_runs/MANIFEST.tsv`, not the size and not the task number.** For a given
model and stage the complete archive is the one with the highest count, and that count should equal the
model's cell in the manifest — 1,440 for E4, 1,080 for E2, 2,880 for E5. The overlap between shard archives is
duplication, not disagreement: the shards write disjoint run keys into one tree, so the larger archive is a
superset of the smaller, and unpacking the larger alone is enough.

## 9. What runs next, in order

**Done on 2 Nov — the chain ran unattended, end to end.**

1. **E4** (48943107) — all ten tasks `COMPLETED 0:0`, every log `non-ok so far 0`, 8,640 runs. Each of the six
   models has one archive at the full 4,567 entries; the other shard of a pair is the earlier snapshot
   (section 8).
2. **Verify and score** (48943713) — 2 h 53 m, `COMPLETED 0:0`. All four manifests `"pass": true` and
   `"complete": true`, **0 missing and 0 mismatched everywhere**: causal 6 × 1,080 = 6,480, slice 6 × 2,400 =
   14,400, track_a 6 × 1,440 = 8,640, sensitivity 6 × 17,280 = **103,680**. E5 is whole and causal now carries
   all six models. The scoring itself ran unrestricted — section 7.
3. **The Hugging Face push** (48944660) — `COMPLETED 0:0` in 9 m 30 s. 236 files in the outbox: **109 uploaded,
   127 excluded, 0 failed**, 7.41 GiB under `cluster_runs/`, both code bundles held back, every empty
   packaging-bug archive held back, `MANIFEST.tsv` written last. The repository is 21.68 GiB of the 100 GB the
   free tier allows.

**What is left.**

4. **Pulled and verified.** `per_run.csv` (39.7 MB) and the four `verify_<key>.json` came down as one 12 MB
   gzip through the proxy in 93 s — about 174 KB/s — with the tar md5 `407258990440adfc54b956e08c6c6d35` and
   the CSV md5 `cfdb318ed1b4e6118025957bc283040f` equal on both ends. All four verify files read `"pass": true`
   and `"complete": true`.
5. **Frame assembled, every assertion green.** The committed headline block (17,568 + 8,784 + 814 = 27,166) plus
   the pulled 133,200 gives **160,366 rows**, written with LF endings as `.gitattributes` requires. The twenty-one
   columns are identical and in the same order in both halves, the manifest sets do not overlap, and the old
   **5,400-row five-model causal block is gone**, replaced by 6,480 at six models. Each stage-2 manifest was
   checked for row count, model count and per-model count before the concatenation: causal 6 × 1,080, slice
   6 × 2,400, track_a 6 × 1,440, sensitivity 6 × 17,280.
6. **The scoring-provenance check failed, and the failure was the check's.** The two `per_run.meta.json` files
   record different `scoring_json_sha256`, which would mean the halves were scored under different parameters —
   fatal for E2, whose contrast runs *between* them. They were not. `evaluation/params/scoring.json` holds 683
   CRLF line endings in this Windows checkout; its sha256 is `4e3e63ea…` as it sits and `11284396…` once
   normalised to LF, and those are exactly the two recorded values. The file is **not** covered by
   `.gitattributes` (`git check-attr` returns `text: unspecified`), so it is CRLF here and LF on the cluster and
   its recorded hash is a platform fingerprint rather than a parameter identity. Content identical, blocks
   comparable, frame sound.

   **The three new `verify_<key>.json` are invisible to `git status`**, since `.gitignore:69` matches the
   directory. They need `git add -f` like everything else there.
7. **E2 ran on six models on 3 Nov, and the output is not yet the registered read.** All six fitted, 54
   confirmatory tests each, one BH family per model, 0 score errors. But
   `PREREG_PHASE_9_STAGE2_E2.md` section 8's deviation gives Llama 3.1 8B **four** claim rules and
   `e9_5_e2_analyse.py` implements only the first of them.

   **Rule 3 is decisive and it is not close.** The directive placebo's JSON contract did not recover in the
   re-run: Llama's `placebo_directive` arm carries a mean parse-fallback share of 0.18 to 0.50 per cell against
   every other arm's exact 0.0, and **not one of its 360 directive runs is fallback-free** — 0 of 60 in all six
   cells, where the rule needs 30. Rule 2's recomputation on the fallback-free subset is therefore on an empty
   set, which gives the same answer. The other five models are 360 of 360 fallback-free in that arm, except
   Gemma 4 31B at 331 of 360.

   So **13 of Llama's 25 claims are `placebo_directive - static` and none of them may be read**; by the rule
   they are *uninterpretable, not null*. Its absorption figure for that arm, a median of +0.209 and the only
   positive one besides OLMo's +0.088, is computed wholly on fallback-contaminated runs and is not readable
   either. The 12 remaining claims — 6 `placebo_declarative`, 6 `wrapper_only`, both arms 60 of 60 clean in
   every cell — stand under rule 4's ordinary section 3 reading.

   **Llama therefore contributes nothing to the imperative-matched placebo claim**, which is the one the
   five-model headline rests on. Rules 2 and 3 must be implemented before any six-model statement is made;
   until then `stats_e2_causal/` holds an unrestricted read, not the registered one.
8. **Revoke the Hugging Face token** on the cluster once the push verifies — remove
   `~/.cache/huggingface/token`, then delete the token at the provider so the copy that sat on shared storage
   is dead. This matters more than it would for a narrow token: the one placed on 2 Nov carries namespace-wide
   write, inference, jobs, webhooks and public posting (section 8). The exception is meant to last hours, not
   to become the state of the account.

**Idle and unrevoked, as of 3 Nov 10:19 UTC.**

* **The queue is empty and has been since the push finished at 15:33 UTC on 2 Nov** — about nineteen hours of
  an allocation that ends 5 Nov. All four experiments are complete, so there is no outstanding GPU work; the
  question is whether anything *should* be run with what is left, and that is a decision, not an oversight.
* **The Hugging Face token is still on the cluster**, mode 600, 38 bytes. The push and the pull are both done
  and verified, so it has no remaining job. See step 8.

**Still open, and none of it blocks the runs.**

* **E5 section 3's frame instruction cannot be implemented as written** (section 6). It wants a numbered deviation
  under its section 8, and the pre-registration is not edited without being asked.
* **`sizing_open.json`: the registered sha256 no longer verifies from a clean checkout.** This is explained
  now, and it is the `.gitattributes` rule doing the opposite of its purpose. `PREREG_PHASE_9_STAGE1_OPEN.md`
  registers the file at `d24f92de…`, which is its sha256 **with CRLF**: 6,559 bytes, 166 CRLF. The stage-1
  checkouts, taken before the rule, still hold exactly that and hash `d24f92de…`. `bc46d12` then added
  `docs/env_v2/generated/**/*.json text eol=lf`, which renormalised the stored blob to 6,393 bytes at 0 CRLF
  and `bf4370d9…`; the stage-2 checkout and git's own blob both hash that. **So a clean clone produces a file
  that does not match its pre-registration.** This working copy still matches only because it has not been
  re-checked-out since the rule landed — one `git checkout --` or `git add --renormalize` of that path converts
  it and the agreement disappears. CLAUDE.md describes the rule as making "a sha256 recorded in a
  pre-registration survive a Windows checkout"; for a hash registered *before* the rule, on CRLF bytes, it does
  the reverse. Needs a decision: re-register `bf4370d9…` under a numbered deviation, exempt the one path, or
  record both values and the command that reproduces each. **Not edited without being asked.**
* No `backup_identifiers.txt`, so the backup scrubber runs on its built-in markers only.
* `_write_stage2` re-verifies the manifest fingerprint but not the cells behind it.
* **Nothing from this programme is committed yet.** `e5_path_change.json` and `verify_causal_open.json` sit under
  `docs/env_v2/generated/v2_1`, which `.gitignore:69` matches, so `git add` drops them silently and they need
  `git add -f` followed by a check of `git show --stat`.
