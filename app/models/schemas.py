"""
Pydantic Schemas for API Validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class PhoneType(str, Enum):
    SMARTPHONE = "smartphone"
    FEATURE_PHONE = "feature_phone"
    TABLET = "tablet"


class ServiceType(str, Enum):
    PREPAID = "prepaid"
    POSTPAID = "postpaid"
    CORPORATE = "corporate"


class RequestType(str, Enum):
    REPAIR = "repair"
    REPLACEMENT = "replacement"
    ACTIVATION = "activation"
    DEACTIVATION = "deactivation"
    MAINTENANCE = "maintenance"


class RequestStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============ Subscriber Schemas ============

class SubscriberBase(BaseModel):
    ric_number: str = Field(..., min_length=10, max_length=20, description="RIC номер абонента")
    pin_code: Optional[str] = Field(None, max_length=10, description="PIN-код")
    full_name: str = Field(..., min_length=2, max_length=255, description="ПІБ абонента")
    phone_model: Optional[str] = Field(None, max_length=100, description="Модель телефону")
    phone_type: Optional[PhoneType] = Field(None, description="Тип телефону")
    service_type: Optional[ServiceType] = Field(None, description="Вид обслуговування")
    contract_duration_months: int = Field(12, ge=1, le=60, description="Тривалість контракту (місяців)")
    monthly_cost: float = Field(0.0, ge=0, description="Вартість обслуговування на місяць")


class SubscriberCreate(SubscriberBase):
    contract_start_date: Optional[date] = Field(None, description="Дата початку контракту")


class SubscriberUpdate(BaseModel):
    pin_code: Optional[str] = None
    full_name: Optional[str] = None
    phone_model: Optional[str] = None
    phone_type: Optional[PhoneType] = None
    service_type: Optional[ServiceType] = None
    contract_duration_months: Optional[int] = None
    monthly_cost: Optional[float] = None
    is_active: Optional[bool] = None


class SubscriberResponse(SubscriberBase):
    id: int
    contract_start_date: Optional[date] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SubscriberWithPayments(SubscriberResponse):
    payments: List["PaymentResponse"] = []
    total_debt: float = 0.0
    disconnection_date: Optional[date] = None


# ============ Payment Schemas ============

class PaymentBase(BaseModel):
    amount: float = Field(..., gt=0, description="Сума платежу")
    due_date: date = Field(..., description="Дата сплати")


class PaymentCreate(PaymentBase):
    subscriber_id: int = Field(..., description="ID абонента")


class PaymentUpdate(BaseModel):
    paid_date: Optional[date] = None
    is_delayed: Optional[bool] = None


class PaymentResponse(PaymentBase):
    id: int
    subscriber_id: int
    paid_date: Optional[date] = None
    is_delayed: bool = False
    delay_days: int = 0
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DelayedPaymentInfo(BaseModel):
    subscriber_id: int
    ric_number: str
    full_name: str
    payment_id: int
    amount: float
    due_date: date
    delay_days: int
    disconnection_date: date
    phone_model: Optional[str] = None
    service_type: Optional[str] = None


# ============ Service Request Schemas ============

class ServiceRequestCreate(BaseModel):
    ric_number: str = Field(..., description="RIC номер абонента")
    phone_model: str = Field(..., description="Модель телефону")
    request_type: RequestType = Field(..., description="Тип заявки")
    connection_date: Optional[date] = Field(None, description="Дата підключення")
    disconnection_date: Optional[date] = Field(None, description="Дата відключення")
    service_duration_hours: float = Field(0, ge=0, description="Час обслуговування (години)")
    has_contract: bool = Field(False, description="Наявність контракту")
    notes: Optional[str] = Field("", description="Примітки")


class ServiceRequestResponse(BaseModel):
    id: str = Field(..., alias="_id")
    ric_number: str
    phone_model: str
    request_type: str
    connection_date: Optional[str] = None
    disconnection_date: Optional[str] = None
    service_duration_hours: float
    has_contract: bool
    notes: str
    status: str
    created_at: str
    updated_at: str
    
    class Config:
        populate_by_name = True


class ServiceRequestStatusUpdate(BaseModel):
    status: RequestStatus


# ============ Column Selection Schema ============

class ColumnSelectionRequest(BaseModel):
    columns: List[str] = Field(..., description="Список колонок для відображення")
    
    @validator("columns")
    def validate_columns(cls, v):
        allowed = {
            "id", "ric_number", "pin_code", "full_name", "phone_model",
            "phone_type", "service_type", "contract_duration_months",
            "contract_start_date", "monthly_cost", "is_active",
            "created_at", "updated_at"
        }
        invalid = set(v) - allowed
        if invalid:
            raise ValueError(f"Invalid columns: {invalid}. Allowed: {allowed}")
        return v


# ============ Analytics Schemas ============

class NetworkNode(BaseModel):
    id: str
    label: str
    plan: Optional[str] = None


class NetworkEdge(BaseModel):
    source: str
    target: str
    weight: int = 1


class NetworkGraph(BaseModel):
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]


# Update forward references
SubscriberWithPayments.model_rebuild()
