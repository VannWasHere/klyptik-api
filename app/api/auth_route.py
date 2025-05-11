from fastapi import APIRouter, HTTPException, Depends, Header, Request, Query
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import logging
import traceback

# Use the REST API implementation instead of the Admin SDK
from app.services.firebase_auth_rest import (
    signup_with_email_password,
    signin_with_email_password,
    get_user_info,
    update_profile
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={404: {"description": "Not found"}},
)

class UserRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('name')
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    photo_url: Optional[str] = None

async def get_current_user(request: Request, token: str = Query(None)):
    """
    Dependency to get the current user from the authorization header or token query parameter
    """
    # Check for Authorization header first
    authorization = request.headers.get("Authorization")
    
    if authorization:
        auth_token = authorization.strip()
    elif token:
        # Fallback to token query parameter
        auth_token = token
    else:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token. Please include an Authorization header or token query parameter."
        )
    
    # Verify the token and get user info
    user = get_user_info(auth_token)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    # Add token to user data for later use
    user["token"] = auth_token
    return user

@router.post("/register")
async def register(request: UserRegisterRequest):
    """
    Register a new user with name, email, and password
    """
    try:
        logger.info(f"Attempting to register user with email: {request.email}")
        
        # We've already validated that passwords match in the model
        
        # Register the user with email and password
        success, result = signup_with_email_password(
            email=request.email,
            password=request.password,
            display_name=request.name
        )
        
        if not success:
            error_detail = result.get("error", "Registration failed")
            logger.error(f"Registration failed: {error_detail}")
            
            # Add user-friendly error messages
            error_message = "Registration failed"
            if "EMAIL_EXISTS" in error_detail:
                error_message = "This email is already registered. Please use a different email or try logging in."
            elif "INVALID_EMAIL" in error_detail:
                error_message = "The email address is not valid. Please check and try again."
            elif "WEAK_PASSWORD" in error_detail:
                error_message = "The password is too weak. Please use a stronger password."
            else:
                error_message = f"Registration failed: {error_detail}"
                
            raise HTTPException(
                status_code=400,
                detail=error_message
            )
        
        logger.info(f"User registered successfully: {request.email}")
        
        # Add success message to the result
        result["message"] = "Registration successful! You can now log in."
        result["success"] = True
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        logger.error(traceback.format_exc())
        if "CONFIGURATION_NOT_FOUND" in str(e):
            raise HTTPException(
                status_code=500,
                detail="CONFIGURATION_NOT_FOUND - Firebase configuration issue"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login")
async def login(request: UserLoginRequest):
    """
    Login with email and password
    """
    try:
        success, result = signin_with_email_password(
            request.email, 
            request.password,
            is_email=True
        )
        
        if not success:
            error_detail = result.get("error", "Login failed")
            logger.error(f"Login failed: {error_detail}")
            
            # Add user-friendly error messages
            error_message = "Login failed"
            if "EMAIL_NOT_FOUND" in error_detail or "INVALID_PASSWORD" in error_detail:
                error_message = "Invalid email or password. Please try again."
            elif "USER_DISABLED" in error_detail:
                error_message = "This account has been disabled. Please contact support."
            elif "TOO_MANY_ATTEMPTS_TRY_LATER" in error_detail:
                error_message = "Too many failed login attempts. Please try again later."
            else:
                error_message = f"Login failed: {error_detail}"
                
            raise HTTPException(
                status_code=401,
                detail=error_message
            )
        
        logger.info(f"User logged in successfully: {request.email}")
        
        # Add success message to the result
        result["message"] = "Login successful!"
        result["success"] = True
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", summary="Get current user info")
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """
    Get current user information.
    
    - **Authorization**: Required. Provide your authentication token in the header
    - **token**: Alternative. You can also provide the token as a query parameter
    """
    return current_user

@router.put("/me", summary="Update user profile")
async def update_current_user(
    request: UserUpdateRequest,
    current_user = Depends(get_current_user)
):
    """
    Update current user profile.
    
    - **Authorization**: Required. Provide your authentication token in the header
    - **token**: Alternative. You can also provide the token as a query parameter
    """
    success, result = update_profile(
        current_user["token"],
        display_name=request.display_name,
        photo_url=request.photo_url
    )
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Update failed")
        )
    
    # Add success message to the result
    result["message"] = "Profile updated successfully!"
    result["success"] = True
    
    return result 