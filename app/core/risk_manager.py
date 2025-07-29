# app/core/risk_manager.py
from typing import Dict, Any, Optional
import structlog
from app.config import settings
from app.models.schemas import OrderCreate, TransactionTypeEnum

logger = structlog.get_logger()

class RiskManager:
    def __init__(self):
        self.max_position_size = settings.max_position_size
        self.max_daily_loss = settings.max_daily_loss
        self.risk_percentage = settings.risk_percentage
        self.daily_pnl = 0.0
        self.positions = {}
        self.order_count = 0
        self.max_orders_per_day = 100
        
    async def validate_order(self, order: OrderCreate, current_price: float) -> Dict[str, Any]:
        """Validate order against risk parameters"""
        try:
            # Check daily loss limit
            if self.daily_pnl <= -self.max_daily_loss:
                return {
                    'approved': False,
                    'reason': f'Daily loss limit exceeded: {self.daily_pnl}'
                }
            
            # Check position size limit
            order_value = order.quantity * current_price
            if order_value > self.max_position_size:
                return {
                    'approved': False,
                    'reason': f'Order value {order_value} exceeds max position size {self.max_position_size}'
                }
            
            # Check order count limit
            if self.order_count >= self.max_orders_per_day:
                return {
                    'approved': False,
                    'reason': f'Daily order limit exceeded: {self.order_count}'
                }
            
            # Check existing position risk
            current_position = self.positions.get(order.symbol, 0)
            if order.transaction_type == TransactionTypeEnum.BUY:
                new_position_value = (current_position + order.quantity) * current_price
            else:
                new_position_value = (current_position - order.quantity) * current_price
            
            if abs(new_position_value) > self.max_position_size:
                return {
                    'approved': False,
                    'reason': f'New position value would exceed limit'
                }
            
            # Calculate risk-adjusted quantity
            risk_adjusted_quantity = await self._calculate_risk_quantity(order, current_price)
            
            return {
                'approved': True,
                'adjusted_quantity': risk_adjusted_quantity,
                'reason': 'Order approved'
            }
            
        except Exception as e:
            logger.error(f"Risk validation error: {str(e)}")
            return {
                'approved': False,
                'reason': f'Risk validation error: {str(e)}'
            }
    
    async def _calculate_risk_quantity(self, order: OrderCreate, current_price: float) -> int:
        """Calculate risk-adjusted order quantity"""
        try:
            # Calculate maximum risk amount
            account_value = 1000000  # This should come from actual account value
            max_risk_amount = account_value * (self.risk_percentage / 100)
            
            # Calculate stop loss distance (assume 2% for market orders)
            stop_loss_distance = current_price * 0.02
            
            # Calculate maximum quantity based on risk
            max_quantity = int(max_risk_amount / stop_loss_distance)
            
            # Use minimum of requested quantity and risk-based quantity
            return min(order.quantity, max_quantity)
            
        except Exception as e:
            logger.error(f"Error calculating risk quantity: {str(e)}")
            return order.quantity
    
    async def update_position(self, symbol: str, quantity: int, transaction_type: str):
        """Update position after order execution"""
        try:
            current_position = self.positions.get(symbol, 0)
            
            if transaction_type == "BUY":
                self.positions[symbol] = current_position + quantity
            else:
                self.positions[symbol] = current_position - quantity
            
            logger.info(f"Position updated: {symbol} = {self.positions[symbol]}")
            
        except Exception as e:
            logger.error(f"Error updating position: {str(e)}")
    
    async def update_daily_pnl(self, pnl_change: float):
        """Update daily P&L"""
        self.daily_pnl += pnl_change
        logger.info(f"Daily P&L updated: {self.daily_pnl}")
    
    def increment_order_count(self):
        """Increment daily order count"""
        self.order_count += 1
    
    def reset_daily_counters(self):
        """Reset daily counters (call at market open)"""
        self.daily_pnl = 0.0
        self.order_count = 0
        logger.info("Daily risk counters reset")