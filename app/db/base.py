from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models so SQLAlchemy's mapper registry is populated before
# Alembic autogenerate or engine.create_all() is called.
# This must happen after Base is defined to avoid circular imports.
import app.models  # noqa: E402, F401
