from prometheus_client import Counter, Gauge, Histogram
import structlog

logger = structlog.get_logger()

# Define Prometheus metrics
order_count = Counter('trading_bot_orders_total', 'Total number of orders placed', ['strategy'])
order_execution_time = Histogram('trading_bot_order_execution_seconds', 'Order execution time')
position_value = Gauge('trading_bot_position_value', 'Current position value', ['symbol'])
pnl_gauge = Gauge('trading_bot_pnl', 'Current P&L', ['symbol'])
api_errors = Counter('trading_bot_api_errors_total', 'Total API errors', ['endpoint'])

def track_order(strategy: str):
    """Track order placement"""
    order_count.labels(strategy=strategy).inc()

def track_execution_time(seconds: float):
    """Track order execution time"""
    order_execution_time.observe(seconds)

def update_position(symbol: str, value: float):
    """Update position value"""
    position_value.labels(symbol=symbol).set(value)

def update_pnl(symbol: str, pnl: float):
    """Update P&L"""
    pnl_gauge.labels(symbol=symbol).set(pnl)

def track_api_error(endpoint: str):
    """Track API errors"""
    api_errors.labels(endpoint=endpoint).inc()