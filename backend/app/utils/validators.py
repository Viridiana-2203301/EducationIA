"""
File validation utilities.
Handles CSV validation, encoding detection, file size checks, and data sanitization.
"""

import os
import chardet
from typing import Tuple, Optional

MAX_FILE_SIZE_MB = 500
MAX_FILES = 36
ALLOWED_EXTENSIONS = {".csv"}


def validate_file_extension(filename: str) -> bool:
    """Check if file has .csv extension."""
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS


def validate_file_size(file_size_bytes: int) -> bool:
    """Check if file size is within limit."""
    return file_size_bytes <= MAX_FILE_SIZE_MB * 1024 * 1024


def detect_encoding(file_bytes: bytes) -> str:
    """
    Detect file encoding using chardet.
    Per csv-data-wrangler skill: never guess encoding, always detect.
    """
    result = chardet.detect(file_bytes[:100000])  # Sample first 100KB
    encoding = result.get("encoding", "utf-8")
    confidence = result.get("confidence", 0)

    if confidence < 0.5 or encoding is None:
        return "utf-8"

    encoding_map = {
        "ascii": "utf-8",
        "ISO-8859-1": "latin-1",
        "Windows-1252": "latin-1",
    }
    return encoding_map.get(encoding, encoding)


def detect_delimiter(sample_text: str) -> str:
    """Auto-detect CSV delimiter from sample text."""
    candidates = [",", ";", "\t", "|"]
    counts = {d: sample_text.count(d) for d in candidates}
    return max(counts, key=counts.get) if max(counts.values()) > 0 else ","


def sanitize_column_name(name: str) -> str:
    """Sanitize column name for safe processing."""
    import re
    name = name.strip()
    name = re.sub(r'[^\w\s]', '_', name)
    name = re.sub(r'\s+', '_', name)
    name = name.lower()
    return name


def validate_csv_content(file_bytes: bytes) -> Tuple[bool, Optional[str]]:
    """
    Basic CSV content validation.
    Returns (is_valid, error_message).
    """
    if len(file_bytes) == 0:
        return False, "El archivo está vacío"

    encoding = detect_encoding(file_bytes)
    try:
        text = file_bytes.decode(encoding)
    except (UnicodeDecodeError, LookupError):
        try:
            text = file_bytes.decode("utf-8", errors="replace")
        except Exception:
            return False, "No se pudo decodificar el archivo"

    lines = text.strip().split("\n")
    if len(lines) < 2:
        return False, "El archivo debe tener al menos un encabezado y una fila de datos"

    delimiter = detect_delimiter(lines[0])
    header_cols = len(lines[0].split(delimiter))

    if header_cols < 1:
        return False, "No se detectaron columnas"

    inconsistent = 0
    for line in lines[1:min(20, len(lines))]:
        if len(line.strip()) == 0:
            continue
        cols = len(line.split(delimiter))
        if abs(cols - header_cols) > 2:
            inconsistent += 1

    if inconsistent > len(lines[1:min(20, len(lines))]) * 0.5:
        return False, "Estructura de columnas inconsistente"

    return True, None
