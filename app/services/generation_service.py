import json
import logging
import re
from fastapi import HTTPException
import torch

from app.models.model_loader import get_model, get_tokenizer

# Configure logging
logger = logging.getLogger(__name__)

def convert_text_answer_to_letter(question_data):
    """
    Convert a text answer to letter format (A/B/C/D) based on the options array.
    """
    if not isinstance(question_data, dict):
        return question_data
    
    # Check if we have both options and answer
    if 'options' in question_data and 'answer' in question_data and isinstance(question_data['options'], list):
        options = question_data['options']
        answer = question_data['answer']
        
        # Skip conversion if answer is already a letter
        if isinstance(answer, str) and len(answer) == 1 and answer.upper() in ['A', 'B', 'C', 'D']:
            return question_data
        
        # Try to find the answer in the options
        for i, option in enumerate(options):
            # Check for exact match
            if str(option).lower() == str(answer).lower():
                # Convert to letter (A for index 0, B for index 1, etc.)
                letter_answer = chr(65 + i)  # 65 is ASCII for 'A'
                question_data['answer'] = letter_answer
                return question_data
            
            # Check for partial match (e.g., if answer is a longer string that contains the option)
            if isinstance(answer, str) and isinstance(option, str) and option.lower() in answer.lower():
                letter_answer = chr(65 + i)
                question_data['answer'] = letter_answer
                return question_data
        
        # If we can't find a match but answer is a number, treat it as index
        if isinstance(answer, (int, str)) and str(answer).isdigit():
            index = int(str(answer)) - 1  # Convert to 0-based index
            if 0 <= index < len(options):
                letter_answer = chr(65 + index)
                question_data['answer'] = letter_answer
                return question_data
        
        logger.warning(f"Could not convert answer '{answer}' to letter format for question: {question_data.get('question', 'unknown')}")
    
    return question_data

def normalize_answer_keys(data):
    """
    Recursively normalize any answer-related key to 'answer' and convert text answers to letter format.
    """
    answer_keys = {"answer", "correct_answer", "right_answer", "ans", "solution", "correct", "response"}

    if isinstance(data, dict):
        normalized = {}
        for key, value in data.items():
            normalized_key = "answer" if key.lower().strip() in answer_keys else key
            normalized[normalized_key] = normalize_answer_keys(value)
        
        # After normalization, check if this is a question dict with options and answer
        if 'question' in normalized and 'options' in normalized and 'answer' in normalized:
            normalized = convert_text_answer_to_letter(normalized)
            
        return normalized
    elif isinstance(data, list):
        return [normalize_answer_keys(item) for item in data]
    else:
        return data

def extract_json_from_text(text):
    """
    Try multiple approaches to extract valid JSON from text.
    """
    # Method 1: Regex search for JSON object
    match = re.search(r'\{[\s\S]*\}', text, re.DOTALL)
    if match:
        try:
            json_text = match.group(0)
            json.loads(json_text)  # Validate JSON
            return json_text
        except json.JSONDecodeError:
            logger.warning("Found JSON-like object with regex, but it's not valid JSON")
    
    # Method 2: Find first { and last } characters
    json_start = text.find('{')
    if json_start != -1:
        json_end = text.rfind('}')
        if json_end > json_start:
            try:
                json_text = text[json_start:json_end+1]
                json.loads(json_text)  # Validate JSON
                return json_text
            except json.JSONDecodeError:
                logger.warning("Found JSON-like object with bracket matching, but it's not valid JSON")
    
    # Method 3: Balance brackets
    if json_start != -1:
        stack = []
        for i, char in enumerate(text[json_start:]):
            if char == '{':
                stack.append('{')
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack:  # If stack is empty, we found the matching brace
                        try:
                            json_text = text[json_start:json_start+i+1]
                            json.loads(json_text)  # Validate JSON
                            return json_text
                        except json.JSONDecodeError:
                            logger.warning("Found balanced brackets, but content is not valid JSON")
                            break  # Try other methods
    
    # Method 4: Look for quoted strings and build a minimal structure
    try:
        pattern = r'"([^"]*)"'
        quoted_strings = re.findall(pattern, text)
        if quoted_strings:
            # Create a basic quiz structure with the extracted strings
            questions = []
            for i in range(0, len(quoted_strings), 2):
                question = quoted_strings[i]
                answer = quoted_strings[i+1] if i+1 < len(quoted_strings) else ""
                questions.append({"question": question, "answer": answer})
            
            if questions:
                return json.dumps({"quiz": {"questions": questions}})
    except Exception:
        logger.exception("Failed to extract quoted strings")
    
    # If all extraction methods fail, return a minimal valid structure
    return json.dumps({"quiz": {"questions": []}})

def sanitize_json(json_text):
    """
    Try to fix common JSON syntax issues.
    """
    # Replace common problematic patterns
    sanitized = json_text.replace('\\n', '\n')
    sanitized = sanitized.replace('\\"', '"')
    sanitized = sanitized.replace('\\t', '\t')
    
    # Fix trailing commas (common error in JSON)
    sanitized = re.sub(r',\s*([}\]])', r'\1', sanitized)
    
    # Fix missing commas between objects
    sanitized = re.sub(r'}\s*{', '},{', sanitized)
    
    # Fix missing quotes around property names
    sanitized = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', sanitized)
    
    return sanitized

def generate_response(instruction):
    """
    Generate a response using the model and return clean JSON with normalized answer keys.
    Always returns a valid JSON response even if errors occur.
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

        # Multi-stage processing to ensure we get valid JSON
        try:
            # Stage 1: Try to extract JSON
            json_text = extract_json_from_text(output_text)
            
            # Stage 2: Try to parse directly
            try:
                parsed_json = json.loads(json_text)
                logger.info("Successfully parsed JSON directly")
            except json.JSONDecodeError:
                # Stage 3: Sanitize and try again
                sanitized_json = sanitize_json(json_text)
                try:
                    parsed_json = json.loads(sanitized_json)
                    logger.info("Successfully parsed JSON after sanitization")
                except json.JSONDecodeError as e:
                    # If all fails, create a minimal valid JSON with error info
                    logger.warning(f"Failed to parse JSON even after sanitization: {str(e)}")
                    parsed_json = {
                        "quiz": {
                            "title": f"Quiz about {instruction}",
                            "questions": []
                        },
                        "error": f"Could not generate valid JSON: {str(e)}"
                    }
            
            # Normalize answer keys and convert text answers to letter format
            normalized_json = normalize_answer_keys(parsed_json)
            return normalized_json
            
        except Exception as e:
            logger.exception(f"Error processing generated text: {str(e)}")
            # Ensure we always return a valid JSON structure
            return {
                "quiz": {
                    "title": f"Quiz about {instruction}",
                    "questions": []
                },
                "error": f"Error processing generated text: {str(e)}"
            }

    except Exception as e:
        logger.exception(f"Error during generation: {str(e)}")
        # Always return a valid JSON instead of raising an exception
        return {
            "quiz": {
                "title": f"Quiz about {instruction}",
                "questions": []
            },
            "error": f"Error during generation: {str(e)}"
        }
