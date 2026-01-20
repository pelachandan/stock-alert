import pandas as pd
import numpy as np
from utils.market_data import get_historical_data
from utils.ema_utils import compute_rsi, compute_ema_incremental
from config.trading_config import (
    ADX_THRESHOLD,
    RSI_MIN,
    RSI_MAX,
    VOLUME_MULTIPLIER,
    MIN_LIQUIDITY_USD,
    PRICE_ABOVE_EMA20_MIN,
    PRICE_ABOVE_EMA20_MAX,
    RISK_REWARD_RATIO,
    CAPITAL_PER_TRADE,
    ATR_POSITION_MULTIPLIER,
    RS_RATING_THRESHOLD,
    EARNINGS_BUFFER_DAYS,
    MAX_GAP_UP_PCT,
    SECTOR_RS_ENABLED,
    SECTOR_RS_LOOKBACK_DAYS
)

# -------------------------------------------------
# ADX
# -------------------------------------------------
def compute_adx(df, period=14):
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
    return dx.rolling(period).mean()


# -------------------------------------------------
# ATR
# -------------------------------------------------
def calculate_atr(df, period=14):
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - df["Close"].shift(1)).abs(),
        (df["Low"] - df["Close"].shift(1)).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()
    return atr.iloc[-1] if not atr.empty else 0


# -------------------------------------------------
# Score Normalization
# -------------------------------------------------
def normalize_score(score, strategy):
    ranges = {
        "EMA Crossover": (5, 18),
        "52-Week High": (6, 12),
        "Consolidation Breakout": (4, 10),
        "Relative Strength": (5, 15),
    }
    low, high = ranges.get(strategy, (0, 20))
    return round((score - low) / (high - low) * 10, 2)


# -------------------------------------------------
# Pre-Buy Check with Market Regime Filter
# -------------------------------------------------
def pre_buy_check(combined_signals, rr_ratio=None, benchmark="SPY", as_of_date=None):
    """
    Deduplicates signals, applies liquidity + trend filters,
    computes ATR-based stops, normalizes scores,
    and blocks breakout trades in bearish market regime.

    Args:
        combined_signals: List of signal dictionaries
        rr_ratio: Risk/reward ratio for target calculation
        benchmark: Benchmark ticker for regime (not used, kept for compatibility)
        as_of_date: Optional date for backtesting. If None, uses latest data (live mode).
                    If provided, filters data to only use information up to this date.
    """

    # Use config value if rr_ratio not provided
    if rr_ratio is None:
        rr_ratio = RISK_REWARD_RATIO

    # Market regime must be supplied by scanner (walk-forward safe)
    is_bullish = True
    mode = "BACKTEST" if as_of_date else "LIVE"
    print(f"📊 Mode: {mode} | Market regime ({benchmark}): {'BULLISH' if is_bullish else 'BEARISH'}")

    # -------------------------------
    # Deduplicate by strategy priority
    # -------------------------------
    priority = {
        "52-Week High": 4,
        "EMA Crossover": 3,
        "Consolidation Breakout": 2,
        "Relative Strength": 1,
    }

    best_signal = {}
    for s in combined_signals:
        t = s["Ticker"]
        if t not in best_signal or priority[s["Strategy"]] > priority[best_signal[t]["Strategy"]]:
            best_signal[t] = s

    signals = list(best_signal.values())
    trades = []

    # Load SPY benchmark once for RS calculations (cache for efficiency)
    from utils.relative_strength_utils import calculate_rs_rating
    spy_benchmark_df = get_historical_data("SPY")
    if as_of_date:
        spy_benchmark_df = spy_benchmark_df[spy_benchmark_df.index <= as_of_date]

    for s in signals:
        ticker = s["Ticker"]
        strategy = s["Strategy"]

        # -------------------------------
        # Skip breakout trades in bearish regime
        # -------------------------------
        market_regime = s.get("MarketRegime", "BULLISH")

        if market_regime == "BEARISH" and strategy in [
            "52-Week High",
            "Consolidation Breakout"
        ]:
            continue

        df = get_historical_data(ticker)
        if df.empty:
            continue

        # 🔒 CRITICAL: Filter to as_of_date for backtesting (prevents look-ahead bias)
        if as_of_date is not None:
            df = df[df.index <= as_of_date]

        if len(df) < 60:
            continue

        df = df.tail(60)
        close = df["Close"].iloc[-1]

        # -------------------------------
        # Relative Strength Filter (55-day vs SPY) - HIGH IMPACT #1
        # -------------------------------
        rs_rating = calculate_rs_rating(ticker, spy_benchmark_df, period=55)
        if rs_rating is None or rs_rating < RS_RATING_THRESHOLD:
            print(f"   Skipping {ticker}: RS rating {rs_rating} < {RS_RATING_THRESHOLD}")
            continue

        # -------------------------------
        # Sector Relative Strength Filter (sector vs SPY)
        # -------------------------------
        if SECTOR_RS_ENABLED:
            from utils.sector_utils import sector_is_leading
            if not sector_is_leading(ticker, days=SECTOR_RS_LOOKBACK_DAYS, as_of_date=as_of_date):
                print(f"   Skipping {ticker}: Sector underperforming SPY")
                continue

        # -------------------------------
        # Earnings date filter - HIGH IMPACT #3 (SKIP IN BACKTEST MODE)
        # -------------------------------
        # Only check earnings in live mode; skip in backtesting to avoid API issues
        if as_of_date is None:
            from utils.earnings_utils import is_near_earnings
            if is_near_earnings(ticker, as_of_date=as_of_date, days_buffer=EARNINGS_BUFFER_DAYS):
                print(f"   Skipping {ticker}: Within {EARNINGS_BUFFER_DAYS} days of earnings")
                continue

        # -------------------------------
        # Gap filter - LOWER IMPACT #10
        # -------------------------------
        if strategy in ["52-Week High", "Consolidation Breakout"]:
            if len(df) >= 2:
                prev_close = df["Close"].iloc[-2]
                today_open = df["Open"].iloc[-1]
                gap_pct = ((today_open - prev_close) / prev_close) * 100

                if gap_pct > MAX_GAP_UP_PCT:
                    print(f"   Skipping {ticker}: Large gap up ({gap_pct:.1f}%)")
                    continue

        # -------------------------------
        # Weekly trend confirmation - MEDIUM IMPACT #7
        # -------------------------------
        if strategy in ["52-Week High", "Consolidation Breakout"]:
            from utils.weekly_data_utils import check_weekly_trend_alignment
            if not check_weekly_trend_alignment(ticker, as_of_date=as_of_date):
                print(f"   Skipping {ticker}: Weekly trend not aligned")
                continue

        # -------------------------------
        # Liquidity filter (from config)
        # -------------------------------
        avg_dollar_vol = (df["Close"] * df["Volume"]).rolling(20).mean().iloc[-1]
        if avg_dollar_vol < MIN_LIQUIDITY_USD:
            continue

        # -------------------------------
        # ATR-based risk
        # -------------------------------
        atr = calculate_atr(df)
        if atr == 0:
            atr = close * 0.02

        entry = close

        if strategy in ["52-Week High", "Consolidation Breakout"]:
            stop = entry - 1.5 * atr
        elif strategy == "EMA Crossover":
            stop = entry - atr
        else:
            stop = entry - 1.2 * atr

        target = entry + rr_ratio * (entry - stop)

        # -------------------------------
        # ATR-based position sizing (2-3x ATR guideline from research)
        # -------------------------------
        suggested_shares = int(CAPITAL_PER_TRADE / entry)
        risk_per_share = atr * ATR_POSITION_MULTIPLIER

        # -------------------------------
        # EMA strategy extra filters
        # -------------------------------
        if strategy == "EMA Crossover":
            df["RSI14"] = compute_rsi(df["Close"], 14)
            df["ADX14"] = compute_adx(df)

            trend_ok = s["EMA20"] > s["EMA50"] > s["EMA200"]
            rsi_ok = RSI_MIN <= df["RSI14"].iloc[-1] <= RSI_MAX
            adx_ok = df["ADX14"].iloc[-1] >= ADX_THRESHOLD

            # Volume confirmation (from config)
            vol_ratio = df["Volume"].iloc[-1] / df["Volume"].rolling(20).mean().iloc[-1]
            volume_ok = vol_ratio >= VOLUME_MULTIPLIER

            # Price action filter (from config)
            price_above_ema20 = (close - s["EMA20"]) / s["EMA20"]
            ema_distance_ok = PRICE_ABOVE_EMA20_MIN <= price_above_ema20 <= PRICE_ABOVE_EMA20_MAX

            if not all([trend_ok, rsi_ok, adx_ok, volume_ok, ema_distance_ok]):
                continue

        norm_score = normalize_score(s.get("Score", 0), strategy)

        trades.append({
            "Ticker": ticker,
            "Strategy": strategy,
            "Entry": round(entry, 2),
            "StopLoss": round(stop, 2),
            "Target": round(target, 2),
            "ATR": round(atr, 2),
            "SuggestedShares": suggested_shares,
            "RiskPerShare": round(risk_per_share, 2),
            "Score": s.get("Score", 0),
            "NormalizedScore": norm_score,
        })

    df_trades = pd.DataFrame(trades)
    if not df_trades.empty:
        df_trades = df_trades.sort_values(by="NormalizedScore", ascending=False)

    return df_trades
