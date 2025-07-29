# app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import redis
import asyncio
import structlog
from contextlib import asynccontextmanager
from typing import List

from app.config import settings
from app.core.angel_client import AngelOneClient
from app.core.websocket_handler import WebSocketHandler
from app.core.strategy_engine import StrategyEngine, SMAStrategy, RSIStrategy
from app.core.risk_manager import RiskManager
from app.core.order_manager import OrderManager
from app.api import auth, orders, portfolio, strategies, websocket
from app.models.database import Base
# Add to app/main.py imports
from app.routes.trade_routes import router as trade_router
# Add to router includes


# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Database setup
engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Global instances
angel_client = AngelOneClient()
risk_manager = RiskManager()
order_manager = OrderManager(angel_client, risk_manager)
websocket_handler = WebSocketHandler(angel_client)
strategy_engine = StrategyEngine(angel_client)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting trading bot application...")
    async with engine.begin() as conn:
        logger.info("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
    logger.info("Attempting Angel One authentication...")
    if await angel_client.authenticate():
        logger.info("Angel One authentication successful")
    else:
        logger.error("Angel One authentication failed")
        raise RuntimeError("Failed to authenticate with Angel One")
    logger.info("Connecting WebSocket...")
    await websocket_handler.connect()
    logger.info("WebSocket connected")
    websocket_handler.add_callback("market_data", strategy_engine.process_market_data)
    sma_strategy = SMAStrategy({
        'short_period': 20,
        'long_period': 50,
        'symbol': 'SBIN-EQ',
        'quantity': 1
    })
    rsi_strategy = RSIStrategy({
        'rsi_period': 14,
        'oversold_level': 30,
        'overbought_level': 70,
        'symbol': 'SBIN-EQ',
        'quantity': 1
    })
    strategy_engine.add_strategy(sma_strategy)
    strategy_engine.add_strategy(rsi_strategy)
    strategy_engine.start()
    logger.info("Trading bot started successfully")
    yield
    logger.info("Shutting down trading bot...")
    strategy_engine.stop()
    await websocket_handler.disconnect()
    await engine.dispose()
    logger.info("Trading bot shutdown complete")

app = FastAPI(
    title="Trading Bot API",
    description="Professional Trading Bot with Angel One SmartAPI Integration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
async def get_db():
    async with async_session() as session:
        yield session

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])
app.include_router(websocket.router, prefix="/api/ws", tags=["WebSocket"])
app.include_router(trade_router, prefix="/api/trades", tags=["Trades"])

@app.get("/")
async def root():
    return {
        "message": "Trading Bot API",
        "version": "1.0.0",
        "status": "running",
        "websocket_connected": websocket_handler.is_connected,
        "strategies_active": len([s for s in strategy_engine.strategies.values() if s.is_active])
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "angel_one_connected": angel_client.auth_token is not None,
        "websocket_connected": websocket_handler.is_connected,
        "database_connected": True,  # Add actual database health check
        "strategy_engine_running": strategy_engine.is_running
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )