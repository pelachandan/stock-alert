from utils.scanner import run_scan
from utils.pre_buy_check import pre_buy_check
from utils.email_utils import send_email_alert

MAX_TRADES_EMAIL = 5
MIN_NORM_SCORE = 7

if __name__ == "__main__":
    print("🚀 Running full stock scan...")

    ema_list, high_list, high_watch_list, consolidation_list, rs_list = run_scan(test_mode=False)

    for s in ema_list:
        s["Strategy"] = "EMA Crossover"
    for s in high_list:
        s["Strategy"] = "52-Week High"
    for s in consolidation_list:
        s["Strategy"] = "Consolidation Breakout"
    for s in rs_list:
        s["Strategy"] = "Relative Strength"

    combined_signals = ema_list + high_list + consolidation_list + rs_list
    trade_ready = pre_buy_check(combined_signals)

    if not trade_ready.empty:
        trade_ready = trade_ready[
            trade_ready["NormalizedScore"] >= MIN_NORM_SCORE
        ].head(MAX_TRADES_EMAIL)

    send_email_alert(
        trade_df=trade_ready,
        high_buy_list=high_list,
        high_watch_list=high_watch_list,
        ema_list=ema_list,
        consolidation_list=consolidation_list,
        rs_list=rs_list
    )
