"""
Neo4j Database Connection for Graph-based Analysis
"""
from neo4j import AsyncGraphDatabase
from typing import Optional, List, Dict, Any

from app.config import get_settings

settings = get_settings()

# Global driver instance
_driver = None


async def get_driver():
    """Get Neo4j driver instance"""
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_url,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
    return _driver


async def init_neo4j():
    """Initialize Neo4j connection and create constraints"""
    try:
        driver = await get_driver()
        
        async with driver.session() as session:
            # Test connection
            result = await session.run("RETURN 1 as test")
            await result.consume()
            
            # Create constraints and indexes
            constraints = [
                "CREATE CONSTRAINT subscriber_ric IF NOT EXISTS FOR (s:Subscriber) REQUIRE s.ric_number IS UNIQUE",
                "CREATE CONSTRAINT service_plan_name IF NOT EXISTS FOR (p:ServicePlan) REQUIRE p.name IS UNIQUE",
            ]
            
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception:
                    pass  # Constraint might already exist
            
            # Create sample service plans
            await session.run("""
                MERGE (p1:ServicePlan {name: 'Basic', cost: 99, data_gb: 5, minutes: 100})
                MERGE (p2:ServicePlan {name: 'Standard', cost: 199, data_gb: 15, minutes: 500})
                MERGE (p3:ServicePlan {name: 'Premium', cost: 399, data_gb: 50, minutes: 1000})
                MERGE (p4:ServicePlan {name: 'Corporate', cost: 799, data_gb: 100, minutes: -1})
            """)
            
        print("✅ Neo4j connected successfully")
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        # Don't raise - allow app to work without Neo4j


async def close_neo4j():
    """Close Neo4j connection"""
    global _driver
    if _driver:
        await _driver.close()
        _driver = None
    print("🔌 Neo4j connection closed")


class Neo4jService:
    """Service class for Neo4j operations"""
    
    @staticmethod
    async def create_subscriber_node(ric_number: str, full_name: str, service_plan: str = "Basic"):
        """Create a subscriber node in Neo4j"""
        driver = await get_driver()
        async with driver.session() as session:
            result = await session.run("""
                MERGE (s:Subscriber {ric_number: $ric_number})
                SET s.full_name = $full_name
                WITH s
                MATCH (p:ServicePlan {name: $plan_name})
                MERGE (s)-[:HAS_PLAN]->(p)
                RETURN s
            """, ric_number=ric_number, full_name=full_name, plan_name=service_plan)
            return await result.single()
    
    @staticmethod
    async def record_call(from_ric: str, to_ric: str, duration_seconds: int, call_date: str):
        """Record a call between two subscribers"""
        driver = await get_driver()
        async with driver.session() as session:
            await session.run("""
                MATCH (from:Subscriber {ric_number: $from_ric})
                MATCH (to:Subscriber {ric_number: $to_ric})
                CREATE (from)-[:CALLED {duration: $duration, date: $date}]->(to)
            """, from_ric=from_ric, to_ric=to_ric, duration=duration_seconds, date=call_date)
    
    @staticmethod
    async def get_subscriber_connections(ric_number: str) -> List[Dict[str, Any]]:
        """Get all connections (calls) for a subscriber"""
        driver = await get_driver()
        async with driver.session() as session:
            result = await session.run("""
                MATCH (s:Subscriber {ric_number: $ric_number})-[c:CALLED]->(other:Subscriber)
                RETURN other.ric_number as to_number, other.full_name as to_name,
                       count(c) as call_count, sum(c.duration) as total_duration
                ORDER BY call_count DESC
                LIMIT 10
            """, ric_number=ric_number)
            return [dict(record) async for record in result]
    
    @staticmethod
    async def get_network_graph() -> Dict[str, Any]:
        """Get the entire network graph for visualization"""
        driver = await get_driver()
        async with driver.session() as session:
            # Get nodes
            nodes_result = await session.run("""
                MATCH (s:Subscriber)
                OPTIONAL MATCH (s)-[:HAS_PLAN]->(p:ServicePlan)
                RETURN s.ric_number as id, s.full_name as label, p.name as plan
            """)
            nodes = [dict(record) async for record in nodes_result]
            
            # Get edges
            edges_result = await session.run("""
                MATCH (from:Subscriber)-[c:CALLED]->(to:Subscriber)
                RETURN from.ric_number as source, to.ric_number as target, 
                       count(c) as weight
            """)
            edges = [dict(record) async for record in edges_result]
            
            return {"nodes": nodes, "edges": edges}
    
    @staticmethod
    async def get_service_plans() -> List[Dict[str, Any]]:
        """Get all service plans"""
        driver = await get_driver()
        async with driver.session() as session:
            result = await session.run("""
                MATCH (p:ServicePlan)
                RETURN p.name as name, p.cost as cost, p.data_gb as data_gb, p.minutes as minutes
                ORDER BY p.cost
            """)
            return [dict(record) async for record in result]
