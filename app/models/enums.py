# app/models/enums.py
import enum

class OrderStatus(enum.Enum):
    PENDING = "PENDING"
    OPEN = "OPEN" 
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class OrderType(enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"

class TransactionType(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"