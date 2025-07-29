from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from app.strategies.base_strategy import BaseStrategy
from app.models.schemas import OrderCreate, TransactionTypeEnum, OrderTypeEnum
import structlog

logger = structlog.get_logger()

class RSIStrategy(BaseStrategy):
    def __init__(self, parameters: Dict[str, Any]):
        super().__init__("RSI_MEAN_REVERSION", parameters)
        self.rsi_period = parameters.get('rsi_period', 14)
        self.oversold_level = parameters.get('oversold_level', 30)
        self.overbought_level = parameters.get('overbought_level', 70)
        self.symbol = parameters.get('symbol', 'SBIN-EQ')
    
    async def generate_signal(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate signal based on RSI levels"""
        try:
            if not self.is_active:
                return None
            
            historical_data = await self._get_historical_data()
            if len(historical_data) < self.rsi_period + 1:
                return None
            
            indicators = await self.calculate_indicators(historical_data)
            current_price = market_data.get('ltp', 0)
            rsi = indicators.get('rsi', 50)
            
            if rsi < self.oversold_level:
                return {
                    'action': 'BUY',
                    'symbol': self.symbol,
                    'price': current_price,
                    'quantity': self.parameters.get('quantity', 1),
                    'reason': f'RSI oversold: {rsi:.2f} < {self.oversold_level}'
                }
            
            elif rsi > self.overbought_level:
                return {
                    'action': 'SELL',
                    'symbol': self.symbol,
                    'price': current_price,
                    'quantity': self.parameters.get('quantity', 1),
                    'reason': f'RSI overbought: {rsi:.2f} > {self.overbought_level}'
                }
            
            return None
        except Exception as e:
            logger.error(f"Error generating RSI signal: {str(e)}")
            return None
    
    async def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate RSI indicator"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return {
            'rsi': rsi.iloc[-1]
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