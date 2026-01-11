import pandas as pd
from utils.market_data import get_historical_data
from utils.ema_utils import compute_ema_incremental, compute_rsi

def check_consolidation_breakout(ticker, lookback=20):
    """
    Detects consolidation breakout:
    - Stock has been trading in a tight range for `lookback` days
    - Breaks above the recent high with volume confirmation
    """
    try:
        df = get_historical_data(ticker)
        if df.empty or "Close" not in df.columns:
            return None

        df = df.copy()
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce").dropna()
        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0)

        # EMA trend
        ema_df = compute_ema_incremental(ticker)
        if ema_df.empty:
            return None
        ema20 = ema_df["EMA20"].iloc[-1]
        ema50 = ema_df["EMA50"].iloc[-1]
        ema200 = ema_df["EMA200"].iloc[-1]

        # Consolidation: price range < 5% over lookback
        recent = df["Close"].iloc[-lookback:]
        max_close = recent.max()
        min_close = recent.min()
        if (max_close - min_close) / min_close * 100 > 5:
            return None  # Not tight range

        # Breakout today
        close_today = df["Close"].iloc[-1]
        if close_today <= max_close:
            return None  # No breakout yet

        # Volume confirmation
        avg_vol = df["Volume"].rolling(lookback).mean().iloc[-1]
        vol_ratio = df["Volume"].iloc[-1] / max(avg_vol, 1)
        if vol_ratio < 1.2:
            return None

        # RSI
        rsi14 = compute_rsi(df["Close"], period=14).iloc[-1]
        if rsi14 > 75:
            return None

        # Score calculation
        price_score = ((close_today - max_close) / max_close) * 100 * 0.4
        ema_score = 10 * 0.4 if ema20 > ema50 > ema200 else 0
        vol_score = min(vol_ratio, 3) * 10 * 0.2
        base_score = price_score + ema_score + vol_score

        ema200_slope = ema200 - ema200_df_shift(ema_df, 5)
        momentum_boost = min(ema200_slope / ema200 + (close_today - df["Close"].iloc[-6])/df["Close"].iloc[-6], 0.1)
        final_score = round(base_score * (1 + momentum_boost), 2)

        return {
            "Ticker": ticker,
            "Close": round(close_today, 2),
            "RangeLow": round(min_close, 2),
            "RangeHigh": round(max_close, 2),
            "VolumeRatio": round(vol_ratio, 2),
            "EMA20": round(ema20, 2),
            "EMA50": round(ema50, 2),
            "EMA200": round(ema200, 2),
            "RSI14": round(rsi14, 2),
            "Score": final_score
        }

    except Exception as e:
        print(f"⚠️ [consolidation_breakout] Error for {ticker}: {e}")
        return None

def ema200_df_shift(ema_df, period):
    """Helper to compute EMA200 slope"""
    if len(ema_df) < period + 1:
        return 0
    return ema_df["EMA200"].iloc[-period-1]
