import requests
import json
import logging
import os
import traceback
import uuid
import time
import hashlib
from typing import Dict, Any, Optional, Tuple

from firebase_admin import firestore
from app.services.firebase_firestore import create_user_profile, get_email_by_username
from app.config import FIREBASE_API_KEY
from app.services.firebase_initiator import initialize_firebase

# Configure logging
logger = logging.getLogger(__name__)

# Check if Firebase API key is set
if not FIREBASE_API_KEY or FIREBASE_API_KEY == "FIREBASE_API_KEY_NOT_SET":
    logger.warning("Firebase API key is not set or has default value. Using direct Firestore authentication instead.")

# Get Firestore client
db = initialize_firebase()

def generate_token(user_id: str) -> str:
    """
    Generate a simple token for authentication
    
    Args:
        user_id: User's ID
        
    Returns:
        A token string
    """
    timestamp = str(int(time.time()))
    random_part = str(uuid.uuid4())
    token_base = f"{user_id}:{timestamp}:{random_part}"
    return hashlib.sha256(token_base.encode()).hexdigest()

def signup_with_email_password(email: str, password: str, display_name: str = None, username: str = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Create a new user directly in Firestore
    
    Args:
        email: User's email
        password: User's password
        display_name: User's display name (optional)
        username: User's username (optional)
        
    Returns:
        Tuple of (success, result)
    """
    try:
        logger.info(f"Creating user with email: {email}")
        
        # Check if email already exists
        users_ref = db.collection('users')
        email_query = users_ref.where('email', '==', email).limit(1).stream()
        
        for _ in email_query:
            logger.warning(f"Email already exists: {email}")
            return False, {"error": "EMAIL_EXISTS"}
        
        # Generate a user ID
        uid = str(uuid.uuid4())
        
        # Hash the password (in a real app, use a proper password hashing library)
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Create user profile in Firestore
        user_profile = create_user_profile(
            uid=uid,
            email=email,
            display_name=display_name,
            username=username
        )
        
        # Store password hash in a separate collection for security
        db.collection('user_auth').document(uid).set({
            'email': email,
            'password_hash': hashed_password,
            'created_at': firestore.SERVER_TIMESTAMP
        })
        
        # Generate a token
        token = generate_token(uid)
        
        # Store token in a tokens collection with expiration
        expiry = int(time.time()) + 3600  # 1 hour from now
        db.collection('tokens').document(token).set({
            'uid': uid,
            'expires_at': expiry
        })
        
        # Include username in the response if available
        username = user_profile.get('username') if user_profile else None
        
        logger.info(f"User created successfully: {uid}")
        return True, {
            "uid": uid,
            "email": email,
            "display_name": display_name,
            "username": username,
            "token": token,
            "expires_in": 3600
        }
    except Exception as e:
        logger.error(f"Error during signup: {str(e)}")
        logger.error(traceback.format_exc())
        return False, {"error": str(e)}

def signin_with_email_password(email_or_username: str, password: str, is_email: bool = True) -> Tuple[bool, Dict[str, Any]]:
    """
    Sign in a user directly from Firestore
    
    Args:
        email_or_username: User's email or username
        password: User's password
        is_email: Whether the first parameter is an email (True) or username (False)
        
    Returns:
        Tuple of (success, result)
    """
    try:
        # If it's a username, we need to find the corresponding email first
        email = email_or_username
        
        if not is_email:
            # This is a username, we need to find the corresponding email
            email = get_email_by_username(email_or_username)
            if not email:
                logger.warning(f"No email found for username: {email_or_username}")
                return False, {"error": "Invalid username or password"}
        
        # Find user by email
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1).stream()
        
        user_data = None
        for doc in query:
            user_data = doc.to_dict()
            user_data['uid'] = doc.id
            break
        
        if not user_data:
            logger.warning(f"No user found for email: {email}")
            return False, {"error": "Invalid email or password"}
        
        # Get the password hash
        uid = user_data['uid']
        auth_doc = db.collection('user_auth').document(uid).get()
        
        if not auth_doc.exists:
            logger.warning(f"No auth data found for user: {uid}")
            return False, {"error": "Invalid email or password"}
        
        auth_data = auth_doc.to_dict()
        stored_hash = auth_data.get('password_hash')
        
        # Check password
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        if input_hash != stored_hash:
            logger.warning(f"Invalid password for user: {uid}")
            return False, {"error": "Invalid email or password"}
        
        # Generate a token
        token = generate_token(uid)
        
        # Store token in a tokens collection with expiration
        expiry = int(time.time()) + 3600  # 1 hour from now
        db.collection('tokens').document(token).set({
            'uid': uid,
            'expires_at': expiry
        })
        
        return True, {
            "uid": uid,
            "email": email,
            "display_name": user_data.get('display_name'),
            "username": user_data.get('username'),
            "token": token,
            "expires_in": 3600
        }
    except Exception as e:
        logger.error(f"Error during signin: {str(e)}")
        logger.error(traceback.format_exc())
        return False, {"error": str(e)}

def get_user_info(token: str) -> Optional[Dict[str, Any]]:
    """
    Get user info from token
    
    Args:
        token: Authentication token
        
    Returns:
        User info or None if failed
    """
    try:
        # Get token document
        token_doc = db.collection('tokens').document(token).get()
        
        if not token_doc.exists:
            logger.warning(f"Token not found: {token}")
            return None
        
        token_data = token_doc.to_dict()
        
        # Check if token is expired
        expires_at = token_data.get('expires_at', 0)
        if expires_at < time.time():
            logger.warning(f"Token expired: {token}")
            return None
        
        # Get user data
        uid = token_data.get('uid')
        user_doc = db.collection('users').document(uid).get()
        
        if not user_doc.exists:
            logger.warning(f"User not found for token: {token}")
            return None
        
        user_data = user_doc.to_dict()
        
        return {
            "uid": uid,
            "email": user_data.get('email'),
            "email_verified": False,  # We don't implement email verification in this simplified version
            "display_name": user_data.get('display_name'),
            "photo_url": user_data.get('photo_url'),
            "username": user_data.get('username')
        }
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def update_profile(token: str, display_name: str = None, photo_url: str = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Update user profile
    
    Args:
        token: Authentication token
        display_name: New display name (optional)
        photo_url: New photo URL (optional)
        
    Returns:
        Tuple of (success, result)
    """
    try:
        # Get user info from token
        user_info = get_user_info(token)
        if not user_info:
            return False, {"error": "Invalid or expired token"}
        
        uid = user_info.get("uid")
        
        # Prepare data to update
        update_data = {}
        if display_name is not None:
            update_data["display_name"] = display_name
        if photo_url is not None:
            update_data["photo_url"] = photo_url
        
        # Update user profile
        from app.services.firebase_firestore import update_user_profile
        success = update_user_profile(uid, update_data)
        
        if not success:
            return False, {"error": "Failed to update profile"}
        
        # Get updated user info
        updated_user = get_user_info(token)
        
        return True, {
            "uid": updated_user.get("uid"),
            "email": updated_user.get("email"),
            "display_name": updated_user.get("display_name"),
            "photo_url": updated_user.get("photo_url"),
            "username": updated_user.get("username"),
            "token": token
        }
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        logger.error(traceback.format_exc())
        return False, {"error": str(e)} 