"""0001_initial_postgis_schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-09-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Enable PostGIS
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # 2. Farmers Table
    op.create_table(
        "farmers",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("phone_number", sa.String(length=15), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("preferred_language", sa.String(length=10), server_default="hi", nullable=False),
        sa.Column("state", sa.String(length=50), nullable=False),
        sa.Column("district", sa.String(length=50), nullable=False),
        sa.Column("sub_district", sa.String(length=50), nullable=True),
        sa.Column("village", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_farmers_phone_number", "farmers", ["phone_number"], unique=True)

    # 3. Plots Table
    op.create_table(
        "plots",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("farmer_id", sa.UUID(), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("boundary", geoalchemy2.Geometry(geometry_type="POLYGON", srid=4326), nullable=False),
        sa.Column("centroid", geoalchemy2.Geometry(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("area_acres", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("soil_texture", sa.String(length=50), nullable=True),
        sa.Column("irrigation_source", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.execute("CREATE INDEX idx_plots_boundary ON plots USING GIST (boundary);")
    op.execute("CREATE INDEX idx_plots_centroid ON plots USING GIST (centroid);")

    # 4. Crop Cycles Table
    op.create_table(
        "crop_cycles",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("plot_id", sa.UUID(), sa.ForeignKey("plots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("crop_name", sa.String(length=50), nullable=False),
        sa.Column("variety", sa.String(length=100), nullable=True),
        sa.Column("season", sa.String(length=20), nullable=False),
        sa.Column("sowing_date", sa.Date(), nullable=False),
        sa.Column("expected_harvest_date", sa.Date(), nullable=True),
        sa.Column("target_yield_quintal_per_acre", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_crop_cycles_plot_active", "crop_cycles", ["plot_id", "is_active"])

    # 5. Soil Health Samples Table
    op.create_table(
        "soil_health_samples",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("location", geoalchemy2.Geometry(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("state", sa.String(length=50), nullable=True),
        sa.Column("district", sa.String(length=50), nullable=True),
        sa.Column("organic_carbon_pct", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("available_nitrogen_kg_ha", sa.Numeric(precision=6, scale=1), nullable=True),
        sa.Column("available_phosphorus_kg_ha", sa.Numeric(precision=6, scale=1), nullable=True),
        sa.Column("available_potassium_kg_ha", sa.Numeric(precision=6, scale=1), nullable=True),
        sa.Column("ph", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("electrical_conductivity", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("zinc_ppm", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("iron_ppm", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("sample_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.execute("CREATE INDEX idx_soil_health_location ON soil_health_samples USING GIST (location);")

    # 6. Satellite Observations Table
    op.create_table(
        "satellite_observations",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("plot_id", sa.UUID(), sa.ForeignKey("plots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("satellite_source", sa.String(length=30), nullable=False),
        sa.Column("acquisition_date", sa.Date(), nullable=False),
        sa.Column("mean_ndvi", sa.Numeric(precision=5, scale=3), nullable=False),
        sa.Column("p10_ndvi", sa.Numeric(precision=5, scale=3), nullable=True),
        sa.Column("p90_ndvi", sa.Numeric(precision=5, scale=3), nullable=True),
        sa.Column("soil_moisture_proxy", sa.Numeric(precision=5, scale=3), nullable=True),
        sa.Column("cloud_cover_percentage", sa.Numeric(precision=5, scale=2), server_default="0.0", nullable=False),
        sa.Column("raw_metrics", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_sat_obs_plot_date", "satellite_observations", ["plot_id", "acquisition_date"])

    # 7. Advisories Table
    op.create_table(
        "advisories",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("crop_cycle_id", sa.UUID(), sa.ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trigger_source", sa.String(length=50), nullable=False),
        sa.Column("crop_stage", sa.String(length=50), nullable=True),
        sa.Column("fertilizer_plan", sa.JSON(), nullable=False),
        sa.Column("irrigation_advice", sa.Text(), nullable=True),
        sa.Column("weather_summary", sa.JSON(), nullable=True),
        sa.Column("localized_message", sa.JSON(), nullable=False),
        sa.Column("is_sent", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_advisories_crop_cycle", "advisories", ["crop_cycle_id", "created_at"])

def downgrade() -> None:
    op.drop_table("advisories")
    op.drop_table("satellite_observations")
    op.drop_table("soil_health_samples")
    op.drop_table("crop_cycles")
    op.drop_table("plots")
    op.drop_table("farmers")
