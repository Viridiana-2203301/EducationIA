"""
Fused Datasets API endpoint.
List, preview, and download concatenated/fused datasets.
"""

import io
import math
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.services.storage import storage

router = APIRouter(prefix="/api/fused", tags=["fused"])


@router.get("")
async def list_fused_datasets():
    """List all fused/concatenated datasets with metadata."""
    all_fused = storage.get_all_fused_dataframes()
    result = []
    for key, df in all_fused.items():
        result.append({
            "key": key,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
        })
    return result


@router.get("/{key}/preview")
async def preview_fused_dataset(key: str, rows: int = 50):
    """Preview the first N rows of a fused dataset."""
    df = storage.get_fused_dataframe(key)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset fusionado no encontrado")

    rows = min(rows, 200)
    preview = df.head(rows)

    # Replace NaN/Inf with None for JSON safety
    safe_data = []
    for record in preview.to_dict(orient="records"):
        safe_record = {}
        for k, v in record.items():
            if v is None:
                safe_record[k] = None
            elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                safe_record[k] = None
            else:
                safe_record[k] = v
        safe_data.append(safe_record)

    return {
        "key": key,
        "columns": preview.columns.tolist(),
        "data": safe_data,
        "total_rows": len(df),
        "showing_rows": len(preview),
    }


@router.get("/{key}/download")
async def download_fused_dataset(key: str):
    """Download a fused dataset as CSV."""
    df = storage.get_fused_dataframe(key)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset fusionado no encontrado")

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)

    filename = f"{key}.csv"
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
