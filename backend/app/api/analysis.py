"""
Analysis API endpoint.
Triggers the full analysis pipeline and retrieves results.
"""

import logging
from fastapi import APIRouter, HTTPException
from app.schemas.schemas import AnalysisRequest, AnalysisResults
from app.pipelines.pipeline import run_full_pipeline
from app.services.storage import storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/run", response_model=AnalysisResults)
async def run_analysis(request: AnalysisRequest = None):
    """
    Execute the full analysis pipeline.
    Steps: profile → clean → match → graph → fuse → ML → insights
    """
    datasets = storage.get_all_datasets()
    if not datasets:
        logger.error("No datasets found")
        raise HTTPException(status_code=400, detail="No hay datasets cargados. Suba archivos primero.")

    if request is None:
        request = AnalysisRequest()

    logger.info(f"Starting analysis with {len(datasets)} datasets")
    logger.info(f"Analysis request: {request}")
    
    try:
        results = run_full_pipeline(request)
        logger.info(f"Analysis completed with status: {results.status}")
        
        if results.status == "error":
            logger.error(f"Pipeline error: {results.error}")
            raise HTTPException(status_code=500, detail=f"Error en análisis: {results.error}")

        return results
    except Exception as e:
        logger.exception("Unhandled exception in analysis")
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")


@router.get("/results/{analysis_id}", response_model=AnalysisResults)
async def get_analysis_results(analysis_id: str):
    """Get results of a specific analysis run."""
    results = storage.get_analysis_results(analysis_id)
    if not results:
        raise HTTPException(status_code=404, detail="Resultados no encontrados")
    return results


@router.get("/latest", response_model=AnalysisResults)
async def get_latest_analysis():
    """Get the most recent analysis results."""
    results = storage.get_latest_analysis()
    if not results:
        raise HTTPException(status_code=404, detail="No hay análisis disponibles. Ejecute uno primero.")
    return results
