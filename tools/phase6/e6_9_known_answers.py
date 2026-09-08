"""
v2.1 Phase 6 -- E6.9: known-answer tests for every audit statistic.

Plan Section 10.2 (E6.9) and REG-14's experiment (i). These are written and run BEFORE any criterion is
applied, because they are what tells us two things a reference distribution alone cannot:

  1. **Is the estimator correct?**  Each statistic is applied to a synthetic process whose value of that
     statistic is known in closed form.  At a long horizon the estimate must converge to the target; a
     failure here means the audit's own code is wrong, not that the generator is.

  2. **How biased is it at T = 200?**  The benchmark runs T = 200, and several of these estimators are
     badly biased at that length (the sample ACF of a near-unit-root process, the Hill index at 5 % of 200
     order statistics).  That bias is measured here and reported, so that in E6.1/E6.2 a gap between the
     generator's windows and the real windows can be attributed to the process rather than to the ruler.
     `item9_mispricing_persistence`'s docstring already asserts this bias exists; E6.9 is where it is
     quantified rather than asserted.

For the criteria that are rejection rules rather than point estimates (Ljung-Box, ARCH-LM, Shapiro-Wilk,
Jarque-Bera) the known answer is the **size** under the null and the **power** under a stated alternative,
both at the T the checklist actually uses.  A criterion whose size at T = 200 is not its nominal level is a
mis-specified criterion, and REG-14's concordance table needs that answered item by item.

Everything is seeded from a fixed root; every case writes its own block, so the run is resumable (rule 14).

Usage:
    python -u tools/phase6/e6_9_known_answers.py --reps 400 --out docs/env_v2/generated/v2_1/e6_9
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from typing import Callable, Dict, List, Optional, Sequence

import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from evaluation.stylized_facts import (  # noqa: E402
    acf, arch_lm_p, garch_fit, hill_index, ljung_box_p, mdd,
)

OUT_DEFAULT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e6_9")

# The benchmark horizon and a long horizon at which a consistent estimator must have converged.
T_BENCH = 200
T_LONG = 20_000
ROOT_SEED = 20260908

# The engine's own mispricing persistence, so that case 3 measures the bias on the process the
# checklist actually applies item 9 to.  Read from the parameter file in force, never stipulated.
def engine_half_life() -> float:
    p = os.path.join(ROOT, "envs", "v2", "params", "mispricing.json")
    with open(p, "r", encoding="utf-8") as fh:
        d = json.load(fh)
    for key in ("half_life_days", "half_life", "h"):
        node = d.get(key)
        if isinstance(node, dict) and "value" in node:
            return float(node["value"])
        if isinstance(node, (int, float)):
            return float(node)
    # nested under a named block
    for v in d.values():
        if isinstance(v, dict):
            for key in ("half_life_days", "half_life", "h"):
                node = v.get(key)
                if isinstance(node, dict) and "value" in node:
                    return float(node["value"])
                if isinstance(node, (int, float)):
                    return float(node)
    raise KeyError("no half-life entry found in envs/v2/params/mispricing.json")


# --------------------------------------------------------------------------------------- processes
def sim_ar1(rng: np.random.Generator, T: int, phi: float, sd_e: float = 1.0, burn: int = 2000) -> np.ndarray:
    """AR(1) started from its stationary distribution (no burn-in artefact in the ACF)."""
    s = sd_e / math.sqrt(1.0 - phi * phi)
    x = np.empty(T + burn)
    x[0] = rng.normal(0.0, s)
    e = rng.normal(0.0, sd_e, T + burn)
    for t in range(1, T + burn):
        x[t] = phi * x[t - 1] + e[t]
    return x[burn:]


def sim_garch(rng: np.random.Generator, T: int, omega: float, alpha: float, beta: float,
              gamma: float = 0.0, burn: int = 2000) -> np.ndarray:
    """(GJR-)GARCH(1,1) with normal innovations, in return units.

    h_t = omega + (alpha + gamma * 1[r_{t-1} < 0]) * r_{t-1}^2 + beta * h_{t-1}
    This is the `arch` package's GJR parameterisation, so the fitted (alpha, gamma, beta) are comparable
    to the simulated ones.  Unconditional variance = omega / (1 - alpha - gamma/2 - beta).
    """
    pers = alpha + gamma / 2.0 + beta
    h0 = omega / max(1e-12, 1.0 - pers)
    n = T + burn
    r = np.empty(n)
    h = h0
    z = rng.normal(0.0, 1.0, n)
    for t in range(n):
        r[t] = math.sqrt(h) * z[t]
        ind = 1.0 if r[t] < 0 else 0.0
        h = omega + (alpha + gamma * ind) * r[t] * r[t] + beta * h
    return r[burn:]


def sim_pareto(rng: np.random.Generator, T: int, alpha: float) -> np.ndarray:
    """Signed Pareto(alpha) on the magnitude: |r| ~ Pareto(alpha), so the Hill index targets alpha exactly."""
    u = rng.uniform(0.0, 1.0, T)
    mag = (1.0 - u) ** (-1.0 / alpha)
    sign = rng.choice([-1.0, 1.0], T)
    return sign * mag


def sim_t(rng: np.random.Generator, T: int, df: float) -> np.ndarray:
    return stats.t.rvs(df, size=T, random_state=rng)


def sim_normal(rng: np.random.Generator, T: int) -> np.ndarray:
    return rng.normal(0.0, 1.0, T)


# ------------------------------------------------------------------------------------------- cases
class Case:
    """One known-answer test.

    kind = "point": `stat(series)` is compared with `target`; convergence is asserted at T_LONG and the
                    bias is reported at T_BENCH.
    kind = "rate" : `stat(series)` returns a p-value; the rejection rate at `alpha` is compared with
                    `target` (the nominal level under a null, or a reported power under an alternative).
    """

    def __init__(self, name: str, statistic: str, kind: str, gen: Callable, stat: Callable,
                 target: Optional[float], note: str, horizons: Sequence[int] = (T_BENCH, T_LONG),
                 reps: Optional[int] = None, alpha: Optional[float] = None, target_is_theory: bool = True):
        self.name, self.statistic, self.kind = name, statistic, kind
        self.gen, self.stat, self.target = gen, stat, target
        self.note, self.horizons, self.reps, self.alpha = note, list(horizons), reps, alpha
        self.target_is_theory = target_is_theory


def build_cases(h_engine: float) -> List[Case]:
    phi_engine = 2.0 ** (-1.0 / h_engine)
    cases: List[Case] = []

    # ---- ACF, the estimator behind items 1, 3, 4, 7, 9 and 12
    for phi, lag in ((0.6, 1), (0.9, 5)):
        cases.append(Case(
            f"acf_ar1_phi{phi}_lag{lag}", f"acf(r, {lag})", "point",
            lambda rng, T, phi=phi: sim_ar1(rng, T, phi),
            lambda x, lag=lag: acf(x, lag),
            phi ** lag,
            f"AR(1) with phi = {phi}: ACF({lag}) = phi^{lag} exactly.",
        ))
    cases.append(Case(
        "acf_ar1_engine_persistence_lag1", "acf(x, 1) on the engine's persistence", "point",
        lambda rng, T: sim_ar1(rng, T, phi_engine),
        lambda x: acf(x, 1),
        phi_engine,
        f"AR(1) at the engine's fitted half-life ({h_engine:g} d, phi = {phi_engine:.6f}). "
        f"Item 9's criterion (ACF(1) >= 0.98) is read off this estimator, so its downward bias at "
        f"T = 200 is exactly what decides whether that criterion is meetable on a 200-day window.",
    ))
    cases.append(Case(
        "half_life_ar1_engine", "half-life from ACF(1)", "point",
        lambda rng, T: sim_ar1(rng, T, phi_engine),
        lambda x: (lambda a: (-math.log(2) / math.log(a)) if 0 < a < 1 else np.nan)(acf(x, 1)),
        h_engine,
        "The half-life item 9 reports, -log2/log(ACF(1)); inherits the ACF's bias nonlinearly.",
    ))
    cases.append(Case(
        "sd_ar1_engine", "sd(x)", "point",
        lambda rng, T: sim_ar1(rng, T, phi_engine, sd_e=1.0),
        lambda x: float(np.std(x)),
        1.0 / math.sqrt(1.0 - phi_engine ** 2),
        "Stationary sd of the AR(1) = sd_e / sqrt(1 - phi^2); item 9's sd(x) band is read off this.",
    ))
    cases.append(Case(
        "acf_logvolume_ar1", "acf(log volume, 1)", "point",
        lambda rng, T: np.exp(sim_ar1(rng, T, 0.65, sd_e=0.3)),
        lambda v: acf(np.log(v), 1),
        0.65,
        "Item 7's log-volume AC(1) on a log-AR(1) volume series with phi = 0.65.",
    ))

    # ---- tail and shape statistics, items 2 and 8
    cases.append(Case(
        "kurtosis_t5", "scipy kurtosis (excess)", "point",
        lambda rng, T: sim_t(rng, T, 5.0),
        lambda r: float(stats.kurtosis(r)),
        6.0 / (5.0 - 4.0),
        "Student-t(5): excess kurtosis = 6/(nu-4) = 6.",
    ))
    cases.append(Case(
        "kurtosis_normal", "scipy kurtosis (excess)", "point",
        sim_normal, lambda r: float(stats.kurtosis(r)), 0.0,
        "Gaussian: excess kurtosis 0. Item 2's threshold is > 1.5, so the null's spread at T = 200 sets its size.",
    ))
    cases.append(Case(
        "skew_normal", "scipy skew", "point",
        sim_normal, lambda r: float(stats.skew(r)), 0.0,
        "Gaussian: skew 0. Item 8's criterion is skew < 0.",
    ))
    cases.append(Case(
        "hill_pareto_alpha3", "hill_index(r, 0.05)", "point",
        lambda rng, T: sim_pareto(rng, T, 3.0),
        hill_index, 3.0,
        "|r| ~ Pareto(3): the Hill estimator targets the tail index 3 exactly. Item 2's Hill band is 2.5-5.",
    ))
    cases.append(Case(
        "hill_t4", "hill_index(r, 0.05)", "point",
        lambda rng, T: sim_t(rng, T, 4.0),
        hill_index, 4.0,
        "Student-t(4) has tail index 4; the Hill estimator is consistent but at T = 200 it uses only "
        "max(10, 0.05*200) = 10 order statistics, so the bias here is the honest size of item 2's Hill band.",
    ))

    # ---- GARCH, items 5 and 6
    g = dict(omega=0.02, alpha=0.08, beta=0.90)
    cases.append(Case(
        "garch_persistence", "garch_fit -> alpha + beta", "point",
        lambda rng, T: sim_garch(rng, T, **g),
        lambda r: (lambda p: p[0] + p[2])(garch_fit(r)),
        g["alpha"] + g["beta"],
        f"GARCH(1,1) simulated at alpha = {g['alpha']}, beta = {g['beta']}; item 5's criterion is "
        f"median alpha+beta in [0.90, 0.995].",
        reps=200,
    ))
    cases.append(Case(
        "garch_alpha", "garch_fit -> alpha", "point",
        lambda rng, T: sim_garch(rng, T, **g),
        lambda r: garch_fit(r)[0], g["alpha"],
        "The ARCH coefficient of the same simulation.", reps=200,
    ))
    gj = dict(omega=0.02, alpha=0.03, beta=0.90, gamma=0.10)
    cases.append(Case(
        "gjr_gamma", "garch_fit(o=1) -> gamma", "point",
        lambda rng, T: sim_garch(rng, T, **gj),
        lambda r: garch_fit(r, o=1)[1], gj["gamma"],
        f"GJR-GARCH simulated at gamma = {gj['gamma']}; item 6's criterion is gamma > 0.",
        reps=200,
    ))
    cases.append(Case(
        "leverage_corr_symmetric", "corr(r_t, |r_t+1|)", "point",
        lambda rng, T: sim_garch(rng, T, **g),
        lambda r: float(np.corrcoef(r[:-1], np.abs(r[1:]))[0, 1]),
        0.0,
        "A symmetric GARCH has no leverage effect: the correlation is 0. Item 6 asks for it to be "
        "negative in >= 70 % of seeds, so this case measures that share's null.",
    ))
    cases.append(Case(
        "leverage_corr_gjr", "corr(r_t, |r_t+1|)", "point",
        lambda rng, T: sim_garch(rng, T, **gj),
        lambda r: float(np.corrcoef(r[:-1], np.abs(r[1:]))[0, 1]),
        None,
        "The same statistic under a true leverage effect (gamma = 0.10). No closed form; the long-horizon "
        "value IS the reference, and the T = 200 spread is what item 6's share criterion has to beat.",
        target_is_theory=False,
    ))

    # ---- MDD, items 10 and 20
    def _det_path(rng, T):
        # A deterministic path with an exact known maximum drawdown of -40 %: up to 1.5, down to 0.9, up.
        up = np.linspace(1.0, 1.5, T // 2)
        down = np.linspace(1.5, 0.9, T - T // 2)
        return np.concatenate([up, down])

    cases.append(Case(
        "mdd_deterministic", "mdd(price)", "point",
        _det_path, mdd, 0.9 / 1.5 - 1.0,
        "A deterministic peak-to-trough path: MDD = 0.9/1.5 - 1 = -0.40 exactly, at every T.",
        horizons=(T_BENCH, 2000),
    ))

    # ---- rejection rules: size under the null, power under a stated alternative
    cases.append(Case(
        "ljung_box_size_iid", "ljung_box_p(r, 10) > 0.05", "rate",
        sim_normal, lambda r: ljung_box_p(r, 10), 0.05,
        "Item 1 asks for LB p > 0.05 in >= 80 % of seeds. Under iid the rejection rate must be the "
        "nominal 0.05, i.e. the criterion's own null share is 0.95 -- so a 0.80 threshold has slack.",
        alpha=0.05,
    ))
    cases.append(Case(
        "ljung_box_power_ar1_015", "ljung_box_p(r, 10) < 0.05", "rate",
        lambda rng, T: sim_ar1(rng, T, 0.15),
        lambda r: ljung_box_p(r, 10), None,
        "Power at phi = 0.15, the edge of item 1's own |ACF(1)| < 0.15 band: how often the LB half of "
        "item 1 fires at the point where its ACF half is indifferent.",
        alpha=0.05, target_is_theory=False,
    ))
    cases.append(Case(
        "arch_lm_size_iid", "arch_lm_p(r, 5) < 0.01", "rate",
        sim_normal, lambda r: arch_lm_p(r, 5), 0.01,
        "Item 3 asks for ARCH-LM p < 0.01 in >= 80 % of seeds. Size under iid must be 0.01.",
        alpha=0.01,
    ))
    cases.append(Case(
        "arch_lm_power_garch", "arch_lm_p(r, 5) < 0.01", "rate",
        lambda rng, T: sim_garch(rng, T, **g),
        lambda r: arch_lm_p(r, 5), None,
        "Power of item 3's ARCH-LM half at the simulated GARCH.",
        alpha=0.01, target_is_theory=False,
    ))
    cases.append(Case(
        "lb_abs_r_power_garch", "ljung_box_p(|r|, 10) < 0.01", "rate",
        lambda rng, T: sim_garch(rng, T, **g),
        lambda r: ljung_box_p(np.abs(r), 10), None,
        "Power of item 3's LB|r| half at the simulated GARCH.",
        alpha=0.01, target_is_theory=False,
    ))
    cases.append(Case(
        "shapiro_size_normal", "shapiro(log v) < 0.01", "rate",
        sim_normal, lambda x: float(stats.shapiro(x)[1]), 0.01,
        "Item 7 (amendment A1) asks for Shapiro p > 0.01 on log volume in >= 50 % of seeds. Under exact "
        "log-normality the rejection rate must be 0.01, so the null share is 0.99.",
        alpha=0.01,
    ))
    cases.append(Case(
        "jarque_bera_size_normal", "jarque_bera(r) < 0.05", "rate",
        sim_normal, lambda r: float(stats.jarque_bera(r)[1]), 0.05,
        "Item 2 reports the JB rejection share; its size under a Gaussian must be 0.05.",
        alpha=0.05,
    ))
    cases.append(Case(
        "jarque_bera_power_t5", "jarque_bera(r) < 0.05", "rate",
        lambda rng, T: sim_t(rng, T, 5.0),
        lambda r: float(stats.jarque_bera(r)[1]), None,
        "Power of the JB half of item 2 at Student-t(5).",
        alpha=0.05, target_is_theory=False,
    ))

    # ---- the generator's OWN volatility block (E3.1 shape in force): the power of item 3's rule against the
    #      process the checklist is actually applied to.  Read from the block file, never restated.
    blk = _block_in_force()
    if blk is not None:
        sh = blk["shape"]
        # omega chosen so the unconditional variance equals sbar^2 (the block's identity value)
        pers = sh["alpha"] + sh["gamma"] / 2.0 + sh["beta"]
        gin = dict(omega=blk["sbar"] ** 2 * (1.0 - pers), alpha=sh["alpha"], beta=sh["beta"], gamma=sh["gamma"])
        lab = f"alpha {sh['alpha']}, gamma {sh['gamma']}, beta {sh['beta']}, sbar {blk['sbar']:.4f}"
        cases.append(Case(
            "arch_lm_power_block_in_force", "arch_lm_p(r, 5) < 0.01", "rate",
            lambda rng, T, gin=gin: sim_garch(rng, T, **gin),
            lambda r: arch_lm_p(r, 5), None,
            f"Power of item 3's ARCH-LM half against the generator's own GJR-GARCH shape ({lab}; "
            f"e3_4/block.json, Gaussian innovations). Item 3 asks for p < 0.01 in >= 80 % of seeds.",
            alpha=0.01, target_is_theory=False,
        ))
        cases.append(Case(
            "lb_abs_r_power_block_in_force", "ljung_box_p(|r|, 10) < 0.01", "rate",
            lambda rng, T, gin=gin: sim_garch(rng, T, **gin),
            lambda r: ljung_box_p(np.abs(r), 10), None,
            f"Power of item 3's LB|r| half against the generator's own shape ({lab}).",
            alpha=0.01, target_is_theory=False,
        ))
        cases.append(Case(
            "acf1_absr_block_in_force", "acf(|r|, 1)", "point",
            lambda rng, T, gin=gin: sim_garch(rng, T, **gin),
            lambda r: acf(np.abs(r), 1), None,
            f"Item 3's ACF|r|(1) band (0.1-0.4) against the generator's own shape ({lab}); no closed form, the "
            f"long-horizon value is the reference and the T = 200 spread is what the band has to hold.",
            target_is_theory=False,
        ))
        cases.append(Case(
            "garch_persistence_block_in_force", "garch_fit -> alpha + beta", "point",
            lambda rng, T, gin=gin: sim_garch(rng, T, **gin),
            lambda r: (lambda p: p[0] + p[2])(garch_fit(r)),
            sh["alpha"] + sh["gamma"] / 2.0 + sh["beta"],
            f"Item 5's alpha + beta recovered by a symmetric GARCH(1,1) fit from the GJR shape in force ({lab}). "
            f"A symmetric fit absorbs gamma/2 into alpha (the indicator is 1 on half the days), so the persistence a "
            f"symmetric fit CAN recover is alpha + gamma/2 + beta = {sh['alpha'] + sh['gamma'] / 2.0 + sh['beta']:.4f}; "
            f"the first run of this case set the target at alpha + beta = {sh['alpha'] + sh['beta']:.4f} and failed "
            f"(long-horizon mean 0.9872), which was the target's error, not the estimator's. The second run, at "
            f"alpha + gamma/2 + beta, gave 0.9872 against 0.9880 -- 6 MCSE away: the pseudo-true value of a symmetric "
            f"QMLE on a GJR process is only APPROXIMATELY alpha + gamma/2 + beta, so this case has no exact closed form "
            f"and is REPORTED with that reference value, not judged (both earlier verdicts are disclosed here). The "
            f"T = 200 spread is what item 5 reads on the generator's own process.",
            reps=200, target_is_theory=False,
        ))
    # the JB size at the long horizon sat at the edge of its interval in the first run; re-measured at 5x the reps
    cases.append(Case(
        "jarque_bera_size_normal_recheck", "jarque_bera(r) < 0.05", "rate",
        sim_normal, lambda r: float(stats.jarque_bera(r)[1]), 0.05,
        "Re-measurement of the JB size (the first run's long-horizon rate was 0.0725 [0.051, 0.102] at 400 reps, "
        "the nominal 0.05 just outside the interval); 2,000 reps decide whether that was a draw or a size distortion.",
        alpha=0.05, reps=2000,
    ))
    return cases


def _block_in_force() -> Optional[Dict]:
    p = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e3_4", "block.json")
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as fh:
        b = json.load(fh)
    return b if ("shape" in b and "sbar" in b) else None


# --------------------------------------------------------------------------------------- execution
def _one_rep(case: Case, T: int, seed: int) -> float:
    rng = np.random.default_rng(seed)
    try:
        series = case.gen(rng, T)
        return float(case.stat(series))
    except Exception:
        return float("nan")


def run_case(case: Case, reps: int, n_jobs: int) -> Dict:
    from joblib import Parallel, delayed
    from threadpoolctl import threadpool_limits

    out = {"name": case.name, "statistic": case.statistic, "kind": case.kind, "note": case.note,
           "target": case.target, "target_is_theory": case.target_is_theory,
           "alpha": case.alpha, "horizons": {}}
    n = case.reps or reps
    for T in case.horizons:
        t0 = time.time()
        seeds = [ROOT_SEED + 1_000_003 * case.horizons.index(T) + i for i in range(n)]
        with threadpool_limits(limits=2):
            vals = Parallel(n_jobs=n_jobs, backend="loky")(
                delayed(_one_rep)(case, T, s) for s in seeds)
        v = np.asarray(vals, float)
        ok = v[~np.isnan(v)]
        blk = {"n_reps": int(n), "n_finite": int(ok.size), "seconds": round(time.time() - t0, 1)}
        if case.kind == "point":
            blk.update({
                "median": float(np.median(ok)) if ok.size else None,
                "mean": float(np.mean(ok)) if ok.size else None,
                "sd": float(np.std(ok, ddof=1)) if ok.size > 1 else None,
                "p10": float(np.percentile(ok, 10)) if ok.size else None,
                "p90": float(np.percentile(ok, 90)) if ok.size else None,
            })
            # Monte-Carlo standard error of the mean; the convergence test uses it rather than a chosen tolerance.
            if ok.size > 1:
                blk["mcse"] = float(np.std(ok, ddof=1) / math.sqrt(ok.size))
            if case.target is not None and ok.size:
                blk["bias_median"] = blk["median"] - case.target
                blk["bias_mean"] = blk["mean"] - case.target
                blk["rel_bias_median"] = (blk["median"] - case.target) / case.target if case.target else None
                if blk.get("mcse"):
                    blk["bias_in_mcse"] = blk["bias_mean"] / blk["mcse"]
        else:
            rate = float(np.mean(ok < case.alpha)) if ok.size else None
            blk["rejection_rate"] = rate
            if rate is not None and ok.size:
                # Wilson 95 % interval for the rejection rate
                z, nn = 1.959963985, ok.size
                d = 1 + z * z / nn
                c = (rate + z * z / (2 * nn)) / d
                hw = z * math.sqrt(rate * (1 - rate) / nn + z * z / (4 * nn * nn)) / d
                blk["rate_ci95"] = [max(0.0, c - hw), min(1.0, c + hw)]
            if case.target is not None and rate is not None:
                blk["size_error"] = rate - case.target
                blk["nominal"] = case.target
        out["horizons"][str(T)] = blk
        print(f"  T={T:>6}: " + (
            f"median {blk.get('median'):+.5f}  bias {blk.get('bias_median', float('nan')):+.5f}"
            if case.kind == "point" else
            f"rejection rate {blk.get('rejection_rate'):.4f}"
        ) + f"  ({blk['seconds']}s)", flush=True)

    # verdict: consistency at the long horizon, measured against Monte-Carlo error, not a chosen tolerance
    out["verdict"] = _verdict(out)
    return out


def _verdict(out: Dict) -> Dict:
    """A known-answer test PASSES when the long-horizon estimate is within 4 Monte-Carlo standard errors
    of the theoretical target (a 'chosen' 4 only in the sense that it is the usual MC convergence check;
    the scale it is measured on is the run's own sampling error, not a tolerance picked to be met).
    Cases without a closed-form target are reported, not judged."""
    hs = sorted(int(k) for k in out["horizons"])
    long_key = str(hs[-1])
    blk = out["horizons"][long_key]
    if not out.get("target_is_theory") or out.get("target") is None:
        return {"status": "reported", "reason": "no closed-form target; the long-horizon value is the reference",
                "long_horizon": long_key}
    if out["kind"] == "point":
        z = blk.get("bias_in_mcse")
        bias = blk.get("bias_mean")
        # A deterministic statistic (mdd on a fixed path) has MCSE at floating-point scale, so a pure
        # z-test can never pass however exact the answer is.  The floor is machine precision on the
        # target's own scale -- it admits an exactly-right answer, nothing looser.
        floor = 1e-9 * max(1.0, abs(out["target"]))
        exact = bias is not None and abs(bias) <= floor
        ok = exact or (z is not None and abs(z) <= 4.0)
        return {"status": "pass" if ok else "fail",
                "criterion": "|mean - target| <= 4 * MCSE at the long horizon, "
                             "or exact to floating point (MCSE degenerate)",
                "z": z, "bias": bias, "exact_to_float": bool(exact), "long_horizon": long_key}
    ci = blk.get("rate_ci95")
    tgt = out.get("target")
    ok = ci is not None and ci[0] <= tgt <= ci[1]
    return {"status": "pass" if ok else "fail",
            "criterion": "nominal level inside the Wilson 95 % interval of the realised rejection rate",
            "rate_ci95": ci, "nominal": tgt, "long_horizon": long_key}


def hill_frac_sensitivity(T: int = 2_000_000, seed: int = ROOT_SEED + 99) -> Dict:
    """Why `hill_index(r, frac=0.05)` misses a Student-t tail index, and by how much.

    The Hill estimator is consistent for the tail index only as k/n -> 0.  On an exact Pareto tail it is
    unbiased at any depth (that is the control, and it is what proves the audit's code is right); on a
    Student-t the second-order term at a 5 % depth is large.  Item 2 reads its Hill band off this
    estimator at frac = 0.05, so the size of that bias is a property of the CRITERION, not of the
    generator -- and it is the argument for a reference-distribution criterion (E6.1/E6.2, REG-14 B/C)
    over the v2 absolute band on this item: the real windows carry the identical bias, so a like-for-like
    comparison is immune to it while an absolute band is not.
    """
    rng = np.random.default_rng(seed)
    fracs = [0.05, 0.02, 0.01, 0.005, 0.002, 0.001]
    out = {"T": T, "fracs": fracs, "note": hill_frac_sensitivity.__doc__.strip()}
    t4 = stats.t.rvs(4.0, size=T, random_state=rng)
    out["student_t4"] = {"true_index": 4.0,
                         "hill": {str(f): float(hill_index(t4, f)) for f in fracs}}
    u = rng.uniform(0.0, 1.0, T)
    par = ((1.0 - u) ** (-1.0 / 3.0)) * rng.choice([-1.0, 1.0], T)
    out["pareto3_control"] = {"true_index": 3.0,
                              "hill": {str(f): float(hill_index(par, f)) for f in fracs}}
    return out


def to_markdown(res: List[Dict], meta: Dict, hill_diag: Optional[Dict] = None) -> str:
    L = [f"# E6.9 — known-answer tests for the audit statistics", "",
         f"Generated by `tools/phase6/e6_9_known_answers.py`. "
         f"Root seed {meta['root_seed']}; {meta['reps']} replications per case per horizon "
         f"(GARCH cases {meta['garch_reps']}); numpy {meta['numpy']}, scipy {meta['scipy']}, "
         f"statsmodels {meta['statsmodels']}, arch {meta['arch']}.", "",
         "**What a pass means.** For a point estimate: the long-horizon mean is within 4 Monte-Carlo "
         "standard errors of the closed-form target, so the estimator is consistent and the audit's code "
         "is right. For a rejection rule: the realised rejection rate's Wilson 95 % interval covers the "
         "nominal level. Cases with no closed form are **reported**, not judged — their long-horizon value "
         "is the reference the T = 200 spread is measured against.", "",
         "**What the bias column is for.** The benchmark runs T = 200. Where the T = 200 bias is large, a "
         "criterion stated in the statistic's *population* units cannot be met on a 200-day window however "
         "good the generator is — that is a mis-specified criterion, and REG-14's concordance table needs "
         "it named. These rows are the input to E6.1 and E6.2.", ""]

    L += ["## Point estimates", "",
          "| case | statistic | target | T = 200 median | bias at 200 | long-T mean | bias/MCSE | verdict |",
          "|---|---|---|---|---|---|---|---|"]
    for r in res:
        if r["kind"] != "point":
            continue
        hs = sorted(int(k) for k in r["horizons"])
        b, lo = r["horizons"][str(hs[0])], r["horizons"][str(hs[-1])]
        tgt = "—" if r["target"] is None else f"{r['target']:.4f}"
        bias = "—" if b.get("bias_median") is None else f"{b['bias_median']:+.4f}"
        z = lo.get("bias_in_mcse")
        L.append(f"| `{r['name']}` | {r['statistic']} | {tgt} | {b.get('median', float('nan')):.4f} | {bias} | "
                 f"{lo.get('mean', float('nan')):.4f} | {'—' if z is None else f'{z:+.2f}'} | "
                 f"**{r['verdict']['status']}** |")

    L += ["", "## Rejection rules (size and power at T = 200)", "",
          "| case | rule | nominal | realised rate at T = 200 | 95 % CI | verdict |", "|---|---|---|---|---|---|"]
    for r in res:
        if r["kind"] != "rate":
            continue
        b = r["horizons"][str(T_BENCH)]
        ci = b.get("rate_ci95")
        nom = "—" if r["target"] is None else f"{r['target']:.3f}"
        L.append(f"| `{r['name']}` | {r['statistic']} | {nom} | {b.get('rejection_rate', float('nan')):.4f} | "
                 f"{'—' if ci is None else f'[{ci[0]:.4f}, {ci[1]:.4f}]'} | **{r['verdict']['status']}** |")

    if hill_diag:
        L += ["", "## Diagnostic: the Hill index against tail depth", "",
              f"One simulation of T = {hill_diag['T']:,} per row, so the sampling error is negligible and what is "
              "left is the estimator's own bias at each depth.", "",
              "| tail fraction | Hill on Student-t(4) (true 4.0) | Hill on Pareto(3) (true 3.0, control) |",
              "|---|---|---|"]
        for f in hill_diag["fracs"]:
            L.append(f"| {f} | {hill_diag['student_t4']['hill'][str(f)]:.4f} | "
                     f"{hill_diag['pareto3_control']['hill'][str(f)]:.4f} |")
        L += ["", "**Reading.** The Pareto control is unbiased at every depth, so the audit's Hill code is "
                  "correct. On a Student-t tail the estimator at the audit's own `frac = 0.05` is biased "
                  "**low**, and the bias closes only as the depth shrinks. Item 2's Hill band (2.5–5.0) is "
                  "therefore stated in units the estimator does not deliver at this tuning. Because the real "
                  "200-day windows of E6.1 are measured with the identical estimator at the identical depth, a "
                  "reference-distribution criterion (REG-14 B or C) is unaffected by this bias, while the v2 "
                  "absolute band (REG-14 A) is not — this is evidence for the criterion form on item 2, "
                  "derived rather than asserted.", ""]

    L += ["", "## Case notes", ""]
    for r in res:
        L.append(f"- **`{r['name']}`** — {r['note']}")
    L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=400)
    ap.add_argument("--garch-reps", type=int, default=200)
    ap.add_argument("--n-jobs", type=int, default=max(1, (os.cpu_count() or 4) // 2))
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--only", default=None, help="comma-separated case names to run")
    ap.add_argument("--hill-diag-T", type=int, default=2_000_000,
                    help="length of the single series behind the Hill-vs-depth diagnostic")
    a = ap.parse_args(argv)

    os.makedirs(a.out, exist_ok=True)
    h = engine_half_life()
    cases = build_cases(h)
    for c in cases:
        # a case-level reps override applies only to the GARCH cases (their fits are the slow part); a case that
        # asks for MORE reps than the default keeps its own count (the JB re-check)
        if c.reps is not None and c.reps < a.reps:
            c.reps = a.garch_reps
    if a.only:
        want = set(a.only.split(","))
        cases = [c for c in cases if c.name in want]

    import scipy, statsmodels, arch as archpkg
    meta = {"root_seed": ROOT_SEED, "reps": a.reps, "garch_reps": a.garch_reps,
            "engine_half_life_days": h, "T_bench": T_BENCH, "T_long": T_LONG,
            "numpy": np.__version__, "scipy": scipy.__version__,
            "statsmodels": statsmodels.__version__, "arch": archpkg.__version__,
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    js = os.path.join(a.out, "known_answers.json")
    res: List[Dict] = []
    if os.path.exists(js):
        # resumable: cases already on disk are kept (a case is re-run only when named in --only)
        with open(js, "r", encoding="utf-8") as fh:
            prev = json.load(fh)
        keep = set(c.name for c in cases) if a.only else set()
        res = [r for r in prev.get("cases", []) if r["name"] not in keep]
        done = {r["name"] for r in res}
        cases = [c for c in cases if c.name not in done]     # --only re-runs the named cases; the rest stay
    for i, c in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {c.name} ({c.statistic})", flush=True)
        res.append(run_case(c, a.reps, a.n_jobs))
        # write after every case: the run is resumable and a crash never costs more than one case
        with open(js, "w", encoding="utf-8") as fh:
            json.dump({"meta": meta, "cases": res}, fh, indent=1)

    print("hill index vs tail depth (diagnostic)", flush=True)
    hill_diag = hill_frac_sensitivity(T=a.hill_diag_T)
    with open(js, "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "cases": res, "hill_frac_sensitivity": hill_diag}, fh, indent=1)
    with open(os.path.join(a.out, "known_answers.md"), "w", encoding="utf-8") as fh:
        fh.write(to_markdown(res, meta, hill_diag))

    n_pass = sum(1 for r in res if r["verdict"]["status"] == "pass")
    n_fail = sum(1 for r in res if r["verdict"]["status"] == "fail")
    n_rep = sum(1 for r in res if r["verdict"]["status"] == "reported")
    print(f"\n{n_pass} pass / {n_fail} fail / {n_rep} reported (no closed form), {len(res)} cases -> {a.out}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
