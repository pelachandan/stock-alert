import pandas as pd
from utils.scanner_historical import run_scan_historical
from utils.pre_buy_check import pre_buy_check
from utils.market_data import get_historical_data

CAPITAL_PER_TRADE = 5_000  # $5k per trade


class Backtester:
    """
    Historical backtester using scanner_historical + pre-buy logic.

    Produces:
    - Outcome (Win/Loss)
    - R-Multiple
    - Dollar P/L
    - MAE / MFE
    - Holding duration
    - Yearly & strategy summaries
    """

    def __init__(self, start_date="2022-01-01", rr_ratio=2, max_days=30):
        self.start_date = pd.to_datetime(start_date)
        self.rr_ratio = rr_ratio
        self.max_days = max_days

    # ---------------------------------------------------------
    # MAIN RUN
    # ---------------------------------------------------------
    def run(self, test_mode=False):
        print(f"🚀 Running backtest from {self.start_date.date()}...")

        # Use historical scanner
        signals = run_scan_historical(as_of_date=self.start_date)
        if test_mode:
            signals = signals[:50]  # limit for testing

        trades_df = pre_buy_check(signals, rr_ratio=self.rr_ratio)
        if trades_df.empty:
            print("⚠️ No trades generated.")
            return pd.DataFrame()

        results = []

        for row in trades_df.to_dict("records"):
            ticker = row["Ticker"]
            entry = row["Entry"]
            stop = row["StopLoss"]
            target = row["Target"]
            signal_date = row.get("AsOfDate", self.start_date)
            strategy = row.get("Strategy", "Unknown")

            hist = get_historical_data(ticker)
            hist = hist[hist.index >= signal_date]
            if hist.empty:
                continue

            outcome = self._simulate_trade(hist, entry, stop, target)

            # ---- position sizing ----
            position_size = CAPITAL_PER_TRADE / entry
            risk = position_size * abs(entry - stop)
            pnl = outcome["RMultiple"] * risk

            results.append({
                **row,
                **outcome,
                "Year": signal_date.year,
                "Strategy": strategy,
                "PositionSize": round(position_size, 2),
                "RiskPerTrade_$": round(risk, 2),
                "PnL_$": round(pnl, 2),
            })

        return pd.DataFrame(results)

    # ---------------------------------------------------------
    # TRADE SIMULATION
    # ---------------------------------------------------------
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
            "HoldingDays": holding_days,
        }

    # ---------------------------------------------------------
    # EVALUATION
    # ---------------------------------------------------------
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
            "AvgHoldingDays": round(df["HoldingDays"].mean(), 2),
        }

        # ---- Yearly breakdown ----
        yearly = (
            df.groupby("Year")
            .agg({
                "Ticker": "count",
                "RMultiple": ["sum", "mean"],
                "PnL_$": "sum",
                "HoldingDays": "mean",
            })
            .round(2)
        )
        yearly.columns = ["Trades", "TotalR", "AvgR", "TotalPnL_$", "AvgHoldingDays"]
        summary["YearlySummary"] = yearly.to_dict("index")

        # ---- Strategy-Year PnL ----
        summary["StrategyYearPnL"] = (
            df.groupby(["Year", "Strategy"])["PnL_$"]
            .sum()
            .round(2)
            .to_dict()
        )

        return summary


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------
if __name__ == "__main__":
    bt = Backtester(start_date="2022-01-01")
    trades = bt.run(test_mode=False)
    print(trades)

    stats = bt.evaluate(trades)
    print("\n📊 Backtest Summary:")
    for k, v in stats.items():
        print(k, ":", v)
