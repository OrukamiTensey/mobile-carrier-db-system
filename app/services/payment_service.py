"""
Payment Service - Business Logic
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import date

from app.database.postgres_db import Payment, Subscriber
from app.models.schemas import PaymentCreate, PaymentUpdate


class PaymentService:
    """Service for payment operations"""
    
    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Payment]:
        """Get all payments"""
        result = await db.execute(
            select(Payment)
            .offset(skip)
            .limit(limit)
            .order_by(Payment.due_date.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_by_id(db: AsyncSession, payment_id: int) -> Optional[Payment]:
        """Get payment by ID"""
        result = await db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_subscriber(db: AsyncSession, subscriber_id: int) -> List[Payment]:
        """Get all payments for a subscriber"""
        result = await db.execute(
            select(Payment)
            .where(Payment.subscriber_id == subscriber_id)
            .order_by(Payment.due_date.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_delayed(db: AsyncSession) -> List[Payment]:
        """Get all delayed payments"""
        result = await db.execute(
            select(Payment)
            .where(
                and_(
                    Payment.is_delayed == True,
                    Payment.paid_date.is_(None)
                )
            )
            .order_by(Payment.delay_days.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def create(db: AsyncSession, data: PaymentCreate) -> Payment:
        """Create a new payment record"""
        payment = Payment(
            subscriber_id=data.subscriber_id,
            amount=data.amount,
            due_date=data.due_date,
            is_delayed=data.due_date < date.today(),
            delay_days=max(0, (date.today() - data.due_date).days) if data.due_date < date.today() else 0
        )
        db.add(payment)
        await db.flush()
        await db.refresh(payment)
        return payment
    
    @staticmethod
    async def mark_as_paid(db: AsyncSession, payment_id: int, paid_date: Optional[date] = None) -> Optional[Payment]:
        """Mark payment as paid"""
        payment = await PaymentService.get_by_id(db, payment_id)
        if not payment:
            return None
        
        payment.paid_date = paid_date or date.today()
        # Update delay info
        if payment.due_date and payment.paid_date > payment.due_date:
            payment.is_delayed = True
            payment.delay_days = (payment.paid_date - payment.due_date).days
        
        await db.flush()
        await db.refresh(payment)
        return payment
    
    @staticmethod
    async def update_delay_status(db: AsyncSession) -> int:
        """Update delay status for all unpaid payments"""
        today = date.today()
        result = await db.execute(
            select(Payment).where(Payment.paid_date.is_(None))
        )
        payments = result.scalars().all()
        
        updated = 0
        for payment in payments:
            if payment.due_date and payment.due_date < today:
                payment.is_delayed = True
                payment.delay_days = (today - payment.due_date).days
                updated += 1
        
        await db.flush()
        return updated
    
    @staticmethod
    async def delete(db: AsyncSession, payment_id: int) -> bool:
        """Delete payment record"""
        payment = await PaymentService.get_by_id(db, payment_id)
        if not payment:
            return False
        
        await db.delete(payment)
        return True
    
    @staticmethod
    async def generate_monthly_payments(db: AsyncSession) -> int:
        """Generate monthly payment records for all active subscribers"""
        today = date.today()
        first_of_month = today.replace(day=1)
        
        # Get all active subscribers
        result = await db.execute(
            select(Subscriber).where(Subscriber.is_active == True)
        )
        subscribers = result.scalars().all()
        
        created = 0
        for subscriber in subscribers:
            # Check if payment already exists for this month
            existing = await db.execute(
                select(Payment).where(
                    and_(
                        Payment.subscriber_id == subscriber.id,
                        Payment.due_date >= first_of_month,
                        Payment.due_date < (first_of_month.replace(month=first_of_month.month + 1) 
                                           if first_of_month.month < 12 
                                           else first_of_month.replace(year=first_of_month.year + 1, month=1))
                    )
                )
            )
            if existing.scalar_one_or_none():
                continue
            
            # Create payment record
            payment = Payment(
                subscriber_id=subscriber.id,
                amount=subscriber.monthly_cost,
                due_date=first_of_month,
                is_delayed=False,
                delay_days=0
            )
            db.add(payment)
            created += 1
        
        await db.flush()
        return created
