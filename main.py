from utils.scanner import run_scan
from utils.pre_buy_check import pre_buy_check
from utils.email_utils import send_email_alert
from utils.high_52w_strategy import score_52week_high_stock, is_52w_watchlist_candidate
import pandas as pd

if __name__ == "__main__":
    print("🚀 Running EMA crossover and 52-week high scan...")

    # --------------------------------------------------
    # Step 1: Run scan
    # --------------------------------------------------
    ema_list, high_list = run_scan(test_mode=False)

    # --------------------------------------------------
    # Step 2: Apply pre-buy checks on EMA setups
    # --------------------------------------------------
    trade_ready = pre_buy_check(ema_list)

    # --------------------------------------------------
    # Step 3: Split 52-week highs
    # --------------------------------------------------
    high_buy_list = []
    high_watch_list = []

    for h in high_list or []:
        score = score_52week_high_stock(h)

        if score is not None:
            h["Score"] = score
            high_buy_list.append(h)
        elif is_52w_watchlist_candidate(h):
            high_watch_list.append(h)

    # --------------------------------------------------
    # Step 4: Console summary (optional)
    # --------------------------------------------------
    if ema_list:
        print("\n📈 EMA Crossovers:")
        for s in ema_list:
            print(f"{s['Ticker']} - {s['PctAboveCrossover']}% | Score: {s['Score']}")
    else:
        print("\n📈 No EMA crossovers found today.")

    if not trade_ready.empty:
        print("\n🔥 Pre-Buy Actionable Trades:")
        for t in trade_ready.to_dict(orient="records"):
            print(
                f"{t['Ticker']} | Entry: {t['Entry']} | Stop: {t['StopLoss']} | "
                f"Target: {t['Target']} | Score: {t['Score']}"
            )
    else:
        print("\n🔥 No actionable trades found today.")

    if high_buy_list:
        print("\n🚀 52-Week High BUY-READY:")
        for h in high_buy_list:
            print(f"{h['Ticker']} | Score: {h['Score']}")
    else:
        print("\n🚀 No BUY-ready 52-week highs today.")

    if high_watch_list:
        print("\n👀 52-Week High WATCHLIST:")
        for h in high_watch_list:
            print(f"{h['Ticker']} | {h['PctFrom52High']}% from high")
    else:
        print("\n👀 No watchlist candidates today.")

    # --------------------------------------------------
    # Step 5: Send email (ALL formatting inside email_utils)
    # --------------------------------------------------
    send_email_alert(
        trade_df=trade_ready,
        high_buy_list=high_buy_list,
        high_watch_list=high_watch_list,
        ema_list=ema_list
    )
