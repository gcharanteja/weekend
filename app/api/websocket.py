from fastapi import APIRouter, WebSocket, Depends
from app.core.websocket_handler import WebSocketHandler
from app.dependencies import get_current_user, get_angel_client
import structlog
from app.core.angel_client import AngelOneClient

logger = structlog.get_logger()
router = APIRouter()

@router.websocket("/market-data")
async def websocket_endpoint(
    websocket: WebSocket,
    user: str = Depends(get_current_user),
    angel_client: AngelOneClient = Depends(get_angel_client)
):
    """WebSocket endpoint for real-time market data"""
    await websocket.accept()
    ws_handler = WebSocketHandler(angel_client)
    
    async def ws_callback(data):
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"WebSocket send error: {str(e)}")
    
    ws_handler.add_callback(f"ws_{user}", ws_callback)
    
    try:
        while True:
            # Keep WebSocket connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_handler.remove_callback(f"ws_{user}")
        logger.info("WebSocket disconnected")