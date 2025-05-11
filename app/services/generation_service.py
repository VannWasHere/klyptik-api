import json
import logging
import re
from fastapi import HTTPException
import torch

from app.models.model_loader import get_model, get_tokenizer

# Configure logging
logger = logging.getLogger(__name__)

def normalize_answer_keys(data):
    """
    Recursively normalize any answer-related key to 'answer'.
    Handles variations like 'correct_answer', 'right_answer', 'solution', etc.
    """
    answer_keys = {"answer", "correct_answer", "right_answer", "ans", "solution", "correct", "response"}

    if isinstance(data, dict):
        normalized = {}
        for key, value in data.items():
            normalized_key = "answer" if key.lower().strip() in answer_keys else key
            normalized[normalized_key] = normalize_answer_keys(value)
        return normalized
    elif isinstance(data, list):
        return [normalize_answer_keys(item) for item in data]
    else:
        return data

def generate_response(instruction):
    """
    Generate a response using the model and return clean JSON with normalized answer keys.
    """
    try:
        model = get_model()
        tokenizer = get_tokenizer()

        input_text = f"<|im_start|>user\nGenerate a JSON quiz based on this instruction: {instruction}<|im_end|>"
        input_ids = tokenizer(input_text, return_tensors="pt").input_ids.to(model.device)
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

        # Extract the JSON block
        match = re.search(r'\{.*\}', output_text, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in the generated output.")

        json_text = match.group(0)
        parsed_json = json.loads(json_text)

        # Normalize answer key
        normalized_json = normalize_answer_keys(parsed_json)

        return normalized_json

    except Exception as e:
        logger.error(f"Error during generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error during text generation: {str(e)}"
        )
