"""
Subscribers API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database.postgres_db import get_db
from app.services.subscriber_service import SubscriberService
from app.models.schemas import (
    SubscriberCreate, 
    SubscriberUpdate, 
    SubscriberResponse,
    SubscriberWithPayments,
    ColumnSelectionRequest,
    DelayedPaymentInfo
)

router = APIRouter()


@router.get("/", response_model=List[SubscriberResponse])
async def get_subscribers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Отримати список всіх абонентів"""
    subscribers = await SubscriberService.get_all(db, skip, limit)
    return subscribers


@router.get("/columns", response_model=List[str])
async def get_available_columns():
    """Отримати список доступних колонок для вибору"""
    return SubscriberService.get_available_columns()


@router.post("/by-columns")
async def get_subscribers_by_columns(
    request: ColumnSelectionRequest,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Отримати абонентів з обраними колонками"""
    return await SubscriberService.get_by_columns(db, request.columns, skip, limit)


@router.get("/delayed-payments", response_model=List[DelayedPaymentInfo])
async def get_delayed_payments_subscribers(db: AsyncSession = Depends(get_db)):
    """Отримати список абонентів із затриманими платежами та датами відключення"""
    return await SubscriberService.get_delayed_payments_subscribers(db)


@router.get("/search")
async def search_subscribers(
    q: str = Query(..., min_length=2, description="Пошуковий запит"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Пошук абонентів за ПІБ або RIC-номером"""
    subscribers = await SubscriberService.search(db, q, skip, limit)
    return [s.to_dict() for s in subscribers]


@router.get("/{subscriber_id}", response_model=SubscriberResponse)
async def get_subscriber(
    subscriber_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Отримати абонента за ID"""
    subscriber = await SubscriberService.get_by_id(db, subscriber_id)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Абонента не знайдено")
    return subscriber


@router.get("/{subscriber_id}/with-payments")
async def get_subscriber_with_payments(
    subscriber_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Отримати абонента з історією платежів"""
    subscriber = await SubscriberService.get_with_payments(db, subscriber_id)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Абонента не знайдено")
    
    result = subscriber.to_dict()
    result["payments"] = [p.to_dict() for p in subscriber.payments]
    result["total_debt"] = sum(
        float(p.amount) for p in subscriber.payments 
        if p.is_delayed and p.paid_date is None
    )
    return result


@router.get("/ric/{ric_number}", response_model=SubscriberResponse)
async def get_subscriber_by_ric(
    ric_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Отримати абонента за RIC-номером"""
    subscriber = await SubscriberService.get_by_ric(db, ric_number)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Абонента не знайдено")
    return subscriber


@router.post("/", response_model=SubscriberResponse, status_code=201)
async def create_subscriber(
    data: SubscriberCreate,
    db: AsyncSession = Depends(get_db)
):
    """Створити нового абонента"""
    # Check if RIC already exists
    existing = await SubscriberService.get_by_ric(db, data.ric_number)
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Абонент з RIC {data.ric_number} вже існує"
        )
    
    subscriber = await SubscriberService.create(db, data)
    return subscriber


@router.put("/{subscriber_id}", response_model=SubscriberResponse)
async def update_subscriber(
    subscriber_id: int,
    data: SubscriberUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Оновити дані абонента"""
    subscriber = await SubscriberService.update(db, subscriber_id, data)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Абонента не знайдено")
    return subscriber


@router.delete("/{subscriber_id}", status_code=204)
async def delete_subscriber(
    subscriber_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Видалити абонента"""
    deleted = await SubscriberService.delete(db, subscriber_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Абонента не знайдено")
