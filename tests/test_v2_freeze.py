"""
v2 generator freeze (v2.1 plan, Phase 0, item 0.3; PREREG_PHASE_0.md §5).

* every file that defines a path or an audit statistic (envs/v2/**/*.py, envs/synthetic_market.py,
  envs/v2/params/*.json, the six evaluation modules) has the SHA-256 recorded in tests/v2_freeze_manifest.json;
* simulation.provenance.env_provenance() reports Env_Code_Hash = manifest hash for a v2 environment, so a change
  to the GARCH, event, mispricing or observables code (not only the facade) changes the hash on every logged row;
* the manifest is regenerated only deliberately (python -m tools.freeze_manifest --write), which the phase
  report logs as a decision (execution-order step-0 rule: any environment change after the freeze re-freezes).
"""
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _stored():
    from simulation.provenance import MANIFEST_PATH
    if not os.path.exists(MANIFEST_PATH):
        pytest.skip("no manifest yet: run python -m tools.freeze_manifest --write at the end of the phase")
    return json.load(open(MANIFEST_PATH, encoding="utf-8"))


def test_manifest_covers_every_generator_file():
    from simulation.provenance import code_manifest
    stored = _stored()
    now = code_manifest(ROOT)
    assert set(now) == set(stored["files"]), (set(now) ^ set(stored["files"]))
    for rel in ("envs/synthetic_market.py", "envs/v2/generator.py", "envs/v2/mispricing.py", "envs/v2/garch.py",
                "envs/v2/events.py", "envs/v2/observables.py", "envs/v2/schedule.py", "envs/v2/rng.py",
                "envs/v2/params/hazard.json", "evaluation/stylized_facts.py", "evaluation/leakage_audit.py",
                "evaluation/observables_oracle.py", "evaluation/metrics_v2.py", "evaluation/baselines_v2.py", "evaluation/targets.py"):
        assert rel in now, rel


def test_generator_matches_frozen_manifest():
    from simulation.provenance import code_manifest, manifest_hash
    stored = _stored()
    now = code_manifest(ROOT)
    changed = [k for k in stored["files"] if now.get(k) != stored["files"][k]]
    assert not changed, ("generator files changed since the freeze (re-freeze deliberately with "
                         "python -m tools.freeze_manifest --write and log it): " + ", ".join(changed))
    assert manifest_hash(now) == stored["manifest_hash"]


def test_env_code_hash_is_the_manifest_hash():
    from envs.synthetic_market import SyntheticMarketEnv
    from simulation.provenance import env_provenance, code_manifest, manifest_hash
    prov = env_provenance(SyntheticMarketEnv("flat", 30, 1))
    assert prov["Env_Version"] == "v2"
    assert prov["Env_Code_Hash"] == manifest_hash(code_manifest(ROOT))[:16]
    assert prov["Env_Code_Hash"] == _stored()["manifest_hash"][:16]


def test_env_code_hash_sensitive_to_any_generator_module(tmp_path, monkeypatch):
    """A change in any listed module (not only the facade) changes the manifest hash."""
    from simulation import provenance as pv
    import shutil
    # copy the repo's generator tree into a temp root, modify a non-facade module, hash both
    for rel in ("envs", "evaluation"):
        shutil.copytree(os.path.join(ROOT, rel), os.path.join(tmp_path, rel), ignore=shutil.ignore_patterns("__pycache__"))
    h0 = pv.manifest_hash(pv.code_manifest(str(tmp_path)))
    p = os.path.join(tmp_path, "envs", "v2", "garch.py")
    with open(p, "a", encoding="utf-8") as fh:
        fh.write("\n# provenance sensitivity check\n")
    h1 = pv.manifest_hash(pv.code_manifest(str(tmp_path)))
    assert h0 != h1
    # and the hash is line-ending independent
    q = os.path.join(tmp_path, "envs", "v2", "events.py")
    raw = open(q, "rb").read().replace(b"\r\n", b"\n")
    with open(q, "wb") as fh:
        fh.write(raw.replace(b"\n", b"\r\n"))
    assert pv.manifest_hash(pv.code_manifest(str(tmp_path))) == h1
