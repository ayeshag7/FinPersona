"""
Technical indicators vs an independent reference implementation (plan Section 3,
'unit tests vs TA-Lib'; the `ta` package is used as the reference since TA-Lib
is not installed): SMA20/50, Wilder RSI(14), MACD(12,26) + signal(9).
"""
import numpy as np
import pandas as pd
import pytest

from envs.v2.observables import technicals_block

ta = pytest.importorskip("ta")


def test_indicators_match_reference():
    rng = np.random.default_rng(0)
    P = 100 * np.exp(np.cumsum(rng.normal(0, 0.015, 400)))
    ours = technicals_block(P)
    s = pd.Series(P)
    sma20 = ta.trend.SMAIndicator(s, window=20).sma_indicator()
    sma50 = ta.trend.SMAIndicator(s, window=50).sma_indicator()
    rsi = ta.momentum.RSIIndicator(s, window=14).rsi()
    macd = ta.trend.MACD(s, window_slow=26, window_fast=12, window_sign=9)
    m = slice(60, None)  # after all warm-ups
    np.testing.assert_allclose(ours["SMA20"][m], sma20.to_numpy()[m], rtol=1e-9)
    np.testing.assert_allclose(ours["SMA50"][m], sma50.to_numpy()[m], rtol=1e-9)
    # RSI: both are Wilder (alpha = 1/14) smoothers; `ta` seeds the recursion with the SMA of the first 14 gains,
    # ours with an EWM (min_periods = 14); the seeds decay at (13/14)^t, so after 60 days they agree to < 0.5 point.
    np.testing.assert_allclose(ours["RSI14"][m], rsi.to_numpy()[m], atol=0.5)
    np.testing.assert_allclose(ours["MACD"][m], macd.macd().to_numpy()[m], atol=1e-9)
    np.testing.assert_allclose(ours["MACD_signal"][m], macd.macd_signal().to_numpy()[m], atol=1e-3)
    assert set(np.unique(ours["trend_regime"])) <= {-1, 0, 1}
