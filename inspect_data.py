"""
Script to inspect raw yfinance data structure.
"""

import yfinance as yf


def inspect_yfinance_data():
    print(" Downloading AAPL Data (Default Settings) ")

    # We download exactly as we tried in the project
    # Note: auto_adjust=True is often the default in newer versions
    df = yf.download(
        "AAPL", start="2019-01-01", end="2021-12-31", progress=False, auto_adjust=True
    )

    print("\n1. DataFrame Shape (Rows, Columns):")
    print(df.shape)

    print("\n2. Column Names:")
    print(df.columns)

    print("\n3. First 5 Rows:")
    print(df.head())

    print("\n4. Data Info:")
    print(df.info())


if __name__ == "__main__":
    inspect_yfinance_data()
