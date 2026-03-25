"""
Technical Indicator Calculator Module

This module calculates technical indicators (e.g., SMA, RSI, MACD)
from a given price DataFrame using the vectorbt library.
"""

import pandas as pd
import vectorbt as vbt
from typing import Dict, Any


def calculate_indicators(
    price_data: pd.DataFrame, settings: Dict[str, Any]
) -> pd.DataFrame:
    """
    Applies technical indicators to the price data based on the provided settings.

    Args:
        price_data: A DataFrame with a single 'price' column.
        settings: A configuration dictionary (from config.py).

    Returns:
        A new DataFrame with the original 'price' column plus all
        calculated indicator columns.
    """
    print("[IndicatorCalculator] Calculating technical indicators...")

    # Work on a copy to avoid modifying the original DataFrame
    processed_data = price_data.copy()
    price = processed_data["price"]

    # 1. Simple Moving Averages (SMAs)
    # vectorbt 0.26+ uses vbt.MA instead of vbt.SMA
    if "sma" in settings:
        for window in settings["sma"]["windows"]:
            col_name = f"SMA{window}"
            # vbt.MA defaults to Simple Moving Average (ewm=False)
            # The output attribute is .ma NOT .sma
            processed_data[col_name] = vbt.MA.run(price, window=window).ma
            print(f"[IndicatorCalculator] Calculated {col_name}")

    # 2. Relative Strength Index (RSI)
    if "rsi" in settings:
        window = settings["rsi"]["window"]
        col_name = f"RSI{window}"
        processed_data[col_name] = vbt.RSI.run(price, window=window).rsi
        print(f"[IndicatorCalculator] Calculated {col_name}")

    # 3. Moving Average Convergence Divergence (MACD)
    if "macd" in settings:
        macd_cfg = settings["macd"]
        macd_output = vbt.MACD.run(
            price,
            fast_window=macd_cfg["fast_window"],
            slow_window=macd_cfg["slow_window"],
            signal_window=macd_cfg["signal_window"],
        )
        # Add both the MACD line and its signal line
        processed_data["MACD"] = macd_output.macd
        processed_data["MACD_signal"] = macd_output.signal
        print("[IndicatorCalculator] Calculated MACD and MACD_signal")

    # Final Cleaning:
    # Drop all rows with NaN values (warm-up period).
    initial_rows = len(processed_data)
    processed_data = processed_data.dropna()
    final_rows = len(processed_data)

    print(f"[IndicatorCalculator] Dropped {initial_rows - final_rows} NaN rows.")
    print("[IndicatorCalculator] Calculation complete.")

    return processed_data
