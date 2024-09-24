import os
import json
import base64
import openai
from dotenv import load_dotenv
from prep_file import combine_json, context_directory, extract_text_content

load_dotenv()

def gpt_api(prompt, file_path=None, context_dir=None, model_name='mini', max_tokens=500):
    print(f"GPT API called with prompt: {prompt[:100]}...")
    print(f"File path: {file_path}")
    print(f"Context directory: {context_dir}")
    
    # Map short names to full model names
    model_name_mapping = {
        'mini': 'gpt-4o-mini',
        'gpt': 'gpt-4o'
    }
    full_model_name = model_name_mapping.get(model_name, 'gpt-4o-mini')
    
    # Configure the API and initialize the model
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
    all_image_urls = file_image_urls + context_image_urls

    # Combine into messages
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    if context_content:
        messages.append({"role": "user", "content": [{"type": "text", "text": f"Context: {context_content}"}]})
    if text_content:
        messages.append({"role": "user", "content": [{"type": "text", "text": f"File content: {text_content}"}]})

    for image_url in all_image_urls:
        try:
            base64_image = encode_image(image_url)
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Image: {os.path.basename(image_url)}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            })
        except FileNotFoundError:
            print(f"Warning: Image file not found at {image_url}")
        except Exception as e:
            print(f"Error opening image {image_url}: {e}")

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
    
# Example usage
# response = gpt_api(
#     prompt="Describe poetically what you see",
#     file_path=r"C:\Users\micah\Downloads\Python Proj\chat_v3\chatbot_v3\context_files\fpsyg-10-00457.pdf",
#     context_dir=None,
#     model_name="mini",
#     max_tokens=500
# )
# if response:
#     print(response)