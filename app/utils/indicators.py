import pandas as pd
import numpy as np
from typing import Dict

def calculate_sma(data: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average"""
    return data.rolling(window=period).mean()

def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return data.ewm(span=period, adjust=False).mean()

def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2.0) -> Dict[str, pd.Series]:
    """Calculate Bollinger Bands"""
    sma = calculate_sma(data, period)
    std = data.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return {
        'upper': upper_band,
        'middle': sma,
        'lower': lower_band
    }

def calculate_macd(data: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, pd.Series]:
    """Calculate MACD"""
    ema_fast = calculate_ema(data, fast_period)
    ema_slow = calculate_ema(data, slow_period)
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=signal_period, adjust=False).mean()
    histogram = macd - signal
    return {
        'macd': macd,
        'signal': signal,
        'histogram': histogram
    }