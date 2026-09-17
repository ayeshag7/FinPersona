#!/usr/bin/env bash
# Probe a HiPerGator-style SLURM cluster for whether it can run the FinPersona LLM grid.
#
#   bash tools/cluster/hpg_probe.sh
#
# The grid is ~100% outbound HTTPS to model providers and ~0% compute, so the decisive question is whether
# COMPUTE nodes have egress -- login-node egress is not enough, because the runs do not execute there.
# Everything here is read-only: no API calls with keys, no jobs beyond a 10-minute probe, nothing written
# outside the current directory.
set -uo pipefail

line() { printf '%s\n' "--------------------------------------------------------------------"; }
say()  { printf '%s\n' "$*"; }

say "FinPersona cluster probe"
line
say "host        : $(hostname)"
say "user        : ${USER:-unknown}"
say "date (utc)  : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say "os          : $(uname -sr)"
say "cwd         : $(pwd)"
line

# ---------------------------------------------------------------- 1. python
say "[1] python"
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1; then say "  $c -> $("$c" -V 2>&1) at $(command -v "$c")"; fi
done
command -v module >/dev/null 2>&1 && say "  'module' present; try: module spider python" || say "  no lmod 'module' command"
line

# ---------------------------------------------------------------- 2. login-node egress
probe() {  # probe <label> <url>
  local code
  code=$(curl -sS -m 12 -o /dev/null -w '%{http_code}' "$2" 2>/dev/null)
  if [ -z "$code" ] || [ "$code" = "000" ]; then say "  $1 : BLOCKED (no response)"; else say "  $1 : HTTP $code"; fi
}
say "[2] egress from the LOGIN node   (401/403 = reachable and refused = GOOD)"
probe "openai   " https://api.openai.com/v1/models
probe "google   " https://generativelanguage.googleapis.com/
probe "anthropic" https://api.anthropic.com/v1/models
probe "openrouter" https://openrouter.ai/api/v1/models
probe "pypi     " https://pypi.org/simple/
probe "github   " https://github.com
say "  http_proxy=${http_proxy:-unset} https_proxy=${https_proxy:-unset} no_proxy=${no_proxy:-unset}"
line

# ---------------------------------------------------------------- 3. slurm
say "[3] slurm"
if ! command -v sinfo >/dev/null 2>&1; then
  say "  no slurm on PATH -- stopping; the compute-node test below cannot run"
  exit 0
fi
ACCT=$(sacctmgr -nP show assoc user="${USER}" format=account 2>/dev/null | sort -u | head -1)
QOS=$(sacctmgr  -nP show assoc user="${USER}" format=qos     2>/dev/null | tr ',' '\n' | sort -u | head -3 | paste -sd, -)
say "  account(s) : ${ACCT:-none found}"
say "  qos        : ${QOS:-none found}"
say "  partitions (name/walltime limit):"
sinfo -h -o '    %-18P %l' 2>/dev/null | sort -u | head -12
line

# ---------------------------------------------------------------- 4. compute-node egress  (the decisive test)
say "[4] egress from a COMPUTE node   <-- this is the one that decides it"
SRUN_ARGS=(-t 00:10:00 --cpus-per-task=2 --mem=4gb)
[ -n "${ACCT:-}" ] && SRUN_ARGS+=(--account="${ACCT}")
say "  srun ${SRUN_ARGS[*]}"
srun "${SRUN_ARGS[@]}" bash -c '
  p() { c=$(curl -sS -m 12 -o /dev/null -w "%{http_code}" "$2" 2>/dev/null)
        if [ -z "$c" ] || [ "$c" = "000" ]; then echo "  $1 : BLOCKED (no response)"; else echo "  $1 : HTTP $c"; fi; }
  echo "  node       : $(hostname)"
  p "openai   " https://api.openai.com/v1/models
  p "google   " https://generativelanguage.googleapis.com/
  p "anthropic" https://api.anthropic.com/v1/models
  p "openrouter" https://openrouter.ai/api/v1/models
  p "pypi     " https://pypi.org/simple/
  echo "  http_proxy=${http_proxy:-unset} https_proxy=${https_proxy:-unset}"
' 2>&1 | sed 's/^/  /'
line

# ---------------------------------------------------------------- 5. storage
say "[5] storage (the grid writes ~1-2 GB of CSV per model)"
for d in "$HOME" /blue /orange /scratch "${SLURM_SUBMIT_DIR:-}"; do
  [ -n "$d" ] && [ -d "$d" ] && say "  $(df -h "$d" 2>/dev/null | awk 'NR==2 {printf "%-28s %6s avail of %-6s", "'"$d"'", $4, $2}')"
done
line
say "Done. Paste everything above back."
say "Reading: section [4] is decisive. 401/403 there = the cluster can run the grid."
say "         BLOCKED there (even if [2] is fine) = it cannot, and we run locally instead."
