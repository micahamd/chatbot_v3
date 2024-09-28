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

def gpt_api(prompt, file_path=None, context_dir=None, model_name='mini', max_tokens=500, chat_history_images=None, image_skip=False):
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
            return response.data[0].url
        except Exception as e:
            print(f"Error generating image: {e}")
            return f"Error generating image: {str(e)}"

    json_file = {}
    if file_path:
        json_file = combine_json(file_path, image_skip=image_skip)

    context_json = {}
    if context_dir:
        context_json = context_directory(context_dir, image_skip=image_skip)

    text_content = extract_text_content(json_file) or ''
    context_content = extract_text_content(context_json) or ''

    messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

    if context_content:
        messages.append({"role": "user", "content": [{"type": "text", "text": f"Context: {context_content}"}]})
    if text_content:
        messages.append({"role": "user", "content": [{"type": "text", "text": f"File content: {text_content}"}]})

    # Prepare the content for the final message
    final_content = [{"type": "text", "text": prompt}]

    image_summaries = ""
    if not image_skip:
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
            try:
                if image_url.startswith('file://'):
                    # Local file
                    image_path = Path(image_url[7:])  # Remove 'file://' prefix
                    if image_path.exists():
                        with open(image_path, "rb") as image_file:
                            image_data = base64.b64encode(image_file.read()).decode('utf-8')
                        final_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}",
                                "detail": "auto"
                            }
                        })
                        print(f"Successfully processed image: {image_url}")
                    else:
                        print(f"Image file not found: {image_url}")
                else:
                    # Remote URL
                    final_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                            "detail": "auto"
                        }
                    })
                    print(f"Successfully processed image: {image_url}")
            except Exception as e:
                print(f"Error processing image {image_url}: {str(e)}")

                # Process images and generate summaries
                image_summary_messages = [
                    {"role": "system", "content": "You are a helpful assistant. Describe each image in 50 words or less."}
                ]

                for image_content in final_content[1:]:  # Skip the first element which is the text content
                    image_summary_messages.append({"role": "user", "content": [image_content]})

                try:
                    image_summary_response = client.chat.completions.create(
                        model=full_model_name,
                        messages=image_summary_messages,
                        max_tokens=max_tokens
                    )
                    image_summaries = image_summary_response.choices[0].message.content
                except Exception as e:
                    print(f"Error generating image summaries: {e}")
                    image_summaries = f"Error generating image summaries: {str(e)}"
                        # Generate content summary without images
            content_summary_messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": [{"type": "text", "text": f"{context_content}\n\n{text_content}\n\n{prompt}"}]}
            ]

        # Add chat history images
        if chat_history_images:
            for image in chat_history_images:
                try:
                    if isinstance(image, str):  # It's a URL
                        final_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": image,
                                "detail": "auto"
                            }
                        })
                    else:  # It's a PIL Image object
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
                    print(f"Successfully processed chat history image")
                except Exception as e:
                    print(f"Error processing chat history image: {str(e)}")

    messages.append({"role": "user", "content": final_content})

    print(f"Number of messages: {len(messages)}")
    print(f"Number of images processed: {len(final_content) - 1}")  # Subtract 1 for the text content

    try:
        content_summary_response = client.chat.completions.create(
            model=full_model_name,
            messages=content_summary_messages,
            max_tokens=max_tokens
        )
        content_summary = content_summary_response.choices[0].message.content
        return image_summaries, content_summary
    except Exception as e:
        error_msg = f"Error generating content summary: {e}"
        print(error_msg)
        return "", error_msg