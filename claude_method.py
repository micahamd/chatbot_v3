from dotenv import load_dotenv
import anthropic
import os
import base64
from PIL import Image
from io import BytesIO
from prep_file import combine_json, context_directory, extract_text_content, extract_image_directory_from_json, image_to_base64
from pathlib import Path

load_dotenv()

def claude_api(prompt, file_path=None, context_dir=None, model_name='claude-3-sonnet-20240220', max_tokens=1000, chat_history_images=None, image_skip=False):
    print(f"Claude API called with prompt: {prompt[:100]}...")
    print(f"File path: {file_path}")
    print(f"Context directory: {context_dir}")
    print(f"Image skip: {image_skip}")
    
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # Process context directory
    context_content = ""
    context_img_paths = []
    if context_dir:
        print("Processing context_dir")
        context_json_file = context_directory(context_dir, image_skip=image_skip, use_cache=True)
        print(f"Context JSON file keys: {list(context_json_file.keys())}")
        context_content = extract_text_content(context_json_file)
        print(f"Extracted context content length: {len(context_content)}")
        
        # Extract images from context if not skipping
        if not image_skip:
            for file_json in context_json_file.values():
                img_dir = extract_image_directory_from_json(file_json)
                if img_dir:
                    context_img_paths.extend(list(img_dir.glob("*.png")))

    # Process file path
    file_content = ""
    img_paths = []
    if file_path:
        json_file = combine_json(file_path, image_skip=image_skip)
        file_content = extract_text_content(json_file)
        if not image_skip:
            img_dir = extract_image_directory_from_json(json_file)
            if img_dir:
                img_paths = list(img_dir.glob("*.png"))
    
    # Combine content
    message_parts = []
    if context_content:
        message_parts.append(f"Context: {context_content}")
    if file_content:
        message_parts.append(f"File: {file_content}")
    message_content = "\n".join(message_parts).strip()
    
    if message_content:
        print(f"Final message_content length: {len(message_content)}")
        print(f"Final message_content preview: {message_content[:500]}...")
    else:
        print("No additional content provided.")
    
    # Combine all image paths if not skipping
    all_img_paths = []
    if not image_skip:
        all_img_paths = img_paths + context_img_paths
        if chat_history_images:
            all_img_paths.extend(chat_history_images)
    
    print(f"Total number of images to process: {len(all_img_paths)}")
    
    # Prepare messages for Claude
    messages = [{"role": "user", "content": []}]
    
    # Add text content
    if message_content:
        messages[0]["content"].append({"type": "text", "text": message_content})
    
    # Add prompt
    messages[0]["content"].append({"type": "text", "text": prompt})
    
    # Add images if not skipping
    if not image_skip:
        for img_path in all_img_paths:
            try:
                if isinstance(img_path, (str, Path)):
                    img_data = image_to_base64(str(img_path))
                else:
                    buffered = BytesIO()
                    img_path.save(buffered, format="PNG")
                    img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                messages[0]["content"].append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_data
                    }
                })
                print(f"Successfully processed image: {getattr(img_path, 'name', 'chat history image')}")
            except Exception as e:
                print(f"Error processing image {img_path}: {str(e)}")
    else:
        print("Image processing skipped.")

    # Generate content
    try:
        response = client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        error_msg = f"Error in Claude API call: {str(e)}"
        print(error_msg)
        return error_msg