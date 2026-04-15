"""
Upload API endpoint.
Handles CSV file uploads with validation, encoding detection, and profiling.
"""

import os
import uuid
import pandas as pd
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.validators import (
    validate_file_extension, validate_file_size, detect_encoding,
    detect_delimiter, validate_csv_content,
)
from app.schemas.schemas import DatasetInfo, DatasetStatus, UploadResponse
from app.services.storage import storage

router = APIRouter(prefix="/api", tags=["upload"])

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "raw")


@router.post("/upload", response_model=UploadResponse)
async def upload_datasets(files: List[UploadFile] = File(...)):
    """
    Upload up to 36 CSV files for analysis.
    Validates format, detects encoding, and loads into memory.
    """
    if len(files) > 36:
        raise HTTPException(status_code=400, detail="Máximo 36 archivos permitidos")

    if storage.get_dataset_count() + len(files) > 36:
        raise HTTPException(
            status_code=400,
            detail=f"Ya hay {storage.get_dataset_count()} datasets. Máximo total: 36"
        )

    uploaded = []
    errors = []

    os.makedirs(DATA_DIR, exist_ok=True)

    for file in files:
        try:
            # Validate extension
            if not validate_file_extension(file.filename):
                errors.append(f"{file.filename}: No es un archivo CSV válido")
                continue

            # Read file bytes
            content = await file.read()

            # Validate size
            if not validate_file_size(len(content)):
                errors.append(f"{file.filename}: Archivo demasiado grande (máx 500MB)")
                continue

            # Validate CSV content
            is_valid, error_msg = validate_csv_content(content)
            if not is_valid:
                errors.append(f"{file.filename}: {error_msg}")
                continue

            # Detect encoding
            encoding = detect_encoding(content)

            # Decode and detect delimiter
            text = content.decode(encoding, errors="replace")
            delimiter = detect_delimiter(text.split("\n")[0])

            # Save raw file
            dataset_id = str(uuid.uuid4())[:8]
            raw_path = os.path.join(DATA_DIR, f"{dataset_id}_{file.filename}")
            with open(raw_path, "wb") as f:
                f.write(content)

            # Load DataFrame
            from io import StringIO
            df = pd.read_csv(
                StringIO(text),
                sep=delimiter,
                encoding=encoding,
                on_bad_lines="skip",
                low_memory=False,
            )

            if df.empty:
                errors.append(f"{file.filename}: El DataFrame resultante está vacío")
                continue

            # Store in memory
            storage.store_dataframe(dataset_id, df)

            file_size_mb = len(content) / (1024 * 1024)

            ds_info = DatasetInfo(
                id=dataset_id,
                filename=file.filename,
                status=DatasetStatus.UPLOADED,
                uploaded_at=datetime.utcnow(),
                row_count=len(df),
                column_count=len(df.columns),
                file_size_mb=round(file_size_mb, 2),
            )
            storage.store_dataset_info(dataset_id, ds_info)
            uploaded.append(ds_info)

        except Exception as e:
            errors.append(f"{file.filename}: Error inesperado - {str(e)}")

    message = f"{len(uploaded)} dataset(s) cargado(s) exitosamente"
    if errors:
        message += f". {len(errors)} error(es) encontrado(s)"

    return UploadResponse(message=message, datasets=uploaded, errors=errors)
