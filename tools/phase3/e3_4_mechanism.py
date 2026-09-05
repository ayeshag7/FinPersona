"""
E3.4 (PREREG_PHASE_3.md sections 5.3 and 6; REG-6): the x-innovation multipliers calibrated closed-loop to the
E3.3 FIT targets, then the three variance mechanisms run and judged by the empirical rise/decay rule.

    python -m tools.phase3.e3_4_mechanism --stage calibrate   # m_x per phase (A's parameterisation, shared)
    python -m tools.phase3.e3_4_mechanism --stage derive-c    # mechanism C's FIT-derived switching parameters
    python -m tools.phase3.e3_4_mechanism --stage arms        # A, B (ramp grid), C at 200 crash seeds each
    python -m tools.phase3.e3_4_mechanism --stage decide      # REG-6's rule against the E3.3 CIs (both rules)

Inputs: e3_3/episodes.json (targets), e3_2/fit.json + e3_5/../refit (the block in force: shape, nu, jumps,
sigma_V*, h*, sbar*) via e3_4/block.json written by tools/phase3/make_block.py.
Outputs: docs/env_v2/generated/v2_1/e3_4/{calibration.json,mechanism_c.json,arms.json,decision.json,decision.md}
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

from tools.phase3.episodes import drawdown_episodes, rise_decay, _rv, rolling_rv  # noqa: E402

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e3_4")
E33 = os.path.join(GEN, "e3_3", "episodes.json")
BLOCK = os.path.join(OUT, "block.json")
SEED_CRASH0, SEED_FLAT0 = 210000, 211000
N_ARM = 200
CAL_SEEDS = 60
CAL_ITERS = 3
RAMP_GRID = (0, 5, 10, 20, 40)
CRASH_PHASES = ("deterioration", "panic", "stabilisation")
BULL_PHASES = ("mania", "blow-off", "post-top")


def load_block():
    return json.load(open(BLOCK, encoding="utf-8"))


def gen_cfg(block, mult=None, scale_mode="variance", ramp_days=0, switching=None):
    g = {"alpha": block["shape"]["alpha"], "gamma": block["shape"]["gamma"], "beta": block["shape"]["beta"],
         "df": block["nu"], "sbar": block["sbar"], "scale_mode": scale_mode, "ramp_days": ramp_days}
    if mult is not None:
        g["mult"] = dict(mult)
    if switching is not None:
        g["switching"] = dict(switching)
        # mechanism C carries endogenous stress spells in calm (entry at p_entry_base), so its calm-REGIME level
        # is scaled down to keep the section-3.4 identity: E[v(R)] over the unconditional regime mix = sbar^2
        g["sbar"] = block["sbar"] * float(switching.get("sbar_scale", 1.0))
    return {"sigma_V": block["sigma_V"], "jump_rate": block["jump_rate"], "jump_sd": block["jump_sd"],
            "engine": f"ar1_hl{block['h']}", "garch": g}


def one_path(args):
    """(scenario, seed, cfg_dict) -> per-phase realised RV ratios + the E3.4 statistics."""
    scenario, seed, cfg = args
    from envs.synthetic_market import SyntheticMarketEnv
    env = SyntheticMarketEnv(scenario, 200, seed, config=cfg)
    d = env.data[env.data["asset"] == 0]
    p = d["price"].to_numpy(float)
    r = np.diff(np.log(p))
    ph = d["phase"].to_numpy(dtype=object)[1:]           # phase of the day the return lands on
    ev = int(env.schedule.event_start)
    out = {"seed": seed, "scenario": scenario, "attempts": env.attempts}
    rv_calm = _rv(r, 0, max(ev - 2, 0), min_n=30)
    out["rv_calm"] = float(rv_calm) if np.isfinite(rv_calm) else None
    if out["rv_calm"]:
        for k in (CRASH_PHASES if scenario == "crash" else BULL_PHASES):
            m = ph == k
            if m.sum() >= 10:
                out[f"m_{k}"] = float(np.mean(r[m] ** 2) / rv_calm)
    if scenario == "crash" and out["rv_calm"]:
        eps = drawdown_episodes(p)
        if eps:
            ep = min(eps, key=lambda e: e["depth"])
            rd = rise_decay(ep, p, r, rv_calm)
            if rd:
                out.update({k: rd[k] for k in ("rise", "decay_half_life", "censored", "stress_spell")})
            out["depth"] = ep["depth"]
    if scenario == "flat":
        out["sd_r"] = float(np.std(r, ddof=1))
        out["sd_x"] = float(d["x"].to_numpy(float).std(ddof=1))
    return out


def run_panel(scenario, seeds, cfg, workers=3):
    jobs = [(scenario, s, cfg) for s in seeds]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(one_path, jobs, chunksize=4))


def med(rows, key):
    v = np.array([x[key] for x in rows if x.get(key) is not None and np.isfinite(x.get(key, np.nan))], float)
    return (float(np.median(v)), int(len(v))) if len(v) else (float("nan"), 0)


def first_order_mx(m_total, s_A, sigma_V):
    return max((m_total * s_A ** 2 - sigma_V ** 2) / (s_A ** 2 - sigma_V ** 2), 0.05)


def stage_calibrate(workers):
    t0 = time.time()
    block = load_block()
    e33 = json.load(open(E33, encoding="utf-8"))
    targets = {k: e33["multipliers"][f"mu_{k}"]["median"] for k in CRASH_PHASES + BULL_PHASES}
    cis = {k: e33["multipliers"][f"mu_{k}"]["ci95"] for k in CRASH_PHASES + BULL_PHASES}
    s_A, sV = block["s_A"], block["sigma_V"]
    mult = {k: first_order_mx(targets[k], s_A, sV) for k in targets}
    mult["calm"] = 1.0
    mult["sustained-bull"] = 1.0          # DESIGN (review R1-D5), restated in PREREG 5.3
    history = [{"iter": 0, "mult": dict(mult), "note": "first-order mapping"}]
    for it in range(1, CAL_ITERS + 1):
        cfg = gen_cfg(block, mult=mult)
        crash = run_panel("crash", range(SEED_CRASH0 + 500, SEED_CRASH0 + 500 + CAL_SEEDS), cfg, workers)
        bull = run_panel("bull_trap", range(SEED_CRASH0 + 700, SEED_CRASH0 + 700 + CAL_SEEDS), cfg, workers)
        real = {}
        for k in CRASH_PHASES:
            real[k] = med(crash, f"m_{k}")
        for k in BULL_PHASES:
            real[k] = med(bull, f"m_{k}")
        adj = {}
        for k in CRASH_PHASES + BULL_PHASES:
            m_r, n = real[k]
            if np.isfinite(m_r) and m_r > 0:
                adj[k] = targets[k] / m_r
                mult[k] = max(mult[k] * adj[k], 0.05)
        history.append({"iter": it, "realised": {k: real[k][0] for k in real},
                        "n": {k: real[k][1] for k in real}, "mult": dict(mult)})
        print(f"iter {it}: realised {[round(real[k][0], 2) for k in CRASH_PHASES + BULL_PHASES]} "
              f"-> mult {[round(mult[k], 2) for k in CRASH_PHASES + BULL_PHASES]}", flush=True)
    # final verification at N_ARM seeds (the A-arm panel, reused by stage_arms via the cache file)
    cfg = gen_cfg(block, mult=mult)
    crash = run_panel("crash", range(SEED_CRASH0, SEED_CRASH0 + N_ARM), cfg, workers)
    bull = run_panel("bull_trap", range(SEED_CRASH0 + 5000, SEED_CRASH0 + 5000 + N_ARM), cfg, workers)
    verify = {}
    for k in CRASH_PHASES:
        m_r, n = med(crash, f"m_{k}")
        verify[k] = {"target": targets[k], "target_ci": cis[k], "realised": m_r, "n": n,
                     "inside_ci": bool(cis[k][0] <= m_r <= cis[k][1])}
    for k in BULL_PHASES:
        m_r, n = med(bull, f"m_{k}")
        verify[k] = {"target": targets[k], "target_ci": cis[k], "realised": m_r, "n": n,
                     "inside_ci": bool(cis[k][0] <= m_r <= cis[k][1])}
    out = {"design": {"cal_seeds": CAL_SEEDS, "iters": CAL_ITERS, "verify_seeds": N_ARM,
                      "rule": "PREREG 5.3: first-order mapping then multiplicative closed-loop iterations on "
                              "the generator-realised total ratio; targets = E3.3 unconditional-reference "
                              "medians (ADDENDUM 1)", "block": block},
           "targets": targets, "target_cis": cis, "mult_x": mult, "history": history, "verify": verify,
           "arm_A_crash": crash, "arm_A_bull": bull, "seconds": round(time.time() - t0)}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "calibration.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({"mult_x": {k: round(v, 3) for k, v in mult.items()},
                      "verify": {k: {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items()}
                                 for k, v in verify.items()}}, indent=1))


def stage_derive_c():
    """Mechanism C's parameters, every piece FIT-derived (PREREG section 6). The panel-side pi is precomputed
    once on the local machine (pi_uncond.json -- datasets/ never travels); everything else is arithmetic."""
    t0 = time.time()
    cal = json.load(open(os.path.join(OUT, "calibration.json"), encoding="utf-8"))
    e33 = json.load(open(E33, encoding="utf-8"))
    mult = cal["mult_x"]
    v_ratio = mult["panic"]
    spell = e33["rise_decay"]["stress_spell"]["median"]
    p_exit = 1.0 / spell
    pre = json.load(open(os.path.join(OUT, "pi_uncond.json"), encoding="utf-8"))
    pi, shares = pre["pi_uncond_stress_share"], range(pre["n_stocks"])
    p_base = p_exit * pi / max(1.0 - pi, 1e-9)
    p_entry = {}
    for k in CRASH_PHASES + BULL_PHASES:
        s = (mult[k] - 1.0) / max(v_ratio - 1.0, 1e-9)
        s = min(max(s, 0.0), 1.0 - 1e-6)
        p_entry[k] = min(p_exit * s / (1.0 - s), 1.0) if mult[k] > 1.0 else p_base
    p_entry["panic"] = min(max(p_entry["panic"], 0.999), 1.0) if mult["panic"] >= v_ratio - 1e-9 else p_entry["panic"]
    pi_model = p_base / (p_base + p_exit)                 # the chain's own stationary stress share in calm
    kappa = 1.0 - pi_model + pi_model * v_ratio
    sw = {"v_ratio": v_ratio, "p_exit": p_exit, "p_entry_base": p_base, "p_entry": p_entry,
          "sbar_scale": 1.0 / math.sqrt(kappa)}
    out = {"switching": sw,
           "derivation": {"v_ratio": "= m_x(panic) (calibration.json)",
                          "p_exit": f"= 1 / median stress spell {spell} d (e3_3)",
                          "pi_uncond_stress_share": pi, "n_stocks": len(shares),
                          "pi_rule": "share of stock-days with RV21 >= own median x (1 + m_panic)/2",
                          "pi_model": pi_model, "kappa_E_v_over_vcalm": kappa,
                          "sbar_scale": "1/sqrt(kappa): C's calm-regime level scaled so the unconditional "
                                        "innovation variance over the regime mix stays sbar^2 (identity, PREREG 3.4)",
                          "p_entry": "p_exit s/(1-s), s = (m_x(phase)-1)/(v_ratio-1), capped at 1 (panic hits "
                                     "the cap by construction); calm/other = p_entry_base from pi"},
           "seconds": round(time.time() - t0)}
    with open(os.path.join(OUT, "mechanism_c.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


def arm_stats(rows):
    rise = np.array([x["rise"] for x in rows if x.get("rise") is not None], float)
    dec = np.array([x["decay_half_life"] for x in rows if x.get("decay_half_life") is not None], float)
    cens = [x.get("censored") for x in rows if "censored" in x]
    rng = np.random.default_rng(3)

    def ci(v):
        if len(v) < 5:
            return None
        m = np.median(v[rng.integers(0, len(v), (2000, len(v)))], axis=1)
        return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]
    return {"n_qualifying": int(len(rise)), "rise_median": float(np.median(rise)) if len(rise) else None,
            "rise_ci": ci(rise), "decay_median": float(np.median(dec)) if len(dec) else None,
            "decay_ci": ci(dec), "censored_share": float(np.mean([bool(c) for c in cens])) if cens else None,
            "mean_attempts": float(np.mean([x["attempts"] for x in rows]))}


def stage_arms(workers):
    t0 = time.time()
    block = load_block()
    cal = json.load(open(os.path.join(OUT, "calibration.json"), encoding="utf-8"))
    mult = cal["mult_x"]
    sw = json.load(open(os.path.join(OUT, "mechanism_c.json"), encoding="utf-8"))["switching"]
    e33 = json.load(open(E33, encoding="utf-8"))
    rise_emp = e33["rise_decay"]["rise"]["median"]
    arms = {}
    # A: the calibration's own 200-seed panel is the A arm (same seeds, same config)
    arms["A_variance"] = arm_stats(cal["arm_A_crash"])
    # B: omega scaling with the FIT ramp -- L_ramp fitted on the rise time alone (grid), decay judged out-of-fit
    b_grid = {}
    for L in RAMP_GRID:
        cfg = gen_cfg(block, mult=mult, scale_mode="omega", ramp_days=L)
        rows = run_panel("crash", range(SEED_CRASH0 + 2000, SEED_CRASH0 + 2000 + CAL_SEEDS), cfg, workers)
        st = arm_stats(rows)
        b_grid[L] = st
        print(f"B ramp {L}: rise {st['rise_median']} decay {st['decay_median']} (n {st['n_qualifying']})", flush=True)
    ok = {L: st for L, st in b_grid.items() if st["rise_median"] is not None}
    L_fit = min(ok, key=lambda L: abs(ok[L]["rise_median"] - rise_emp)) if ok else 0
    cfg = gen_cfg(block, mult=mult, scale_mode="omega", ramp_days=L_fit)
    arms["B_omega_ramp"] = arm_stats(run_panel("crash", range(SEED_CRASH0, SEED_CRASH0 + N_ARM), cfg, workers))
    arms["B_omega_ramp"]["ramp_days_fit"] = int(L_fit)
    arms["B_omega_ramp"]["ramp_grid"] = {str(L): {"rise": st["rise_median"], "decay": st["decay_median"]}
                                         for L, st in b_grid.items()}
    # C: two-regime switching
    cfg = gen_cfg(block, mult=mult, scale_mode="switching", switching=sw)
    arms["C_switching"] = arm_stats(run_panel("crash", range(SEED_CRASH0, SEED_CRASH0 + N_ARM), cfg, workers))
    # flat arm (mechanism A): V4's unconditional check and the calm/sd(x) numbers
    cfg = gen_cfg(block, mult=mult)
    flat = run_panel("flat", range(SEED_FLAT0, SEED_FLAT0 + N_ARM), cfg, workers)
    sd_r, n1 = med(flat, "sd_r")
    sd_x, _ = med(flat, "sd_x")
    arms["flat_A"] = {"sd_r_median": sd_r, "sd_x_median": sd_x, "n": n1,
                      "s_A_target": block["s_A"],
                      "note": "per-path sd over 200 benchmark days; the 200,000-step V4 check is in the report"}
    out = {"arms": arms, "block": block, "mult_x": mult, "switching": sw,
           "seeds": {"crash": [SEED_CRASH0, SEED_CRASH0 + N_ARM - 1], "flat": [SEED_FLAT0, SEED_FLAT0 + N_ARM - 1]},
           "seconds": round(time.time() - t0)}
    with open(os.path.join(OUT, "arms.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if not isinstance(vv, dict)} for k, v in arms.items()},
                     indent=1))


def stage_decide():
    e33 = json.load(open(E33, encoding="utf-8"))
    arms = json.load(open(os.path.join(OUT, "arms.json"), encoding="utf-8"))["arms"]
    rules = {"pooled (primary, PREREG 6)": {"rise": e33["rise_decay"]["rise"]["ci95"],
                                            "decay": e33["rise_decay"]["decay_half_life"]["ci95"]},
             "fast-crash (ADDENDUM 2, governs adoption)": {"rise": e33["rise_decay_fast"]["rise"]["ci95"],
                                                           "decay": e33["rise_decay_fast"]["decay_half_life"]["ci95"]}}
    order = ["A_variance", "B_omega_ramp", "C_switching"]     # REG-6's free-parameter ordering A < B < C
    verdicts = {}
    for rname, ci in rules.items():
        v = {}
        for a in order:
            st = arms[a]
            ok_r = st["rise_median"] is not None and ci["rise"][0] <= st["rise_median"] <= ci["rise"][1]
            ok_d = st["decay_median"] is not None and ci["decay"][0] <= st["decay_median"] <= ci["decay"][1]
            v[a] = {"rise": st["rise_median"], "rise_in": bool(ok_r), "decay": st["decay_median"],
                    "decay_in": bool(ok_d), "passes": bool(ok_r and ok_d)}
        passers = [a for a in order if v[a]["passes"]]
        v["adopted"] = passers[0] if passers else "A_variance (documented shortfall, REG-6's consequence)"
        verdicts[rname] = v
    adopted = verdicts["fast-crash (ADDENDUM 2, governs adoption)"]
    out = {"empirical_cis": rules, "verdicts": verdicts,
           "decision": {"adopted": adopted["adopted"],
                        "rule": "REG-6: both statistics inside the empirical 95 % CI; ties -> fewer parameters "
                                "(A < B < C); none -> A with the shortfall documented. ADDENDUM 2: the "
                                "fast-crash CIs govern adoption, the pooled CIs are the registered primary "
                                "and both are reported."}}
    with open(os.path.join(OUT, "decision.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    L = ["# E3.4 mechanism decision (REG-6; PREREG_PHASE_3.md section 6, ADDENDUM section 2)", ""]
    for rname, v in verdicts.items():
        L += [f"## Against the {rname} CIs: rise {rules[rname]['rise']}, decay {rules[rname]['decay']}", "",
              "| mechanism | rise (d) | in CI | decay (d) | in CI | passes |", "|---|---|---|---|---|---|"]
        for a in order:
            L.append(f"| {a} | {v[a]['rise']} | {v[a]['rise_in']} | {v[a]['decay']} | {v[a]['decay_in']} | "
                     f"{v[a]['passes']} |")
        L += [f"", f"**Adopted under this rule: {v['adopted']}**", ""]
    with open(os.path.join(OUT, "decision.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["calibrate", "derive-c", "arms", "decide"])
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.stage == "calibrate":
        stage_calibrate(a.workers)
    elif a.stage == "derive-c":
        stage_derive_c()
    elif a.stage == "arms":
        stage_arms(a.workers)
    else:
        stage_decide()


if __name__ == "__main__":
    main()
