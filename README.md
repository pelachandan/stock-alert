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
- **Relative Strength ≥ 80** (55-day RS vs SPY benchmark) - HIGH IMPACT #1
- **Sector Relative Strength** (20-day sector ETF vs SPY performance) - NEW
- **Accumulation/Distribution** (institutional buying/selling detection) - NEW
- **Earnings avoidance** (5-day buffer before earnings) - HIGH IMPACT #3 *(Live mode only)*
- **Weekly trend alignment** (for breakout strategies) - MEDIUM IMPACT #7
- **Gap filter** (max 3% gap up for breakouts) - LOWER IMPACT #10
- **Market regime filter** (blocks breakouts in bearish markets)

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
- **NEW:** Filters out stocks under institutional distribution (selling pressure)
- **NEW:** Boosts scores for stocks with strong accumulation (A+/A ratings)  

### ⭐ Relative Strength / Sector Leaders
- Stocks outperforming peers in their sector or index  
- Identified via relative price strength and volume  
- Weighted score based on sector leadership and trend momentum

### 🛡️ Risk Management Filters

**HIGH IMPACT Filters:**
1. **Relative Strength (RS) Rating ≥ 80** - Only trades stocks outperforming SPY benchmark over 55-day period. Filters out weak relative performers that are more likely to fail. *(Applied to all strategies)*

2. **Sector Relative Strength** - Ensures the stock's sector ETF is outperforming SPY over 20-day period. Maps stocks to 11 GICS sectors (XLK, XLF, XLV, etc.) and only trades stocks in leading sectors. *(Applied to all strategies)*

3. **Accumulation/Distribution Detection** - Uses 6 industry-recognized methods (Chaikin A/D, OBV, CMF, IBD-style rating, Up/Down Volume, VPT) to detect institutional buying vs selling. Blocks breakout trades on stocks under distribution (D+ or lower rating). Boosts scores 20% for stocks with A+/A accumulation ratings. *(Applied to Consolidation Breakout strategy)*

4. **Earnings Date Avoidance** - Skips stocks within 5 days of earnings announcements to avoid unpredictable volatility. Uses yfinance calendar with 24-hour caching. *(Live trading only - disabled in backtesting mode)*

**MEDIUM IMPACT Filters:**
3. **Weekly Trend Alignment** - For breakout strategies (52-Week High, Consolidation Breakout), ensures weekly timeframe is also trending up. Price must be above weekly EMA20 and weekly EMA20 > EMA50. *(Breakout strategies only)*

**LOWER IMPACT Filters:**
4. **Gap Filter** - Blocks entries on large gap ups (>3%) for breakout strategies to avoid chasing extended moves. *(Breakout strategies only)*

5. **Market Regime Filter** - Automatically blocks breakout trades (52-Week High, Consolidation Breakout) when SPY is in bearish regime (price below EMA20/50). Trend-following strategies like EMA Crossover still allowed.

### 🔥 Pre-Buy Actionable Trades
- **Low-risk entry zones** identified after EMA crossover, 52-week highs, consolidation patterns, or relative strength setups
- **ATR-Based Stop Loss:**
  - Breakout strategies (52-Week High, Consolidation): Entry - 1.5× ATR
  - EMA Crossover: Entry - 1.0× ATR
  - Other strategies: Entry - 1.2× ATR
- **Target Calculation:** Entry + (Risk/Reward Ratio × Stop Distance)
- **Position Sizing:** Based on 2.5× ATR multiplier for volatility-adjusted sizing
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

All trading parameters are centralized in `config/trading_config.py`. This ensures consistency between live trading and backtesting.

**Key Configuration Parameters:**
- `RS_RATING_THRESHOLD` - Relative strength minimum (default: 80)
- `SECTOR_RS_ENABLED` - Enable sector relative strength filter (default: True)
- `SECTOR_RS_LOOKBACK_DAYS` - Sector vs SPY lookback period (default: 20)
- `ACCUM_DIST_ENABLED` - Enable institutional accumulation detection (default: True)
- `ACCUM_DIST_PERIOD` - Lookback period for A/D analysis (default: 20)
- `ACCUM_DIST_MIN_RATING` - Minimum IBD-style rating required (default: B-)
- `ACCUM_DIST_BOOST_MULTIPLIER` - Score boost for A+/A ratings (default: 1.2)
- `EARNINGS_BUFFER_DAYS` - Days to avoid before earnings (default: 5)
- `MAX_GAP_UP_PCT` - Maximum gap up allowed for breakouts (default: 3%)
- `ATR_POSITION_MULTIPLIER` - Position sizing multiplier (default: 2.5x ATR)
- `RISK_REWARD_RATIO` - Target profit vs stop loss (default: 2:1)
- `MAX_TRADES_PER_SCAN` - Maximum concurrent positions (default: 3)

**To adjust the strategy:**
1. Edit values in `config/trading_config.py`
2. Run backtest: `python3 backtester_walkforward.py --scan-frequency W-MON`
3. Review results and iterate

**Common adjustments:**
- **Higher win rate:** Increase ADX, tighten RSI range, increase RS_RATING_THRESHOLD, reduce MAX_TRADES_PER_SCAN
- **More opportunities:** Decrease ADX, widen RSI range, lower RS_RATING_THRESHOLD, increase MAX_TRADES_PER_SCAN
- **Risk tolerance:** Adjust RISK_REWARD_RATIO (2:1 = safer, 3:1 = higher profit potential)
- **Earnings volatility:** Adjust EARNINGS_BUFFER_DAYS (5-7 days recommended)

See `trading_config.py` for detailed parameter descriptions and tuning guidelines.

## New Utility Modules

### 📊 `utils/earnings_utils.py`
- Fetches next earnings date using yfinance calendar API
- 24-hour caching to minimize API calls
- `is_near_earnings()` checks if stock is within buffer period (default 5 days)
- Automatically disabled during backtesting to avoid API inconsistencies

### 💪 `utils/relative_strength_utils.py`
- Calculates 55-day relative strength rating vs SPY benchmark
- RS Rating = (Stock's % change) / (SPY's % change) × 100
- Filters out stocks with RS < 80 (underperforming market)
- Uses cached SPY data for efficiency

### 📈 `utils/weekly_data_utils.py`
- Converts daily data to weekly timeframe
- `check_weekly_trend_alignment()` ensures weekly EMAs are bullish
- Applied to breakout strategies for higher-timeframe confirmation
- Prevents buying daily breakouts against weekly downtrends

### 🎯 `utils/sector_utils.py`
- Maps S&P 500 stocks to 11 GICS sector ETFs (XLK, XLF, XLV, etc.)
- `sector_is_leading()` checks if stock's sector is outperforming SPY
- Calculates 20-day performance for sector ETF vs SPY benchmark
- Fails open (allows trades) when sector data is unavailable
- Supports backtesting with `as_of_date` parameter

### 📈 `utils/accumulation_distribution.py`
- **6 Industry Methods for Institutional Detection:**
  1. **Chaikin A/D Line** - Where price closes within daily range × volume
  2. **On-Balance Volume (OBV)** - Cumulative volume on up vs down days
  3. **Chaikin Money Flow (CMF)** - Bounded -1 to +1 money flow indicator
  4. **IBD-Style Rating** - A+ to E rating based on volume patterns
  5. **Up/Down Volume Analysis** - Volume ratio on up vs down days
  6. **Volume Price Trend (VPT)** - Volume weighted by price change %
- **Rating Scale:**
  - A+ (80+) = Heavy institutional buying
  - A (60+) = Strong accumulation
  - B (10+) = Moderate accumulation
  - C (±10) = Neutral
  - D (-60) = Strong distribution
  - E (-90) = Heavy institutional selling
- **Key Functions:**
  - `detect_accumulation(df)` - Comprehensive analysis with composite score
  - `get_accumulation_rating(df)` - Quick IBD-style letter rating
  - `is_under_accumulation(df)` - Boolean check for institutional buying
  - `is_under_distribution(df)` - Boolean check for institutional selling

## Running Backtests

```bash
# Activate virtual environment
source venv/bin/activate

# Run walk-forward backtest with daily scans (default)
python3 backtester_walkforward.py --scan-frequency B

# Run with weekly scans (much faster, recommended for initial testing)
python3 backtester_walkforward.py --scan-frequency W-MON
```

**Scan Frequency Options:**
- `B` - Daily (business days)
- `W-MON` - Weekly on Mondays
- `W-TUE` through `W-FRI` - Weekly on other days

**Backtesting Mode Features:**
- Automatically downloads only missing historical data for faster runs
- **Earnings filter disabled** - Historical earnings data via API is unreliable, so this filter is skipped in backtests but active in live trading
- Walk-forward methodology ensures no look-ahead bias
- All data filtered to `as_of_date` to simulate real trading conditions

## Recent Enhancements

### Risk Management Improvements
- ✅ **Relative Strength Filter** - Only trades stocks with RS rating ≥80 vs SPY (55-day period)
- ✅ **Sector Relative Strength Filter** - Only trades stocks whose sectors are outperforming SPY (20-day period)
- ✅ **Accumulation/Distribution Filter** - Detects institutional buying/selling using 6 methods; blocks breakouts under distribution
- ✅ **Earnings Date Avoidance** - Skips stocks within 5 days of earnings (live mode only)
- ✅ **Weekly Trend Confirmation** - Breakout strategies require weekly timeframe alignment
- ✅ **Gap Filter** - Avoids chasing large gap ups (>3%) on breakout entries
- ✅ **Market Regime Filter** - Blocks breakout trades during bearish market conditions

### New Utility Modules
- 📦 `utils/earnings_utils.py` - Earnings date fetching with caching
- 📦 `utils/relative_strength_utils.py` - RS rating calculations vs SPY
- 📦 `utils/weekly_data_utils.py` - Weekly timeframe analysis
- 📦 `utils/sector_utils.py` - Sector-based relative strength filtering
- 📦 `utils/accumulation_distribution.py` - Institutional buying/selling detection (6 methods)

### Backtesting Enhancements
- 🔧 Earnings filter automatically disabled in backtest mode to prevent API errors
- 🔧 Configurable scan frequency (daily, weekly) for faster testing
- 🔧 Improved walk-forward methodology with strict `as_of_date` filtering
