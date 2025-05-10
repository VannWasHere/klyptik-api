import json
import logging
from fastapi import HTTPException
import torch

from app.models.model_loader import get_model, get_tokenizer

# Configure logging
logger = logging.getLogger(__name__)

def generate_response(instruction):
    """
    Generate a response using the model
    """
    try:
        model = get_model()
        tokenizer = get_tokenizer()
        
        input_text = f"<|im_start|>user\nGenerate a JSON quiz based on this instruction: {instruction}<|im_end|>"
        
        input_ids = tokenizer(input_text, return_tensors="pt").input_ids.to(model.device)
        
        # Set attention mask explicitly to avoid warning
        attention_mask = torch.ones_like(input_ids)
        
        outputs = model.generate(
            input_ids,
            attention_mask=attention_mask,
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
            # Handle different potential JSON structures
            formatted_json = {"quiz": []}
            
            # Case 1: Direct list of questions
            if isinstance(json_data, list):
                formatted_json["quiz"] = json_data
            # Case 2: Nested under "quiz" > "questions"
            elif isinstance(json_data, dict) and "quiz" in json_data:
                quiz_data = json_data.get("quiz", {})
                if isinstance(quiz_data, dict) and "questions" in quiz_data:
                    formatted_json["quiz"] = quiz_data.get("questions", [])
                elif isinstance(quiz_data, list):
                    formatted_json["quiz"] = quiz_data
            
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