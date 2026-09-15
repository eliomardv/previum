"""Add workers without changing existing companies or memberships."""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("workers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("registration", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False))
    op.create_index("ix_workers_tenant_company", "workers", ["tenant_id", "company_id"])


def downgrade():
    op.drop_index("ix_workers_tenant_company", table_name="workers")
    op.drop_table("workers")
