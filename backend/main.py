"""
CSV Analytics Platform - Backend Entry Point.
FastAPI application with CORS support and API routers.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import upload, datasets, analysis, relationships, insights, fused

# Create data directories
for dir_name in ["data/raw", "data/processed", "data/temp"]:
    os.makedirs(os.path.join(os.path.dirname(__file__), dir_name), exist_ok=True)

app = FastAPI(
    title="CSV Analytics Platform",
    description="Plataforma de análisis automático de múltiples datasets CSV",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://education-ia.vercel.app",
        "https://educationia-backend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(upload.router)
app.include_router(datasets.router)
app.include_router(analysis.router)
app.include_router(relationships.router)
app.include_router(insights.router)
app.include_router(fused.router)


@app.get("/")
async def root():
    return {
        "name": "CSV Analytics Platform",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    from app.services.storage import storage
    return {
        "status": "healthy",
        "datasets_loaded": storage.get_dataset_count(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
