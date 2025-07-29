# trading_bot/migrations/env.py
from sqlalchemy import create_engine, pool
from alembic import context
from app.models.database import Base
from app.config import settings

# Alembic Config object
config = context.config

# Use synchronous URL for migrations
sync_db_url = settings.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
config.set_main_option('sqlalchemy.url', sync_db_url)

# Connectable for database
connectable = create_engine(sync_db_url, poolclass=pool.NullPool)

# Set up migration context
with connectable.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata
    )
    
    with context.begin_transaction():
        context.run_migrations()