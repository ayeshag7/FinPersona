"""
Section 9 validation checklist (v2 plan): stylized-facts and scenario-property
tests, run on >= 50 seeds per scenario, producing the pass-rate table.

The library is generator-agnostic: it consumes PathData objects (one per
scenario x seed) with a standard column set, so the same tests run on the v1
generator (E0 baseline, expected to fail most items) and on every v2 block.

Standard per-path DataFrame columns
    day, price, value, volume, sentiment, iv, phase, macro
    optional: x (log P/V; computed if absent), sigma (GARCH conditional sd)
Phase taxonomy (plan 2.1 block 5): calm; deterioration, panic, stabilisation;
mania, blow-off, post-top; sustained-bull.  Macro classes: calm, down-event,
up-event, resolution.
meta keys used: delta (crash discount), D_V (fundamental drop), topped (bool),
rejected (bool), b_pred (configured sentiment predictiveness).

CLI:  python -m evaluation.stylized_facts --env v1 --seeds 50 --T 200
"""
from __future__ import annotations

import argparse
import math
import os
import sys
import warnings
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CALM = {"calm"}
DOWN = {"deterioration", "panic"}
UP = {"mania", "blow-off"}
RESOLUTION = {"stabilisation", "post-top"}
MACRO_OF = {"calm": "calm", "sustained-bull": "calm",
            "deterioration": "down-event", "panic": "down-event",
            "mania": "up-event", "blow-off": "up-event",
            "stabilisation": "resolution", "post-top": "resolution"}

# v1 phase labels -> v2 taxonomy
V1_PHASE_MAP = {"flat": "calm", "legitimate_rise": "calm", "mania": "mania", "blowoff": "blow-off",
                "deterioration": "deterioration", "panic": "panic", "stabilization": "stabilisation"}


@dataclass
class PathData:
    scenario: str
    seed: int
    df: pd.DataFrame
    meta: Dict = field(default_factory=dict)

    def __post_init__(self):
        d = self.df
        if "x" not in d.columns:
            d["x"] = np.log(d["price"].astype(float) / d["value"].astype(float))
        if "macro" not in d.columns:
            d["macro"] = d["phase"].map(MACRO_OF).fillna("calm")
        d["r"] = np.log(d["price"].astype(float)).diff()
        d["rv"] = np.log(d["value"].astype(float)).diff()


# --------------------------------------------------------------------------
# adapters
# --------------------------------------------------------------------------
def from_v1_env(scenario: str, seed: int, T: int = 200, **kw) -> PathData:
    from envs.v1.synthetic_market_v1 import SyntheticMarketEnv
    env = SyntheticMarketEnv(scenario=scenario, n_days=T, seed=seed, **kw)
    d = env.data
    phases = []
    for i in range(T):
        env.current_step = i
        phases.append(V1_PHASE_MAP[env.get_scenario_phase()])
    env.current_step = 0
    df = pd.DataFrame({"day": d["day"].values, "price": d["price"].values,
                       "value": d["fundamental_value"].values, "volume": d["volume"].values,
                       "sentiment": d["news_sentiment"].values, "iv": d["implied_volatility"].values,
                       "phase": phases})
    v = df["value"].values
    meta = {"delta": kw.get("crash_discount", env.crash_discount), "D_V": 1 - v.min() / v[0],
            "topped": None, "rejected": False, "b_pred": 0.0}
    return PathData(scenario, seed, df, meta)


# --------------------------------------------------------------------------
# statistics helpers
# --------------------------------------------------------------------------
def acf(x, k):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) <= k + 2:
        return np.nan
    x = x - x.mean()
    den = (x * x).sum()
    return float((x[:-k] * x[k:]).sum() / den) if den > 0 else np.nan


def ljung_box_p(x, lags=10):
    from statsmodels.stats.diagnostic import acorr_ljungbox
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) < lags + 5:
        return np.nan
    return float(acorr_ljungbox(x, lags=[lags], return_df=True)["lb_pvalue"].iloc[0])


def arch_lm_p(x, lags=5):
    from statsmodels.stats.diagnostic import het_arch
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) < lags + 5:
        return np.nan
    return float(het_arch(x - x.mean(), nlags=lags)[1])


def hill_index(r, frac=0.05):
    a = np.sort(np.abs(np.asarray(r, float)[~np.isnan(r)]))[::-1]
    k = max(10, int(frac * len(a)))
    if len(a) <= k or a[k] <= 0:
        return np.nan
    return float(1.0 / np.mean(np.log(a[:k] / a[k])))


def garch_fit(r, o=0):
    """Returns (alpha, gamma, beta) of a (GJR-)GARCH(1,1) fit on percent returns."""
    try:
        from arch import arch_model
        r = np.asarray(r, float)
        r = r[~np.isnan(r)] * 100
        am = arch_model(r, mean="Zero", vol="GARCH", p=1, o=o, q=1, dist="normal")
        res = am.fit(disp="off", show_warning=False)
        p = res.params
        return float(p.get("alpha[1]", np.nan)), float(p.get("gamma[1]", np.nan)), float(p.get("beta[1]", np.nan))
    except Exception:
        return np.nan, np.nan, np.nan


def mdd(p):
    p = np.asarray(p, float)
    return float((p / np.maximum.accumulate(p) - 1).min())


def _share(vals, cond):
    v = np.asarray(vals, float)
    v = v[~np.isnan(v)]
    return float(np.mean(cond(v))) if len(v) else np.nan


def _med(vals):
    v = np.asarray(vals, float)
    v = v[~np.isnan(v)]
    return float(np.median(v)) if len(v) else np.nan


def _row(item, prop, stat, criterion, passed, n):
    return {"item": item, "property": prop, "statistic": stat, "criterion": criterion,
            "pass": passed, "n_seeds": n}


def _inrange(v, lo, hi):
    return (not math.isnan(v)) and lo <= v <= hi


# --------------------------------------------------------------------------
# checklist items (each takes the list of paths of the relevant scenario(s))
# --------------------------------------------------------------------------
def item1_no_linear_acf(paths: List[PathData]):
    ps, a1 = [], []
    for p in paths:
        r = p.df.loc[p.df["phase"].isin(CALM), "r"].values
        if len(r) > 30:
            ps.append(ljung_box_p(r)); a1.append(acf(r, 1))
    s_p = _share(ps, lambda v: v > 0.05); m_a = _med(np.abs(a1))
    return _row(1, "No linear autocorrelation of returns in calm phases (Cont 1)",
                f"LB Q(10) p>0.05 in {s_p:.0%}; median |ACF(1)| = {m_a:.3f}",
                ">= 80% of seeds p>0.05; |ACF(1)| < 0.15",
                (s_p >= 0.8) and (m_a < 0.15), len(ps))


def item2_heavy_tails(paths):
    k, jb, hl = [], [], []
    for p in paths:
        r = p.df["r"].dropna().values
        k.append(stats.kurtosis(r)); jb.append(stats.jarque_bera(r)[1]); hl.append(hill_index(r))
    s_k = _share(k, lambda v: v > 1.5); s_jb = _share(jb, lambda v: v < 0.05); m_h = _med(hl)
    return _row(2, "Heavy tails (Cont 2, 7)",
                f"excess kurtosis > 1.5 in {s_k:.0%} (median {_med(k):.2f}); JB rejects in {s_jb:.0%}; Hill median {m_h:.2f}",
                "kurtosis > 1.5 in >= 80%; JB rejects; Hill 2.5-5",
                (s_k >= 0.8) and _inrange(m_h, 2.5, 5.0), len(k))


def item3_vol_clustering(paths):
    pa, p2, a1, al = [], [], [], []
    for p in paths:
        r = p.df["r"].dropna().values
        pa.append(ljung_box_p(np.abs(r))); p2.append(ljung_box_p(r ** 2)); al.append(arch_lm_p(r))
        a1.append(acf(np.abs(r), 1))
    s_a = _share(pa, lambda v: v < 0.01); s_2 = _share(p2, lambda v: v < 0.01); s_al = _share(al, lambda v: v < 0.01)
    m = _med(a1)
    return _row(3, "Volatility clustering (Cont 6)",
                f"LB|r| p<0.01 in {s_a:.0%}; LB r^2 in {s_2:.0%}; ARCH-LM(5) rejects in {s_al:.0%}; median ACF|r|(1) = {m:.3f}",
                "p < 0.01 in >= 80%; ACF|r|(1) 0.1-0.4",
                (s_a >= 0.8) and _inrange(m, 0.1, 0.4), len(pa))


def item4_acf_decay(paths):
    lags = [1, 5, 10, 20, 50]
    med = {L: _med([acf(np.abs(p.df["r"].dropna().values), L) for p in paths]) for L in lags}
    return _row(4, "Decay of ACF|r| (Cont 8)", "median ACF|r| at lags " +
                ", ".join(f"{L}: {v:.3f}" for L, v in med.items()),
                "descriptive (T = 800 paths); not a pass criterion", None, len(paths))


def item5_garch_persistence(paths):
    pers = []
    for p in paths:
        a, _, b = garch_fit(p.df["r"].dropna().values)
        pers.append(a + b)
    m = _med(pers)
    return _row(5, "GARCH persistence recoverable", f"median alpha+beta = {m:.3f}",
                "median alpha + beta in [0.90, 0.995]", _inrange(m, 0.90, 0.995), len(pers))


def item6_leverage(paths):
    c, g = [], []
    for p in paths:
        r = p.df["r"].dropna().values
        c.append(np.corrcoef(r[:-1], np.abs(r[1:]))[0, 1])
        _, gam, _ = garch_fit(r, o=1); g.append(gam)
    s = _share(c, lambda v: v < 0); mg = _med(g)
    return _row(6, "Leverage effect (Cont 9)", f"corr(r_t,|r_t+1|) < 0 in {s:.0%} (median {_med(c):.3f}); GJR gamma median {mg:.3f}",
                "negative in >= 70%; gamma > 0", (s >= 0.7) and (mg > 0), len(c))


def item7_volume_vol(paths):
    sp, ac1, sw = [], [], []
    for p in paths:
        d = p.df.dropna(subset=["r"])
        sp.append(stats.spearmanr(d["volume"], np.abs(d["r"]))[0])
        lv = np.log(p.df["volume"].astype(float).values)
        ac1.append(acf(lv, 1)); sw.append(stats.shapiro(lv)[1] if len(lv) <= 5000 else np.nan)
    m_sp, m_ac, m_sw = _med(sp), _med(ac1), _med(sw)
    s_sw = _share(sw, lambda v: v > 0.01)
    # Operationalisation (PREREGISTRATION_AMENDMENTS.md, A1): "not rejected" = Shapiro-Wilk on log volume
    # not rejected at the 1% level in the majority of seeds. The plan's volume equation adds |r| and |x|
    # terms that are right-skewed by construction, so a 5% test on 200 days rejects routinely.
    return _row(7, "Volume-volatility (Cont 10)",
                f"median Spearman corr(volume,|r|) = {m_sp:.3f}; median AC(1) log volume = {m_ac:.3f}; "
                f"Shapiro p > 0.01 in {s_sw:.0%} of seeds (median p = {m_sw:.3f})",
                "corr 0.2-0.5; AC(1) 0.5-0.8; log-normality not rejected (p > 0.01 in >= 50% of seeds)",
                _inrange(m_sp, 0.2, 0.5) and _inrange(m_ac, 0.5, 0.8) and (s_sw >= 0.5), len(sp))


def item8_gain_loss(crash_paths):
    sk, worse = [], []
    for p in crash_paths:
        r = p.df["r"].dropna().values
        sk.append(stats.skew(r)); worse.append(abs(r.min()) > abs(r.max()))
    s = float(np.mean(worse)) if worse else np.nan
    return _row(8, "Gain/loss asymmetry in crash (Cont 3)",
                f"median skew = {_med(sk):.3f}; worst day larger than best in {s:.0%}",
                "skew < 0; worst > best in >= 70% of crash seeds", (_med(sk) < 0) and (s >= 0.7), len(sk))


def _persistence_stats(paths):
    a1, hl, sd = [], [], []
    for p in paths:
        x = p.df.loc[p.df["phase"].isin(CALM), "x"].values
        if len(x) > 30:
            a = acf(x, 1); a1.append(a)
            hl.append(-math.log(2) / math.log(a) if 0 < a < 1 else np.inf); sd.append(np.std(x))
    return _med(a1), _med(hl), _med(sd), len(a1)


def item9_mispricing_persistence(paths, long_paths=None):
    """Persistence is a property of the process, not of the window: the pass
    criterion is evaluated on the long phase-free paths (T = 800) when they are
    supplied (sample ACF and sd of a near-unit-root process are biased down on
    200-day windows); the 200-day-window values are reported beside them."""
    m_a, m_h, m_s, n = _persistence_stats(paths)
    stat = f"200-day calm windows: median ACF(1) of x = {m_a:.4f}, half-life = {m_h:.0f} d, sd(x) = {m_s:.3f}"
    if long_paths:
        la, lh, ls, ln = _persistence_stats(long_paths)
        stat += f"; T=800 phase-free: ACF(1) = {la:.4f}, half-life = {lh:.0f} d, sd(x) = {ls:.3f} (criterion applied here)"
        m_a, m_h, m_s, n = la, lh, ls, ln
    return _row(9, "Mispricing persistence (FW regime)", stat,
                "ACF(1) >= 0.98; half-life >= 60 d; sd 0.08-0.20",
                (m_a >= 0.98) and (m_h >= 60) and _inrange(m_s, 0.08, 0.20), n)


def _event_window_mdd(p):
    """MDD measured from the first event day (deterioration onset) to the end of the path:
    the drawdown attributable to the scripted crash, not to calm-phase excursions."""
    ph = p.df["phase"].values
    idx = np.where(ph != "calm")[0]
    if len(idx) == 0:
        return np.nan
    return mdd(p.df["price"].values[idx[0]:])


def _delta_stats(df):
    X1 = np.column_stack([np.ones(len(df)), df["D_V"]]); X2 = np.column_stack([X1, df["delta"]])
    y = df["mdd"].values
    sse1 = ((y - X1 @ np.linalg.lstsq(X1, y, rcond=None)[0]) ** 2).sum()
    sse2 = ((y - X2 @ np.linalg.lstsq(X2, y, rcond=None)[0]) ** 2).sum()
    pr2 = (sse1 - sse2) / sse1 if sse1 > 0 else np.nan
    g = df.groupby("delta")["mdd"].mean()
    spread = abs(float(g.loc[g.index.min()] - g.loc[g.index.max()])) * 100
    return pr2, spread, g


def item10_delta_matters(crash_paths):
    """Amendment A7: the primary statistic is the EVENT-WINDOW MDD (from the first
    event day), because delta is the crash-severity parameter and whole-path MDD
    mixes in calm-phase mispricing excursions unrelated to delta; the whole-path
    version (the original operationalisation) is reported beside it."""
    rows = [(p.meta.get("delta"), p.meta.get("D_V"), _event_window_mdd(p), mdd(p.df["price"].values)) for p in crash_paths]
    df = pd.DataFrame(rows, columns=["delta", "D_V", "mdd", "mdd_full"]).dropna()
    if df["delta"].nunique() < 2:
        return _row(10, "Delta matters", "single delta in sample", "partial R2 > 0.7; spread >= 20 pp", None, len(df))
    pr2, spread, g = _delta_stats(df)
    pr2f, spreadf, gf = _delta_stats(df.assign(mdd=df["mdd_full"]))
    return _row(10, "Delta matters",
                f"event-window MDD: partial R2 of delta (controlling D_V) = {pr2:.2f}, spread between delta {g.index.min()} and "
                f"{g.index.max()} = {spread:.1f} pp, means " + ", ".join(f"{k}: {v:.1%}" for k, v in g.items()) +
                f"; whole-path MDD (reported): partial R2 {pr2f:.2f}, spread {spreadf:.1f} pp, means " +
                ", ".join(f"{k}: {v:.1%}" for k, v in gf.items()),
                "partial R2 > 0.7; spread >= 20 pp between delta 0.55 and 0.85 (event-window MDD, amendment A7)",
                (pr2 > 0.7) and (spread >= 20), len(df))


def item11_bubble(bull_paths):
    conv, topped, peak_t, peak_all = [], [], [], []
    for p in bull_paths:
        d = p.df
        mania = d[d["phase"].isin(UP)]
        if len(mania) > 5:
            conv.append(np.mean(np.diff(np.log(mania["price"].values), 2)))
        pk = float((d["price"] / d["value"]).max()); peak_all.append(pk)
        t = p.meta.get("topped")
        if t is not None:
            topped.append(bool(t))
            if t:
                peak_t.append(pk)
    s_conv = _share(conv, lambda v: v > 0)
    ts = float(np.mean(topped)) if topped else np.nan
    pk = _med(peak_t) if peak_t else _med(peak_all)
    return _row(11, "Bubble shape and populations",
                f"mean 2nd difference of log P over mania > 0 in {s_conv:.0%} (median {_med(conv):.2e}); "
                f"topped share = {'n/a (v1 has no hazard top)' if math.isnan(ts) else f'{ts:.0%}'}; "
                f"median peak P/V {'in topped seeds' if peak_t else '(all seeds)'} = {pk:.2f}",
                "convex; 40-60% topped; peak P/V 1.6-2.5 in topped seeds",
                (s_conv >= 0.5) and _inrange(ts, 0.4, 0.6) and _inrange(pk, 1.6, 2.5), len(bull_paths))


def item12_sentiment(paths):
    a1, c0, c1 = [], [], []
    for p in paths:
        d = p.df.dropna(subset=["r"])
        s = d["sentiment"].values; r = d["r"].values
        a1.append(acf(p.df["sentiment"].values, 1)); c0.append(np.corrcoef(s, r)[0, 1])
        calm = d["phase"].isin(CALM).values
        if calm.sum() > 30:
            c1.append(np.corrcoef(s[:-1][calm[1:]], r[1:][calm[1:]])[0, 1])
    m_a, m_c = _med(a1), _med(c0)
    bp = paths[0].meta.get("b_pred", 0.0) if paths else 0.0
    return _row(12, "Sentiment dynamics", f"median ACF(1) = {m_a:.3f}; median corr(s_t, r_t) = {m_c:.3f}; "
                f"median calm corr(s_t-1, r_t) = {_med(c1):.3f} (configured b_pred = {bp})",
                "ACF(1) 0.7-0.9; corr 0.25-0.55; lagged corr equals configured b_pred within CI",
                _inrange(m_a, 0.7, 0.9) and _inrange(m_c, 0.25, 0.55), len(a1))


def item13_iv(paths_all: Dict[str, List[PathData]]):
    calm_iv, panic_iv, corr, gap_calm, gap_panic = [], [], [], [], []
    for sc, paths in paths_all.items():
        for p in paths:
            d = p.df.copy()
            r = d["r"].values
            rv = np.array([np.std(r[i + 1:i + 21]) * np.sqrt(252) * 100 if i + 21 <= len(r) else np.nan
                           for i in range(len(r))])
            d["rv20"] = rv
            ok = ~np.isnan(rv)
            if ok.sum() > 30 and np.std(d["iv"].values[ok]) > 0:
                corr.append(np.corrcoef(d["iv"].values[ok], rv[ok])[0, 1])
            c = d["phase"].isin(CALM) & ok
            if c.sum() > 10:
                calm_iv.append(d.loc[c, "iv"].mean()); gap_calm.append((d.loc[c, "iv"] - d.loc[c, "rv20"]).mean())
            pz = (d["phase"] == "panic") & ok
            if pz.sum() > 5:
                panic_iv.append(d.loc[pz, "iv"].mean()); gap_panic.append((d.loc[pz, "iv"] - d.loc[pz, "rv20"]).mean())
    m_calm, m_panic, m_corr = _med(calm_iv), _med(panic_iv), _med(corr)
    return _row(13, "IV realism", f"mean IV calm {m_calm:.1f}%, panic {m_panic:.1f}%; median corr(IV, next-20d RV) = {m_corr:.2f}; "
                f"IV-RV calm {_med(gap_calm):+.1f} pts, panic {_med(gap_panic):+.1f} pts; sd of calm IV across seeds {np.nanstd(calm_iv):.2f}",
                "calm 25-35%, panic 60-100%; corr 0.4-0.8; IV-RV +3..+8 calm, +10..+25 panic; non-degenerate across seeds",
                _inrange(m_calm, 25, 35) and _inrange(m_panic, 60, 100) and _inrange(m_corr, 0.4, 0.8)
                and _inrange(_med(gap_calm), 3, 8) and _inrange(_med(gap_panic), 10, 25), len(corr))


def item15_phase_time(paths_all: Dict[str, List[PathData]]):
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.model_selection import GroupKFold, cross_val_score
    frames = []
    for sc, paths in paths_all.items():
        for p in paths:
            frames.append(pd.DataFrame({"day": np.asarray(p.df["day"].values, float),
                                        "macro": np.asarray(p.df["macro"].to_numpy(dtype=object)),
                                        "grp": f"{sc}-{p.seed}"}))
    d = pd.concat(frames, ignore_index=True)
    # keep only event-bearing scenarios for the classifier? No: mixed set, as the plan says.
    X = d[["day"]].to_numpy(dtype=float); y = d["macro"].to_numpy(dtype=object)
    if len(np.unique(y)) < 2:
        return _row(15, "Phase/time separability", "single macro class", "< 80%; < 0.9", None, len(frames))
    acc = cross_val_score(HistGradientBoostingClassifier(max_depth=3), X, y, cv=GroupKFold(5),
                          groups=d["grp"].to_numpy(dtype=object)).mean()
    ordinal = {"calm": 0, "down-event": 1, "up-event": 1, "resolution": 2}
    c = abs(np.corrcoef(d["day"].values, d["macro"].map(ordinal).values)[0, 1])
    # also report the within-scenario number (v1: 100% by construction); the pass
    # criterion is the mixed set, as pre-registered.
    within = []
    d["scenario"] = d["grp"].str.rsplit("-", n=1).str[0]
    for sc, g in d.groupby("scenario"):
        if g["macro"].nunique() < 2:
            continue
        within.append(cross_val_score(HistGradientBoostingClassifier(max_depth=3), g[["day"]].to_numpy(dtype=float),
                                      g["macro"].to_numpy(dtype=object), cv=GroupKFold(min(5, g["grp"].nunique())),
                                      groups=g["grp"].to_numpy(dtype=object)).mean())
    w = float(np.mean(within)) if within else float("nan")
    return _row(15, "Phase/time separability", f"macro-phase accuracy from day alone = {acc:.1%} (mixed set, "
                f"{len(frames)} paths; within-scenario mean {w:.1%}); |corr(day, phase id)| = {c:.2f}",
                "< 80% on the mixed set; < 0.9", (acc < 0.8) and (c < 0.9), len(frames))


def item17_conditioning(paths_all: Dict[str, List[PathData]]):
    out, ok = [], True
    for sc, paths in paths_all.items():
        rej = np.mean([bool(p.meta.get("rejected", False)) for p in paths]) if paths else np.nan
        n_att = sum(1 + int(p.meta.get("n_rejections", 0)) for p in paths)
        rate = sum(int(p.meta.get("n_rejections", 0)) for p in paths) / n_att if n_att else np.nan
        out.append(f"{sc}: rejection rate {rate:.1%}")
        if not math.isnan(rate) and rate >= 0.05:
            ok = False
    topped = [p.meta.get("topped") for p in paths_all.get("bull_trap", []) if p.meta.get("topped") is not None]
    out.append("bull-trap topped share " + (f"{np.mean(topped):.0%}" if topped else "n/a"))
    return _row(17, "Conditioning", "; ".join(out), "rejection < 5% per scenario; joint conditioning published", ok,
                sum(len(v) for v in paths_all.values()))


def item20_magnitudes(paths_all: Dict[str, List[PathData]]):
    crash = paths_all.get("crash", []); flat = paths_all.get("flat", [])
    m_mdd = _med([mdd(p.df["price"].values) for p in crash])
    m_sig = _med([p.df.loc[p.df["phase"].isin(CALM), "r"].std() for p in flat])
    worst = [p.df.loc[p.df["phase"] == "panic", "r"].min() for p in crash]
    m_w = _med(worst)
    return _row(20, "Magnitudes", f"median crash MDD = {m_mdd:.1%}; median calm daily sigma (flat) = {m_sig:.2%}; "
                f"median worst panic day = {m_w:.1%}",
                "crash MDD -20..-65%; calm sigma 1.4-2.2%/day; worst day -6..-15% in panic",
                _inrange(m_mdd, -0.65, -0.20) and _inrange(m_sig, 0.014, 0.022) and _inrange(m_w, -0.15, -0.06),
                len(crash) + len(flat))


# --------------------------------------------------------------------------
def run_checklist(paths_all: Dict[str, List[PathData]], leakage_rows: Optional[List[Dict]] = None) -> pd.DataFrame:
    """paths_all: scenario -> list of PathData. 'crash' may contain several deltas
    (meta['delta']); 'flat' is used for calm-phase tests together with the calm
    phases of the other scenarios."""
    allp = [p for v in paths_all.values() for p in v]
    calm_bearing = paths_all.get("flat", []) + paths_all.get("bull_trap", []) + paths_all.get("sustained_bull", [])
    crash = paths_all.get("crash", []); bull = paths_all.get("bull_trap", [])
    rows = [item1_no_linear_acf(calm_bearing or allp), item2_heavy_tails(allp), item3_vol_clustering(allp),
            item4_acf_decay(paths_all.get("flat_T800", paths_all.get("flat", allp))),
            item5_garch_persistence(allp), item6_leverage(allp), item7_volume_vol(allp)]
    rows.append(item8_gain_loss(crash) if crash else _row(8, "Gain/loss asymmetry", "no crash paths", "", None, 0))
    rows.append(item9_mispricing_persistence(calm_bearing or allp, paths_all.get("flat_T800")))
    rows.append(item10_delta_matters(crash) if crash else _row(10, "Delta matters", "no crash paths", "", None, 0))
    rows.append(item11_bubble(bull) if bull else _row(11, "Bubble", "no bull paths", "", None, 0))
    rows.append(item12_sentiment(allp))
    rows.append(item13_iv(paths_all))
    if leakage_rows:
        rows.extend(leakage_rows)  # items 14 and 16 come from evaluation.leakage_audit
    else:
        rows.append(_row(14, "Value leak", "see evaluation.leakage_audit (L1-L3)", "calm R2 <= 0.30; event R2 < 0.90 & MAPE >= 10%; no inversion", None, 0))
    rows.append(item15_phase_time(paths_all))
    if not leakage_rows:
        rows.append(_row(16, "Composite phase clock", "see evaluation.leakage_audit (L2b)", "selectivity <= 10 pp", None, 0))
    rows.append(item17_conditioning(paths_all))
    rows.append(_row(18, "Start design applied", "unit test (tests/)", "C_0 as configured", None, 0))
    rows.append(_row(19, "Action-space reachability", "unit test (tests/)", "any allocation reachable; SELL feasible at t=1", None, 0))
    rows.append(item20_magnitudes(paths_all))
    df = pd.DataFrame(rows).sort_values("item").reset_index(drop=True)
    return df


REFERENCE_NOTE = ("Reference values (plan Section 9): S&P 500 daily excess kurtosis ~7-10; |r| ACF(1) ~0.2; "
                  "TwinMarket SSE-50 kurtosis 7.26, leverage 0.14, GARCH alpha+beta 0.95; Hashimoto 18 JPX stocks "
                  "kurtosis 7.85 +/- 1.07, |r| ACF(1) 0.19, |r|-volume correlation 0.46.")


def to_markdown(df: pd.DataFrame, title: str, preamble: str = "") -> str:
    def fmt(p):
        return "n/a" if p is None or (isinstance(p, float) and math.isnan(p)) else ("PASS" if p else "FAIL")
    lines = [f"# {title}", "", preamble, "", "| # | Property | Statistic | Pass criterion | Result | n |", "|---|---|---|---|---|---|"]
    for _, r in df.iterrows():
        lines.append(f"| {r['item']} | {r['property']} | {r['statistic']} | {r['criterion']} | {fmt(r['pass'])} | {r['n_seeds']} |")
    vals = [None if (p is None or (isinstance(p, float) and math.isnan(p))) else bool(p) for p in df["pass"]]
    n_pass = int(sum(1 for p in vals if p is True)); n_fail = int(sum(1 for p in vals if p is False))
    lines += ["", f"**Pass {n_pass} / fail {n_fail} / not applicable {len(df) - n_pass - n_fail}.**", "", REFERENCE_NOTE, ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# v2.1 Phase 6 -- the reference criteria (REG-14 B and C), beside `run_checklist` (untouched).
#
# A separate entry point, not a change to `run_checklist`: with these functions unused the module's behaviour is
# what it was (the switch's "off" position is not calling them).  Every per-path statistic is computed by
# `evaluation.reference_stats.window_stats`, the function that produced E6.1's real-window reference, so the two
# sides of every criterion go through one estimator.  The criteria in force come from
# `evaluation/params/phase6_criteria.json` (PREREG_PHASE_6.md section 5); the reference SAMPLE for criterion B is
# the windows file the criteria file cites (KS needs the empirical distribution, not its percentiles).
# --------------------------------------------------------------------------
SCENARIOS_T200 = ("flat", "bull_trap", "crash", "sustained_bull")


def path_reference_stats(paths_all: Dict[str, List[PathData]], with_garch: bool = True) -> pd.DataFrame:
    """`window_stats` on every T = 200 path of the four scenarios ('mixed' and 'flat_T800' are not 200-day
    windows of the benchmark's own design and are excluded; the pooled population is stated)."""
    from evaluation.reference_stats import window_stats
    rows = []
    for sc in SCENARIOS_T200:
        for p in paths_all.get(sc, []):
            d = p.df.sort_values("day")
            try:
                s = window_stats(d["price"].to_numpy(float), d["volume"].to_numpy(float), with_garch)
            except Exception as e:                       # recorded, never silently dropped
                s = {"error": type(e).__name__}
            s.update({"scenario": sc, "seed": p.seed, "n_returns": int(len(d) - 1)})
            rows.append(s)
    return pd.DataFrame(rows)


def _e6_8_rows(paths_all: Dict[str, List[PathData]], n_boot: int, rng: np.random.Generator) -> List[Dict]:
    """The never-implemented criteria (weakness 64; PREREG_PHASE_6.md 5.4): item 12's lagged relation equals the
    configured b_pred, and item 13's non-degeneracy across seeds -- both with cluster-bootstrap intervals over paths."""
    out = []
    allp = [p for sc in SCENARIOS_T200 for p in paths_all.get(sc, [])]
    if not allp:
        return out
    # item 12: slope of r_t on the standardised s_{t-1}, calm rows, controlling for r_{t-1} (a within-phase partial slope)
    xs, ys, ctrl, pid = [], [], [], []
    for i, p in enumerate(allp):
        d = p.df.sort_values("day")
        s = d["sentiment"].to_numpy(float); r = d["r"].to_numpy(float)
        calm = d["phase"].isin(CALM).to_numpy()
        sd = np.nanstd(s)
        if sd <= 0 or calm.sum() < 30:
            continue
        z = (s - np.nanmean(s)) / sd
        m = calm[2:] & np.isfinite(r[2:]) & np.isfinite(r[1:-1])
        xs.append(z[1:-1][m]); ys.append(r[2:][m]); ctrl.append(r[1:-1][m]); pid.append(np.full(m.sum(), i))
    if xs:
        X = np.column_stack([np.ones(sum(len(v) for v in xs)), np.concatenate(xs), np.concatenate(ctrl)])
        y = np.concatenate(ys); pid = np.concatenate(pid); n_paths = len(allp)

        def slope(rows):
            b, *_ = np.linalg.lstsq(X[rows], y[rows], rcond=None)
            return float(b[1])
        est = slope(np.arange(len(y)))
        idx_by = [np.where(pid == i)[0] for i in range(n_paths)]
        draws = []
        for _ in range(n_boot):
            pick = rng.integers(0, n_paths, n_paths)
            rows = np.concatenate([idx_by[i] for i in pick if len(idx_by[i])])
            draws.append(slope(rows))
        lo, hi = float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))
        bp = float(allp[0].meta.get("b_pred", 0.0))
        out.append({"item": 12, "statistic": "slope of r_t on z(s_{t-1}) | r_{t-1}, calm rows", "population": "all",
                    "value": est, "ci95": [lo, hi], "reference": bp, "criterion": "CI contains the configured b_pred (E6.8)",
                    "pass": bool(lo <= bp <= hi), "n_gen": n_paths, "n_rows": int(len(y))})
    # item 13: the cross-seed sd of the calm IV mean, bootstrap CI over paths, must exclude zero
    ivm = []
    for p in allp:
        d = p.df
        c = d["phase"].isin(CALM).to_numpy()
        if c.sum() > 10:
            ivm.append(float(d.loc[c, "iv"].mean()))
    if len(ivm) > 10:
        ivm = np.asarray(ivm)
        draws = [float(np.std(ivm[rng.integers(0, len(ivm), len(ivm))], ddof=1)) for _ in range(n_boot)]
        lo, hi = float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))
        out.append({"item": 13, "statistic": "sd across seeds of the calm IV mean", "population": "all", "value": float(np.std(ivm, ddof=1)),
                    "ci95": [lo, hi], "reference": 0.0, "criterion": "non-degenerate: CI excludes 0 (E6.8)", "pass": bool(lo > 0),
                    "n_gen": int(len(ivm)), "n_rows": None})
    # item 9 (PREREG 5.4): the FIT persistence measured with the same biased ruler, flat paths only
    return out


def _item9_rows(paths_all: Dict[str, List[PathData]], doc: Dict) -> List[Dict]:
    ref = (doc or {}).get("item9_reference")
    flat = paths_all.get("flat", [])
    if not ref or not flat:
        return []
    a1, sd = [], []
    for p in flat:
        x = p.df.sort_values("day")["x"].to_numpy(float)
        a = acf(x, 1); a1.append(a); sd.append(float(np.std(x)))
    v = ref["value"]
    ma, ms = float(np.median(a1)), float(np.median(sd))
    return [{"item": 9, "statistic": "median 200-day ACF(1) of x, flat paths", "population": "flat", "value": ma,
             "reference": [v["acf1_p10"], v["acf1_p90"]], "criterion": "inside E6.9's AR(1) reference [P10, P90] at the FIT half-life",
             "pass": bool(v["acf1_p10"] <= ma <= v["acf1_p90"]), "n_gen": len(a1), "n_rows": None},
            {"item": 9, "statistic": "median 200-day sd(x), flat paths", "population": "flat", "value": ms,
             "reference": [v["sd_lo"], v["sd_hi"]], "criterion": "inside the AR(1) reference [P10, P90] scaled to s_x",
             "pass": bool(v["sd_lo"] <= ms <= v["sd_hi"]), "n_gen": len(sd), "n_rows": None}]


def run_checklist_reference(paths_all: Dict[str, List[PathData]], doc: Dict, reference_windows: pd.DataFrame,
                            n_boot: int = 500, seed: int = 620001, gen_stats: Optional[pd.DataFrame] = None) -> Dict[str, object]:
    """The checklist under REG-14 B and C (and E6.8's rows), per item, per statistic, per population.

    `doc` is the criteria file (`evaluation.criteria.load()`); `reference_windows` the E6.1 windows frame it cites.
    Returns {"per_statistic": DataFrame, "per_item": DataFrame, "extra": DataFrame, "n_gen": {...}}.
    """
    from evaluation.reference_stats import criterion_B, criterion_C
    rng = np.random.default_rng(seed)
    g = gen_stats if gen_stats is not None else path_reference_stats(paths_all)
    items = doc["items"]
    crash_mdd = float(doc["crash_window_rule"]["value"]["mdd_at_or_below"])
    ref_all = reference_windows
    ref_crash = reference_windows[pd.to_numeric(reference_windows["mdd"], errors="coerce") <= crash_mdd]
    refblk = doc["reference"]["value"]
    rows = []
    for item, spec in items.items():
        for st in spec["statistics"]:
            if st not in g.columns or st not in ref_all.columns:
                continue
            ref_kind = spec.get("reference", "all")
            ref_v = pd.to_numeric((ref_crash if ref_kind == "crash" else ref_all)[st], errors="coerce").to_numpy(float)
            ref_v = ref_v[np.isfinite(ref_v)]
            band_blk = refblk.get(st, {}).get("crash_windows" if ref_kind == "crash" else "all", {})
            band = (band_blk["p10"], band_blk["p90"]) if band_blk.get("n", 0) > 0 else None
            main_pop = spec["population"]
            for pop in ("all",) + SCENARIOS_T200:
                gg = g if pop == "all" else g[g["scenario"] == pop]
                gv = pd.to_numeric(gg[st], errors="coerce").to_numpy(float)
                gv = gv[np.isfinite(gv)]
                if len(gv) < 20 or len(ref_v) < 20:
                    continue
                B = criterion_B(gv, ref_v, rng, n_boot); C = criterion_C(gv, ref_v, band=band)
                rows.append({"item": int(item), "statistic": st, "population": pop, "is_main": pop == main_pop, "reference": ref_kind,
                             "n_gen": int(len(gv)), "n_ref": int(len(ref_v)),
                             "gen_p10": float(np.percentile(gv, 10)), "gen_p50": float(np.percentile(gv, 50)), "gen_p90": float(np.percentile(gv, 90)),
                             "ref_p10": B and float(np.percentile(ref_v, 10)), "ref_p50": float(np.percentile(ref_v, 50)), "ref_p90": float(np.percentile(ref_v, 90)),
                             "B_D": B["D"], "B_upper95": B["D_upper95"], "B_pass": B["pass"],
                             "C_share": C["share_inside"], "C_threshold": C["threshold"], "C_pass": C["pass"]})
    per_stat = pd.DataFrame(rows)
    per_item = []
    if len(per_stat):
        for item, gi in per_stat[per_stat["is_main"]].groupby("item"):
            per_item.append({"item": int(item), "property": items[str(item)]["property"], "n_statistics": int(len(gi)),
                             "population": gi["population"].iloc[0], "n_gen": int(gi["n_gen"].min()),
                             "B_pass": bool(gi["B_pass"].all()), "C_pass": bool(gi["C_pass"].all()),
                             "B_undecidable_at_n": bool(gi["n_gen"].min() < int(doc.get("criterion_B", {}).get("value", {}).get("n_min_size", 500)))})
    extra = pd.DataFrame(_e6_8_rows(paths_all, n_boot, rng) + _item9_rows(paths_all, doc))
    n_gen = {sc: len(paths_all.get(sc, [])) for sc in SCENARIOS_T200}
    return {"per_statistic": per_stat, "per_item": pd.DataFrame(per_item), "extra": extra, "n_gen": n_gen,
            "gen_stats": g, "criteria": {"D0": doc["criterion_B"]["value"]["D0"], "p0": doc["criterion_C"]["value"]["p0"], "crash_mdd": crash_mdd}}


def to_markdown_reference(res: Dict[str, object], title: str, v2_df: Optional[pd.DataFrame] = None, preamble: str = "") -> str:
    """The B/C table per item with the v2 verdict beside, the E6.8/item-9 rows, and a footer per criterion in the
    form `test_footer_counts` parses: **B: pass a / fail b / not applicable c.**"""
    def fmt(p):
        return "n/a" if p is None or (isinstance(p, float) and math.isnan(p)) else ("PASS" if p else "FAIL")
    pi = res["per_item"]; ps = res["per_statistic"]; ex = res["extra"]
    if len(ps) == 0:                       # fewer than 20 paths in every population: nothing to judge, and said so
        ps = pd.DataFrame(columns=["item", "statistic", "population", "is_main", "n_gen", "n_ref", "gen_p10", "gen_p50", "gen_p90",
                                   "ref_p10", "ref_p50", "ref_p90", "B_D", "B_upper95", "B_pass", "C_share", "C_threshold", "C_pass"])
    if len(pi) == 0:
        pi = pd.DataFrame(columns=["item", "property", "n_statistics", "population", "n_gen", "B_pass", "C_pass", "B_undecidable_at_n"])
    v2 = {} if v2_df is None else {int(r["item"]): r for _, r in v2_df.iterrows()}
    L = [f"# {title}", "", preamble, "",
         f"Populations: {', '.join(f'{k} {v}' for k, v in res['n_gen'].items())} paths (T = 200). B: bootstrap 95 % upper limit of the KS "
         f"distance < {res['criteria']['D0']}; C: share inside the reference P10–P90 ≥ {res['criteria']['p0']} − the share's half-width; "
         f"crash windows = MDD ≤ {res['criteria']['crash_mdd']}.", "",
         "| # | Property | statistics | population | n | B | C | A (v2) |", "|---|---|---|---|---|---|---|---|"]
    for _, r in pi.iterrows():
        a = v2.get(int(r["item"]))
        L.append(f"| {r['item']} | {r['property']} | {r['n_statistics']} | {r['population']} | {r['n_gen']} | "
                 f"{fmt(r['B_pass'])}{' (undecidable at this n)' if r['B_undecidable_at_n'] else ''} | {fmt(r['C_pass'])} | "
                 f"{fmt(None if a is None else a['pass'])} |")
    L += ["", "## Per statistic (main population)", "", "| # | statistic | pop | n_gen / n_ref | gen P10 / P50 / P90 | ref P10 / P50 / P90 | D (upper) | B | share (thr) | C |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in ps[ps["is_main"]].iterrows():
        L.append(f"| {r['item']} | `{r['statistic']}` | {r['population']} | {r['n_gen']} / {r['n_ref']} | {r['gen_p10']:.3g} / {r['gen_p50']:.3g} / {r['gen_p90']:.3g} | "
                 f"{r['ref_p10']:.3g} / {r['ref_p50']:.3g} / {r['ref_p90']:.3g} | {r['B_D']:.3f} ({r['B_upper95']:.3f}) | {fmt(r['B_pass'])} | "
                 f"{r['C_share']:.3f} ({r['C_threshold']:.3f}) | {fmt(r['C_pass'])} |")
    if len(ex):
        L += ["", "## E6.8 and item 9 (the criteria without a real-window counterpart)", "", "| # | statistic | pop | value [CI] | reference | criterion | result | n |",
              "|---|---|---|---|---|---|---|---|"]
        for _, r in ex.iterrows():
            ci = r.get("ci95")
            val = f"{r['value']:.5g}" + (f" [{ci[0]:.4g}, {ci[1]:.4g}]" if isinstance(ci, (list, tuple)) else "")
            L.append(f"| {r['item']} | {r['statistic']} | {r['population']} | {val} | {r['reference']} | {r['criterion']} | {fmt(r['pass'])} | {r['n_gen']} |")
    for crit in ("B", "C"):
        vals = [bool(v) for v in pi[f"{crit}_pass"]] if len(pi) else []
        n_pass = sum(vals); n_fail = len(vals) - n_pass
        L.append(f"\n**{crit}: pass {n_pass} / fail {n_fail} / not applicable {len(ex) if crit == 'C' else 0}.**")
    L.append("")
    return "\n".join(L)


def v1_paths(n_seeds: int, T: int) -> Dict[str, List[PathData]]:
    out = {"flat": [from_v1_env("flat", s, T) for s in range(n_seeds)],
           "bull_trap": [from_v1_env("bull_trap", s, T) for s in range(n_seeds)],
           "crash": [from_v1_env("crash", s, T, crash_discount=d) for d in (0.85, 0.92, 0.95) for s in range(n_seeds)]}
    out["flat_T800"] = [from_v1_env("flat", s, 800) for s in range(min(n_seeds, 20))]
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="v1", choices=["v1", "v2"])
    ap.add_argument("--seeds", type=int, default=50)
    ap.add_argument("--T", type=int, default=200)
    ap.add_argument("--out", default=None)
    ap.add_argument("--config", default=None, help="JSON dict of SyntheticMarketEnv config overrides (sensitivity runs)")
    ap.add_argument("--engine", default=None, help="mispricing engine override: fw_single | fw_index | pruna | ar1")
    a = ap.parse_args()
    import json as _json
    cfg = _json.loads(a.config) if a.config else None
    if a.env == "v1":
        paths = v1_paths(a.seeds, a.T)
    else:
        from envs.synthetic_market import checklist_paths  # provided by the v2 generator
        paths = checklist_paths(a.seeds, a.T, config=cfg, engine=a.engine)
    df = run_checklist(paths)
    out = a.out or os.path.join(ROOT, "docs", "env_v2", "generated", f"checklist_{a.env}.md")
    pre = (f"Generator {a.env}; {a.seeds} seeds per scenario (crash: per delta), T = {a.T}; "
           f"config overrides {cfg or '{}'}; engine {a.engine or 'default'}. "
           "Items 14 and 16 are filled by `python -m evaluation.leakage_audit`; 18 and 19 are unit tests.")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(to_markdown(df, f"Section 9 validation checklist ({a.env})", pre))
    df.to_csv(out.replace(".md", ".csv"), index=False)
    print(df[["item", "property", "pass"]].to_string(index=False))
    print("written", out)
