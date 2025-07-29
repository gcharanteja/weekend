#app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog
from app.config import settings

logger = structlog.get_logger()
router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class LoginRequest(BaseModel):
    username: str
    password: str

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: LoginRequest):
    """Authenticate user and generate JWT token"""
    # This is a simplified authentication check
    # In production, verify against a user database
    if form_data.username != settings.username or not pwd_context.verify(form_data.password, pwd_context.hash(settings.password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds())
    }