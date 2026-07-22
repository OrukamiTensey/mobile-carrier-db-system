"""
Service Request Service - Business Logic for CouchDB
"""
from typing import List, Optional, Dict, Any
from datetime import date

from app.database.couchdb_client import CouchDBService, ServiceRequestDocument
from app.models.schemas import ServiceRequestCreate, RequestStatus


class ServiceRequestService:
    """Service for service request operations"""
    
    @staticmethod
    def create_request(data: ServiceRequestCreate) -> Dict[str, Any]:
        """Create a new service request"""
        request = ServiceRequestDocument(
            ric_number=data.ric_number,
            phone_model=data.phone_model,
            request_type=data.request_type.value,
            connection_date=str(data.connection_date) if data.connection_date else None,
            disconnection_date=str(data.disconnection_date) if data.disconnection_date else None,
            service_duration_hours=data.service_duration_hours,
            has_contract=data.has_contract,
            notes=data.notes or "",
            status="pending"
        )
        return CouchDBService.create_service_request(request)
    
    @staticmethod
    def get_request(request_id: str) -> Optional[Dict[str, Any]]:
        """Get service request by ID"""
        return CouchDBService.get_service_request(request_id)
    
    @staticmethod
    def get_requests_by_ric(ric_number: str) -> List[Dict[str, Any]]:
        """Get all service requests for a RIC number"""
        return CouchDBService.get_requests_by_ric(ric_number)
    
    @staticmethod
    def get_pending_requests() -> List[Dict[str, Any]]:
        """Get all pending service requests"""
        return CouchDBService.get_pending_requests()
    
    @staticmethod
    def get_all_requests(limit: int = 100) -> List[Dict[str, Any]]:
        """Get all service requests"""
        return CouchDBService.get_all_requests(limit)
    
    @staticmethod
    def update_status(request_id: str, status: RequestStatus) -> Optional[Dict[str, Any]]:
        """Update request status"""
        return CouchDBService.update_request_status(request_id, status.value)
    
    @staticmethod
    def delete_request(request_id: str) -> bool:
        """Delete service request"""
        return CouchDBService.delete_request(request_id)
    
    @staticmethod
    def get_request_types() -> List[Dict[str, str]]:
        """Get available request types"""
        return [
            {"value": "repair", "label": "Ремонт"},
            {"value": "replacement", "label": "Заміна"},
            {"value": "activation", "label": "Активація"},
            {"value": "deactivation", "label": "Деактивація"},
            {"value": "maintenance", "label": "Технічне обслуговування"}
        ]
    
    @staticmethod
    def get_status_options() -> List[Dict[str, str]]:
        """Get available status options"""
        return [
            {"value": "pending", "label": "Очікує"},
            {"value": "in_progress", "label": "В процесі"},
            {"value": "completed", "label": "Завершено"},
            {"value": "cancelled", "label": "Скасовано"}
        ]
