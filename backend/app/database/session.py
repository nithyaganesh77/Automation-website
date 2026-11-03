from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.core.config import settings

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.core.config import settings

# Handle SQLite vs PostgreSQL production configuration
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if is_sqlite:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

else:
    # Production PostgreSQL with connection pooling and timeout guards
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        isolation_level="READ COMMITTED"
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency that yields a database session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health() -> dict:
    """Performs a live ping and dialect inspection on the configured database."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            dialect = engine.dialect.name
            return {
                "status": "healthy" if result == 1 else "unhealthy",
                "dialect": dialect,
                "is_production": dialect == "postgresql",
                "pool_size": getattr(engine.pool, "size", lambda: None)() if hasattr(engine.pool, "size") else None
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "dialect": engine.dialect.name
        }

