from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import structlog

logger = structlog.get_logger()

class BaseStrategy(ABC):
    def __init__(self, name: str, parameters: Dict[str, Any]):
        self.name = name
        self.parameters = parameters
        self.is_active = False
        self.positions = {}
        self.orders = []
        
    @abstractmethod
    async def generate_signal(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate trading signal based on market data"""
        pass
    
    @abstractmethod
    async def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical indicators"""
        pass
    
    def activate(self):
        """Activate strategy"""
        self.is_active = True
        logger.info(f"Strategy {self.name} activated")
    
    def deactivate(self):
        """Deactivate strategy"""
        self.is_active = False
        logger.info(f"Strategy {self.name} deactivated")