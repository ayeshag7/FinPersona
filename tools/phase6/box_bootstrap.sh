#!/usr/bin/env bash
# v2.1 Phase 6 -- the lab box (docs/COMPUTE_GPU_ACCESS.md): from a fresh clone to a verified reference machine, then the
# sklearn-heavy stages at 24 workers.  Every stage writes its own files and skips itself when they exist (rule 14), so
# the script can be re-run after a reset.  Run under tmux:
#
#     tmux new -d -s p6 "bash tools/phase6/box_bootstrap.sh env,panel,hashes,refrow 2>&1 | tee -a /nfs1/ayesha/logs/bootstrap.log"
#     tmux new -d -s nulls "bash tools/phase6/box_bootstrap.sh nulls 2>&1 | tee -a /nfs1/ayesha/logs/nulls.log"
#
# Stages: env      -- versions, cores, the cgroup limit, missing packages installed through the proxy
#         panel    -- the 1,600-path SEP panel of the deployed state regenerated with the fast renderer (verified bit for bit
#                     against panel_from_env on the first seed) -> _panels/sep_phase5_after.pkl
#         hashes   -- the 95-configuration path hashes compared with the laptop's fixture (path_hashes_phase5_after.json)
#         refrow   -- the two reference rows: test_smm_reference_row, and BASE|x|all of e5_7a/final refitted on the regenerated
#                     panel (must equal 0.4058695137596712 exactly or at floating-point level)
#         nulls    -- E6.6/E6.7 target-permutation nulls (resumes from the null.json in the clone)
#
# The rule (COMPUTE_GPU_ACCESS.md): no fitted number from this machine is reported until refrow agrees.
set -u
STAGES="${1:-env,panel,hashes,refrow}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY=/nfs1/ayesha/venv/bin/python
LOGS=/nfs1/ayesha/logs
GEN="$ROOT/docs/env_v2/generated/v2_1"
PANEL="$GEN/_panels/sep_phase5_after.pkl"
WORKERS="${WORKERS:-24}"
export http_proxy=http://127.0.0.1:7890/ https_proxy=http://127.0.0.1:7890/ NO_PROXY=localhost,127.0.0.1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONUNBUFFERED=1
mkdir -p "$LOGS" "$GEN/_panels"
cd "$ROOT"
has() { case ",$STAGES," in *",$1,"*) return 0;; *) return 1;; esac; }
say() { echo "[$(date +%H:%M:%S)] $*"; }

if has env; then
  say "host $(hostname); nproc $(nproc); cgroup $(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || cat /sys/fs/cgroup/memory.max) bytes"
  # the tree arrives as a GitHub tarball (git 2.25's gnutls fails the handshake through the proxy; curl does not), so the
  # commit is recorded from the COMMIT file the laptop writes beside it, or from git when a clone exists
  say "commit $(git rev-parse --short HEAD 2>/dev/null || cat "$ROOT/COMMIT" 2>/dev/null || echo unknown)"
  $PY -c "import sys,numpy,pandas,scipy,sklearn; print('python', sys.version.split()[0], 'numpy', numpy.__version__, 'pandas', pandas.__version__, 'scipy', scipy.__version__, 'sklearn', sklearn.__version__)"
  # the venv was built with uv and carries no pip
  $PY -c "import statsmodels, arch, pytest" 2>/dev/null || { say "installing statsmodels + arch + pytest through the proxy (uv)"; /nfs1/ayesha/uv/uv pip install -q --python "$PY" "statsmodels==0.14.6" "arch==8.0.0" pytest 2>&1 | tail -2; }
  $PY -c "import statsmodels, arch, pytest; print('statsmodels', statsmodels.__version__, 'arch', arch.__version__)"
fi

if has panel; then
  if [ -f "$PANEL" ]; then say "panel exists: $PANEL"; else
    say "building the SEP panel of the deployed state at $WORKERS workers (verify=True on the first seed)"
    $PY -m tools.phase5.e5_after_state --stages panel --workers "$WORKERS" 2>&1 | tail -5
    [ -f "$PANEL" ] && say "panel written: $(du -h "$PANEL" | cut -f1)" || say "PANEL BUILD FAILED"
  fi
fi

if has hashes; then
  if [ -f "$LOGS/hashes_box.json" ]; then say "hashes exist"; else
    say "computing the 95-configuration path hashes"
    $PY -m tools.path_hashes --out "$LOGS/hashes_box.json" 2>&1 | tail -2
  fi
  say "comparing with the laptop fixture"
  $PY -m tools.path_hashes --compare "$GEN/path_hashes_phase5_after.json" "$LOGS/hashes_box.json" 2>&1 | tail -6
fi

if has refrow; then
  say "reference row 1: test_smm_reference_row"
  $PY -m pytest tests/test_v2_1_phase_2.py::test_smm_reference_row -q -p no:cacheprovider 2>&1 | tail -3
  say "reference row 2: BASE|x|all refitted on the regenerated panel (e5_7a_ablation, add stage, VAL only, x, all rows)"
  if [ ! -f "$LOGS/refrow/ablation.json" ]; then
    $PY -m tools.phase5.e5_7a_ablation --panel "$PANEL" --out "$LOGS/refrow" --label "box reference row" --stages add --groups VAL --targets x --pops all --workers 4 2>&1 | tail -4
  fi
  $PY - <<'EOF'
import json, os
box = json.load(open(os.path.join("/nfs1/ayesha/logs/refrow", "ablation.json")))["fits"]["BASE|x|all"]["R2"]
# the laptop's value: read from e5_7a/final/ablation.json when the 9.8 MB file is on the box, else the verified record
# (e6_0/verify.md row "BASE|x|all (the box's reference row)": 0.4058695137596712)
p = "docs/env_v2/generated/v2_1/e5_7a/final/ablation.json"
lap = json.load(open(p))["fits"]["BASE|x|all"]["R2"] if os.path.exists(p) else 0.4058695137596712
print(f"BASE|x|all  box {box!r}  laptop {lap!r}  diff {box - lap:.3e}  ->", "AGREE" if abs(box - lap) < 1e-9 else "DISAGREE")
EOF
fi

if has nulls; then
  say "E6.6 L2 null (all, calm) at $WORKERS workers"
  $PY -u tools/phase6/e6_6_null.py --panel "$PANEL" --out "$GEN/e6_6/null" --label "Phase-5 hand-over state (box)" \
      --stages l2 --pops all,calm --n-perm 20 --workers "$WORKERS" 2>&1 | grep -v "^\[state\]"
  say "E6.7 L2b null at $WORKERS workers"
  $PY -u tools/phase6/e6_6_null.py --panel "$PANEL" --out "$GEN/e6_6/null" --label "Phase-5 hand-over state (box)" \
      --stages l2b --n-perm 20 --workers "$WORKERS" 2>&1 | grep -v "^\[state\]"
  say "nulls done"
fi
say "stages [$STAGES] finished"
