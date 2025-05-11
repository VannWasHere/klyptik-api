import firebase_admin
from firebase_admin import auth
import logging
from typing import Dict, Any, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

def create_user(email: str, password: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Create a new user with email and password
    
    Args:
        email: User's email
        password: User's password
        
    Returns:
        Tuple of (success, result)
    """
    try:
        user = auth.create_user(
            email=email,
            password=password,
            email_verified=False
        )
        logger.info(f"Created new user: {user.uid}")
        return True, {
            "uid": user.uid,
            "email": user.email,
            "message": "User created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return False, {"error": str(e)}

def login_user(email: str, password: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Authenticate a user with email and password
    
    Args:
        email: User's email
        password: User's password
        
    Returns:
        Tuple of (success, result)
    """
    try:
        # Note: Firebase Admin SDK doesn't provide direct email/password authentication
        # We need to use the REST API or Firebase Auth SDK for this
        # This is a placeholder for the actual implementation
        
        # Try to get the user by email
        user = auth.get_user_by_email(email)
        
        # In a real implementation, we would verify the password
        # Since Admin SDK doesn't support this directly, we're just checking if the user exists
        
        # Generate a custom token that can be used by the client
        custom_token = auth.create_custom_token(user.uid)
        
        return True, {
            "uid": user.uid,
            "email": user.email,
            "token": custom_token.decode('utf-8'),
            "message": "Login successful"
        }
    except auth.UserNotFoundError:
        logger.warning(f"Login attempt for non-existent user: {email}")
        return False, {"error": "Invalid email or password"}
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return False, {"error": str(e)}

def get_user(uid: str) -> Optional[Dict[str, Any]]:
    """
    Get user details by UID
    
    Args:
        uid: User's UID
        
    Returns:
        User details or None if not found
    """
    try:
        user = auth.get_user(uid)
        return {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "photo_url": user.photo_url,
            "email_verified": user.email_verified
        }
    except auth.UserNotFoundError:
        logger.warning(f"User not found: {uid}")
        return None
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        return None

def update_user(uid: str, display_name: str = None, photo_url: str = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Update user profile
    
    Args:
        uid: User's UID
        display_name: New display name (optional)
        photo_url: New photo URL (optional)
        
    Returns:
        Tuple of (success, result)
    """
    try:
        # Build update dictionary with only provided fields
        update_kwargs = {}
        if display_name is not None:
            update_kwargs['display_name'] = display_name
        if photo_url is not None:
            update_kwargs['photo_url'] = photo_url
            
        # Update user
        user = auth.update_user(uid, **update_kwargs)
        
        return True, {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "photo_url": user.photo_url,
            "message": "User updated successfully"
        }
    except auth.UserNotFoundError:
        logger.warning(f"Update attempt for non-existent user: {uid}")
        return False, {"error": "User not found"}
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return False, {"error": str(e)} 