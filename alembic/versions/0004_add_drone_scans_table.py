"""Add drone_scans table

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "drone_scans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("plot_id", sa.UUID(), nullable=False),
        sa.Column("scan_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["plot_id"], ["plots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_drone_scans_plot_id", "drone_scans", ["plot_id"])


def downgrade() -> None:
    op.drop_table("drone_scans")
