from fastapi import APIRouter, HTTPException
import logging 
from predict import ort_session

router = APIRouter()
logger = logging.getLogger()
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if model is loaded
        if ort_session is None:
            error_msg = "Model not loaded"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))