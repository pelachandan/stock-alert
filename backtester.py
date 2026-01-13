import pandas as pd
from utils.scanner_historical import run_scan_historical
from utils.pre_buy_check import pre_buy_check
from utils.market_data import get_historical_data

CAPITAL_PER_TRADE = 5_000  # $5k per trade


class Backtester:
    def __init__(self, start_date="2025-11-01", rr_ratio=2, max_days=30):
        self.start_date = pd.to_datetime(start_date)
        self.rr_ratio = rr_ratio
        self.max_days = max_days

    # ---------------- Main run ----------------
    def run(self):
        print(f"🚀 Running backtest from {self.start_date.date()}...")

        trades_outcomes = []

        # Loop through each business day from start_date to today
        all_days = pd.date_range(self.start_date, pd.Timestamp.today(), freq="B")

        for day in all_days:
            # Run historical scanner for that day
            signals = run_scan_historical(as_of_date=day)

            if not signals:
                continue

            # Pre-buy check
            trades_df = pre_buy_check(signals, rr_ratio=self.rr_ratio)
            if trades_df.empty:
                continue

            # Simulate each trade
            for row in trades_df.to_dict("records"):
                ticker = row["Ticker"]
                entry = row["Entry"]
                stop = row["StopLoss"]
                target = row["Target"]
                strategy = row.get("Strategy", "Unknown")

                hist = get_historical_data(ticker)
                hist = hist[hist.index >= day]
                if hist.empty:
                    continue

                outcome = self._simulate_trade(hist, entry, stop, target)

                # Position sizing & P/L
                position_size = CAPITAL_PER_TRADE / entry
                risk = position_size * abs(entry - stop)
                pnl = outcome["RMultiple"] * risk

                trades_outcomes.append({
                    **row,
                    **outcome,
                    "Year": day.year,
                    "Strategy": strategy,
                    "PositionSize": round(position_size, 2),
                    "RiskPerTrade_$": round(risk, 2),
                    "PnL_$": round(pnl, 2)
                })

        return pd.DataFrame(trades_outcomes)

    # ---------------- Trade simulation ----------------
    def _simulate_trade(self, df, entry, stop, target):
        df = df.iloc[: self.max_days]

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

        r = (exit_price - entry) / max(entry - stop, 0.01)

        return {
            "Outcome": outcome,
            "ExitPrice": round(exit_price, 2),
            "RMultiple": round(r, 2),
            "MAE": round(mae, 2),
            "MFE": round(mfe, 2),
            "HoldingDays": holding_days
        }

    # ---------------- Evaluation ----------------
    def evaluate(self, df):
        if df.empty:
            return "No trades executed"

        wins = (df["Outcome"] == "Win").sum()

        summary = {
            "TotalTrades": len(df),
            "Wins": wins,
            "Losses": len(df) - wins,
            "WinRate%": round(wins / len(df) * 100, 2),
            "AvgRMultiple": round(df["RMultiple"].mean(), 2),
            "TotalPnL_$": round(df["PnL_$"].sum(), 2),
            "AvgHoldingDays": round(df["HoldingDays"].mean(), 2)
        }

        # ---------------- Yearly summary ----------------
        yearly = df.groupby("Year").agg(
            Trades=("Ticker", "count"),
            TotalR=("RMultiple", "sum"),
            AvgR=("RMultiple", "mean"),
            TotalPnL_=("PnL_$", "sum"),  # ✅ corrected syntax
            AvgHoldingDays=("HoldingDays", "mean")
        ).round(2)

        summary["YearlySummary"] = yearly.to_dict("index")

        # Strategy-Year PnL
        summary["StrategyYearPnL"] = df.groupby(["Year", "Strategy"])["PnL_$"].sum().round(2).to_dict()

        return summary


# ---------------- Run ----------------
if __name__ == "__main__":
    bt = Backtester(start_date="2022-01-01")
    trades = bt.run()
    print(trades)

    stats = bt.evaluate(trades)
    print("\n📊 Backtest Summary:")
    for k, v in stats.items():
        print(k, ":", v)
