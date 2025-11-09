from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from datetime import datetime
import os
import json

# Database URL (use SQLite for development, PostgreSQL for production)
# For SQLite with async support, we need aiosqlite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./minerva_library.db")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for declarative models (SQLAlchemy 2.0 style)
class Base(DeclarativeBase):
    pass

# Search history table
class SearchHistory(Base):
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String(500), nullable=False)
    filters = Column(Text, nullable=True)  # JSON stored as text
    results_count = Column(Integer, default=0)
    search_time = Column(Float, default=0.0)  # seconds
    databases_searched = Column(Text, nullable=True)  # JSON stored as text
    created_at = Column(DateTime, default=datetime.utcnow)
    user_ip = Column(String(50), nullable=True)  # optional: track user IP

# For backward compatibility, create a reference to the table
search_history = SearchHistory.__table__

# Database connection management
async def connect_db():
    """Connect to database"""
    # Test connection
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database connected")

async def disconnect_db():
    """Disconnect from database"""
    await engine.dispose()
    print("❌ Database disconnected")

def create_tables():
    """Create all tables - called on startup"""
    # Tables are created in connect_db() using async engine
    print("✅ Database tables will be created on connection")

