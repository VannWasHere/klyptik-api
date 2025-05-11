import os
import json
import logging
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_firebase_credentials():
    """Test if Firebase credentials are valid"""
    # Load environment variables
    load_dotenv()
    
    # Check if API key is set
    firebase_api_key = os.environ.get("FIREBASE_API_KEY")
    if not firebase_api_key:
        logger.error("FIREBASE_API_KEY environment variable is not set")
        return False
    
    logger.info(f"Firebase API Key found: {firebase_api_key[:5]}...")
    
    # Check if credentials file exists
    creds_path = "creds/klyptik.json"
    if not os.path.exists(creds_path):
        logger.error(f"Firebase credentials file not found at {creds_path}")
        return False
    
    # Check if credentials file is valid JSON
    try:
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
        
        # Check for required fields
        required_fields = ["type", "project_id", "private_key_id", "private_key", "client_email"]
        for field in required_fields:
            if field not in creds_data:
                logger.error(f"Firebase credentials file is missing required field: {field}")
                return False
        
        logger.info(f"Firebase credentials file is valid JSON with required fields")
    except json.JSONDecodeError:
        logger.error(f"Firebase credentials file is not valid JSON")
        return False
    except Exception as e:
        logger.error(f"Error reading Firebase credentials file: {str(e)}")
        return False
    
    # Try to initialize Firebase
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred)
        
        # Try to access Firestore
        db = firestore.client()
        # Try a simple operation
        collections = [col.id for col in db.collections()]
        logger.info(f"Successfully connected to Firestore. Collections: {collections}")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing Firebase: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_firebase_credentials()
    if success:
        print("Firebase credentials are valid!")
    else:
        print("Firebase credentials are NOT valid. See logs for details.") 