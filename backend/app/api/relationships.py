"""
Relationships API endpoint.
Returns detected dataset relationships and graph data.
"""

from typing import List
from fastapi import APIRouter, HTTPException
from app.schemas.schemas import DatasetRelationship, RelationshipGraph
from app.services.storage import storage

router = APIRouter(prefix="/api/relationships", tags=["relationships"])


@router.get("", response_model=List[DatasetRelationship])
async def get_relationships():
    """Get all detected relationships between datasets."""
    return storage.get_relationships()


@router.get("/graph", response_model=RelationshipGraph)
async def get_relationship_graph():
    """Get the relationship graph for D3.js visualization."""
    graph = storage.get_graph()
    if not graph:
        raise HTTPException(
            status_code=404,
            detail="Grafo no disponible. Ejecute el análisis primero."
        )
    return graph
