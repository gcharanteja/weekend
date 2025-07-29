from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.models.schemas import StrategyCreate, StrategyResponse
from app.core.strategy_engine import StrategyEngine, SMAStrategy, RSIStrategy
from app.dependencies import get_db, get_current_user, get_angel_client
import structlog
from app.core.angel_client import AngelOneClient

logger = structlog.get_logger()
router = APIRouter()

@router.post("/", response_model=StrategyResponse)
async def create_strategy(
    strategy: StrategyCreate,
    db: AsyncSession = Depends(get_db),
    user: str = Depends(get_current_user),
    angel_client: AngelOneClient = Depends(get_angel_client)
):
    """Create a new trading strategy"""
    try:
        strategy_engine = StrategyEngine(angel_client)
        
        if strategy.name == "SMA_CROSSOVER":
            new_strategy = SMAStrategy(strategy.parameters)
        elif strategy.name == "RSI_MEAN_REVERSION":
            new_strategy = RSIStrategy(strategy.parameters)
        else:
            raise HTTPException(status_code=400, detail="Unsupported strategy type")
        
        strategy_engine.add_strategy(new_strategy)
        
        # Save to database
        from app.models.database import Strategy
        db_strategy = Strategy(
            name=strategy.name,
            description=strategy.description,
            parameters=json.dumps(strategy.parameters),
            is_active=False
        )
        db.add(db_strategy)
        await db.commit()
        
        return StrategyResponse.from_orm(db_strategy)
    except Exception as e:
        logger.error(f"Error creating strategy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[StrategyResponse])
async def get_strategies(
    db: AsyncSession = Depends(get_db),
    user: str = Depends(get_current_user)
):
    """Get all strategies"""
    from app.models.database import Strategy
    strategies = await db.execute(select(Strategy))
    return [StrategyResponse.from_orm(s) for s in strategies.scalars().all()]

@router.post("/{strategy_name}/activate")
async def activate_strategy(
    strategy_name: str,
    db: AsyncSession = Depends(get_db),
    user: str = Depends(get_current_user),
    angel_client: AngelOneClient = Depends(get_angel_client)
):
    """Activate a strategy"""
    strategy_engine = StrategyEngine(angel_client)
    strategy_engine.activate_strategy(strategy_name)
    return {"message": f"Strategy {strategy_name} activated"}

@router.post("/{strategy_name}/deactivate")
async def deactivate_strategy(
    strategy_name: str,
    db: AsyncSession = Depends(get_db),
    user: str = Depends(get_current_user),
    angel_client: AngelOneClient = Depends(get_angel_client)
):
    """Deactivate a strategy"""
    strategy_engine = StrategyEngine(angel_client)
    strategy_engine.deactivate_strategy(strategy_name)
    return {"message": f"Strategy {strategy_name} deactivated"}