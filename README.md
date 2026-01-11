# sma-stock-alert

Daily SMA / EMA stock alert system (automated with GitHub Actions).

This project scans U.S. stocks daily to identify high-probability swing trade setups using:

## Logic & Filters

### 📈 EMA Crossover Signals
- Bullish EMA20/50/200 crossovers
- EMA20 > EMA50 and EMA50 > EMA200 trend confirmation
- Volume spike above 20-day average
- RSI14 below 70 to avoid overbought conditions
- Momentum-adjusted scoring to prioritize strong setups

### 🔥 Pre-Buy Actionable Trades
- Low-risk entry zones identified after EMA crossover
- Entry, stop-loss, and target calculated based on price action
- Weighted score based on EMA alignment, volume, and momentum

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

## Email Alerts
- Formatted HTML email automatically sent daily
- Includes EMA crossovers, pre-buy trades, BUY-ready 52-week highs, and watchlist
- Scores are color-coded for priority
