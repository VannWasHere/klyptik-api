import firebase_admin
from firebase_admin import firestore
import logging
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

def get_firestore_client():
    """
    Get Firestore client
    """
    try:
        db = firestore.client()
        return db
    except Exception as e:
        logger.error(f"Error getting Firestore client: {str(e)}")
        raise

def create_user_profile(uid: str, email: str, display_name: str = None, username: str = None):
    """
    Create a user profile in Firestore
    
    Args:
        uid: User's UID from Firebase Auth
        email: User's email
        display_name: User's display name
        username: User's username (optional)
    """
    try:
        db = get_firestore_client()
        
        # If username is not provided, generate one from email
        if not username:
            username = email.split('@')[0]
        
        # Check if username already exists
        username_doc = db.collection('usernames').document(username).get()
        if username_doc.exists:
            # Username already exists, append a number to make it unique
            base_username = username
            count = 1
            while db.collection('usernames').document(f"{base_username}{count}").get().exists:
                count += 1
            username = f"{base_username}{count}"
        
        # Create a document in the usernames collection to ensure uniqueness
        db.collection('usernames').document(username).set({
            'uid': uid,
            'created_at': firestore.SERVER_TIMESTAMP
        })
        
        # Create user profile
        user_data = {
            'uid': uid,
            'email': email,
            'username': username,
            'display_name': display_name or username,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        
        db.collection('users').document(uid).set(user_data)
        
        return user_data
    except Exception as e:
        logger.error(f"Error creating user profile: {str(e)}")
        return None

def get_email_by_username(username: str) -> Optional[str]:
    """
    Get user's email by username
    
    Args:
        username: User's username
        
    Returns:
        User's email or None if not found
    """
    try:
        db = get_firestore_client()
        
        # First check if username exists
        username_doc = db.collection('usernames').document(username).get()
        if not username_doc.exists:
            logger.warning(f"Username not found: {username}")
            return None
        
        # Get user ID from username document
        uid = username_doc.to_dict().get('uid')
        if not uid:
            logger.warning(f"User ID not found for username: {username}")
            return None
        
        # Get user document
        user_doc = db.collection('users').document(uid).get()
        if not user_doc.exists:
            logger.warning(f"User document not found for UID: {uid}")
            return None
        
        # Return user's email
        return user_doc.to_dict().get('email')
    except Exception as e:
        logger.error(f"Error getting email by username: {str(e)}")
        return None

def update_user_profile(uid: str, data: Dict[str, Any]) -> bool:
    """
    Update user profile in Firestore
    
    Args:
        uid: User's UID
        data: Data to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db = get_firestore_client()
        
        # Add updated_at timestamp
        data['updated_at'] = firestore.SERVER_TIMESTAMP
        
        # Update user profile
        db.collection('users').document(uid).update(data)
        
        return True
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        return False

def get_user_profile(uid: str) -> Optional[Dict[str, Any]]:
    """
    Get user profile from Firestore
    
    Args:
        uid: User's UID
        
    Returns:
        User profile or None if not found
    """
    try:
        db = get_firestore_client()
        
        # Get user document
        user_doc = db.collection('users').document(uid).get()
        if not user_doc.exists:
            logger.warning(f"User document not found for UID: {uid}")
            return None
        
        # Return user profile
        return user_doc.to_dict()
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return None 