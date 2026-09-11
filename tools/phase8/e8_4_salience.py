"""
v2.1 Phase 8 -- E8.4: are the salience shares identified? (PREREG_PHASE_8.md 4; weakness 55, 67)

    python -u -m tools.phase8.e8_4_salience --stages pilot,synthetic,bootstrap

`pilot`      the identification check on the pilot's own designs: the main runs (start-at-target, four arms), the
             main static + memory runs alone (E8.5's arm set), and the nine common-start runs.
`synthetic`  two known-answer designs, each with c* = the persona's centre + a market effect + noise and NO directive
             effect: (A) start-at-target, static and memory (the pilot's design); (B) common start, static / memory /
             swapped for ISFJ, INTJ, ENTJ plus the NONE and O3 references.  The check's verdict for each, and the
             shares over 10 surrogate seeds -- their spread under (A) is the non-identification made visible.
`bootstrap`  design (B) through `salience_by_window(identification="v2_1")`: the seed-cluster bootstrap intervals
             (200 refits per window, PREREG 4), and whether S_directive's interval covers 0 and S_persona's excludes it.

Outputs: docs/env_v2/generated/v2_1/e8_4/{identification.json, identification.md, shares_synthetic.csv,
bootstrap.csv, bootstrap.json}
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
warnings.filterwarnings("ignore")

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e8_4")
SWAP = {"ISFJ": "ENTJ", "ENTJ": "ISFJ", "INTJ": "ENTJ"}
N_SEEDS, N_DAYS = 8, 50


def _centre(p: str) -> float:
    from evaluation.targets import centre
    try:
        return float(centre(p))
    except Exception:                                       # noqa: BLE001
        return 0.5


def pilot_runs(sub: str) -> pd.DataFrame:
    rows = []
    for f in glob.glob(os.path.join(ROOT, "results_v2_pilot", sub, "*", "*", "*", "*.csv")):
        d = pd.read_csv(f, nrows=1)
        n = sum(1 for _ in open(f, encoding="utf-8")) - 1
        if n < 200:
            continue
        rows.append(d.iloc[0])
    return pd.DataFrame(rows)


def frame(design: str, rng) -> pd.DataFrame:
    from evaluation.salience import MARKET_FEATURES
    if design == "A_start_at_target":
        cells = [(p, a, mb, p) for p in ("ISFJ", "INTJ", "ENTJ") for a, mb in (("static", "none"), ("memory", "mandate"))]
        start = "target"
    else:
        cells = [(p, a, mb, (SWAP[p] if a == "swapped" else p)) for p in ("ISFJ", "INTJ", "ENTJ")
                 for a, mb in (("static", "none"), ("memory", "mandate"), ("swapped", "mandate"))]
        cells += [(p, "static", "none", p) for p in ("NONE", "O3_conservative", "O3_aggressive")]
        start = "common"
    market = {(s, t): {f: rng.normal() for f in MARKET_FEATURES} for s in range(N_SEEDS) for t in range(1, N_DAYS + 1)}
    rows = []
    for p, arm, mb, mp in cells:
        c0 = _centre(p) if start == "target" else 0.5
        for s in range(N_SEEDS):
            for t in range(1, N_DAYS + 1):
                mk = market[(s, t)]
                y = float(np.clip(_centre(p) + 0.05 * mk["obs_RSI14"] + rng.normal(0, 0.05), 0, 1))
                rows.append({"Model": "synthetic", "Persona": p, "Arm": arm, "Mandate_Block": mb, "Mandate_Persona": mp,
                             "Seed": s, "Decode_Replicate": 0, "Day": t, "Start_Design": start, "Start_Cash_Share": c0,
                             "Target_Cash_Share": y, "Cash_Share": y, **mk})
    return pd.DataFrame(rows)


def _jsonable(chk):
    return json.loads(json.dumps(chk, default=float))


def stage_pilot() -> dict:
    from evaluation.salience import identification_check
    main = pilot_runs("main"); common = pilot_runs("common_start")
    out = {"pilot_main_all_arms": identification_check(main),
           "pilot_main_static_memory": identification_check(main[main["Arm"].isin(["static", "memory"])]),
           "pilot_common_start": identification_check(common)}
    return {k: _jsonable(v) for k, v in out.items()}


def _synthetic_fit(args):
    from evaluation.salience import surrogate_shares
    design, w0, s, dw = args
    t0 = time.time()
    return {"design": design, "window_start": w0, "surrogate_seed": s, **surrogate_shares(dw, seed=s),
            "seconds": time.time() - t0}


def stage_synthetic(workers: int) -> dict:
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from evaluation.salience import _init_threads, identification_check
    res, tasks = {}, []
    for design in ("A_start_at_target", "B_common_start_with_references"):
        d = frame(design, np.random.default_rng(84))
        res[design] = _jsonable(identification_check(d))
        print(design, "identified:", res[design]["identified"], res[design]["failing_clauses"],
              "| as registered:", res[design]["identified_as_registered"], flush=True)
        for w0 in (1, 26):
            dw = d[(d.Day >= w0) & (d.Day < w0 + 25)]
            tasks += [(design, w0, s, dw) for s in range(10)]
    share_rows = []
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_threads) as ex:
        futs = [ex.submit(_synthetic_fit, t) for t in tasks]
        for fu in as_completed(futs):
            r = fu.result()
            share_rows.append(r)
            print(f"  [{len(share_rows)}/{len(tasks)}] {r['design']} window {r['window_start']} seed {r['surrogate_seed']}: "
                  f"{r['seconds']:.0f}s", flush=True)
    sh = pd.DataFrame(share_rows).sort_values(["design", "window_start", "surrogate_seed"])
    os.makedirs(OUT, exist_ok=True)
    sh.to_csv(os.path.join(OUT, "shares_synthetic.csv"), index=False)
    spread = (sh.groupby(["design", "window_start"])[["S_persona", "S_directive", "S_start", "S_market", "r2"]]
              .agg(["mean", "std", "min", "max"]))
    print(spread.round(3).to_string())
    return res


def stage_bootstrap(n_boot: int, workers: int) -> dict:
    from evaluation.salience import salience_by_window
    d = frame("B_common_start_with_references", np.random.default_rng(84))
    t0 = time.time()
    t = salience_by_window(d, window=25, null_reps=0, identification="v2_1", n_boot=n_boot, n_jobs=workers)
    t.to_csv(os.path.join(OUT, "bootstrap.csv"), index=False)
    verdict = []
    for _, r in t.iterrows():
        verdict.append({"window_start": int(r["window_start"]), "status": r["status"],
                        "S_persona": float(r["S_persona"]), "S_persona_ci": [float(r["S_persona_lo"]), float(r["S_persona_hi"])],
                        "S_directive": float(r["S_directive"]), "S_directive_ci": [float(r["S_directive_lo"]), float(r["S_directive_hi"])],
                        "directive_interval_covers_0": bool(r["S_directive_lo"] <= 0.0),
                        "persona_interval_excludes_0": bool(r["S_persona_lo"] > 0.0)})
    doc = {"n_boot": n_boot, "seconds": time.time() - t0, "windows": verdict,
           "cv_groups": "the original seed of each resampled copy (evaluation/salience._boot_frame; addendum 18)",
           "note": ("the shares are sums of max(permutation importance, 0), so a share cannot be negative and its lower "
                    "percentile reaches 0 only if at least 2.5 % of refits give it exactly 0")}
    json.dump(doc, open(os.path.join(OUT, "bootstrap.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(doc, indent=1))
    return doc


def _leak_fit(args):
    from evaluation.salience import surrogate_shares
    dw, pick, refit_seed, variant, b = args
    parts = []
    for j, s in enumerate(pick):
        part = dw[dw["Seed"] == s].copy()
        part["Seed"] = f"{s}#{j}" if variant == "relabelled (as run)" else s
        parts.append(part)
    t0 = time.time()
    r = surrogate_shares(pd.concat(parts, ignore_index=True), include_state=False, seed=refit_seed)
    return {"b": b, "variant": variant, "unique_seeds": len(set(pick)), "S_persona": r["S_persona"],
            "S_directive": r["S_directive"], "S_market": r["S_market"], "r2": r["r2"], "seconds": time.time() - t0}


def stage_leak_diagnostic(workers: int):
    """UNREGISTERED (PREREG_PHASE_8_ADDENDUM.md 18): the measurement that located the fold leak.  The first bootstrap
    run's first 12 resamples of window 1 (seed 0, drawn in loop order), each refitted with the default surrogate twice:
    copies relabelled `s#j` as that run did (so copies of a seed fall in different folds), and copies left under their
    original seed (one cross-validation group).  It builds its frames itself, so the fix in `_boot_frame` does not
    change it.  -> e8_4/bootstrap_leak_diagnostic.csv"""
    from concurrent.futures import ProcessPoolExecutor
    from evaluation.salience import _init_threads
    d = frame("B_common_start_with_references", np.random.default_rng(84))
    dw = d[(d.Day >= 1) & (d.Day < 26)]
    rng = np.random.default_rng(0)
    seeds = np.array(sorted(dw["Seed"].unique(), key=str), dtype=object)
    picks = [rng.choice(seeds, len(seeds), replace=True) for _ in range(12)]
    tasks = [(dw, picks[b], b, v, b) for b in range(12) for v in ("relabelled (as run)", "copies in one CV group")]
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_threads) as ex:
        rows = list(ex.map(_leak_fit, tasks))
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(OUT, "bootstrap_leak_diagnostic.csv"), index=False)
    print(t.groupby("variant")[["S_persona", "S_directive", "r2"]].agg(["median", "min", "max"]).to_string())


def write_report(ident: dict):
    os.makedirs(OUT, exist_ok=True)
    json.dump(ident, open(os.path.join(OUT, "identification.json"), "w", encoding="utf-8"), indent=1)
    L = ["# E8.4 — are the salience shares identified? The identification condition on each design", "",
         "| design | runs | start designs | rank P / D / S / all | (i) P, D vary | (ii) no block in span | (iii) common start | (iv) references | R² of S on P, D | max canonical corr P~S | P~D | **identified** | identified as registered (addendum 10) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, c in ident.items():
        rk = c["ranks"]; cc = c["max_canonical_corr"]
        L.append(f"| {name} | {c['n_runs']} | {', '.join(c['start_designs'])} | {rk['persona']} / {rk['directive']} / {rk['start']} / {rk['all']} | "
                 f"{'yes' if c['clauses']['i'] else '**no**'} | {'yes' if c['clauses']['ii'] else '**no**'} | "
                 f"{'yes' if c['clauses']['iii'] else '**no**'} | {'yes' if c['clauses']['iv'] else '**no**'} | "
                 f"{c['r2_block_on_others'].get('start', float('nan')):.3f} | {cc.get('persona~start', float('nan')):.3f} | "
                 f"{cc.get('persona~directive', float('nan')):.3f} | **{'yes' if c['identified'] else 'NO'}** | "
                 f"{'yes' if c.get('identified_as_registered') else 'no'} |")
    with open(os.path.join(OUT, "identification.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="pilot,synthetic,bootstrap")
    ap.add_argument("--n-boot", type=int, default=200)
    ap.add_argument("--workers", type=int, default=7)
    a = ap.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)
    stages = [s.strip() for s in a.stages.split(",") if s.strip()]
    ident = {}
    p = os.path.join(OUT, "identification.json")
    if os.path.exists(p):
        ident = json.load(open(p, encoding="utf-8"))
    if "pilot" in stages:
        ident.update(stage_pilot())
    if "synthetic" in stages:
        ident.update(stage_synthetic(a.workers))
    if "pilot" in stages or "synthetic" in stages:
        write_report(ident)
    if "bootstrap" in stages:
        stage_bootstrap(a.n_boot, a.workers)
    if "leak_diagnostic" in stages:
        stage_leak_diagnostic(a.workers)


if __name__ == "__main__":
    main()
