import requests
import os
from dotenv import load_dotenv
load_dotenv()

# OpenAI API Key
api_key = os.getenv("OPEN_AI_API_KEY")
import requests

def query_openai_with_image(base64_image, model="gpt-4o", max_tokens=300):
    """
    Queries the OpenAI API with an image in base64 encoding.
    
    Args:
    - base64_image (str): The base64-encoded image string.
    - model (str): The model to use for the API call. Default is "gpt-4o".
    - max_tokens (int): The maximum number of tokens for the response. Default is 300.
    
    Returns:
    - dict: The JSON response from the OpenAI API.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "response_format":{ "type": "json_object" },
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Please process this image and output the following JSON: 
                        "data": {
                        "type": "object",
                        "properties": {
                            "idNumber": {
                            "type": "string"
                            },
                            "name": {
                            "type": "string"
                            },
                            "birthdate": {
                            "type": "string"
                            },
                            "sex": {
                            "type": "string"
                            },
                            "address": {
                            "type": "string"
                            }
                        },
                        "required": ["idNumber", "name", "birthdate", "sex", "address"]
                        },
                        "checks": {
                        "type": "object",
                        "properties": {
                            "expired": {
                            "type": "boolean"
                            },
                            "electronicReplica": {
                            "type": "boolean"
                            },
                            "fabrication": {
                            "type": "boolean"
                            },
                            "portraitClarity": {
                            "type": "boolean"
                            },
                            "idImageTampering": {
                            "type": "boolean"
                            },
                            "validDates": {
                            "type": "boolean"
                            },
                            "paperDetection": {
                            "type": "boolean"
                            }
                        }
                        """
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": max_tokens
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    return response.json()

