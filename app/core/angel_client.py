# app/core/angel_client.py
from SmartApi import SmartConnect
import pyotp
import redis
import json
import asyncio
from typing import Optional, Dict, Any, List
import structlog
from app.config import settings

logger = structlog.get_logger()

class AngelOneClient:
    def __init__(self):
        self.api_key = settings.api_key
        self.username = settings.username
        self.password = settings.password
        self.totp_key = settings.totp_key
        self.smart_api = None
        self.auth_token = None
        self.feed_token = None
        self.redis_client = redis.from_url(settings.redis_url)
        
    async def authenticate(self) -> bool:
        """Authenticate with Angel One API"""
        try:
            self.smart_api = SmartConnect(api_key=self.api_key)
            
            # Generate TOTP
            totp = pyotp.TOTP(self.totp_key)
            totp_code = totp.now()
            
            # Login
            data = self.smart_api.generateSession(
                self.username, 
                self.password, 
                totp_code
            )
            
            if data['status']:
                self.auth_token = data['data']['jwtToken']
                self.feed_token = data['data']['feedToken']
                
                # Cache tokens in Redis
                await self._cache_tokens()
                
                logger.info("Angel One authentication successful")
                return True
            else:
                logger.error(f"Authentication failed: {data['message']}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    async def _cache_tokens(self):
        """Cache authentication tokens in Redis"""
        token_data = {
            'auth_token': self.auth_token,
            'feed_token': self.feed_token
        }
        self.redis_client.setex(
            'angel_tokens', 
            3600,  # 1 hour expiry
            json.dumps(token_data)
        )
    
    async def get_cached_tokens(self) -> bool:
        """Get cached tokens from Redis"""
        try:
            cached_data = self.redis_client.get('angel_tokens')
            if cached_data:
                token_data = json.loads(cached_data)
                self.auth_token = token_data['auth_token']
                self.feed_token = token_data['feed_token']
                return True
            return False
        except Exception as e:
            logger.error(f"Error getting cached tokens: {str(e)}")
            return False
    
    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place order through Angel One API"""
        try:
            if not self.smart_api:
                await self.authenticate()
            
            result = self.smart_api.placeOrder(
                variety="NORMAL",
                tradingsymbol=order_data['symbol'],
                symboltoken=await self._get_symbol_token(order_data['symbol']),
                transactiontype=order_data['transaction_type'],
                exchange=order_data['exchange'],
                ordertype=order_data['order_type'],
                producttype="INTRADAY",
                duration="DAY",
                price=str(order_data.get('price', '0')),
                squareoff="0",
                stoploss="0",
                quantity=str(order_data['quantity'])
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Order placement error: {str(e)}")
            return {'status': False, 'message': str(e)}
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions"""
        try:
            if not self.smart_api:
                await self.authenticate()
                
            result = self.smart_api.position()
            return result.get('data', [])
            
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return []
    
    async def get_orders(self) -> List[Dict[str, Any]]:
        """Get order history"""
        try:
            if not self.smart_api:
                await self.authenticate()
                
            result = self.smart_api.orderBook()
            return result.get('data', [])
            
        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            return []
    
    async def get_ltp(self, symbol: str, exchange: str) -> Optional[float]:
        """Get Last Traded Price"""
        try:
            if not self.smart_api:
                await self.authenticate()
                
            token = await self._get_symbol_token(symbol)
            result = self.smart_api.ltpData(exchange, symbol, token)
            
            if result['status']:
                return float(result['data']['ltp'])
            return None
            
        except Exception as e:
            logger.error(f"Error getting LTP: {str(e)}")
            return None
    
    async def _get_symbol_token(self, symbol: str) -> str:
        """Get symbol token from cache or API"""
        # This is a simplified implementation
        # In production, you'd maintain a symbol master cache
        return "3045"  # Example token for SBIN
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        try:
            if not self.smart_api:
                await self.authenticate()
                
            result = self.smart_api.cancelOrder(
                variety="NORMAL",
                orderid=order_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Order cancellation error: {str(e)}")
            return {'status': False, 'message': str(e)}