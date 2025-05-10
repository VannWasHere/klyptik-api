from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import logging
import json

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize model and tokenizer as None
model = None
tokenizer = None

def load_model(model_path="VannWasHere/qwen3-tuned-response"):
    global model, tokenizer
    try:
        # Check GPU availability
        if torch.cuda.is_available():
            logger.info(f"GPU is available. Device: {torch.cuda.get_device_name(0)}")
            logger.info(f"CUDA version: {torch.version.cuda}")
        else:
            logger.warning("No GPU available. Model will run on CPU.")
        
        logger.info("Loading model and tokenizer...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Log device placement
        if hasattr(model, 'device'):
            logger.info(f"Model loaded on device: {model.device}")
        else:
            logger.info("Model device placement not explicitly set")
            
        logger.info("Model and tokenizer loaded successfully")
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load model: {str(e)}"
        )

def generate_response(instruction):
    if model is None or tokenizer is None:
        raise HTTPException(
            status_code=500,
            detail="Model not loaded. Please check server logs."
        )
    
    try:
        input_text = f"<|im_start|>user\nGenerate a JSON quiz based on this instruction: {instruction}<|im_end|>"
        
        input_ids = tokenizer(input_text, return_tensors="pt").input_ids.to(model.device)
        
        outputs = model.generate(
            input_ids,
            max_length=1024,
            temperature=0.3,
            top_p=0.9,
            repetition_penalty=1.2,
            do_sample=True,
            num_return_sequences=1,
            pad_token_id=tokenizer.eos_token_id
        )
        
        output_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Clean up the response to only include the JSON content
        if "<|im_start|>assistant" in output_text:
            output_text = output_text.split("<|im_start|>assistant")[-1].strip()
        
        # Find the first occurrence of a JSON object
        json_start = output_text.find('{')
        if json_start != -1:
            output_text = output_text[json_start:]
            
        # Find the last occurrence of a closing brace
        json_end = output_text.rfind('}')
        if json_end != -1:
            output_text = output_text[:json_end + 1]
        
        # Parse and re-format the JSON to ensure clean formatting
        try:
            json_data = json.loads(output_text)
            # Re-format the JSON with proper structure
            formatted_json = {
                "quiz": json_data.get("quiz", {}).get("questions", [])
            }
            return json.dumps(formatted_json, ensure_ascii=False)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate valid JSON response"
            )
            
    except Exception as e:
        logger.error(f"Error during generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error during text generation: {str(e)}"
        )

class AskRequest(BaseModel):
    instruction: str

@app.on_event("startup")
async def startup_event():
    load_model()

@app.post("/ask")
def ask(request: AskRequest):
    response = generate_response(request.instruction)
    try:
        # Parse the JSON string and return it directly
        return json.loads(response)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate valid JSON response"
        )
