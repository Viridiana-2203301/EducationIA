"""
Insights API endpoint.
Returns generated natural-language insights.
"""

from typing import List
from fastapi import APIRouter
from app.schemas.schemas import Insight
from app.services.storage import storage

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("", response_model=List[Insight])
async def get_insights():
    """Get all generated insights from the latest analysis."""
    return storage.get_insights()
