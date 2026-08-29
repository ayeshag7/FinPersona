"""
Provenance hashing for FinPersona-Bench runs (v2 plan, Section 2.1 block 10 and
Section 8 item 5; author review F28).

Every output row of a simulation carries:
  - Env_Version        : generator version string ("v1", "v2", ...)
  - Gen_Config_Hash    : sha256[:16] of the generator's full configuration
                         (scenario, T, seed, every parameter the generator
                         exposes through get_metadata()) -- a change in any
                         parameter changes the hash, so two rows with the same
                         hash were produced by identical generator settings.
  - Env_Code_Hash      : v1: sha256[:16] of the generator source file. v2 (from v2.1
                         Phase 0): sha256[:16] of the FREEZE MANIFEST -- the sorted
                         "path:sha256" lines of every file in V2_FREEZE_PATTERNS
                         (envs/v2/**/*.py, the facade, envs/v2/params/*.json and the six
                         evaluation modules), hashed after CRLF -> LF normalisation -- so
                         a change to the GARCH, event, mispricing or observables code, or
                         to a parameter file, changes the hash on every logged row
                         (weakness item 65). The frozen manifest is tests/v2_freeze_manifest.json.
  - Prompt_Hash        : sha256[:16] of the complete prompt *template* the agent
                         uses (system prompt + human template + format
                         instructions + mandate text if any), i.e. everything
                         that is constant across steps. The per-step rendered
                         observation is not part of the hash (it is logged
                         in the row itself).
  - Temperature        : the sampling temperature actually passed to the model.

All hashes are short (16 hex chars = 64 bits), which is ample for collision
avoidance across a benchmark's worth of configurations while keeping CSVs
readable.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from typing import Any, Dict, Iterable, Optional

HASH_LEN = 16
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V2_FREEZE_PATTERNS = ("envs/v2/**/*.py", "envs/synthetic_market.py", "envs/v2/params/*.json",
                      "evaluation/stylized_facts.py", "evaluation/leakage_audit.py", "evaluation/observables_oracle.py",
                      "evaluation/metrics_v2.py", "evaluation/baselines_v2.py", "evaluation/targets.py")
MANIFEST_PATH = os.path.join(REPO_ROOT, "tests", "v2_freeze_manifest.json")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:HASH_LEN]


def code_manifest(root: str = REPO_ROOT) -> Dict[str, str]:
    """{relative path: full sha256} of every file in V2_FREEZE_PATTERNS under `root`, line endings normalised."""
    import glob
    out = {}
    for pat in V2_FREEZE_PATTERNS:
        for p in glob.glob(os.path.join(root, pat), recursive=True):
            if "__pycache__" in p:
                continue
            with open(p, "rb") as fh:
                data = fh.read().replace(b"\r\n", b"\n")
            out[os.path.relpath(p, root).replace("\\", "/")] = hashlib.sha256(data).hexdigest()
    return dict(sorted(out.items()))


def manifest_hash(files: Dict[str, str]) -> str:
    """Full sha256 of the sorted 'path:hash' lines."""
    payload = "\n".join(f"{k}:{files[k]}" for k in sorted(files)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def stable_hash(obj: Any) -> str:
    """Hash of a JSON-serialisable object, independent of key order."""
    payload = json.dumps(obj, sort_keys=True, default=str, ensure_ascii=False,
                         separators=(",", ":"))
    return _sha(payload.encode("utf-8"))


def text_hash(*parts: str) -> str:
    """Hash of one or more text parts. Parts are joined with an unambiguous
    separator so ("ab","c") != ("a","bc")."""
    joined = "\x1f".join(parts)
    return _sha(joined.encode("utf-8"))


def file_hash(path: str) -> str:
    with open(path, "rb") as fh:
        return _sha(fh.read())


def generator_config_hash(metadata: Dict[str, Any]) -> str:
    """Hash of the generator configuration dict (use env.get_metadata())."""
    return stable_hash(metadata)


def prompt_hash(system_prompt: str,
                human_template: str,
                format_instructions: str = "",
                mandate: str = "",
                extra: Optional[Iterable[str]] = None) -> str:
    parts = [system_prompt, human_template, format_instructions, mandate]
    if extra:
        parts.extend(extra)
    return text_hash(*parts)


def git_commit(short: bool = True) -> str:
    """Current git commit of the working tree, or 'unknown'."""
    try:
        out = subprocess.run(["git", "rev-parse", "--short" if short else "HEAD"],
                             capture_output=True, text=True, timeout=5,
                             cwd=os.path.dirname(os.path.abspath(__file__)))
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return "unknown"


def env_provenance(env) -> Dict[str, Any]:
    """Provenance fields derived from an environment object.

    Works with any env exposing get_metadata(); ENV_VERSION is read from the
    class if present (v1 generator has none -> "v1")."""
    import inspect
    meta = env.get_metadata()
    version = getattr(env, "ENV_VERSION", None) or meta.get("env_version", "v1")
    try:
        if version == "v2":
            code_hash = manifest_hash(code_manifest(REPO_ROOT))[:HASH_LEN]
        else:
            src = inspect.getsourcefile(type(env))
            code_hash = file_hash(src) if src else "unknown"
    except Exception:
        code_hash = "unknown"
    return {
        "Env_Version": version,
        "Gen_Config_Hash": generator_config_hash(meta),
        "Env_Code_Hash": code_hash,
    }


def agent_provenance(agent) -> Dict[str, Any]:
    """Provenance fields derived from an agent object.

    The agent may expose prompt_components() -> dict(system=..., human=...,
    format_instructions=..., mandate=...). Falls back to attributes used by the
    v1 agents (full_system_prompt, core_mandate, parser)."""
    comps = None
    if hasattr(agent, "prompt_components"):
        try:
            comps = agent.prompt_components()
        except Exception:
            comps = None
    if comps is None:
        comps = {
            "system": getattr(agent, "full_system_prompt", ""),
            "human": getattr(agent, "human_template", ""),
            "format_instructions": "",
            "mandate": getattr(agent, "core_mandate", ""),
        }
        parser = getattr(agent, "parser", None)
        if parser is not None and hasattr(parser, "get_format_instructions"):
            try:
                comps["format_instructions"] = parser.get_format_instructions()
            except Exception:
                pass
    return {
        "Prompt_Hash": prompt_hash(comps.get("system", ""), comps.get("human", ""),
                                   comps.get("format_instructions", ""),
                                   comps.get("mandate", "")),
        "System_Prompt_Hash": text_hash(comps.get("system", "")),
        "Temperature": getattr(agent, "temperature", None),
        "Git_Commit": git_commit(),
    }
