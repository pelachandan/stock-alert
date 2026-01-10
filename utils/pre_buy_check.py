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


def pre_buy_check(ema_list):
    """
    Apply pre-buy filters and calculate entry/stop/target levels.
    Returns a DataFrame with actionable info.
    """
    actionable = []

    for s in ema_list:
        ticker = s["Ticker"]
        df = get_historical_data(ticker)
        if df.empty or len(df) < 50:
            continue

        # Compute trend & momentum indicators
        df["RSI14"] = compute_rsi(df["Close"], 14)
        df["ADX14"] = compute_adx(df)
        df["ATR14"] = df["Close"].rolling(14).apply(lambda x: x.max() - x.min())

        current = df.iloc[-1]

        # --- Filters ---
        trend_ok = s["EMA20"] > s["EMA50"] and s["EMA50"] > s["EMA200"]
        rsi_ok = 45 <= current["RSI14"] <= 72
        adx_ok = current["ADX14"] >= 20  # strong trend
        price_ok = current["Close"] <= s["CurrentPrice"] * 1.05  # not too extended

        if all([trend_ok, rsi_ok, adx_ok, price_ok]):
            # --- Suggested levels ---
            entry_price = round(s["CurrentPrice"], 2)
            stop_loss = round(s["EMA50"], 2)  # below EMA50
            target = round(entry_price + 2 * (entry_price - stop_loss), 2)  # 2x RR

            actionable.append({
                "Ticker": ticker,
                "Entry": entry_price,
                "StopLoss": stop_loss,
                "Target": target,
                "PctAboveCrossover": s["PctAboveCrossover"],
                "PctAboveEMA200": s["PctAboveEMA200"],
                "RSI14": round(current["RSI14"], 1),
                "ADX14": round(current["ADX14"], 1),
                "ATR14": round(current["ATR14"], 2),
                "Score": s["Score"]
            })

    df_actionable = pd.DataFrame(actionable)
    if not df_actionable.empty:
        df_actionable = df_actionable.sort_values(by="Score", ascending=False)

    return df_actionable
