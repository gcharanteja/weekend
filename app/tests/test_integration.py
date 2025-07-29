import pytest
from app.core.angel_client import AngelOneClient
from app.core.strategy_engine import StrategyEngine

@pytest.mark.asyncio
async def test_angel_client_auth():
    client = AngelOneClient()
    # Mock authentication for testing
    # In production, this would require valid credentials
    assert client.auth_token is None

@pytest.mark.asyncio
async def test_strategy_engine():
    client = AngelOneClient()
    engine = StrategyEngine(client)
    assert engine.is_running is False
    engine.start()
    assert engine.is_running is True