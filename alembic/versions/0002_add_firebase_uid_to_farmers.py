"""Add firebase_uid to farmers table

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "farmers",
        sa.Column("firebase_uid", sa.String(128), nullable=True),
    )
    # Unique index — one Firebase account maps to exactly one farmer row
    op.create_index("ix_farmers_firebase_uid", "farmers", ["firebase_uid"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_farmers_firebase_uid", table_name="farmers")
    op.drop_column("farmers", "firebase_uid")
