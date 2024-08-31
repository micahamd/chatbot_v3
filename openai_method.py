import os
import json
import base64
import openai
from dotenv import load_dotenv
from prep_file import combine_json, context_directory, batch_directory

load_dotenv()

def openai_method(prompt, instructions, file_path=None, context_dir=None, model_name='mini', token_count=500, include_images=True):
    # Map short names to full model names
    model_name_mapping = {
        'mini': 'gpt-4o-mini',
        'gpt': 'gpt-4o'
    }

    # Get the full model name from the mapping
    full_model_name = model_name_mapping.get(model_name, 'gpt-4o-mini')
    
    # Configure the API and initialize the model
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("WARNING: OPENAI_API_KEY environment variable not set. OpenAI API will not be available.")
        return None

    openai.api_key = api_key

    # Prepare JSON file if file_path is provided
    json_file = {}
    if file_path:
        json_file = combine_json(file_path, image_skip=False)

    # Prepare context JSON if context_dir is provided
    context_json = {}
    if context_dir:
        context_json = context_directory(context_dir, image_skip=False)

    # Text extraction method
    def extract_text_content(json_file):
        return json_file.get('text_JSON', {}).get('content', {}).get('text', '')

    # Image extraction method
    def extract_image_urls(json_file):
        image_urls = []
        images = json_file.get('image_JSON', {}).get('images', [])
        for image_info in images:
            image_path = image_info.get('url', '').replace('file:///', '')
            image_urls.append(image_path)
        return image_urls

    # Image encoding method
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    # Extract text content and image URLs
    text_content = extract_text_content(json_file)
    image_urls = extract_image_urls(json_file)

    # Combine into messages
    messages = [{"role": "system", "content": instructions}]
    if text_content:
        messages.append({"role": "user", 
                         "content": [
                             {"type": "text", 
                              "text": text_content}
                         ]})

    if include_images:
        for image_url in image_urls:
            try:
                base64_image = encode_image(image_url)
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", 
                         "text": f"Context image: {os.path.basename(image_url)}"},
                        {"type": "image_url", 
                         "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                })
            except FileNotFoundError:
                print(f"Warning: Image file not found at {image_url}")
            except Exception as e:
                print(f"Error opening image {image_url}: {e}")

    # Add the prompt to the messages
    messages.append({"role": "user", "content": [{"type": "text", "text": prompt}]})

    # Generate content using the OpenAI model
    try:
        response = openai.chat.completions.create(
            model=full_model_name,
            messages=messages,
            max_tokens=token_count
        )
        return response
    except Exception as e:
        print(f"Error generating content: {e}")
        return None

# Example usage
# prompt = "Please summarize this"
# instructions = "You may receive JSON documents with image URLs. Please focus on the 'content' section of the JSON to comprehend the document. Don't respond in JSON."
# file_path = r"C:\Users\Admin\OneDrive - The University of the South Pacific\Documents\cfs-crafter.pdf"
# response = openai_method(prompt, instructions, file_path=file_path, include_images=False)
# if response:
#     print(response.choices[0].message.content)
# else:
#     print("Failed to generate response from OpenAI API.")
