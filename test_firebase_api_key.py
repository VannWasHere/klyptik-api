import os
import requests
import json
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_firebase_api_key():
    """Test if Firebase API key is valid"""
    # Load environment variables
    load_dotenv()
    
    # Check if API key is set
    firebase_api_key = os.environ.get("FIREBASE_API_KEY")
    if not firebase_api_key:
        logger.error("FIREBASE_API_KEY environment variable is not set")
        return False
    
    logger.info(f"Firebase API Key found: {firebase_api_key[:5]}...")
    
    # Test the API key by making a request to get the sign-in providers configuration
    # This is a simple request that doesn't require authentication
    test_url = f"https://identitytoolkit.googleapis.com/v1/accounts:createAuthUri?key={firebase_api_key}"
    
    try:
        # Make a minimal request just to test if the API key is valid
        payload = {
            "continueUri": "http://localhost",
            "providerId": "password"
        }
        
        response = requests.post(test_url, json=payload)
        
        # Check if the response is valid
        if response.status_code == 400:
            # This is actually expected because we're not providing all required fields
            # But it means the API key is valid (we're getting a proper Firebase error)
            error_message = response.json().get("error", {}).get("message", "")
            if "INVALID_CONTINUE_URI" in error_message or "MISSING_IDENTIFIER" in error_message:
                logger.info("Firebase API key is valid (received expected error response)")
                return True
                
        # If we get a 200 response, that's also valid
        if response.status_code == 200:
            logger.info("Firebase API key is valid (received 200 OK)")
            return True
            
        # If we get here, something went wrong
        logger.error(f"Firebase API key test failed with status code: {response.status_code}")
        logger.error(f"Response: {response.text}")
        return False
    except Exception as e:
        logger.error(f"Error testing Firebase API key: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_firebase_api_key()
    if success:
        print("Firebase API key is valid!")
    else:
        print("Firebase API key is NOT valid. See logs for details.") 