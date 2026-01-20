"""
Trading Strategy Configuration
================================
Centralized configuration for BOTH live trading and backtesting.
Modify these values to tune your strategy - changes apply everywhere.
"""

# =============================================================================
# POSITION SIZING & RISK MANAGEMENT
# =============================================================================

CAPITAL_PER_TRADE = 10_000  # Capital allocated per trade in USD
RISK_REWARD_RATIO = 2       # Target profit is X times the risk (OPTION 3: Easier target)
                            # 2 = 2:1 (conservative)
                            # 3 = 3:1 (balanced)
                            # 4 = 4:1 (aggressive)

MAX_HOLDING_DAYS = 45       # Maximum days to hold a trade

ATR_POSITION_MULTIPLIER = 2.5  # 2-3x ATR for swing trading (HIGH IMPACT #2)


# =============================================================================
# TRADE SELECTION
# =============================================================================

MAX_TRADES_PER_SCAN = 3     # Maximum trades to take per scan
                            # Live mode: top 3 trades in email
                            # Backtest: top 3 trades per simulation date
                            # 1 = most selective
                            # 3 = balanced
                            # 5-10 = more opportunities


# =============================================================================
# TECHNICAL FILTER PARAMETERS
# =============================================================================

# Trend strength (ADX)
ADX_THRESHOLD = 25          # Minimum ADX for valid trend (HIGH IMPACT #5 - stricter)
                            # 20 = weak trend OK
                            # 22 = medium trend (balanced)
                            # 24 = good trend (Option 3)
                            # 25 = strong trend required
                            # 30 = very strong trend

# Momentum (RSI)
RSI_MIN = 50                # Minimum RSI value (OPTION 3: Tighter range)
RSI_MAX = 66                # Maximum RSI value (OPTION 3: Tighter range)
                            # Tight: 50-65 (selective)
                            # Medium: 48-68 (balanced)
                            # Option 3: 50-66 (balanced quality)
                            # Wide: 45-70 (more trades)

# Volume confirmation
VOLUME_MULTIPLIER = 1.5     # Current volume vs 20-day average (HIGH IMPACT #4 - stronger volume)
                            # 1.0 = no filter
                            # 1.3 = 30% above average (relaxed)
                            # 1.4 = 40% above average (Option 3)
                            # 1.5 = 50% above average (moderate)
                            # 2.0 = 100% above average (strict)

# Liquidity requirement
MIN_LIQUIDITY_USD = 30_000_000  # Minimum 20-day avg dollar volume
                                # $20M = smaller stocks OK
                                # $30M = balanced (current)
                                # $50M = large cap only
                                # $100M = mega cap only

MIN_SHARES_PER_DAY = 1_000_000  # Minimum 1M shares/day (LOWER IMPACT #11)

RS_RATING_THRESHOLD = 80  # Minimum relative strength percentile (55-day vs SPY) - HIGH IMPACT #1

SECTOR_RS_ENABLED = True     # Enable sector relative strength filter
SECTOR_RS_LOOKBACK_DAYS = 20 # Sector vs SPY lookback period (trading days)

# Accumulation/Distribution Filter
ACCUM_DIST_ENABLED = True         # Enable institutional accumulation detection
ACCUM_DIST_PERIOD = 20            # Lookback period for A/D analysis (trading days)
ACCUM_DIST_MIN_RATING = "B-"      # Minimum IBD-style rating (E, D, D+, C, B-, B, B+, A-, A, A+)
ACCUM_DIST_BOOST_MULTIPLIER = 1.2 # Score boost for strong accumulation (A/A+ ratings)

EARNINGS_BUFFER_DAYS = 5  # Skip trades within N days of earnings - HIGH IMPACT #3
MAX_GAP_UP_PCT = 5.0      # Skip breakouts with >5% gap up - LOWER IMPACT #10

CONSOLIDATION_MIN_DAYS = 21  # Minimum 3 weeks (21 days) for consolidation - MEDIUM IMPACT #8

# Price action (distance from EMA20)
PRICE_ABOVE_EMA20_MIN = 0.01    # Min 1% above EMA20
PRICE_ABOVE_EMA20_MAX = 0.05    # Max 5% above EMA20
                                # Prevents buying at resistance


# =============================================================================
# BACKTEST-SPECIFIC SETTINGS
# =============================================================================

BACKTEST_START_DATE = "2022-01-01"  # Historical backtest start date
SCAN_FREQUENCY = "B"                # Backtest scan frequency (default)
                                    # "B" = daily
                                    # "W-MON" = weekly Monday
                                    # "W-FRI" = weekly Friday
                                    # Note: Can be overridden via --scan-frequency flag


# =============================================================================
# NOTES & GUIDELINES
# =============================================================================

"""
TUNING FOR HIGHER WIN RATE (fewer trades):
-------------------------------------------
✓ Increase ADX_THRESHOLD to 25+
✓ Tighten RSI to 50-65
✓ Increase VOLUME_MULTIPLIER to 1.5+
✓ Increase MIN_LIQUIDITY_USD to $50M+
✓ Reduce MAX_TRADES_PER_SCAN to 1-2
✓ Use RISK_REWARD_RATIO of 2:1

Expected: 40-45% win rate, lower total profit


TUNING FOR HIGHER PROFIT (more trades):
----------------------------------------
✓ Decrease ADX_THRESHOLD to 20
✓ Widen RSI to 45-70
✓ Decrease VOLUME_MULTIPLIER to 1.2
✓ Decrease MIN_LIQUIDITY_USD to $20M
✓ Increase MAX_TRADES_PER_SCAN to 5-10
✓ Use RISK_REWARD_RATIO of 3:1

Expected: 30-35% win rate, higher total profit


CURRENT SETTINGS (Balanced):
-----------------------------
ADX: 22, RSI: 48-68, Volume: 1.3x, Liquidity: $30M
Max Trades: 3, R/R: 3:1
Expected: ~35-40% win rate, balanced profit


RISK/REWARD IMPACT:
-------------------
2:1 → Higher win rate (~40%), smaller wins, steady growth
3:1 → Medium win rate (~30%), bigger wins, good balance
4:1 → Lower win rate (~25%), large wins, high volatility
"""
