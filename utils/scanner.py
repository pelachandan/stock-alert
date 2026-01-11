import time
import pandas as pd
import yfinance as yf
from config import MIN_MARKET_CAP, SP500_SOURCE
from utils.market_data import get_market_cap
from utils.ema_signals import get_ema_signals
from utils.high_52w_strategy import score_52week_high_stock
from utils.consolidation_breakout import check_consolidation_breakout
from utils.relative_strength import check_relative_strength

BACKOFF_BASE = 2
MAX_RETRIES = 5

def run_scan(test_mode=False):
    """
    Runs the complete SMA crossover + 52-week high scan.
    Sequential, with exponential backoff and retry.
    """
    print("🚀 Running SMA crossover and 52-week high scan...")

    sp500 = pd.read_csv(SP500_SOURCE)
    tickers = sp500["Symbol"].tolist()
    if test_mode:
        tickers = tickers[:15]

    ema_signals, new_highs = [], []

    for ticker in tickers:
        # --- Market Cap Check ---
        attempt, market_cap = 0, None
        while attempt < MAX_RETRIES:
            market_cap = get_market_cap(ticker)
            if market_cap and market_cap > MIN_MARKET_CAP:
                break
            wait = BACKOFF_BASE ** attempt
            print(f"⚠️ [scanner.py] Retry {attempt+1} for {ticker} market cap in {wait}s")
            time.sleep(wait)
            attempt += 1
        else:
            print(f"⚠️ [scanner.py] Skipping {ticker} due to low/missing market cap")
            continue

        # --- EMA Signal ---
        try:
            ema_result = get_ema_signals(ticker)
            if ema_result:
                ema_signals.append(ema_result)
        except Exception as e:
            print(f"⚠️ [scanner.py] Error processing SMA for {ticker}: {e}")

        # --- 52-Week High ---
        try:
            high_result = score_52week_high_stock(ticker)
            if high_result:
                new_highs.append(high_result)
        except Exception as e:
            print(f"⚠️ [scanner.py] Error processing new high for {ticker}: {e}")

    # --- New: Consolidation Breakouts ---
    consolidation_list = []
    for t in tickers:
        result = check_consolidation_breakout(t)
        if result:
            consolidation_list.append(result)

    # --- New: Relative Strength ---
    benchmark_df = yf.download("SPY", period="3mo", interval="1d")
    rs_list = []
    for t in tickers:
        result = check_relative_strength(t, benchmark_df)
        if result:
            rs_list.append(result)

    return ema_list, high_list, consolidation_list, rs_list

    print("✅ Scan completed!")
    print(f"📈 EMA Crossovers: {ema_signals}")
    print(f"🔥 New 52-week Highs: {new_highs}")
    print(f"🔥 New Consolidation Breakouts: {consolidation_list}")
    print(f"🔥 New Relative Strength Breakouts: {rs_list}")
    return ema_signals, new_highs
