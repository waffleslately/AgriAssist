"""Add livestock and livestock_locations tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-12
"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "livestock",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("farmer_id", sa.UUID(), nullable=False),
        sa.Column("plot_id", sa.UUID(), nullable=True),
        sa.Column("tag_id", sa.String(length=50), nullable=False),
        sa.Column("animal_type", sa.String(length=50), nullable=False, server_default="cattle"),
        sa.Column("collar_battery", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plot_id"], ["plots.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_livestock_tag_id", "livestock", ["tag_id"], unique=True)

    op.create_table(
        "livestock_locations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("livestock_id", sa.UUID(), nullable=False),
        sa.Column("geom", Geometry(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["livestock_id"], ["livestock.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_livestock_locations_livestock_id", "livestock_locations", ["livestock_id"])
    op.create_index("ix_livestock_locations_timestamp", "livestock_locations", ["timestamp"])


def downgrade() -> None:
    op.drop_table("livestock_locations")
    op.drop_table("livestock")
