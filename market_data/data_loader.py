"""
Data Loader Module

This module is responsible for fetching raw stock data using yfinance
and performing initial data cleaning.
"""

import yfinance as yf
import pandas as pd
from typing import Optional


def load_raw_data(
    ticker: str, start_date: str, end_date: str
) -> Optional[pd.DataFrame]:
    """
    Downloads raw OHLCV data and returns a DataFrame with only the 'Close' price.
    Handles both MultiIndex (newer yfinance) and Flat Index formats.

    Args:
        ticker: The stock ticker to download (e.g., 'AAPL').
        start_date: The start date for the data (e.g., '2019-01-01').
        end_date: The end date for the data (e.g., '2021-12-31').

    Returns:
        A pandas DataFrame with a single 'price' column (from 'Close')
        and a DatetimeIndex. Returns None if download fails.
    """
    print(f"[DataLoader] Downloading {ticker} data from {start_date} to {end_date}...")
    try:
        # auto_adjust=True ensures we get the split/dividend adjusted price
        raw_data = yf.download(
            ticker, start=start_date, end=end_date, progress=False, auto_adjust=True
        )

        if raw_data.empty:
            print(
                f"[DataLoader] Error: No data found for {ticker} "
                "in the given date range."
            )
            return None

        # 1. Select the 'Close' data.
        # With a MultiIndex, this usually returns a DataFrame with the Ticker
        # as the column name (e.g., column 'AAPL').
        close_data = raw_data["Close"]

        # 2. Force conversion to a clean DataFrame with a specific column name.
        # If close_data is a DataFrame (MultiIndex case), take the first column.
        # If close_data is a Series (Flat Index case), just convert to frame.
        if isinstance(close_data, pd.DataFrame):
            price_data = close_data.iloc[:, 0].to_frame()
        else:
            price_data = close_data.to_frame()

        # 3. Rename the single column to 'price'
        price_data.columns = ["price"]

        print(f"[DataLoader] Download successful. Found {len(price_data)} data points.")
        return price_data

    except Exception as e:
        print(f"[DataLoader] Error during data download: {e}")
        return None
