"""
v2.1 Phase 5 regression tests (plan Section 9.4; PREREG_PHASE_5.md section 11).

Each test locks a decision Phase 5 took on evidence, or a property every design must have.  The seed counts are the
pre-registration's, and every tolerance traces to a generated file or to a plan number rather than to a preference.

    python -m pytest tests/test_v2_1_phase_5.py -q
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
PARAMS = os.path.join(ROOT, "envs", "v2", "params")
pytestmark = pytest.mark.filterwarnings("ignore")

from envs.v2 import observables_params as OP          # noqa: E402
from envs.v2 import observables as obs                 # noqa: E402


def _gen(name):
    p = os.path.join(GEN, name)
    if not os.path.exists(p):
        pytest.skip(f"{name} not generated in this working tree")
    return json.load(open(p, encoding="utf-8"))


# --------------------------------------------------------------------------- Section 9.4 tests

def test_observable_params_provenance():
    """Every constant is read from params/observables.json with a source field; the loader is loud."""
    assert OP.PRESENT, "envs/v2/params/observables.json is absent; run python -m tools.phase5.apply_e5"
    for key in OP.REQUIRED:
        prov = OP.provenance(key)
        assert prov, f"{key} has no provenance block"
        for f in ("label", "source", "date", "interval", "n", "status"):
            assert f in prov, f"{key} is missing {f}"
        assert prov["interval"] is not None, f"{key} ships interval=None"
    d = json.load(open(OP.OBSERVABLES_PATH, encoding="utf-8"))
    declared = set(d["_status_key"])
    used = {k: v["status"] for k, v in d.items() if isinstance(v, dict) and "status" in v}
    assert used and set(used.values()) <= declared, f"undeclared statuses: {used}"
    # the constants in force equal the file (the loud-loader contract), section by section
    p = OP.in_force()
    for s in OP.SECTIONS:
        for k, v in d[s]["value"].items():
            assert p[s][k] == v, (s, k)
    # and the guard fires: a missing entry, a null interval, an undeclared status
    with tempfile.TemporaryDirectory() as td:
        bad = dict(d); bad.pop("volume")
        q = os.path.join(td, "a.json"); json.dump(bad, open(q, "w", encoding="utf-8"))
        with pytest.raises(RuntimeError):
            OP.load(q)
        bad = json.loads(json.dumps(d)); bad["eps"]["interval"] = None
        json.dump(bad, open(q, "w", encoding="utf-8"))
        with pytest.raises(RuntimeError, match="null"):
            OP.load(q)
        bad = json.loads(json.dumps(d)); bad["eps"]["status"] = "NOT A DECLARED TERM"
        json.dump(bad, open(q, "w", encoding="utf-8"))
        with pytest.raises(RuntimeError, match="does not declare"):
            OP.load(q)


def test_observables_switches_preserve_v2():
    """Every block reproduces the committed HEAD functions exactly with params=None (observables.py is under the
    freeze manifest; the switch must be provably inert when off), on 50 random inputs, and obs_mode='v2' makes the
    environment ignore the parameter file."""
    src = subprocess.run(["git", "show", "HEAD:envs/v2/observables.py"], cwd=ROOT, capture_output=True, text=True)
    if src.returncode != 0:
        pytest.skip("git not available or file not in HEAD")
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as fh:
        fh.write(src.stdout); path = fh.name
    spec = importlib.util.spec_from_file_location("obs_head", path)
    head = importlib.util.module_from_spec(spec); spec.loader.exec_module(head)
    day = np.arange(-750, 201); L = len(day)
    # the committed file may itself be the Phase-5 one (after the commit): then it must accept params=None
    head_takes_params = "params" in head.earnings_block.__code__.co_varnames
    for seed in range(50):
        rng = np.random.default_rng(seed)
        V = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, L))); x = np.cumsum(rng.normal(0, 0.01, L)) * 0.3
        P = V * np.exp(x); r = np.concatenate([[0.0], np.diff(np.log(P))]); q = int(rng.integers(0, 63))
        kw = {"params": None} if head_takes_params else {}
        a1 = head.announcement_schedule(day, np.random.default_rng(seed), q_phase=q, **kw)
        a2 = obs.announcement_schedule(day, np.random.default_rng(seed), q_phase=q, params=None)
        assert a1 == a2, seed
        e1 = head.earnings_block(day, V, P, np.random.default_rng(seed), np.random.default_rng(seed + 1), np.random.default_rng(seed + 2), ann=a1, q_phase=q, **kw)
        e2 = obs.earnings_block(day, V, P, np.random.default_rng(seed), np.random.default_rng(seed + 1), np.random.default_rng(seed + 2), ann=a1, q_phase=q, params=None)
        for k in e1:
            assert np.array_equal(e1[k], e2[k], equal_nan=True), (seed, k)
        b1 = head.analyst_block(day, V, np.random.default_rng(seed), **kw); b2 = obs.analyst_block(day, V, np.random.default_rng(seed), params=None)
        assert all(np.array_equal(b1[k], b2[k]) for k in b1), seed
        v1 = head.volume_block(day, r, x, np.random.default_rng(seed), lag=3, **kw); v2 = obs.volume_block(day, r, x, np.random.default_rng(seed), lag=3, params=None)
        assert all(np.array_equal(v1[k], v2[k]) for k in v1), seed
        s1 = head.SentimentState(np.random.default_rng(seed), lag=2, **kw); s2 = obs.SentimentState(np.random.default_rng(seed), lag=2, params=None)
        for i in range(L):
            assert s1.step(x[i], np.log(P[i] / P[max(i - 20, 0)]), r[i]) == s2.step(x[i], np.log(P[i] / P[max(i - 20, 0)]), r[i]), (seed, i)
    os.unlink(path)
    from envs.synthetic_market import SyntheticMarketEnv
    e_v2 = SyntheticMarketEnv("crash", 120, 7, config={"obs_mode": "v2"})
    assert e_v2.get_metadata()["observables"] == "v2"
    assert int(e_v2.data["pe_nm"].sum()) == 0 and abs(e_v2.data["hidden_multiple"].iloc[0] - np.clip(e_v2.data["hidden_multiple"].iloc[0], 14, 22)) < 1e-12


def test_sentiment_level_free():
    """s_t is bit-identical when P and V are both scaled by a constant (every design), and when P alone is scaled
    (designs A and C: returns-only; x does not enter)."""
    p = OP.in_force()
    if p["sentiment"].get("design", "v2") == "v2":
        pytest.skip("the sentiment in force is the v2 construction (reads x); Phase 5 not applied")
    L = 400
    for seed in range(10):
        rng = np.random.default_rng(seed)
        V = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, L))); x = np.cumsum(rng.normal(0, 0.01, L)) * 0.3
        P = V * np.exp(x); r = np.concatenate([[0.0], np.diff(np.log(P))])
        for c in (0.1, 3.7):
            out = []
            for scale_P, scale_V in ((1.0, 1.0), (c, c), (c, 1.0)):
                Ps, Vs = P * scale_P, V * scale_V
                xs = np.log(Ps / Vs)
                st = obs.SentimentState(np.random.default_rng(seed), lag=2, params=p)
                out.append([st.step(xs[i], np.log(Ps[i] / Ps[max(i - 20, 0)]), r[i]) for i in range(L)])
            assert out[0] == out[1], "a common level shift of P and V changed the sentiment"
            if p["sentiment"]["design"] in ("A", "C"):
                assert out[0] == out[2], "design A/C sentiment must not depend on x"


def test_eps_lag_distribution():
    """The announcement lags the generator draws (500 seeds) lie inside the FIT grid's range and their median is nearer
    the panel's P50 than the grid midpoint (the Phase-4 sampler test)."""
    p = OP.in_force()
    if p["eps"].get("design", "v2") == "v2":
        pytest.skip("Phase 5 not applied")
    grid = np.asarray(p["eps"]["lag_grid_td"], float)
    day = np.arange(-750, 201)
    from envs.v2.rng import Streams
    lags = []
    for seed in range(500):
        ann = obs.announcement_schedule(day, Streams(600000 + seed, 0).get("announce", 0), q_phase=int(seed % 63), params=p)
        lags += [a - q for q, a in ann.items()]
    lags = np.asarray(lags, float)
    assert lags.min() >= grid.min() - 0.5 and lags.max() <= grid.max() + 0.5, (lags.min(), lags.max())
    p50 = p["eps"]["lag_p10_p50_p90_td"][1]
    mid = 0.5 * (grid.min() + grid.max())
    if abs(p50 - mid) > 1.0:
        assert abs(np.median(lags) - p50) < abs(np.median(lags) - mid), "the lag is being drawn uniformly, not from the FIT grid"


def test_no_field_is_deterministic_in_x():
    """The stored FINAL ablation: every group's add-one R2(x) gain over the level-free base (all rows) is at or below
    the PROVISIONAL bound written in observables.json (0.20, amendment A8's reference value; Phase 6 derives the margin
    that replaces it); plus a live guard on an 8-seed panel that no single rendered field alone reaches R2(x) >= 0.90."""
    if not OP.PRESENT:
        pytest.skip("Phase 5 not applied")
    bound = float(OP.AUDIT_BOUNDS["no_field_deterministic_R2"])
    fin = _gen("e5_7a/final/ablation.json")
    tab = fin["tables"]["x|all"]
    worst = max((v["add_one"]["delta"], g) for g, v in tab["groups"].items() if v.get("add_one"))
    assert worst[0] <= bound, f"group {worst[1]} adds {worst[0]:.4f} R2(x) on all rows, above the provisional bound {bound}"
    from envs.synthetic_market import audit_panel
    from sklearn.linear_model import Ridge
    panel = audit_panel(8, 200, seed0=30000)
    y = panel["x"].to_numpy(float)
    for f in [c for c in panel.columns if c not in ("scenario", "seed", "day", "phase", "V", "P", "macro", "x")]:
        v = panel[f].to_numpy(float)
        ok = np.isfinite(v)
        if ok.sum() < 100 or v[ok].std() == 0:
            continue
        X = np.column_stack([v[ok], np.log(np.abs(v[ok]) + 1e-9)])
        pred = Ridge(alpha=1e-6).fit(X, y[ok]).predict(X)
        r2 = 1 - ((y[ok] - pred) ** 2).sum() / ((y[ok] - y[ok].mean()) ** 2).sum()
        assert r2 < 0.90, f"field {f} alone reproduces x with R2 {r2:.3f}: a deterministic function of the hidden state"


def test_onset_audit_bound():
    """The stored final onset audit: no NON-PRICE (field, transition) exceeds the circular-shift null's 95th percentile
    against the price-derived reference (PREREG_PHASE_5_ADDENDUM.md section 1.3: the technical fields are functions of
    the price path and sit on the reference side; the verdict as registered is kept in the file for the record and its
    failures must all be price-derived fields); and the audit's own machinery still computes on a tiny live sample."""
    res = _gen("e5_7c/final/onset.json")
    assert res["verdict_nonprice"]["all_pass"], res["verdict_nonprice"]["failures"]
    # every failure under the rule AS REGISTERED is either a price-derived field (on the reference side under the addendum)
    # or a non-price field that passes against the price-derived reference: nothing fails the corrected rule
    for t, f in res["verdict"]["failures"]:
        fd = res["transitions"][t]["fields"][f]
        assert fd.get("pass_nonprice_rule") in (True, None), (t, f, fd)
    for k, t in res["transitions"].items():
        if t.get("skipped"):
            continue
        assert t["n_pos_days"] > 0 and t["n_neg_days"] > 0
        for f, v in t["fields"].items():
            assert v["null_n"] >= 100, (k, f)
    from tools.phase5.e5_7c_onset import _path, auc_rank
    r = _path(("crash", 410000, {}))
    assert "deterioration->panic" in r["labs"] and any(np.isfinite(v).any() for v in r["scores"].values())


def test_nm_rendering_and_audit_encoding():
    """An undefined P/E is rendered as the string 'n/m' (the observation dict value), never as a number, and the
    hidden `pe_nm` indicator marks exactly those days; the audit encodes it as the cap plus an indicator."""
    p = OP.in_force()
    if p["eps"].get("design", "v2") == "v2":
        pytest.skip("Phase 5 not applied")
    from envs.synthetic_market import SyntheticMarketEnv
    from evaluation.leakage_audit import panel_from_env
    from tools.phase5.common import encode_nm
    found = False
    for seed in range(700000, 700040):
        env = SyntheticMarketEnv("flat", 200, seed)
        d = env.data
        if d["pe_nm"].sum() == 0:
            continue
        found = True
        env.reset()
        for t in range(200):
            o = env.get_observation()
            if bool(d["pe_nm"].iloc[t]):
                assert o["reported_PE"] == "n/m"
            else:
                assert isinstance(o["reported_PE"], float) and np.isfinite(o["reported_PE"])
            env.step()
        pan = encode_nm(panel_from_env(env, "flat", seed))
        assert "reported_PE_nm" in pan and pan["reported_PE_nm"].sum() == d["pe_nm"].sum()
        assert np.isfinite(pan["reported_PE"]).all()
        break
    assert found, "no n/m day in 40 flat seeds; the loss process is not producing undefined P/E at all"


def test_hidden_field_switches():
    """D10 'hidden' and analyst design B omit the key from the observation (not None), and the hidden path is unchanged."""
    from envs.synthetic_market import SyntheticMarketEnv
    base = SyntheticMarketEnv("flat", 60, 3)
    p = OP.in_force()
    if p["dividend"].get("design", "v2") == "v2":
        pytest.skip("Phase 5 not applied")
    e = SyntheticMarketEnv("flat", 60, 3, config={"obs_overrides": {"dividend": {"field": "hidden"}, "analyst": {"design": "B", "field": "hidden"}}})
    o = e.get_observation()
    assert "dividend_yield" not in o and "analyst_fair_value" not in o
    np.testing.assert_allclose(e.data["price"].to_numpy(), base.data["price"].to_numpy())


def test_phase5_report_parameter_table_matches_observables_json():
    """The report's parameter table equals the deployed file's statuses (the P4-47 pattern)."""
    import re
    rep = os.path.join(ROOT, "docs", "env_v2", "v2_1", "PHASE_5_REPORT.md")
    if not (os.path.exists(rep) and OP.PRESENT):
        pytest.skip("Phase-5 report or observables.json absent")
    d = json.load(open(OP.OBSERVABLES_PATH, encoding="utf-8"))
    text = open(rep, encoding="utf-8").read()
    entries = {k: v["status"] for k, v in d.items() if isinstance(v, dict) and "status" in v}
    missing, wrong = [], []
    for key, status in entries.items():
        m = re.search(r"\|\s*`%s`\s*\|\s*\*{0,2}([^|*]+?)\*{0,2}\s*\|" % re.escape(key), text)
        if m is None:
            missing.append(key)
        elif m.group(1).strip() != status:
            wrong.append((key, status, m.group(1).strip()))
    assert not missing, f"observables.json entries absent from the report's parameter table: {missing}"
    assert not wrong, "the report's parameter table disagrees with the deployed observables.json (entry, file, report): " + repr(wrong)
