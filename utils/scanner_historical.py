import pandas as pd
from utils.market_data import get_historical_data
from utils.indicators import calculate_ema, calculate_rs  # adjust if names differ

"""
Historical scanner
-----------------------------
Returns signals AS-OF a given historical date without look-ahead bias.
Used ONLY by backtester.py
"""

SPY_TICKER = "SPY"


def _market_regime(as_of_date):
    """Determine market regime using SPY EMA200 as of date."""
    spy = get_historical_data(SPY_TICKER)
    if spy.empty:
        return "UNKNOWN"

    spy = spy[spy.index <= as_of_date]
    if len(spy) < 200:
        return "UNKNOWN"

    ema200 = spy["Close"].ewm(span=200).mean().iloc[-1]
    close = spy["Close"].iloc[-1]

    return "BULLISH" if close > ema200 else "BEARISH"


def run_scan_historical(as_of_date, tickers, min_market_cap=1_000_000_000):
    """
    Run historical scan for a specific date.

    Parameters
    ----------
    as_of_date : datetime-like
        Date for which signals are generated
    tickers : list[str]
        Universe of tickers
    min_market_cap : int
        Market-cap filter (already applied upstream if desired)

    Returns
    -------
    tuple of lists: ema_list, high_list, consolidation_list, rs_list
    """
    as_of_date = pd.to_datetime(as_of_date)

    ema_list = []
    high_list = []
    consolidation_list = []
    rs_list = []

    regime = _market_regime(as_of_date)

    for ticker in tickers:
        df = get_historical_data(ticker)
        if df.empty:
            continue

        df = df[df.index <= as_of_date]
        if len(df) < 200:
            continue

        close = df["Close"].iloc[-1]
        high_52w = df["High"].rolling(252).max().iloc[-1]

        ema20 = df["Close"].ewm(span=20).mean().iloc[-1]
        ema50 = df["Close"].ewm(span=50).mean().iloc[-1]
        ema200 = df["Close"].ewm(span=200).mean().iloc[-1]

        # -------- EMA Crossover Strategy --------
        if ema20 > ema50 > ema200 and close > ema20:
            ema_list.append({
                "Ticker": ticker,
                "Price": round(close, 2),
                "AsOfDate": as_of_date,
                "Strategy": "EMA Crossover",
                "MarketRegime": regime,
            })

        # -------- 52-Week High Breakout --------
        if close >= 0.99 * high_52w and regime == "BULLISH":
            high_list.append({
                "Ticker": ticker,
                "Price": round(close, 2),
                "AsOfDate": as_of_date,
                "Strategy": "52-Week High",
                "MarketRegime": regime,
            })

        # -------- Consolidation Breakout (simple) --------
        recent = df.tail(20)
        if recent["High"].max() - recent["Low"].min() < 0.05 * close:
            consolidation_list.append({
                "Ticker": ticker,
                "Price": round(close, 2),
                "AsOfDate": as_of_date,
                "Strategy": "Consolidation Breakout",
                "MarketRegime": regime,
            })

        # -------- Relative Strength --------
        try:
            rs = calculate_rs(df)
            if rs > 1.1:
                rs_list.append({
                    "Ticker": ticker,
                    "Price": round(close, 2),
                    "AsOfDate": as_of_date,
                    "Strategy": "Relative Strength",
                    "MarketRegime": regime,
                })
        except Exception:
            pass

    return ema_list, high_list, consolidation_list, rs_list
