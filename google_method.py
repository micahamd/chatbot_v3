from dotenv import load_dotenv
import google.generativeai as genai
from pathlib import Path
import os
import PIL.Image
from prep_file import combine_json, context_directory, extract_text_content, extract_image_directory_from_json

load_dotenv()

def gemini_api(prompt, file_path=None, context_dir=None, model_name='flash', max_tokens=500, chat_history=None, chat_history_images=None, image_skip=True):
    print(f"Gemini API called with prompt: {prompt[:100]}...")
    print(f"File path: {file_path}")
    print(f"Context directory: {context_dir}")
    print(f"Image skip: {image_skip}")
    
    # Model configuration
    model_name_mapping = {
        'flash': 'gemini-1.5-flash',
        'pro': 'gemini-1.5-pro'
    }
    full_model_name = model_name_mapping.get(model_name, 'gemini-1.5-flash')
    
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    generation_config = {
        "temperature": 0.3,
        "top_p": 0.95,
        "top_k": 60,
        "max_output_tokens": max_tokens
    }
    model = genai.GenerativeModel(full_model_name, generation_config=generation_config)

    # Process context directory
    context_content = ""
    if context_dir:
        print("Processing context_dir")
        context_json_file = context_directory(context_dir, image_skip=image_skip, use_cache=True)
        print(f"Context JSON file keys: {list(context_json_file.keys())}")
        context_content = extract_text_content(context_json_file)
        print(f"Extracted context content length: {len(context_content)}")

    # Process file path
    file_content = ""
    if file_path:
        json_file = combine_json(file_path, image_skip=image_skip)
        file_content = extract_text_content(json_file)
    
    # Combine content
    message_parts = []
    if context_content:
        message_parts.append(f"Context: {context_content}")
    if file_content:
        message_parts.append(f"File: {file_content}")
    message_content = "\n".join(message_parts).strip()
    if chat_history:
        message_parts.append(f"Chat History: {chat_history}")
    
    if message_content:
        print(f"Final message_content length: {len(message_content)}")
        print(f"Final message_content preview: {message_content[:500]}...")
    else:
        print("No additional content provided.")
    
    # Skip image processing if image_skip is True
    if image_skip:
        print("Image processing skipped.")
        response = model.generate_content([prompt, message_content] if message_content else [prompt])
        return "", response.text
    
    # Process images only if image_skip is False
    print("Processing images...")
    all_img_paths = []
    if file_path:
        img_dir = extract_image_directory_from_json(json_file)
        if img_dir:
            all_img_paths.extend(list(img_dir.glob("*.png")))
    if context_dir:
        for file_json in context_json_file.values():
            img_dir = extract_image_directory_from_json(file_json)
            if img_dir:
                all_img_paths.extend(list(img_dir.glob("*.png")))
    if chat_history_images:
        all_img_paths.extend(chat_history_images)
    
    print(f"Total number of images to process: {len(all_img_paths)}")
    
    image_summaries = []
    if all_img_paths:
        for image in all_img_paths:
            print(f"Processing image: {getattr(image, 'name', 'chat history image')}")
            if isinstance(image, (str, Path)):  # It's a file path or Path object
                img = PIL.Image.open(str(image))
            else:  # It's already a PIL.Image object
                img = image
            response = model.generate_content(["Describe this image in 50 words or less:", img])
            image_summaries.append(f"Image {getattr(image, 'name', 'chat history image')}: {response.text}")

    # Generate content summary
    content_summary = model.generate_content([prompt, message_content] if message_content else [prompt])
    
    return "\n\n".join(image_summaries) if image_summaries else "", content_summary.text
