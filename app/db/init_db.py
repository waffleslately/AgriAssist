from sqlalchemy import text
from app.db.session import engine
from app.db.base import Base
# Import all models to register with Base.metadata
import app.models  # noqa

async def init_db():
    async with engine.begin() as conn:
        # Create PostGIS extension if available
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        except Exception:
            # Fallback for environments where PostGIS extension is pre-installed or in test mode
            pass
        await conn.run_sync(Base.metadata.create_all)
