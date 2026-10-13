import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from secvarta.database.models import Base

# Project root: directory containing pyproject.toml.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Load the project's .env file.
load_dotenv(PROJECT_ROOT / ".env")

# Read configuration from environment variables.
DATABASE_URL = os.getenv(
    "SECVARTA_DATABASE_URL",
    "sqlite:///data/secvarta.db",
)

DB_ECHO = os.getenv(
    "SECVARTA_DB_ECHO",
    "false",
).strip().lower() in {"1", "true", "yes", "on"}


# Resolve relative SQLite paths against the project root.
url = make_url(DATABASE_URL)

if (
    url.get_backend_name() == "sqlite"
    and url.database
    and url.database != ":memory:"
    and not url.database.startswith("file:")
):
    database_path = Path(url.database)

    if not database_path.is_absolute():
        database_path = PROJECT_ROOT / database_path

    database_path.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = url.set(database=str(database_path)).render_as_string(
        hide_password=False
    )


# Create the engine and session factory.
engine = create_engine(
    DATABASE_URL,
    echo=DB_ECHO,
)

if engine.dialect.name == "sqlite":

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def init_db():
    """Create any missing database tables."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Return a new SQLAlchemy session."""
    return SessionLocal()
