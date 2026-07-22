"""
PostgreSQL Database Connection and ORM Models
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, Numeric, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, date
from typing import AsyncGenerator

from app.config import get_settings

settings = get_settings()

# Convert sync URL to async using psycopg
async_url = settings.postgres_url.replace("postgresql://", "postgresql+psycopg://")

# Create async engine
engine = create_async_engine(async_url, echo=settings.debug)

# Async session factory
async_session_factory = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

Base = declarative_base()


class Subscriber(Base):
    """Subscriber ORM model"""
    __tablename__ = "subscribers"
    
    id = Column(Integer, primary_key=True, index=True)
    ric_number = Column(String(20), unique=True, nullable=False, index=True)
    pin_code = Column(String(10))
    full_name = Column(String(255), nullable=False)
    phone_model = Column(String(100))
    phone_type = Column(String(50))  # smartphone, feature_phone, tablet
    service_type = Column(String(50))  # prepaid, postpaid, corporate
    contract_duration_months = Column(Integer, default=12)
    contract_start_date = Column(Date, default=date.today)
    monthly_cost = Column(Numeric(10, 2), default=0.00)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    payments = relationship("Payment", back_populates="subscriber", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "ric_number": self.ric_number,
            "pin_code": self.pin_code,
            "full_name": self.full_name,
            "phone_model": self.phone_model,
            "phone_type": self.phone_type,
            "service_type": self.service_type,
            "contract_duration_months": self.contract_duration_months,
            "contract_start_date": str(self.contract_start_date) if self.contract_start_date else None,
            "monthly_cost": float(self.monthly_cost) if self.monthly_cost else 0,
            "is_active": self.is_active,
            "created_at": str(self.created_at) if self.created_at else None,
            "updated_at": str(self.updated_at) if self.updated_at else None,
        }


class Payment(Base):
    """Payment ORM model"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    subscriber_id = Column(Integer, ForeignKey("subscribers.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    paid_date = Column(Date, nullable=True)
    is_delayed = Column(Boolean, default=False)
    delay_days = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    subscriber = relationship("Subscriber", back_populates="payments")
    
    def to_dict(self):
        return {
            "id": self.id,
            "subscriber_id": self.subscriber_id,
            "amount": float(self.amount) if self.amount else 0,
            "due_date": str(self.due_date) if self.due_date else None,
            "paid_date": str(self.paid_date) if self.paid_date else None,
            "is_delayed": self.is_delayed,
            "delay_days": self.delay_days,
            "created_at": str(self.created_at) if self.created_at else None,
        }


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_postgres():
    """Initialize PostgreSQL connection"""
    try:
        async with engine.begin() as conn:
            # Test connection
            await conn.execute(text("SELECT 1"))
        print("✅ PostgreSQL connected successfully")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        raise


async def close_postgres():
    """Close PostgreSQL connection"""
    await engine.dispose()
    print("🔌 PostgreSQL connection closed")
