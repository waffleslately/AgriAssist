"""Add pest_reference and pest_diagnoses tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. pest_reference table
    op.create_table(
        "pest_reference",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("pest_name", sa.String(length=100), nullable=False),
        sa.Column("scientific_name", sa.String(length=100), nullable=False),
        sa.Column("affected_crops", sa.JSON(), nullable=False),
        sa.Column("symptoms", sa.Text(), nullable=False),
        sa.Column("organic_countermeasures", sa.JSON(), nullable=False),
        sa.Column("chemical_countermeasures", sa.JSON(), nullable=False),
        sa.Column("ideal_spray_timing", sa.Text(), nullable=False),
        sa.Column("regulatory_note", sa.Text(), nullable=True),
        sa.Column("source_note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pest_reference_pest_name", "pest_reference", ["pest_name"], unique=True)

    # 2. pest_diagnoses history table
    op.create_table(
        "pest_diagnoses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("plot_id", sa.UUID(), nullable=True),
        sa.Column("photo_url", sa.String(length=255), nullable=False),
        sa.Column("detected_class", sa.String(length=100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("is_uncertain", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("alternate_matches", sa.JSON(), nullable=False),
        sa.Column("countermeasures", sa.JSON(), nullable=False),
        sa.Column("drone_prescription", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pest_diagnoses_plot_id", "pest_diagnoses", ["plot_id"])


def downgrade() -> None:
    op.drop_index("ix_pest_diagnoses_plot_id", table_name="pest_diagnoses")
    op.drop_table("pest_diagnoses")
    op.drop_index("ix_pest_reference_pest_name", table_name="pest_reference")
    op.drop_table("pest_reference")
