from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 50)
print("DATABASE_URL:", repr(os.getenv("DATABASE_URL")))
print("ENV COUNT:", len(os.environ))
print("=" * 50)

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL missing. Check Railway Variables."
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
