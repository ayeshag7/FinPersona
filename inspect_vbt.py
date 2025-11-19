"""
Script to inspect the installed vectorbt library capabilities.
"""

import vectorbt as vbt
import inspect


def inspect_vectorbt():
    print(f" VectorBT Version: {vbt.__version__} ---\n")

    all_attributes = dir(vbt)

    # 1. Search for Moving Average related terms
    ma_terms = [attr for attr in all_attributes if "MA" in attr]
    print("Attributes containing 'MA' (Moving Averages):")
    print(ma_terms)
    print("-" * 40)

    # 2. Search for RSI related terms
    rsi_terms = [attr for attr in all_attributes if "RSI" in attr]
    print("Attributes containing 'RSI':")
    print(rsi_terms)
    print("-" * 40)

    # 3. Search for MACD related terms
    macd_terms = [attr for attr in all_attributes if "MACD" in attr]
    print("Attributes containing 'MACD':")
    print(macd_terms)
    print("-" * 40)

    # 4. specific check for the 'MA' class which replaces SMA in newer versions
    if "MA" in all_attributes:
        print("\nFound 'vbt.MA' class. Checking its run method signature...")
        try:
            # Inspect the parameters of the run method to see what it accepts
            sig = inspect.signature(vbt.MA.run)
            print(f"vbt.MA.run signature: {sig}")
        except Exception as e:
            print(f"Could not inspect vbt.MA.run: {e}")


if __name__ == "__main__":
    inspect_vectorbt()
