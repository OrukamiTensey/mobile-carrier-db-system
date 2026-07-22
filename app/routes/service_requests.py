"""
Service Requests API Routes (CouchDB)
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.services.service_request_service import ServiceRequestService
from app.models.schemas import (
    ServiceRequestCreate, 
    ServiceRequestResponse,
    ServiceRequestStatusUpdate,
    RequestStatus
)

router = APIRouter()


@router.get("/")
async def get_all_service_requests(limit: int = Query(100, ge=1, le=500)):
    """Отримати всі заявки на обслуговування"""
    return ServiceRequestService.get_all_requests(limit)


@router.get("/pending")
async def get_pending_requests():
    """Отримати заявки зі статусом 'очікує'"""
    return ServiceRequestService.get_pending_requests()


@router.get("/types")
async def get_request_types():
    """Отримати типи заявок"""
    return ServiceRequestService.get_request_types()


@router.get("/statuses")
async def get_status_options():
    """Отримати можливі статуси заявок"""
    return ServiceRequestService.get_status_options()


@router.get("/by-ric/{ric_number}")
async def get_requests_by_ric(ric_number: str):
    """Отримати заявки за RIC-номером абонента"""
    return ServiceRequestService.get_requests_by_ric(ric_number)


@router.get("/{request_id}")
async def get_service_request(request_id: str):
    """Отримати заявку за ID"""
    request = ServiceRequestService.get_request(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Заявку не знайдено")
    return request


@router.post("/", status_code=201)
async def create_service_request(data: ServiceRequestCreate):
    """
    Створити заявку на обслуговування номеру.
    
    Включає:
    - RIC номер абонента
    - Модель телефону
    - Дату підключення/відключення
    - Час обслуговування
    - Наявність контракту
    """
    return ServiceRequestService.create_request(data)


@router.patch("/{request_id}/status")
async def update_request_status(request_id: str, data: ServiceRequestStatusUpdate):
    """Оновити статус заявки"""
    result = ServiceRequestService.update_status(request_id, data.status)
    if not result:
        raise HTTPException(status_code=404, detail="Заявку не знайдено")
    return result


@router.delete("/{request_id}", status_code=204)
async def delete_service_request(request_id: str):
    """Видалити заявку"""
    deleted = ServiceRequestService.delete_request(request_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Заявку не знайдено")
