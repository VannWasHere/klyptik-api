from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import json
import logging
import traceback
from datetime import datetime
from typing import List, Optional

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
    topic: str = Field(..., description="The topic for the quiz questions")
    number_of_questions: int = Field(10, description="Number of questions to generate (default: 10)", ge=1, le=20)

class QuestionDetail(BaseModel):
    question: str
    options: List[str]
    correctAnswer: str
    userAnswer: str
    isCorrect: bool

class QuizResultRequest(BaseModel):
    userId: str
    topic: str
    score: int
    totalQuestions: int
    percentage: float
    completedAt: datetime
    questionDetails: List[QuestionDetail]

# Simple user verification function instead of token-based auth
async def verify_user_exists(user_id: str = Query(..., description="The user ID to verify")):
    """
    Verify that the user exists in the database
    """
    try:
        db = initialize_firebase()
        user_ref = db.collection("users").document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found"
            )
        
        # Return user data
        user_data = user_doc.to_dict()
        user_data["uid"] = user_id
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error verifying user: {str(e)}"
        )

@router.post("/ask")
def ask(request: AskRequest):
    """
    Generate a quiz with the specified number of questions about the given topic.
    
    - **topic**: The subject or theme for the quiz questions
    - **number_of_questions**: Number of questions to generate (1-20, default: 10)
    
    Returns a JSON quiz with multiple-choice questions.
    """
    try:
        # Create a standardized instruction
        instruction = f"Create {request.number_of_questions} multiple-choice questions about {request.topic}"
        
        # Generate quiz
        response = generate_response(instruction)
        return response
    except Exception as e:
        logger.error(f"Error in /ask endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        if "CONFIGURATION_NOT_FOUND" in str(e):
            raise HTTPException(
                status_code=500,
                detail="CONFIGURATION_NOT_FOUND - Check Firebase credentials"
            )
        raise

@router.post("/save-quiz")
def submit_quiz_result(quiz_result: QuizResultRequest, user_id: str = Query(..., description="User ID for authentication")):
    """
    Save quiz result to Firebase.
    
    Requires user_id query parameter for authentication.
    """
    try:
        # Initialize Firebase
        db = initialize_firebase()
        
        # Verify user exists
        user_ref = db.collection("users").document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(
                status_code=404, 
                detail=f"User with ID {user_id} not found"
            )
        
        # Verify the user ID matches the one in the quiz result
        if user_id != quiz_result.userId:
            raise HTTPException(
                status_code=403, 
                detail="User ID in query parameter does not match userId in quiz result"
            )
        
        # Convert to dictionary and add timestamps
        result_data = quiz_result.dict()
        result_data["createdAt"] = datetime.now().isoformat()
        
        # Save to Firestore
        quiz_ref = db.collection("quiz_results").document()
        quiz_ref.set(result_data)
        
        # Add the document ID to the response
        result_data["id"] = quiz_ref.id
        
        # Update user stats without a transaction (simpler approach)
        user_data = user_doc.to_dict()
        stats = user_data.get("quizStats", {
            "totalQuizzes": 0,
            "totalCorrect": 0,
            "totalQuestions": 0,
            "averageScore": 0
        })
        
        # Update stats
        stats["totalQuizzes"] = stats.get("totalQuizzes", 0) + 1
        stats["totalCorrect"] = stats.get("totalCorrect", 0) + quiz_result.score
        stats["totalQuestions"] = stats.get("totalQuestions", 0) + quiz_result.totalQuestions
        
        # Calculate new average
        if stats["totalQuestions"] > 0:
            stats["averageScore"] = (stats["totalCorrect"] / stats["totalQuestions"]) * 100
        
        # Update the document
        user_ref.update({"quizStats": stats})
        
        return {
            "success": True,
            "message": "Quiz result saved successfully",
            "resultId": quiz_ref.id,
            "updatedStats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving quiz result: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save quiz result: {str(e)}"
        )

@router.get("/user-profile")
async def get_user_profile(user_id: str = Query(..., description="User ID to retrieve profile")):
    """
    Get a user's profile including quiz statistics.
    """
    try:
        user_data = await verify_user_exists(user_id)
        return {
            "success": True,
            "profile": user_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user profile: {str(e)}"
        )

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
