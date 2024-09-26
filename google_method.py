from dotenv import load_dotenv
import google.generativeai as genai
from pathlib import Path
import os
import PIL.Image
from prep_file import combine_json, context_directory, extract_text_content, extract_image_directory_from_json

load_dotenv()

def gemini_api(prompt, file_path=None, context_dir=None, model_name='flash', max_tokens=500, chat_history_images=None):
    print(f"Gemini API called with prompt: {prompt[:100]}...")
    print(f"File path: {file_path}")
    print(f"Context directory: {context_dir}")
    
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
    context_img_paths = []
    if context_dir:
        print("Processing context_dir")
        context_json_file = context_directory(context_dir, image_skip=False, use_cache=True)
        print(f"Context JSON file keys: {list(context_json_file.keys())}")
        context_content = extract_text_content(context_json_file)
        print(f"Extracted context content length: {len(context_content)}")
        
        # Extract images from context
        for file_json in context_json_file.values():
            img_dir = extract_image_directory_from_json(file_json)
            if img_dir:
                context_img_paths.extend(list(img_dir.glob("*.png")))


    # Process file path
    file_content = ""
    img_paths = []
    if file_path:
        json_file = combine_json(file_path, image_skip=False)
        file_content = extract_text_content(json_file)
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
    
    print(f"Number of images to process: {len(img_paths)}")

    # Combine all image paths
    all_img_paths = img_paths + context_img_paths

    # Add chat history images
    if chat_history_images:
        all_img_paths.extend(chat_history_images)
    
    print(f"Total number of images to process: {len(all_img_paths)}")
    
    # Generate content
    if all_img_paths:
        responses = []
        for image in all_img_paths:
            print(f"Processing image: {getattr(image, 'name', 'chat history image')}")
            if isinstance(image, str):  # It's a file path
                img = PIL.Image.open(image)
            else:  # It's already a PIL.Image object
                img = image
            response = model.generate_content([prompt, message_content, img] if message_content else [prompt, img])
            responses.append(f"Response for {getattr(image, 'name', 'chat history image')}:\n{response.text}")
        return "\n\n".join(responses)
    else:
        response = model.generate_content([prompt, message_content] if message_content else [prompt])
        return response.text

# Example usage
# response = gemini_api(
#     prompt="Describe this article poetically",
#     file_path=None,
#     context_dir=r"C:\Users\micah\Downloads\Python Proj\chat_v3\chatbot_v3\context_files",
#     model_name="gemini-1.5-flash",
#     max_tokens=1000
# )
# print(response)
