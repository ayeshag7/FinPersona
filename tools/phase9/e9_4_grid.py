"""
v2.1 Phase 9 -- E9.4 stage 1: the manifests the grid runs, and the check that every planned cell has a run with the
right hashes and configuration (plan 13.4; PREREG_PHASE_9.md 4.1).

    python -u -m tools.phase9.e9_4_grid --stages manifest          # after E9.2's sizing.json exists
    python -u -m tools.phase9.e9_launch --manifest docs/env_v2/generated/v2_1/e9_4/manifest_headline.json --workers 15
    python -u -m tools.phase9.e9_launch --manifest docs/env_v2/generated/v2_1/e9_4/manifest_slice.json --workers 15
    python -u -m tools.phase9.e9_4_grid --stages verify,status

**Two manifests, run in order per model.** The headline cells answer the question the team staged first; the D11
common-start slice (P8-13, P8-14) runs after them, so no model's headline answer waits on it.

`manifest`  Reads the seed count S from `e9_2/sizing.json` (E9.2's rule: the maximum of the roster's band-MAS sigma_d
            limits, then Appendix A at alpha' = 0.05 / 36).  Refuses if any roster model is missing from the sizing.
            * headline: 3 personas x (static, memory) x 4 scenarios x seeds 10001..10000+S, setting "default";
            * slice: 3 personas x (static, memory, swapped) + the NONE trader, all at `start_design="common"`, the
              same scenarios and seeds, setting "common_start" (the setting is a path and run-key component, so a
              slice run never collides with its headline twin).
            Both carry the fingerprint `tools/phase9/e9_runner.fingerprint` computes.
`verify`    For every planned cell with a run on disk: the run's `Prompt_Hash` equals the manifest's for that
            (configuration, persona, arm), `Env_Code_Hash` equals the manifest's, the harness and placebo versions are
            v2_1, `Provider_Options` names the cell's configuration, and the scenario, seed and start design are the
            planned ones.  Missing runs are counted, never silently passed.
`status`    Runs done and pending per configuration, per manifest.

Outputs: docs/env_v2/generated/v2_1/e9_4/{manifest_headline.json, manifest_slice.json, verify.json}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e9_4")
SIZING = os.path.join(GEN, "e9_2", "sizing.json")
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
SCENARIOS = ("flat", "bull_trap", "crash", "sustained_bull")
HEADLINE_ARMS = ("static", "memory")
SLICE_ARMS = ("static", "memory", "swapped")
GRID_SEED0 = 10001
MANIFESTS = {"headline": "manifest_headline.json", "slice": "manifest_slice.json"}


def seeds_from_sizing() -> tuple:
    if not os.path.exists(SIZING):
        raise SystemExit(f"{os.path.relpath(SIZING, ROOT)} does not exist: E9.2's pilots must be scored and analysed first "
                         f"(PREREG_PHASE_9.md 2)")
    d = json.load(open(SIZING, encoding="utf-8"))
    if not d.get("complete"):
        raise SystemExit(f"the sizing lacks a model: {d.get('missing_models')}. Stage 1 does not start on a plug-in that "
                         f"lacks a roster model (PREREG_PHASE_9.md 2)")
    S = int(d["stage1_seeds_appA"])
    return S, list(range(GRID_SEED0, GRID_SEED0 + S)), d


def grid_configs(sizing: dict) -> tuple:
    """The configurations the grid runs: the roster members the sizing actually MEASURED (PREREG_PHASE_9.md 2).

    A configuration that was never piloted cannot be in a grid sized without it -- Qwen3.7 Flash and GLM 4.7 Flash
    failed the registered smoke stopping rule (DECISION_LOG P9-10) -- so it is named in the manifest rather than
    included silently.  A roster member missing from the sizing WITHOUT a registered reason is refused, which is what
    the docstring above always promised and `sizing.json`'s `complete` no longer checks on its own."""
    from tools.phase9 import e9_roster as RO
    measured = set(sizing.get("per_model_band_mas", {}))
    configs = [k for k in RO.ROSTER if k in measured]
    left_out = [k for k in RO.ROSTER if k not in measured]
    unregistered = [k for k in left_out if k not in set(sizing.get("not_piloted_registered", []))]
    if unregistered:
        raise SystemExit(f"roster configurations missing from the sizing with no registered reason: {unregistered}. "
                         f"Stage 1 does not start on a plug-in that lacks a roster model (PREREG_PHASE_9.md 2)")
    if not configs:
        raise SystemExit("the sizing measured no roster configuration")
    return configs, left_out


def cells_for(kind: str, seeds) -> list:
    out = []
    if kind == "headline":
        for p in PERSONAS:
            for a in HEADLINE_ARMS:
                for sc in SCENARIOS:
                    for s in seeds:
                        out.append({"persona": p, "arm": a, "scenario": sc, "seed": s, "rep": 0, "setting": "default"})
        return out
    for p in PERSONAS:
        for a in SLICE_ARMS:
            for sc in SCENARIOS:
                for s in seeds:
                    out.append({"persona": p, "arm": a, "scenario": sc, "seed": s, "rep": 0, "setting": "common_start",
                                "factors": {"start_design": "common"}})
    for sc in SCENARIOS:                      # the no-persona reference (P8-14: NONE only; O3 cannot run in v2)
        for s in seeds:
            out.append({"persona": "NONE", "arm": "trader", "scenario": sc, "seed": s, "rep": 0, "setting": "common_start"})
    return out


def stage_manifest():
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    S, seeds, sizing = seeds_from_sizing()
    configs, left_out = grid_configs(sizing)
    if left_out:
        print(f"[manifest] {len(left_out)} roster configuration(s) not piloted and therefore NOT in the grid (P9-10): {left_out}")
    os.makedirs(OUT, exist_ok=True)
    for kind, fname in MANIFESTS.items():
        cells = cells_for(kind, seeds)
        m = {"name": f"e9_4_stage1_{kind}", "kind": "grid", "subdir": f"stage1_{kind}", "ledger_dir": "e9_4",
             "T": 200, "configs": configs, "configs_not_piloted": left_out, "cells": cells, "seeds": seeds,
             "seeds_per_cell": S,
             "sizing": {k: sizing[k] for k in ("plugin_sigma_d_band_mas", "plugin_model", "alpha_bonferroni", "delta",
                                               "stage1_seeds_appA", "stage1_seeds_paired_correct")},
             "registered": "PREREG_PHASE_9.md 4.1; DECISION_LOG P9-2, P9-3, P9-5",
             "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        path = os.path.join(OUT, fname)
        if os.path.exists(path):
            R.verify_fingerprint(json.load(open(path, encoding="utf-8")))
            print(f"{fname}: exists and its fingerprint matches; not rewritten")
            continue
        m["fingerprint"] = R.fingerprint(m)
        json.dump(m, open(path, "w", encoding="utf-8", newline="\n"), indent=1)
        print(f"{fname}: {len(m['configs'])} configurations x {len(cells):,} runs at {S} seeds per cell")


def stage_verify():
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    rows, missing = [], []
    for kind, fname in MANIFESTS.items():
        path = os.path.join(OUT, fname)
        if not os.path.exists(path):
            continue
        m = R.load_manifest(path)
        fp = m["fingerprint"]
        for key in m["configs"]:
            mc = RO.by_key(key)
            n_ok = n_missing = 0
            bad = []
            for c in m["cells"]:
                cfg = R.cfg_for(mc, c, m["subdir"])
                p = R.run_paths(cfg)
                if not (os.path.exists(p["csv"]) and os.path.exists(p["meta"])):
                    n_missing += 1
                    continue
                meta = json.load(open(p["meta"], encoding="utf-8"))
                prov, rc = meta["provenance"], meta["run_config"]
                want_prompt = fp["prompt_hash"].get(f"{key}|{c['persona']}|{c['arm']}")
                checks = {
                    "prompt_hash": want_prompt is None or prov.get("Prompt_Hash") == want_prompt,
                    "env_code_hash": prov.get("Env_Code_Hash") == fp["Env_Code_Hash"],
                    "harness_version": rc.get("harness_version") == "v2_1",
                    "placebo_version": rc.get("placebo_version") == "v2_1",
                    "config_tag": (rc.get("provider_options") or {}).get("config_tag") == mc.config_tag,
                    "model": rc.get("model_name") == mc.model,
                    "scenario": rc.get("scenario") == c["scenario"],
                    "seed": int(rc.get("seed", -1)) == int(c["seed"]),
                    "start_design": rc.get("start_design") == ("common" if c.get("setting") == "common_start" else "target"),
                }
                if all(checks.values()):
                    n_ok += 1
                else:
                    bad.append({"run_key": R.run_key(c, cfg), "failed": [k for k, v in checks.items() if not v]})
            rows.append({"manifest": kind, "config": key, "planned": len(m["cells"]), "verified": n_ok,
                         "missing": n_missing, "mismatched": len(bad)})
            missing += bad[:20]
            print(f"  {kind:9s} {key:34s} verified {n_ok}/{len(m['cells'])}, missing {n_missing}, mismatched {len(bad)}", flush=True)
    doc = {"registered": "plan 13.4; PREREG_PHASE_9.md 4.1", "rows": rows, "mismatches": missing,
           "pass": bool(rows) and all(r["mismatched"] == 0 for r in rows),
           "complete": bool(rows) and all(r["missing"] == 0 for r in rows),
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    os.makedirs(OUT, exist_ok=True)
    json.dump(doc, open(os.path.join(OUT, "verify.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps({k: doc[k] for k in ("pass", "complete")}, indent=1))
    return 0 if doc["pass"] else 1


def stage_status():
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    for kind, fname in MANIFESTS.items():
        path = os.path.join(OUT, fname)
        if not os.path.exists(path):
            continue
        m = R.load_manifest(path)
        for key in m["configs"]:
            mc = RO.by_key(key)
            led = R.read_ledger(R.ledger_file(m["ledger_dir"], mc))
            st = pd.Series([r["status"] for r in led]).value_counts().to_dict() if led else {}
            print(f"{kind:9s} {key:34s} {len(R.done_keys(m['subdir'], mc, m['cells']))}/{len(m['cells'])} done; attempts {st}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="manifest")
    a = ap.parse_args(argv)
    rc = 0
    for st in [x.strip() for x in a.stages.split(",") if x.strip()]:
        if st == "manifest":
            stage_manifest()
        elif st == "verify":
            rc = stage_verify() or rc
        elif st == "status":
            stage_status()
        else:
            raise SystemExit(f"unknown stage {st!r}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
