import os
import json
import base64
import openai
from dotenv import load_dotenv
from prep_file import combine_json, context_directory, extract_text_content
from PIL import Image
import io

load_dotenv()

def gpt_api(prompt, file_path=None, context_dir=None, model_name='mini', max_tokens=500, chat_history_images=None, current_image=None):
    print(f"GPT API called with prompt: {prompt[:100]}...")
    print(f"File path: {file_path}")
    print(f"Context directory: {context_dir}")
    print(f"Model name: {model_name}") 
    
    # Map short names to full model names
    model_name_mapping = {
        'mini': 'gpt-4-vision-preview',  # Use vision-capable model
        'gpt': 'gpt-4-vision-preview',
        'dall-e-3': 'dall-e-3',
    }
    full_model_name = model_name_mapping.get(model_name, model_name)
    print(f"Full model name: {full_model_name}")

    # Handle DALL-E image generation
    if full_model_name == 'dall-e-3':
        try:
            response = openai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            return response.data[0].url
        except Exception as e:
            print(f"Error generating image: {e}")
            return f"Error generating image: {str(e)}"
    
    # Configure the API
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    openai.api_key = api_key

    # Prepare JSON file if file_path is provided
    json_file = {}
    if file_path:
        json_file = combine_json(file_path, image_skip=False)

    # Prepare context JSON if context_dir is provided
    context_json = {}
    if context_dir:
        context_json = context_directory(context_dir, image_skip=False)

    # Image extraction method
    def extract_image_urls(json_data):
        image_urls = []
        if isinstance(json_data, dict):
            images = json_data.get('image_JSON', {}).get('images', [])
            for image_info in images:
                image_path = image_info.get('url', '').replace('file:///', '')
                image_urls.append(image_path)
        elif isinstance(json_data, dict):
            for file_data in json_data.values():
                image_urls.extend(extract_image_urls(file_data))
        return image_urls

    # Image encoding method
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    # Extract text content and image URLs
    text_content = extract_text_content(json_file)
    context_content = extract_text_content(context_json)
    file_image_urls = extract_image_urls(json_file)
    context_image_urls = extract_image_urls(context_json)
    
    # Combine all image URLs and add chat history images
    all_image_urls = file_image_urls + context_image_urls
    if chat_history_images:
        all_image_urls.extend(chat_history_images)

    # Combine into messages
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    if context_content:
        messages.append({"role": "user", "content": [{"type": "text", "text": f"Context: {context_content}"}]})
    if text_content:
        messages.append({"role": "user", "content": [{"type": "text", "text": f"File content: {text_content}"}]})

    for image_url in all_image_urls:
        try:
            if isinstance(image_url, str):  # It's a file path
                base64_image = encode_image(image_url)
                image_content = f"data:image/jpeg;base64,{base64_image}"
            else:  # It's already a base64 encoded string
                image_content = image_url
            
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": "Image:"},
                    {"type": "image_url", "image_url": {"url": image_content}}
                ]
            })
        except Exception as e:
            print(f"Error processing image: {e}")

    # Add the current image if provided
    if current_image:
        if isinstance(current_image, str):
            if current_image.startswith(('http://', 'https://')):
                # It's a URL
                image_content = {"type": "image_url", "image_url": {"url": current_image}}
            else:
                # It's a file path
                with open(current_image, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                image_content = {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        elif isinstance(current_image, Image.Image):
            # It's a PIL Image object
            buffered = io.BytesIO()
            current_image.save(buffered, format="PNG")
            base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
            image_content = {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
        else:
            raise ValueError("Unsupported image type")

        messages.append({"role": "user", "content": [
            {"type": "text", "text": "Here's an image:"},
            image_content
        ]})

    # Add the prompt to the messages
    messages.append({"role": "user", "content": [{"type": "text", "text": prompt}]})

    print(f"Number of messages: {len(messages)}")
    print(f"Number of images processed: {len(all_image_urls)}")

    # Generate content using the OpenAI model
    try:
        response = openai.chat.completions.create(
            model=full_model_name,
            messages=messages,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating content: {e}")
        return None