"""
Subscriber Service - Business Logic
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import date, timedelta

from app.database.postgres_db import Subscriber, Payment
from app.database.neo4j_db import Neo4jService
from app.models.schemas import SubscriberCreate, SubscriberUpdate, DelayedPaymentInfo
from app.config import get_settings

settings = get_settings()


class SubscriberService:
    """Service for subscriber operations"""
    
    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Subscriber]:
        """Get all subscribers"""
        result = await db.execute(
            select(Subscriber)
            .offset(skip)
            .limit(limit)
            .order_by(Subscriber.id)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_by_id(db: AsyncSession, subscriber_id: int) -> Optional[Subscriber]:
        """Get subscriber by ID"""
        result = await db.execute(
            select(Subscriber).where(Subscriber.id == subscriber_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_ric(db: AsyncSession, ric_number: str) -> Optional[Subscriber]:
        """Get subscriber by RIC number"""
        result = await db.execute(
            select(Subscriber).where(Subscriber.ric_number == ric_number)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_columns(
        db: AsyncSession, 
        columns: List[str],
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get subscribers with only specified columns"""
        # Build column selection
        column_attrs = []
        for col in columns:
            if hasattr(Subscriber, col):
                column_attrs.append(getattr(Subscriber, col))
        
        if not column_attrs:
            return []
        
        result = await db.execute(
            select(*column_attrs)
            .offset(skip)
            .limit(limit)
            .order_by(Subscriber.id)
        )
        
        rows = result.all()
        return [dict(zip(columns, row)) for row in rows]
    
    @staticmethod
    async def create(db: AsyncSession, data: SubscriberCreate) -> Subscriber:
        """Create a new subscriber"""
        subscriber = Subscriber(
            ric_number=data.ric_number,
            pin_code=data.pin_code,
            full_name=data.full_name,
            phone_model=data.phone_model,
            phone_type=data.phone_type.value if data.phone_type else None,
            service_type=data.service_type.value if data.service_type else None,
            contract_duration_months=data.contract_duration_months,
            contract_start_date=data.contract_start_date or date.today(),
            monthly_cost=data.monthly_cost
        )
        db.add(subscriber)
        await db.flush()
        await db.refresh(subscriber)
        
        # Also create in Neo4j for graph analysis
        try:
            await Neo4jService.create_subscriber_node(
                ric_number=data.ric_number,
                full_name=data.full_name,
                service_plan="Basic"  # Default plan
            )
        except Exception:
            pass  # Neo4j might not be available
        
        return subscriber
    
    @staticmethod
    async def update(db: AsyncSession, subscriber_id: int, data: SubscriberUpdate) -> Optional[Subscriber]:
        """Update subscriber"""
        subscriber = await SubscriberService.get_by_id(db, subscriber_id)
        if not subscriber:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(subscriber, field):
                if hasattr(value, 'value'):  # Enum
                    value = value.value
                setattr(subscriber, field, value)
        
        await db.flush()
        await db.refresh(subscriber)
        return subscriber
    
    @staticmethod
    async def delete(db: AsyncSession, subscriber_id: int) -> bool:
        """Delete subscriber"""
        subscriber = await SubscriberService.get_by_id(db, subscriber_id)
        if not subscriber:
            return False
        
        await db.delete(subscriber)
        return True
    
    @staticmethod
    async def get_with_payments(db: AsyncSession, subscriber_id: int) -> Optional[Subscriber]:
        """Get subscriber with their payments"""
        result = await db.execute(
            select(Subscriber)
            .options(selectinload(Subscriber.payments))
            .where(Subscriber.id == subscriber_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_delayed_payments_subscribers(db: AsyncSession) -> List[DelayedPaymentInfo]:
        """Get list of subscribers with delayed payments and disconnection dates"""
        today = date.today()
        delay_threshold = settings.payment_delay_days_for_disconnection
        
        result = await db.execute(
            select(Subscriber, Payment)
            .join(Payment)
            .where(
                and_(
                    Payment.is_delayed == True,
                    Payment.paid_date.is_(None)
                )
            )
            .order_by(Payment.delay_days.desc())
        )
        
        rows = result.all()
        delayed_list = []
        
        for subscriber, payment in rows:
            # Calculate disconnection date based on delay
            delay_days = (today - payment.due_date).days if payment.due_date else 0
            disconnection_date = payment.due_date + timedelta(days=delay_threshold) if payment.due_date else today
            
            delayed_list.append(DelayedPaymentInfo(
                subscriber_id=subscriber.id,
                ric_number=subscriber.ric_number,
                full_name=subscriber.full_name,
                payment_id=payment.id,
                amount=float(payment.amount),
                due_date=payment.due_date,
                delay_days=delay_days,
                disconnection_date=disconnection_date,
                phone_model=subscriber.phone_model,
                service_type=subscriber.service_type
            ))
        
        return delayed_list
    
    @staticmethod
    async def search(
        db: AsyncSession, 
        query: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Subscriber]:
        """Search subscribers by name or RIC number"""
        search_term = f"%{query}%"
        result = await db.execute(
            select(Subscriber)
            .where(
                or_(
                    Subscriber.full_name.ilike(search_term),
                    Subscriber.ric_number.ilike(search_term)
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    def get_available_columns() -> List[str]:
        """Get list of available columns for selection"""
        return [
            "id", "ric_number", "pin_code", "full_name", "phone_model",
            "phone_type", "service_type", "contract_duration_months",
            "contract_start_date", "monthly_cost", "is_active",
            "created_at", "updated_at"
        ]
