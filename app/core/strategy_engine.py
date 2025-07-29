# app/core/strategy_engine.py
import asyncio
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import structlog
from app.core.angel_client import AngelOneClient
from app.models.schemas import OrderCreate, TransactionTypeEnum, OrderTypeEnum

logger = structlog.get_logger()

class BaseStrategy(ABC):
    def __init__(self, name: str, parameters: Dict[str, Any]):
        self.name = name
        self.parameters = parameters
        self.is_active = False
        self.positions = {}
        self.orders = []
        
    @abstractmethod
    async def generate_signal(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate trading signal based on market data"""
        pass
    
    @abstractmethod
    async def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical indicators"""
        pass
    
    def activate(self):
        """Activate strategy"""
        self.is_active = True
        logger.info(f"Strategy {self.name} activated")
    
    def deactivate(self):
        """Deactivate strategy"""
        self.is_active = False
        logger.info(f"Strategy {self.name} deactivated")

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
            
            # Get historical data for calculation
            historical_data = await self._get_historical_data()
            if len(historical_data) < self.long_period:
                return None
            
            indicators = await self.calculate_indicators(historical_data)
            
            current_price = market_data.get('ltp', 0)
            sma_short = indicators.get('sma_short', 0)
            sma_long = indicators.get('sma_long', 0)
            prev_sma_short = indicators.get('prev_sma_short', 0)
            prev_sma_long = indicators.get('prev_sma_long', 0)
            
            # Check for crossover
            if sma_short > sma_long and prev_sma_short <= prev_sma_long:
                # Bullish crossover - Buy signal
                return {
                    'action': 'BUY',
                    'symbol': self.symbol,
                    'price': current_price,
                    'quantity': self.parameters.get('quantity', 1),
                    'reason': f'SMA bullish crossover: {sma_short:.2f} > {sma_long:.2f}'
                }
            
            elif sma_short < sma_long and prev_sma_short >= prev_sma_long:
                # Bearish crossover - Sell signal
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
        # This would fetch from database or API
        # For demo, returning sample data
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
            
            # RSI oversold - Buy signal
            if rsi < self.oversold_level:
                return {
                    'action': 'BUY',
                    'symbol': self.symbol,
                    'price': current_price,
                    'quantity': self.parameters.get('quantity', 1),
                    'reason': f'RSI oversold: {rsi:.2f} < {self.oversold_level}'
                }
            
            # RSI overbought - Sell signal
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
        # Sample data - replace with actual implementation
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

class StrategyEngine:
    def __init__(self, angel_client: AngelOneClient):
        self.angel_client = angel_client
        self.strategies: Dict[str, BaseStrategy] = {}
        self.is_running = False
        
    def add_strategy(self, strategy: BaseStrategy):
        """Add strategy to engine"""
        self.strategies[strategy.name] = strategy
        logger.info(f"Strategy {strategy.name} added to engine")
    
    def remove_strategy(self, strategy_name: str):
        """Remove strategy from engine"""
        if strategy_name in self.strategies:
            del self.strategies[strategy_name]
            logger.info(f"Strategy {strategy_name} removed from engine")
    
    def activate_strategy(self, strategy_name: str):
        """Activate a strategy"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].activate()
    
    def deactivate_strategy(self, strategy_name: str):
        """Deactivate a strategy"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].deactivate()
    
    async def process_market_data(self, market_data: Dict[str, Any]):
        """Process market data through all active strategies"""
        if not self.is_running:
            return
        
        for strategy in self.strategies.values():
            if strategy.is_active:
                try:
                    signal = await strategy.generate_signal(market_data)
                    if signal:
                        await self._execute_signal(signal, strategy.name)
                except Exception as e:
                    logger.error(f"Error processing strategy {strategy.name}: {str(e)}")
    
    async def _execute_signal(self, signal: Dict[str, Any], strategy_name: str):
        """Execute trading signal"""
        try:
            order_data = OrderCreate(
                symbol=signal['symbol'],
                exchange="NSE",
                quantity=signal['quantity'],
                price=signal.get('price'),
                order_type=OrderTypeEnum.MARKET,
                transaction_type=TransactionTypeEnum.BUY if signal['action'] == 'BUY' else TransactionTypeEnum.SELL,
                strategy_name=strategy_name
            )
            
            # This would normally go through the order management system
            result = await self.angel_client.place_order(order_data.dict())
            
            logger.info(f"Signal executed: {signal['reason']}, Result: {result}")
            
        except Exception as e:
            logger.error(f"Error executing signal: {str(e)}")
    
    def start(self):
        """Start strategy engine"""
        self.is_running = True
        logger.info("Strategy engine started")
    
    def stop(self):
        """Stop strategy engine"""
        self.is_running = False
        for strategy in self.strategies.values():
            strategy.deactivate()
        logger.info("Strategy engine stopped")