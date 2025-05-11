from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
import logging
import traceback

from app.models.model_loader import get_model, get_tokenizer
from app.services.generation_service import generate_response
from app.services.firebase_initiator import initialize_firebase

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
    try:
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
    except Exception as e:
        logger.error(f"Error in /ask endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        if "CONFIGURATION_NOT_FOUND" in str(e):
            raise HTTPException(
                status_code=500,
                detail="CONFIGURATION_NOT_FOUND - Check Firebase credentials"
            )
        raise

@router.get("/users")
def get_users():
    try:
        # Initialize Firebase
        try:
            db = initialize_firebase()
        except Exception as e:
            logger.error(f"Firebase initialization error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="CONFIGURATION_NOT_FOUND"
            )
        
        # Get users collection
        users_ref = db.collection("users").stream()
        
        # Convert Firestore documents to dictionaries
        users_list = []
        for user in users_ref:
            user_data = user.to_dict()
            user_data['id'] = user.id  # Add document ID
            users_list.append(user_data)
        
        return {"users": users_list}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /users endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e), "users": []}
