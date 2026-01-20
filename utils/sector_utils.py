"""
Sector Relative Strength Utilities
===================================
Functions to determine if a stock's sector is outperforming the market (SPY).
"""

import pandas as pd
from pathlib import Path
from utils.market_data import get_historical_data

SECTOR_MAPPING_FILE = Path("data/sector_mapping.csv")

# Cache for sector mapping (loaded once per session)
_sector_mapping_cache = None


def get_sector_etf(ticker):
    """
    Get the sector ETF for a given ticker.

    Args:
        ticker: Stock symbol (e.g., "AAPL")

    Returns:
        Sector ETF symbol (e.g., "XLK") or None if not found
    """
    global _sector_mapping_cache

    # Load and cache sector mapping on first call
    if _sector_mapping_cache is None:
        if not SECTOR_MAPPING_FILE.exists():
            print(f"⚠️ [sector_utils.py] Sector mapping file not found: {SECTOR_MAPPING_FILE}")
            return None

        try:
            _sector_mapping_cache = pd.read_csv(SECTOR_MAPPING_FILE)
        except Exception as e:
            print(f"⚠️ [sector_utils.py] Error loading sector mapping: {e}")
            return None

    # Look up ticker in mapping
    result = _sector_mapping_cache[_sector_mapping_cache["Symbol"] == ticker]

    if result.empty:
        return None

    return result.iloc[0]["SectorETF"]


def calculate_performance(ticker, days=20, as_of_date=None):
    """
    Calculate percentage performance over N days.

    Args:
        ticker: Stock or ETF symbol
        days: Lookback period in trading days
        as_of_date: Optional date for backtesting. If None, uses latest data.

    Returns:
        Performance percentage (e.g., 5.2 for 5.2% gain) or None if insufficient data
    """
    df = get_historical_data(ticker)

    if df.empty:
        return None

    # Filter to as_of_date for backtesting (prevents look-ahead bias)
    if as_of_date is not None:
        df = df[df.index <= as_of_date]

    if len(df) < days + 1:
        return None

    # Get current price and price N days ago
    current_price = df["Close"].iloc[-1]
    past_price = df["Close"].iloc[-(days + 1)]

    if past_price == 0:
        return None

    # Calculate percentage performance
    performance = ((current_price - past_price) / past_price) * 100

    return performance


def sector_is_leading(ticker, days=20, as_of_date=None):
    """
    Check if a stock's sector is outperforming SPY over N days.

    Args:
        ticker: Stock symbol (e.g., "AAPL")
        days: Lookback period in trading days (default: 20)
        as_of_date: Optional date for backtesting. If None, uses latest data.

    Returns:
        True if sector is outperforming SPY, False otherwise

    Edge cases:
        - Ticker not in sector mapping: Returns True (allow trade)
        - Sector ETF data missing: Returns True (allow trade)
        - SPY data missing: Returns True (allow trade)
        - Insufficient historical data: Returns True (allow trade)
    """
    # Get sector ETF for this ticker
    sector_etf = get_sector_etf(ticker)

    if sector_etf is None:
        # Ticker not in sector mapping - allow trade (fail open)
        return True

    # Calculate sector performance
    sector_perf = calculate_performance(sector_etf, days=days, as_of_date=as_of_date)

    if sector_perf is None:
        # Insufficient sector data - allow trade (fail open)
        return True

    # Calculate SPY performance
    spy_perf = calculate_performance("SPY", days=days, as_of_date=as_of_date)

    if spy_perf is None:
        # Insufficient SPY data - allow trade (fail open)
        return True

    # Sector is leading if it outperforms SPY
    return sector_perf > spy_perf


def get_sector_performance_summary(tickers, days=20, as_of_date=None):
    """
    Get performance summary for multiple tickers and their sectors.

    Useful for debugging and analysis.

    Args:
        tickers: List of stock symbols
        days: Lookback period in trading days
        as_of_date: Optional date for backtesting

    Returns:
        DataFrame with ticker, sector ETF, sector performance, SPY performance, and leading status
    """
    results = []

    for ticker in tickers:
        sector_etf = get_sector_etf(ticker)
        sector_perf = calculate_performance(sector_etf, days=days, as_of_date=as_of_date) if sector_etf else None
        spy_perf = calculate_performance("SPY", days=days, as_of_date=as_of_date)
        is_leading = sector_is_leading(ticker, days=days, as_of_date=as_of_date)

        results.append({
            "Ticker": ticker,
            "SectorETF": sector_etf,
            "SectorPerf": round(sector_perf, 2) if sector_perf else None,
            "SPYPerf": round(spy_perf, 2) if spy_perf else None,
            "IsLeading": is_leading
        })

    return pd.DataFrame(results)
