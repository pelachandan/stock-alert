# pre_sell_check.py

import pandas as pd
import numpy as np
from utils.market_data import get_historical_data
from utils.ema_utils import compute_rsi

def compute_adx(df, period=14):
    """
    Compute ADX (Average Directional Index) for trend strength.
    """
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    plus_dm = high.diff()
    minus_dm = low.diff() * -1

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.rolling(period).mean()
    return adx

def pre_sell_check(strategy_list):
    """
    Apply pre-sell filters to multiple strategies.
    Returns a DataFrame with actionable short/put trades.
    
    strategy_list: list of dicts from any strategy (EMA, 52-week high, consolidation, RS)
    """
    actionable = []

    for s in strategy_list:
        ticker = s["Ticker"]
        df = get_historical_data(ticker)
        if df.empty or len(df) < 50:
            continue

        # --- Compute indicators ---
        df["RSI14"] = compute_rsi(df["Close"], 14)
        df["ADX14"] = compute_adx(df)
        df["ATR14"] = df["Close"].rolling(14).apply(lambda x: x.max() - x.min())

        current = df.iloc[-1]

        # --- Filters for short setup ---
        trend_ok = s.get("EMA20", 0) < s.get("EMA50", 0) and s.get("EMA50", 0) < s.get("EMA200", 0)
        rsi_ok = 28 <= current["RSI14"] <= 55  # Avoid oversold extremes
        adx_ok = current["ADX14"] >= 20        # Strong trend
        price_ok = current["Close"] >= s.get("CurrentPrice", current["Close"]) * 0.95  # Not too far below

        if all([trend_ok, rsi_ok, adx_ok, price_ok]):
            # --- Suggested levels ---
            entry_price = round(current["Close"], 2)
            stop_loss = round(current["EMA50"], 2)  # above EMA50
            target = round(entry_price - 2 * (stop_loss - entry_price), 2)  # 2x RR

            actionable.append({
                "Ticker": ticker,
                "Entry": entry_price,
                "StopLoss": stop_loss,
                "Target": target,
                "PctBelowCrossover": s.get("PctBelowCrossover", 0),
                "PctBelowEMA200": s.get("PctBelowEMA200", 0),
                "RSI14": round(current["RSI14"], 1),
                "ADX14": round(current["ADX14"], 1),
                "ATR14": round(current["ATR14"], 2),
                "Score": s.get("Score", 0)
            })

    df_actionable = pd.DataFrame(actionable)
    if not df_actionable.empty:
        df_actionable = df_actionable.sort_values(by="Score", ascending=False)

    return df_actionable
