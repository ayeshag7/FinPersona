"""
Market Environment Module

This is the main "public" class for the data module.
It imports and uses the other files (config, loader, calculator)
to build the complete, final environment.

The backtest runner will only interact with this class.
"""

import pandas as pd
from typing import Dict, Any, Optional

# Import our modular components
# Import our modular components
import legacy_market_data.config as config
import legacy_market_data.data_loader as data_loader
import legacy_market_data.indicator_calculator as indicator_calculator


class MarketEnvironment:
    """
    Orchestrates the loading and processing of market data.

    This class is the single point of entry for the main backtest.
    It serves the complete, processed market state one day at a time,
    ensuring no look-ahead bias.
    """

    def __init__(self):
        """
        Initializes the environment by loading config and setting up data.
        """
        print("[MarketEnvironment] Initializing...")
        self.config = config.INDICATOR_SETTINGS
        self.processed_data: Optional[pd.DataFrame] = None

        # This private method does the actual setup
        self._setup_environment()

    def _setup_environment(self):
        """
        Private method to run the data pipeline:
        1. Load config
        2. Call DataLoader
        3. Call IndicatorCalculator
        """
        # 1. Load raw data
        raw_price_data = data_loader.load_raw_data(
            ticker=config.TICKER, start_date=config.START_DATE, end_date=config.END_DATE
        )

        if raw_price_data is None:
            raise RuntimeError("Failed to load raw data. Environment setup aborted.")

        # 2. Calculate indicators
        self.processed_data = indicator_calculator.calculate_indicators(
            raw_price_data, self.config
        )
        print("[MarketEnvironment] Environment setup complete.")
        print(f"[MarketEnvironment] Final data has {len(self)} tradable days.")

    def get_state_for_day(self, day_index: int) -> Dict[str, Any]:
        """
        Returns all market data for a single day, specified by its
        integer-based index (iloc).

        Args:
            day_index: The integer index (iloc) of the day to retrieve.

        Returns:
            A dictionary of the market state (price, SMA20, RSI, etc.).
        """
        if self.processed_data is None:
            raise ValueError("Environment not set up. `processed_data` is None.")

        try:
            # Get the data for the specific day by its integer location
            state_series = self.processed_data.iloc[day_index]

            # Convert the pandas Series to a simple dictionary
            state_dict = state_series.to_dict()

            # Add the date (which is the index name) for clarity in the prompt
            state_dict["date"] = state_series.name.strftime("%Y-%m-%d")

            return state_dict

        except IndexError:
            # This is a critical error to catch during backtesting
            raise IndexError(
                f"Error: day_index {day_index} is out of bounds for processed data."
            )

    def get_price_series(self) -> pd.Series:
        """
        Returns the clean 'price' series (after dropping NaNs).
        This is needed by the vectorbt Portfolio.
        """
        if self.processed_data is None:
            raise ValueError("Environment not set up. `processed_data` is None.")
        return self.processed_data["price"]

    def __len__(self) -> int:
        """
        Returns the number of available trading days after processing.
        """
        if self.processed_data is None:
            return 0
        return len(self.processed_data)


#  This block allows us to test the file directly
if __name__ == "__main__":
    # 1. Initialize the environment
    print(" Testing MarketEnvironment Setup ")
    try:
        env = MarketEnvironment()

        # 2. Test the getters
        print("\n Environment Ready ")
        print(f"Total trading days (after processing): {len(env)}")

        # 3. Get state for a sample day (e.g., the first and last day)
        first_day_state = env.get_state_for_day(0)
        last_day_state = env.get_state_for_day(len(env) - 1)

        print(f"\n State for First Day ({first_day_state['date']}) ")
        import json

        print(json.dumps(first_day_state, indent=2, default=str))

        print(f"\n State for Last Day ({last_day_state['date']}) ")
        print(json.dumps(last_day_state, indent=2, default=str))

        # 4. Get the full price series
        price_data = env.get_price_series()
        print("\n Price Series (first 5 days) ")
        print(price_data.head())
        print("\n Price Series (last 5 days) ")
        print(price_data.tail())

    except Exception as e:
        print(f"\n!! An error occurred during testing: {e} !!")
