import pandas as pd
from datetime import datetime
from utils.scanner import run_scan
from utils.pre_buy_check import pre_buy_check
from utils.market_data import get_historical_data

CAPITAL_PER_TRADE = 5_000  # $5,000 per trade


class Backtester:
    """
    Historical backtester using your scan + pre-buy logic.

    Computes:
    - R-multiple
    - Dollar P/L (fixed $5k per trade)
    - MAE / MFE
    - Holding duration
    - Year-wise & strategy-wise summaries
    """

    def __init__(self, start_date="2022-01-01", rr_ratio=2, max_days=30):
        self.start_date = pd.to_datetime(start_date)
        self.rr_ratio = rr_ratio
        self.max_days = max_days

    def run(self, test_mode=False):
        print(f"🚀 Running backtest from {self.start_date.date()}...")

        ema_list, high_list, watchlist_highs, consolidation_list, rs_list = run_scan(
            test_mode=test_mode
        )

        # Ensure Strategy field exists
        for lst, name in [
            (ema_list, "EMA Crossover"),
            (high_list, "52-Week High"),
            (consolidation_list, "Consolidation Breakout"),
            (rs_list, "Relative Strength"),
        ]:
            for s in lst:
                s.setdefault("Strategy", name)

        combined_signals = ema_list + high_list + consolidation_list + rs_list
        trades_df = pre_buy_check(combined_signals, rr_ratio=self.rr_ratio)

        if trades_df.empty:
            print("⚠️ No trades generated for backtest.")
            return trades_df

        trades_outcomes = []

        for _, trade in trades_df.iterrows():
            ticker = trade["Ticker"]
            entry = trade["Entry"]
            stop = trade["StopLoss"]
            target = trade["Target"]
            strategy = trade.get("Strategy", "Unknown")

            hist_df = get_historical_data(ticker)
            if hist_df.empty:
                continue

            hist_df = hist_df[hist_df.index >= self.start_date]
            if hist_df.empty:
                continue

            outcome = self._simulate_trade(
                hist_df, entry, stop, target, self.max_days
            )

            # ---- Position sizing & dollar P/L ----
            position_size = CAPITAL_PER_TRADE / entry
            risk_per_trade = position_size * abs(entry - stop)
            pnl_dollars = outcome["RMultiple"] * risk_per_trade

            trade.update(outcome)
            trade["Strategy"] = strategy
            trade["Year"] = hist_df.index[0].year
            trade["PositionSize"] = round(position_size, 2)
            trade["RiskPerTrade_$"] = round(risk_per_trade, 2)
            trade["PnL_$"] = round(pnl_dollars, 2)

            trades_outcomes.append(trade)

        return pd.DataFrame(trades_outcomes)

    def _simulate_trade(self, df, entry, stop, target, max_days):
        df = df.iloc[:max_days].copy()

        mae = (entry - df["Low"]).max()
        mfe = (df["High"] - entry).max()

        exit_price = df["Close"].iloc[-1]
        outcome = "Win" if exit_price >= entry else "Loss"
        holding_days = len(df)

        for i, row in enumerate(df.itertuples()):
            if row.Low <= stop:
                exit_price = stop
                outcome = "Loss"
                holding_days = i + 1
                break
            if row.High >= target:
                exit_price = target
                outcome = "Win"
                holding_days = i + 1
                break

        r_multiple = (exit_price - entry) / max(entry - stop, 0.01)

        return {
            "MAE": round(mae, 2),
            "MFE": round(mfe, 2),
            "ExitPrice": round(exit_price, 2),
            "Outcome": outcome,
            "RMultiple": round(r_multiple, 2),
            "HoldingDays": holding_days,
        }

    def evaluate(self, trades_df):
        if trades_df.empty:
            return "No trades executed"

        total_trades = len(trades_df)
        wins = (trades_df["Outcome"] == "Win").sum()

        summary = {
            "TotalTrades": total_trades,
            "Wins": wins,
            "Losses": total_trades - wins,
            "WinRate%": round(wins / total_trades * 100, 2),
            "AvgRMultiple": round(trades_df["RMultiple"].mean(), 2),
            "TotalPnL_$": round(trades_df["PnL_$"].sum(), 2),
            "AvgHoldingDays": round(trades_df["HoldingDays"].mean(), 2),
        }

        # ---- Year-wise breakdown (FIXED) ----
        yearly = (
            trades_df.groupby("Year")
            .agg({
                "Ticker": "count",
                "RMultiple": ["sum", "mean"],
                "PnL_$": "sum",
                "HoldingDays": "mean",
            })
            .round(2)
        )

        yearly.columns = [
            "Trades",
            "TotalR",
            "AvgR",
            "TotalPnL_$",
            "AvgHoldingDays",
        ]

        summary["YearlySummary"] = yearly.to_dict(orient="index")

        # ---- Strategy + Year PnL ----
        summary["StrategyYearPnL"] = (
            trades_df.groupby(["Year", "Strategy"])["PnL_$"]
            .sum()
            .round(2)
            .to_dict()
        )

        return summary


if __name__ == "__main__":
    bt = Backtester(start_date="2022-01-01", rr_ratio=2)
    trades = bt.run(test_mode=False)
    print(trades)

    summary = bt.evaluate(trades)
    print("\n📊 Backtest Summary:")
    for k, v in summary.items():
        print(k, ":", v)
