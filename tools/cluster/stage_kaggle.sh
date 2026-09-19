#!/usr/bin/env bash
# Stage every completed vLLM pilot for Kaggle and push it as a new dataset version: an off-site backup of run outputs
# that are otherwise on disk only (results_v2/ is gitignored).
#
#   bash tools/cluster/stage_kaggle.sh            # stage and push a new version
#   bash tools/cluster/stage_kaggle.sh --create   # first time only: create the dataset
#   bash tools/cluster/stage_kaggle.sh --dry-run  # stage and scan, push nothing
#
# Only our own derived outputs go up -- ledgers, per-run CSVs, the manifests and the roster.  Never datasets/.
# Two Kaggle CLI quirks this works around, both learned the hard way:
#   * a staging path containing "~" (Windows 8.3 names such as AYESHA~1.GUL) breaks the CLI's upload temp paths,
#     so the stage lives at a short, plain path;
#   * a LOOSE top-level file (a README.md) fails the same way, while directories zip fine, so every file sits in a
#     directory.
set -euo pipefail
MODE="${1:-version}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
STAGE="${FP_KAGGLE_STAGE:-$HOME/AppData/Local/Temp/fp_stage}"
DATASET="ayeshaiq/finpersona-vllm-pilots"

rm -rf "$STAGE"; mkdir -p "$STAGE/e9_2" "$STAGE/results" "$STAGE/provenance" "$STAGE/about"
cd "$REPO"
cp docs/env_v2/generated/v2_1/e9_2/ledger_default_vllm_*.jsonl "$STAGE/e9_2/" 2>/dev/null || true
for d in results_v2/phase9/pilot/default/default/vllm_*; do [ -d "$d" ] && cp -r "$d" "$STAGE/results/"; done
# OpenRouter pilots whose per-run outputs exist only on this disk (results_v2/ is gitignored), named explicitly
for slug in ${FP_OPENROUTER_SLUGS:-openrouter_deepseek_deepseek-v4.1-flash}; do
  cp docs/env_v2/generated/v2_1/e9_2/ledger_default_${slug}.jsonl "$STAGE/e9_2/" 2>/dev/null || true
  d=results_v2/phase9/pilot/default/default/$slug; [ -d "$d" ] && cp -r "$d" "$STAGE/results/"
done
# a manifest goes up exactly when its ledger does -- so no manifest travels without the runs it describes
python - "$STAGE" <<'PYM'
import glob, json, os, shutil, sys
e92 = "docs/env_v2/generated/v2_1/e9_2"
for m in glob.glob(f"{e92}/manifest_vllm_*.json") + glob.glob(f"{e92}/manifest_openrouter_*.json"):
    slug = json.load(open(m, encoding="utf-8"))["configs"][0].split("|")[0].replace("/", "_")
    if os.path.exists(os.path.join(sys.argv[1], "e9_2", f"ledger_default_{slug}.jsonl")):   # its ledger is staged
        shutil.copy(m, os.path.join(sys.argv[1], "e9_2"))
PYM
cp tools/phase9/e9_roster.py "$STAGE/provenance/"

cat > "$STAGE/dataset-metadata.json" <<JSON
{ "title": "finpersona-vllm-pilots", "id": "$DATASET", "licenses": [{ "name": "other" }] }
JSON

cat > "$STAGE/about/README.md" <<'MD'
# FinPersona -- E9.2 variance pilots for open-weight models

Two routes, recorded on every row as `provider_options.provider`:
* `vllm` -- served on our own vLLM (UF HiPerGator, RTX PRO 6000 Blackwell); no key, `base_url` 127.0.0.1, no cost;
* `openrouter` -- bought through OpenRouter, pinned to one upstream (`upstream_pinned`), cost logged per run.

Each model runs the same 96 cells: 3 personas x (static, memory) x 4 scenarios x 4 seeds (3001-3004), 200 LLM calls
per run, environment frozen at Env_Code_Hash = 1d689aaf82a33a2e.

* e9_2/ledger_default_vllm_*.jsonl -- one row per run: status, tokens, seconds, provider options
* e9_2/manifest_vllm_*.json        -- the cells and the fingerprint the runner verified against
* results/                         -- per run: step-level CSV, .meta.json, .usage.json
* provenance/e9_roster.py          -- the configurations, each pinned to a Hugging Face revision
MD

echo "staged $(find "$STAGE" -type f | wc -l) files ($(du -sh "$STAGE" | cut -f1)) at $STAGE"
ls "$STAGE/results"

# refuse to publish anything that looks like a credential
if grep -rqE "sk-[A-Za-z0-9]{16,}|AIza[0-9A-Za-z_-]{30,}|sk-or-v1|_API_KEY *=" "$STAGE"; then
  echo "REFUSING: a credential-like string is in the stage"; exit 1
fi
echo "secret scan: clean"

[ "$MODE" = "--dry-run" ] && { echo "dry run: nothing pushed"; exit 0; }
WIN_STAGE="$(cygpath -m "$STAGE" 2>/dev/null || echo "$STAGE")"   # the CLI is a Windows Python: give it C:/ paths
if [ "$MODE" = "--create" ]; then
  python -m kaggle datasets create -p "$WIN_STAGE" --dir-mode zip
else
  python -m kaggle datasets version -p "$WIN_STAGE" --dir-mode zip -m "${FP_KAGGLE_MSG:-pilot results update}"
fi
