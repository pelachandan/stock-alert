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
    Runs the complete SMA/EMA crossover + 52-week high + consolidation + relative strength scan.
    Sequential, with exponential backoff and retry.
    """

    print("🚀 Running full stock scan...")

    # Load S&P500 tickers
    sp500 = pd.read_csv(SP500_SOURCE)
    tickers = sp500["Symbol"].tolist()
    if test_mode:
        tickers = tickers[:15]

    # --- Initialize output lists ---
    ema_list = []
    high_list = []
    consolidation_list = []
    rs_list = []

    # Download benchmark for relative strength
    benchmark_df = yf.download("SPY", period="3mo", interval="1d")

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
                ema_list.append(ema_result)
        except Exception as e:
            print(f"⚠️ [scanner.py] Error processing EMA for {ticker}: {e}")

        # --- 52-Week High ---
        try:
            high_result = score_52week_high_stock(ticker)
            if high_result:
                high_list.append(high_result)
        except Exception as e:
            print(f"⚠️ [scanner.py] Error processing 52-week high for {ticker}: {e}")

        # --- Consolidation Breakout ---
        try:
            cons_result = check_consolidation_breakout(ticker)
            if cons_result:
                consolidation_list.append(cons_result)
        except Exception as e:
            print(f"⚠️ [scanner.py] Error processing consolidation breakout for {ticker}: {e}")

        # --- Relative Strength ---
        try:
            rs_result = check_relative_strength(ticker, benchmark_df)
            if rs_result:
                rs_list.append(rs_result)
        except Exception as e:
            print(f"⚠️ [scanner.py] Error processing relative strength for {ticker}: {e}")

    # --- Summary ---
    print("✅ Scan completed!")
    print(f"📈 EMA Crossovers: {len(ema_list)} stocks")
    print(f"🔥 52-week Highs: {len(high_list)} stocks")
    print(f"🔥 Consolidation Breakouts: {len(consolidation_list)} stocks")
    print(f"🚀 Relative Strength Leaders: {len(rs_list)} stocks")

    return ema_list, high_list, consolidation_list, rs_list
