from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from app.strategies.base_strategy import BaseStrategy
from app.models.schemas import OrderCreate, TransactionTypeEnum, OrderTypeEnum
import structlog

logger = structlog.get_logger()

class ScalpingStrategy(BaseStrategy):
    def __init__(self, parameters: Dict[str, Any]):
        super().__init__("SCALPING", parameters)
        self.timeframe = parameters.get('timeframe', '1min')
        self.profit_target = parameters.get('profit_target', 0.005)  # 0.5%
        self.stop_loss = parameters.get('stop_loss', 0.002)  # 0.2%
        self.symbol = parameters.get('symbol', 'SBIN-EQ')
    
    async def generate_signal(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate scalping signal based on price movements"""
        try:
            if not self.is_active:
                return None
            
            historical_data = await self._get_historical_data()
            if len(historical_data) < 20:  # Need enough data for analysis
                return None
            
            indicators = await self.calculate_indicators(historical_data)
            current_price = market_data.get('ltp', 0)
            
            # Simple momentum-based scalping strategy
            momentum = indicators.get('momentum', 0)
            if momentum > 0 and indicators['price_change'] > 0:
                return {
                    'action': 'BUY',
                    'symbol': self.symbol,
                    'price': current_price,
                    'quantity': self.parameters.get('quantity', 1),
                    'reason': f'Positive momentum detected: {momentum:.2f}',
                    'stop_loss': current_price * (1 - self.stop_loss),
                    'profit_target': current_price * (1 + self.profit_target)
                }
            elif momentum < 0 and indicators['price_change'] < 0:
                return {
                    'action': 'SELL',
                    'symbol': self.symbol,
                    'price': current_price,
                    'quantity': self.parameters.get('quantity', 1),
                    'reason': f'Negative momentum detected: {momentum:.2f}',
                    'stop_loss': current_price * (1 + self.stop_loss),
                    'profit_target': current_price * (1 - self.profit_target)
                }
            
            return None
        except Exception as e:
            logger.error(f"Error generating scalping signal: {str(e)}")
            return None
    
    async def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate scalping indicators"""
        data['returns'] = data['close'].pct_change()
        momentum = data['returns'].rolling(window=5).mean().iloc[-1]
        price_change = data['close'].iloc[-1] - data['close'].iloc[-2]
        
        return {
            'momentum': momentum * 100,
            'price_change': price_change
        }
    
    async def _get_historical_data(self) -> pd.DataFrame:
        """Get historical data for calculations"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='min')
        prices = np.random.randn(100).cumsum() + 100
        
        return pd.DataFrame({
            'timestamp': dates,
            'close': prices,
            'open': prices * 0.99,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'volume': np.random.randint(1000, 10000, 100)
        })