# Trading Bot

A professional-grade trading bot with Angel One SmartAPI integration, real-time data processing, and comprehensive risk management.

## Features

- Real-time market data processing via WebSocket
- Multiple trading strategies (SMA Crossover, RSI Mean Reversion, Scalping)
- Risk management with position sizing and stop-loss
- Monitoring with Prometheus and Grafana
- REST API and WebSocket endpoints
- Dockerized deployment

## Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Angel One SmartAPI account
- PostgreSQL and Redis instances

### Installation

1. Clone the repository:

   ```bash
   git clone <repository>
   cd trading_bot
   ```

2. Create a `.env` file with the required environment variables:

   ```bash
   API_KEY=your_api_key
   USERNAME=your_username
   PASSWORD=your_password
   TOTP_KEY=your_totp_key
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/trading_bot
   REDIS_URL=redis://localhost:6379/0
   SECRET_KEY=your_secret_key
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run database migrations:

   ```bash
   alembic upgrade head
   ```

5. Start the application:
   ```bash
   docker-compose up -d
   ```

## API Endpoints

- `GET /`: Root endpoint
- `GET /health`: Health check
- `POST /api/auth/login`: Authenticate and get JWT token
- `POST /api/orders`: Create new order
- `GET /api/orders`: Get all orders
- `DELETE /api/orders/{order_id}`: Cancel order
- `GET /api/portfolio`: Get portfolio positions
- `POST /api/strategies`: Create new strategy
- `GET /api/strategies`: Get all strategies
- `POST /api/strategies/{strategy_name}/activate`: Activate strategy
- `POST /api/strategies/{strategy_name}/deactivate`: Deactivate strategy
- `WS /api/ws/market-data`: WebSocket for real-time market data

## Monitoring

- Prometheus: Available at `http://localhost:9090`
- Grafana: Available at `http://localhost:3000` (default credentials: admin/admin)

## Development

Run the development server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run tests:

```bash
pytest
```

## Security

- Uses JWT for API authentication
- HTTPS enforced
- Input validation and sanitization
- Encrypted storage for sensitive data

## Notes

- The `_get_historical_data` methods in strategies are implemented with sample data. Replace with actual API/database calls.
- The `_get_symbol_token` method in `angel_client.py` is simplified. Implement proper symbol token mapping.
- Add more comprehensive test cases in the `tests/` directory.
- Configure Prometheus and Grafana for production monitoring.
