from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.models.schemas import PositionResponse
from app.core.angel_client import AngelOneClient
from app.dependencies import get_db, get_current_user, get_angel_client
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/", response_model=List[PositionResponse])
async def get_portfolio(
    db: AsyncSession = Depends(get_db),
    user: str = Depends(get_current_user),
    angel_client: AngelOneClient = Depends(get_angel_client)
):
    """Get current portfolio positions"""
    try:
        positions = await angel_client.get_positions()
        result = []
        
        for pos in positions:
            db_position = await db.get(Position, pos['symbol'])
            if db_position:
                result.append(PositionResponse.from_orm(db_position))
            else:
                result.append(PositionResponse(
                    id=uuid4(),
                    symbol=pos['symbol'],
                    exchange=pos['exchange'],
                    quantity=pos['quantity'],
                    average_price=float(pos['avg_price']),
                    current_price=float(pos.get('ltp', 0)),
                    pnl=float(pos.get('pnl', 0)),
                    unrealized_pnl=float(pos.get('unrealized_pnl', 0)),
                    updated_at=datetime.utcnow()
                ))
        
        return result
    except Exception as e:
        logger.error(f"Error getting portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))