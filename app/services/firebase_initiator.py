import firebase_admin
from firebase_admin import credentials, firestore
import logging
import os

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Firebase
def initialize_firebase():
    """
    Initialize Firebase
    """
    try:
        # Check if the credentials file exists
        creds_path = "creds/klyptik.json"
        if not os.path.exists(creds_path):
            logger.error(f"Firebase credentials file not found at {creds_path}")
            raise FileNotFoundError(f"Firebase credentials file not found at {creds_path}")
        
        # Log the file size to confirm it's not empty
        file_size = os.path.getsize(creds_path)
        logger.info(f"Found Firebase credentials file. Size: {file_size} bytes")
        
        # Initialize Firebase if not already initialized
        if not firebase_admin._apps:
            logger.info("Initializing Firebase...")
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized successfully")
        
        # Get Firestore client
        db = firestore.client()
        return db
    except Exception as e:
        logger.error(f"Error initializing Firebase: {str(e)}")
        raise