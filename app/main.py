from fastapi import FastAPI
import logging
from fastapi.middleware.cors import CORSMiddleware

from app.models.model_loader import load_model
from app.api.route import router as api_router
from app.api.auth_route import router as auth_router
from app.config import FIREBASE_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log the API key (masked for security)
if FIREBASE_API_KEY:
    logger.info(f"Firebase API Key loaded: {FIREBASE_API_KEY[:5]}...")
else:
    logger.error("Firebase API Key not found!")

# Create FastAPI app
app = FastAPI(
    title="Klyptik API",
    description="API for generating quiz questions using AI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)
app.include_router(auth_router)

@app.on_event("startup")
async def startup_event():
    """
    Load the model on startup
    """
    load_model()

@app.get("/")
def read_root():
    """
    Root endpoint
    """
    return {"message": "Welcome to Klyptik API"} 