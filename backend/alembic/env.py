from alembic import context
from sqlalchemy import create_engine, pool
from app.core.config import settings
from app.models.user import Base, User, Membership
from app.models.tenant import Tenant
from app.models.company import Company

from app.models.worker import Worker

target_metadata = Base.metadata

if context.is_offline_mode():
    context.configure(url=settings.DATABASE_URL, target_metadata=target_metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
