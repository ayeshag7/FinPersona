"""
FinPersona-Bench synthetic market environment, **v2** (plan Aug 2026).

Price is decomposed as log P_t = log V_t + x_t with an exogenous fundamental V
(GBM with t(5) shocks), a Franke-Westerhoff-shaped mispricing x (single-stock
re-estimated / documented fallback; index parameters as sensitivity) driven by
ONE GJR-GARCH(1,1)-t innovation, scripted event drifts with randomised onsets,
a hazard-based bubble top, rejection sampling with published criteria, separate
named RNG streams, a 260-day burn-in, N-asset capability, and observables that
depend on the path (never on the phase label).  The v1 generator is frozen at
envs/v1/synthetic_market_v1.py (tag v1-env-freeze).

Public interface (same as v1, plus extras):
    env = SyntheticMarketEnv(scenario, n_days, seed, crash_discount, ...)
    env.reset(); env.get_observation(); env.get_ground_truth(); env.get_scenario_phase()
    env.get_metadata(); env.step(); env.data (DataFrame, benchmark days only)
    env.ENV_VERSION == "v2"; env.schedule; env.event_meta; env.attempts; env.rejections
Module-level exports for the audits and Table 2:
    audit_panel(seeds, T), checklist_paths(seeds, T), TABLE2_DEFINITIONS,
    TABLE2_PORTFOLIO_DEFS, TABLE2_OBS_ROUNDING
"""
from __future__ import annotations

import math
from dataclasses import asdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from envs.v2.generator import GenConfig, PathResult, generate, BURN_IN
from envs.v2.mispricing import ENGINE_DEFAULT
from envs.v2.rng import Streams
from envs.v2 import observables as obs
from envs.v2.schedule import SCENARIOS, ORDERINGS

ENV_VERSION = "v2"
MACRO_OF = {"calm": "calm", "sustained-bull": "calm", "deterioration": "down-event", "panic": "down-event",
            "mania": "up-event", "blow-off": "up-event", "stabilisation": "resolution", "post-top": "resolution"}
THETAS = (0.03, 0.05, 0.08)

# canonical rendered field order (decision 11; a randomised-order arm permutes this per seed)
CANONICAL_FIELDS = ["date", "price", "SMA20", "SMA50", "trend_strength", "trend_regime", "RSI14", "MACD",
                    "MACD_signal", "volume", "volume_ratio", "news_sentiment", "sentiment_MA5", "sentiment_change",
                    "implied_volatility", "reported_PE", "dividend_yield", "analyst_fair_value",
                    "days_since_eps_announcement"]

TABLE2_OBS_ROUNDING = {
    "date": "string 'Day-N' (+ 'of T' when disclosed)", "days_remaining": "int (only when disclosed)",
    "price": "2 dp", "SMA20": "2 dp", "SMA50": "2 dp", "trend_strength": "2 dp", "trend_regime": "int",
    "RSI14": "1 dp", "MACD": "4 dp", "MACD_signal": "4 dp", "volume": "int", "volume_ratio": "2 dp",
    "news_sentiment": "2 dp", "sentiment_MA5": "2 dp", "sentiment_change": "2 dp", "implied_volatility": "1 dp",
    "reported_PE": "1 dp", "dividend_yield": "2 dp", "analyst_fair_value": "2 dp",
    "days_since_eps_announcement": "int",
}

# (category, definition, code ref) for EVERY column of env.data
TABLE2_DEFINITIONS = {
    "asset": ("Index", "Asset index (0 = the scenario asset; N > 1 only in the multi-asset extension).", "synthetic_market.py"),
    "day": ("Index", "Trading-day index 1..T; rendered as 'Day-N' under key 'date' (T appended only in the disclosed-horizon arm).", "synthetic_market.py get_observation"),
    "price": ("Price action", "P_t = V_t exp(x_t); P_1 = 100 under the provisional start-price mechanism B (v2.1 Phase 1, D13; under C every price-denominated rendered field is multiplied by a per-seed k_render). x_t follows the FW recursion (calm) plus scripted event drifts; one GJR-GARCH-t innovation.", "v2/generator.py, v2/mispricing.py, v2/events.py"),
    "fundamental_value": ("Hidden", "V_t: GBM, mu_V and sigma_V from envs/v2/params/value.json (v2.1 Phase 1: FIT; sustained bull U(0.0015,0.0025); crash deterioration log-linear drift delivering D_V ~ U(10,30)%, then flat), standardised t(df_V) shocks (N > 1: sqrt(rho) f + sqrt(1-rho) z_i -- not itself t); announcement jumps in log V under jump_placement 'V_announce'/'both'. Start price: mode B (P_1 = 100, V_1 = 100 e^-x_1) in Phases 1-6 (D13). Never rendered.", "v2/generator.py"),
    "x": ("Hidden", "log(P/V): referee's mispricing; resolvable iff |x| >= theta.", "v2/generator.py"),
    "phase": ("Hidden", "Phase label (calm, deterioration, panic, stabilisation, mania, blow-off, post-top, sustained-bull). Never rendered.", "v2/events.py, v2/schedule.py"),
    "macro_phase": ("Hidden", "Macro class {calm, down-event, up-event, resolution} for the L2b audit. Never rendered.", "synthetic_market.py"),
    "garch_sigma": ("Hidden", "Conditional sd of the x-innovation (GJR-GARCH state). Never rendered.", "v2/garch.py"),
    "n_f": ("Hidden", "Fundamentalist population share of the FW recursion. Never rendered.", "v2/mispricing.py"),
    "resolvable_0.03": ("Hidden", "|x| >= 0.03", "synthetic_market.py"),
    "resolvable_0.05": ("Hidden", "|x| >= 0.05 (pre-registered theta)", "synthetic_market.py"),
    "resolvable_0.08": ("Hidden", "|x| >= 0.08", "synthetic_market.py"),
    "SMA20": ("Trend", "20-day simple moving average of price (warm from the 260-day burn-in).", "v2/observables.py technicals_block"),
    "SMA50": ("Trend", "50-day simple moving average of price.", "v2/observables.py technicals_block"),
    "trend_strength": ("Trend", "(SMA20 - SMA50) / SMA50 x 100.", "v2/observables.py technicals_block"),
    "trend_regime": ("Trend", "1 if trend_strength > 2, -1 if < -2, else 0.", "v2/observables.py technicals_block"),
    "RSI14": ("Momentum", "Wilder RSI(14) (EMA smoothing, alpha = 1/14).", "v2/observables.py technicals_block"),
    "MACD": ("Momentum", "EMA12 - EMA26 of price.", "v2/observables.py technicals_block"),
    "MACD_signal": ("Momentum", "EMA9 of MACD.", "v2/observables.py technicals_block"),
    "volume": ("Liquidity", "log Vol_t = mu_v + 0.65 (log Vol_{t-1} - mu_v) + 0.25 (|r_t|/sigma - 1) + 1.2 |x_{t-j}| + 0.30 eps (j = |jitter| d); no label-driven shifts.", "v2/observables.py volume_block"),
    "volume_SMA20": ("Liquidity (internal)", "20-day mean of volume.", "v2/observables.py volume_block"),
    "volume_ratio": ("Liquidity", "volume / volume_SMA20.", "v2/observables.py volume_block"),
    "news_sentiment": ("Sentiment", "s_t = tanh(m_t + 0.85 (raw_{t-1} - m_{t-1}) + 0.25 r_t/sigma_r + 0.25 eps), m_t = 0.6 tanh(2 x_{t-j}) + 0.3 tanh(ret20/0.15); predictive component b_pred (+8 bp next-day per +1 sd, 6 bp reversed days 2-5; 0 in the control arm) applied inside the generator.", "v2/observables.py SentimentState, v2/generator.py"),
    "sentiment_MA5": ("Sentiment", "5-day rolling mean of news_sentiment.", "synthetic_market.py"),
    "sentiment_change": ("Sentiment", "news_sentiment - sentiment_MA5.", "synthetic_market.py"),
    "implied_volatility": ("Risk", "sqrt(252 (sigma_V^2 + w_t^2 fvar21_t)) x (1 + premium) x 100; fvar21 = mean 21-day GARCH variance forecast; premium 0.20, 0.35 when the GARCH variance is in its top decile (state-based); floor 12%.", "v2/observables.py iv_block"),
    "hidden_multiple": ("Hidden", "Valuation multiple k ~ U(14, 22) per seed (never rendered).", "v2/observables.py earnings_block"),
    "trailing_eps": ("Valuation (internal)", "Sum of the last four ANNOUNCED quarterly EPS; EPS_q = V(quarter end)/k x exp(N(0, 0.10)), announced quarter end + U(25, 35) d.", "v2/observables.py earnings_block"),
    "last_quarter_eps": ("Valuation (internal)", "Most recently announced quarterly EPS.", "v2/observables.py earnings_block"),
    "reported_PE": ("Valuation", "P_t / trailing_eps, capped at 200.", "v2/observables.py earnings_block"),
    "dps_quarterly": ("Valuation (internal)", "Sticky quarterly dividend: DPS_q = 0.7 DPS_{q-1} + 0.3 x 0.35 x EPS_q.", "v2/observables.py earnings_block"),
    "dividend_yield": ("Valuation", "4 x DPS_quarterly / P_t x 100.", "v2/observables.py earnings_block"),
    "days_since_eps_announcement": ("Valuation", "Days since the last earnings announcement.", "v2/observables.py earnings_block"),
    "analyst_fair_value": ("Valuation", "F_t = V_t exp(u_t), u AR(1) rho 0.95 per weekly update, stationary sd 0.15 (fixed ex ante; the sqrt(5) scaling that made it 0.335 was removed in v2.1 Phase 0).", "v2/observables.py analyst_block"),
    "analyst_error_u": ("Hidden", "Analyst log error u_t (never rendered).", "v2/observables.py analyst_block"),
    "fvar21": ("Hidden", "21-day mean GARCH variance forecast (never rendered; enters IV).", "v2/garch.py forecast_var"),
    "fw_weight": ("Hidden", "FW innovation weight w_t (never rendered).", "v2/mispricing.py"),
}
TABLE2_PORTFOLIO_DEFS = {
    "cash": "Cash balance after the previous day's trade (initial = start_cash_share x 10,000; start design is a factor).",
    "holdings_value": "Mark-to-market value of shares held.",
    "cash_share": "cash / (cash + holdings_value).",
}


class SyntheticMarketEnv:
    ENV_VERSION = ENV_VERSION

    def __init__(self, scenario: str = "flat", n_days: int = 200, seed: int = 42, start_price: float = 100.0,
                 crash_discount: float = 0.70, ordering: str = "setup_first", n_assets: int = 1,
                 engine: str = ENGINE_DEFAULT, b_pred: Optional[float] = None, disclose_horizon: bool = False,
                 field_order: str = "canonical", config: Optional[Dict] = None,
                 volatility: float = None, drift: float = None):
        # `volatility` / `drift` are accepted for v1 call-compatibility and ignored (v2 uses plan parameters)
        if scenario not in SCENARIOS:
            raise ValueError(f"scenario must be one of {SCENARIOS}")
        if ordering not in ORDERINGS:
            raise ValueError(f"ordering must be one of {ORDERINGS}")
        self.scenario, self.n_days, self.seed = scenario, int(n_days), int(seed)
        self.start_price, self.crash_discount = float(start_price), float(crash_discount)
        self.ordering, self.n_assets, self.engine = ordering, int(n_assets), engine
        self.disclose_horizon, self.field_order = bool(disclose_horizon), field_order
        kw = dict(scenario=scenario, T=self.n_days, seed=self.seed, ordering=ordering, delta=self.crash_discount,
                  n_assets=self.n_assets, start_price=self.start_price, engine=engine)
        if b_pred is not None:
            kw["b_pred"] = float(b_pred)
        if config:
            kw.update(config)
        self.cfg = GenConfig(**kw)
        self.current_step = 0
        self.result: PathResult = generate(self.cfg)
        self.schedule = self.result.schedule
        self.event_meta = self.result.event_meta
        self.attempts = self.result.attempts
        self.rejections = self.result.rejections
        self._full, self.data = self._build_frames()
        self._perm = self._field_permutation()

    # ------------------------------------------------------------------ frames
    def _build_frames(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        r = self.result
        st = Streams(self.cfg.seed, r.attempts - 1)
        day = r.day
        frames = []
        for a in range(max(1, self.cfg.n_assets)):
            V = r.V[a]; P = r.P[a]; x = r.x[a]
            ret = np.concatenate([[0.0], np.diff(np.log(P))])
            d = {"day": day, "asset": a, "price": P, "fundamental_value": V, "x": x,
                 "phase": r.phase, "garch_sigma": r.sigma[a], "n_f": r.n_f[a], "fvar21": r.fvar21[a],
                 "fw_weight": r.w[a], "news_sentiment": r.sent[a]}
            d.update(obs.technicals_block(P))
            d.update(obs.volume_block(day, ret, x, st.get("volume", a), lag=self.schedule.jitter.get("volume", 0)))
            d.update(obs.earnings_block(day, V, P, st.get("multiple", a), st.get("eps", a), st.get("dividend", a),
                                        ann=r.ann[a] if r.ann else None, ann_jumps=r.ann_jumps[a] if r.ann_jumps else None))
            d.update(obs.analyst_block(day, V, st.get("analyst", a)))
            d.update(obs.iv_block(r.fvar21[a], r.w[a], r.sigma[a] ** 2, self.cfg.sigma_V))
            df = pd.DataFrame(d)
            df["macro_phase"] = df["phase"].map(MACRO_OF).fillna("calm")
            df["sentiment_MA5"] = df["news_sentiment"].rolling(5, min_periods=1).mean()
            df["sentiment_change"] = df["news_sentiment"] - df["sentiment_MA5"]
            for th in THETAS:
                df[f"resolvable_{th}"] = np.abs(df["x"]) >= th
            frames.append(df)
        full = pd.concat(frames, ignore_index=True)
        bench = full[full["day"] >= 1].reset_index(drop=True)
        return full, bench

    def _field_permutation(self) -> List[str]:
        fields = list(CANONICAL_FIELDS)
        if self.field_order == "randomised":
            rng = Streams(self.cfg.seed, 0).get("field_order")
            fields = [fields[i] for i in rng.permutation(len(fields))]
        return fields

    # ------------------------------------------------------------------ API
    def reset(self):
        self.current_step = 0
        return self.get_observation()

    def _row(self, asset: int = 0):
        return self.data[self.data["asset"] == asset].iloc[self.current_step]

    # price-denominated rendered fields: scaled by k_render under start_price_mode 'both' (mechanism C); ratios,
    # shares, RSI and trend fields are invariant and are not scaled (tests/test_v2_1_phase_1.py::test_render_scale_invariance)
    PRICE_DENOMINATED = ("price", "SMA20", "SMA50", "MACD", "MACD_signal", "analyst_fair_value")

    def _render_asset(self, row) -> Dict:
        d = int(row["day"])
        k = float(self.result.k_render)
        vals = {
            "date": f"Day-{d} of {self.n_days}" if self.disclose_horizon else f"Day-{d}",
            "price": round(float(row["price"]) * k, 2), "SMA20": round(float(row["SMA20"]) * k, 2),
            "SMA50": round(float(row["SMA50"]) * k, 2), "trend_strength": round(float(row["trend_strength"]), 2),
            "trend_regime": int(row["trend_regime"]), "RSI14": round(float(row["RSI14"]), 1),
            "MACD": round(float(row["MACD"]) * k, 4), "MACD_signal": round(float(row["MACD_signal"]) * k, 4),
            "volume": int(row["volume"]), "volume_ratio": round(float(row["volume_ratio"]), 2),
            "news_sentiment": round(float(row["news_sentiment"]), 2),
            "sentiment_MA5": round(float(row["sentiment_MA5"]), 2),
            "sentiment_change": round(float(row["sentiment_change"]), 2),
            "implied_volatility": round(float(row["implied_volatility"]), 1),
            "reported_PE": round(float(row["reported_PE"]), 1),
            "dividend_yield": round(float(row["dividend_yield"]), 2),
            "analyst_fair_value": round(float(row["analyst_fair_value"]) * k, 2),
            "days_since_eps_announcement": int(row["days_since_eps_announcement"]),
        }
        out = {k: vals[k] for k in self._perm}
        if self.disclose_horizon:
            out["days_remaining"] = self.n_days - d
        return out

    def get_observation(self) -> Optional[Dict]:
        if self.current_step >= self.n_days:
            return None
        o = self._render_asset(self._row(0))
        if self.n_assets > 1:
            o["assets"] = [self._render_asset(self._row(a)) for a in range(self.n_assets)]
        return o

    def get_ground_truth(self) -> Dict:
        if self.current_step >= self.n_days:
            return {}
        row = self._row(0).to_dict()
        row["truth_step"] = self.current_step
        row["macro_phase"] = MACRO_OF.get(row["phase"], "calm")
        if self.n_assets > 1:
            row["assets"] = [self._row(a).to_dict() for a in range(self.n_assets)]
        return row

    def get_scenario_phase(self) -> str:
        if self.current_step >= self.n_days:
            return "done"
        return str(self._row(0)["phase"])

    def get_metadata(self) -> Dict:
        sched = self.schedule.to_dict()
        return {
            "env_version": ENV_VERSION, "scenario": self.scenario, "n_days": self.n_days, "seed": self.seed,
            "start_price": self.start_price, "crash_discount": self.crash_discount, "ordering": self.ordering,
            "n_assets": self.n_assets, "engine": self.engine, "engine_used": self.result.params.name,
            "disclose_horizon": self.disclose_horizon,
            "field_order": self.field_order, "burn_in": self.cfg.burn_in, "burn_in_mode": self.cfg.burn_in_mode,
            "start_price_mode": self.cfg.start_price_mode, "k_render": float(self.result.k_render),
            "jump_placement": self.cfg.jump_placement, "value_params_file": "envs/v2/params/value.json",
            "gen_config": self.cfg.to_dict(), "fw_params": self.result.params.to_dict(),
            "garch_params": asdict(self.result.garch_params), "schedule": sched,
            "attempts": self.attempts, "rejections": list(self.rejections),
            "event_meta": {k: v for k, v in self.event_meta.items() if k != "assets"},
            "sma_short": 20, "sma_long": 50,
        }

    def step(self) -> Tuple[Optional[Dict], bool]:
        self.current_step += 1
        done = self.current_step >= self.n_days
        return self.get_observation(), done


# ---------------------------------------------------------------------------
# helpers for the audits (evaluation/leakage_audit.py, evaluation/stylized_facts.py)
# ---------------------------------------------------------------------------
def _path_data(env: SyntheticMarketEnv):
    from evaluation.stylized_facts import PathData
    d = env.data[env.data["asset"] == 0]
    df = pd.DataFrame({"day": d["day"].values, "price": d["price"].values, "value": d["fundamental_value"].values,
                       "volume": d["volume"].values, "sentiment": d["news_sentiment"].values,
                       "iv": d["implied_volatility"].values, "phase": d["phase"].values, "x": d["x"].values,
                       "sigma": d["garch_sigma"].values})
    v = df["value"].values
    meta = {"delta": env.crash_discount, "D_V": env.schedule.D_V if env.scenario == "crash" else 1 - v.min() / v[0],
            "topped": env.event_meta.get("topped"), "rejected": False, "n_rejections": env.attempts - 1,
            "b_pred": env.cfg.b_pred, "ordering": env.ordering}
    return PathData(env.scenario, env.seed, df, meta)


def checklist_paths(n_seeds: int = 50, T: int = 200, deltas=(0.55, 0.70, 0.85), config: Optional[Dict] = None,
                    engine: Optional[str] = None, seed0: int = 0) -> Dict[str, list]:
    """Paths for the Section 9 checklist: flat, bull_trap, crash (per delta),
    sustained_bull, a mirrored/phase-free mix for item 15, and flat T=800.
    `config` / `engine` override the generator (sensitivity runs). `seed0` offsets every seed (v2.1 Phase 1: the
    standard checklist panel SCL uses seed0 = 40000; the published v2 file used 0)."""
    kw = {"config": config}
    if engine:
        kw["engine"] = engine
    out = {"flat": [], "bull_trap": [], "crash": [], "sustained_bull": [], "mixed": [], "flat_T800": []}
    for s in range(seed0, seed0 + n_seeds):
        out["flat"].append(_path_data(SyntheticMarketEnv("flat", T, s, **kw)))
        out["bull_trap"].append(_path_data(SyntheticMarketEnv("bull_trap", T, s, **kw)))
        out["sustained_bull"].append(_path_data(SyntheticMarketEnv("sustained_bull", T, s, **kw)))
        for d in deltas:
            out["crash"].append(_path_data(SyntheticMarketEnv("crash", T, s, crash_discount=d, **kw)))
    # mixed set for phase/time separability: setup-first, event-first, phase-free
    for s in range(seed0, seed0 + n_seeds):
        sc = ("crash", "bull_trap")[s % 2]
        out["mixed"].append(_path_data(SyntheticMarketEnv(sc, T, 1000 + s, ordering="event_first", **kw)))
        out["mixed"].append(_path_data(SyntheticMarketEnv(sc, T, 2000 + s, ordering="setup_first", **kw)))
        out["mixed"].append(_path_data(SyntheticMarketEnv("flat", T, 3000 + s, **kw)))
    for s in range(seed0, seed0 + min(n_seeds, 20)):
        out["flat_T800"].append(_path_data(SyntheticMarketEnv("flat", 800, s, **kw)))
    return out


def audit_panel_multi(seeds: int = 10, T: int = 200, n_assets: int = 3, target_asset: int = 0,
                      asset_vol_scale=(1.0, 1.0, 0.5)) -> pd.DataFrame:
    """Rendered-field panel for the multi-asset audit: features = the FULL N-asset rendered vector
    (suffix _aK), target = x of `target_asset`; the own-block columns (suffix _a{target}) are the
    control (methods review: cross-asset leakage through the common factor must be measured)."""
    frames = []
    for s in range(seeds):
        for sc in ("flat", "bull_trap", "crash", "sustained_bull"):
            env = SyntheticMarketEnv(sc, T, s, n_assets=n_assets,
                                     config={"asset_vol_scale": list(asset_vol_scale), "rho_common": 0.3})
            rows = []
            env.reset()
            for t in range(T):
                o = env.get_observation(); gt = env.get_ground_truth()
                row = {"scenario": sc, "seed": s, "day": t + 1, "phase": gt["phase"],
                       "V": float(gt["assets"][target_asset]["fundamental_value"]),
                       "P": float(gt["assets"][target_asset]["price"])}
                for k_, a in enumerate(o["assets"]):
                    for k, v in a.items():
                        if k != "date" and isinstance(v, (int, float)):
                            row[f"{k}_a{k_}"] = float(v)
                # keep the target asset's own fields also under the plain names (price-only control keys)
                for k, v in o["assets"][target_asset].items():
                    if k != "date" and isinstance(v, (int, float)):
                        row[k] = float(v)
                rows.append(row); env.step()
            df = pd.DataFrame(rows); df["macro"] = df["phase"].map(MACRO_OF).fillna("calm"); df["x"] = np.log(df["P"] / df["V"])
            frames.append(df)
    return pd.concat(frames, ignore_index=True)


def audit_panel(seeds: int = 30, T: int = 200, deltas=(0.55, 0.70, 0.85), seed0: int = 0) -> pd.DataFrame:
    """Rendered-field panel for the Section 5 audits: setup-first, event-first and
    phase-free runs mixed, as the plan requires. `seed0` offsets every seed (v2.1 Phase 1: the standard evaluation
    panel SEP uses seed0 = 30000, event-first paths at 1000 + seed; the published v2 audit used 0)."""
    from evaluation.leakage_audit import panel_from_env
    frames = []
    for s in range(seed0, seed0 + seeds):
        frames.append(panel_from_env(SyntheticMarketEnv("flat", T, s), "flat", s))
        frames.append(panel_from_env(SyntheticMarketEnv("bull_trap", T, s), "bull_trap", s))
        frames.append(panel_from_env(SyntheticMarketEnv("bull_trap", T, 1000 + s, ordering="event_first"), "bull_trap", 1000 + s))
        frames.append(panel_from_env(SyntheticMarketEnv("sustained_bull", T, s), "sustained_bull", s))
        for d in deltas:
            f = panel_from_env(SyntheticMarketEnv("crash", T, s, crash_discount=d), "crash", s)
            f["seed"] = s * 100 + int(round(d * 100))
            frames.append(f)
        f = panel_from_env(SyntheticMarketEnv("crash", T, 1000 + s, ordering="event_first"), "crash", 1000 + s)
        frames.append(f)
    return pd.concat(frames, ignore_index=True)
