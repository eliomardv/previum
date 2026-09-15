"""Create tenants, companies, users and memberships."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False))
    op.create_table("users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("companies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False))
    op.create_index("ix_companies_tenant_id", "companies", ["tenant_id"])
    op.create_table("memberships",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), primary_key=True),
        sa.Column("is_active", sa.Boolean(), nullable=False))


def downgrade():
    op.drop_table("memberships")
    op.drop_index("ix_companies_tenant_id", table_name="companies")
    op.drop_table("companies")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("tenants")
