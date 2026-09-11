"""
v2.1 Phase 8 -- E8.5's analysis: variance components, ICCs, the power table that sizes the main grid, the minimum
detectable differences, and the transfer check (PREREG_PHASE_8.md 5.4-5.6; D12 = P8-1; D on its own = P8-2).

    python -u -m tools.phase8.e8_5_analyse --stages score,components,power,transfer

`score`       every checkpointed run -> `metrics_v2.score_run(scoring="v2_1")` at the theta in force (read back through
              the loud loader first, P6-12; its sha256 recorded, P4-19) -> e8_5/per_run.csv
`components`  per model and metric: (1) REML y ~ C(Arm) * C(Persona) [* C(Scenario)] with variance components
              {path, path x arm}, residual = replicate; ICCs.  (2) the model-free plug-ins: seed-level pairs
              d = replicate-mean(memory) - replicate-mean(static); sigma_d(3) on (pairs - persona x scenario cells)
              df; sigma^2_rep pooled within (persona, arm, scenario, seed); sigma^2_int = max(0, sigma_d(3)^2 -
              2 sigma^2_rep / R); sigma_d(R')^2 = sigma^2_int + 2 sigma^2_rep / R'.  (3) upper confidence limits of
              sigma_d(R') by percentile cluster bootstrap over paths within scenario (2,000), at 80 / 90 / 95 %; the
              chi-square limit of sigma_d(3) beside.  B and D in their own rows.
`power`       D12: Delta = 0.05 on band-MAS, plug-in = the one-sided 90 % limit, alpha' = 0.05 / m(Q1, C); seeds per
              persona x scenario cell by Appendix A as written (factor 2) and paired-correct beside, at nominal alpha
              beside; the minimum detectable difference of every metric at E8.5's design, Tier A's and the
              band-MAS-sized design (P8-2's achieved power for D); replicates against seeds; the model-level DESIGN table.
`transfer`    sigma_d on bull_trap for each model (24 seed-level pairs), the ratio with a 90 % paired path bootstrap,
              and the main grid's plug-in sigma_UCL(Flash) x max(1, r).

Outputs: docs/env_v2/generated/v2_1/e8_5/{per_run.csv, components.{csv,json}, power.{csv,json,md}, transfer.json}
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
warnings.filterwarnings("ignore")

from tools.phase8 import e8_5_variance_pilot as E   # noqa: E402

OUT = E.OUT
DELTA = 0.05                  # D12 (P8-1), band-MAS
POWER = 0.80
ALPHA = 0.05
PLUGIN_Q = 0.90               # one-sided 90 % upper confidence limit (P8-1)
SENS_Q = (0.80, 0.95)
N_BOOT = 2000
TIER_A = {"seeds": 5, "reps": 1}
KEYS = ["Model", "Persona", "Arm", "Scenario", "Seed", "Decode_Replicate"]


def metric_names():
    from evaluation.metrics_v2 import thetas_in_force
    ths = thetas_in_force()
    out = ["band_mas"]
    for th in sorted(ths, reverse=True):
        out += [f"v21_mcr_B_{th}", f"v21_mcr_D_{th}", f"v21_mcr_{th}"]
    return out + ["turnover"]


# =================================================================================================== score
def stage_score():
    from evaluation import scoring_params as SP
    from evaluation.metrics_v2 import score_run, thetas_in_force
    SP.load()                                               # the loud loader, before any table under the file
    rows = []
    for which in ("main", "transfer"):
        model, cells = E.design(which)
        done = E.done_ids(model)
        for c in cells:
            cfg = E.cfg_for(model, c)
            if cfg.run_id() not in done:
                continue
            df = pd.read_csv(E.run_paths(cfg)["csv"])
            m = score_run(df, cfg.persona, scoring="v2_1")
            u = json.load(open(E.run_paths(cfg)["usage"], encoding="utf-8"))
            rows.append({"Model": model, "Persona": cfg.persona, "Arm": cfg.arm, "Scenario": cfg.scenario, "Seed": cfg.seed,
                         "Decode_Replicate": cfg.decode_replicate, "Path": f"{cfg.scenario}|{cfg.seed}",
                         "Temperature": float(df["Temperature"].iloc[0]), "usd": u["usd"],
                         **{k: m.get(k) for k in metric_names() + ["mdd_pct", "return_pct", "fallback_share", "trade_count"]}})
    t = pd.DataFrame(rows)
    os.makedirs(OUT, exist_ok=True)
    t.to_csv(os.path.join(OUT, "per_run.csv"), index=False)
    json.dump({"scoring_json_sha256": SP.SHA256, "thetas_in_force": list(thetas_in_force()), "n_runs": int(len(t)),
               "by_model": t.groupby("Model").size().to_dict() if len(t) else {},
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "per_run.meta.json"), "w", encoding="utf-8"), indent=1)
    print("scored", len(t), "runs", t.groupby("Model").size().to_dict() if len(t) else {})


# =================================================================================================== components
def plug_ins(t: pd.DataFrame, metric: str) -> dict:
    """The model-free quantities of PREREG 5.4 (2) on one model's runs."""
    cell = t.groupby(["Persona", "Arm", "Scenario", "Seed"])[metric]
    cm = cell.mean().unstack("Arm")
    nrep = cell.size().unstack("Arm")
    d = (cm["memory"] - cm["static"]).dropna()
    grp = d.groupby(level=["Persona", "Scenario"])
    resid = d - grp.transform("mean")
    df_d = int(len(d) - grp.ngroups)
    s2_d = float((resid ** 2).sum() / df_d) if df_d > 0 else float("nan")
    dev = t[metric] - cell.transform("mean")
    n_cells = int(cell.ngroups)
    df_rep = int(len(t) - n_cells)
    s2_rep = float((dev ** 2).sum() / df_rep) if df_rep > 0 else float("nan")
    R = float(stats.hmean(nrep.to_numpy().ravel()[np.isfinite(nrep.to_numpy().ravel())])) if nrep.size else 1.0
    s2_int = max(0.0, s2_d - 2 * s2_rep / R) if np.isfinite(s2_d) and np.isfinite(s2_rep) else float("nan")
    return {"n_pairs": int(len(d)), "df_d": df_d, "sigma_d_R": math.sqrt(s2_d) if np.isfinite(s2_d) else float("nan"),
            "R_harmonic": R, "sigma2_rep": s2_rep, "df_rep": df_rep, "sigma2_int": s2_int,
            **{f"sigma_d_R{r}": math.sqrt(s2_int + 2 * s2_rep / r) if np.isfinite(s2_int) else float("nan") for r in (1, 2, 3)},
            "mean_d": float(d.mean()), "share_int_R1": s2_int / (s2_int + 2 * s2_rep) if np.isfinite(s2_int) and (s2_int + 2 * s2_rep) > 0 else float("nan")}


def mls_ucl_sigma_d(ms_d: float, df_d: int, ms_rep: float, df_rep: int, R: float, R_prime: int, q: float = PLUGIN_Q) -> float:
    """A closed-form one-sided upper limit for sigma_d(R'), the modified large-sample bound for a non-negative
    combination of independent mean squares (Graybill & Wang 1980; not re-read -- its coverage is MEASURED on known
    answers, e8_5/validate.json, and nothing is taken from the paper but the form).

    sigma_d(R')^2 = sigma^2_int + 2 sigma^2_rep / R' = E[MS_d] + (2/R' - 2/R) E[MS_rep], with MS_d the seed-level pair
    variance (df_d) and MS_rep the replicate variance (df_rep).  For R' <= R both coefficients are >= 0 and
        U = theta + sqrt( (c_d MS_d H_d)^2 + (c_rep MS_rep H_rep)^2 ),  H = df / chi2_{1-q}(df) - 1;
    at R' = R it reduces exactly to the chi-square limit MS_d df_d / chi2_{1-q}(df_d)
    (`test_mls_limit_reduces_to_chi_square`).  Added after the registered percentile path bootstrap was measured to
    cover a 90 % limit only 60-67 % of the time (PREREG_PHASE_8_ADDENDUM.md 16) -- before any pilot number was read."""
    c_d, c_rep = 1.0, 2.0 / R_prime - 2.0 / R
    if not (np.isfinite(ms_d) and np.isfinite(ms_rep)) or df_d <= 0 or df_rep <= 0 or c_rep < -1e-12:
        return float("nan")
    c_rep = max(c_rep, 0.0)
    h_d = df_d / stats.chi2.ppf(1 - q, df_d) - 1.0
    h_rep = df_rep / stats.chi2.ppf(1 - q, df_rep) - 1.0
    theta = c_d * ms_d + c_rep * ms_rep
    return float(math.sqrt(theta + math.sqrt((c_d * ms_d * h_d) ** 2 + (c_rep * ms_rep * h_rep) ** 2)))


def boot_plug_ins(t: pd.DataFrame, metric: str, rng, n_boot=N_BOOT) -> dict:
    """Percentile cluster bootstrap over paths within scenario (PREREG 5.5)."""
    paths = {sc: sorted(g["Seed"].unique()) for sc, g in t.groupby("Scenario")}
    draws = {f"sigma_d_R{r}": [] for r in (1, 2, 3)}
    by_path = {(sc, s): g for (sc, s), g in t.groupby(["Scenario", "Seed"])}
    for _ in range(n_boot):
        parts = []
        for sc, seeds in paths.items():
            for j, s in enumerate(rng.choice(seeds, len(seeds), replace=True)):
                g = by_path[(sc, s)].copy()
                g["Seed"] = f"{s}#{j}"
                parts.append(g)
        p = plug_ins(pd.concat(parts, ignore_index=True), metric)
        for k in draws:
            draws[k].append(p[k])
    out = {}
    for k, v in draws.items():
        v = np.asarray(v, float)
        for q in (PLUGIN_Q,) + SENS_Q:
            out[f"{k}_ucl{int(q * 100)}"] = float(np.nanquantile(v, q))
    return out


def _balanced_array(t: pd.DataFrame, metric: str):
    """The runs as one array Y[persona, arm (static, memory), scenario, seed position, replicate] when the design is
    complete and every cell has the same replicate count >= 2; None otherwise (the loop is then used)."""
    if set(t["Arm"].unique()) != {"static", "memory"} or t[metric].isna().any():
        return None
    personas = sorted(t["Persona"].unique())
    scen = [sc for sc, _ in t.groupby("Scenario")]                       # groupby order, as the loop iterates it
    seeds_by_sc = {sc: sorted(g["Seed"].unique()) for sc, g in t.groupby("Scenario")}
    S = {len(v) for v in seeds_by_sc.values()}
    reps = sorted(t["Decode_Replicate"].unique())
    if len(S) != 1 or len(reps) < 2:
        return None
    S = S.pop(); R = len(reps); P, C = len(personas), len(scen)
    if len(t) != P * 2 * C * S * R:
        return None
    pi = {p: i for i, p in enumerate(personas)}; ai = {"static": 0, "memory": 1}; ci = {c: i for i, c in enumerate(scen)}
    si = {c: {s: j for j, s in enumerate(v)} for c, v in seeds_by_sc.items()}; ri = {r: k for k, r in enumerate(reps)}
    Y = np.full((P, 2, C, S, R), np.nan)
    for p, a, c, s, r, y in zip(t["Persona"], t["Arm"], t["Scenario"], t["Seed"], t["Decode_Replicate"], t[metric]):
        Y[pi[p], ai[a], ci[c], si[c][s], ri[r]] = y
    if np.isnan(Y).any():
        return None
    return Y, scen, seeds_by_sc


def boot_plug_ins_fast(t: pd.DataFrame, metric: str, rng, n_boot=N_BOOT) -> dict:
    """`boot_plug_ins` as array arithmetic -- the same resamples (the seeds are drawn with the same generator calls, in
    the same order, as the loop draws them) and the same statistics, computed over all draws at once.  Proven equal to
    the loop (`tests/test_v2_1_phase_8.py::test_boot_plug_ins_fast_equals_loop`; rule 18).  An incomplete design, or
    one with a single replicate, falls back to the loop."""
    arr = _balanced_array(t, metric)
    if arr is None:
        return boot_plug_ins(t, metric, rng, n_boot)
    Y, scen, seeds_by_sc = arr
    P, _, C, S, R = Y.shape
    idx = np.empty((n_boot, C, S), dtype=int)
    pos = {c: {s: j for j, s in enumerate(v)} for c, v in seeds_by_sc.items()}
    for b in range(n_boot):
        for c_i, sc in enumerate(scen):
            seeds = seeds_by_sc[sc]
            idx[b, c_i] = [pos[sc][s] for s in rng.choice(seeds, len(seeds), replace=True)]
    cm = Y.mean(axis=-1)                                                   # (P, 2, C, S) cell means
    ss = ((Y - cm[..., None]) ** 2).sum(axis=-1)                           # (P, 2, C, S) within-cell sums of squares
    gather = np.broadcast_to(idx[:, None, None, :, :], (n_boot, P, 2, C, S))
    cm_b = np.take_along_axis(np.broadcast_to(cm, (n_boot, P, 2, C, S)), gather, axis=-1)
    ss_b = np.take_along_axis(np.broadcast_to(ss, (n_boot, P, 2, C, S)), gather, axis=-1)
    d = cm_b[:, :, 1] - cm_b[:, :, 0]                                      # (B, P, C, S) memory - static
    resid = d - d.mean(axis=-1, keepdims=True)
    s2_d = (resid ** 2).sum(axis=(1, 2, 3)) / (P * C * S - P * C)
    s2_rep = ss_b.sum(axis=(1, 2, 3, 4)) / (P * 2 * C * S * (R - 1))
    s2_int = np.maximum(0.0, s2_d - 2 * s2_rep / R)
    out = {}
    for r in (1, 2, 3):
        v = np.sqrt(s2_int + 2 * s2_rep / r)
        for q in (PLUGIN_Q,) + SENS_Q:
            out[f"sigma_d_R{r}_ucl{int(q * 100)}"] = float(np.nanquantile(v, q))
    return out


def reml(t: pd.DataFrame, metric: str) -> dict:
    import statsmodels.formula.api as smf
    d = t.dropna(subset=[metric]).copy()
    d["y"] = d[metric].astype(float)
    form = "y ~ C(Arm) * C(Persona)" + (" * C(Scenario)" if d["Scenario"].nunique() > 1 else "")
    try:
        r = smf.mixedlm(form, d, groups=np.ones(len(d)), re_formula="0",
                        vc_formula={"path": "0 + C(Path)", "path_arm": "0 + C(Path):C(Arm)"}).fit(reml=True, method="lbfgs", maxiter=500)
        vc = dict(zip(r.model.exog_vc.names, np.asarray(r.vcomp, float)))
        tot = vc.get("path", 0) + vc.get("path_arm", 0) + r.scale
        return {"reml_sigma2_path": vc.get("path"), "reml_sigma2_path_arm": vc.get("path_arm"), "reml_sigma2_rep": float(r.scale),
                "icc_path": vc.get("path", 0) / tot, "icc_path_arm": vc.get("path_arm", 0) / tot,
                "reml_converged": bool(r.converged), "reml_n": int(len(d))}
    except Exception as e:                                     # noqa: BLE001
        return {"reml_error": f"{type(e).__name__}: {str(e)[:100]}"}


def stage_components():
    t = pd.read_csv(os.path.join(OUT, "per_run.csv"))
    rows = []
    rng = np.random.default_rng(8508)
    for model, tm in t.groupby("Model"):
        for metric in metric_names():
            tt = tm.dropna(subset=[metric])
            p = plug_ins(tt, metric)
            chi_ucl = math.sqrt(p["df_d"] * p["sigma_d_R"] ** 2 / stats.chi2.ppf(1 - PLUGIN_Q, p["df_d"])) if p["df_d"] > 0 else float("nan")
            # the closed-form limit that sizes the grid (P8-15), beside the registered bootstrap limit
            mls = {f"sigma_d_R{r}_mls90": mls_ucl_sigma_d(p["sigma_d_R"] ** 2, p["df_d"], p["sigma2_rep"], p["df_rep"],
                                                          p["R_harmonic"], r) for r in (1, 2, 3)}
            rows.append({"Model": model, "metric": metric, "n_runs": int(len(tt)), **p, "sigma_d_R_chi2_ucl90": chi_ucl,
                         **mls, **boot_plug_ins_fast(tt, metric, rng), **reml(tt, metric)})
            print(model, metric, {k: round(v, 5) for k, v in rows[-1].items() if isinstance(v, float) and k.startswith(("sigma_d_R1", "sigma2", "icc"))}, flush=True)
    c = pd.DataFrame(rows)
    c.to_csv(os.path.join(OUT, "components.csv"), index=False)
    json.dump({"plugin_quantile": PLUGIN_Q, "n_boot": N_BOOT, "rows": json.loads(c.to_json(orient="records"))},
              open(os.path.join(OUT, "components.json"), "w", encoding="utf-8"), indent=1)


# =================================================================================================== power
def m_q1_c(n_personas=3, n_scen=4, n_tier_c=3, n_contrasts=1) -> int:
    return n_contrasts * n_personas * n_scen * n_tier_c


def n_seeds(sigma, delta, alpha, factor2=True):
    z = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(POWER)
    return int(math.ceil((2 if factor2 else 1) * z * z * sigma * sigma / (delta * delta)))


def mdd(sigma, n, alpha, factor2=True):
    z = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(POWER)
    return math.sqrt(2 if factor2 else 1) * z * sigma / math.sqrt(n)


def power_t_two_sided(tcrit: float, df: int, ncp: float) -> float:
    """P(|T| > tcrit) for T ~ noncentral t(df, ncp), by integrating the normal tail over the chi-square scale:
    P(T > c) = E_V[Phi(ncp - c sqrt(V/df))] and P(T < -c) = E_V[Phi(-ncp - c sqrt(V/df))], V ~ chi2(df).  scipy's
    `nct.cdf` returned NaN at df 7, ncp 6.8 (the model-level DESIGN table's M = 8 row), so the integral is used for
    every row; it equals `nct` wherever that is finite (`test_power_t_two_sided_matches_nct`)."""
    from scipy import integrate
    upper = float(stats.chi2.ppf(1 - 1e-14, df))
    # geometric segments from 1e-14: at df 1 and tcrit ~ 458 (M = 2 at alpha') all the mass sits at V < 6e-5, which one
    # adaptive quad over [0, upper] never samples
    edges = np.concatenate([[0.0], np.logspace(-14, math.log10(upper), 60)])

    def tail(v, sign):
        return stats.norm.cdf(sign * ncp - tcrit * math.sqrt(v / df)) * stats.chi2.pdf(v, df)

    total = 0.0
    for a, b in zip(edges[:-1], edges[1:]):
        for sign in (1.0, -1.0):
            total += integrate.quad(tail, a, b, args=(sign,), limit=200)[0]
    return float(total)


def stage_power():
    c = pd.read_csv(os.path.join(OUT, "components.csv"))
    main = c[c.Model == E.MAIN_MODEL].set_index("metric")
    m = m_q1_c()
    a_b = ALPHA / m
    rows = []
    bm = main.loc["band_mas"]
    sized = {}
    for R in (1, 2, 3):
        sig = bm[f"sigma_d_R{R}_mls90"]            # PRIMARY: the closed-form limit (P8-15; addendum 16)
        sig_b = bm[f"sigma_d_R{R}_ucl90"]          # the registered percentile path bootstrap, beside
        sized[R] = {"sigma_limit": sig, "sigma_point": bm[f"sigma_d_R{R}"],
                    "appA_bonf": n_seeds(sig, DELTA, a_b), "paired_bonf": n_seeds(sig, DELTA, a_b, False),
                    "appA_nominal": n_seeds(sig, DELTA, ALPHA), "paired_nominal": n_seeds(sig, DELTA, ALPHA, False),
                    "appA_bonf_at_point": n_seeds(bm[f"sigma_d_R{R}"], DELTA, a_b),
                    "sigma_bootstrap_ucl90": sig_b, "appA_bonf_bootstrap": n_seeds(sig_b, DELTA, a_b),
                    **{f"appA_bonf_bootstrap_ucl{int(q * 100)}": n_seeds(bm[f"sigma_d_R{R}_ucl{int(q * 100)}"], DELTA, a_b)
                       for q in SENS_Q}}
        sized[R]["runs_per_contrast_cell_appA_bonf"] = 2 * sized[R]["appA_bonf"] * R
    designs = {"E8.5 (8 seeds, 3 reps)": (8, 3), "Tier A (5 seeds, 1 rep)": (TIER_A["seeds"], TIER_A["reps"]),
               "band-MAS-sized (R=1, App. A, Bonferroni)": (sized[1]["appA_bonf"], 1)}
    for metric, r in main.iterrows():
        for dname, (n, R) in designs.items():
            sig = r[f"sigma_d_R{R}_mls90"]; sig_b = r[f"sigma_d_R{R}_ucl90"]
            rows.append({"metric": metric, "design": dname, "seeds_per_cell": n, "reps": R, "sigma_limit": sig,
                         "sigma_point": r[f"sigma_d_R{R}"], "sigma_bootstrap_ucl90": sig_b,
                         "mdd_appA_bonf": mdd(sig, n, a_b), "mdd_paired_bonf": mdd(sig, n, a_b, False),
                         "mdd_appA_nominal": mdd(sig, n, ALPHA), "mdd_paired_nominal": mdd(sig, n, ALPHA, False),
                         "mdd_appA_bonf_bootstrap": mdd(sig_b, n, a_b)})
    t = pd.DataFrame(rows)
    # replicates against seeds (PREREG 5.5): variance of the mean contrast x runs, per run of cost
    rvs = [{"metric": metric, "R": R, "var_x_cost": R * r["sigma2_int"] + 2 * r["sigma2_rep"],
            "share_int_R1": r["share_int_R1"]} for metric, r in main.iterrows() for R in (1, 2, 3)]
    # model-level DESIGN table: M models, each with the band-MAS-sized seeds at R = 1; between-model sd tau
    ml = []
    sig1 = bm["sigma_d_R1_mls90"]; n1 = sized[1]["appA_bonf"]
    for M in (2, 3, 5, 8):
        for mult in (0.5, 1.0, 2.0):
            tau = mult * sig1
            se = math.sqrt((tau ** 2 + sig1 ** 2 / n1) / M)
            df = M - 1
            tcrit = stats.t.ppf(1 - a_b / 2, df)
            ncp = DELTA / se
            pw = power_t_two_sided(tcrit, df, ncp)
            ml.append({"models": M, "tau_over_sigma": mult, "tau": tau, "seeds_per_cell": n1, "power_bonf": pw, "label": "DESIGN",
                       "power_method": "noncentral t by integration over the chi-square (power_t_two_sided)"})
    doc = {"delta_band_mas": DELTA, "power": POWER, "alpha": ALPHA, "m_Q1_C": m, "alpha_bonferroni": a_b,
           "plugin": ("PRIMARY: the closed-form one-sided 90 % limit (modified large-sample; known-answer coverage "
                      "0.915-0.945); BESIDE: the registered percentile path-bootstrap limit (coverage 0.60-0.67 when "
                      "seed x arm variance is present) -- P8-15, addendum 16"),
           "sized_band_mas": sized,
           "mdd": json.loads(t.to_json(orient="records")), "replicates_vs_seeds": rvs, "model_level_DESIGN": ml,
           "note_D": "P8-2: no Delta_D is stipulated; D's minimum detectable difference at the band-MAS-sized design is its achieved power, in D's units",
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    t.to_csv(os.path.join(OUT, "power.csv"), index=False)
    json.dump(doc, open(os.path.join(OUT, "power.json"), "w", encoding="utf-8"), indent=1, default=float)
    print(json.dumps(sized, indent=1, default=float))
    print(t.round(4).to_string(index=False))


# =================================================================================================== transfer
def _transfer_picks(bt: pd.DataFrame, rng, n_boot: int):
    """The shared seed resamples of the transfer bootstrap, drawn in the order the loop draws them."""
    seeds = sorted(bt["Seed"].unique())
    return seeds, [rng.choice(seeds, len(seeds), replace=True) for _ in range(n_boot)]


def transfer_ratios_loop(bt: pd.DataFrame, metric: str, picks) -> np.ndarray:
    """The reference: sigma_d(GPT-5 mini) / sigma_d(Flash) on each shared resample of bull_trap's seeds."""
    ratios = []
    for pick in picks:
        parts = {mdl: pd.concat([bt[(bt.Model == mdl) & (bt.Seed == sd)].assign(Seed=f"{sd}#{j}") for j, sd in enumerate(pick)])
                 for mdl in (E.MAIN_MODEL, E.TRANSFER_MODEL)}
        a = plug_ins(parts[E.MAIN_MODEL].dropna(subset=[metric]), metric)["sigma_d_R"]
        b = plug_ins(parts[E.TRANSFER_MODEL].dropna(subset=[metric]), metric)["sigma_d_R"]
        ratios.append(b / a if a and np.isfinite(a) and a > 0 else np.nan)
    return np.asarray(ratios, float)


def _sigma_d_draws(tm: pd.DataFrame, metric: str, picks):
    """sigma_d at the observed replicate count (plug_ins' `sigma_d_R`) on every resample of a one-scenario frame, as
    array arithmetic; None when the frame is not balanced (the loop is then used)."""
    arr = _balanced_array(tm, metric)
    if arr is None:
        return None
    Y, scen, seeds_by_sc = arr
    if len(scen) != 1:
        return None
    pos = {s: j for j, s in enumerate(seeds_by_sc[scen[0]])}
    try:
        idx = np.array([[pos[s] for s in pick] for pick in picks], dtype=int)      # (B, S)
    except KeyError:
        return None
    cm = Y.mean(axis=-1)[:, :, 0, :]                                               # (P, 2, S)
    d = cm[:, 1, :] - cm[:, 0, :]                                                  # (P, S)
    d_b = d[:, idx]                                                                # (P, B, S)
    resid = d_b - d_b.mean(axis=-1, keepdims=True)
    P, S = d.shape
    return np.sqrt((resid ** 2).sum(axis=(0, 2)) / (P * S - P))                    # (B,)


def transfer_ratios_fast(bt: pd.DataFrame, metric: str, picks) -> np.ndarray:
    """`transfer_ratios_loop` as array arithmetic -- the same resamples, the same statistic; proven equal
    (`test_transfer_ratios_fast_equals_loop`, rule 18); falls back to the loop on an unbalanced frame."""
    fa = bt[bt.Model == E.MAIN_MODEL].dropna(subset=[metric])
    fb = bt[bt.Model == E.TRANSFER_MODEL].dropna(subset=[metric])
    a = _sigma_d_draws(fa, metric, picks)
    b = _sigma_d_draws(fb, metric, picks)
    if a is None or b is None:
        return transfer_ratios_loop(bt, metric, picks)
    ok = np.isfinite(a) & (a > 0)
    return np.where(ok, b / np.where(ok, a, 1.0), np.nan)


def stage_transfer():
    t = pd.read_csv(os.path.join(OUT, "per_run.csv"))
    bt = t[t.Scenario == "bull_trap"]
    rng = np.random.default_rng(8506)
    out = {}
    for metric in metric_names():
        s, parts = {}, {}
        for model in (E.MAIN_MODEL, E.TRANSFER_MODEL):
            tm = bt[bt.Model == model].dropna(subset=[metric])
            parts[model] = plug_ins(tm, metric) if len(tm) else {}
            s[model] = parts[model].get("sigma_d_R", float("nan"))
        seeds, picks = _transfer_picks(bt, rng, N_BOOT)
        ratios = transfer_ratios_fast(bt, metric, picks)
        r = s[E.TRANSFER_MODEL] / s[E.MAIN_MODEL] if s[E.MAIN_MODEL] else float("nan")
        a, b = parts[E.MAIN_MODEL], parts[E.TRANSFER_MODEL]
        out[metric] = {"sigma_d_flash_bull_trap": s[E.MAIN_MODEL], "sigma_d_gpt5mini_bull_trap": s[E.TRANSFER_MODEL],
                       "ratio": r, "ratio_ci90": [float(np.nanquantile(ratios, 0.05)), float(np.nanquantile(ratios, 0.95))],
                       # where the difference sits (descriptive, beside the registered ratio): replicate vs seed x arm
                       "sigma2_rep_flash_bull_trap": a.get("sigma2_rep"), "sigma2_rep_gpt5mini_bull_trap": b.get("sigma2_rep"),
                       "sigma2_int_flash_bull_trap": a.get("sigma2_int"), "sigma2_int_gpt5mini_bull_trap": b.get("sigma2_int"),
                       "ratio_R1": (b.get("sigma_d_R1") / a.get("sigma_d_R1")) if a.get("sigma_d_R1") else float("nan")}
    comp = pd.read_csv(os.path.join(OUT, "components.csv"))
    flash = comp[(comp.Model == E.MAIN_MODEL) & (comp.metric == "band_mas")].iloc[0]
    rb = out["band_mas"]
    lim = float(flash["sigma_d_R1_mls90"])                 # the closed-form limit (P8-15)
    boot = float(flash["sigma_d_R1_ucl90"])                # the registered bootstrap limit, beside
    plug = {"sigma_limit_flash_R1": lim, "sigma_bootstrap_ucl90_flash_R1": boot, "ratio": rb["ratio"],
            "plugin_main_grid": lim * max(1.0, rb["ratio"]),
            "plugin_at_ratio_upper": lim * max(1.0, rb["ratio_ci90"][1]),
            "plugin_main_grid_bootstrap": boot * max(1.0, rb["ratio"])}
    # the seeds per persona x scenario cell the main grid needs at that plug-in (Appendix A, Bonferroni; PREREG 5.5-5.6)
    a_b = ALPHA / m_q1_c()
    plug.update({"alpha_bonferroni": a_b,
                 "seeds_appA_bonf_main_grid": n_seeds(plug["plugin_main_grid"], DELTA, a_b),
                 "seeds_paired_bonf_main_grid": n_seeds(plug["plugin_main_grid"], DELTA, a_b, False),
                 "seeds_appA_bonf_at_ratio_upper": n_seeds(plug["plugin_at_ratio_upper"], DELTA, a_b),
                 "seeds_appA_bonf_main_grid_bootstrap": n_seeds(plug["plugin_main_grid_bootstrap"], DELTA, a_b)})
    # P8-2's achieved power at the design actually sized: every metric's own limit x max(1, its own ratio), at the main
    # grid's seed count
    flash_all = comp[comp.Model == E.MAIN_MODEL].set_index("metric")
    for metric, v in out.items():
        v["sigma_limit_main_grid"] = float(flash_all.loc[metric, "sigma_d_R1_mls90"]) * max(1.0, v["ratio"])
        v["mdd_appA_bonf_main_grid"] = mdd(v["sigma_limit_main_grid"], plug["seeds_appA_bonf_main_grid"], a_b)
    doc = {"per_metric": out, "band_mas_plugin": plug,
           "temperature": {E.MAIN_MODEL: E.TEMPERATURE[E.MAIN_MODEL], E.TRANSFER_MODEL: E.TEMPERATURE[E.TRANSFER_MODEL]},
           "caveat": "GPT-5 mini runs at temperature 1.0 (the only value the provider accepts): the ratio is a transfer of model AND temperature"}
    json.dump(doc, open(os.path.join(OUT, "transfer.json"), "w", encoding="utf-8"), indent=1, default=float)
    print(json.dumps(doc, indent=1, default=float))


# =================================================================================================== unregistered checks
def stage_reml_pp():
    """UNREGISTERED (PREREG_PHASE_8_ADDENDUM.md 17): where Flash's variance sits once persona x path and persona x path x
    arm join the registered {path, path x arm}.  Implied sigma_d(R = 1) = sqrt(2 (path_arm + persona_path_arm) +
    2 replicate), checked against the plug-in.  Fitted by lbfgs, as first computed; Powell's REML log-likelihood beside
    (a local optimum would show as a gap).  -> e8_5/components_reml_persona_path.json, whose band-MAS components
    `e8_3_simulate --stages mixed_pp` plants."""
    import statsmodels.formula.api as smf
    t = pd.read_csv(os.path.join(OUT, "per_run.csv"))
    t = t[t.Model == E.MAIN_MODEL].copy()
    out = {}
    for metric in ["band_mas", "v21_mcr_D_0.05", "v21_mcr_D_0.002", "turnover"]:
        d = t.dropna(subset=[metric]).copy()
        d["y"] = d[metric].astype(float)
        vc = {"path": "0 + C(Path)", "path_arm": "0 + C(Path):C(Arm)",
              "persona_path": "0 + C(Persona):C(Path)", "persona_path_arm": "0 + C(Persona):C(Path):C(Arm)"}
        md = smf.mixedlm("y ~ C(Arm) * C(Persona) * C(Scenario)", d, groups=np.ones(len(d)), re_formula="0", vc_formula=vc)
        r = md.fit(reml=True, method="lbfgs", maxiter=1000)
        comp = dict(zip(r.model.exog_vc.names, map(float, r.vcomp)))
        comp["replicate"] = float(r.scale)
        tot = sum(comp.values())
        s2d1 = 2 * (comp["path_arm"] + comp["persona_path_arm"]) + 2 * comp["replicate"]
        try:
            llf_powell = float(md.fit(reml=True, method="powell", maxiter=4000).llf)
        except Exception:                                    # noqa: BLE001
            llf_powell = float("nan")
        out[metric] = {"components": comp, "icc": {k: v / tot for k, v in comp.items()}, "converged": bool(r.converged),
                       "implied_sigma_d_R1": float(np.sqrt(s2d1)), "n": int(len(d)),
                       "llf_lbfgs": float(r.llf), "llf_powell": llf_powell}
        print(metric, {k: f"{v:.3g}" for k, v in comp.items()}, "implied sigma_d(R=1)", round(out[metric]["implied_sigma_d_R1"], 5),
              "llf lbfgs / powell", round(r.llf, 3), round(llf_powell, 3), flush=True)
    json.dump(out, open(os.path.join(OUT, "components_reml_persona_path.json"), "w", encoding="utf-8"), indent=1)


def stage_e1_pairing():
    """UNREGISTERED (PREREG_PHASE_8_ADDENDUM.md 17): does E1 pair?  On Flash's band-MAS runs, the SE of the average
    memory - static contrast (sum-to-zero coding over the 12 persona x scenario cells) under E1's registered components,
    under E1 plus persona x path terms, and the model-free paired SE of the seed-level differences (84 df) -- at R = 1
    (replicate 0) and R = 3.  Fitted by lbfgs, as first computed, and at the better of lbfgs and Powell beside.
    -> e8_5/e1_pairing_se.json"""
    import statsmodels.formula.api as smf
    from tools.stats_v2 import _reml_fit
    t = pd.read_csv(os.path.join(OUT, "per_run.csv"))
    t = t[t.Model == E.MAIN_MODEL].copy()
    t["y"] = t["band_mas"].astype(float)
    t["PP"] = t["Persona"] + "|" + t["Path"]
    t["A"] = t["Arm"].map({"static": "a_static", "memory": "b_memory"})    # sum coding: coefficient = (static - memory) / 2
    form = "y ~ C(A, Sum) * C(Persona, Sum) * C(Scenario, Sum)"
    term = "C(A, Sum)[S.a_static]"
    out = {"metric": "band_mas", "model": E.MAIN_MODEL, "contrast": "memory - static, averaged over persona x scenario cells"}
    for label, d, r1 in (("R1_replicate0", t[t.Decode_Replicate == 0], True), ("R3_all_replicates", t, False)):
        vc_reg = {"path": "0 + C(Path)"} if r1 else {"path": "0 + C(Path)", "path_arm": "0 + C(Path):C(A)"}
        vc_pp = dict(vc_reg, persona_path="0 + C(PP)")
        if not r1:
            vc_pp["persona_path_arm"] = "0 + C(PP):C(A)"
        fits = {}
        for name, vc in (("e1_registered", vc_reg), ("e1_plus_persona_path", vc_pp)):
            md = smf.mixedlm(form, d, groups=np.ones(len(d)), re_formula="0", vc_formula=vc)
            for opt in ("lbfgs", "best"):
                r = md.fit(reml=True, method="lbfgs", maxiter=2000) if opt == "lbfgs" else _reml_fit(md, "best")
                fits[f"{name}|{opt}"] = {"effect": float(-2 * r.params[term]), "se": float(2 * r.bse[term]),
                                         "llf": float(r.llf), "residual": float(r.scale), "converged": bool(r.converged),
                                         "vc": dict(zip(r.model.exog_vc.names, map(float, r.vcomp)))}
        cm = d.groupby(["Persona", "Scenario", "Seed", "Arm"])["y"].mean().unstack("Arm")
        dd = cm["memory"] - cm["static"]
        res = dd - dd.groupby(level=["Persona", "Scenario"]).transform("mean")
        paired_se = float(np.sqrt((res ** 2).sum() / (len(dd) - 12)) / np.sqrt(len(dd)))
        out[label] = {"n_runs": int(len(d)), "n_pairs": int(len(dd)), "paired_effect": float(dd.mean()), "paired_se": paired_se,
                      "fits": fits,
                      "se_ratio_over_paired": {k: v["se"] / paired_se for k, v in fits.items()},
                      "seeds_multiplier_registered_lbfgs": (fits["e1_registered|lbfgs"]["se"] / paired_se) ** 2}
        print(label, "paired SE", round(paired_se, 5), {k: round(v["se"], 5) for k, v in fits.items()}, flush=True)
    json.dump(out, open(os.path.join(OUT, "e1_pairing_se.json"), "w", encoding="utf-8"), indent=1)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="score,components,power,transfer")
    a = ap.parse_args(argv)
    for st in [s.strip() for s in a.stages.split(",") if s.strip()]:
        {"score": stage_score, "components": stage_components, "power": stage_power, "transfer": stage_transfer,
         "reml_pp": stage_reml_pp, "e1_pairing": stage_e1_pairing}[st]()


if __name__ == "__main__":
    main()
