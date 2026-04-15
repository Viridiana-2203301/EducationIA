"""
Datasets API endpoint.
List and retrieve dataset information and profiles.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from app.schemas.schemas import DatasetInfo, DatasetProfile, CleaningStats
from app.services.storage import storage

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.get("", response_model=List[DatasetInfo])
async def list_datasets():
    """List all uploaded datasets with their status and metadata."""
    return storage.get_all_datasets()


@router.get("/{dataset_id}", response_model=DatasetInfo)
async def get_dataset(dataset_id: str):
    """Get detailed information about a specific dataset."""
    ds_info = storage.get_dataset_info(dataset_id)
    if not ds_info:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    return ds_info


@router.get("/{dataset_id}/profile", response_model=Optional[DatasetProfile])
async def get_dataset_profile(dataset_id: str):
    """Get the profiling results for a dataset."""
    profile = storage.get_profile(dataset_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado. Ejecute el análisis primero.")
    return profile


@router.get("/{dataset_id}/cleaning", response_model=Optional[CleaningStats])
async def get_cleaning_stats(dataset_id: str):
    """Get the cleaning statistics for a dataset."""
    stats = storage.get_cleaning_stats(dataset_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Stats de limpieza no disponibles.")
    return stats


@router.get("/{dataset_id}/preview")
async def preview_dataset(dataset_id: str, rows: int = 20):
    """Preview the first N rows of a dataset as JSON."""
    df = storage.get_best_dataframe(dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")

    rows = min(rows, 100)
    preview = df.head(rows)

    return {
        "columns": preview.columns.tolist(),
        "data": preview.fillna("").to_dict(orient="records"),
        "total_rows": len(df),
        "showing_rows": len(preview),
    }
