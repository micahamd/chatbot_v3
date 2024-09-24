import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configure the API and initialize the model
api_key = os.getenv("IDEOGRAM_API_KEY")
if not api_key:
    raise ValueError("IDEOGRAM_API_KEY environment variable not set")

url = "https://api.ideogram.ai/generate"

payload = { "image_request": {
        "prompt": "Illustrate a normal t-distribution for a statistics class. Clearly mark out the 2.5 and 97.5 quantiles using text labels. The distribution should be centered at 0 and have a standard deviation of 1.",
        "aspect_ratio": "ASPECT_1_1", 
        "model": "V1_TURBO", # V1, V2, V2_TURBO
        "magic_prompt_option": "AUTO", # ON, OFF
    } }
headers = {
    "Api-Key": api_key,
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())