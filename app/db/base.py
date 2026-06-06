from sqlalchemy.orm import declarative_base

Base = declarative_base()

import app.models  # noqa: E402, F401 — registers all ORM models with Base.metadata
