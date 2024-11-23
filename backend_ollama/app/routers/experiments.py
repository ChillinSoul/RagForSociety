# app/routers/experiments.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ExperimentScore(BaseModel):
    question: str
    answer: str
    model_config_id: int
    score: float
    feedback: Optional[str] = None

class ExperimentGroup(BaseModel):
    name: str

@router.get("/experiment-groups", response_model=List[str])
async def get_experiment_groups(config_service=None):
    if not config_service:
        raise HTTPException(status_code=500, detail="Configuration service not initialized")
    return config_service.get_experiment_groups()

@router.post("/score")
async def score_result(score_data: ExperimentScore, config_service=None):
    if not config_service:
        raise HTTPException(status_code=500, detail="Configuration service not initialized")
    
    try:
        config_service.save_experiment_result(
            question=score_data.question,
            answer=score_data.answer,
            model_config_id=score_data.model_config_id,
            score=score_data.score,
            feedback=score_data.feedback
        )
        return {"message": "Score saved successfully"}
    except Exception as e:
        logger.error(f"Error saving score: {str(e)}")
        raise HTTPException(status_code=500, detail="Error saving score")