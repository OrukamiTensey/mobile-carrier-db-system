"""
Mobile Operator Database - Main Application
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.config import get_settings
from app.database.postgres_db import init_postgres, close_postgres
from app.database.neo4j_db import init_neo4j, close_neo4j
from app.database.couchdb_client import init_couchdb
from app.routes import subscribers, payments, service_requests, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events"""
    # Startup
    print("🚀 Starting Mobile Operator Database...")
    
    # Try to connect to databases (non-fatal if they fail)
    try:
        await init_postgres()
    except Exception as e:
        print(f"⚠️ PostgreSQL connection failed: {e}")
    
    try:
        await init_neo4j()
    except Exception as e:
        print(f"⚠️ Neo4j connection failed: {e}")
    
    try:
        await init_couchdb()
    except Exception as e:
        print(f"⚠️ CouchDB connection failed: {e}")
    
    print("✅ Server started! Some databases may be unavailable.")
    
    yield
    
    # Shutdown
    print("🔌 Shutting down...")
    try:
        await close_postgres()
    except:
        pass
    try:
        await close_neo4j()
    except:
        pass
    print("👋 Goodbye!")


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="База даних оператора мобільної телефонії",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# Include routers
app.include_router(subscribers.router, prefix="/api/subscribers", tags=["Абоненти"])
app.include_router(payments.router, prefix="/api/payments", tags=["Платежі"])
app.include_router(service_requests.router, prefix="/api/service-requests", tags=["Заявки на обслуговування"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Аналітика"])


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - redirect to frontend"""
    return {
        "message": "Mobile Operator Database API",
        "docs": "/docs",
        "frontend": "/static/index.html"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.app_version}
