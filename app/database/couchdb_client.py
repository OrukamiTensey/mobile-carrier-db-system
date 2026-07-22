"""
CouchDB Client for Service Requests (Document Database)
"""
import couchdb
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from app.config import get_settings

settings = get_settings()

# Global database instance
_server = None
_db = None


def get_couchdb_server():
    """Get CouchDB server connection"""
    global _server
    if _server is None:
        url = f"http://{settings.couchdb_user}:{settings.couchdb_password}@{settings.couchdb_url.replace('http://', '')}"
        _server = couchdb.Server(url)
    return _server


def get_service_requests_db():
    """Get the service_requests database"""
    global _db
    if _db is None:
        server = get_couchdb_server()
        db_name = settings.couchdb_database
        
        if db_name not in server:
            _db = server.create(db_name)
            # Create design document for views
            _create_views(_db)
        else:
            _db = server[db_name]
    return _db


def _create_views(db):
    """Create CouchDB views for querying"""
    design_doc = {
        "_id": "_design/service_requests",
        "views": {
            "by_ric_number": {
                "map": "function(doc) { if(doc.ric_number) { emit(doc.ric_number, doc); } }"
            },
            "by_status": {
                "map": "function(doc) { if(doc.status) { emit(doc.status, doc); } }"
            },
            "by_date": {
                "map": "function(doc) { if(doc.created_at) { emit(doc.created_at, doc); } }"
            },
            "pending": {
                "map": "function(doc) { if(doc.status === 'pending') { emit(doc.created_at, doc); } }"
            }
        }
    }
    try:
        db.save(design_doc)
    except couchdb.http.ResourceConflict:
        pass  # Design doc already exists


async def init_couchdb():
    """Initialize CouchDB connection"""
    try:
        db = get_service_requests_db()
        # Test by getting info
        info = db.info()
        print(f"✅ CouchDB connected successfully (docs: {info.get('doc_count', 0)})")
    except Exception as e:
        print(f"❌ CouchDB connection failed: {e}")
        # Don't raise - allow app to work without CouchDB


class ServiceRequestDocument:
    """Service Request document structure"""
    
    def __init__(
        self,
        ric_number: str,
        phone_model: str,
        request_type: str,  # repair, replacement, activation, deactivation
        connection_date: Optional[str] = None,
        disconnection_date: Optional[str] = None,
        service_duration_hours: float = 0,
        has_contract: bool = False,
        notes: str = "",
        status: str = "pending"  # pending, in_progress, completed, cancelled
    ):
        self.id = f"sr_{uuid.uuid4().hex[:12]}"
        self.ric_number = ric_number
        self.phone_model = phone_model
        self.request_type = request_type
        self.connection_date = connection_date
        self.disconnection_date = disconnection_date
        self.service_duration_hours = service_duration_hours
        self.has_contract = has_contract
        self.notes = notes
        self.status = status
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "_id": self.id,
            "type": "service_request",
            "ric_number": self.ric_number,
            "phone_model": self.phone_model,
            "request_type": self.request_type,
            "connection_date": self.connection_date,
            "disconnection_date": self.disconnection_date,
            "service_duration_hours": self.service_duration_hours,
            "has_contract": self.has_contract,
            "notes": self.notes,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class CouchDBService:
    """Service class for CouchDB operations"""
    
    @staticmethod
    def create_service_request(request: ServiceRequestDocument) -> Dict[str, Any]:
        """Create a new service request"""
        db = get_service_requests_db()
        doc = request.to_dict()
        doc_id, doc_rev = db.save(doc)
        doc["_rev"] = doc_rev
        return doc
    
    @staticmethod
    def get_service_request(request_id: str) -> Optional[Dict[str, Any]]:
        """Get a service request by ID"""
        db = get_service_requests_db()
        try:
            return dict(db[request_id])
        except couchdb.http.ResourceNotFound:
            return None
    
    @staticmethod
    def get_requests_by_ric(ric_number: str) -> List[Dict[str, Any]]:
        """Get all service requests for a RIC number"""
        db = get_service_requests_db()
        try:
            results = db.view("service_requests/by_ric_number", key=ric_number)
            return [row.value for row in results]
        except Exception:
            # Fallback to manual filter if view doesn't exist
            return [dict(doc) for doc in db.view("_all_docs", include_docs=True).rows 
                    if doc.doc.get("ric_number") == ric_number]
    
    @staticmethod
    def get_pending_requests() -> List[Dict[str, Any]]:
        """Get all pending service requests"""
        db = get_service_requests_db()
        try:
            results = db.view("service_requests/pending")
            return [row.value for row in results]
        except Exception:
            return [dict(doc.doc) for doc in db.view("_all_docs", include_docs=True).rows 
                    if doc.doc.get("status") == "pending"]
    
    @staticmethod
    def get_all_requests(limit: int = 100) -> List[Dict[str, Any]]:
        """Get all service requests"""
        db = get_service_requests_db()
        results = []
        for row in db.view("_all_docs", include_docs=True, limit=limit):
            if row.doc and row.doc.get("type") == "service_request":
                results.append(dict(row.doc))
        return results
    
    @staticmethod
    def update_request_status(request_id: str, status: str) -> Optional[Dict[str, Any]]:
        """Update service request status"""
        db = get_service_requests_db()
        try:
            doc = db[request_id]
            doc["status"] = status
            doc["updated_at"] = datetime.utcnow().isoformat()
            db.save(doc)
            return dict(doc)
        except couchdb.http.ResourceNotFound:
            return None
    
    @staticmethod
    def delete_request(request_id: str) -> bool:
        """Delete a service request"""
        db = get_service_requests_db()
        try:
            doc = db[request_id]
            db.delete(doc)
            return True
        except couchdb.http.ResourceNotFound:
            return False
