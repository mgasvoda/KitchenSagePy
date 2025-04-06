# DB connection and session management

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Database URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{Path(__file__).parent.parent.absolute()}/kitchensage.db"

# Create the engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for declarative models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    """
    Dependency function to get a database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize the database
def init_db():
    """
    Initialize the database by creating all tables.
    """
    from . import models  # Import models here to avoid circular imports
    Base.metadata.create_all(bind=engine)
