"""
v2.1 Phase 6 -- the per-window checklist statistics, computed by ONE function for real windows and generator paths.

`window_stats(px, vol)` is the estimator behind E6.1's reference distributions (`tools/phase6/e6_1_reference.py`)
and behind the reference-criteria checklist (`stylized_facts.run_checklist_reference`).  Keeping it here, in
`evaluation/`, means the audit machinery never imports from `tools/`, and that the two sides of every REG-14 B/C
criterion are guaranteed to go through the same code: the T = 200 estimator biases E6.9 measured (the Hill index at
a 5 % tail depth, the sample kurtosis of a heavy tail, the ACF of a persistent process) fall on both sides alike.

Every statistic is one of `evaluation.stylized_facts`' own helpers or a scipy call the checklist items already make.
"""
from __future__ import annotations

from typing import Dict

import numpy as np
from scipy import stats

from evaluation.stylized_facts import acf, arch_lm_p, garch_fit, hill_index, ljung_box_p, mdd

T_WINDOW = 200
ACF_LAGS = (1, 5, 10, 20, 50)


def window_stats(px: np.ndarray, vol: np.ndarray, with_garch: bool = True) -> Dict[str, float]:
    """Every checklist statistic that a real price/volume window can carry.

    `px` is the (adjusted) close over the window; `vol` the volume aligned with it.  A 201-price real window and a
    200-price generator path give 200 and 199 returns respectively; the one-day difference is immaterial to every
    statistic here and is recorded by the callers.  Statistics the generator defines on hidden state (x, phase, IV,
    sentiment) have no real-data counterpart and are absent by design (`NOT_IN_REFERENCE`).
    """
    r = np.diff(np.log(np.asarray(px, float)))
    a = np.abs(r)
    out: Dict[str, float] = {}

    # item 1 -- no linear autocorrelation
    out["lb_p_r"] = ljung_box_p(r, 10)
    out["acf1_r"] = acf(r, 1)
    out["abs_acf1_r"] = abs(out["acf1_r"]) if out["acf1_r"] == out["acf1_r"] else np.nan

    # item 2 -- heavy tails
    out["kurtosis"] = float(stats.kurtosis(r))
    out["jb_p"] = float(stats.jarque_bera(r)[1])
    out["hill"] = hill_index(r)

    # item 3 -- volatility clustering
    out["lb_p_absr"] = ljung_box_p(a, 10)
    out["lb_p_r2"] = ljung_box_p(r ** 2, 10)
    out["arch_lm_p"] = arch_lm_p(r, 5)
    out["acf1_absr"] = acf(a, 1)

    # item 4 -- ACF|r| decay
    for L in ACF_LAGS:
        out[f"acf{L}_absr"] = acf(a, L)

    # items 5 and 6 -- GARCH persistence, leverage
    if with_garch:
        al, _, be = garch_fit(r)
        out["garch_alpha"], out["garch_beta"] = al, be
        out["garch_persistence"] = al + be if (al == al and be == be) else np.nan
        _, gam, _ = garch_fit(r, o=1)
        out["gjr_gamma"] = gam
    out["leverage_corr"] = float(np.corrcoef(r[:-1], a[1:])[0, 1])

    # item 7 -- volume / volatility
    v = np.asarray(vol, float)[1:]          # align with r
    ok = np.isfinite(v) & (v > 0)
    if ok.sum() > 30:
        out["volume_absr_spearman"] = float(stats.spearmanr(v[ok], a[ok])[0])
        lv = np.log(v[ok])
        out["logvolume_acf1"] = acf(lv, 1)
        out["logvolume_shapiro_p"] = float(stats.shapiro(lv)[1]) if len(lv) <= 5000 else np.nan
    else:
        out["volume_absr_spearman"] = out["logvolume_acf1"] = out["logvolume_shapiro_p"] = np.nan

    # item 8 -- gain/loss asymmetry
    out["skew"] = float(stats.skew(r))
    out["worst_day"] = float(r.min())
    out["best_day"] = float(r.max())
    out["worst_over_best"] = float(abs(r.min()) / r.max()) if r.max() > 0 else np.nan

    # items 10 and 20 -- magnitudes
    out["mdd"] = mdd(np.asarray(px, float))
    out["daily_sigma"] = float(np.std(r, ddof=1))
    return out


# ----------------------------------------------------------------------------------------- REG-14 B and C
D0 = 0.10          # the equivalence margin of criterion B (V2_1_ALTERNATIVES_REGISTER.md section 14; Appendix A)
SHARE_P0 = 0.80    # criterion C's share
N_BOOT = 500


def ks_distance(a: np.ndarray, b: np.ndarray) -> float:
    a = np.sort(np.asarray(a, float)); b = np.sort(np.asarray(b, float))
    allv = np.concatenate([a, b])
    return float(np.max(np.abs(np.searchsorted(a, allv, "right") / len(a) - np.searchsorted(b, allv, "right") / len(b))))


def criterion_B(gen: np.ndarray, ref: np.ndarray, rng: np.random.Generator, n_boot: int = N_BOOT, d0: float = D0) -> Dict:
    """REG-14 B: the bootstrap 95 % upper limit of the two-sample KS distance is below d0."""
    d = ks_distance(gen, ref)
    draws = np.empty(n_boot)
    for i in range(n_boot):
        draws[i] = ks_distance(rng.choice(gen, len(gen)), rng.choice(ref, len(ref)))
    up = float(np.percentile(draws, 95))
    return {"D": d, "D_upper95": up, "D0": d0, "pass": bool(up < d0), "n_gen": int(len(gen)), "n_ref": int(len(ref))}


def criterion_C(gen: np.ndarray, ref: np.ndarray, p0: float = SHARE_P0, band=None) -> Dict:
    """REG-14 C: the share inside the reference P10-P90 is at least p0 minus the share's sampling half-width at
    n_gen.  `band` = (p10, p90) from the criteria file overrides the band computed from `ref`."""
    p10, p90 = band if band is not None else (float(np.percentile(ref, 10)), float(np.percentile(ref, 90)))
    share = float(np.mean((gen >= p10) & (gen <= p90)))
    hw = 1.96 * np.sqrt(p0 * (1 - p0) / len(gen))
    thr = p0 - hw
    return {"p10": float(p10), "p90": float(p90), "share_inside": share, "threshold": float(thr), "halfwidth": float(hw),
            "pass": bool(share >= thr), "n_gen": int(len(gen)), "n_ref": int(len(ref)) if ref is not None else None}


# statistics the generator's checklist defines on hidden or synthetic state; there is no real-window counterpart,
# so no reference distribution can exist for them and none is invented.
NOT_IN_REFERENCE = {
    9: "mispricing persistence -- x is hidden state; no real-data counterpart",
    11: "bubble shape -- defined on the generator's P/V and phase labels",
    12: "sentiment dynamics -- the field is generated; item 12's b_pred is LIT (Phase 5 found the free "
        "sentiment source does not reproduce Tetlock's 8.1 bp), so the criterion tests fidelity to the "
        "configured value, not to the world (E6.8)",
    13: "IV realism -- handled from the index VIX/RV relation and the five single-stock IV histories, "
        "not from the price panel (separate E6.1 block)",
    15: "phase/time separability -- defined on generator phase labels",
    17: "conditioning / rejection rate -- a property of the sampler",
}
