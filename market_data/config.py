"""
Configuration File for FinPersona

This file centralizes all static parameters for the backtest.
Changing a value here will propagate through the entire application.
"""

#  Backtest Core Settings
TICKER: str = "AAPL"
START_DATE: str = "2019-01-01"
END_DATE: str = "2021-12-31"

#  Technical Indicator Settings
INDICATOR_SETTINGS = {
    "sma": {"windows": [20, 60]},  # List of windows for Simple Moving Averages
    "rsi": {"window": 14},
    "macd": {"fast_window": 12, "slow_window": 26, "signal_window": 9},
}
