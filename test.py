import json
import requests
import os
from helpers import encode_image

photo_path = "/Users/sayakmaity/fast-kyc-backend/7407996533_id_document.jpg"

encoded_img = encode_image(photo_path)
api_key = 'sk-proj-jyuGE23nydlWIzuKF04CT3BlbkFJMAIhGviGIh4PdlEnzppZ'
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "gpt-4o",
    "response_format": { "type": "json_object" },
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """Please process this image and output the following in JSON:

                    idNumber (string)
                    name (string)
                    birthdate (string)
                    sex (string)
                    address (string)
                    electronicReplicaOfID (boolean)
                    paperReplicaOfID (boolean)
                    pictureIsClear (boolean)
                    idImageIsTampered (boolean)
                    """
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded_img}"
                    }
                }
            ]
        }
    ],
    "max_tokens": 300
}

response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
result = response.json()

# Process the response here
print(result)

# Update the user's data with the verification results
# This is a placeholder - implement according to your needs
# update_verification_results(account_id, result)

# Parse the outer JSON

# Extract the content field
content_string = result['choices'][0]['message']['content']

# Parse the content field
card_parsed = json.loads(content_string)

# Now you can access the parsed content
print(json.dumps(content_json, indent=2))

# You can also access individual fields, for example:
print(f"Name: {content_json['name']}")
print(f"Birthdate: {content_json['birthdate']}")