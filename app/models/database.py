# trading_bot/app/models/database.py
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Integer, DateTime, Enum, JSON, Boolean
from datetime import datetime
from uuid import uuid4
from app.models.enums import OrderStatus, OrderType, TransactionType

class Base(AsyncAttrs, DeclarativeBase):
    pass

class Order(Base):
    __tablename__ = "orders"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    exchange: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=True)
    order_type: Mapped[OrderType] = mapped_column(Enum(OrderType), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING)
    strategy_name: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    filled_quantity: Mapped[int] = mapped_column(Integer, default=0)
    average_price: Mapped[float] = mapped_column(Float, nullable=True)
    message: Mapped[str] = mapped_column(String, nullable=True)

class Position(Base):
    __tablename__ = "positions"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    exchange: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    average_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float] = mapped_column(Float, nullable=True)
    pnl: Mapped[float] = mapped_column(Float, default=0.0)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Strategy(Base):
    __tablename__ = "strategies"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MarketData(Base):
    __tablename__ = "market_data"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    exchange: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    open_price: Mapped[float] = mapped_column(Float, nullable=True)
    high_price: Mapped[float] = mapped_column(Float, nullable=True)
    low_price: Mapped[float] = mapped_column(Float, nullable=True)
    close_price: Mapped[float] = mapped_column(Float, nullable=True)
    volume: Mapped[int] = mapped_column(Integer, nullable=True)
    ltp: Mapped[float] = mapped_column(Float, nullable=True)  # Last Traded Price