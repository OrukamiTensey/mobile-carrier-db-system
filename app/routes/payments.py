"""
Payments API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import date

from app.database.postgres_db import get_db
from app.services.payment_service import PaymentService
from app.models.schemas import PaymentCreate, PaymentResponse, PaymentUpdate

router = APIRouter()


@router.get("/", response_model=List[PaymentResponse])
async def get_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Отримати всі платежі"""
    payments = await PaymentService.get_all(db, skip, limit)
    return payments


@router.get("/delayed", response_model=List[PaymentResponse])
async def get_delayed_payments(db: AsyncSession = Depends(get_db)):
    """Отримати всі прострочені платежі"""
    return await PaymentService.get_delayed(db)


@router.get("/subscriber/{subscriber_id}", response_model=List[PaymentResponse])
async def get_subscriber_payments(
    subscriber_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Отримати платежі абонента"""
    return await PaymentService.get_by_subscriber(db, subscriber_id)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Отримати платіж за ID"""
    payment = await PaymentService.get_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Платіж не знайдено")
    return payment


@router.post("/", response_model=PaymentResponse, status_code=201)
async def create_payment(
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Створити запис про платіж"""
    return await PaymentService.create(db, data)


@router.post("/{payment_id}/pay", response_model=PaymentResponse)
async def mark_payment_as_paid(
    payment_id: int,
    paid_date: date = None,
    db: AsyncSession = Depends(get_db)
):
    """Позначити платіж як оплачений"""
    payment = await PaymentService.mark_as_paid(db, payment_id, paid_date)
    if not payment:
        raise HTTPException(status_code=404, detail="Платіж не знайдено")
    return payment


@router.post("/update-delays")
async def update_delay_statuses(db: AsyncSession = Depends(get_db)):
    """Оновити статуси затримок для всіх неоплачених платежів"""
    updated = await PaymentService.update_delay_status(db)
    return {"message": f"Оновлено {updated} платежів"}


@router.post("/generate-monthly")
async def generate_monthly_payments(db: AsyncSession = Depends(get_db)):
    """Згенерувати місячні платежі для всіх активних абонентів"""
    created = await PaymentService.generate_monthly_payments(db)
    return {"message": f"Створено {created} нових платежів"}


@router.delete("/{payment_id}", status_code=204)
async def delete_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Видалити платіж"""
    deleted = await PaymentService.delete(db, payment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Платіж не знайдено")
