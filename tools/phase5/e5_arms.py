"""
The Phase-5 design arms (PREREG_PHASE_5.md sections 4-9): panels, per-arm statistics and the ablation launch.

    python -m tools.phase5.e5_arms --stage panels|stats|ablate [--blocks multiple,analyst,volume,sentiment,epsdiv]
                                   [--workers 3]

Every arm = the baseline (every block at its v2 design) with ONE block changed, so each block's contest is decided
on a like-for-like background; the winners are combined by apply_e5.py and measured again in the final ablation.
Post-hoc blocks (multiple, eps/dividend, analyst, volume) are rendered from one generation of the hidden path and
are therefore paired by construction; the sentiment arms and `b_pred = 0` re-simulate (paired by seed).

  panels   builds `_panels/sep_phase5_<arm>.pkl` for every arm of the requested blocks (tools/phase5/e5_panels.py)
  stats    per-arm statistics that need no model fit: E5.1's KS check (per-path median rendered P/E vs the EDGAR
           pooled cross-section truncated to the width; bootstrap upper limit of D), the n/m share, E5.5's item-12
           statistics (200-day ACF(1) of s, corr(s, r)) against the data's window references, E5.6's item-7 statistics
  ablate   launches tools/phase5/e5_7a_ablation.py per arm (add-one for the arm's own group), sequentially

Output: docs/env_v2/generated/v2_1/e5_arms/<arm>/{ablation.*}, e5_arms/stats.{json,md}
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

from tools.phase5.common import GEN, PANELS, pin_state, encode_nm  # noqa: E402
from tools.phase5.e5_params import sections, ANALYST_LIT_ANCHOR  # noqa: E402

OUT = os.path.join(GEN, "e5_arms")
PY = sys.executable
WIDTHS = ("P10-P90", "P25-P75", "P5-P95")
ANALYST_SDS = (0.30, 0.45, ANALYST_LIT_ANCHOR, 0.60)


def v2_all():
    return {s: {"design": "v2"} for s in ("multiple", "eps", "dividend", "analyst", "sentiment", "volume")}


def arms_for(blocks):
    """{arm name: {"obs_overrides": ..., "config": ..., "group": ..., "block": ...}}"""
    S = sections()          # every FIT section at its default design; arms pick the pieces they need
    arms = {}
    if "multiple" in blocks:
        for w in WIDTHS:
            for dsg in ("A", "B"):
                o = v2_all(); o["multiple"] = {**S["multiple"], "design": dsg, "width": w}
                arms[f"multiple_{dsg}_{w}"] = {"obs_overrides": o, "config": {}, "group": "VAL", "block": "multiple"}
    if "epsdiv" in blocks:
        o = v2_all(); o["eps"] = {**S["eps"], "design": "v21"}; o["dividend"] = {**S["dividend"], "design": "v21", "field": "shown"}
        arms["epsdiv_v21_shown"] = {"obs_overrides": o, "config": {}, "group": "VAL", "block": "epsdiv"}
        o2 = copy.deepcopy(o); o2["dividend"]["field"] = "hidden"
        arms["epsdiv_v21_hidden"] = {"obs_overrides": o2, "config": {}, "group": "VAL", "block": "epsdiv"}
    if "analyst" in blocks:
        for sd in ANALYST_SDS:
            o = v2_all(); o["analyst"] = {**S["analyst"], "design": "A", "sd": float(sd), "field": "shown"}
            arms[f"analyst_A_sd{sd:.3f}"] = {"obs_overrides": o, "config": {}, "group": "ANALYST", "block": "analyst"}
        o = v2_all(); o["analyst"] = {**S["analyst"], "design": "C", "sd": ANALYST_LIT_ANCHOR, "field": "shown"}
        arms["analyst_C"] = {"obs_overrides": o, "config": {}, "group": "ANALYST", "block": "analyst"}
    if "volume" in blocks:
        for dsg in ("A", "B"):
            o = v2_all(); o["volume"] = {**S["volume"], "design": dsg}
            arms[f"volume_{dsg}"] = {"obs_overrides": o, "config": {}, "group": "VOL", "block": "volume"}
    if "sentiment" in blocks:
        for name, dsg, link in (("sentiment_A", "A", "full"), ("sentiment_B_full", "B", "full"), ("sentiment_B_half", "B", "half"),
                                ("sentiment_C", "C", "full")):
            sec = sections({"sentiment": dsg, "sentiment_link": link})["sentiment"]
            o = v2_all(); o["sentiment"] = sec
            arms[name] = {"obs_overrides": o, "config": {}, "group": "SENT", "block": "sentiment"}
        arms["sentiment_v2_bpred0"] = {"obs_overrides": v2_all(), "config": {"b_pred": 0.0, "b_rev": 0.0}, "group": "SENT",
                                       "block": "sentiment"}
    return arms


def ks_upper(a, b, n_boot=200, seed=590001):
    rng = np.random.default_rng(seed)
    a = np.asarray(a, float); b = np.asarray(b, float)
    def ks(u, v):
        u = np.sort(u); v = np.sort(v); allv = np.concatenate([u, v])
        return float(np.max(np.abs(np.searchsorted(u, allv, "right") / len(u) - np.searchsorted(v, allv, "right") / len(v))))
    d0 = ks(a, b)
    draws = [ks(a[rng.integers(0, len(a), len(a))], b[rng.integers(0, len(b), len(b))]) for _ in range(n_boot)]
    return d0, float(np.percentile(draws, 97.5))


def stats_multiple(panel, width):
    e51 = json.load(open(os.path.join(GEN, "e5_1", "multiple.json"), encoding="utf-8"))
    pe_data = pd.read_csv(os.path.join(GEN, "e5_1", "pe_panel_monthly.csv"), index_col=0).stack().to_numpy(float)
    pe_data = pe_data[np.isfinite(pe_data) & (pe_data > 0)]
    lo, hi = e51["design_grids"]["A"][width]["truncation"]
    pe_data_w = pe_data[(pe_data >= lo) & (pe_data <= hi)]
    p = panel.copy()
    pe = p["reported_PE"].to_numpy(float)
    if "reported_PE_nm" in p:
        pe = np.where(p["reported_PE_nm"].to_numpy(float) > 0, np.nan, pe)
    p["pe"] = pe
    med = p.groupby(["scenario", "seed"])["pe"].median().dropna().to_numpy(float)
    d0, up = ks_upper(med, pe_data_w)
    return {"width": width, "truncation": [lo, hi], "n_paths": int(len(med)), "n_data": int(len(pe_data_w)),
            "ks_D": d0, "ks_upper95": up, "pass": bool(up < 0.10), "per_path_median_pe_p10_p50_p90": [float(np.percentile(med, q)) for q in (10, 50, 90)]}


def stats_sentiment(panel):
    e55 = json.load(open(os.path.join(GEN, "e5_5", "sentiment.json"), encoding="utf-8"))
    refs = e55["window_references_rule_i"]; refs_c = e55["aaii_weekly"]["window_refs_40w"]
    rows = []
    for (sc, sd), g in panel.groupby(["scenario", "seed"], sort=False):
        s = g["news_sentiment"].to_numpy(float); P = g["P"].to_numpy(float)
        r = np.diff(np.log(P)); s1 = s[1:]
        if s.std() < 1e-9:
            continue
        a1 = float(np.corrcoef(s[:-1], s[1:])[0, 1]); c0 = float(np.corrcoef(s1, r)[0, 1])
        # weekly statistics for design C's reference: 5-day blocks
        n5 = len(s) // 5
        sw = s[:n5 * 5].reshape(n5, 5)[:, -1]; rw = np.log(P[:n5 * 5].reshape(n5, 5)[:, -1] / np.r_[P[0], P[:n5 * 5].reshape(n5, 5)[:-1, -1]])
        aw = float(np.corrcoef(sw[:-1], sw[1:])[0, 1]) if sw.std() > 1e-9 else np.nan
        cw = float(np.corrcoef(sw, rw)[0, 1]) if sw.std() > 1e-9 else np.nan
        rows.append({"acf1": a1, "corr": c0, "acf1_w": aw, "corr_w": cw})
    df = pd.DataFrame(rows)
    rng = np.random.default_rng(590002)
    def med_ci(v):
        v = v[np.isfinite(v)]
        m = np.median(v[rng.integers(0, len(v), (500, len(v)))], axis=1)
        return {"median": float(np.median(v)), "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))], "n": int(len(v))}
    out = {"daily": {"acf1": med_ci(df["acf1"].to_numpy()), "corr_s_r": med_ci(df["corr"].to_numpy())},
           "weekly": {"acf1": med_ci(df["acf1_w"].to_numpy()), "corr_s_r": med_ci(df["corr_w"].to_numpy())},
           "reference_daily": refs, "reference_weekly": refs_c}
    def overlap(a, b):
        return not (a["ci95"][1] < b["ci95"][0] or b["ci95"][1] < a["ci95"][0])
    out["meets_i_daily"] = bool(overlap(out["daily"]["acf1"], refs["acf1_200d"]) and overlap(out["daily"]["corr_s_r"], refs["corr_s_r_200d"]))
    out["meets_i_weekly"] = bool(overlap(out["weekly"]["acf1"], refs_c["acf1_40w"]) and overlap(out["weekly"]["corr_s_r"], refs_c["corr_40w"]))
    return out


def stats_volume(panel):
    from scipy import stats as st
    rows = []
    for (sc, sd), g in panel.groupby(["scenario", "seed"], sort=False):
        v = g["volume"].to_numpy(float); P = g["P"].to_numpy(float); r = np.diff(np.log(P))
        lv = np.log(v)
        rows.append({"spearman": float(st.spearmanr(v[1:], np.abs(r))[0]), "acf1": float(np.corrcoef(lv[:-1], lv[1:])[0, 1]),
                     "shapiro_p": float(st.shapiro(lv)[1])})
    df = pd.DataFrame(rows)
    return {"median_spearman_vol_absr": float(df["spearman"].median()), "median_acf1_logvol": float(df["acf1"].median()),
            "share_shapiro_p_gt_0.01": float((df["shapiro_p"] > 0.01).mean()), "n_paths": int(len(df)),
            "v2_checklist_item7_bands": "corr 0.2-0.5; AC(1) 0.5-0.8; log-normality not rejected in >= 50 % (stipulated; Phase 6 re-derives)"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["panels", "stats", "ablate"])
    ap.add_argument("--blocks", default="multiple,epsdiv,analyst,volume,sentiment")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--only", default=None, help="comma list of arm names")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    blocks = [b.strip() for b in a.blocks.split(",")]
    arms = arms_for(blocks)
    if a.only:
        arms = {k: v for k, v in arms.items() if k in set(x.strip() for x in a.only.split(","))}
    state = pin_state()
    # arms.json is MERGED, not overwritten: one invocation per block must leave the other blocks' arms on record
    ap_ = os.path.join(OUT, "arms.json")
    prev = json.load(open(ap_, encoding="utf-8")) if os.path.exists(ap_) else {}
    prev.update({k: {kk: vv for kk, vv in v.items()} for k, v in arms.items()})
    json.dump(prev, open(ap_, "w", encoding="utf-8"), indent=1, default=str)
    if a.stage == "panels":
        from tools.phase5.e5_panels import build
        t0 = time.time()
        todo = {k: {"obs_overrides": v["obs_overrides"], "config": v["config"]} for k, v in arms.items()
                if not os.path.exists(os.path.join(PANELS, f"sep_phase5_{k}.pkl"))}
        print(f"[panels] {len(todo)} arms to build ({len(arms) - len(todo)} cached)", flush=True)
        if todo:
            build(todo, workers=a.workers)
        print(f"[panels] done in {time.time() - t0:.0f} s", flush=True)
    elif a.stage == "stats":
        jp = os.path.join(OUT, "stats.json")
        res = json.load(open(jp, encoding="utf-8")) if os.path.exists(jp) else {}
        for name, spec in arms.items():
            p = os.path.join(PANELS, f"sep_phase5_{name}.pkl")
            if not os.path.exists(p):
                print(f"    {name}: no panel"); continue
            panel = encode_nm(pd.read_pickle(p))
            r = {"block": spec["block"], "group": spec["group"], "n_rows": int(len(panel)),
                 "nm_share_days": float(panel["reported_PE_nm"].mean()) if "reported_PE_nm" in panel else 0.0}
            if spec["block"] == "multiple":
                r["ks"] = stats_multiple(panel, spec["obs_overrides"]["multiple"]["width"])
            if spec["block"] == "epsdiv":
                r["ks_P10-P90_v2k"] = stats_multiple(panel, "P10-P90")
                r["dividend_yield_zero_share"] = float((panel["dividend_yield"] <= 0).mean()) if "dividend_yield" in panel else None
            if spec["block"] == "sentiment":
                r["item12"] = stats_sentiment(panel)
            if spec["block"] == "volume":
                r["item7"] = stats_volume(panel)
            res[name] = r
            print(f"    {name}: {json.dumps({k: v for k, v in r.items() if k not in ('block', 'group')}, default=str)[:300]}", flush=True)
            json.dump(res, open(jp, "w", encoding="utf-8"), indent=1, default=str)
    elif a.stage == "ablate":
        for name, spec in arms.items():
            p = os.path.join(PANELS, f"sep_phase5_{name}.pkl")
            out = os.path.join(OUT, name)
            if os.path.exists(os.path.join(out, "ablation.json")) and "tables" in json.load(open(os.path.join(out, "ablation.json"), encoding="utf-8")):
                print(f"    {name}: ablation exists, skipped"); continue
            if not os.path.exists(p):
                print(f"    {name}: no panel"); continue
            cmd = [PY, "-u", "-m", "tools.phase5.e5_7a_ablation", "--panel", p, "--out", out, "--label", name,
                   "--stages", "add", "--groups", spec["group"], "--workers", str(a.workers),
                   "--reuse-base", os.path.join(GEN, "e5_7a", "baseline", "ablation.json")]
            print("[ablate] " + " ".join(cmd), flush=True)
            subprocess.run(cmd, cwd=ROOT, check=False)


if __name__ == "__main__":
    main()
