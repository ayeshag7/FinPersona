"""
v2.1 Phase 6 regression tests (plan Section 10.4; PREREG_PHASE_6.md section 11).

Each test reads a criterion, a gate or a known answer back from the file that carries it, so that no number in the
audit machinery is stated twice.  The tests that need the derived gates skip until the criteria file carries them
(they are written from the nulls' file by tools/phase6/e6_criteria_extra.py --stages gates); once written they are
asserted as the file holds them, pass or fail (a failing derived gate is the registry's business, not a tolerance).

    python -m pytest tests/test_v2_1_phase_6.py -q
"""
from __future__ import annotations

import glob
import json
import os
import pickle
import re

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
pytestmark = pytest.mark.filterwarnings("ignore")

from evaluation import criteria as CR  # noqa: E402


def _gen(rel):
    p = os.path.join(GEN, rel)
    if not os.path.exists(p):
        pytest.skip(f"{rel} not generated in this working tree")
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _doc():
    if not CR.PRESENT:
        pytest.skip("evaluation/params/phase6_criteria.json absent")
    return CR.load()


# --------------------------------------------------------------------------------- 10.4: the criteria file
def test_checklist_criteria_from_reference():
    """The criteria file carries the reference percentiles WITH their n, every block with provenance and a declared
    status, D0 and p0 as registered, the crash-window rule, and item -> statistics; the loud loader accepts it and
    rejects a file with an empty reference or an undeclared status."""
    doc = _doc()
    assert doc["criterion_B"]["value"]["D0"] == 0.10 and doc["criterion_C"]["value"]["p0"] == 0.80
    assert doc["crash_window_rule"]["value"]["mdd_at_or_below"] == -0.20
    ref = doc["reference"]["value"]
    assert len(ref) >= 20
    for st, blk in ref.items():
        a = blk["all"]
        assert a["n"] > 10000 and a["p10"] <= a["p50"] <= a["p90"], st
        for spn, b in blk["by_sub_period"].items():
            assert b["n"] > 0 and b["p10"] <= b["p50"] <= b["p90"], (st, spn)
    # every item's statistics exist in the reference
    for item, spec in doc["items"].items():
        for st in spec["statistics"]:
            assert st in ref, (item, st)
    # the reference's n and survivorship are recorded
    assert doc["reference"]["n"]["windows"] == ref["kurtosis"]["all"]["n"]
    assert "survivor" in json.dumps(doc["reference"]["survivorship"]).lower()
    # the loud loader rejects an empty reference and an undeclared status
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        bad = json.loads(json.dumps(doc)); bad["reference"]["value"] = {}
        p = os.path.join(td, "a.json"); json.dump(bad, open(p, "w", encoding="utf-8"))
        with pytest.raises(CR.CriteriaError):
            CR.load(p)
        bad = json.loads(json.dumps(doc)); bad["criterion_B"]["status"] = "GUESSED"
        json.dump(bad, open(p, "w", encoding="utf-8"))
        with pytest.raises(CR.CriteriaError):
            CR.load(p)


def test_criteria_match_reference_file():
    """The percentiles in the criteria file equal E6.1's reference.json (the file they cite), to the digit."""
    doc = _doc()
    ref = _gen("e6_1/reference.json")
    rows = {(r["scope"], r["statistic"]): r for r in ref["percentiles"]}
    for st, blk in doc["reference"]["value"].items():
        r = rows[("all", st)]
        assert blk["all"]["n"] == r["n"]
        for k in ("p10", "p50", "p90"):
            assert abs(blk["all"][k] - r[k]) < 1e-12, (st, k)


def test_b_minimum_n_from_size_table():
    """Criterion B's minimum n is the smallest n at which its median pass rate under a true D = 0 is >= 0.90 in E6.2's
    size/power table -- and at n = 200 that rate is far below (the finding of PREREG 5.2)."""
    doc = _doc()
    v = doc["criterion_B"]["value"]
    if "n_min_size" not in v:
        pytest.skip("n_min not written yet")
    tab = {int(k): float(x) for k, x in v["size_pass_rate_at_D0_by_n"].items()}
    assert tab[200] < 0.20
    assert v["n_min_size"] == min(n for n, m in tab.items() if m >= 0.90)


# --------------------------------------------------------------------------------- 10.4: footer counts
@pytest.mark.parametrize("name", [os.path.basename(p)[:-3] for p in glob.glob(os.path.join(GEN, "e6_after_checklist*.md"))] or ["__none__"])
def test_footer_counts(name):
    """Every Phase-6 checklist markdown's footer equals the pass/fail counts of its own csv (v2 form), and the
    reference-criteria markdown's B and C footers equal the per-item table."""
    if name == "__none__":
        pytest.skip("no Phase-6 checklist written yet")
    md = open(os.path.join(GEN, name + ".md"), encoding="utf-8").read()
    csv_p = os.path.join(GEN, name + ".csv")
    if os.path.exists(csv_p):
        df = pd.read_csv(csv_p)
        vals = df["pass"].map(lambda v: None if pd.isna(v) else (str(v) == "True")).tolist()
        n_pass = sum(1 for v in vals if v is True); n_fail = sum(1 for v in vals if v is False)
        m = re.search(r"\*\*Pass (\d+) / fail (\d+) / not applicable (\d+)\.\*\*", md)
        assert m, f"{name}.md has no footer"
        assert (int(m.group(1)), int(m.group(2)), int(m.group(3))) == (n_pass, n_fail, len(vals) - n_pass - n_fail)
    for crit in ("B", "C"):
        m = re.search(r"\*\*" + crit + r": pass (\d+) / fail (\d+) / not applicable (\d+)\.\*\*", md)
        if m:
            items_p = os.path.join(GEN, name + f"_items.csv")
            if os.path.exists(items_p):
                pi = pd.read_csv(items_p)
                assert int(m.group(1)) == int(pi[f"{crit}_pass"].astype(bool).sum())
                assert int(m.group(2)) == int((~pi[f"{crit}_pass"].astype(bool)).sum())


# --------------------------------------------------------------------------------- 10.4: known answers
def test_audit_known_answers():
    """E6.9's convergence verdicts re-read: every closed-form case with a consistent estimator passed at the long
    horizon (Pareto Hill, the AR(1) ACF, GARCH/GJR coefficients, deterministic MDD, the rejection rules' sizes), and
    the two estimator findings -- Hill at a 5 % depth on a Student-t tail, the sample kurtosis of a heavy tail --
    are recorded as failures, not silenced."""
    ka = _gen("e6_9/known_answers.json")
    cases = {c["name"]: c for c in ka["cases"]}
    for name in ("acf_ar1_phi0.6_lag1", "acf_ar1_phi0.9_lag5", "acf_ar1_engine_persistence_lag1", "hill_pareto_alpha3",
                 "garch_persistence", "gjr_gamma", "mdd_deterministic", "ljung_box_size_iid", "arch_lm_size_iid",
                 "jarque_bera_size_normal_recheck", "kurtosis_normal", "skew_normal"):
        assert cases[name]["verdict"]["status"] == "pass", (name, cases[name]["verdict"])
    assert cases["hill_t4"]["verdict"]["status"] == "fail" and cases["hill_t4"]["horizons"]["20000"]["mean"] < 3.5
    assert cases["kurtosis_t5"]["verdict"]["status"] == "fail"
    # the Hill diagnostic: the Pareto control is unbiased at every depth, the t(4) bias closes with depth
    h = ka["hill_frac_sensitivity"]
    assert all(abs(v - 3.0) < 0.06 for v in h["pareto3_control"]["hill"].values())
    assert h["student_t4"]["hill"]["0.05"] < h["student_t4"]["hill"]["0.001"]
    # item 3's rules against the generator's own shape: power well below the 80 % the v2 criterion demands
    assert cases["arch_lm_power_block_in_force"]["horizons"]["200"]["rejection_rate"] < 0.5
    assert cases["lb_abs_r_power_block_in_force"]["horizons"]["200"]["rejection_rate"] < 0.5


# --------------------------------------------------------------------------------- 10.4: no subsampling
@pytest.mark.parametrize("rel", ["e5_after/audit_after_levelfree.pkl"] +
                         [os.path.relpath(p, GEN).replace("\\", "/") for p in glob.glob(os.path.join(GEN, "e6_after", "audit_*.pkl"))])
def test_no_subsampling_in_published_audit(rel):
    """Every published audit ran on every path of the standard evaluation panel."""
    p = os.path.join(GEN, rel)
    if not os.path.exists(p):
        pytest.skip(f"{rel} absent")
    with open(p, "rb") as fh:
        res = pickle.load(fh)
    assert res["subsampled"] is False and res["n_paths"] == 1600 and res["n_paths_input"] == 1600


# --------------------------------------------------------------------------------- 10.4: the derived gates
def test_l2_gate_derived():
    """Each derived gate's margin equals the stored null 95th percentile plus the stored sampling half-width, the
    verdict equals the stored comparison, and the L1 floor equals E6.5's ceiling plus its half-width."""
    doc = _doc()
    gates = doc.get("gates") or {}
    if "l1_floor" in gates:
        g = gates["l1_floor"]["value"]
        assert abs(g["margin_5pct"] - (g["ceiling_5pct"] + g["halfwidth_5pct"])) < 1e-12
        fl = _gen("e6_5/floor.json")
        assert abs(g["ceiling_5pct"] - fl["rule"]["ceiling_5pct"]) < 1e-12
    if not any(k in gates for k in ("l2_all", "l2_calm", "l2b")):
        pytest.skip("the L2/L2b gates are not written yet (the nulls have not run)")
    null = _gen("e6_6/null/null.json")["summary"]
    for name, key in (("l2_all", "x|all"), ("l2_calm", "x|calm"), ("l2b", "macro|all")):
        if name not in gates:
            continue
        v = gates[name]["value"]
        assert abs(v["margin"] - (v["null_p95"] + v["sampling_halfwidth"])) < 1e-12
        assert v["pass"] == (v["measured_selectivity"] <= v["margin"])
        s = null[key]
        assert abs(v["null_p95"] - s["null"]["p95"]) < 1e-12 and abs(v["measured_selectivity"] - s["measured_selectivity"]) < 1e-12
        assert v["null_n_draws"] >= 20, "the 95th percentile needs at least 20 draws (the resolution note)"


def test_audit_switches_inert():
    """With the defaults, run_audit's output on the CI panel is field-for-field what it was before Phase 6; the
    switches only add keys.  Uses the tests' own 8-seed panel (tests/test_leakage_ci.py's construction)."""
    from evaluation.leakage_audit import run_audit
    from envs.synthetic_market import audit_panel
    from agent.render import rendered_market_fields
    from tools.phase5.common import encode_nm
    panel = encode_nm(audit_panel(seeds=2, T=120, seed0=30000))
    shown = [f for f in rendered_market_fields("v2") if f in panel.columns] + (["reported_PE_nm"] if "reported_PE_nm" in panel else [])
    base = run_audit(panel, shown, max_rows=None, n_boot=20)
    again = run_audit(panel, shown, max_rows=None, n_boot=20, gates="derived")
    assert "gates" not in base and "derived" not in base and "L2_holdout" not in base
    for k in ("L1", "L2", "L4"):
        pd.testing.assert_frame_equal(base[k], again[k])
    assert base["L2_verdict"] == again["L2_verdict"] and base["L2b"] == again["L2b"]
    assert again["gates"] == "derived" and "derived" in again


def test_reference_stats_is_the_reference_estimator():
    """The estimator behind the reference criteria is byte-identical to the one that produced E6.1's windows:
    re-running it on one stored real window reproduces the stored row."""
    from evaluation.reference_stats import window_stats
    from tools.phase1.panel import DEFAULT as SPEC
    w = os.path.join(GEN, "e6_1", "windows.csv")
    if not os.path.exists(w):
        pytest.skip("e6_1/windows.csv absent")
    df = pd.read_csv(w)
    row = df.iloc[0]
    p = SPEC.path(SPEC.price_dir, f"{row['ticker']}.parquet")
    if not os.path.exists(p):
        pytest.skip("datasets/ not on this machine")
    d = pd.read_parquet(p, columns=["Date", "Adj Close", "Volume"])
    d = d[(d["Date"] >= SPEC.start) & (d["Date"] <= SPEC.end)].reset_index(drop=True)
    d = d[np.isfinite(d["Adj Close"]) & (d["Adj Close"] > 0)].reset_index(drop=True)
    seg = d.iloc[0:201]
    s = window_stats(seg["Adj Close"].to_numpy(float), seg["Volume"].to_numpy(float))
    for k in ("kurtosis", "hill", "acf1_absr", "mdd", "daily_sigma", "garch_persistence", "volume_absr_spearman"):
        assert abs(float(s[k]) - float(row[k])) < 1e-9, k


def test_phase6_report_tables_match_files():
    """Every marked table block in PHASE_6_REPORT.md equals what its file generates now (rule 13: the report can
    never go stale without this test failing)."""
    from tools.phase6.e6_report_tables import REPORT, render
    if not os.path.exists(REPORT):
        pytest.skip("PHASE_6_REPORT.md absent")
    with open(REPORT, "r", encoding="utf-8") as fh:
        text = fh.read()
    _, status = render(text)
    stale = [k for k, v in status.items() if v == "updated"]
    assert not stale, f"stale report blocks: {stale} (run python -m tools.phase6.e6_report_tables)"
    assert any(v == "unchanged" for v in status.values()), status


def test_known_defect_registry_names_derived_gates():
    """The registry's Phase-6 entries (if any remain) name a derived gate, never a chosen margin."""
    from tests.known_defects import V2_DEFECTS
    for d in V2_DEFECTS:
        if d["phase"] >= 6:
            assert "derived" in d["reason"].lower() or "null" in d["reason"].lower(), d
