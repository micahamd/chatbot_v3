import ollama
from typing import Optional, List, Dict
from prep_file import combine_json, context_directory, extract_text_content, extract_image_directory_from_json
from pathlib import Path
from ollama import generate
import base64
import json

def ollama_api(prompt: str, file_path: Optional[str] = None, context_dir: Optional[str] = None, model_name: str = 'llama2', max_tokens: int = 1000, chat_history_images: Optional[List] = None, chat_history: Optional[str] = None, image_skip: bool = False) -> tuple[str, str]:
    print(f"Ollama API called with prompt: {prompt[:100]}...")
    print(f"File path: {file_path}")
    print(f"Context directory: {context_dir}")
    print(f"Model name: {model_name}")
    print(f"Image skip: {image_skip}")

    # Model name mapping
    model_name_mapping = {
        'llama3.1': 'mannix/llama3.1-8b-abliterated:latest',
        'llama3.2': 'llama3.2',
        'minicpm': 'minicpm-v:latest',
        'codestral': 'codestral:latest',
        'phi3': 'phi3.5:latest',
        'mistral-nemo': 'mistral-nemo:latest',
        'qwen-2.5': 'qwen2.5:7b-instruct-q8_0 '
    }
    full_model_name = model_name_mapping.get(model_name, model_name)

    def process_image(img_path):
        try:
            with open(img_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            print(f"Error processing image {img_path}: {str(e)}")
            return None

    # Process file content
    file_content = ""
    if file_path:
        try:
            json_file = combine_json(file_path, image_skip=image_skip)
            file_content = extract_text_content(json_file)
            print(f"Extracted file content (first 500 chars): {file_content[:500]}")
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")

    # Process context directory
    context_content = ""
    if context_dir:
        try:
            context_json = context_directory(context_dir, image_skip=image_skip)
            context_content = extract_text_content(context_json)
            print(f"Extracted context content (first 500 chars): {context_content[:500]}")
        except Exception as e:
            print(f"Error processing context directory {context_dir}: {str(e)}")

    # Process images only if not skipping
    image_descriptions = []
    if not image_skip:
        all_images = []
        
        # Collect images from file
        if file_path:
            img_dir = extract_image_directory_from_json(json_file)
            if img_dir:
                all_images.extend(list(img_dir.glob("*.png")))
        
        # Collect images from context
        if context_dir:
            for file_json in context_json.values():
                img_dir = extract_image_directory_from_json(file_json)
                if img_dir:
                    all_images.extend(list(img_dir.glob("*.png")))
        
        # Add chat history images
        if chat_history_images:
            all_images.extend(chat_history_images)
        
        print(f"Total images to process: {len(all_images)}")
        
        # Process images
        for img_path in all_images:
            try:
                img_data = process_image(img_path)
                if img_data:
                    img_response = ollama.chat(model='minicpm-v:latest', messages=[
                        {'role': 'user', 'content': "Describe this image in 50 words or less:", 'images': [img_data]}
                    ])
                    description = f"Image {getattr(img_path, 'name', 'chat history image')}:\n{img_response['message']['content']}"
                    image_descriptions.append(description)
                    print(description)
                else:
                    print(f"Skipping image {img_path} due to processing error")
            except Exception as e:
                error_msg = f"Error processing image {img_path}: {str(e)}"
                print(error_msg)
                image_descriptions.append(error_msg)
    
    # Combine image descriptions
    image_summaries = "\n\n".join(image_descriptions) if image_descriptions else ""

    # Combine all content
    messages = [{'role': 'system', 'content': "You are a helpful assistant."}]
    
    # Add text content (context and file content)
    text_content_parts = []
    if context_content:
        text_content_parts.append(f"Context: {context_content}")
    if file_content:
        text_content_parts.append(f"File content: {file_content}")
    
    if text_content_parts:
        messages.append({'role': 'user', 'content': "\n\n".join(text_content_parts)})
    
    # Add image summaries
    if image_summaries:
        messages.append({'role': 'user', 'content': f"Image summaries:\n\n{image_summaries}"})
    
    # Process chat history
    if chat_history:
        try:
            chat_history_messages = json.loads(chat_history)
            if isinstance(chat_history_messages, list):
                messages.extend(chat_history_messages)
            else:
                print("Chat history is not in the expected format. Skipping.")
        except json.JSONDecodeError:
            print("Failed to parse chat history as JSON. Adding as plain text.")
            messages.append({'role': 'user', 'content': f"Chat history: {chat_history}"})
    
    # Add the user's prompt
    messages.append({'role': 'user', 'content': f"User query: {prompt}"})

    print(f"Number of messages: {len(messages)}")

    # Flatten the prompt to utilize ollama's generate function
    flattened_prompt = "\n\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in messages])

    print(f"Flattened prompt length: {len(flattened_prompt)}")

    try:
        response = generate(
            model=full_model_name,
            prompt=flattened_prompt,
            options={
                'num_predict': max_tokens,
                'temperature': 0.4,  
            }
        )
        content_summary = response['response']
        print(f"Final response: {content_summary[:500]}...")  # Print first 500 chars of the response
        return image_summaries, content_summary
    except Exception as e:
        error_msg = f"Error in Ollama API call: {str(e)}"
        print(error_msg)
        return "", error_msg


# Chat function
#    try:
#        response = ollama.chat(
#            model=full_model_name,
#            messages=messages,
#            options={
#                'num_predict': max_tokens,
#                'temperature': 0.4,  # You can adjust this or make it a parameter
#            }
#        )
#        content_summary = response['message']['content']
#        print(f"Final response: {content_summary}")
#        return image_summaries, content_summary
#    except Exception as e:
#        error_msg = f"Error in Ollama API call: {str(e)}"
#        print(error_msg)
#        return "", error_msg