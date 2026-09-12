"""
v2.1 Phase 9 -- E9.0: throughput measured from the ledgers, the wall-clock of every candidate design on every candidate
model at 10 and 15 concurrent calls per model (P9-1), and the model-level DESIGN power table at candidate roster sizes.
Makes no call; re-run after every smoke, pilot or batch.

    python -u -m tools.phase9.e9_wallclock --stages throughput,wallclock,model_power

`throughput`  Every ledger row, from E8.5's ledgers and Phase 9's, grouped by (model, config_tag, kind). Only runs that
              completed all their calls enter. Per group:
              * runs, mean / median / p90 seconds per run, seconds per call;
              * the busy wall time: the union of the runs' [start, end] intervals;
              * runs per busy hour, and effective concurrency = sum(seconds) / busy time;
              * runs per stream-hour = 3600 / mean seconds;
              * $ per run where a price was read, and tokens per call.
              kind is "batch" (E8.5's per-model ledgers; Phase 9's pilot and grid ledgers) or "smoke". A smoke's two
              runs share the provider with little else, so its seconds per run are a LOWER bound on a batch's. The
              measured batch / smoke ratio of every configuration that has both is written beside.
`wallclock`   hours per model = runs / (streams x runs per stream-hour), for every candidate design in `e9_designs`,
              at the seed counts `e9_designs.seeds_grid()` reads from the inference parameters, at 10 and 15 streams.
              A configuration timed by smoke only carries its smoke rate and, beside it, that rate scaled by the largest
              measured batch / smoke ratio. A roster's wall-clock is its slowest member's, because every model runs at
              once. A register design that runs on one model (REG-1, REG-9) is priced on Flash only.
`model_power` The model-level DESIGN table: Appendix A's model-level version with a t reference on M - 1 df (P8-17;
              e8_5/power.json's construction). Power to detect D12's Delta at alpha' and at nominal alpha, for M in
              ROSTER_SIZES, at the table's seed counts, with a between-model sd of the per-model arm effect
              tau = {0.5, 1, 2} x Flash's sigma_d limit. The within-model sigma_d is the main grid's plug-in (0.0841),
              with Flash's limit beside. Phase 8's M = 8 row is reproduced before anything is written. The reference
              distribution itself is E9.3's to simulate; this table is the analytic t row only.

Outputs: docs/env_v2/generated/v2_1/e9_0/{throughput.{csv,json}, wallclock.{csv,json}, model_power.{csv,json}}
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e9_0")
T = 200
STREAMS = (10, 15)                               # P9-1: 10-15 in-flight calls per model
ROSTER_SIZES = (2, 3, 4, 5, 6, 8, 10, 12, 14)
TAU_MULTS = (0.5, 1.0, 2.0)                      # e8_5/power.json's convention: tau = mult x Flash's sigma_d limit
POWER_TARGET = 0.80
MAX_M_SEARCH = 60


def _rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


# ============================================================================================ ledgers
def _is_uncapped_openrouter(r: dict) -> bool:
    """PREREG_PHASE_9_ADDENDUM.md 8: the FIRST OpenRouter smoke ran before the registered `max_tokens` existed, and
    its runs are discarded.  They are 200-call runs, so no call-count filter removes them; the one thing that tells
    them from the registered configuration is the cap the client held.  A first-party route sends no cap BY DESIGN
    (only OpenRouter needs one), so the test is on the provider as well."""
    po = r.get("provider_options") or {}
    return po.get("provider") == "openrouter" and po.get("max_tokens_client") in (None, "")


def read_ledgers() -> pd.DataFrame:
    rows = []
    for p in sorted(glob.glob(os.path.join(GEN, "e8_5", "ledger*.jsonl"))):
        kind = "smoke" if os.path.basename(p) == "ledger.jsonl" else "batch"
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    rows.append({**json.loads(line), "kind": kind, "ledger": _rel(p), "phase": 8})
    for p in sorted(glob.glob(os.path.join(GEN, "e9_*", "**", "ledger*.jsonl"), recursive=True)):
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    r = json.loads(line)
                    rows.append({**r, "kind": r.get("kind", "unknown"), "ledger": _rel(p), "phase": 9})
    n_uncapped = sum(1 for r in rows if _is_uncapped_openrouter(r))
    rows = [r for r in rows if not _is_uncapped_openrouter(r)]
    t = pd.DataFrame(rows)
    if t.empty:
        return t
    t.attrs["uncapped_openrouter_rows_dropped"] = n_uncapped
    # E8.5's first smoke predates configuration tags (Flash at the provider-default thinking; addendum 8)
    t["config_tag"] = t["config_tag"].fillna("untagged") if "config_tag" in t else "untagged"
    t["calls_expected"] = t["calls_expected"].fillna(T) if "calls_expected" in t else T
    t["end"] = pd.to_datetime(t["utc"], utc=True).map(lambda x: x.timestamp())
    t["start"] = t["end"] - t["seconds"].astype(float)
    return t


def busy_seconds(starts, ends) -> float:
    """The measure of the union of [start, end] intervals."""
    iv = sorted(zip(map(float, starts), map(float, ends)))
    if not iv:
        return 0.0
    total, (cs, ce) = 0.0, iv[0]
    for s, e in iv[1:]:
        if s > ce:
            total += ce - cs
            cs, ce = s, e
        else:
            ce = max(ce, e)
    return total + ce - cs


def throughput_table(t: pd.DataFrame) -> pd.DataFrame:
    done = t[t["n_llm_calls"].astype(float) >= t["calls_expected"].astype(float)]
    out = []
    for (model, tag, kind), g in done.groupby(["model", "config_tag", "kind"], sort=True):
        sec = g["seconds"].astype(float)
        busy = busy_seconds(g["start"], g["end"])
        calls = g["n_llm_calls"].astype(float)
        usd = pd.to_numeric(g.get("usd"), errors="coerce") if "usd" in g else pd.Series(dtype=float)
        out.append({
            "model": model, "config_tag": tag, "kind": kind, "n_runs": int(len(g)),
            "n_status_ok": int((g["status"] == "ok").sum()),
            "mean_s_per_run": float(sec.mean()), "median_s_per_run": float(sec.median()),
            "p90_s_per_run": float(sec.quantile(0.9)), "s_per_call": float(sec.sum() / calls.sum()),
            "busy_hours": busy / 3600.0, "runs_per_busy_hour": float(len(g) / (busy / 3600.0)) if busy > 0 else float("nan"),
            "effective_concurrency": float(sec.sum() / busy) if busy > 0 else float("nan"),
            "runs_per_stream_hour": 3600.0 / float(sec.mean()),
            "usd_per_run": float(usd.mean()) if usd.notna().any() else float("nan"),
            "input_tokens_per_call": float(g["input_tokens"].astype(float).sum() / calls.sum()),
            "output_tokens_per_call": float(g["output_tokens"].astype(float).sum() / calls.sum()),
            "reasoning_tokens_per_call": float(g["reasoning_tokens"].astype(float).sum() / calls.sum()),
            "llm_errors": int(sum(len(e) for e in g.get("llm_errors", pd.Series([[]] * len(g))) if isinstance(e, list))),
            "fallbacks": int(pd.to_numeric(g.get("n_fallbacks"), errors="coerce").fillna(0).sum()),
            "temperature": ",".join(sorted({str(v) for v in g.get("temperature", pd.Series([None] * len(g)))})),
            "provider_options": ",".join(sorted({json.dumps(v, sort_keys=True) for v in g["provider_options"]}))
                                if "provider_options" in g else "",
            "first_utc": str(g["utc"].min()), "last_utc": str(g["utc"].max()),
            "ledgers": ",".join(sorted(set(g["ledger"]))),
        })
    tab = pd.DataFrame(out)
    ratios = []
    for (model, tag), g in tab.groupby(["model", "config_tag"]):
        kinds = set(g["kind"])
        if "batch" in kinds and "smoke" in kinds:
            b = float(g[g.kind == "batch"]["mean_s_per_run"].iloc[0]); s = float(g[g.kind == "smoke"]["mean_s_per_run"].iloc[0])
            ratios.append({"model": model, "config_tag": tag, "batch_over_smoke_mean_s": b / s,
                           "n_batch": int(g[g.kind == "batch"]["n_runs"].iloc[0]), "n_smoke": int(g[g.kind == "smoke"]["n_runs"].iloc[0])})
    tab.attrs["batch_smoke_ratios"] = ratios
    return tab


def stage_throughput():
    t = read_ledgers()
    tab = throughput_table(t)
    os.makedirs(OUT, exist_ok=True)
    tab.to_csv(os.path.join(OUT, "throughput.csv"), index=False)
    doc = {"rows": json.loads(tab.to_json(orient="records")), "batch_smoke_ratios": tab.attrs["batch_smoke_ratios"],
           "definitions": {"busy_hours": "measure of the union of the runs' [utc - seconds, utc] intervals",
                           "effective_concurrency": "sum of run seconds / busy seconds",
                           "runs_per_stream_hour": "3600 / mean seconds per run (one sequential stream)",
                           "completed": "n_llm_calls >= calls_expected (200 for a stateless run)"},
           "n_ledger_rows": int(len(t)), "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(doc, open(os.path.join(OUT, "throughput.json"), "w", encoding="utf-8"), indent=1, default=str)
    show = ["model", "config_tag", "kind", "n_runs", "mean_s_per_run", "median_s_per_run", "s_per_call", "busy_hours",
            "runs_per_busy_hour", "effective_concurrency", "runs_per_stream_hour", "usd_per_run", "llm_errors", "fallbacks"]
    print(tab[show].round(3).to_string(index=False))
    print("batch / smoke:", tab.attrs["batch_smoke_ratios"])


# ============================================================================================ wall-clock
def rate_sources(tab: pd.DataFrame) -> pd.DataFrame:
    """One row per (model, config_tag): the batch rate when a batch exists, else the smoke rate (a lower bound)."""
    ratios = [r["batch_over_smoke_mean_s"] for r in json.load(open(os.path.join(OUT, "throughput.json"), encoding="utf-8"))["batch_smoke_ratios"]]
    worst = max(ratios) if ratios else float("nan")
    out = []
    for (model, tag), g in tab.groupby(["model", "config_tag"]):
        if tag == "untagged":
            continue                          # E8.5's first smoke: a configuration no design runs (addendum 8)
        src = "batch" if "batch" in set(g["kind"]) else "smoke"
        r = g[g.kind == src].iloc[0]
        out.append({"model": model, "config_tag": tag, "source": src, "n_runs_timed": int(r["n_runs"]),
                    "runs_per_stream_hour": float(r["runs_per_stream_hour"]),
                    "runs_per_stream_hour_ratio_adjusted": float(r["runs_per_stream_hour"]) / worst if src == "smoke" else float(r["runs_per_stream_hour"]),
                    "worst_batch_smoke_ratio": worst})
    return pd.DataFrame(out)


def stage_wallclock():
    from tools.phase9.e9_designs import designs, seeds_grid
    tab = pd.read_csv(os.path.join(OUT, "throughput.csv"))
    src = rate_sources(tab)
    rows = []
    for d in designs().values():
        for S in (seeds_grid() if d.per_seed else (None,)):
            n = d.runs(S if S is not None else 1)
            models = src if d.all_models else src[(src.model == "gemini-2.5-flash") & (src.config_tag == "thinking0")]
            for _, m in models.iterrows():
                for k in STREAMS:
                    h = n / (k * m["runs_per_stream_hour"])
                    h_adj = n / (k * m["runs_per_stream_hour_ratio_adjusted"])
                    rows.append({"design": d.name, "design_label": d.label, "seeds_per_cell": S, "runs_per_model": n,
                                 "calls_per_run": d.calls_per_run, "stateful": d.stateful, "all_models": d.all_models,
                                 "model": m["model"], "config_tag": m["config_tag"], "rate_source": m["source"],
                                 "streams": k, "hours": h, "days": h / 24.0,
                                 "hours_smoke_ratio_adjusted": h_adj, "note": d.note})
    w = pd.DataFrame(rows)
    w.to_csv(os.path.join(OUT, "wallclock.csv"), index=False)
    json.dump({"rows": json.loads(w.to_json(orient="records")), "rate_sources": json.loads(src.to_json(orient="records")),
               "rule": "every model's batch runs at once; a roster's wall-clock is its slowest member's",
               "streams": list(STREAMS), "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "wallclock.json"), "w", encoding="utf-8"), indent=1, default=str)
    piv = w[w.streams == 15].pivot_table(index=["model", "config_tag", "rate_source"], columns=["design", "seeds_per_cell"],
                                         values="days", aggfunc="first")
    print(src.round(3).to_string(index=False))
    print("days at 15 streams:")
    print(piv.round(2).to_string())


# ============================================================================================ model-level power
_GL_X, _GL_W = np.polynomial.legendre.leggauss(64)
N_SEGMENTS = 60


def power_t_two_sided_fast(tcrit: float, df: int, ncp: float) -> float:
    """`tools.phase8.e8_5_analyse.power_t_two_sided` on the SAME geometric segments of the chi-square scale, each
    integrated by a fixed 64-point Gauss-Legendre rule instead of adaptive quadrature, as array arithmetic.  The
    adaptive form took ~1 s per value, and the table needs thousands.  Proven equal to the adaptive integral before
    the table is written (`stage_model_power`, stored in model_power.json) and in
    `tests/test_v2_1_phase_9.py::test_power_fast_equals_integral` (rule 18)."""
    upper = float(stats.chi2.ppf(1 - 1e-14, df))
    edges = np.concatenate([[0.0], np.logspace(-14, math.log10(upper), N_SEGMENTS)])
    a, b = edges[:-1], edges[1:]
    v = ((a + b) / 2)[:, None] + ((b - a) / 2)[:, None] * _GL_X[None, :]
    w = ((b - a) / 2)[:, None] * _GL_W[None, :]
    s = np.sqrt(v / df)
    tail = stats.norm.cdf(ncp - tcrit * s) + stats.norm.cdf(-ncp - tcrit * s)
    return float(np.sum(tail * stats.chi2.pdf(v, df) * w))


def model_power_rows():
    from experiments import inference_params as IP
    from tools.phase8.e8_5_analyse import power_t_two_sided
    from tools.phase9.e9_designs import seeds_grid
    sizing = IP.block("main_grid_sizing")["value"]
    sw_plugin = float(sizing["plugin_sigma_d"])
    sw_flash = float(IP.block("sigma_plugin")["value"]["band_mas_R1_limit"])
    a_b = float(sizing["alpha_bonferroni"])
    delta = float(IP.block("min_effect")["value"]["band_mas"])

    def args(M, S, tau, sw, alpha):
        se = math.sqrt((tau ** 2 + sw ** 2 / S) / M)
        return float(stats.t.ppf(1 - alpha / 2, M - 1)), M - 1, delta / se

    def power(M, S, tau, sw, alpha):
        pw = power_t_two_sided_fast(*args(M, S, tau, sw, alpha))
        if not (np.isfinite(pw) and -1e-9 <= pw <= 1 + 1e-9):
            raise SystemExit(f"power not finite / outside [0, 1] at M={M} S={S} tau={tau} sw={sw} alpha={alpha}: {pw} (rule 22)")
        return float(min(max(pw, 0.0), 1.0))

    # Phase 8's DESIGN row reproduced first, by the adaptive integral AND the fast rule (e8_5/power.json: M = 8,
    # tau = 0.5 x limit, 19 seeds, sigma = Flash's limit)
    ref = [r for r in json.load(open(os.path.join(GEN, "e8_5", "power.json"), encoding="utf-8"))["model_level_DESIGN"]
           if r["models"] == 8 and r["tau_over_sigma"] == 0.5][0]
    mine = power(8, int(ref["seeds_per_cell"]), 0.5 * sw_flash, sw_flash, a_b)
    if abs(mine - ref["power_bonf"]) > 1e-9:
        raise SystemExit(f"e8_5/power.json's M = 8 row not reproduced by the fast rule: {mine} against {ref['power_bonf']}")
    # the fast rule against the adaptive integral on a spread of the table's own arguments (the extremes of M, S, tau
    # and both alphas), before any row is written
    proof = []
    for M in (2, 3, 8, max(ROSTER_SIZES)):
        for S in (min(seeds_grid()), max(seeds_grid())):
            for mult in (min(TAU_MULTS), max(TAU_MULTS)):
                for alpha in (a_b, 0.05):
                    x = args(M, S, mult * sw_flash, sw_plugin, alpha)
                    proof.append({"M": M, "S": S, "tau_mult": mult, "alpha": alpha,
                                  "fast": power_t_two_sided_fast(*x), "adaptive": power_t_two_sided(*x)})
    worst = max(abs(p["fast"] - p["adaptive"]) for p in proof)
    if worst > 1e-9:
        raise SystemExit(f"the fast power rule differs from the adaptive integral by {worst:.2e} (rule 18)")
    rows, need = [], []
    for S in seeds_grid():
        for mult in TAU_MULTS:
            tau = mult * sw_flash
            for sw_label, sw in (("main_grid_plugin", sw_plugin), ("flash_limit", sw_flash)):
                for M in ROSTER_SIZES:
                    rows.append({"models": M, "seeds_per_cell": S, "tau_over_flash_limit": mult, "tau": tau,
                                 "within_sigma_d": sw_label, "sigma_d": sw,
                                 "power_alpha_bonf": power(M, S, tau, sw, a_b), "power_alpha_nominal": power(M, S, tau, sw, 0.05),
                                 "label": "DESIGN", "reference": "t with M - 1 df"})
                for alpha_label, alpha in (("bonf", a_b), ("nominal", 0.05)):
                    m_need = next((M for M in range(2, MAX_M_SEARCH + 1) if power(M, S, tau, sw, alpha) >= POWER_TARGET), None)
                    need.append({"seeds_per_cell": S, "tau_over_flash_limit": mult, "within_sigma_d": sw_label,
                                 "alpha": alpha_label, "models_for_power_0.8": m_need if m_need else f">{MAX_M_SEARCH}"})
    return rows, need, {"reproduced_e8_5_row": {"phase8": ref["power_bonf"], "here": mine},
                        "fast_vs_adaptive": {"n": len(proof), "worst_abs_diff": worst, "rows": proof}, "alpha_bonferroni": a_b,
                        "delta": delta, "sigma_plugin_main_grid": sw_plugin, "sigma_flash_limit": sw_flash}


def stage_model_power():
    rows, need, meta = model_power_rows()
    p = pd.DataFrame(rows)
    p.to_csv(os.path.join(OUT, "model_power.csv"), index=False)
    json.dump({"rows": rows, "models_needed": need, **meta,
               "note": ("DESIGN: one model cannot measure the between-model sd; tau is a stated range. The contrast is "
                        "one persona x scenario cell; alpha' = 0.05 / 36 is E8.5's cell structure (P8-16) and moves "
                        "with the pre-registered family count"),
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "model_power.json"), "w", encoding="utf-8"), indent=1, default=str)
    print("reproduced:", meta["reproduced_e8_5_row"])
    show = p[p.within_sigma_d == "main_grid_plugin"].pivot_table(index=["seeds_per_cell", "tau_over_flash_limit"],
                                                                 columns="models", values="power_alpha_bonf")
    print(show.round(3).to_string())
    print(pd.DataFrame(need).to_string(index=False))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="throughput,wallclock,model_power")
    a = ap.parse_args(argv)
    for s in [x.strip() for x in a.stages.split(",") if x.strip()]:
        {"throughput": stage_throughput, "wallclock": stage_wallclock, "model_power": stage_model_power}[s]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
