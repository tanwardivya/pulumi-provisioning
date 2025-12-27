"""Database models."""
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import settings

Base = declarative_base()


class Item(Base):
    """Sample database model."""
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# Database connection
def get_db_engine():
    """Create database engine."""
    if not all([settings.db_host, settings.db_name, settings.db_user, settings.db_password]):
        return None
    
    database_url = (
        f"postgresql://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )
    
    return create_engine(database_url, pool_pre_ping=True)


def get_db_session():
    """Get database session."""
    engine = get_db_engine()
    if not engine:
        return None
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def init_db():
    """Initialize database tables."""
    engine = get_db_engine()
    if engine:
        Base.metadata.create_all(bind=engine)

