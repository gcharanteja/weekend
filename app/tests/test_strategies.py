import pytest
import pandas as pd
import numpy as np
from app.strategies.sma_crossover import SMAStrategy
from app.strategies.rsi_strategy import RSIStrategy
from app.strategies.scalping_strategy import ScalpingStrategy

@pytest.mark.asyncio
async def test_sma_crossover():
    strategy = SMAStrategy({
        'short_period': 5,
        'long_period': 10,
        'symbol': 'TEST-EQ',
        'quantity': 1
    })
    
    market_data = {'ltp': 100.0}
    signal = await strategy.generate_signal(market_data)
    assert signal is None  # Not enough data initially

@pytest.mark.asyncio
async def test_rsi_strategy():
    strategy = RSIStrategy({
        'rsi_period': 14,
        'oversold_level': 30,
        'overbought_level': 70,
        'symbol': 'TEST-EQ',
        'quantity': 1
    })
    
    market_data = {'ltp': 100.0}
    signal = await strategy.generate_signal(market_data)
    assert signal is None  # Not enough data initially

@pytest.mark.asyncio
async def test_scalping_strategy():
    strategy = ScalpingStrategy({
        'timeframe': '1min',
        'profit_target': 0.005,
        'stop_loss': 0.002,
        'symbol': 'TEST-EQ',
        'quantity': 1
    })
    
    market_data = {'ltp': 100.0}
    signal = await strategy.generate_signal(market_data)
    assert signal is None  # Not enough data initially