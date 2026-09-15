"""Exercise migration upgrade, metadata consistency and rollback in isolation."""
import os
from pathlib import Path
import subprocess
import sys

from sqlalchemy import create_engine, inspect, text


def test_migration_roundtrip(tmp_path):
    url = f"sqlite:///{tmp_path / 'migration.db'}"
    env = {**os.environ, "DATABASE_URL": url,
           "JWT_SECRET_KEY": "migration-test-secret-with-at-least-32-bytes"}
    backend = Path(__file__).resolve().parents[1]

    def alembic(*args):
        subprocess.run([sys.executable, "-m", "alembic", *args],
                       cwd=backend, env=env, check=True, capture_output=True, text=True)

    alembic("upgrade", "0001")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO tenants (id, name, is_active) VALUES ('kept', 'Kept', true)"))
        connection.execute(text("INSERT INTO companies (id, tenant_id, name, is_active) VALUES ('kept', 'kept', 'Kept', true)"))
    alembic("upgrade", "head")
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT name FROM companies WHERE id = 'kept'")) == 'Kept'
    alembic("downgrade", "0001")
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT name FROM companies WHERE id = 'kept'")) == 'Kept'
    alembic("upgrade", "head")
    inspector = inspect(engine)
    assert set(inspector.get_table_names()) == {
        "alembic_version", "tenants", "companies", "users", "memberships", "workers"}
    assert inspector.get_foreign_keys("companies")[0]["referred_table"] == "tenants"
    assert {fk["referred_table"] for fk in inspector.get_foreign_keys("memberships")} == {"users", "tenants"}
    assert {fk["referred_table"] for fk in inspector.get_foreign_keys("workers")} == {"companies", "tenants"}
    alembic("check")
    alembic("upgrade", "head")
    alembic("downgrade", "base")
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}
    alembic("upgrade", "head")
    alembic("check")
    engine.dispose()
