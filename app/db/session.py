# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# import os

# DATABASE_URL = os.getenv("DATABASE_URL")

# print("=" * 50)
# print("DATABASE_URL:", repr(os.getenv("DATABASE_URL")))
# print("ENV COUNT:", len(os.environ))
# print("=" * 50)

# if not DATABASE_URL:
#     raise RuntimeError(
#         "DATABASE_URL missing. Check Railway Variables."
#     )

# engine = create_engine(
#     DATABASE_URL,
#     pool_pre_ping=True,
#     pool_recycle=300,
#     pool_size=10,
#     max_overflow=20,
#     echo=False,
# )

# SessionLocal = sessionmaker(
#     autocommit=False,
#     autoflush=False,
#     bind=engine,
# )

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

_engine = None
_SessionLocal = None

def get_engine():
    global _engine
    if _engine is None:
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL missing. Check Railway Variables.")
        _engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=10,
            max_overflow=20,
            echo=False,
        )
    return _engine

def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine()
        )
    return _SessionLocal

# =====================================================
# 👇 COMPATIBILITY LAYER — Keeps old code working
# =====================================================

class _SessionLocalProxy:
    """Allows old code to use SessionLocal() just like before."""
    def __call__(self):
        return get_session_local()()
    
    def __getattr__(self, name):
        # Forward any other attribute access to the real SessionLocal class
        return getattr(get_session_local(), name)

class _EngineProxy:
    """Allows old code to use engine just like before."""
    def __getattr__(self, name):
        return getattr(get_engine(), name)

# These look like the old globals, but they're lazy proxies
SessionLocal = _SessionLocalProxy()
engine = _EngineProxy()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()