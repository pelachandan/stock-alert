from utils.scanner import run_scan
from utils.pre_buy_check import pre_buy_check
from utils.pre_sell_check import pre_sell_check
from utils.email_utils import send_email_alert
from utils.high_52w_strategy import score_52week_high_stock
import pandas as pd

if __name__ == "__main__":
    print("🚀 Running full stock scan...")

    # --------------------------------------------------
    # Step 1: Run complete scan
    # Returns: ema_list, high_list (BUY-ready), watchlist_highs, consolidation_list, rs_list
    # --------------------------------------------------
    ema_list, high_list, high_watch_list, consolidation_list, rs_list = run_scan(test_mode=False)

    # --------------------------------------------------
    # Step 2: Apply pre-buy checks on all strategies
    # --------------------------------------------------
    prebuy_list = []
    for lst in [ema_list, high_list, consolidation_list, rs_list]:
        prebuy_list.extend(lst if lst else [])
    trade_ready = pre_buy_check(prebuy_list)

    # --------------------------------------------------
    # Step 3: Apply pre-sell checks on all strategies
    # --------------------------------------------------
    # Pre-Sell Actionable Trades (fix by generating low_list, reverse_consolidation_list, reverse_rs_list)
    presell_list = []
    low_list = []
    reverse_consolidation_list = []
    reverse_rs_list = []

    # Use low / breakdown / underperforming lists
    presell_list.extend(ema_list if ema_list else [])
    presell_list.extend(low_list if low_list else [])
    presell_list.extend(reverse_consolidation_list if reverse_consolidation_list else [])
    presell_list.extend(reverse_rs_list if reverse_rs_list else [])    
    trade_short_ready = pre_sell_check(presell_list)

    # --------------------------------------------------
    # Step 4: Console summary
    # --------------------------------------------------
    # EMA Crossovers
    if ema_list:
        print("\n📈 EMA Crossovers:")
        for s in ema_list:
            print(f"{s['Ticker']} - {s['PctAboveCrossover']}% | Score: {s['Score']}")
    else:
        print("\n📈 No EMA crossovers today.")

    # Pre-Buy Actionable Trades
    if not trade_ready.empty:
        print("\n🔥 Pre-Buy Actionable Trades:")
        for t in trade_ready.to_dict(orient="records"):
            print(
                f"{t['Ticker']} | Entry: {t['Entry']} | Stop: {t['StopLoss']} | "
                f"Target: {t['Target']} | Score: {t['Score']}"
            )
    else:
        print("\n🔥 No actionable trades today.")

    # Pre-Sell Actionable Trades
    if not trade_short_ready.empty:
        print("\n📉 Pre-Sell Actionable Trades:")
        for t in trade_short_ready.to_dict(orient="records"):
            print(
                f"{t['Ticker']} | Entry: {t['Entry']} | Stop: {t['StopLoss']} | "
                f"Target: {t['Target']} | Score: {t['Score']}"
            )
    else:
        print("\n📉 No actionable short trades today.")

    # 52-Week High BUY-READY
    if high_list:
        print("\n🚀 52-Week High BUY-READY:")
        for h in high_list:
            print(f"{h['Ticker']} | Score: {h.get('Score', 'N/A')}")
    else:
        print("\n🚀 No BUY-ready 52-week highs today.")

    # 52-Week High WATCHLIST
    if high_watch_list:
        print("\n👀 52-Week High WATCHLIST:")
        for h in high_watch_list:
            print(f"{h['Ticker']} | {h['PctFrom52High']:.2f}% from high")
    else:
        print("\n👀 No watchlist candidates today.")

    # Consolidation Breakouts
    if consolidation_list:
        print("\n📦 Consolidation Breakouts:")
        for c in consolidation_list:
            print(f"{c['Ticker']} | Score: {c['Score']}")
    else:
        print("\n📦 No consolidation breakouts today.")

    # Relative Strength Leaders
    if rs_list:
        print("\n💪 Relative Strength Leaders:")
        for r in rs_list:
            print(f"{r['Ticker']} | RS%: {r['RS%']} | Score: {r['Score']}")
    else:
        print("\n💪 No relative strength leaders today.")

    # --------------------------------------------------
    # Step 5: Send HTML email
    # --------------------------------------------------
    send_email_alert(
        prebuy_df=trade_ready,
        presell_df=trade_short_ready,
        high_buy_list=high_list,
        high_watch_list=high_watch_list,
        ema_list=ema_list,
        consolidation_list=consolidation_list,
        rs_list=rs_list
    )
