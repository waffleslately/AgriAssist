"""Add user_soil_reports table

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_soil_reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("farmer_id", sa.String(length=100), nullable=True),
        sa.Column("plot_id", sa.UUID(), nullable=True),
        sa.Column("raw_file_url", sa.String(length=255), nullable=True),
        sa.Column("source_format", sa.String(length=50), nullable=False, server_default="pdf"),
        sa.Column("extracted_data", sa.JSON(), nullable=False),
        sa.Column("reviewed_and_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_soil_reports_farmer_id", "user_soil_reports", ["farmer_id"])
    op.create_index("ix_user_soil_reports_plot_id", "user_soil_reports", ["plot_id"])


def downgrade() -> None:
    op.drop_index("ix_user_soil_reports_plot_id", table_name="user_soil_reports")
    op.drop_index("ix_user_soil_reports_farmer_id", table_name="user_soil_reports")
    op.drop_table("user_soil_reports")
