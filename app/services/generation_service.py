import json
import logging
import re
from fastapi import HTTPException
import torch

from app.models.model_loader import get_model, get_tokenizer

# Configure logging
logger = logging.getLogger(__name__)

def generate_response(instruction):
    """
    Generate a response using the model and return clean JSON only
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

        # Extract JSON string using regex
        match = re.search(r'\{.*\}', output_text, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in the generated output.")

        json_text = match.group(0)

        # Parse to confirm it's valid
        parsed_json = json.loads(json_text)

        return parsed_json  # Or json_text if you want raw string output

    except Exception as e:
        logger.error(f"Error during generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error during text generation: {str(e)}"
        )
