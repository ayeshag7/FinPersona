"""
L5: the best-achievable-from-observables oracle (plan Section 5 L5, Section 8 item 1;
review D18).

A surrogate policy fit on RENDERED fields only, scored like an agent: the gap
between it and the true-V (mandate-conditional) oracle is the information the
environment deliberately withholds.

Design (DECISION_LOG, "remaining environment items"): a gradient-boosted
regressor predicts x_hat = log(P/V) from the rendered observation (+5 lags) on
TRAINING seeds; on a held-out seed the policy applies the mandate-conditional
rule to x_hat (cash -> band-low if x_hat < -theta, band-high if x_hat > +theta,
unchanged otherwise).  Predicting x and then applying the same rule as the
V-oracle keeps the two oracles comparable (same decision rule, different
information); a direct policy classifier would conflate information with
decision-rule differences.  Seeds used for fitting are disjoint from the seeds
being scored (the fit is refreshed per held-out seed block).
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from envs.synthetic_market import SyntheticMarketEnv, CANONICAL_FIELDS
from evaluation.leakage_audit import panel_from_env, add_lags_and_returns, add_level_free_columns
from evaluation.targets import band

FEATURE_KEYS = [k for k in CANONICAL_FIELDS if k != "date"]
PRICE_ONLY_KEYS = ["price", "SMA20", "SMA50", "trend_strength", "trend_regime", "RSI14", "MACD", "MACD_signal"]   # v2 (contains the level)
# v2.1 Phase 1 (E1.6): the level-free price-only oracle -- returns (added as lags/returns), log P/SMA, RSI, MACD/P, trend
LEVEL_FREE_KEYS = ["lp_sma20", "lp_sma50", "trend_strength", "trend_regime", "RSI14", "macd_p", "macds_p"]


class ObservablesOracle:
    def __init__(self, theta: float = 0.05, train_seeds: Optional[List[int]] = None, T: int = 200,
                 scenarios=("flat", "bull_trap", "crash", "sustained_bull"), deltas=(0.55, 0.70, 0.85),
                 feature_set: str = "full", config: Optional[Dict] = None):
        """feature_set 'full' (all rendered fields), 'price_only' (the v2 price + technicals set, which contains the
        price level) or 'level_free' (v2.1 Phase 1: returns, log P/SMA, RSI, MACD/P, trend -- no level): the gap between
        the L5 policies decomposes the withheld information into price-dynamics vs non-price fields."""
        self.theta = theta
        self.feature_set = feature_set
        self.keys = {"full": FEATURE_KEYS, "price_only": PRICE_ONLY_KEYS, "level_free": LEVEL_FREE_KEYS}[feature_set]
        self.oos = {}                     # per-phase OOS R2 / sign accuracy of x_hat on the training pool
        self.train_seeds = list(train_seeds) if train_seeds is not None else list(range(500, 512))
        self.T, self.scenarios, self.deltas = T, scenarios, deltas
        self.config = dict(config) if config else None      # GenConfig overrides (v2.1 Phase 1: the before/after L5 runs)
        self.model = None
        self.cols: List[str] = []

    def _panel(self, seeds) -> pd.DataFrame:
        frames = []
        for s in seeds:
            for sc in self.scenarios:
                if sc == "crash":
                    for d in self.deltas:
                        f = panel_from_env(SyntheticMarketEnv("crash", self.T, s, crash_discount=d, config=self.config), "crash", s)
                        f["seed"] = s * 100 + int(round(d * 100)); frames.append(f)
                else:
                    frames.append(panel_from_env(SyntheticMarketEnv(sc, self.T, s, config=self.config), sc, s))
        return pd.concat(frames, ignore_index=True)

    def fit(self):
        from sklearn.ensemble import HistGradientBoostingRegressor
        from sklearn.model_selection import GroupKFold
        panel = self._panel(self.train_seeds)
        if self.feature_set == "level_free":
            panel = add_level_free_columns(panel)
        dfl, cols = add_lags_and_returns(panel, [k for k in self.keys if k in panel.columns])
        dfl = dfl.dropna(subset=cols).reset_index(drop=True)
        self.cols = cols
        X = dfl[cols].to_numpy(dtype=float); y = dfl["x"].to_numpy(dtype=float)
        groups = (dfl["scenario"].astype(str) + "-" + dfl["seed"].astype(str)).to_numpy(dtype=object)
        # per-phase OOS diagnostics on the training pool (blocked by seed)
        pred = np.full(len(y), np.nan)
        for tr, te in GroupKFold(n_splits=min(5, len(np.unique(groups)))).split(X, y, groups):
            m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, max_depth=6, random_state=0).fit(X[tr], y[tr])
            pred[te] = m.predict(X[te])
        pg = dfl["macro"].replace({"down-event": "event", "up-event": "event"}).to_numpy(dtype=object)
        for g in ("calm", "event", "resolution"):
            mk = pg == g
            if mk.sum() > 30:
                ss = ((y[mk] - y[mk].mean()) ** 2).sum()
                res = mk & (np.abs(y) >= self.theta)
                self.oos[g] = {"R2": float(1 - ((y[mk] - pred[mk]) ** 2).sum() / ss) if ss > 0 else np.nan,
                               "sign_acc": float(np.mean(np.sign(pred[res]) == np.sign(y[res]))) if res.any() else np.nan}
        self.model = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, max_depth=6, random_state=0)
        self.model.fit(X, y)
        return self

    def predict_x(self, env: SyntheticMarketEnv) -> np.ndarray:
        """x_hat for every benchmark day of `env` (env must not be a training seed)."""
        assert env.seed not in self.train_seeds, "held-out seed required"
        d = env.data[env.data["asset"] == 0].copy()
        # rebuild the rendered-field frame from the observation dict (rounded as rendered)
        rows = []
        env.reset()
        for t in range(env.n_days):
            o = env.get_observation(); rows.append({k: float(v) for k, v in o.items() if k != "date" and not isinstance(v, (list, str))})
            env.step()
        env.reset()
        f = pd.DataFrame(rows); f["scenario"] = env.scenario; f["seed"] = env.seed; f["day"] = np.arange(1, len(f) + 1)
        f["P"] = d["price"].values; f["V"] = d["fundamental_value"].values; f["x"] = d["x"].values
        if self.feature_set == "level_free":
            f = add_level_free_columns(f)
        fl, cols = add_lags_and_returns(f, [k for k in self.keys if k in f.columns])
        X = fl[self.cols].to_numpy(dtype=float)
        # early rows have NaN lags: fall back to 0 prediction there (no information)
        ok = ~np.isnan(X).any(axis=1)
        xh = np.zeros(len(fl)); xh[ok] = self.model.predict(X[ok])
        return xh

    def policy(self, persona: Optional[str], x_hat: np.ndarray, start_cash_share: float) -> np.ndarray:
        lo, hi = band(persona) if persona and persona not in ("NONE", "TRADER") else (0.0, 1.0)
        out = np.empty(len(x_hat)); cur = min(max(start_cash_share, lo), hi)
        for i, xh in enumerate(x_hat):
            if xh < -self.theta:
                cur = lo
            elif xh > self.theta:
                cur = hi
            out[i] = cur
        return out


def observables_oracle_trajectory(env: SyntheticMarketEnv, persona: Optional[str], start_cash_share: float,
                                  oracle: ObservablesOracle, cost_bp: float = 5.0) -> pd.DataFrame:
    """Run the L5 policy through PortfolioV2 on `env` and return a run-CSV-style frame."""
    from evaluation.baselines_v2 import _run_policy
    targets = oracle.policy(persona, oracle.predict_x(env), start_cash_share)
    return _run_policy(env, start_cash_share, lambda t, r, st, s: float(targets[t]), cost_bp=cost_bp, interface="target")
