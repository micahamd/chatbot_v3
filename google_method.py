from dotenv import load_dotenv
import google.generativeai as genai
import glob
import os
import json
from PIL import Image
from prep_file import combine_json, context_directory, batch_directory
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value
from google.generativeai.types import HarmCategory, HarmBlockThreshold

load_dotenv()  # Make sure to actually call the function

# Set parameters
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not set")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')
generation_config = {
    "temperature": 0.3,
    "top_p": 0.95,
    "top_k": 60,
    "max_output_tokens": 500
}

file_path = r"C:\Users\Admin\OneDrive - The University of the South Pacific\Documents\Graduate Students\maria_done\maria.thesis.finaldocx.docx"  
context_dir = r"C:\Users\Admin\OneDrive - The University of the South Pacific\Documents\Graduate Students\maria_done"


### BEGIN METHOD ###

# Text extraction method
def extract_text_content(json_file):
    return json_file.get('text_JSON', {}).get('content', {}).get('text', '')

# Begin method
# Prepare JSON file if file_path is provided
json_file = {}
dumped_json = ""
if file_path:
    json_file = combine_json(file_path, image_skip=False)
    text_content = json.dumps(json_file) # Creates a string representation of the JSON file

# Prepare context JSON if context_dir is provided
context_json = {}
dumped_context_json = ""
if context_dir:
    context_json = context_directory(context_dir, image_skip=False)
    context_content = json.dumps(context_json)

# Extract image paths from JSON and open images
images = []
if 'image_JSON' in json_file and 'images' in json_file['image_JSON']:
    for image_info in json_file['image_JSON']['images']:
        image_path = image_info['url'].replace('file:///', '')
        try:
            image = Image.open(image_path)
            images.append(image)
        except FileNotFoundError:
            print(f"Warning: Image file not found at {image_path}")
        except Exception as e:
            print(f"Error opening image {image_path}: {e}")
            # Attempt to convert the image to a different format
            try:
                with Image.open(image_path) as img:
                    converted_path = image_path + ".png"
                    img.save(converted_path, format="PNG")
                    image = Image.open(converted_path)
                    images.append(image)
                    print(f"Successfully converted and opened image {image_path}")
            except Exception as convert_error:
                print(f"Error converting image {image_path}: {convert_error}")






# Example usage
prompt = "Poetically describe this image"
instructions = "System Instructions: You will receive the text content of a document that had been pre-processed into JSON format for easier understanding. Examine the metadata to derive the structure, function and name of the original document to help guide your response with the user's prompt. You don't have to respond in JSON. You may also receive image paths, which you can use to access the images. Please describe these when available."

# Identify message source
prompt = "User Prompt: " + prompt
instructions = "System Instructions: " + instructions


response = model.generate_content(
    [prompt, instructions, text_content,context_content]+images,
    generation_config=generation_config,
    safety_settings={
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
    }
)


response = model.generate_content(
    [prompt, instructions, text_content,context_content],
    generation_config=generation_config,
    safety_settings={
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
    }
)


print(response.text)
















# IGNORE THE CODE BELOW


def gemini_api(prompt, instructions, file_path=None, context_dir=None, model_name='flash', token_count=500, include_images=True):
    # Map short names to full model names
    model_name_mapping = {
        'flash': 'gemini-1.5-flash',
        'pro': 'gemini-1.5-pro'
    }
    
    # Get the full model name from the mapping
    full_model_name = model_name_mapping.get(model_name, 'gemini-1.5-flash')

    # Configure the API and initialize the model
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(full_model_name)

    generation_config = {
        "temperature": 0.3,
        "top_p": 0.95,
        "top_k": 60,
        "max_output_tokens": token_count
    }

    # Prepare JSON file if file_path is provided
    json_file = {}
    dumped_json = ""
    if file_path:
        json_file = combine_json(file_path, image_skip=False)
        dumped_json = json.dumps(json_file)

    # Prepare context JSON if context_dir is provided
    context_json = {}
    dumped_context_json = ""
    if context_dir:
        context_json = context_directory(context_dir, image_skip=False)
        dumped_context_json = json.dumps(context_json)

    # Extract image paths from JSON and open images
    images = []
    if include_images and 'image_JSON' in json_file and 'images' in json_file['image_JSON']:
        for image_info in json_file['image_JSON']['images']:
            image_path = image_info['url'].replace('file:///', '')
            try:
                image = Image.open(image_path)
                images.append(image)
            except FileNotFoundError:
                print(f"Warning: Image file not found at {image_path}")
            except Exception as e:
                print(f"Error opening image {image_path}: {e}")

    # Generate content using the Gemini model
    try:
        if include_images and context_dir:
            response = model.generate_content(
                [prompt, instructions, dumped_json, dumped_context_json] + images,
                generation_config=generation_config,
                safety_settings="BLOCK_NONE"
            )
        elif include_images and not context_dir:
            response = model.generate_content(
                [prompt, instructions, dumped_json] + images,
                generation_config=generation_config,
                safety_settings="BLOCK_NONE"
            )
        elif not include_images and context_dir:
            response = model.generate_content(
                [prompt, instructions, dumped_json, dumped_context_json],
                generation_config=generation_config,
                safety_settings="BLOCK_NONE"
            )
        else:  # not include_images and not context_dir
            response = model.generate_content(
                [prompt, instructions, dumped_json],
                generation_config=generation_config,
                safety_settings="BLOCK_NONE"
            )
        return response
    except Exception as e:
        print(f"Error generating content: {e}")
        return None
    finally:
        # Close images to free resources
        for image in images:
            image.close()

# Example usage
file_path = r"C:\Users\Admin\OneDrive - The University of the South Pacific\Documents\fig2_heat.png"  # C:\path\to\file
prompt = "Poetically describe this image"
instructions = "You will receive a document in JSON format. Please examine the metadata to derive the structure, function and name of the original document. Please focus on the text content of the JSON to comprehend the document. You don't have to respond in JSON. If you receive any images, please describe these. The metadata for the images can be found in the JSON content."
# # context_dir = r"C:\Users\Admin\Python Projects\chatbot\context_files\test_context"
response = gemini_api(prompt=prompt, instructions=None, file_path=file_path, context_dir=None, model_name='flash', token_count=300, include_images=False)
# if response:
#     print(response.text)
# else:
#     print("Failed to generate content")