import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv
from prep_file import combine_json, context_directory, extract_text_content

load_dotenv()

def gpt_api(prompt, file_path=None, context_dir=None, model_name='mini', max_tokens=500, chat_history_images=None):
    print(f"GPT API called with prompt: {prompt[:100]}...")
    print(f"File path: {file_path}")
    print(f"Context directory: {context_dir}")
    print(f"Model name: {model_name}") 
    
    model_name_mapping = {
        'mini': 'gpt-4-vision-preview',
        'gpt': 'gpt-4-vision-preview',
        'dall-e-3': 'dall-e-3',
    }
    full_model_name = model_name_mapping.get(model_name, model_name)
    print(f"Full model name: {full_model_name}")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    client = OpenAI(api_key=api_key)

    if full_model_name == 'dall-e-3':
        try:
            response = client.images.generate(
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

    json_file = {}
    if file_path:
        json_file = combine_json(file_path, image_skip=False)

    context_json = {}
    if context_dir:
        context_json = context_directory(context_dir, image_skip=False)

    text_content = extract_text_content(json_file)
    context_content = extract_text_content(context_json)

    messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

    if context_content:
        messages.append({"role": "user", "content": [{"type": "text", "text": f"Context: {context_content}"}]})
    if text_content:
        messages.append({"role": "user", "content": [{"type": "text", "text": f"File content: {text_content}"}]})

    # Prepare the content for the final message
    final_content = [{"type": "text", "text": prompt}]

    # Add images from json_file and context_json
    def extract_image_urls(json_data):
        image_urls = []
        if isinstance(json_data, dict):
            images = json_data.get('image_JSON', {}).get('images', [])
            for image_info in images:
                image_url = image_info.get('url', '')
                if image_url:
                    image_urls.append(image_url)
        elif isinstance(json_data, dict):
            for file_data in json_data.values():
                image_urls.extend(extract_image_urls(file_data))
        return image_urls

    all_image_urls = extract_image_urls(json_file) + extract_image_urls(context_json)

    for image_url in all_image_urls:
        final_content.append({
            "type": "image_url",
            "image_url": {
                "url": image_url,
                "detail": "auto"
            }
        })

    # Add chat history images
    if chat_history_images:
        for image in chat_history_images:
            if isinstance(image, str):  # It's a URL
                final_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": image,
                        "detail": "auto"
                    }
                })
            else:  # It's a PIL Image object
                # Convert PIL Image to base64
                import io
                import base64
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                final_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_str}",
                        "detail": "auto"
                    }
                })

    messages.append({"role": "user", "content": final_content})

    print(f"Number of messages: {len(messages)}")
    print(f"Number of images processed: {len(final_content) - 1}")  # Subtract 1 for the text content

    try:
        response = client.chat.completions.create(
            model=full_model_name,
            messages=messages,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating content: {e}")
        return None