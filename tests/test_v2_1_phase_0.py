"""
Phase 0 (v2.1) fix-locking tests (plan Section 4, item 0.2; PREREG_PHASE_0.md §4, §6, §7):
  * sensitivity-checklist footers equal their CSV counts (item 39);
  * MCR normalisation labels agree with the code (item 53);
  * the day-1 gate runs on common-start cells only; the start-at-target delta-C_1 table is exploratory (item 54);
  * hazard.json cannot silently override the module constants (item 69);
  * the mispricing engine is named honestly; a renamed REJECTED file cannot switch engines (item 70);
  * the trader arm is band-free in the runner as in the metrics (item 73);
  * the analyst block has no sqrt(5) scaling (item 68; the statistical test is in test_v2_1_stats.py);
  * the known-defect registry equals the strict xfails in the suite;
  * the Phase-0 code changes left every non-analyst path column bit-identical (PREREG §7).
"""
import glob
import inspect
import json
import os
import re
import shutil

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "docs", "env_v2", "generated")


# ----------------------------------------------------------------------------------------- item 39
@pytest.mark.parametrize("name", ["checklist_v2"] + [f"checklist_v2_sens_{k}" for k in ("fw_index", "pruna", "hl60", "omega_mode", "panic3", "panic6")])
def test_footer_counts_match_csv(name):
    df = pd.read_csv(os.path.join(GEN, name + ".csv"))
    vals = df["pass"].map(lambda v: None if pd.isna(v) else (str(v) == "True")).tolist()
    n_pass = sum(1 for v in vals if v is True); n_fail = sum(1 for v in vals if v is False); n_na = len(vals) - n_pass - n_fail
    md = open(os.path.join(GEN, name + ".md"), encoding="utf-8").read()
    m = re.search(r"\*\*Pass (\d+) / fail (\d+) / not applicable (\d+)\.\*\*", md)
    assert m, f"{name}.md has no footer"
    assert (int(m.group(1)), int(m.group(2)), int(m.group(3))) == (n_pass, n_fail, n_na), (name, m.groups(), (n_pass, n_fail, n_na))
    # and the table rows agree with the CSV verdicts
    for _, r in df.iterrows():
        want = "PASS" if vals[int(r.name)] is True else ("FAIL" if vals[int(r.name)] is False else "n/a")
        line = [ln for ln in md.splitlines() if ln.startswith(f"| {int(r['item'])} |")]
        assert line and f"| {want} |" in line[0], (name, int(r["item"]), want)


# ----------------------------------------------------------------------------------------- item 53
def test_mcr_normalisation_label():
    from evaluation.metrics_v2 import floors_and_ceilings, HIGHER_BETTER
    doc = inspect.getdoc(floors_and_ceilings)
    assert "constant_mix" in doc and "ceiling" in doc and "mcr" in doc.lower(), doc
    b = {"always_hold": {"mcr_0.05": 0.12, "rg_v1": 60.0}, "random": {"mcr_0.05": 0.30, "rg_v1": 50.0}, "buy_day1_hold": {"mcr_0.05": 0.2, "rg_v1": 90.0},
         "always_buy": {"mcr_0.05": 0.8}, "always_sell": {"mcr_0.05": 0.4}, "constant_mix": {"mcr_0.05": 0.10},
         "mandate_conditional_oracle": {"mcr_0.05": 0.003, "rg_v1": 100.0}}
    fc = floors_and_ceilings(b, "ISFJ")
    assert HIGHER_BETTER["mcr_0.05"] is False
    assert fc["mcr_0.05"]["ceiling"] == 0.10 and fc["mcr_0.05"]["floor"] == 0.8, fc["mcr_0.05"]   # ceiling = constant_mix, floor = worst of the pool
    assert fc["rg_v1"]["ceiling"] == 100.0 and fc["rg_v1"]["floor"] == 90.0
    import tools.report_v2 as rep
    src = inspect.getsource(rep.write_report)
    assert "constant-mix" in src and "mandate-conditional oracle, floor = best trivial policy" not in src


# ----------------------------------------------------------------------------------------- item 54
def _runs(start_design):
    rows = []
    rng = np.random.default_rng(0)
    for p, c in (("ISFJ", 0.8), ("INTJ", 0.5), ("ENTJ", 0.1)):
        for seed in range(4):
            c0 = c if start_design == "target" else 0.5
            for day in (1, 2):
                rows.append({"Model": "m", "Persona": p, "Seed": seed, "Arm": "static", "Decode_Replicate": 0, "Mandate_Block": "none",
                             "Mandate_Persona": p, "Day": day, "Cash_Share": float(np.clip(c + 0.02 * rng.normal(), 0, 1)),
                             "Start_Cash_Share": c0, "Start_Design": start_design, "Parse_Status": "ok", "Target_Cash_Share": c,
                             "obs_price": 100.0, "obs_RSI14": 50.0, "obs_news_sentiment": 0.0})
    return [pd.DataFrame(rows)]


def test_gate_common_start_only():
    from tools.report_v2 import salience_tables
    t = salience_tables(_runs("target"))
    assert "gate_common_start" not in t and not any(k.startswith("gate_") for k in t), list(t)
    assert "exploratory_deltaC1_start_at_target" in t and "note" in t["exploratory_deltaC1_start_at_target"].columns
    c = salience_tables(_runs("common"))
    assert "gate_common_start" in c and "exploratory_deltaC1_start_at_target" not in c


# ----------------------------------------------------------------------------------------- item 69
def test_hazard_loader_is_loud(tmp_path):
    from envs.v2 import generator as g
    from envs.v2 import events as ev
    hz = json.load(open(os.path.join(ROOT, "envs", "v2", "params", "hazard.json"), encoding="utf-8"))
    assert (g.HAZARD_H0, g.HAZARD_B, g.G_MAX_CAL) == (hz["h0"], hz["b"], hz["g_max"])
    assert ev.G_MAX == hz["g_max"]
    # v2.1 Phase 4 introduced a SECOND source for the hazard: events.json's `hazard` block overrides
    # hazard.json for the GenConfig defaults, while the module constants keep carrying the v2 values (the
    # digest probe in test_v2_1_phase_4.py depends on that -- it builds its v2 baseline from HAZARD_H0/B).
    # Assert the override chain explicitly, so neither source can drift unnoticed. This assertion previously
    # read `GenConfig().hazard_h0 == hz["h0"]` and has been failing since Phase 4's main pass; it went unseen
    # because this suite was never run (PHASE_4_REPORT section 9.11).
    try:
        from envs.v2 import events_params as ep
        present = bool(getattr(ep, "PRESENT", False))
    except Exception:
        present = False
    if not present:
        assert g.GenConfig().hazard_h0 == hz["h0"] and g.GenConfig().g_max == hz["g_max"]
    else:
        assert g.GenConfig().hazard_h0 == ep.HAZARD_H0 and g.GenConfig().hazard_b == ep.HAZARD_B, (
            "events.json is present but GenConfig is not honouring its hazard block")
        assert g.GenConfig().g_max == hz["g_max"], "g_max drifted from hazard.json"
    with pytest.raises(RuntimeError):
        g.load_hazard_params(str(tmp_path / "missing.json"))
    bad = tmp_path / "hazard.json"
    bad.write_text(json.dumps({**hz, "h0": hz["h0"] * 2}), encoding="utf-8")
    with pytest.raises(RuntimeError):
        g.load_hazard_params(str(bad))
    assert g.load_hazard_params() == {"h0": hz["h0"], "b": hz["b"], "g_max": hz["g_max"]}


# ----------------------------------------------------------------------------------------- item 70
def test_engine_named_honestly(tmp_path, monkeypatch):
    from envs.v2 import mispricing as mp
    from envs.v2.generator import GenConfig
    from envs.synthetic_market import SyntheticMarketEnv
    from simulation.runner_v2 import RunConfig
    # v2.1 Phase 2: the engine that runs is whatever `envs/v2/params/mispricing.json` names (E2.4's decision,
    # `ar1_fit`); before that file existed it was v2's CAL `fw_fallback_hl150`.  Both are asserted from the
    # source of truth rather than hard-coded, and the LEGACY engine is asserted to be unchanged behind its own
    # name, which is what P2-2 promises.
    from envs.v2 import mispricing_params as MP
    expected = MP.ENGINE if MP.PRESENT else "fw_fallback_hl150"
    assert mp.ENGINE_DEFAULT == expected
    assert GenConfig().engine == mp.ENGINE_DEFAULT and RunConfig().engine == mp.ENGINE_DEFAULT
    p = mp.load_params(mp.ENGINE_DEFAULT)
    assert p.name == expected
    legacy = mp.load_params("fw_fallback_hl150")
    assert legacy.name == "fw_fallback_hl150" and abs(legacy.phi - 0.4632) < 5e-4 and legacy.price_scale == 100.0
    with pytest.raises(FileNotFoundError):
        mp.load_params("fw_single")           # no accepted single-stock estimate exists
    # a renamed REJECTED file must not switch the engine
    monkeypatch.setattr(mp, "PARAM_DIR", str(tmp_path))
    shutil.copy(os.path.join(ROOT, "envs", "v2", "params", "fw_single_stock.REJECTED.json"), tmp_path / "fw_single_stock.json")
    with pytest.raises(ValueError):
        mp.load_params("fw_single")
    d = json.load(open(tmp_path / "fw_single_stock.json", encoding="utf-8")); d["accepted"] = True
    (tmp_path / "fw_single_stock.json").write_text(json.dumps(d), encoding="utf-8")
    assert mp.load_params("fw_single").name == "fw_single_stock"
    monkeypatch.undo()
    md = SyntheticMarketEnv("flat", 20, 1).get_metadata()
    assert md["engine"] == expected and md["engine_used"] == expected and md["fw_params"]["name"] == expected


# ----------------------------------------------------------------------------------------- item 73
def test_trader_band_free(tmp_path):
    from langchain_core.runnables import RunnableLambda
    from experiments.arms_v2 import build_config
    from simulation.runner_v2 import run_simulation_v2
    from evaluation.metrics_v2 import oracle_target
    cfg = build_config("fake", "ISFJ", "trader", "flat", 1, T=5, output_dir=str(tmp_path))
    cfg.agent_llm = RunnableLambda(lambda m: json.dumps({"target_cash_share": 0.4, "rationale": "t"}))
    df = run_simulation_v2(cfg, verbose=False)
    assert df is not None and (df["Band_Lo"] == 0.0).all() and (df["Band_Hi"] == 1.0).all() and (df["Band_Centre"] == 0.5).all()
    assert oracle_target(np.array([-0.2, 0.2]), 0.05, "TRADER", 0.5).tolist() == [0.0, 1.0]


def test_v1_rule_threshold_documented():
    from evaluation import metrics_v2 as m
    assert m.V1_RULE_HOLDINGS_THRESHOLD == 1.0
    assert "V1_RULE_HOLDINGS_THRESHOLD" in inspect.getsource(m.v1_rule)


# ----------------------------------------------------------------------------------------- item 68 (code form)
def test_analyst_block_no_sqrt5():
    from envs.v2 import observables as obs
    src = inspect.getsource(obs.analyst_block)
    assert "sqrt(ANALYST_UPDATE_DAYS)" not in src and "sqrt(5" not in src
    assert obs.ANALYST_SD == 0.15 and obs.ANALYST_RHO == 0.95


# ----------------------------------------------------------------------------------------- registry
def test_known_defect_registry_matches_strict_xfails():
    from tests.known_defects import registry_ids
    found = set()
    for path in glob.glob(os.path.join(ROOT, "tests", "test_*.py")):
        src = open(path, encoding="utf-8").read()
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        for m in re.finditer(r"@pytest\.mark\.xfail\((.*?)\)\s*\ndef (test_\w+)", src, flags=re.S):
            if "strict=True" in m.group(1):
                found.add(f"{rel}::{m.group(2)}")
    assert found == registry_ids(), {"missing_from_registry": found - registry_ids(), "not_in_suite": registry_ids() - found}


# ----------------------------------------------------------------------------------------- PREREG §7
def test_phase0_paths_unchanged():
    from tools.path_hashes import compare
    before = os.path.join(GEN, "v2_1", "path_hashes_before.json"); after = os.path.join(GEN, "v2_1", "path_hashes_after.json")
    if not (os.path.exists(before) and os.path.exists(after)):
        pytest.skip("path-hash fixtures not present")
    r = compare(before, after)
    assert r["changed_non_analyst"] == [], r["changed_non_analyst"][:10]
    assert r["changed_analyst"] > 0      # the declared fix
