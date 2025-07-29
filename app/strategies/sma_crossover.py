from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from app.strategies.base_strategy import BaseStrategy
from app.models.schemas import OrderCreate, TransactionTypeEnum, OrderTypeEnum
import structlog

logger = structlog.get_logger()

class SMAStrategy(BaseStrategy):
    def __init__(self, parameters: Dict[str, Any]):
        super().__init__("SMA_CROSSOVER", parameters)
        self.short_period = parameters.get('short_period', 20)
        self.long_period = parameters.get('long_period', 50)
        self.symbol = parameters.get('symbol', 'SBIN-EQ')
    
    async def generate_signal(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate signal based on SMA crossover"""
        try:
            if not self.is_active:
                return None
            
            historical_data = await self._get_historical_data()
            if len(historical_data) < self.long_period:
                return None
            
            indicators = await self.calculate_indicators(historical_data)
            
            current_price = market_data.get('ltp', 0)
            sma_short = indicators.get('sma_short', 0)
            sma_long = indicators.get('sma_long', 0)
            prev_sma_short = indicators.get('prev_sma_short', 0)
            prev_sma_long = indicators.get('prev_sma_long', 0)
            
            if sma_short > sma_long and prev_sma_short <= prev_sma_long:
                return {
                    'action': 'BUY',
                    'symbol': self.symbol,
                    'price': current_price,
                    'quantity': self.parameters.get('quantity', 1),
                    'reason': f'SMA bullish crossover: {sma_short:.2f} > {sma_long:.2f}'
                }
            
            elif sma_short < sma_long and prev_sma_short >= prev_sma_long:
                return {
                    'action': 'SELL',
                    'symbol': self.symbol,
                    'price': current_price,
                    'quantity': self.parameters.get('quantity', 1),
                    'reason': f'SMA bearish crossover: {sma_short:.2f} < {sma_long:.2f}'
                }
            
            return None
        except Exception as e:
            logger.error(f"Error generating SMA signal: {str(e)}")
            return None
    
    async def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate SMA indicators"""
        data['sma_short'] = data['close'].rolling(window=self.short_period).mean()
        data['sma_long'] = data['close'].rolling(window=self.long_period).mean()
        
        return {
            'sma_short': data['sma_short'].iloc[-1],
            'sma_long': data['sma_long'].iloc[-1],
            'prev_sma_short': data['sma_short'].iloc[-2],
            'prev_sma_long': data['sma_long'].iloc[-2]
        }
    
    async def _get_historical_data(self) -> pd.DataFrame:
        """Get historical data for calculations"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        prices = np.random.randn(100).cumsum() + 100
        
        return pd.DataFrame({
            'timestamp': dates,
            'close': prices,
            'open': prices * 0.99,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'volume': np.random.randint(1000, 10000, 100)
        })