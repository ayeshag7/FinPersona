"""
v2.1 Phase 4 regression tests (plan Section 8.4).

Each test locks a decision that Phase 4 took on evidence, or records one it deliberately did NOT take.  The
seed counts are the ones the pre-registration states, and every tolerance traces to a generated file rather
than to a preference.

    python -m pytest tests/test_v2_1_phase_4.py -q
"""
from __future__ import annotations

import json
import os

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")

from envs.v2 import events_params as EP                       # noqa: E402
from envs.v2.schedule import draw_schedule, _spec             # noqa: E402
from envs.synthetic_market import SyntheticMarketEnv          # noqa: E402


def _gen(name):
    p = os.path.join(GEN, name)
    if not os.path.exists(p):
        pytest.skip(f"{name} not generated in this working tree")
    return json.load(open(p, encoding="utf-8"))


# --------------------------------------------------------------------------- Section 8.4 tests

def test_events_params_present_and_provenanced():
    """The parameter file exists once Phase 4 is applied, and every required entry carries provenance.

    The loader itself raises on a null interval; this test asserts the file is actually in force, so an
    absent events.json cannot persist past the hand-over."""
    assert EP.PRESENT, "envs/v2/params/events.json is absent; run python -m tools.phase4.apply_e4"
    for key in EP.REQUIRED:
        prov = EP.provenance(key)
        assert prov, f"{key} has no provenance block"
        for field in ("label", "source", "date", "interval", "n"):
            assert field in prov, f"{key} is missing {field}"
        assert prov["interval"] is not None, f"{key} ships interval=None"


def test_schedule_ranges_from_params():
    """Draws land inside the FIT ranges the parameter file records (plan 8.4)."""
    e41 = _gen("e4_1/episodes4.json")
    q = e41["panel_families"]["dd30_fast"]["quantiles"]
    rng = np.random.default_rng(4040)
    det, pan, fl = [], [], []
    for _ in range(300):
        s = draw_schedule("crash", 200, rng, schedule_mode="v21")
        if not s.truncated:                       # truncation by T is allowed to push below the P10
            det.append(s.det_len)
            pan.append(s.panic_len)
        fl.append(s.front_load)
    for vals, key, is_int in ((det, "det_len", True), (pan, "panic_len", True),
                              (fl, "front_load", False)):
        lo, hi = q[key]["p10"], q[key]["p90"]
        tol = 0.5 + 1e-9 if is_int else 1e-9      # integer parameters round to the nearest day
        assert min(vals) >= lo - tol, f"{key} drew {min(vals)} below the FIT P10 {lo}"
        assert max(vals) <= hi + tol, f"{key} drew {max(vals)} above the FIT P90 {hi}"
    # and the shape is the EMPIRICAL one, not a uniform: the median must sit near the panel's, not near
    # the midpoint of the interval (PREREG_PHASE_4_ADDENDUM section 3)
    lo, hi = q["panic_len"]["p10"], q["panic_len"]["p90"]
    assert abs(np.median(pan) - q["panic_len"]["p50"]) < abs(np.median(pan) - 0.5 * (lo + hi)), \
        "panic_len is being drawn uniformly over [P10, P90] rather than from the empirical distribution"


def test_hazard_params_provenance():
    """The hazard entry names the rule that chose it AND records that the adoption was withdrawn.

    E4.3 adopted mapping A on a topped share measured before events.json existed; on the deployed state the
    share is 0.008 and E4.12 showed window-matched that the criterion is dominated by remaining horizon
    (P4-21). The entry must be INCUMBENT and carry the withdrawal, not read as an adopted result."""
    prov = EP.provenance("hazard")
    # The status word was INCUMBENT until P4-39 showed that term's declared meaning ("the v2 behaviour
    # stays") contradicted the value in force -- E4.3's fit, not v2's hazard.  The assertion is on the
    # INTENT, which is unchanged: not adopted, and the withdrawal recorded.
    assert prov["status"] in ("INCUMBENT", "IN FORCE, ADOPTION WITHDRAWN"),         f"the hazard entry reads {prov['status']!r}; it must not claim to be ADOPTED"
    assert prov.get("adoption_withdrawn")
    e49 = _gen("e4_9/deployed.json")
    assert e49["as_calibrated_vs_deployed"]["hazard_topped_share"]["inside_panel_ci_deployed"] is False
    assert _gen("e4_12/horizon.json")["verdict"]["conclusion"].startswith("HORIZON")
    assert EP.HAZARD_MAPPING == "A_no_scaling"
    assert "REG-18" in prov["label"]
    assert "GSY" in prov["label"] or "Greenwood" in prov["label"]
    e43 = _gen("e4_3/hazard.json")
    arm = e43["arms"]["A_no_scaling"]
    assert abs(EP.HAZARD_H0 - arm["h0"]) < 1e-12
    assert abs(EP.HAZARD_B - arm["b"]) < 1e-9
    # the retired bands must be recorded as RETIRED outcomes, not as tolerances the arm was selected against
    assert "RETIRED" in prov["outcome_not_target"]
    assert e43["decision"]["rule"].startswith("REG-18"),         "the adoption rule recorded in the evidence file is not REG-18's"
    assert "40-60" not in json.dumps(e43["decision"]),         "the retired topped-share band appears in the DECISION block, i.e. it was used to choose"


def test_blowoff_label_reaches_the_driver():
    """E4.8: a label assigned EX POST cannot drive the variance. Under the dynamic criterion it must.

    This is the direct regression for the defect Phase 3 measured (the blow-off multiplier has been dead code
    since v2)."""
    assert EP.BLOWOFF_MODE == "dynamic"
    assert EP.BLOWOFF_G_THRESHOLD is not None and EP.BLOWOFF_G_THRESHOLD > 0
    seen = 0
    for seed in range(9100, 9120):
        env = SyntheticMarketEnv("bull_trap", 200, seed)
        ph = set(env.data[env.data["asset"] == 0]["phase"].tolist())
        if "blow-off" in ph:
            seen += 1
            # the label must be present on the path the DRIVER produced, not added afterwards
            assert env.event_meta.get("blowoff_days", 0) > 0, \
                "blow-off days appear in the phase column but the driver never counted them -- the label is " \
                "still being assigned ex post"
    assert seen >= 15, f"only {seen}/20 bull-trap paths carry a blow-off phase"


def test_post_top_leg_is_not_drift_dominated():
    """E4.8/E4.11: the v2 linear reversal leg floors the realised variance ratio at 1.59 (Phase 3, n = 20).

    The half-life in force must be the one adopted ON THE DEPLOYED STATE. E4.8's first search ran before
    events.json existed and its half-life of 50 does not reproduce there (P4-19, P4-20)."""
    assert EP.POST_TOP_MODE == "decay" and EP.POST_TOP_HALF_LIFE
    e411 = _gen("e4_11/posttop_recal.json")
    adopted = e411["decision"]["adopted"]
    assert adopted, "E4.11 adopted no arm"
    arm = e411["arms"][adopted]
    assert abs(EP.POST_TOP_HALF_LIFE - arm["half_life"]) < 1e-9,         f"the half-life in force ({EP.POST_TOP_HALF_LIFE}) is not the one E4.11 adopted ({arm['half_life']})"
    assert arm["ratio_inside_panel_ci"], "the adopted arm is not inside the panel CI it was chosen by"
    assert arm["post_top_over_mania"] < 1.0, "the leg is still drift-dominated"
    # every arm tested must beat Phase 3's measured floor of 1.59 -- that is the defect being closed
    assert max(v["post_top_over_mania"] for v in e411["arms"].values()) < 1.59


def test_top_day_recorded_at_the_realised_peak():
    """E4.8: the top day is recorded at the realised price peak as well as at the hazard firing, and the
    off-by-one is measurable rather than asserted."""
    offs = []
    for seed in range(9200, 9240):
        env = SyntheticMarketEnv("bull_trap", 200, seed)
        m = env.event_meta
        if m.get("topped") and m.get("top_day_realised") is not None:
            offs.append(m["top_day_offset"])
            d = env.data[env.data["asset"] == 0]
            p = d["price"].to_numpy(float)
            day = d["day"].to_numpy(int)
            i = int(np.argmax(day == m["top_day_realised"]))
            lo = int(np.argmax(day >= env.schedule.event_start))
            assert p[i] >= p[lo:i + 1].max() - 1e-9, "top_day_realised is not the realised maximum"
    assert offs, "no topped path produced a realised top day"


def test_no_x_selection_in_control():
    """Accepted and rejected control paths must have the same x distribution -- weakness items 18 and 42.

    Under definitions A, B and D there is no x-band at all, so this holds by construction; under the INCUMBENT
    definition C it does not, and this test records that as the reason D14 is open rather than passing."""
    e45 = _gen("e4_5/control.json")
    a = e45["definitions"]["A"]["ii_selection"]
    c = e45["definitions"]["C"]["ii_selection"]
    assert a["sd_r"]["ks"] < c["sd_r"]["ks"], \
        "definition A should select less on volatility than the anchored definition C"
    # C's selection is severe and is the substantive finding
    assert c["sd_r"]["ks"] > 0.25, "definition C's measured selection on daily sd has changed materially"
    # the registered equivalence bound is not attainable at these rejection counts; the test records that
    assert a["null_floor"]["attainable"] is False


def test_sustained_bull_selection():
    """Known-defect registry items 18 and 42, inherited from Phase 3 as a strict xfail.

    Phase 4 was to end this phase either PASSING or re-registered with a new owner and reason. It is
    re-registered: the measurement that would close it is done (E4.5 audits all four definitions and shows
    A/B/D remove the selection entirely), but ADOPTING one of them is D14, which the team has not taken and
    which the pre-registration forbids Phase 4 from taking for it."""
    assert EP.CONTROL_DEF in ("A", "B", "D"), \
        "the control still runs the anchored definition C, whose x-band selects on the hidden state"


def test_script_share_reported():
    """The event-phase script share is computed and stored, and it is measured from the RECORDED drift."""
    e46 = _gen("e4_6/dynamics.json")
    for name, arm in e46["arms"].items():
        assert arm.get("script_share_median") is not None, f"{name} has no script share"
    env = SyntheticMarketEnv("crash", 200, 9301, crash_discount=0.70)
    assert hasattr(env.result, "drift"), "PathResult does not record the scripted drift"
    assert float(np.abs(env.result.drift).sum()) > 0, "the recorded drift is identically zero on a crash path"


def test_day_index_rendering_option():
    """REG-9 / D6: three renderings behind a switch, and the renderer honours the chosen one."""
    obs = {}
    for mode in ("day_n", "none", "date"):
        env = SyntheticMarketEnv("flat", 200, 9400, day_index_mode=mode)
        obs[mode] = env.get_observation()
    assert obs["day_n"]["date"].startswith("Day-")
    assert "date" not in obs["none"], "day_index_mode='none' must omit the key, not render None"
    assert obs["date"]["date"][:4].isdigit(), "day_index_mode='date' should render a calendar date"
    # the excluded crash windows of REG-9
    year = int(obs["date"]["date"][:4])
    for lo, hi in SyntheticMarketEnv.EXCLUDED_YEARS:
        assert not (lo <= year < hi), f"a random start date landed in the excluded window {lo}-{hi}"
    assert EP.DAY_INDEX_MODE == "day_n", "D6 keeps Day-N as the default"


def test_arm_grid_has_ordering_factor():
    """E4.7a: the ordering factor is in the arm grid (it was supported by the runner but never varied)."""
    from experiments.arms_v2 import FACTOR_DEFAULTS, ORDERINGS, build_config, expand_grid
    assert "ordering" in FACTOR_DEFAULTS
    assert set(ORDERINGS) == {"setup_first", "event_first", "phase_free"}
    for o in ORDERINGS:
        cfg = build_config("m", "ISFJ", "static", "crash", 1, factors={"ordering": o})
        assert cfg.ordering == o
    grid = expand_grid(["m"], ["ISFJ"], ["static"], ["crash"], [1], 1, (0.70,),
                       {"ordering": "event_first"})
    assert all(c.ordering == "event_first" for c in grid)


def test_all_four_switches_together_reproduce_v2():
    """P4-17, corrected: `schedule_mode="v2"` reproduces the SCHEDULE, not the whole v2 generator.

    Once events.json exists the hazard, the blow-off criterion and the post-top leg are separate switches, so
    reproducing v2 needs all four. Measured on bull-trap seeds chosen to actually top with a real post-top
    window, so the leg is exercised -- the 12-path probe used during development did not exercise it (its one
    topping seed tops on day 200) and would have shown a false invariance."""
    import hashlib
    from envs.v2.generator import HAZARD_H0, HAZARD_B
    # seeds chosen under v2_all itself: the v2 hazard is weaker than events.json's, so seeds picked under the
    # deployed hazard do not all top here -- which is what the assertion at the end of this test caught.
    seeds = [9518, 9528, 9578, 9608, 9627]
    v2_all = {"schedule_mode": "v2", "blowoff_mode": "ex_post", "post_top_mode": "v2_linear",
              "hazard_h0": HAZARD_H0, "hazard_b": HAZARD_B}
    def digest(cfg):
        h = hashlib.sha256()
        for s in seeds:
            e = SyntheticMarketEnv("bull_trap", 200, s, config=cfg)
            h.update(np.ascontiguousarray(
                e.data[e.data["asset"] == 0]["price"].to_numpy(float)).tobytes())
        return h.hexdigest()
    assert digest(v2_all) != digest({"schedule_mode": "v2"}), (
        "schedule_mode='v2' alone appears to reproduce the whole generator; if that is now true the other "
        "switches have stopped taking effect and this test's premise needs re-checking")
    # the tops must be real, or the probe proves nothing
    tops = [SyntheticMarketEnv("bull_trap", 200, s, config=v2_all).event_meta for s in seeds]
    assert all(t.get("topped") and t.get("top_day") and t["top_day"] < 170 for t in tops),         "the probe seeds no longer top with a post-top window; pick new ones before trusting this test"


def test_quarter_phase_switch_preserves_v2():
    """E4.7d: the per-seed quarter-grid shift must reproduce v2 exactly at q_phase = 0.

    `envs/v2/observables.py` is under the freeze manifest, so the switch has to be provably inert when off.
    Compared against the committed version of the two functions, on 20 random inputs."""
    import importlib.util
    import subprocess
    import tempfile
    import envs.v2.observables as new
    src = subprocess.run(["git", "show", "HEAD:envs/v2/observables.py"], cwd=ROOT,
                         capture_output=True, text=True)
    if src.returncode != 0:
        pytest.skip("git not available or file not in HEAD")
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as fh:
        fh.write(src.stdout)
        path = fh.name
    spec = importlib.util.spec_from_file_location("obs_head", path)
    head = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(head)
    day = np.arange(-260, 201)
    for seed in range(20):
        a_ = head.announcement_schedule(day, np.random.default_rng(seed))
        b_ = new.announcement_schedule(day, np.random.default_rng(seed), q_phase=0)
        assert a_ == b_, f"q_phase=0 changed the announcement schedule at seed {seed}"
    # and the switch must actually do something when it is on
    assert (new.announcement_schedule(day, np.random.default_rng(0), q_phase=0)
            != new.announcement_schedule(day, np.random.default_rng(0), q_phase=17))
    os.unlink(path)


def test_measurement_tools_pin_the_schedule():
    """P4-19: three Phase-4 tools measured the generator without pinning `schedule_mode`, so they silently
    measured the v2 ranges and their numbers were quoted as deployed properties. No test could catch that --
    deployed and recorded agreed; the recorded values had just been measured elsewhere. This is the guard."""
    import pathlib
    root = pathlib.Path(ROOT) / "tools" / "phase4"
    offenders = [f.name for f in sorted(root.glob("e4_*.py"))
                 if "SyntheticMarketEnv(" in f.read_text(encoding="utf-8")
                 and "schedule_mode" not in f.read_text(encoding="utf-8")]
    assert not offenders, (
        f"these tools construct the environment without pinning schedule_mode: {offenders}. A tool that "
        f"measures the generator must pin the configuration it measures (addendum section 5).")


def test_post_top_ranges_are_fit_not_stipulated():
    """P4-20: post_top_drop and post_top_len shipped as v2 DESIGN ranges while the panel held the data."""
    for k in ("post_top_drop", "post_top_len"):
        spec = EP.RANGES[k]
        assert isinstance(spec, dict) and "grid" in spec,             f"{k} is still a stipulated interval, not an empirical grid"
        assert len(spec["grid"]) >= 10


def test_v2_schedule_path_is_bit_identical():
    """Every Phase-4 generator change is a switch with the v2 behaviour behind it (plan's execution rule).

    With schedule_mode='v2' the draw sequence must be exactly v2's, including the ORDER in which the bull-trap
    parameters consume the stream."""
    rng_a = np.random.default_rng(77)
    rng_b = np.random.default_rng(77)
    for scenario in ("crash", "bull_trap", "sustained_bull", "flat"):
        a = draw_schedule(scenario, 200, rng_a, schedule_mode="v2").to_dict()
        b = draw_schedule(scenario, 200, rng_b, schedule_mode="v2").to_dict()
        assert a == b
    rng = np.random.default_rng(5)
    s = draw_schedule("bull_trap", 200, rng, schedule_mode="v2")
    assert 0.02 <= s.kappa <= 0.04 and 10 <= s.post_top_len <= 30 and 0.30 <= s.post_top_drop <= 0.50
    s = draw_schedule("crash", 200, rng, schedule_mode="v2")
    assert 15 <= s.det_len <= 40 and s.front_load == 0.5 and s.delta == 0.70


def test_grid_sampler_reproduces_the_panel_shape():
    """The inverse-CDF sampler must reproduce the panel's median, not the interval midpoint."""
    grid = {"grid": [0.0, 1.0, 2.0, 3.0, 100.0]}
    rng = np.random.default_rng(11)
    draws = [_draw_helper(rng, grid) for _ in range(4000)]
    assert np.median(draws) < 10.0, "the sampler is behaving like a uniform over [min, max]"


def _draw_helper(rng, spec):
    from envs.v2.schedule import _draw
    return _draw(rng, {"k": spec}, "k")


def test_status_vocabulary_is_declared_and_enforced():
    """P4-39: every status in events.json must be a term the file itself declares, and the loader must RAISE
    when one is not.

    Nothing enforced this during Phase 4 and the vocabulary drifted: by the end of the phase two of ten
    entries carried undeclared statuses (`crash_v_drift`, `multi_asset`) and `hazard` carried INCUMBENT,
    whose declared meaning is "the v2 behaviour stays", while a FITTED value was in force. A controlled
    vocabulary is only a control if something enforces it, so this asserts both halves: the file is clean,
    and a file that is not clean is rejected."""
    import json
    from envs.v2 import events_params as ep
    if not ep.PRESENT:
        pytest.skip("events.json absent")
    d = json.load(open(ep.EVENTS_PATH, encoding="utf-8"))
    declared = set(d["_status_key"])
    used = {k: v["status"] for k, v in d.items() if isinstance(v, dict) and "status" in v}
    assert used, "no entry carries a status"
    undeclared = {k: v for k, v in used.items() if v not in declared}
    assert not undeclared, f"undeclared statuses: {undeclared}; declared: {sorted(declared)}"
    # INCUMBENT means the v2 behaviour stays -- so an INCUMBENT hazard must carry v2's hazard, not a fit
    if used.get("hazard") == "INCUMBENT":
        hz = json.load(open(os.path.join(ROOT, "envs", "v2", "params", "hazard.json"), encoding="utf-8"))
        assert d["hazard"]["value"]["h0"] == hz["h0"], (
            "hazard is labelled INCUMBENT ('the v2 behaviour stays') but ships a value that is not v2's")
    # and the guard must actually fire
    import tempfile
    bad = dict(d)
    bad["blowoff"] = {**d["blowoff"], "status": "NOT A DECLARED TERM"}
    with tempfile.TemporaryDirectory() as td:
        q = os.path.join(td, "events.json")
        with open(q, "w", encoding="utf-8") as fh:
            json.dump(bad, fh)
        with pytest.raises(RuntimeError, match="does not declare"):
            ep.load(q)
