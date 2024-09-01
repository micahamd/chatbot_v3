from dotenv import load_dotenv
import google.generativeai as genai
from pathlib import Path
from urllib.parse import urlparse
import glob
import os
import json
import PIL.Image
from prep_file import combine_json, context_directory, batch_directory
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value
from google.generativeai.types import HarmCategory, HarmBlockThreshold

load_dotenv()  # Make sure to actually call the function

# 1. Configuration
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
generation_config = {"temperature": 0.3,"top_p": 0.95,"top_k": 60,"max_output_tokens": 500}

# 2. Initialize the model
model = genai.GenerativeModel('gemini-1.5-flash', generation_config=generation_config)


# 6. Extract Images created temporarily and linked within the JSON files 
def extract_text_content(json_file):
    return json_file.get('text_JSON', {}).get('content', {}).get('text', '')

def extract_image_directory_from_json(json_file):
    images = json_file.get('image_JSON', {}).get('images', [])
    image_urls = [image.get('url', '') for image in images]
    
    if not image_urls:
        return None
    
    # Parse the first URL to get the path
    parsed_url = urlparse(image_urls[0])
    image_path = Path(parsed_url.path.lstrip('/'))  # Remove leading slash
    
    # Return the directory containing the images
    return image_path.parent

file_path = r"C:\Users\Admin\Python Projects\chatbot\context_files\pdf_test\Amd, 2023_sub_selfesteem.pdf"  # C:\path\to\file
prompt = "Describe what you see poetically"
context_dir = r"C:\Users\Admin\Pictures\image_dir_test"

message_content = ""

if file_path and context_dir:
    json_file = combine_json(file_path, image_skip=False)
    text_content = extract_text_content(json_file)
    context_json_file = context_directory(context_dir, image_skip=True)
    context_text_content = extract_text_content(context_json_file)
    message_content = "File content: [ " + text_content + "], Context files in JSON: [" + context_text_content + "]"
elif file_path and not context_dir:
    json_file = combine_json(file_path, image_skip=False)
    text_content = extract_text_content(json_file)
    message_content = "File: [" + text_content + "]"
elif context_dir and not file_path:
    context_json_file = context_directory(context_dir, image_skip=True)
    context_text_content = json.dumps(context_json_file)
    message_content = "Context files in JSON: [" + context_text_content + "]"
else:
    message_content = "No additional files."

# Test
# response = model.generate_content([prompt, message_content])
# print(response.text)


img_dir = extract_image_directory_from_json(json_file)

include_images = False  # Set to True to include images in the prompt

chat_history = []  # Initialize a list to store the descriptions
if include_images:
    for image_path in img_dir.glob("*.png"):  # Iterate over all PNG files in the directory
        img = PIL.Image.open(image_path)
        response = model.generate_content([prompt, message_content, img])
        description = f"Response: {image_path.name}:\n{response.text}\n"
        print(description)
        chat_history.append(description)  # Append the description to the list
else:
        response = model.generate_content([prompt, message_content])
        description = f"Response: {response.text}\n"
        print(description)
        chat_history.append(description)  # Append the description to the list

