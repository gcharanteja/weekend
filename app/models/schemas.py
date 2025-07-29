# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from uuid import UUID

class OrderTypeEnum(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"

class TransactionTypeEnum(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatusEnum(str, Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class OrderCreate(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    exchange: str = Field(..., description="Exchange (NSE/BSE)")
    quantity: int = Field(..., gt=0, description="Order quantity")
    price: Optional[float] = Field(None, description="Order price (for limit orders)")
    order_type: OrderTypeEnum = Field(..., description="Order type")
    transaction_type: TransactionTypeEnum = Field(..., description="Buy or Sell")
    strategy_name: Optional[str] = Field(None, description="Strategy that generated this order")

class OrderResponse(BaseModel):
    id: UUID
    order_id: Optional[str]
    symbol: str
    exchange: str
    quantity: int
    price: Optional[float]
    order_type: OrderTypeEnum
    transaction_type: TransactionTypeEnum
    status: OrderStatusEnum
    strategy_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    filled_quantity: int
    average_price: Optional[float]
    message: Optional[str]

class PositionResponse(BaseModel):
    id: UUID
    symbol: str
    exchange: str
    quantity: int
    average_price: float
    current_price: float
    pnl: float
    unrealized_pnl: float
    updated_at: datetime

class StrategyCreate(BaseModel):
    name: str = Field(..., description="Strategy name")
    description: Optional[str] = Field(None, description="Strategy description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")

class StrategyResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    parameters: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class MarketDataResponse(BaseModel):
    symbol: str
    exchange: str
    timestamp: datetime
    open_price: Optional[float]
    high_price: Optional[float]
    low_price: Optional[float]
    close_price: Optional[float]
    volume: Optional[int]
    ltp: Optional[float]

class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)