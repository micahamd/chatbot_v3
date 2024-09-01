from dotenv import load_dotenv
import google.generativeai as genai
from pathlib import Path
from urllib.parse import urlparse
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

# 3. Generate content (text only)
# prompt = "Describe a fire engine poetically"
# response = model.generate_content([prompt])
# print(response.text)

# 4a. With Single Image File processing
# image_path = Path(r"C:\Users\Admin\Pictures\micah_2024.jpg")
# image_part = {
#     "mime_type": "image/jpg",
#     "data": image_path.read_bytes()
# }
# prompt_parts = [
#      "Describe this image:\n",
#      image_part
# ]
# response = model.generate_content(prompt_parts)
# print(response.text)

# 4b. With Multiple Image File processing

# img1 = PIL.Image.open(r"C:\Users\Admin\Pictures\micah_2024.jpg")
# img2 = PIL.Image.open(r"C:\Users\Admin\Pictures\micah_2024.jpg")
# 
# # List of images
# images = [img1, img2]
# 
# # Process each image sequentially
# for img in images:
#     response = model.generate_content([img])
#     print(response.text)


# 4c. With Image Directory processing

# image_directory = Path(r"C:\Users\Admin\Pictures\image_dir_test")
# for image_path in image_directory.glob("*.jpg"):
#     # Open the image
#     img = PIL.Image.open(image_path)
#     
#     # Generate content using the model API
#     response = model.generate_content([img])
#     
#     # Print the response
#     print(f"Description for {image_path.name}:\n{response.text}\n")


# 5. with JSON files 
def extract_text_content(json_file):
    return json_file.get('text_JSON', {}).get('content', {}).get('text', '')

def extract_image_paths(json_file):
    images = json_file.get('image_JSON', {}).get('images', [])
    return [image.get('url', '') for image in images]

def extract_common_directory(image_urls):
    if not image_urls:
        return None
    
    # Parse the first URL to get the path
    parsed_url = urlparse(image_urls[0])
    image_path = Path(parsed_url.path)
    
    # Return the directory containing the images
    return image_path.parent


file_path = r"C:\Users\Admin\Python Projects\chatbot\context_files\pdf_test\Amd, 2023_sub_selfesteem.pdf"  # C:\path\to\file
prompt = "Describe what you see poetically"
instructions = "You will receive documents that have been pre-processed into JSON and dumped into a single string. Please refer to the content when responding."
context_dir = r"C:\Users\Admin\Pictures\image_dir_test"

# Extract JSON files
json_file = combine_json(file_path, image_skip=True)
text_content = extract_text_content(json_file)
img_paths = extract_image_paths(json_file)
img_dir = extract_common_directory(img_paths)

# Image and text processing
for image_path in img_dir.glob("*.png"):
    # Open the image
    img = PIL.Image.open(image_path)
    
    # Generate content using the model API
    response = model.generate_content([img])
    
    # Print the response
    print(f"Description for {image_path.name}:\n{response.text}\n")

# 
# 
# # Process JSON files (text only)
# if file_path and context_dir:
#    json_file = combine_json(file_path, image_skip=True)
#    text_content = extract_text_content(json_file)
#    context_json_file = context_directory(context_dir, image_skip=True)
#    context_text_content = extract_text_content(context_json_file)
#    message_content = "File:[ " + text_content + "], Context files: [" + context_text_content + "]"
# 
# elif file_path and not context_dir:
#    json_file = combine_json(file_path, image_skip=True)
#    text_content = extract_text_content(json_file)
#    message_content = "File: [" + text_content + "]"
# 
# elif context_dir and not file_path:
#     context_json_file = context_directory(context_dir, image_skip=True)
#     context_text_content = json.dumps(context_json_file)
#     message_content = "Context files: [" + context_text_content + "]"
# 
# else:
#     message_content = "None."
# 
# # Construct message
# if file_path or context_dir:
#     msg_content = "Prompt: [" + prompt + "], Dumped JSON documents: [" + message_content + "]"
# else:
#     msg_content = "Prompt: [" + prompt + "]"
# 
# # Send to model
# response = model.generate_content([msg_content])
# print(response.text)
