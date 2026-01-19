# stock-alert

Daily SMA / EMA stock alert system (automated with GitHub Actions).

This project scans U.S. stocks daily to identify high-probability swing trade setups using multiple technical strategies. The system has been backtested over 4 years (2022-2025) and optimized for a balanced win rate and profitability.

## Current Configuration (Option 3 - Balanced)

**Trade Parameters:**
- Capital per trade: $10,000
- Risk/Reward ratio: 2:1 (conservative targets)
- Max trades per scan: 3
- Max holding period: 45 days

**Technical Filters:**
- ADX ≥ 24 (strong trend required)
- RSI: 50-66 (balanced momentum range)
- Volume: ≥1.4× 20-day average
- Liquidity: ≥$30M daily dollar volume
- Price action: 1-5% above EMA20

**Backtest Performance (2022-2025):**
- Total trades: 492
- Win rate: **35.77%** (10.77% above 2:1 R/R breakeven of 33.33%)
- Total profit: **$70,300** @ $10K per trade
- Annual return: **~29%**
- Required capital: $60,000 (max 6 concurrent positions)

This configuration prioritizes **safety margin** over maximum profit. The 10.77% buffer above breakeven provides stability across different market conditions.

## Logic & Filters

### 📈 EMA Crossover Signals
- Bullish EMA20/50/200 crossovers  
- EMA20 > EMA50 and EMA50 > EMA200 trend confirmation  
- Volume spike above 20-day average  
- RSI14 below 70 to avoid overbought conditions  
- Momentum-adjusted scoring to prioritize strong setups  

### 🚀 52-Week High Continuation (BUY-READY)
- Stocks near all-time 52-week highs (0% to -8% from high)  
- EMA20 > EMA50 > EMA200 structure  
- Volume ratio above 1.2× average  
- RSI14 below 75  
- Base score weighted by price proximity, EMA structure, and volume  
- Momentum boost applied via EMA200 slope + 5-day price momentum  

### 👀 52-Week High Watchlist
- Stocks slightly below 52-week highs not yet BUY-ready  
- Monitored for potential breakout or pullback opportunities  

### 📊 Consolidation Breakouts
- Stocks breaking out from multi-week sideways consolidation zones  
- Confirmed by above-average volume and trend continuation  
- Weighted score based on consolidation duration, breakout strength, and momentum  

### ⭐ Relative Strength / Sector Leaders
- Stocks outperforming peers in their sector or index  
- Identified via relative price strength and volume  
- Weighted score based on sector leadership and trend momentum

### 🔥 Pre-Buy Actionable Trades
- **Low-risk entry zones** identified after EMA crossover, 52-week highs, consolidation patterns, or relative strength setups  
- **Entry, Stop-Loss, and Target:** Calculated using price action, ATR-based volatility, and risk/reward ratios  
- **Weighted Score:** Combines EMA alignment, volume, momentum (RSI & ADX), and breakout potential  
- Designed to prioritize high-probability trades with defined risk management  
- Helps traders **quickly act** while controlling downside  

## Email Alerts
- Formatted HTML email automatically sent daily
- **Actionable Trades:** Shows only stocks that passed all filters (entry, stop-loss, target levels)
- **Watchlist:** Top 10 non-actionable signals with strategy names and scores
- Scores are **color-coded** for quick priority identification:
  - Green: Score ≥8.5 (high priority)
  - Yellow: Score 6.5-8.5 (medium priority)
  - Red: Score <6.5 (low priority)

## Configuration Management

All trading parameters are centralized in `trading_config.py`. This ensures consistency between live trading and backtesting.

**To adjust the strategy:**
1. Edit values in `trading_config.py`
2. Run backtest: `python3 backtester_walkforward.py`
3. Review results and iterate

**Common adjustments:**
- **Higher win rate:** Increase ADX, tighten RSI range, reduce MAX_TRADES_PER_SCAN
- **More opportunities:** Decrease ADX, widen RSI range, increase MAX_TRADES_PER_SCAN
- **Risk tolerance:** Adjust RISK_REWARD_RATIO (2:1 = safer, 3:1 = higher profit potential)

See `trading_config.py` for detailed parameter descriptions and tuning guidelines.

## Running Backtests

```bash
# Activate virtual environment
source venv/bin/activate

# Run walk-forward backtest (auto-updates data)
python3 backtester_walkforward.py
```

The backtester automatically downloads only missing data for faster subsequent runs.
