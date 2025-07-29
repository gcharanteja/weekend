from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from app.config import settings
from app.models.database import Base
from app.core.angel_client import AngelOneClient
import structlog

logger = structlog.get_logger()

security = HTTPBearer()

async def get_db():
    """Dependency to get database session"""
    from app.main import async_session
    async with async_session() as session:
        yield session

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to validate JWT token and get current user"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_angel_client():
    """Dependency to get Angel One client"""
    client = AngelOneClient()
    if not client.auth_token:
        if not await client.authenticate():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to authenticate with Angel One"
            )
    return client