# app/core/websocket_handler.py
import asyncio
import websockets
import json
import struct
from typing import Dict, Any, Callable, Optional
import structlog
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from app.core.angel_client import AngelOneClient
from app.config import settings

logger = structlog.get_logger()

class WebSocketHandler:
    def __init__(self, angel_client: AngelOneClient):
        self.angel_client = angel_client
        self.websocket = None
        self.callbacks: Dict[str, Callable] = {}
        self.is_connected = False
        self.subscribed_symbols = set()
        
    # In app/core/websocket_handler.py
    async def connect(self):
        try:
            if not self.angel_client.auth_token:
                await self.angel_client.authenticate()
                logger.info("Authenticated with Angel One, auth_token: %s", self.angel_client.auth_token)
            self.websocket = SmartWebSocketV2(
                self.angel_client.auth_token,
                self.angel_client.api_key,
                self.angel_client.username,
                self.angel_client.feed_token
            )
            self.websocket.on_open = self._on_open
            self.websocket.on_data = self._on_data
            self.websocket.on_error = self._on_error
            self.websocket.on_close = self._on_close
            self.websocket.connect()
            self.is_connected = True
            logger.info("WebSocket connected successfully, subscribing to SBIN-EQ")
            await self.subscribe(["SBIN-EQ"], "NSE")
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            self.is_connected = False
    
    async def disconnect(self):
        """Disconnect WebSocket"""
        if self.websocket:
            self.websocket.close()
            self.is_connected = False
            logger.info("WebSocket disconnected")
    
    def _on_open(self, ws):
        """WebSocket open callback"""
        logger.info("WebSocket opened")
        
    def _on_data(self, ws, message):
        """WebSocket data callback"""
        try:
            # Process binary data from Angel One
            data = self._parse_binary_data(message)
            
            # Trigger callbacks
            for callback in self.callbacks.values():
                asyncio.create_task(callback(data))
                
        except Exception as e:
            logger.error(f"Error processing WebSocket data: {str(e)}")
    
    def _on_error(self, ws, error):
        """WebSocket error callback"""
        logger.error(f"WebSocket error: {str(error)}")
        self.is_connected = False
    
    def _on_close(self, ws):
        """WebSocket close callback"""
        logger.info("WebSocket closed")
        self.is_connected = False
    
    def _parse_binary_data(self, binary_data: bytes) -> Dict[str, Any]:
        """Parse binary data from Angel One WebSocket"""
        try:
            # Angel One sends data in binary format
            # This is a simplified parser - actual implementation would be more complex
            
            # Header: 2 bytes for data length
            data_length = struct.unpack('>H', binary_data[:2])[0]
            
            # Extract actual data
            data_bytes = binary_data[2:2+data_length]
            
            # Parse based on Angel One's binary protocol
            # This is a placeholder implementation
            parsed_data = {
                'symbol': 'SBIN-EQ',
                'ltp': 545.50,
                'volume': 1000,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing binary data: {str(e)}")
            return {}
    
    async def subscribe(self, symbols: list, exchange: str = "NSE"):
        """Subscribe to symbols"""
        try:
            if not self.is_connected:
                await self.connect()
            
            # Format subscription data for Angel One
            subscription_data = {
                "action": 1,  # Subscribe
                "params": {
                    "mode": 1,  # LTP mode
                    "tokenList": [
                        {
                            "exchangeType": 1 if exchange == "NSE" else 2,
                            "tokens": symbols
                        }
                    ]
                }
            }
            
            # Send subscription
            self.websocket.send(json.dumps(subscription_data))
            
            self.subscribed_symbols.update(symbols)
            logger.info(f"Subscribed to symbols: {symbols}")
            
        except Exception as e:
            logger.error(f"Subscription error: {str(e)}")
    
    async def unsubscribe(self, symbols: list, exchange: str = "NSE"):
        """Unsubscribe from symbols"""
        try:
            subscription_data = {
                "action": 0,  # Unsubscribe
                "params": {
                    "mode": 1,
                    "tokenList": [
                        {
                            "exchangeType": 1 if exchange == "NSE" else 2,
                            "tokens": symbols
                        }
                    ]
                }
            }
            
            self.websocket.send(json.dumps(subscription_data))
            
            for symbol in symbols:
                self.subscribed_symbols.discard(symbol)
                
            logger.info(f"Unsubscribed from symbols: {symbols}")
            
        except Exception as e:
            logger.error(f"Unsubscription error: {str(e)}")
    
    def add_callback(self, name: str, callback: Callable):
        """Add data callback"""
        self.callbacks[name] = callback
    
    def remove_callback(self, name: str):
        """Remove data callback"""
        if name in self.callbacks:
            del self.callbacks[name]