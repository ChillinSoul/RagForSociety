# app/routers/experiments.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
_config_service = None

def initialize_router(config_service):
    global _config_service
    _config_service = config_service
    logger.info("Experiments router initialized with config service")

class ScoreRequest(BaseModel):
    queryId: str
    score: int

@router.post("/score", response_model=dict)
async def score_result(score_data: ScoreRequest):
    """Simple endpoint to record experiment scores"""
    logger.info(f"Received score request: {score_data}")
    
    if not _config_service:
        logger.error("Configuration service not initialized")
        raise HTTPException(status_code=500, detail="Configuration service not initialized")
    
    try:
        # Extract experiment_group and model_config_id from queryId
        experiment_group, model_config_id = score_data.queryId.split(':', 1)
        model_config_id = int(model_config_id)
        
        logger.info(f"Processing score for experiment group: {experiment_group}, model: {model_config_id}")
        
        # Save the score
        _config_service.save_experiment_result(
            question="",  # We don't need to store the question for simple scoring
            answer="",   # We don't need to store the answer for simple scoring
            model_config_id=model_config_id,
            score=score_data.score
        )
        
        return JSONResponse(
            content={
                "message": "Score saved successfully",
                "experiment_group": experiment_group,
                "score": score_data.score
            }
        )
    except ValueError:
        logger.error(f"Invalid queryId format: {score_data.queryId}")
        raise HTTPException(status_code=400, detail="Invalid queryId format")
    except Exception as e:
        logger.error(f"Error saving score: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving score: {str(e)}")

@router.get("/groups", response_model=list[str])
async def get_experiment_groups():
    """Get available experiment groups"""
    if not _config_service:
        raise HTTPException(status_code=500, detail="Configuration service not initialized")
    return _config_service.get_experiment_groups()