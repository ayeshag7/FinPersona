"""
v2.1 Phase 9 -- E9.4 stage 1: the manifests the grid runs, and the check that every planned cell has a run with the
right hashes and configuration (plan 13.4; PREREG_PHASE_9.md 4.1).

    python -u -m tools.phase9.e9_4_grid --stages manifest          # after E9.2's sizing.json exists
    python -u -m tools.phase9.e9_launch --manifest docs/env_v2/generated/v2_1/e9_4/manifest_headline.json --workers 15
    python -u -m tools.phase9.e9_launch --manifest docs/env_v2/generated/v2_1/e9_4/manifest_slice.json --workers 15
    python -u -m tools.phase9.e9_launch --manifest docs/env_v2/generated/v2_1/e9_4/manifest_track_a.json --workers 15
    python -u -m tools.phase9.e9_4_grid --stages verify,status

**Three manifests, run in order per model.** The headline cells answer the question the team staged first; the D11
common-start slice (P8-13, P8-14) runs after them, so no model's headline answer waits on it, and the Track-A
communicated-target mirror of the headline grid runs last.

`manifest`  Reads the seed count S from `e9_2/sizing.json` (E9.2's rule: the maximum of the roster's band-MAS sigma_d
            limits, then Appendix A at alpha' = 0.05 / 36).  Refuses if any roster model is missing from the sizing.
            * headline: 3 personas x (static, memory) x 4 scenarios x seeds 10001..10000+S, setting "default";
            * slice: 3 personas x (static, memory, swapped) + the NONE trader, all at `start_design="common"`, the
              same scenarios and seeds, setting "common_start" (the setting is a path and run-key component, so a
              slice run never collides with its headline twin);
            * track_a: the headline cells exactly, each at `track="A"` (the persona's cash band is stated in the
              system prompt), setting "track_a".
            All three carry the fingerprint `tools/phase9/e9_runner.fingerprint` computes.
`manifest_open`  DECISION_LOG P9-12 to P9-14: the headline cells on the open-weight six (e9_roster.HEADLINE_OPEN) at
            `e9_2/sizing_open.json`'s paired-correct count, subdir "stage1_open" -> manifest_headline_open.json.
`manifest_open_b2`  DECISION_LOG P9-17, P9-18: the second batch (e9_roster.HEADLINE_OPEN_B2) on the six's cells and
            seeds -> manifest_headline_open_b2.json.
`verify`    For every planned cell with a run on disk: the run's `Prompt_Hash` equals the manifest's for that
            (configuration, persona, arm), `Env_Code_Hash` equals the manifest's, the harness and placebo versions are
            v2_1, `Provider_Options` names the cell's configuration, and the scenario, seed and start design are the
            planned ones.  Missing runs are counted, never silently passed.
`status`    Runs done and pending per configuration, per manifest.
`score`     Every completed run of every manifest -> e9_4/per_run.csv, scored as the pilots were
            (`evaluation.metrics_v2.score_run(scoring="v2_1")`); per_run.meta.json carries scored / planned counts.

Outputs: docs/env_v2/generated/v2_1/e9_4/{manifest_headline.json, manifest_slice.json, manifest_track_a.json,
         verify.json, per_run.csv}
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
MANIFESTS = {"headline": "manifest_headline.json", "slice": "manifest_slice.json",
             "track_a": "manifest_track_a.json"}
# DECISION_LOG P9-12 to P9-14: the open-weight headline is a fourth manifest, built by its own stage from its own sizing;
# verify, status and score read it with the other three
OPEN_MANIFEST = "manifest_headline_open.json"
SIZING_OPEN = os.path.join(GEN, "e9_2", "sizing_open.json")
# DECISION_LOG P9-17, P9-18: the second batch, on the six's cells and seeds
OPEN_B2_MANIFEST = "manifest_headline_open_b2.json"
SIZING_OPEN_B2 = os.path.join(GEN, "e9_2", "sizing_open_b2.json")

# ------------------------------------------------------------------------------------------ stage 2 (E2-E5)
# GRID_EXPERIMENT_PLAN.md 3 at its own quoted scale, S = 60, on the models HEADLINE_MODEL_SELECTION.md 4.3 assigns.
# Seeds are the FIRST 60 of the headline's 10001-10122, so every stage-2 cell shares its market paths with the
# headline's static and memory runs already on disk -- which is what lets E2 compare against them without re-running
# them, and what P9-21 relies on for E5's default level.
S_STAGE2 = 60
CAUSAL_ARMS = ("placebo_declarative", "placebo_directive", "wrapper_only")   # E2: static and memory are the headline's
CAUSAL_SCENARIOS = ("flat", "crash")                                        # E2: the plan's 1,080 = 3 x 3 x 2 x 60
CAUSAL_MANIFEST = "manifest_causal_open.json"                               # E2
SLICE_OPEN_MANIFEST = "manifest_slice_open.json"                            # E3
TRACK_A_OPEN_MANIFEST = "manifest_track_a_open.json"                        # E4
SENSITIVITY_MANIFEST = "manifest_sensitivity_open.json"                     # E5
STAGE2_MANIFESTS = {"causal_open": CAUSAL_MANIFEST, "slice_open": SLICE_OPEN_MANIFEST,
                    "track_a_open": TRACK_A_OPEN_MANIFEST, "sensitivity_open": SENSITIVITY_MANIFEST}
ALL_MANIFESTS = {**MANIFESTS, "headline_open": OPEN_MANIFEST, "headline_open_b2": OPEN_B2_MANIFEST,
                 **STAGE2_MANIFESTS}


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
    if kind == "causal":
        # E2: the three arms that separate CONTENT from IMPERATIVE FORCE from POSITION.  static and memory are not
        # here -- the headline already ran them on these same seeds and paths, so E2 is scored against those rows.
        for p in PERSONAS:
            for a in CAUSAL_ARMS:
                for sc in CAUSAL_SCENARIOS:
                    for s in seeds:
                        out.append({"persona": p, "arm": a, "scenario": sc, "seed": s, "rep": 0, "setting": "causal"})
        return out
    if kind in ("headline", "track_a"):
        # track_a mirrors the headline grid cell for cell; only the communicated-target factor and the setting (a path
        # and run-key component, so a track_a run never collides with its headline twin) differ.
        extra = ({"setting": "default"} if kind == "headline"
                 else {"setting": "track_a", "factors": {"track": "A"}})
        for p in PERSONAS:
            for a in HEADLINE_ARMS:
                for sc in SCENARIOS:
                    for s in seeds:
                        out.append({"persona": p, "arm": a, "scenario": sc, "seed": s, "rep": 0, **extra})
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


def stage_manifest_open():
    """PREREG_PHASE_9_STAGE1_OPEN.md; DECISION_LOG P9-12 to P9-14: PREREG_PHASE_9.md 4.1's headline cells on
    `e9_roster.HEADLINE_OPEN`, at `e9_2/sizing_open.json`'s paired-correct count.  The D11 slice and Track A are not
    built for this roster (P9-14).  Its own subdir, so none of its runs can mix with the API headline's."""
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    if not os.path.exists(SIZING_OPEN):
        raise SystemExit(f"{os.path.relpath(SIZING_OPEN, ROOT)} does not exist: run `e9_2_pilot --stages open` first")
    sz = json.load(open(SIZING_OPEN, encoding="utf-8"))
    if not sz.get("complete") or sz.get("roster") != list(RO.HEADLINE_OPEN):
        raise SystemExit("the open sizing is incomplete, or was taken over a roster other than e9_roster.HEADLINE_OPEN")
    S = int(sz["stage1_seeds"])
    seeds = list(range(GRID_SEED0, GRID_SEED0 + S))
    cells = cells_for("headline", seeds)
    m = {"name": "e9_4_stage1_headline_open", "kind": "grid", "subdir": "stage1_open", "ledger_dir": "e9_4",
         "T": 200, "configs": list(RO.HEADLINE_OPEN), "cells": cells, "seeds": seeds, "seeds_per_cell": S,
         "sizing": {k: sz[k] for k in ("plugin_sigma_d_band_mas", "plugin_model", "alpha_bonferroni", "delta",
                                       "stage1_seeds", "stage1_seeds_rule", "stage1_seeds_appA")},
         "registered": "PREREG_PHASE_9_STAGE1_OPEN.md; PREREG_PHASE_9.md 4.1 (headline cells); "
                       "DECISION_LOG P9-5, P9-12, P9-13, P9-14",
         "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    path = os.path.join(OUT, OPEN_MANIFEST)
    if os.path.exists(path):
        R.verify_fingerprint(json.load(open(path, encoding="utf-8")))
        print(f"{OPEN_MANIFEST}: exists and its fingerprint matches; not rewritten")
        return
    m["fingerprint"] = R.fingerprint(m)
    os.makedirs(OUT, exist_ok=True)
    json.dump(m, open(path, "w", encoding="utf-8", newline="\n"), indent=1)
    print(f"{OPEN_MANIFEST}: {len(m['configs'])} configurations x {len(cells):,} runs at {S} seeds per cell")


def stage_manifest_open_b2():
    """PREREG_PHASE_9_STAGE1_OPEN_B2.md; DECISION_LOG P9-17, P9-18: the second batch (`e9_roster.HEADLINE_OPEN_B2`) on
    exactly the six's cells and seeds.  Its own sizing (`e9_2/sizing_open_b2.json`) gives 19 seeds; the batch runs the
    six's 122 instead, so all nine models are compared on the same market paths (P9-18), and the manifest records both.
    Same subdir as the six: every run lives under its own configuration's directory and ledger."""
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    if not os.path.exists(SIZING_OPEN_B2):
        raise SystemExit(f"{os.path.relpath(SIZING_OPEN_B2, ROOT)} does not exist: run `e9_2_pilot --stages open_b2` first")
    sz = json.load(open(SIZING_OPEN_B2, encoding="utf-8"))
    if not sz.get("complete") or sz.get("roster") != list(RO.HEADLINE_OPEN_B2):
        raise SystemExit("the second batch's sizing is incomplete, or was taken over a roster other than HEADLINE_OPEN_B2")
    six = json.load(open(os.path.join(OUT, OPEN_MANIFEST), encoding="utf-8"))
    seeds = list(six["seeds"])
    cells = cells_for("headline", seeds)
    if cells != six["cells"]:
        raise SystemExit("the headline cells no longer equal the six's manifest: refusing to build the second batch")
    m = {"name": "e9_4_stage1_headline_open_b2", "kind": "grid", "subdir": "stage1_open", "ledger_dir": "e9_4",
         "T": 200, "configs": list(RO.HEADLINE_OPEN_B2), "cells": cells, "seeds": seeds, "seeds_per_cell": len(seeds),
         "sizing": {**{k: sz[k] for k in ("plugin_sigma_d_band_mas", "plugin_model", "alpha_bonferroni", "delta",
                                          "stage1_seeds", "stage1_seeds_rule", "stage1_seeds_appA")},
                    "seeds_run": len(seeds), "seeds_run_rule": "the six's count, so all nine share their market paths "
                                                               "(P9-18)"},
         "registered": "PREREG_PHASE_9_STAGE1_OPEN_B2.md; PREREG_PHASE_9_STAGE1_OPEN.md (cells, analysis); "
                       "DECISION_LOG P9-17, P9-18",
         "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    path = os.path.join(OUT, OPEN_B2_MANIFEST)
    if os.path.exists(path):
        R.verify_fingerprint(json.load(open(path, encoding="utf-8")))
        print(f"{OPEN_B2_MANIFEST}: exists and its fingerprint matches; not rewritten")
        return
    m["fingerprint"] = R.fingerprint(m)
    json.dump(m, open(path, "w", encoding="utf-8", newline="\n"), indent=1)
    print(f"{OPEN_B2_MANIFEST}: {len(m['configs'])} configurations x {len(cells):,} runs at {len(seeds)} seeds per cell")


# ================================================================================================ stage 2 (E2-E5)
def sensitivity_cells(seeds) -> list:
    """E5: the headline's 24 cells at each of the twelve NON-DEFAULT generator levels -- P9-6's data-driven six
    (the GARCH set, sbar, mu_V, the half-life, sigma_V, the jump rate) at two levels each, taken from
    `e9_1_ranking.level_configs()`, which is the code that produced the ranking those six come from.

    The default level is NOT here: P9-21 reads it from the 122 stage-1 seeds already on disk, so the sweep runs only
    what does not exist yet.  Each level is its own `setting`, which `e9_runner.cfg_for` makes a path and run-key
    component, so two levels of one cell cannot collide; the level's GenConfig override rides on the cell as
    `env_config`, which `cfg_for` passes to `SyntheticMarketEnv`.  A cell that ran at the default parameters would
    therefore have a different `Gen_Config_Hash` from the one its level implies, which `stage_verify` checks."""
    from tools.phase9.e9_1_ranking import level_configs
    six = ("garch_set", "sbar", "mu_V", "half_life", "sigma_V", "jump_rate")      # P9-6, e9_1/ranking.json
    lv = {k: v for k, v in level_configs().items() if k != "default" and k.split("__")[0] in six}
    if len(lv) != 2 * len(six):
        raise SystemExit(f"expected {2 * len(six)} non-default levels for the data-driven six, got "
                         f"{len(lv)}: {sorted(lv)}. E9.1's calibration.json must exist for the half-life levels")
    out = []
    for level in sorted(lv):
        for p in PERSONAS:
            for a in HEADLINE_ARMS:
                for sc in SCENARIOS:
                    for s in seeds:
                        out.append({"persona": p, "arm": a, "scenario": sc, "seed": s, "rep": 0,
                                    "setting": f"sens_{level}", "env_config": lv[level]})
    return out


def _write_stage2(kind: str, fname: str, configs, cells, seeds, registered: str) -> None:
    """One stage-2 manifest.  Its own subdir, so its checkpoints and runs never mix with the headline's or another
    stage's; its fingerprint is `e9_runner.fingerprint`, as every other manifest's is, and a manifest already on disk
    is checked rather than rewritten."""
    from tools.phase9 import e9_runner as R
    m = {"name": f"e9_4_stage2_{kind}", "kind": "grid", "subdir": f"stage2_{kind}", "ledger_dir": "e9_4",
         "T": 200, "configs": list(configs), "cells": cells, "seeds": list(seeds), "seeds_per_cell": len(seeds),
         "registered": registered, "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    path = os.path.join(OUT, fname)
    if os.path.exists(path):
        R.verify_fingerprint(json.load(open(path, encoding="utf-8")))
        print(f"{fname}: exists and its fingerprint matches; not rewritten")
        return
    m["fingerprint"] = R.fingerprint(m)
    os.makedirs(OUT, exist_ok=True)
    json.dump(m, open(path, "w", encoding="utf-8", newline="\n"), indent=1)
    settings = sorted({c.get("setting", "default") for c in cells})
    print(f"{fname}: {len(m['configs'])} configurations x {len(cells):,} runs "
          f"({len(settings)} setting(s)) at {len(seeds)} seeds per cell "
          f"= {len(m['configs']) * len(cells):,} runs in all")


def stage_manifest_stage2():
    """E2-E5 on the models HEADLINE_MODEL_SELECTION.md 4.3 assigns, at GRID_EXPERIMENT_PLAN.md 3's own S = 60, on the
    first 60 of the headline's seeds so every cell shares its market paths with the headline runs already on disk."""
    from tools.phase9 import e9_roster as RO
    seeds = list(range(GRID_SEED0, GRID_SEED0 + S_STAGE2))
    sel = "HEADLINE_MODEL_SELECTION.md 4.3 (e9_4/selection)"
    _write_stage2("causal", CAUSAL_MANIFEST, RO.CAUSAL_OPEN, cells_for("causal", seeds), seeds,
                  f"GRID_EXPERIMENT_PLAN.md 3 (E2); {sel}; the core less gpt-oss-20b (R_effect) plus Gemma 4 31B")
    _write_stage2("slice", SLICE_OPEN_MANIFEST, RO.CAUSAL_OPEN, cells_for("slice", seeds), seeds,
                  f"GRID_EXPERIMENT_PLAN.md 3 (E3); {sel}; DECISION_LOG P8-13, P8-14 (D11, the identified design)")
    _write_stage2("track_a", TRACK_A_OPEN_MANIFEST, RO.CORE_OPEN, cells_for("track_a", seeds), seeds,
                  f"GRID_EXPERIMENT_PLAN.md 3 (E4); {sel}; the headline cells at track=A")
    _write_stage2("sens", SENSITIVITY_MANIFEST, RO.CORE_OPEN, sensitivity_cells(seeds), seeds,
                  f"GRID_EXPERIMENT_PLAN.md 3 (E5); {sel}; DECISION_LOG P9-6 (the data-driven six), P9-21 (the "
                  f"default read from the 122 stage-1 seeds, so the twelve non-default levels run)")


def gen_config_collisions(gen_hashes: dict) -> list:
    """Where two settings of one (configuration, scenario, seed) ran the SAME generator configuration.

    `Gen_Config_Hash` is the sha256 of everything the generator was built with, so two sensitivity levels of one cell
    must differ in it.  If they do not, a level's `env_config` never reached the generator and those runs are the
    default's under another name -- the one failure mode `Env_Code_Hash` cannot see, because the CODE is identical and
    only the parameters differ.  A setting that produced more than one hash on one cell is also reported: that means
    the level changed under the runs."""
    out = []
    for (key, scenario, seed), by_setting in sorted(gen_hashes.items()):
        inconsistent = sorted(s for s, h in by_setting.items() if len(h) > 1)
        seen = {}
        for s, h in sorted(by_setting.items()):
            if len(h) == 1:
                seen.setdefault(next(iter(h)), []).append(s)
        shared = {h: ss for h, ss in seen.items() if len(ss) > 1}
        if shared or inconsistent:
            out.append({"config": key, "scenario": scenario, "seed": seed,
                        "settings_sharing_one_gen_config": shared,
                        "settings_with_more_than_one_gen_config": inconsistent})
    return out


def stage_verify():
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    rows, missing = [], []
    for kind, fname in ALL_MANIFESTS.items():
        path = os.path.join(OUT, fname)
        if not os.path.exists(path):
            continue
        m = R.load_manifest(path)
        fp = m["fingerprint"]
        # P9-20/E5: a cell carrying an `env_config` runs a NON-DEFAULT generator.  Env_Code_Hash cannot see that --
        # the code is identical, only the parameters passed to it differ -- so a level that silently ran at the
        # default would verify clean, which would void the whole sweep.  Gen_Config_Hash is the sha256 of the
        # generator's full configuration, so on one (scenario, seed) the settings must map to DISTINCT hashes.
        gen_hashes = {}
        has_env_config = any(c.get("env_config") for c in m["cells"])
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
                want_prompt = fp["prompt_hash"].get(R.prompt_key(key, c))
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
                    # the generator's PARAMETERS, which Env_Code_Hash cannot see: it hashes the code, and an E5 level
                    # that silently ran at the default has identical code and a hash no other setting shares (P9-21
                    # leaves no default level in the manifest), so only the override itself distinguishes them
                    "env_config": (rc.get("env_config") or {}) == (c.get("env_config") or {}),
                    "gen_config_hash_present": bool(prov.get("Gen_Config_Hash")),
                }
                if has_env_config:
                    g = gen_hashes.setdefault((key, c["scenario"], int(c["seed"])), {})
                    g.setdefault(c.get("setting", "default"), set()).add(prov.get("Gen_Config_Hash"))
                if all(checks.values()):
                    n_ok += 1
                else:
                    bad.append({"run_key": R.run_key(c, cfg), "failed": [k for k, v in checks.items() if not v]})
            rows.append({"manifest": kind, "config": key, "planned": len(m["cells"]), "verified": n_ok,
                         "missing": n_missing, "mismatched": len(bad)})
            missing += bad[:20]
            print(f"  {kind:9s} {key:34s} verified {n_ok}/{len(m['cells'])}, missing {n_missing}, mismatched {len(bad)}", flush=True)
        collisions = gen_config_collisions(gen_hashes)
        if collisions:
            for r in rows:
                if r["manifest"] == kind:
                    r["gen_config_collisions"] = sum(1 for c in collisions if c["config"] == r["config"])
            missing += [{"gen_config_collision": c} for c in collisions[:20]]
            print(f"  {kind:9s} GEN_CONFIG COLLISIONS: {len(collisions)} (scenario, seed) groups where two settings "
                  f"ran the SAME generator configuration -- a level did not take effect", flush=True)
    doc = {"registered": "plan 13.4; PREREG_PHASE_9.md 4.1", "rows": rows, "mismatches": missing,
           "pass": bool(rows) and all(r["mismatched"] == 0 and not r.get("gen_config_collisions") for r in rows),
           "complete": bool(rows) and all(r["missing"] == 0 for r in rows),
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    os.makedirs(OUT, exist_ok=True)
    json.dump(doc, open(os.path.join(OUT, "verify.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps({k: doc[k] for k in ("pass", "complete")}, indent=1))
    return 0 if doc["pass"] else 1


def score_rows(m: dict) -> list:
    """One scored row per COMPLETED run of manifest `m` (checkpointed and on disk), scored exactly as the pilots were:
    `evaluation.metrics_v2.score_run(scoring="v2_1")`.  A planned run without a checkpoint contributes nothing; a run
    whose scoring raises is recorded with `score_error` rather than dropped, so the count of scored runs can be read
    against the count planned."""
    from evaluation.metrics_v2 import score_run
    from tools.phase8.e8_5_analyse import metric_names
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    rows = []
    for key in m["configs"]:
        mc = RO.by_key(key)
        done = R.done_keys(m["subdir"], mc, m["cells"])
        for c in m["cells"]:
            cfg = R.cfg_for(mc, c, m["subdir"])
            if R.run_key(c, cfg) not in done:
                continue
            row = {"Manifest": m["name"], "Setting": c.get("setting", "default"), "Model": key, "Persona": cfg.persona,
                   "Arm": cfg.arm, "Scenario": cfg.scenario, "Seed": cfg.seed, "Decode_Replicate": 0, "score_error": ""}
            try:
                sc = score_run(pd.read_csv(R.run_paths(cfg)["csv"]), cfg.persona, scoring="v2_1")
                row.update({k: sc.get(k) for k in metric_names() + ["mdd_pct", "return_pct", "fallback_share", "trade_count"]})
            except Exception as e:                            # noqa: BLE001 -- recorded, not hidden
                row["score_error"] = f"{type(e).__name__}: {str(e)[:160]}"
            rows.append(row)
    return rows


def stage_score():
    """Every completed run of every stage-1 manifest -> e9_4/per_run.csv, with per_run.meta.json carrying the scoring
    file's hash and the scored / planned counts per configuration."""
    from evaluation import scoring_params as SP
    from tools.phase9 import e9_runner as R
    SP.load()
    rows, planned = [], {}
    for kind, fname in ALL_MANIFESTS.items():
        path = os.path.join(OUT, fname)
        if not os.path.exists(path):
            continue
        m = R.load_manifest(path)
        rows += score_rows(m)
        for key in m["configs"]:
            planned[f"{m['name']}|{key}"] = len(m["cells"])
    t = pd.DataFrame(rows)
    os.makedirs(OUT, exist_ok=True)
    t.to_csv(os.path.join(OUT, "per_run.csv"), index=False)
    scored = t.groupby(["Manifest", "Model"]).size().to_dict() if len(t) else {}
    json.dump({"scoring_json_sha256": SP.SHA256, "n_runs_scored": int(len(t)),
               "n_score_errors": int((t["score_error"] != "").sum()) if len(t) else 0,
               "scored_vs_planned": {k: [int(scored.get(tuple(k.split("|", 1)), 0)), v] for k, v in sorted(planned.items())},
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "per_run.meta.json"), "w", encoding="utf-8"), indent=1)
    print(f"scored {len(t)} runs" + (f"; {int((t['score_error'] != '').sum())} scoring errors" if len(t) else ""))
    return 0


def stage_status():
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    for kind, fname in ALL_MANIFESTS.items():
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
        elif st == "manifest_open":
            stage_manifest_open()
        elif st == "manifest_open_b2":
            stage_manifest_open_b2()
        elif st == "manifest_stage2":
            stage_manifest_stage2()
        elif st == "verify":
            rc = stage_verify() or rc
        elif st == "status":
            stage_status()
        elif st == "score":
            rc = stage_score() or rc
        else:
            raise SystemExit(f"unknown stage {st!r}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
