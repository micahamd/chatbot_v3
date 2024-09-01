from dotenv import load_dotenv
import google.generativeai as genai
from pathlib import Path
import os
import PIL.Image
from prep_file import combine_json, context_directory, extract_text_content, extract_image_directory_from_json

load_dotenv()

def gemini_api(prompt, file_path=None, context_dir=None, model_name='flash', max_tokens=500):
         
    # Map short names to full model names
    model_name_mapping = {
        'flash': 'gemini-1.5-flash',
        'pro': 'gemini-1.5-pro'
    }

    # Get the full model name from the mapping
    full_model_name = model_name_mapping.get(model_name, 'gemini-1.5-flash')
           
    # Configuration
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    generation_config = {
        "temperature": 0.3,
        "top_p": 0.95,
        "top_k": 60,
        "max_output_tokens": max_tokens
    }

    # Initialize the model
    model = genai.GenerativeModel(model_name, generation_config=generation_config)

    # Process JSON files
    message_content = ""
    if file_path and context_dir:
        json_file = combine_json(file_path, image_skip=False)
        text_content = extract_text_content(json_file)
        context_json_file = context_directory(context_dir, image_skip=True)
        context_text_content = extract_text_content(context_json_file)
        message_content = f"File content: [ {text_content} ], Context files in JSON: [ {context_text_content} ]"
    elif file_path and not context_dir:
        json_file = combine_json(file_path, image_skip=False)
        text_content = extract_text_content(json_file)
        message_content = f"File: [ {text_content} ]"
    elif context_dir and not file_path:
        context_json_file = context_directory(context_dir, image_skip=True)
        context_text_content = extract_text_content(context_json_file)
        message_content = f"Context files in JSON: [ {context_text_content} ]"
    else:
        message_content = "No additional files."

    # Handle images if present in the file_path
    img_dir = None
    if file_path:
        json_file = combine_json(file_path, image_skip=False)
        img_dir = extract_image_directory_from_json(json_file)

    # Generate content
    if img_dir:
        responses = []
        for image_path in img_dir.glob("*.png"):
            img = PIL.Image.open(image_path)
            response = model.generate_content([prompt, message_content, img])
            responses.append(f"Response for {image_path.name}:\n{response.text}")
        return "\n\n".join(responses)
    else:
        response = model.generate_content([prompt, message_content])
        return response.text

# Example usage
# response = gemini_api(
#     prompt="Describe what you see poetically",
#     file_path=r"C:\Users\Admin\Pictures\image_dir_test\back_sunset_woman_beach.png",
#     context_dir=None,
#     model_name="gemini-1.5-flash",
#     max_tokens=500
# )
# print(response)
