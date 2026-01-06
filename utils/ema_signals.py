import pandas as pd
from utils.ema_utils import compute_ema_incremental

def get_ema_signals(ticker):
    """
    Detects bullish EMA crossover (20>50 while 50>200) within last 20 days.
    Returns a dictionary with ticker info if 5–10% above crossover, else None.
    """
     df = compute_ema_incremental(ticker)

    if df.empty or len(df) < 210:
        return None

    df = df.copy()

    # --- Derived columns ---
    df["EMA200_slope"] = df["EMA200"] - df["EMA200"].shift(5)
    df["AvgVolume20"] = df["Volume"].rolling(20).mean()

    current_price = df.iloc[-1]["Close"]
    current_volume = df.iloc[-1]["Volume"]
    avg_volume = df.iloc[-1]["AvgVolume20"]

    # --- Volume confirmation (at least 20% above avg) ---
    if current_volume < 1.2 * avg_volume:
        return None

    # --- Look for crossover in last 20 days ---
    for i in range(-20, 0):
        today = df.iloc[i]
        yesterday = df.iloc[i - 1]

        if any(pd.isna([
            today["EMA20"], today["EMA50"], today["EMA200"], today["EMA200_slope"]
        ])):
            continue

        crossed = (
            yesterday["EMA20"] <= yesterday["EMA50"]
            and today["EMA20"] > today["EMA50"]
        )

        if not crossed:
            continue

        # --- Trend confirmation ---
        if today["EMA50"] <= today["EMA200"]:
            continue

        # --- EMA200 must be rising ---
        if today["EMA200_slope"] <= 0:
            continue

        crossover_price = today["Close"]

        pct_above_cross = (
            (current_price - crossover_price) / crossover_price * 100
        )

        pct_above_ema200 = (
            (current_price - today["EMA200"]) / today["EMA200"] * 100
        )

        if not (5 <= pct_above_cross <= 10 and 5 <= pct_above_ema200 <= 10):
            continue

        # --- Ranking score ---
        score = round(
            (pct_above_cross * 0.4)
            + (pct_above_ema200 * 0.4)
            + (min(current_volume / avg_volume, 3) * 10 * 0.2),
            2
        )

        return {
            "Ticker": ticker,
            "CrossoverDate": str(today.name.date()),
            "CrossoverPrice": round(crossover_price, 2),
            "CurrentPrice": round(current_price, 2),
            "PctAboveCrossover": round(pct_above_cross, 2),
            "PctAboveEMA200": round(pct_above_ema200, 2),
            "EMA20": round(today["EMA20"], 2),
            "EMA50": round(today["EMA50"], 2),
            "EMA200": round(today["EMA200"], 2),
            "VolumeRatio": round(current_volume / avg_volume, 2),
            "Score": score,
        }

    return None
