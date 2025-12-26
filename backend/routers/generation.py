from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(
    prefix="/generation",
    tags=["generation"]
)

class GenerateRequest(BaseModel):
    exam: str
    skill: str
    difficulty: str
    topic: Optional[str] = None
    n_items: int = 1

from core.generation_service import GenerationService

@router.post("/generate")
def generate_questions(request: GenerateRequest, db: Session = Depends(get_db)):
    service = GenerationService(db)
    result = service.generate_item(
        exam=request.exam,
        skill=request.skill,
        difficulty=request.difficulty
    )
    return result

@router.post("/validate")
def validate_question(question: Dict[str, Any]):
    return {"valid": True, "issues": []}

@router.post("/similarity-check")
def check_similarity(content: str):
    return {"is_original": True, "max_similarity": 0.05}
