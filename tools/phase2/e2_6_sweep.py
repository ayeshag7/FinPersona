"""
E2.6 (PREREG_PHASE_2.md section 8): the persistence sweep.

Half-life levels {30, 60, 120, 250, 500} d (plus any level section 5.3's union rule adds), run twice:
  `sd`    -- MATCHED STATIONARY sd(x): sbar scaled so the realised sd(x) at T = 5,000 equals the value in force,
             so persistence is isolated from variance (the E1.3 convention, recalibrated for this engine)
  `innov` -- MATCHED INNOVATION VARIANCE: sbar held at the value in force, so sd(x) moves with h

Per level and matching: the full Section-9 checklist at 200 seeds x 4 scenarios (seeds SW 130000), the level-free
leakage surrogate at 100 seeds (seeds 131000), the hazard/topped share, the rejection rate, and -- reported at
EVERY level because it feeds the 16A go/no-go checkpoint -- the median number of oracle target switches per run
(ISFJ, theta = 0.05) with its IQR and the share of runs with >= 2 switches with a Wilson interval.

    python -m tools.phase2.e2_6_sweep [--levels 30,60,120,250,500] [--matching sd,innov]
        [--engine-template fw_hl{h}] [--n-checklist 200] [--n-audit 100] [--workers 3] [--only-stage calib]
Outputs: docs/env_v2/generated/v2_1/e2_6/sweep.json, sweep.md, checklist_<match>_h<h>.csv, cache/*.json
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

OUT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e2_6")
SEED_SW, SEED_AUD = 130000, 131000
SCEN4 = ("flat", "crash", "bull_trap", "sustained_bull")
THETA = 0.05
N_CAL_PATHS, T_CAL = 20, 5000


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def _sd_x_job(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.v2.generator import GenConfig, generate
    engine, sbar, seed, T = args
    r = generate(GenConfig(scenario="flat", T=T, seed=seed, engine=engine, jumps=False, reject=False,
                           garch={"sbar": float(sbar)}))
    m = r.day >= 1
    return float(r.x[0, m].std())


def _fmt(h):
    return f"{h:g}"


def calibrate(engine_template, levels, sbar_ref, workers, target_sd=None):
    """sd(x) at T = 5,000 per level at sbar_ref, then sbar_level = sbar_ref * target_sd / sd_measured
    (sd(x) is linear in the innovation scale), then a confirmation pass at the rescaled sbar."""
    out = {"sbar_ref": sbar_ref, "T": T_CAL, "n_paths": N_CAL_PATHS, "levels": {}}
    jobs, keys = [], []
    for h in levels:
        eng = engine_template.format(h=_fmt(h))
        for s in range(N_CAL_PATHS):
            jobs.append((eng, sbar_ref, 132000 + 100 * levels.index(h) + s, T_CAL))
            keys.append(h)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        vals = list(ex.map(_sd_x_job, jobs, chunksize=1))
    for h in levels:
        sd = float(np.mean([v for v, k in zip(vals, keys) if k == h]))
        out["levels"][_fmt(h)] = {"sd_x_at_sbar_ref": sd}
    tgt = target_sd if target_sd is not None else out["levels"][_fmt(levels[0])]["sd_x_at_sbar_ref"]
    out["target_sd_x"] = float(tgt)
    jobs, keys = [], []
    for h in levels:
        sb = sbar_ref * tgt / out["levels"][_fmt(h)]["sd_x_at_sbar_ref"]
        out["levels"][_fmt(h)]["sbar_matched_sd"] = float(sb)
        out["levels"][_fmt(h)]["sbar_matched_innov"] = float(sbar_ref)
        eng = engine_template.format(h=_fmt(h))
        for s in range(N_CAL_PATHS):
            jobs.append((eng, sb, 133000 + 100 * levels.index(h) + s, T_CAL))
            keys.append(h)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        vals = list(ex.map(_sd_x_job, jobs, chunksize=1))
    for h in levels:
        out["levels"][_fmt(h)]["sd_x_after_match"] = float(np.mean([v for v, k in zip(vals, keys) if k == h]))
    return out


def _switch_job(args):
    import warnings
    warnings.filterwarnings("ignore")
    import numpy as _np
    from envs.v2.generator import GenConfig, generate
    from evaluation.metrics_v2 import oracle_target
    from evaluation.targets import centre
    sc, seed, engine, sbar = args
    kw = dict(scenario=sc, T=200, seed=seed, engine=engine, garch={"sbar": float(sbar)})
    if sc == "crash":
        kw["delta"] = 0.70
    r = generate(GenConfig(**kw))
    m = r.day >= 1
    x = r.x[0, m]
    cs = oracle_target(x, THETA, "ISFJ", prev_target=centre("ISFJ"))
    return {"scenario": sc, "seed": seed, "switches": int(_np.sum(_np.diff(cs) != 0)),
            "sd_x_200": float(x.std()), "coverage": float(_np.mean(_np.abs(x) >= THETA)),
            "attempts": int(r.attempts), "topped": bool(r.event_meta.get("topped", False))}


def switches(engine, sbar, n, workers):
    jobs = [(sc, SEED_SW + s, engine, sbar) for sc in SCEN4 for s in range(n)]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        rows = list(ex.map(_switch_job, jobs, chunksize=4))
    out = {}
    for sc in SCEN4:
        sw = np.array([r["switches"] for r in rows if r["scenario"] == sc])
        k = int((sw >= 2).sum())
        lo, hi = wilson(k, len(sw))
        rs = [r for r in rows if r["scenario"] == sc]
        out[sc] = {"n": int(len(sw)), "median_switches": float(np.median(sw)),
                   "iqr": [float(np.percentile(sw, 25)), float(np.percentile(sw, 75))],
                   "share_ge2": float((sw >= 2).mean()), "share_ge2_wilson": [lo, hi],
                   "mean_sd_x_200": float(np.mean([r["sd_x_200"] for r in rs])),
                   "mean_coverage": float(np.mean([r["coverage"] for r in rs])),
                   "mean_attempts": float(np.mean([r["attempts"] for r in rs])),
                   "rejection_rate": float(np.mean([r["attempts"] > 1 for r in rs])),
                   "topped_share": float(np.mean([r["topped"] for r in rs])) if sc == "bull_trap" else None}
    return out


def _panel_job(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    from evaluation.leakage_audit import panel_from_env
    sc, seed, engine, sbar = args
    kw = dict(scenario=sc, n_days=200, seed=seed, engine=engine, config={"garch": {"sbar": float(sbar)}})
    if sc == "crash":
        kw["crash_discount"] = 0.70
    env = SyntheticMarketEnv(**kw)
    return panel_from_env(env, sc, seed)


def level_free_audit(engine, sbar, n, workers):
    import pandas as pd
    from evaluation.leakage_audit import l2_surrogate
    jobs = [(sc, SEED_AUD + s, engine, sbar) for sc in SCEN4 for s in range(n)]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        frames = list(ex.map(_panel_job, jobs, chunksize=4))
    panel = pd.concat(frames, ignore_index=True)
    from agent.render import rendered_market_fields
    shown = [c for c in rendered_market_fields("v2") if c in panel.columns]
    l2 = l2_surrogate(panel, shown, control="level_free")
    return {"n_paths": len(jobs), "n_rows": int(len(panel)), "n_shown_fields": len(shown),
            "table": json.loads(l2.to_json(orient="records"))}


def run_checklist_level(engine, sbar, n, tag):
    from envs.synthetic_market import checklist_paths
    from evaluation.stylized_facts import run_checklist, to_markdown
    paths = checklist_paths(n, 200, config={"garch": {"sbar": float(sbar)}}, engine=engine, seed0=SEED_SW)
    df = run_checklist(paths)
    df.to_csv(os.path.join(OUT, f"checklist_{tag}.csv"), index=False)
    with open(os.path.join(OUT, f"checklist_{tag}.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(to_markdown(df, f"E2.6 checklist, {tag}",
                             f"engine {engine}, sbar {sbar:.5f}, {n} seeds per scenario, T = 200, seeds from {SEED_SW}."))
    cols = [c for c in ("item", "property", "statistic", "criterion", "pass", "n_seeds") if c in df.columns]
    return {"n_pass": int(df["pass"].sum()), "n_items": int(len(df)),
            "items": json.loads(df[cols].to_json(orient="records"))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", default="30,60,120,250,500")
    ap.add_argument("--matching", default="sd,innov")
    ap.add_argument("--engine-template", default="fw_hl{h}")
    ap.add_argument("--sbar-ref", type=float, default=0.017)
    ap.add_argument("--target-sd", type=float, default=None)
    ap.add_argument("--n-checklist", type=int, default=200)
    ap.add_argument("--n-switch", type=int, default=200)
    ap.add_argument("--n-audit", type=int, default=100)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--stages", default="calib,switch,checklist,audit")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT, "cache"), exist_ok=True)
    levels = [float(v) if "." in v else int(v) for v in a.levels.split(",")]
    stages = a.stages.split(",")
    path = os.path.join(OUT, "sweep.json")
    res = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    res.setdefault("design", {})
    res["design"].update({"levels": levels, "matching": a.matching.split(","), "engine_template": a.engine_template,
                          "sbar_ref": a.sbar_ref, "n_checklist": a.n_checklist, "n_switch": a.n_switch,
                          "n_audit": a.n_audit, "seed_sw": SEED_SW, "seed_aud": SEED_AUD, "theta": THETA})

    def save():
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1)

    if "calib" in stages and "calibration" not in res:
        t0 = time.time()
        res["calibration"] = calibrate(a.engine_template, levels, a.sbar_ref, a.workers, a.target_sd)
        res["calibration"]["seconds"] = round(time.time() - t0)
        save()
        print(json.dumps(res["calibration"], indent=1), flush=True)
    elif "calib" in stages and "calibration" in res:
        # EXTEND an existing calibration with levels it does not have, keeping the stored target sd(x) so the
        # cells already run stay valid.  The extension's seeds are keyed on the LEVEL VALUE rather than on its
        # index in the list (the original six used the index), so adding levels can never move an existing one;
        # the different seed rule is stated in the output.
        cal = res["calibration"]
        missing = [h for h in levels if _fmt(h) not in cal["levels"]]
        if missing:
            t0 = time.time()
            tgt = float(cal["target_sd_x"])
            jobs, keys = [], []
            for h in missing:
                eng = a.engine_template.format(h=_fmt(h))
                for sd_seed in range(N_CAL_PATHS):
                    jobs.append((eng, a.sbar_ref, 134000 + int(round(h * 10)) * 100 + sd_seed, T_CAL))
                    keys.append(h)
            with ProcessPoolExecutor(max_workers=a.workers) as ex:
                vals = list(ex.map(_sd_x_job, jobs, chunksize=1))
            for h in missing:
                sd = float(np.mean([v for v, k in zip(vals, keys) if k == h]))
                cal["levels"][_fmt(h)] = {"sd_x_at_sbar_ref": sd,
                                          "sbar_matched_sd": float(a.sbar_ref * tgt / sd),
                                          "sbar_matched_innov": float(a.sbar_ref),
                                          "sd_x_after_match": None,
                                          "seed_rule": "extension: seeds keyed on the level value (134000 + "
                                                       "round(10 h) * 100 + i), not on the list index"}
            cal.setdefault("extended", []).extend(_fmt(h) for h in missing)
            cal["extension_seconds"] = round(time.time() - t0)
            save()
            print(f"[e2_6] calibration extended with {[_fmt(h) for h in missing]} "
                  f"in {cal['extension_seconds']} s", flush=True)
    cal = res.get("calibration")
    res.setdefault("cells", {})
    for match in a.matching.split(","):
        for h in levels:
            eng = a.engine_template.format(h=_fmt(h))
            sbar = cal["levels"][_fmt(h)][f"sbar_matched_{match}"]
            key = f"{match}|h{_fmt(h)}"
            cell = res["cells"].setdefault(key, {"engine": eng, "sbar": sbar, "half_life": h, "matching": match})
            for stage, fn in (("switch", lambda: switches(eng, sbar, a.n_switch, a.workers)),
                              ("checklist", lambda: run_checklist_level(eng, sbar, a.n_checklist, key.replace("|", "_"))),
                              ("audit", lambda: level_free_audit(eng, sbar, a.n_audit, a.workers))):
                if stage not in stages or stage in cell:
                    continue
                t0 = time.time()
                print(f"[e2_6] {key} {stage} ...", flush=True)
                cell[stage] = fn()
                cell[f"{stage}_seconds"] = round(time.time() - t0)
                save()
                print(f"[e2_6] {key} {stage}: {cell[f'{stage}_seconds']} s", flush=True)
    write_md(res, levels, a)
    print("written", OUT)


def _best(table, feature_set, target, phase_group):
    """Best (max R2) model of a feature set / target / phase group, with its cluster-bootstrap interval.
    `price_only` is the CONTROL label the audit keeps for continuity -- under control='level_free' it is the
    level-free set (returns, ratios to moving averages, RSI, MACD/P, trend), not the price level."""
    rows = [r for r in table if r["feature_set"] == feature_set and r["target"] == target
            and r["phase_group"] == phase_group and r.get("R2") is not None]
    if not rows:
        return "-"
    b = max(rows, key=lambda r: r["R2"])
    return f"{b['R2']:.3f} [{b['R2_lo']:.3f}, {b['R2_hi']:.3f}] ({b['model']})"


def write_md(res, levels, a):
    cal = res.get("calibration", {})
    L = ["# E2.6 persistence sweep (PREREG_PHASE_2.md section 8)", "",
         f"Engine template `{res['design']['engine_template']}`; levels {levels} d; two matchings "
         "(**sd** = matched stationary sd(x); **innov** = matched innovation variance). Checklist "
         f"{res['design']['n_checklist']} seeds x 4 scenarios (seeds from {SEED_SW}); oracle switches "
         f"{res['design']['n_switch']} seeds; level-free surrogate {res['design']['n_audit']} seeds "
         f"(seeds from {SEED_AUD}). No criterion is attached: this is the sensitivity table Phases 6 and 9 "
         "consume, and 16A's G3 is decided in Phase 6 on the frozen generator.", ""]
    if cal:
        L += ["## Calibration of the innovation scale", "",
              f"Target stationary sd(x) = {cal['target_sd_x']:.4f} (the value in force). sd(x) at T = "
              f"{cal['T']}, {cal['n_paths']} flat paths, jumps off.", "",
              "| h (d) | sd(x) at sbar_ref | sbar (matched sd) | sd(x) after match | calibration pass |",
              "|---|---|---|---|---|"]
        for h in levels:
            c = cal["levels"][_fmt(h)]
            after = ("-" if c.get("sd_x_after_match") is None else f"{c['sd_x_after_match']:.4f}")
            L.append(f"| {_fmt(h)} | {c['sd_x_at_sbar_ref']:.4f} | {c['sbar_matched_sd']:.5f} | {after}"
                     + (" | extension |" if c.get("seed_rule") else " | original |"))
    L += ["", "## Oracle target switches per run (ISFJ, theta = 0.05) -- the 16A G3 input", "",
          "| matching | h (d) | scenario | median switches | IQR | share >= 2 | Wilson 95 % | sd(x) over 200 d | coverage |",
          "|---|---|---|---|---|---|---|---|---|"]
    for key, cell in res.get("cells", {}).items():
        if "switch" not in cell:
            continue
        for sc, s in cell["switch"].items():
            L.append(f"| {cell['matching']} | {cell['half_life']} | {sc} | {s['median_switches']:.0f} | "
                     f"{s['iqr'][0]:.0f}-{s['iqr'][1]:.0f} | {s['share_ge2']:.2f} | "
                     f"[{s['share_ge2_wilson'][0]:.2f}, {s['share_ge2_wilson'][1]:.2f}] | "
                     f"{s['mean_sd_x_200']:.4f} | {s['mean_coverage']:.2f} |")
    L += ["", "## Checklist and the level-free surrogate", "",
          "| matching | h (d) | checklist passes | level-free R2(x), calm | level-free, all phases | full-field R2(x), calm |",
          "|---|---|---|---|---|---|"]
    for key, cell in res.get("cells", {}).items():
        cl = cell.get("checklist")
        au = cell.get("audit")
        r2c, r2a, r2cf = "-", "-", "-"
        if au:
            r2c = _best(au["table"], "price_only", "x", "calm")
            r2a = _best(au["table"], "price_only", "x", "all")
            r2cf = _best(au["table"], "full", "x", "calm")
        L.append(f"| {cell['matching']} | {cell['half_life']} | "
                 f"{(str(cl['n_pass']) + '/' + str(cl['n_items'])) if cl else '-'} | {r2c} | {r2a} | {r2cf} |")
    with open(os.path.join(OUT, "sweep.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
