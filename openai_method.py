import os
import base64
import io
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv
from prep_file import combine_json, context_directory, extract_text_content
from pathlib import Path

load_dotenv()

def gpt_api(prompt, file_path=None, context_dir=None, model_name='mini', max_tokens=500, chat_history=None, chat_history_images=None, image_skip=False):
    print(f"GPT API called with prompt: {prompt[:100]}...")
    print(f"File path: {file_path}")
    print(f"Context directory: {context_dir}")
    print(f"Model name: {model_name}")
    print(f"Image skip: {image_skip}")
    
    model_name_mapping = {
        'mini': 'gpt-4o-mini',
        'gpt': 'gpt-4o',
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
            return "", response.data[0].url
        except Exception as e:
            print(f"Error generating image: {e}")
            return "", f"Error generating image: {str(e)}"

    json_file = {}
    if file_path:
        json_file = combine_json(file_path, image_skip=image_skip)

    context_json = {}
    if context_dir:
        context_json = context_directory(context_dir, image_skip=image_skip)

    text_content = extract_text_content(json_file) or ''
    context_content = extract_text_content(context_json) or ''

    image_summaries = []
    if not image_skip:
        # Process images and generate summaries
        image_urls = []
        def extract_image_urls(json_data):
            urls = []
            if isinstance(json_data, dict):
                images = json_data.get('image_JSON', {}).get('images', [])
                for image_info in images:
                    image_url = image_info.get('url', '')
                    if image_url:
                        urls.append(image_url)
            elif isinstance(json_data, dict):
                for file_data in json_data.values():
                    urls.extend(extract_image_urls(file_data))
            return urls
    
        image_urls.extend(extract_image_urls(json_file))
        image_urls.extend(extract_image_urls(context_json))
        
        # Process chat history images
        if not image_skip and chat_history_images:
            image_urls.extend(chat_history_images)
    
        for image_url in image_urls:
            try:
                image_content = None
                if image_url.startswith('file://'):
                    image_path = Path(image_url[7:])
                    if image_path.exists():
                        with open(image_path, "rb") as image_file:
                            image_data = base64.b64encode(image_file.read()).decode('utf-8')
                        image_content = {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}",
                                "detail": "auto"
                            }
                        }
                else:
                    image_content = {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                            "detail": "auto"
                        }
                    }
                
                if image_content:
                    image_summary_messages = [
                        {"role": "system", "content": "You are a helpful assistant. Describe the following image in 50 words or less."},
                        {"role": "user", "content": [image_content]}
                    ]
                    
                    image_summary_response = client.chat.completions.create(
                        model=full_model_name,
                        messages=image_summary_messages,
                        max_tokens=max_tokens
                    )
                    summary = image_summary_response.choices[0].message.content
                    image_summaries.append(f"Image {Path(image_url).name}: {summary}")
                    print(f"Successfully processed image: {image_url}")
                else:
                    print(f"Skipped image processing for: {image_url}")
            except Exception as e:
                print(f"Error processing image {image_url}: {str(e)}")
                image_summaries.append(f"Error processing image {Path(image_url).name}: {str(e)}")

    # Generate content summary
    content_summary_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"{context_content}\n\n{text_content}\n\n{prompt}"}
    ]

    # Add chat history to the content summary messages
    if chat_history:
        content_summary_messages.insert(1, {"role": "system", "content": f"Previous conversation: {chat_history}"})

    try:
        content_summary_response = client.chat.completions.create(
            model=full_model_name,
            messages=content_summary_messages,
            max_tokens=max_tokens
        )
        content_summary = content_summary_response.choices[0].message.content
        
        if image_skip:
            return "", content_summary
        else:
            combined_response = f"Image summaries:\n\n{' '.join(image_summaries)}\n\nContent summary:\n\n{content_summary}"
            return combined_response, ""
    except Exception as e:
        error_msg = f"Error generating content summary: {e}"
        print(error_msg)
        return "", error_msg