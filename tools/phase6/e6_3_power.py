"""
v2.1 Phase 6 -- E6.3: the power analysis per checklist item, from a stored panel's cross-seed variance.

Plan Section 10.2 (E6.3) and Appendix A. The seed count per item comes from the cross-seed variance of the
item's per-seed statistic in a pilot; the plan says "a 50-seed pilot". No new generator run is needed for
the pilot (rule 1: the pre-registration exists before the first run): the Phase-5 hand-over panel
(`_panels/sep_phase5_after.pkl`, 1,600 paths = 200 seeds x 8 path designs) already carries every per-seed
statistic the checklist computes, and it is the state the criteria will be applied to.

Two of Appendix A's rules are used, exactly as written there:

  share-type   n = (z_0.95 sqrt(p0 q0) + z_0.80 sqrt(p1 q1))^2 / (p1 - p0)^2
               one-sided alpha 0.05, power 0.80; p0 the criterion's share, p1 the pilot's observed share
               (when p1 is on the criterion's own side the test is against the nearest failing share the
               plan names, 0.75 for a 0.80 criterion, so that the count is never zero by construction)
  median-type  n such that 1.96 * 1.25 * s / sqrt(n) <= w / 5
               s the cross-seed sd from the pilot, w the width of the acceptance band, 1.25 = sqrt(pi/2)

The band width w depends on the criterion, and Phase 6 has two candidate bands per item: the v2 numeric
band (REG-14 A) and the P10-P90 reference band (REG-14 C, from E6.1). The tool therefore takes a bands file
and is run once per criterion set; the pre-registered seed count per item is the MAXIMUM over the criteria
used (REG-14's rule).

Every per-seed statistic is computed with the checklist's own helpers (`evaluation.stylized_facts`) and the
checklist's own masks, so that the pilot variance is the variance of the number the criterion will see.

Usage:
    python -u tools/phase6/e6_3_power.py --panel docs/env_v2/generated/v2_1/_panels/sep_phase5_after.pkl \
        --out docs/env_v2/generated/v2_1/e6_3 [--bands v2|<json>]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

from evaluation.stylized_facts import (  # noqa: E402
    CALM, acf, arch_lm_p, garch_fit, hill_index, ljung_box_p, mdd,
)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT_DEFAULT = os.path.join(GEN, "e6_3")
PANEL_DEFAULT = os.path.join(GEN, "_panels", "sep_phase5_after.pkl")
Z95, Z80 = 1.6448536269514722, 0.8416212335729143

# The v2 criteria, item by item, as `evaluation/stylized_facts.py` states them.  A "share" row is a share-of-seeds
# criterion (p0 = its threshold); a "band" row is a median-in-[lo, hi] criterion (w = hi - lo).  A criterion with
# one open end has no finite width; Appendix A's median rule needs one, so the open end is closed at the pilot's
# own P05/P95 -- and that is recorded, not hidden.
V2_CRITERIA = {
    "item1_lb_p_share":      {"item": 1, "kind": "share", "p0": 0.80, "stat": "lb_p_r_calm", "cond": "> 0.05"},
    "item1_abs_acf1":        {"item": 1, "kind": "band",  "lo": -0.15, "hi": 0.15, "stat": "abs_acf1_r_calm"},
    "item2_kurt_share":      {"item": 2, "kind": "share", "p0": 0.80, "stat": "kurtosis", "cond": "> 1.5"},
    "item2_hill":            {"item": 2, "kind": "band",  "lo": 2.5, "hi": 5.0, "stat": "hill"},
    "item3_lb_absr_share":   {"item": 3, "kind": "share", "p0": 0.80, "stat": "lb_p_absr", "cond": "< 0.01"},
    "item3_acf1_absr":       {"item": 3, "kind": "band",  "lo": 0.10, "hi": 0.40, "stat": "acf1_absr"},
    "item5_persistence":     {"item": 5, "kind": "band",  "lo": 0.90, "hi": 0.995, "stat": "garch_persistence"},
    "item6_lev_share":       {"item": 6, "kind": "share", "p0": 0.70, "stat": "leverage_corr", "cond": "< 0"},
    "item6_gamma":           {"item": 6, "kind": "band",  "lo": 0.0, "hi": None, "stat": "gjr_gamma"},
    "item7_spearman":        {"item": 7, "kind": "band",  "lo": 0.20, "hi": 0.50, "stat": "volume_absr_spearman"},
    "item7_logvol_ac1":      {"item": 7, "kind": "band",  "lo": 0.50, "hi": 0.80, "stat": "logvolume_acf1"},
    "item7_shapiro_share":   {"item": 7, "kind": "share", "p0": 0.50, "stat": "logvolume_shapiro_p", "cond": "> 0.01"},
    "item8_skew":            {"item": 8, "kind": "band",  "lo": None, "hi": 0.0, "stat": "skew", "scenario": "crash"},
    "item8_worst_share":     {"item": 8, "kind": "share", "p0": 0.70, "stat": "worst_gt_best", "cond": "== 1", "scenario": "crash"},
    "item9_acf1_x":          {"item": 9, "kind": "band",  "lo": 0.98, "hi": None, "stat": "acf1_x_calm"},
    "item9_sd_x":            {"item": 9, "kind": "band",  "lo": 0.08, "hi": 0.20, "stat": "sd_x_calm"},
    "item12_sent_acf1":      {"item": 12, "kind": "band", "lo": 0.70, "hi": 0.90, "stat": "sent_acf1"},
    "item12_sent_corr":      {"item": 12, "kind": "band", "lo": 0.25, "hi": 0.55, "stat": "sent_corr_r"},
    "item13_iv_calm":        {"item": 13, "kind": "band", "lo": 25.0, "hi": 35.0, "stat": "iv_calm_mean"},
    "item13_iv_rv_corr":     {"item": 13, "kind": "band", "lo": 0.40, "hi": 0.80, "stat": "iv_rv20_corr"},
    "item20_mdd":            {"item": 20, "kind": "band", "lo": -0.65, "hi": -0.20, "stat": "mdd", "scenario": "crash"},
    "item20_calm_sigma":     {"item": 20, "kind": "band", "lo": 0.014, "hi": 0.022, "stat": "calm_sigma", "scenario": "flat"},
    "item20_worst_panic":    {"item": 20, "kind": "band", "lo": -0.15, "hi": -0.06, "stat": "worst_panic_day", "scenario": "crash"},
}


# ------------------------------------------------------------------------------------- per-path statistics
def path_stats(g: pd.DataFrame) -> Dict[str, float]:
    """Every per-seed quantity the checklist items reduce, with the items' own masks."""
    g = g.sort_values("day")
    P = g["P"].to_numpy(float)
    r_full = np.concatenate([[np.nan], np.diff(np.log(P))])
    ph = g["phase"].astype(str).to_numpy()
    calm = np.isin(ph, list(CALM))
    r = r_full[1:]
    a = np.abs(r)
    out: Dict[str, float] = {}
    rc = r_full[calm]; rc = rc[np.isfinite(rc)]
    # item 1
    out["lb_p_r_calm"] = ljung_box_p(rc, 10) if len(rc) > 30 else np.nan
    out["abs_acf1_r_calm"] = abs(acf(rc, 1)) if len(rc) > 30 else np.nan
    # item 2
    out["kurtosis"] = float(stats.kurtosis(r)); out["jb_p"] = float(stats.jarque_bera(r)[1]); out["hill"] = hill_index(r)
    # item 3
    out["lb_p_absr"] = ljung_box_p(a, 10); out["lb_p_r2"] = ljung_box_p(r ** 2, 10)
    out["arch_lm_p"] = arch_lm_p(r, 5); out["acf1_absr"] = acf(a, 1)
    # items 5, 6
    al, _, be = garch_fit(r); out["garch_persistence"] = al + be if (al == al and be == be) else np.nan
    _, gam, _ = garch_fit(r, o=1); out["gjr_gamma"] = gam
    out["leverage_corr"] = float(np.corrcoef(r[:-1], a[1:])[0, 1])
    # item 7
    v = g["volume"].to_numpy(float)[1:]
    ok = np.isfinite(v) & (v > 0)
    out["volume_absr_spearman"] = float(stats.spearmanr(v[ok], a[ok])[0]) if ok.sum() > 30 else np.nan
    lv = np.log(g["volume"].to_numpy(float)); lv = lv[np.isfinite(lv)]
    out["logvolume_acf1"] = acf(lv, 1); out["logvolume_shapiro_p"] = float(stats.shapiro(lv)[1]) if len(lv) > 3 else np.nan
    # item 8
    out["skew"] = float(stats.skew(r)); out["worst_gt_best"] = float(abs(r.min()) > abs(r.max()))
    # item 9 (calm x)
    xc = g["x"].to_numpy(float)[calm]
    if len(xc) > 30:
        a1 = acf(xc, 1); out["acf1_x_calm"] = a1
        out["half_life_x_calm"] = (-math.log(2) / math.log(a1)) if 0 < a1 < 1 else np.inf
        out["sd_x_calm"] = float(np.std(xc))
    else:
        out["acf1_x_calm"] = out["half_life_x_calm"] = out["sd_x_calm"] = np.nan
    # item 12
    s = g["news_sentiment"].to_numpy(float)
    out["sent_acf1"] = acf(s, 1)
    out["sent_corr_r"] = float(np.corrcoef(s[1:], r)[0, 1]) if np.std(s[1:]) > 0 else np.nan
    # item 13
    iv = g["implied_volatility"].to_numpy(float)
    n = len(r_full)
    rv = np.array([np.std(r_full[i + 1:i + 21]) * np.sqrt(252) * 100 if i + 21 <= n else np.nan for i in range(n)])
    okv = np.isfinite(rv) & np.isfinite(iv)
    out["iv_rv20_corr"] = float(np.corrcoef(iv[okv], rv[okv])[0, 1]) if okv.sum() > 30 and np.std(iv[okv]) > 0 else np.nan
    c = calm & okv
    out["iv_calm_mean"] = float(iv[c].mean()) if c.sum() > 10 else np.nan
    # items 10 / 20
    out["mdd"] = mdd(P)
    out["calm_sigma"] = float(np.nanstd(r_full[calm], ddof=1)) if calm.sum() > 30 else np.nan
    pz = ph == "panic"
    out["worst_panic_day"] = float(np.nanmin(r_full[pz])) if pz.sum() > 0 else np.nan
    return out


def _one(args):
    key, frame = args
    try:
        s = path_stats(frame)
    except Exception as e:                       # recorded, never silently dropped
        s = {"error": type(e).__name__}
    s["scenario"], s["seed"] = key
    return s


# ------------------------------------------------------------------------------------- Appendix A
def n_share(p0: float, p1: float) -> Optional[int]:
    if p1 is None or not np.isfinite(p1) or abs(p1 - p0) < 1e-9:
        return None
    q0, q1 = 1 - p0, 1 - p1
    return int(math.ceil((Z95 * math.sqrt(p0 * q0) + Z80 * math.sqrt(p1 * q1)) ** 2 / (p1 - p0) ** 2))


def n_median(s: float, w: float) -> Optional[int]:
    if not (np.isfinite(s) and np.isfinite(w)) or w <= 0:
        return None
    return int(math.ceil((1.96 * 1.25 * s / (w / 5.0)) ** 2))


def analyse(df: pd.DataFrame, criteria: Dict, bands_label: str) -> List[Dict]:
    rows = []
    for name, c in criteria.items():
        sc = c.get("scenario")
        sub = df if sc is None else df[df["scenario"] == sc]
        v = pd.to_numeric(sub[c["stat"]], errors="coerce").to_numpy(float)
        v = v[np.isfinite(v)]
        row = {"criterion": name, "item": c["item"], "statistic": c["stat"], "kind": c["kind"],
               "scenario": sc or "all", "n_pilot": int(v.size), "bands": bands_label}
        if v.size == 0:
            rows.append(row); continue
        if c["kind"] == "share":
            cond = c["cond"]
            thr = float(cond.split()[-1])
            op = cond.split()[0]
            hit = {">": v > thr, "<": v < thr, "==": v == thr}[op]
            p_obs = float(hit.mean())
            row.update({"p0": c["p0"], "p_observed": p_obs,
                        "p1_used": p_obs if (p_obs < c["p0"]) else round(c["p0"] - 0.05, 3),
                        "note": ("observed share below the criterion: power to detect the observed shortfall" if p_obs < c["p0"]
                                 else "observed share meets the criterion: n to detect a 5 pp shortfall (the plan's p1 = 0.75 for 0.80)")})
            row["n_required"] = n_share(c["p0"], row["p1_used"])
        else:
            lo, hi = c.get("lo"), c.get("hi")
            s = float(np.std(v, ddof=1))
            med = float(np.median(v))
            one_sided = (lo is None) or (hi is None)
            edges = [e for e in (lo, hi) if e is not None]
            # distance from the pilot median to the nearest band edge: the verdict is decidable at n when the
            # median's half-width at n is below it (the CI then lies wholly inside or wholly outside the band)
            dist = float(min(abs(med - e) for e in edges)) if edges else np.nan
            row.update({"lo": lo, "hi": hi, "one_sided": one_sided, "cross_seed_sd": s, "median": med,
                        "median_inside": bool((lo is None or med >= lo) and (hi is None or med <= hi)),
                        "distance_to_nearest_edge": dist})
            if one_sided:
                # Appendix A's median rule needs a band width; a one-sided criterion has none, so its n is the
                # count at which the median's half-width falls below the distance to the threshold
                row.update({"width": None, "n_required": n_median(s, 5.0 * dist) if dist > 0 else None,
                            "n_required_rule": "one-sided: 1.96*1.25*s/sqrt(n) <= |median - threshold|"})
            else:
                w = hi - lo
                row.update({"width": w, "n_required": n_median(s, w),
                            "n_required_rule": "Appendix A: 1.96*1.25*s/sqrt(n) <= w/5"})
        rows.append(row)
    return rows


def achieved(rows: List[Dict], n_planned: int) -> List[Dict]:
    """The achieved precision at the planned n: the median's half-width 1.96*1.25*s/sqrt(n) against w/5, and the
    share test's power at n_planned (normal approximation, the same formula solved for power)."""
    for r in rows:
        if r.get("kind") == "band" and r.get("cross_seed_sd") is not None:
            hw = 1.96 * 1.25 * r["cross_seed_sd"] / math.sqrt(n_planned)
            r["halfwidth_at_planned_n"] = hw
            r["target_halfwidth"] = r["width"] / 5.0 if r.get("width") else None
            # precision: Appendix A's w/5 target (closed bands only); verdict: the median's CI at n clears the nearest edge
            r["precision_met_at_planned_n"] = bool(hw <= r["target_halfwidth"]) if r["target_halfwidth"] else None
            r["verdict_decidable_at_planned_n"] = bool(hw < r["distance_to_nearest_edge"]) if np.isfinite(r.get("distance_to_nearest_edge", np.nan)) else None
            r["decidable_at_planned_n"] = r["verdict_decidable_at_planned_n"]
        elif r.get("kind") == "share" and r.get("p1_used") is not None:
            p0, p1, pobs = r["p0"], r["p1_used"], r["p_observed"]
            # power of Appendix A's design test at n (the 5-pp shortfall, or the observed shortfall)
            se0 = math.sqrt(p0 * (1 - p0) / n_planned); se1 = math.sqrt(p1 * (1 - p1) / n_planned)
            z = (abs(p1 - p0) - Z95 * se0) / se1 if se1 > 0 else float("inf")
            r["power_at_planned_n"] = float(stats.norm.cdf(z))
            # verdict decidability on THIS state: the observed share's Wilson interval at n excludes p0
            zz = 1.959963985; d = 1 + zz * zz / n_planned
            c = (pobs + zz * zz / (2 * n_planned)) / d
            hwv = zz * math.sqrt(pobs * (1 - pobs) / n_planned + zz * zz / (4 * n_planned * n_planned)) / d
            r["share_ci95_at_planned_n"] = [max(0.0, c - hwv), min(1.0, c + hwv)]
            r["verdict_decidable_at_planned_n"] = not (r["share_ci95_at_planned_n"][0] <= p0 <= r["share_ci95_at_planned_n"][1])
            r["decidable_at_planned_n"] = r["verdict_decidable_at_planned_n"]
        r["n_planned"] = n_planned
    return rows


def to_markdown(rows: List[Dict], meta: Dict) -> str:
    L = [f"# E6.3 — power analysis per checklist item (pilot: {meta['panel']})", "",
         f"{meta['n_paths']} paths ({meta['per_scenario']}); per-seed statistics with the checklist's own helpers and masks; "
         f"Appendix A's share and median rules; bands = **{meta['bands']}**; planned n = {meta['n_planned']} seeds per scenario.", "",
         "| criterion | item | scenario | kind | pilot n | observed | band / p0 | cross-seed sd | n required | at planned n |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if r["kind"] == "share":
            obs = f"share {r.get('p_observed', float('nan')):.3f}"
            band = f"p0 {r['p0']} (design p1 {r.get('p1_used')})"
            sd = "—"
            ci = r.get("share_ci95_at_planned_n")
            at = f"design power {r.get('power_at_planned_n', float('nan')):.2f}; share CI [{ci[0]:.3f}, {ci[1]:.3f}]" if ci else ""
        else:
            obs = f"median {r.get('median', float('nan')):.4g}"
            lo = "−∞" if r.get("lo") is None else f"{r['lo']:.4g}"; hi = "+∞" if r.get("hi") is None else f"{r['hi']:.4g}"
            band = f"[{lo}, {hi}]"
            sd = f"{r.get('cross_seed_sd', float('nan')):.4g}"
            tw = r.get("target_halfwidth")
            at = (f"half-width {r.get('halfwidth_at_planned_n', float('nan')):.4g} vs w/5 {tw:.4g}" if tw else
                  f"half-width {r.get('halfwidth_at_planned_n', float('nan')):.4g} (one-sided)") + \
                 f"; to edge {r.get('distance_to_nearest_edge', float('nan')):.4g}"
        dec = r.get("verdict_decidable_at_planned_n")
        at += " → " + ("**decidable**" if dec else ("undecidable" if dec is False else "—"))
        if r["kind"] == "band" and r.get("median_inside") is not None:
            at += " (" + ("inside" if r["median_inside"] else "OUTSIDE") + ")"
        L.append(f"| `{r['criterion']}` | {r['item']} | {r['scenario']} | {r['kind']} | {r['n_pilot']} | {obs} | {band} | {sd} | "
                 f"{r.get('n_required') if r.get('n_required') is not None else '—'} | {at} |")
    L += ["", f"**Maximum n required (Appendix A's precision rule, closed bands; the one-sided rule otherwise): {meta['max_n_required']}.** "
              "Two questions are answered per row: Appendix A's *design* n (the count at which the band's w/5 precision, or a "
              "5-pp share shortfall, is resolved) and whether the *verdict on this state* is decidable at the planned n (the "
              "median's or share's interval at n clears the nearest edge / p0). An item can be undecidable by the first and "
              "decidable by the second when the pilot sits far from the edge, and the reverse when it sits on it; the "
              "pre-registration's seed count is the maximum over the items it must decide.", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", default=PANEL_DEFAULT)
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--bands", default="v2", help="'v2' or a JSON file in V2_CRITERIA's shape (e.g. the E6.1 reference bands)")
    ap.add_argument("--n-planned", type=int, default=200)
    ap.add_argument("--n-jobs", type=int, default=max(1, (os.cpu_count() or 4) // 2))
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)

    cache = os.path.join(a.out, "per_path_stats.csv")
    if os.path.exists(cache) and os.path.getsize(cache) > 0:
        df = pd.read_csv(cache)
        print(f"per-path statistics: cached ({len(df)} paths)", flush=True)
    else:
        panel = pd.read_pickle(a.panel)
        t0 = time.time()
        jobs = [((sc, sd), g) for (sc, sd), g in panel.groupby(["scenario", "seed"], sort=False)]
        from joblib import Parallel, delayed
        from threadpoolctl import threadpool_limits
        with threadpool_limits(limits=2):
            rows = Parallel(n_jobs=a.n_jobs, backend="loky", verbose=5)(delayed(_one)(j) for j in jobs)
        df = pd.DataFrame(rows)
        df.to_csv(cache, index=False)
        print(f"per-path statistics: {len(df)} paths in {time.time() - t0:.0f}s", flush=True)

    if a.bands == "v2":
        criteria, label = V2_CRITERIA, "v2 numeric criteria (REG-14 A)"
    else:
        with open(a.bands, "r", encoding="utf-8") as fh:
            criteria = json.load(fh)
        label = os.path.relpath(a.bands, ROOT).replace("\\", "/")
    rows = achieved(analyse(df, criteria, label), a.n_planned)
    req = [r["n_required"] for r in rows if r.get("n_required") is not None]
    meta = {"panel": os.path.relpath(a.panel, ROOT).replace("\\", "/"), "n_paths": int(len(df)),
            "per_scenario": ", ".join(f"{k} {v}" for k, v in df.groupby("scenario").size().items()),
            "bands": label, "n_planned": a.n_planned, "max_n_required": int(max(req)) if req else None,
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    tag = "v2" if a.bands == "v2" else os.path.splitext(os.path.basename(a.bands))[0]
    with open(os.path.join(a.out, f"power_{tag}.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "rows": rows}, fh, indent=1, default=float)
    with open(os.path.join(a.out, f"power_{tag}.md"), "w", encoding="utf-8") as fh:
        fh.write(to_markdown(rows, meta))
    print(json.dumps(meta, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
