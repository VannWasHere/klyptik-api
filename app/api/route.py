from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
import logging

from app.models.model_loader import get_model, get_tokenizer
from app.services.generation_service import generate_response

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api",
    tags=["quiz"],
    responses={404: {"description": "Not found"}},
)

class AskRequest(BaseModel):
    instruction: str

@router.post("/ask")
def ask(request: AskRequest):
    response = generate_response(request.instruction)
    try:
        # Parse the JSON string and return it directly
        return json.loads(response)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate valid JSON response"
        )
