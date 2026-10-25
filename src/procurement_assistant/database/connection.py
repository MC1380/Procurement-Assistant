
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker , DeclarativeBase


# Find the root directory of the project.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Store the SQLite database in the data directory.
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATA_DIR / "procurement.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

# Create the database engine.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Base class for all models.
class Base(DeclarativeBase):
    pass


# Create a factory for database sessions.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)
