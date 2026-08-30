"""
L5 report: the best-achievable-from-observables oracle vs the true-V (mandate-conditional)
oracle, per persona x scenario, full-fields and price-only variants (plan Section 5 L5,
Section 8; methods review 23 Aug 2026: report MCR/band-MAS/turnover first, return/MDD
after, per-phase OOS R2 of x_hat, training pool disjoint from the scored seeds).

Usage: python -m tools.l5_report [--train 12] [--eval 10] [--T 200]
Writes docs/env_v2/generated/l5_observables_oracle.{md,csv}
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from envs.synthetic_market import SyntheticMarketEnv  # noqa: E402
from evaluation.observables_oracle import ObservablesOracle, observables_oracle_trajectory  # noqa: E402
from evaluation.baselines_v2 import run_baselines  # noqa: E402
from evaluation.metrics_v2 import score_run  # noqa: E402
from evaluation.targets import centre  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", type=int, default=12)
    ap.add_argument("--eval", type=int, default=10)
    ap.add_argument("--T", type=int, default=200)
    ap.add_argument("--feature-sets", default="full,price_only,level_free",
                    help="comma list of L5 variants: full | price_only (v2, contains the level) | level_free (v2.1 Phase 1)")
    ap.add_argument("--out", default=None, help="output stem (default docs/env_v2/generated/l5_observables_oracle)")
    ap.add_argument("--config", default=None, help="JSON GenConfig overrides (v2.1 Phase 1: the BEFORE run uses the frozen-equivalent settings)")
    a = ap.parse_args()
    import json as _json
    cfg = _json.loads(a.config) if a.config else None
    train_seeds = list(range(500, 500 + a.train))
    fsets = [f.strip() for f in a.feature_sets.split(",") if f.strip()]
    oracles = {fs: ObservablesOracle(train_seeds=train_seeds, T=a.T, feature_set=fs, config=cfg).fit() for fs in fsets}
    rows = []
    for persona in ("ISFJ", "INTJ", "ENTJ"):
        c0 = centre(persona)
        for sc in ("flat", "bull_trap", "crash", "sustained_bull"):
            for s in range(a.eval):
                env = SyntheticMarketEnv(sc, a.T, s, config=cfg)
                base = run_baselines(env, persona, c0, random_seeds=2)
                ref = {k: score_run(v, persona, c0) for k, v in base.items() if k in ("v_oracle", "mandate_conditional_oracle", "always_hold", "constant_mix")}
                for fs, orc in oracles.items():
                    m = score_run(observables_oracle_trajectory(env, persona, c0, orc), persona, c0)
                    rows.append({"persona": persona, "scenario": sc, "seed": s, "policy": f"L5_{fs}", **{k: m[k] for k in ("mcr_0.05", "band_mas", "turnover", "cost_paid", "return_pct", "mdd_pct", "coverage_0.05")}})
                for k, m in ref.items():
                    rows.append({"persona": persona, "scenario": sc, "seed": s, "policy": k, **{kk: m[kk] for kk in ("mcr_0.05", "band_mas", "turnover", "cost_paid", "return_pct", "mdd_pct", "coverage_0.05")}})
            print(persona, sc, "done", flush=True)
    df = pd.DataFrame(rows)
    out = a.out or os.path.join(ROOT, "docs", "env_v2", "generated", "l5_observables_oracle")
    df.to_csv(out + ".csv", index=False)
    agg = df.groupby(["persona", "scenario", "policy"])[["mcr_0.05", "band_mas", "turnover", "return_pct", "mdd_pct"]].mean().round(3)
    gap = []
    for (p, sc), g in df.groupby(["persona", "scenario"]):
        mco = g[g.policy == "mandate_conditional_oracle"]["mcr_0.05"].mean()
        for fs in fsets:
            l5 = g[g.policy == f"L5_{fs}"]["mcr_0.05"].mean()
            gap.append({"persona": p, "scenario": sc, "L5": fs, "MCR_L5": l5, "MCR_true_oracle": mco, "withheld_info_gap": l5 - mco})
    gap = pd.DataFrame(gap).round(3)
    with open(out + ".md", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# L5 observables oracle vs true-V oracle\n\n"
                 f"Training seeds {train_seeds[0]}..{train_seeds[-1]} (disjoint from evaluated seeds 0..{a.eval-1}); T = {a.T}; generator config overrides {cfg or '{}'}; "
                 "GBT on rendered fields + 5 lags -> x_hat; policy = mandate-conditional rule on x_hat. The gap is a LOWER "
                 "bound on what observables allow (this model class), i.e. an UPPER bound on the information withheld.\n\n"
                 "## Per-phase OOS R2 / sign accuracy of x_hat on the training pool\n\n")
        for fs, orc in oracles.items():
            fh.write(f"- {fs}: " + "; ".join(f"{g}: R2 {v['R2']:.2f}, sign {v['sign_acc']:.2f}" for g, v in orc.oos.items()) + "\n")
        fh.write("\n## Withheld-information gap (MCR at theta 0.05; lower MCR is better)\n\n" + gap.to_string(index=False) +
                 "\n\n## Policy means per persona x scenario\n\n" + agg.to_string() + "\n")
    print("written", out + ".md")


if __name__ == "__main__":
    main()
