from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.models.schemas import OrderCreate, OrderResponse
from app.core.order_manager import OrderManager
from app.core.angel_client import AngelOneClient  # Add this import
from app.core.risk_manager import RiskManager
from app.dependencies import get_db, get_current_user, get_angel_client
import structlog
from sqlalchemy.future import select  # Add for database queries

logger = structlog.get_logger()
router = APIRouter()

@router.post("/", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    db: AsyncSession = Depends(get_db),
    user: str = Depends(get_current_user),
    angel_client: AngelOneClient = Depends(get_angel_client)
):
    """Create a new order"""
    order_manager = OrderManager(angel_client, RiskManager())
    result = await order_manager.place_order(order, db)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    # Query database for order details
    from app.models.database import Order
    db_order = await db.get(Order, result['db_id'])
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse.from_orm(db_order)

@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    db: AsyncSession = Depends(get_db),
    user: str = Depends(get_current_user),
    angel_client: AngelOneClient = Depends(get_angel_client)
):
    """Get all orders"""
    order_manager = OrderManager(angel_client, RiskManager())
    orders = await order_manager.get_pending_orders()
    return [OrderResponse(**order['order'].dict()) for order in orders]

@router.delete("/{order_id}")
async def cancel_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    user: str = Depends(get_current_user),
    angel_client: AngelOneClient = Depends(get_angel_client)
):
    """Cancel an order"""
    order_manager = OrderManager(angel_client, RiskManager())
    result = await order_manager.cancel_order(order_id, db)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return {"message": "Order cancelled successfully"}