"""
L5 on the Phase-5 state: tools/l5_report.py's design with an oracle that encodes "n/m" exactly as the audit does.

    python -m tools.phase5.e5_l5 --out STEM [--train 40 --eval 50] [--feature-sets full,price_only,level_free]

`evaluation/observables_oracle.py` is frozen; its `_panel` and `predict_x` keep only numeric observation values, so a
rendered "n/m" would drop the training row and zero the prediction on that day.  This subclass overrides those two
methods only: the NaN becomes the P/E cap plus a `reported_PE_nm` indicator, the estimator, lags and policy are the
parent's, unchanged.  Everything else (baselines, scoring, the persona x scenario x seed design) is l5_report.py's.

Output: <stem>.csv / .md (the discrimination summariser reads the csv)
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

from envs.synthetic_market import SyntheticMarketEnv, CANONICAL_FIELDS  # noqa: E402
from evaluation.observables_oracle import ObservablesOracle, observables_oracle_trajectory  # noqa: E402
from evaluation.leakage_audit import panel_from_env, add_lags_and_returns, add_level_free_columns  # noqa: E402
from evaluation.baselines_v2 import run_baselines  # noqa: E402
from evaluation.metrics_v2 import score_run  # noqa: E402
from evaluation.targets import centre  # noqa: E402
from tools.phase5.common import encode_nm, pin_state  # noqa: E402


class OracleNM(ObservablesOracle):
    """The frozen oracle with the audit's n/m encoding."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        if self.feature_set == "full":
            self.keys = [x for x in CANONICAL_FIELDS if x != "date"] + ["reported_PE_nm"]

    def _panel(self, seeds):
        return encode_nm(super()._panel(seeds))

    def predict_x(self, env):
        assert env.seed not in self.train_seeds, "held-out seed required"
        d = env.data[env.data["asset"] == 0].copy()
        rows = []
        env.reset()
        for t in range(env.n_days):
            o = env.get_observation()
            row = {k: float(v) for k, v in o.items() if k != "date" and not isinstance(v, (list, str))}
            if o.get("reported_PE") == "n/m":
                row["reported_PE"] = np.nan
            rows.append(row); env.step()
        env.reset()
        f = pd.DataFrame(rows); f["scenario"] = env.scenario; f["seed"] = env.seed; f["day"] = np.arange(1, len(f) + 1)
        f["P"] = d["price"].values; f["V"] = d["fundamental_value"].values; f["x"] = d["x"].values
        f = encode_nm(f)
        if "reported_PE_nm" not in f and "reported_PE_nm" in self.keys:
            f["reported_PE_nm"] = 0.0
        if self.feature_set == "level_free":
            f = add_level_free_columns(f)
        fl, cols = add_lags_and_returns(f, [k for k in self.keys if k in f.columns])
        X = fl[self.cols].to_numpy(dtype=float)
        ok = ~np.isnan(X).any(axis=1)
        xh = np.zeros(len(fl)); xh[ok] = self.model.predict(X[ok])
        return xh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", type=int, default=40)
    ap.add_argument("--eval", type=int, default=50)
    ap.add_argument("--T", type=int, default=200)
    ap.add_argument("--feature-sets", default="full,price_only,level_free")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    state = pin_state()
    train_seeds = list(range(500, 500 + a.train))
    fsets = [f.strip() for f in a.feature_sets.split(",") if f.strip()]
    oracles = {fs: OracleNM(train_seeds=train_seeds, T=a.T, feature_set=fs).fit() for fs in fsets}
    rows = []
    for persona in ("ISFJ", "INTJ", "ENTJ"):
        c0 = centre(persona)
        for sc in ("flat", "bull_trap", "crash", "sustained_bull"):
            for s in range(a.eval):
                env = SyntheticMarketEnv(sc, a.T, s)
                base = run_baselines(env, persona, c0, random_seeds=2)
                ref = {k: score_run(v, persona, c0) for k, v in base.items() if k in ("v_oracle", "mandate_conditional_oracle", "always_hold", "constant_mix")}
                for fs, orc in oracles.items():
                    m = score_run(observables_oracle_trajectory(env, persona, c0, orc), persona, c0)
                    rows.append({"persona": persona, "scenario": sc, "seed": s, "policy": f"L5_{fs}",
                                 **{k: m[k] for k in ("mcr_0.05", "band_mas", "turnover", "cost_paid", "return_pct", "mdd_pct", "coverage_0.05")}})
                for k, m in ref.items():
                    rows.append({"persona": persona, "scenario": sc, "seed": s, "policy": k,
                                 **{kk: m[kk] for kk in ("mcr_0.05", "band_mas", "turnover", "cost_paid", "return_pct", "mdd_pct", "coverage_0.05")}})
            print(persona, sc, "done", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(a.out + ".csv", index=False)
    with open(a.out + ".md", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# L5 observables oracle vs true-V oracle (Phase-5 state; oracle encodes 'n/m' as the audit does)\n\n"
                 f"Training seeds {train_seeds[0]}..{train_seeds[-1]}; T = {a.T}; state {state}.\n\n"
                 "## Per-phase OOS R2 / sign accuracy of x_hat on the training pool\n\n")
        for fs, orc in oracles.items():
            fh.write(f"- {fs}: " + "; ".join(f"{g}: R2 {v['R2']:.2f}, sign {v['sign_acc']:.2f}" for g, v in orc.oos.items()) + "\n")
    print("written", a.out + ".csv")


if __name__ == "__main__":
    main()
