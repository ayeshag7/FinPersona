"""
E5.7(c) -- the onset-detection audit per field, with a label-permutation null (PREREG_PHASE_5.md section 10c; REV-11b).

    python -m tools.phase5.e5_7c_onset --out DIR [--label NAME] [--overrides JSON] [--seeds 200] [--workers 3]

200 crash seeds (delta 0.70, seeds 410000+) and 200 bull-trap seeds (411000+), `schedule_mode` pinned to the
deployed v21 and the observable designs pinned by `--overrides` (P4-19).  Transitions: crash calm->deterioration,
deterioration->panic, panic->stabilisation; bull-trap calm->mania, mania->blow-off, blow-off->post-top.  Labels: 1 on
days tau-3..tau+3; 0 on days at least 10 days from every transition; other days excluded.  Per field the day score is
|d field| for bounded/signed fields and |d log field| for positive level fields (undefined days excluded).  The
price-derived reference is the best AUC over {|r_t|, |ret_5|, |d log sqrt(252 fc_t)| with fc the IV filter's own
past-only forecast, |d RSI14|, |d log(P/SMA20)|}.  Statistic: dAUC_f = AUC_f - AUC_ref, pooled day-level.  Null: 500
per-path circular shifts of the label vector (E3.5's construction; a seed-label permutation is degenerate when paths
share a day axis, P4-29).  Rule: dAUC_f <= the null's 95th percentile for every field and transition.  Timing error:
per path, the day of the field's maximum score within [tau-10, tau+10] minus tau (median, IQR).

Output: <out>/onset.{json,md}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

from tools.phase5.common import GEN, pin_state  # noqa: E402

SEED_CRASH, SEED_BULL = 410000, 411000
N_PERM = 500
SEED_PERM = 412001
TRANS = {"crash": [("calm", "deterioration"), ("deterioration", "panic"), ("panic", "stabilisation")],
         "bull_trap": [("calm", "mania"), ("mania", "blow-off"), ("blow-off", "post-top")]}
LOG_FIELDS = ("volume", "implied_volatility", "reported_PE", "dividend_yield", "analyst_fair_value", "SMA20", "SMA50")
REF = ("ref_abs_r", "ref_abs_ret5", "ref_dlog_rvfc", "ref_dRSI", "ref_dlogPSMA20")


def _path(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    from tools.phase5.e5_panels import fast_panel
    scenario, seed, overrides = args
    kw = {"crash_discount": 0.70} if scenario == "crash" else {}
    env = SyntheticMarketEnv(scenario, 200, seed, config={"schedule_mode": "v21", "obs_overrides": overrides}, **kw)
    f = fast_panel(env, scenario, seed)
    d = env.data[env.data["asset"] == 0].reset_index(drop=True)
    ph = f["phase"].to_numpy(object)
    P = f["P"].to_numpy(float)
    r = np.concatenate([[np.nan], np.diff(np.log(P))])
    scores = {}
    scores["ref_abs_r"] = np.abs(r)
    lp = np.log(P)
    scores["ref_abs_ret5"] = np.abs(np.concatenate([np.full(5, np.nan), lp[5:] - lp[:-5]]))
    fc = d["iv_fc21"].to_numpy(float) if "iv_fc21" in d else np.full(len(P), np.nan)
    scores["ref_dlog_rvfc"] = np.abs(np.concatenate([[np.nan], np.diff(np.log(np.sqrt(252.0 * fc)))]))
    scores["ref_dRSI"] = np.abs(np.concatenate([[np.nan], np.diff(f["RSI14"].to_numpy(float))]))
    scores["ref_dlogPSMA20"] = np.abs(np.concatenate([[np.nan], np.diff(np.log(f["price"].to_numpy(float) / f["SMA20"].to_numpy(float)))]))
    for c in f.columns:
        if c in ("scenario", "seed", "day", "phase", "V", "P", "macro", "x", "price"):
            continue
        v = f[c].to_numpy(float)
        if c in LOG_FIELDS:
            with np.errstate(divide="ignore", invalid="ignore"):
                v = np.log(np.where(v > 0, v, np.nan))
        elif c in ("MACD", "MACD_signal"):
            v = v / f["price"].to_numpy(float)
        scores[c] = np.abs(np.concatenate([[np.nan], np.diff(v)]))
    # labels per transition
    labs = {}
    taus = {}
    for a, b in TRANS[scenario]:
        idx = np.where((ph[:-1] == a) & (ph[1:] == b))[0]
        taus[f"{a}->{b}"] = int(idx[0]) + 1 if len(idx) else None
    all_t = [t for t in taus.values() if t is not None]
    for key, tau in taus.items():
        lab = np.full(len(P), -1, dtype=np.int8)
        far = np.ones(len(P), bool)
        for t in all_t:
            far[max(t - 9, 0):t + 10] = False
        lab[far] = 0
        if tau is not None:
            lab[max(tau - 3, 0):tau + 4] = 1
        labs[key] = lab
    return {"seed": seed, "scenario": scenario, "scores": {k: v.astype(np.float32) for k, v in scores.items()},
            "labs": labs, "taus": taus}


def auc_rank(scores, labels):
    """Mann-Whitney AUC over rows with finite scores and labels in {0, 1}."""
    ok = np.isfinite(scores) & (labels >= 0)
    s, y = scores[ok], labels[ok]
    n1 = int(y.sum()); n0 = len(y) - n1
    if n1 < 5 or n0 < 5:
        return np.nan
    from scipy.stats import rankdata
    rk = rankdata(s)
    return float((rk[y == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    ap.add_argument("--overrides", default="{}")
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--n-perm", type=int, default=N_PERM)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(a.out, exist_ok=True)
    overrides = json.loads(a.overrides) if not os.path.exists(a.overrides) else json.load(open(a.overrides, encoding="utf-8"))
    state = pin_state()
    jobs = [("crash", s, overrides) for s in range(SEED_CRASH, SEED_CRASH + a.seeds)] + \
           [("bull_trap", s, overrides) for s in range(SEED_BULL, SEED_BULL + a.seeds)]
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        rows = list(ex.map(_path, jobs, chunksize=4))
    print(f"[paths] {len(rows)} generated in {time.time() - t0:.0f} s", flush=True)
    rng = np.random.default_rng(SEED_PERM)
    res = {"what": "E5.7(c): onset-detection audit per field with a circular-shift label null (PREREG section 10c)",
           "label": a.label, "overrides": overrides, "state": state, "seeds": {"crash": [SEED_CRASH, SEED_CRASH + a.seeds - 1],
           "bull_trap": [SEED_BULL, SEED_BULL + a.seeds - 1]}, "n_perm": a.n_perm, "reference_set": list(REF),
           "transitions": {}}
    for scenario, trans in TRANS.items():
        R = [r for r in rows if r["scenario"] == scenario]
        fields = sorted(set(k for r in R for k in r["scores"]))
        for aa, bb in trans:
            key = f"{aa}->{bb}"
            lab = np.concatenate([r["labs"][key] for r in R])
            n_paths_with = sum(1 for r in R if r["taus"][key] is not None)
            if n_paths_with < 20:
                res["transitions"][f"{scenario}:{key}"] = {"n_paths_with_transition": n_paths_with, "skipped": True}
                continue
            S = {f: np.concatenate([r["scores"][f] if f in r["scores"] else np.full(len(r["labs"][key]), np.nan) for r in R])
                 for f in fields}
            aucs = {f: auc_rank(S[f], lab) for f in fields}
            ref_best = max((aucs[f] for f in REF if np.isfinite(aucs[f])), default=np.nan)
            ref_name = max((f for f in REF if np.isfinite(aucs[f])), key=lambda f: aucs[f], default=None)
            # null: per-path circular shift of the label vector, the same shift applied to every field's AUC
            null = {f: [] for f in fields if not f.startswith("ref_")}
            lens = [len(r["labs"][key]) for r in R]
            for _ in range(a.n_perm):
                shifted = np.concatenate([np.roll(r["labs"][key], int(rng.integers(10, L - 10))) for r, L in zip(R, lens)])
                ref_null = max((auc_rank(S[f], shifted) for f in REF if np.isfinite(aucs[f])), default=np.nan)
                for f in null:
                    null[f].append(auc_rank(S[f], shifted) - ref_null)
            out = {"n_paths_with_transition": n_paths_with, "n_pos_days": int((lab == 1).sum()), "n_neg_days": int((lab == 0).sum()),
                   "auc_ref_best": ref_best, "ref_best_name": ref_name, "auc_ref_all": {f: aucs[f] for f in REF}, "fields": {}}
            for f in null:
                nv = np.asarray([v for v in null[f] if np.isfinite(v)])
                d_auc = aucs[f] - ref_best if np.isfinite(aucs[f]) else np.nan
                p95 = float(np.percentile(nv, 95)) if len(nv) else np.nan
                # timing error
                errs = []
                for r in R:
                    tau = r["taus"][key]
                    if tau is None or f not in r["scores"]:
                        continue
                    sc = r["scores"][f]
                    lo, hi = max(tau - 10, 1), min(tau + 10, len(sc) - 1)
                    seg = sc[lo:hi + 1]
                    if np.isfinite(seg).sum() < 5:
                        continue
                    errs.append(int(lo + np.nanargmax(seg)) - tau)
                out["fields"][f] = {"auc": aucs[f], "delta_auc": d_auc, "null_p95": p95, "null_n": int(len(nv)),
                                    "pass": bool(np.isfinite(d_auc) and d_auc <= p95),
                                    "timing_error_median": float(np.median(errs)) if errs else None,
                                    "timing_error_iqr": [float(np.percentile(errs, 25)), float(np.percentile(errs, 75))] if errs else None}
            res["transitions"][f"{scenario}:{key}"] = out
            worst = max(((f, v["delta_auc"] - v["null_p95"]) for f, v in out["fields"].items() if np.isfinite(v["delta_auc"])),
                        key=lambda t: t[1], default=(None, None))
            print(f"    {scenario:9s} {key:28s} n={n_paths_with:3d} ref {ref_best:.3f} ({ref_name}); worst field {worst[0]} "
                  f"excess {worst[1]:+.4f} -> {'ALL PASS' if all(v['pass'] for v in out['fields'].values()) else 'FAIL: ' + ', '.join(f for f, v in out['fields'].items() if not v['pass'])}",
                  flush=True)
    fails = [(k, f) for k, t in res["transitions"].items() if not t.get("skipped") for f, v in t["fields"].items() if not v["pass"]]
    res["verdict"] = {"all_pass": not fails, "failures": fails,
                      "rule": "dAUC_f <= null p95 for every field and transition (PREREG section 10c, as registered)"}
    # PREREG_PHASE_5_ADDENDUM section 1.3: the price-derived fields belong on the reference side; the rule applies
    # to the NON-PRICE fields, against the best of the registered scores and the price-derived fields' own scores.
    PRICE_DERIVED = ("SMA20", "SMA50", "MACD", "MACD_signal", "RSI14", "trend_strength", "trend_regime")
    fails_np = []
    for k, t in res["transitions"].items():
        if t.get("skipped"):
            continue
        ref2 = max([t["auc_ref_best"]] + [t["fields"][f]["auc"] for f in PRICE_DERIVED
                                          if f in t["fields"] and np.isfinite(t["fields"][f]["auc"])])
        t["auc_ref_extended"] = float(ref2)
        for f, v in t["fields"].items():
            if f in PRICE_DERIVED or not np.isfinite(v["delta_auc"]):
                v["pass_nonprice_rule"] = None
                continue
            d2 = v["auc"] - ref2
            v["delta_auc_extended"] = float(d2)
            v["pass_nonprice_rule"] = bool(d2 <= v["null_p95"])
            if not v["pass_nonprice_rule"]:
                fails_np.append((k, f))
    res["verdict_nonprice"] = {"all_pass": not fails_np, "failures": fails_np,
                               "rule": "ADDENDUM section 1.3: non-price fields vs the best of the registered scores and the "
                                       "price-derived fields' own scores; dAUC <= null p95"}
    res["seconds"] = round(time.time() - t0)
    json.dump(res, open(os.path.join(a.out, "onset.json"), "w", encoding="utf-8"), indent=1, default=str)
    L = [f"# E5.7(c) onset-detection audit -- {a.label or os.path.basename(a.out)}", "",
         f"{a.seeds} crash + {a.seeds} bull-trap seeds, schedule pinned v21, overrides {json.dumps(overrides)}; "
         f"{a.n_perm} circular-shift null draws. Rule: dAUC (field - best price-derived reference) <= null p95.", ""]
    for k, t in res["transitions"].items():
        if t.get("skipped"):
            L += [f"## {k}: skipped ({t['n_paths_with_transition']} paths carry the transition)", ""]
            continue
        L += [f"## {k} (n = {t['n_paths_with_transition']} paths; {t['n_pos_days']} positive / {t['n_neg_days']} negative days; "
              f"reference AUC {t['auc_ref_best']:.3f} = {t['ref_best_name']})", "",
              "| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |", "|---|---|---|---|---|---|"]
        for f, v in sorted(t["fields"].items(), key=lambda kv: -(kv[1]["delta_auc"] if np.isfinite(kv[1]["delta_auc"]) else -9)):
            te = f"{v['timing_error_median']:+.0f} {v['timing_error_iqr']}" if v["timing_error_median"] is not None else "n/a"
            L.append(f"| {f} | {v['auc']:.3f} | {v['delta_auc']:+.4f} | {v['null_p95']:+.4f} | {'yes' if v['pass'] else '**NO**'} | {te} |")
        L.append("")
    L += [f"**Verdict (as registered):** {'every field passes at every transition' if not fails else 'FAILURES: ' + str(fails)}.", "",
          f"**Verdict (non-price fields, ADDENDUM 1.3):** {'every non-price field passes at every transition' if not fails_np else 'FAILURES: ' + str(fails_np)}.", ""]
    with open(os.path.join(a.out, "onset.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"wrote {a.out}/onset.json in {res['seconds']} s; all pass (registered): {not fails}; non-price rule: {not fails_np}", flush=True)


if __name__ == "__main__":
    main()
