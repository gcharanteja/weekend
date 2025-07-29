# app/core/order_manager.py
import asyncio
from typing import Dict, Any, List, Optional
from uuid import uuid4
import structlog
from app.core.angel_client import AngelOneClient
from app.core.risk_manager import RiskManager
from app.models.schemas import OrderCreate, OrderResponse, OrderStatusEnum
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

class OrderManager:
    def __init__(self, angel_client: AngelOneClient, risk_manager: RiskManager):
        self.angel_client = angel_client
        self.risk_manager = risk_manager
        self.pending_orders: Dict[str, Dict[str, Any]] = {}
        self.order_callbacks = {}
        
    async def place_order(self, order: OrderCreate, db: AsyncSession) -> Dict[str, Any]:
        """Place order with risk validation"""
        try:
            # Get current market price
            current_price = await self.angel_client.get_ltp(order.symbol, order.exchange)
            if not current_price:
                return {
                    'success': False,
                    'message': 'Unable to get current market price'
                }
            
            # Validate order through risk manager
            risk_result = await self.risk_manager.validate_order(order, current_price)
            
            if not risk_result['approved']:
                return {
                    'success': False,
                    'message': f'Order rejected by risk manager: {risk_result["reason"]}'
                }
            
            # Adjust quantity if needed
            if 'adjusted_quantity' in risk_result:
                order.quantity = risk_result['adjusted_quantity']
            
            # Create order in database
            db_order = await self._create_db_order(order, db)
            
            # Place order through Angel One API
            order_data = {
                'symbol': order.symbol,
                'exchange': order.exchange,
                'quantity': order.quantity,
                'price': order.price,
                'order_type': order.order_type.value,
                'transaction_type': order.transaction_type.value
            }
            
            api_result = await self.angel_client.place_order(order_data)
            
            if api_result.get('status'):
                # Update order with API response
                order_id = api_result['data']['orderid']
                db_order.order_id = order_id
                db_order.status = OrderStatusEnum.OPEN
                
                # Track pending order
                self.pending_orders[order_id] = {
                    'db_id': str(db_order.id),
                    'order': order,
                    'timestamp': asyncio.get_event_loop().time()
                }
                
                # Update risk manager
                self.risk_manager.increment_order_count()
                
                await db.commit()
                
                logger.info(f"Order placed successfully: {order_id}")
                
                return {
                    'success': True,
                    'order_id': order_id,
                    'db_id': str(db_order.id),
                    'message': 'Order placed successfully'
                }
            else:
                # Update order status to rejected
                db_order.status = OrderStatusEnum.REJECTED
                db_order.message = api_result.get('message', 'Order rejected by broker')
                await db.commit()
                
                return {
                    'success': False,
                    'message': api_result.get('message', 'Order rejected by broker')
                }
                
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return {
                'success': False,
                'message': f'Error placing order: {str(e)}'
            }
    
    async def cancel_order(self, order_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Cancel an order"""
        try:
            # Cancel through Angel One API
            result = await self.angel_client.cancel_order(order_id)
            
            if result.get('status'):
                # Update database
                # This would update the order status in database
                logger.info(f"Order cancelled successfully: {order_id}")
                
                return {
                    'success': True,
                    'message': 'Order cancelled successfully'
                }
            else:
                return {
                    'success': False,
                    'message': result.get('message', 'Failed to cancel order')
                }
                
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return {
                'success': False,
                'message': f'Error cancelling order: {str(e)}'
            }
    
    async def _create_db_order(self, order: OrderCreate, db: AsyncSession):
        """Create order record in database"""
        from app.models.database import Order
        
        db_order = Order(
            symbol=order.symbol,
            exchange=order.exchange,
            quantity=order.quantity,
            price=order.price,
            order_type=order.order_type.value,
            transaction_type=order.transaction_type.value,
            strategy_name=order.strategy_name
        )
        
        db.add(db_order)
        await db.flush()
        return db_order
    
    async def update_order_status(self, order_id: str, status: str, filled_qty: int = 0, avg_price: float = 0.0):
        """Update order status from WebSocket feed"""
        try:
            if order_id in self.pending_orders:
                pending_order = self.pending_orders[order_id]
                
                # Update position in risk manager if filled
                if status == "COMPLETE":
                    order = pending_order['order']
                    await self.risk_manager.update_position(
                        order.symbol,
                        filled_qty,
                        order.transaction_type.value
                    )
                    
                    # Remove from pending orders
                    del self.pending_orders[order_id]
                
                # Trigger callbacks if registered
                if order_id in self.order_callbacks:
                    callback = self.order_callbacks[order_id]
                    await callback(order_id, status, filled_qty, avg_price)
                
                logger.info(f"Order {order_id} status updated to {status}")
                
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}")
    
    def add_order_callback(self, order_id: str, callback):
        """Add callback for order status updates"""
        self.order_callbacks[order_id] = callback
    
    async def get_pending_orders(self) -> List[Dict[str, Any]]:
        """Get all pending orders"""
        return list(self.pending_orders.values())