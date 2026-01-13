import pandas as pd
import yfinance as yf
from config import MIN_MARKET_CAP, SP500_SOURCE
from utils.market_data import get_market_cap, get_historical_data
from utils.ema_utils import compute_rsi


def run_scan_historical(as_of_date, lookback_years=2):
    """
    Historical scanner that only uses data available up to `as_of_date`.
    Returns list of signal dicts compatible with pre_buy_check().
    """
    as_of_date = pd.to_datetime(as_of_date)

    # Load S&P500 tickers
    sp500 = pd.read_csv(SP500_SOURCE)
    tickers = sp500["Symbol"].tolist()

    signals = []

    # ---------- Market regime (SPY EMA200) ----------
    spy = yf.download(
        "SPY",
        start=as_of_date - pd.DateOffset(years=2),
        end=as_of_date + pd.Timedelta(days=1),
        progress=False
    )

    if spy.empty:
        market_bullish = True
    else:
        spy["EMA200"] = spy["Close"].ewm(span=200, adjust=False).mean()
        spy = spy[spy.index <= as_of_date]
        market_bullish = spy["Close"].iloc[-1] > spy["EMA200"].iloc[-1]

    # ---------- Scan tickers ----------
    for ticker in tickers:
        market_cap = get_market_cap(ticker)
        if not market_cap or market_cap < MIN_MARKET_CAP:
            continue

        # Get historical data
        df = get_historical_data(ticker)
        if df.empty:
            continue

        # Filter to lookback period
        lookback_start = as_of_date - pd.DateOffset(years=lookback_years)
        df = df[(df.index >= lookback_start) & (df.index <= as_of_date)]

        if df.empty or len(df) < 200:
            continue

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        ema20 = close.ewm(span=20).mean()
        ema50 = close.ewm(span=50).mean()
        ema200 = close.ewm(span=200).mean()

        # ---------- EMA crossover ----------
        if ema20.iloc[-1] > ema50.iloc[-1] > ema200.iloc[-1]:
            signals.append({
                "Ticker": ticker,
                "Price": close.iloc[-1],
                "AsOfDate": as_of_date,
                "Strategy": "EMA Crossover"
            })

        if not market_bullish:
            continue

        # ---------- 52-week high ----------
        high_52w = close.rolling(252).max().iloc[-1]
        pct_from_high = (close.iloc[-1] - high_52w) / high_52w * 100
        rsi14 = compute_rsi(close, 14).iloc[-1]

        if pct_from_high > -5 and rsi14 > 50:
            signals.append({
                "Ticker": ticker,
                "Price": close.iloc[-1],
                "AsOfDate": as_of_date,
                "Strategy": "52-Week High"
            })

        # ---------- Consolidation breakout ----------
        range_pct = (high.iloc[-20:].max() - low.iloc[-20:].min()) / close.iloc[-1]
        vol_ratio = volume.iloc[-1] / max(volume.iloc[-20:].mean(), 1)

        if range_pct < 0.08 and vol_ratio > 1.5:
            signals.append({
                "Ticker": ticker,
                "Price": close.iloc[-1],
                "AsOfDate": as_of_date,
                "Strategy": "Consolidation Breakout"
            })

        # ---------- Relative strength ----------
        if not spy.empty and len(spy) > 60:
            spy_close = spy["Close"].iloc[-1]
            rel_perf = (close.iloc[-1] / close.iloc[-60]) - (spy_close / spy["Close"].iloc[-60])
            if rel_perf > 0:
                signals.append({
                    "Ticker": ticker,
                    "Price": close.iloc[-1],
                    "AsOfDate": as_of_date,
                    "Strategy": "Relative Strength"
                })

    return signals
