"""
Analytics API Routes (Neo4j)
"""
from fastapi import APIRouter, HTTPException
from typing import List

from app.database.neo4j_db import Neo4jService
from app.models.schemas import NetworkGraph

router = APIRouter()


@router.get("/network-graph")
async def get_network_graph():
    """Отримати граф зв'язків абонентів для візуалізації"""
    try:
        return await Neo4jService.get_network_graph()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j error: {str(e)}")


@router.get("/service-plans")
async def get_service_plans():
    """Отримати список тарифних планів"""
    try:
        return await Neo4jService.get_service_plans()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j error: {str(e)}")


@router.get("/connections/{ric_number}")
async def get_subscriber_connections(ric_number: str):
    """Отримати зв'язки (дзвінки) абонента"""
    try:
        return await Neo4jService.get_subscriber_connections(ric_number)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j error: {str(e)}")


@router.post("/subscriber-node")
async def create_subscriber_node(ric_number: str, full_name: str, service_plan: str = "Basic"):
    """Створити вузол абонента в графі"""
    try:
        result = await Neo4jService.create_subscriber_node(ric_number, full_name, service_plan)
        return {"message": "Вузол створено", "ric_number": ric_number}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j error: {str(e)}")


@router.post("/record-call")
async def record_call(from_ric: str, to_ric: str, duration_seconds: int, call_date: str):
    """Записати дзвінок між абонентами"""
    try:
        await Neo4jService.record_call(from_ric, to_ric, duration_seconds, call_date)
        return {"message": "Дзвінок зареєстровано"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j error: {str(e)}")
