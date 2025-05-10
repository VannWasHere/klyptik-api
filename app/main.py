from fastapi import FastAPI
import logging

from app.models.model_loader import load_model
from app.api.route import router as api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Klyptik API",
    description="API for generating quiz questions using AI",
    version="1.0.0"
)

# Include routers
app.include_router(api_router)

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