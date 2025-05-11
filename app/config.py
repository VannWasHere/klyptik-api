import os
import logging
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
load_dotenv()

# Firebase Configuration
FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY")
if not FIREBASE_API_KEY:
    logger.warning("FIREBASE_API_KEY environment variable is not set. Firebase authentication will not work.")
    # Use a placeholder value for development - this won't work in production
    FIREBASE_API_KEY = "FIREBASE_API_KEY_NOT_SET"

# Model Configuration
MODEL_PATH = os.environ.get("MODEL_PATH", "VannWasHere/qwen3-tuned-response")

# Server Configuration
PORT = int(os.environ.get("PORT", 8000))
HOST = os.environ.get("HOST", "0.0.0.0")
DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "t")

# Function to get configuration as a dictionary
def get_config():
    return {
        "firebase": {
            "api_key": FIREBASE_API_KEY,
        },
        "model": {
            "path": MODEL_PATH,
        },
        "server": {
            "port": PORT,
            "host": HOST,
            "debug": DEBUG,
        }
    } 