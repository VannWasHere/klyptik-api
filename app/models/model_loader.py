import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from fastapi import HTTPException
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Initialize model and tokenizer as None
_model = None
_tokenizer = None

def load_model(model_path="VannWasHere/qwen3-tuned-response"):
    """
    Load the model and tokenizer
    """
    global _model, _tokenizer
    try:
        # Check GPU availability
        if torch.cuda.is_available():
            logger.info(f"GPU is available. Device: {torch.cuda.get_device_name(0)}")
            logger.info(f"CUDA version: {torch.version.cuda}")
        else:
            logger.warning("No GPU available. Model will run on CPU.")
        
        logger.info("Loading model and tokenizer...")
        _model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        _tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Log device placement
        if hasattr(_model, 'device'):
            logger.info(f"Model loaded on device: {_model.device}")
        else:
            logger.info("Model device placement not explicitly set")
            
        logger.info("Model and tokenizer loaded successfully")
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load model: {str(e)}"
        )

def get_model():
    """
    Get the loaded model
    """
    global _model
    if _model is None:
        raise HTTPException(
            status_code=500,
            detail="Model not loaded. Please check server logs."
        )
    return _model

def get_tokenizer():
    """
    Get the loaded tokenizer
    """
    global _tokenizer
    if _tokenizer is None:
        raise HTTPException(
            status_code=500,
            detail="Tokenizer not loaded. Please check server logs."
        )
    return _tokenizer 