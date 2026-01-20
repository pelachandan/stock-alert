"""
Accumulation/Distribution Detection Module
===========================================
Detects institutional buying (accumulation) vs selling (distribution) using 6 methods:

1. Chaikin A/D Line - Where price closes within daily range × volume
2. On-Balance Volume (OBV) - Cumulative volume on up vs down days
3. Chaikin Money Flow (CMF) - Bounded -1 to +1 money flow over N periods
4. IBD-Style Rating - A+ to E institutional activity rating
5. Up/Down Volume Analysis - Classic volume pattern analysis
6. Volume Price Trend (VPT) - Volume weighted by price change %

Author: Stock Alert System
Date: 2026-01-20
"""

import pandas as pd
import numpy as np


class AccumulationDistribution:
    """
    Comprehensive accumulation/distribution analyzer using multiple methods.
    """

    def __init__(self, period=20):
        """
        Initialize analyzer.

        Args:
            period: Lookback period for calculations (default: 20 days)
        """
        self.period = period

    # ============================================================================
    # METHOD 1: Chaikin A/D Line
    # ============================================================================
    def chaikin_ad_line(self, df):
        """
        Calculate Chaikin Accumulation/Distribution Line.

        Formula:
            Money Flow Multiplier = [(Close - Low) - (High - Close)] / (High - Low)
            Money Flow Volume = MFM × Volume
            A/D Line = Cumulative sum of MFV

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Series with A/D line values
        """
        high = df["High"]
        low = df["Low"]
        close = df["Close"]
        volume = df["Volume"]

        # Avoid division by zero
        range_hl = high - low
        range_hl = range_hl.replace(0, np.nan)

        # Money Flow Multiplier
        mfm = ((close - low) - (high - close)) / range_hl

        # Money Flow Volume
        mfv = mfm * volume

        # A/D Line (cumulative)
        ad_line = mfv.cumsum()

        return ad_line

    # ============================================================================
    # METHOD 2: On-Balance Volume (OBV)
    # ============================================================================
    def on_balance_volume(self, df):
        """
        Calculate On-Balance Volume (OBV) by Joe Granville.

        Logic:
            - If close > prev_close: OBV += volume
            - If close < prev_close: OBV -= volume
            - If close == prev_close: OBV unchanged

        Args:
            df: DataFrame with Close and Volume

        Returns:
            Series with OBV values
        """
        close = df["Close"]
        volume = df["Volume"]

        # Price direction
        price_change = close.diff()

        # OBV calculation
        obv = (np.sign(price_change) * volume).fillna(0).cumsum()

        return obv

    # ============================================================================
    # METHOD 3: Chaikin Money Flow (CMF)
    # ============================================================================
    def chaikin_money_flow(self, df, period=None):
        """
        Calculate Chaikin Money Flow (CMF).

        Formula:
            CMF = Sum(Money Flow Volume, N) / Sum(Volume, N)
            Range: -1 to +1

        Args:
            df: DataFrame with OHLCV data
            period: Lookback period (default: self.period)

        Returns:
            Series with CMF values
        """
        if period is None:
            period = self.period

        high = df["High"]
        low = df["Low"]
        close = df["Close"]
        volume = df["Volume"]

        # Money Flow Multiplier
        range_hl = high - low
        range_hl = range_hl.replace(0, np.nan)
        mfm = ((close - low) - (high - close)) / range_hl

        # Money Flow Volume
        mfv = mfm * volume

        # CMF = Sum of MFV / Sum of Volume
        cmf = mfv.rolling(period).sum() / volume.rolling(period).sum()

        return cmf

    # ============================================================================
    # METHOD 4: IBD-Style Accumulation/Distribution Rating
    # ============================================================================
    def ibd_style_rating(self, df, period=None):
        """
        Calculate IBD-style Accumulation/Distribution rating (A+ to E).

        Logic:
            Accumulation = Up days on HIGH volume + Down days on LOW volume
            Distribution = Down days on HIGH volume + Up days on LOW volume

        Rating Scale:
            A+ (80+)  = Heavy institutional buying
            A  (60+)  = Strong accumulation
            B  (10+)  = Moderate accumulation
            C  (±10)  = Neutral
            D  (-60)  = Strong distribution
            E  (-90)  = Heavy institutional selling

        Args:
            df: DataFrame with Close and Volume
            period: Lookback period (default: self.period)

        Returns:
            dict with score, rating, acc_days, dist_days
        """
        if period is None:
            period = self.period

        # Calculate only for the lookback period
        df_period = df.tail(period + 1).copy()

        close = df_period["Close"]
        volume = df_period["Volume"]

        # Price direction
        price_change = close.diff()
        up_days = price_change > 0
        down_days = price_change < 0

        # Volume relative to average
        avg_volume = volume.rolling(period).mean()
        high_volume = volume > avg_volume
        low_volume = volume <= avg_volume

        # Accumulation patterns
        acc_up_high = (up_days & high_volume).sum()  # Up days on high volume
        acc_down_low = (down_days & low_volume).sum()  # Down days on low volume
        total_accumulation = acc_up_high + acc_down_low

        # Distribution patterns
        dist_down_high = (down_days & high_volume).sum()  # Down days on high volume
        dist_up_low = (up_days & low_volume).sum()  # Up days on low volume
        total_distribution = dist_down_high + dist_up_low

        # Calculate score (-100 to +100)
        total_days = len(df_period) - 1  # Exclude first day (no price change)
        if total_days == 0:
            return {"score": 0, "rating": "C", "acc_days": 0, "dist_days": 0}

        acc_pct = (total_accumulation / total_days) * 100
        dist_pct = (total_distribution / total_days) * 100
        score = acc_pct - dist_pct

        # Assign letter grade
        if score >= 80:
            rating = "A+"
        elif score >= 60:
            rating = "A"
        elif score >= 40:
            rating = "A-"
        elif score >= 20:
            rating = "B+"
        elif score >= 10:
            rating = "B"
        elif score >= 0:
            rating = "B-"
        elif score >= -10:
            rating = "C"
        elif score >= -40:
            rating = "D+"
        elif score >= -60:
            rating = "D"
        else:
            rating = "E"

        return {
            "score": round(score, 1),
            "rating": rating,
            "acc_days": total_accumulation,
            "dist_days": total_distribution,
        }

    # ============================================================================
    # METHOD 5: Up/Down Volume Analysis
    # ============================================================================
    def up_down_volume_analysis(self, df, period=None):
        """
        Analyze up volume vs down volume.

        Args:
            df: DataFrame with Close and Volume
            period: Lookback period (default: self.period)

        Returns:
            dict with up_volume, down_volume, ratio
        """
        if period is None:
            period = self.period

        df_period = df.tail(period + 1).copy()

        close = df_period["Close"]
        volume = df_period["Volume"]

        # Price direction
        price_change = close.diff()

        # Volume on up days vs down days
        up_volume = volume[price_change > 0].sum()
        down_volume = volume[price_change < 0].sum()

        # Calculate ratio
        if down_volume == 0:
            ratio = np.inf if up_volume > 0 else 1.0
        else:
            ratio = up_volume / down_volume

        return {
            "up_volume": up_volume,
            "down_volume": down_volume,
            "ratio": round(ratio, 2),
        }

    # ============================================================================
    # METHOD 6: Volume Price Trend (VPT)
    # ============================================================================
    def volume_price_trend(self, df):
        """
        Calculate Volume Price Trend (VPT).

        Formula:
            VPT = VPT_prev + (Volume × (Close - Close_prev) / Close_prev)

        Args:
            df: DataFrame with Close and Volume

        Returns:
            Series with VPT values
        """
        close = df["Close"]
        volume = df["Volume"]

        # Price change percentage
        price_pct_change = close.pct_change()

        # VPT calculation
        vpt = (volume * price_pct_change).fillna(0).cumsum()

        return vpt

    # ============================================================================
    # COMPOSITE ANALYSIS
    # ============================================================================
    def detect_divergence(self, df, period=None):
        """
        Detect bullish/bearish divergence between price and volume indicators.

        Args:
            df: DataFrame with OHLCV data
            period: Lookback period (default: self.period)

        Returns:
            dict with divergence_type, strength
        """
        if period is None:
            period = self.period

        df_period = df.tail(period).copy()

        # Price trend
        price_first = df_period["Close"].iloc[0]
        price_last = df_period["Close"].iloc[-1]
        price_trend = "UP" if price_last > price_first else "DOWN"

        # OBV trend
        obv = self.on_balance_volume(df)
        obv_first = obv.iloc[-period]
        obv_last = obv.iloc[-1]
        obv_trend = "UP" if obv_last > obv_first else "DOWN"

        # A/D Line trend
        ad_line = self.chaikin_ad_line(df)
        ad_first = ad_line.iloc[-period]
        ad_last = ad_line.iloc[-1]
        ad_trend = "UP" if ad_last > ad_first else "DOWN"

        # Detect divergence
        if price_trend == "UP" and (obv_trend == "DOWN" or ad_trend == "DOWN"):
            return {"type": "BEARISH_DIVERGENCE", "strength": "STRONG"}
        elif price_trend == "DOWN" and (obv_trend == "UP" or ad_trend == "UP"):
            return {"type": "BULLISH_DIVERGENCE", "strength": "STRONG"}
        else:
            return {"type": "NO_DIVERGENCE", "strength": "NEUTRAL"}

    def full_analysis(self, df, period=None):
        """
        Run all 6 methods and return comprehensive analysis.

        Args:
            df: DataFrame with OHLCV data
            period: Lookback period (default: self.period)

        Returns:
            dict with all indicator values and composite score
        """
        if period is None:
            period = self.period

        # Calculate all indicators
        ad_line = self.chaikin_ad_line(df)
        obv = self.on_balance_volume(df)
        cmf = self.chaikin_money_flow(df, period)
        ibd = self.ibd_style_rating(df, period)
        updown = self.up_down_volume_analysis(df, period)
        vpt = self.volume_price_trend(df)
        divergence = self.detect_divergence(df, period)

        # Get latest values
        latest_ad = ad_line.iloc[-1] if not ad_line.empty else 0
        latest_obv = obv.iloc[-1] if not obv.empty else 0
        latest_cmf = cmf.iloc[-1] if not cmf.empty else 0
        latest_vpt = vpt.iloc[-1] if not vpt.empty else 0

        # Composite score (0-100)
        # Weighted average of normalized indicators
        cmf_score = (latest_cmf + 1) * 50  # CMF is -1 to +1, normalize to 0-100
        ibd_score = (ibd["score"] + 100) / 2  # IBD is -100 to +100, normalize to 0-100
        updown_score = min(updown["ratio"] * 25, 100)  # Ratio > 4 = 100

        composite_score = (cmf_score * 0.3 + ibd_score * 0.5 + updown_score * 0.2)

        return {
            "chaikin_ad": round(latest_ad, 2),
            "obv": round(latest_obv, 2),
            "cmf": round(latest_cmf, 3),
            "ibd_rating": ibd["rating"],
            "ibd_score": ibd["score"],
            "acc_days": ibd["acc_days"],
            "dist_days": ibd["dist_days"],
            "up_volume": updown["up_volume"],
            "down_volume": updown["down_volume"],
            "volume_ratio": updown["ratio"],
            "vpt": round(latest_vpt, 2),
            "divergence_type": divergence["type"],
            "composite_score": round(composite_score, 1),
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def detect_accumulation(df, period=20):
    """
    Quick detection of accumulation/distribution status.

    Args:
        df: DataFrame with OHLCV data
        period: Lookback period (default: 20)

    Returns:
        dict with status, signal, ibd_rating, cmf, composite_score

    Example:
        result = detect_accumulation(df)
        if result['signal'] == 'BUY':
            print("Strong accumulation detected!")
    """
    analyzer = AccumulationDistribution(period=period)
    analysis = analyzer.full_analysis(df, period=period)

    # Determine status based on composite score
    if analysis["composite_score"] >= 70:
        status = "STRONG_ACCUMULATION"
        signal = "BUY"
    elif analysis["composite_score"] >= 55:
        status = "ACCUMULATION"
        signal = "BULLISH"
    elif analysis["composite_score"] >= 45:
        status = "NEUTRAL"
        signal = "HOLD"
    elif analysis["composite_score"] >= 30:
        status = "DISTRIBUTION"
        signal = "BEARISH"
    else:
        status = "STRONG_DISTRIBUTION"
        signal = "AVOID"

    return {
        "status": status,
        "signal": signal,
        "ibd_rating": analysis["ibd_rating"],
        "ibd_score": analysis["ibd_score"],
        "cmf": analysis["cmf"],
        "composite_score": analysis["composite_score"],
        "volume_ratio": analysis["volume_ratio"],
        "acc_days": analysis["acc_days"],
        "dist_days": analysis["dist_days"],
    }


def get_accumulation_rating(df, period=20):
    """
    Get IBD-style letter rating (A+ to E).

    Args:
        df: DataFrame with OHLCV data
        period: Lookback period (default: 20)

    Returns:
        str: Letter rating (A+, A, A-, B+, B, B-, C, D+, D, E)

    Example:
        rating = get_accumulation_rating(df)
        if rating in ['A+', 'A', 'A-']:
            print("Strong institutional buying!")
    """
    analyzer = AccumulationDistribution(period=period)
    ibd = analyzer.ibd_style_rating(df, period=period)
    return ibd["rating"]


def is_under_accumulation(df, period=20, min_rating="B-"):
    """
    Boolean check if stock is under accumulation.

    Args:
        df: DataFrame with OHLCV data
        period: Lookback period (default: 20)
        min_rating: Minimum acceptable rating (default: B-)

    Returns:
        bool: True if stock meets minimum accumulation threshold

    Example:
        if is_under_accumulation(df, min_rating="B"):
            print("Institutions are buying!")
    """
    # Rating hierarchy
    rating_order = ["E", "D", "D+", "C", "B-", "B", "B+", "A-", "A", "A+"]

    current_rating = get_accumulation_rating(df, period)

    # Compare ratings
    try:
        current_index = rating_order.index(current_rating)
        min_index = rating_order.index(min_rating)
        return current_index >= min_index
    except ValueError:
        return False


def is_under_distribution(df, period=20, max_rating="C"):
    """
    Boolean check if stock is under distribution (selling).

    Args:
        df: DataFrame with OHLCV data
        period: Lookback period (default: 20)
        max_rating: Maximum rating to consider distribution (default: C)

    Returns:
        bool: True if stock is under distribution

    Example:
        if is_under_distribution(df):
            print("Institutions are selling - avoid!")
    """
    rating_order = ["E", "D", "D+", "C", "B-", "B", "B+", "A-", "A", "A+"]

    current_rating = get_accumulation_rating(df, period)

    try:
        current_index = rating_order.index(current_rating)
        max_index = rating_order.index(max_rating)
        return current_index <= max_index
    except ValueError:
        return False
