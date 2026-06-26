
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base

# Actual DATABASE_URL from .env file
DATABASE_URL = "postgresql+asyncpg://sribuu:sribuu_dev_2026@localhost:5432/sribuu"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) # Explicitly not nullable
    amount = Column(Float, nullable=False)
    due_date = Column(Date, nullable=False)
    recurrence: Optional[str] = Column(String, nullable=True)  # e.g., "monthly", "yearly", "none"
    user_id = Column(Integer, ForeignKey("users.id")) # Assuming a 'users' table exists
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Function to create tables (run once)
def create_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables()
