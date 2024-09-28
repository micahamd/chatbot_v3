import ollama
from typing import Optional, List
from prep_file import combine_json, context_directory, extract_text_content, extract_image_directory_from_json
import os

def ollama_api(prompt: str, file_path: Optional[str] = None, context_dir: Optional[str] = None, model_name: str = 'phi3.5:latest', max_tokens: int = 1000, chat_history_images: Optional[List] = None) -> str:
    print(f"Ollama API called with prompt: {prompt[:100]}...")
    print(f"File path: {file_path}")
    print(f"Context directory: {context_dir}")
    print(f"Model name: {model_name}")

    # Process file content
    file_content = ""
    file_images = []
    if file_path:
        json_file = combine_json(file_path, image_skip=False)
        file_content = extract_text_content(json_file)
        img_dir = extract_image_directory_from_json(json_file)
        if img_dir:
            file_images = list(img_dir.glob("*.png"))

    # Process context directory
    context_content = ""
    context_images = []
    if context_dir:
        context_json = context_directory(context_dir, image_skip=False)
        context_content = extract_text_content(context_json)
        for file_json in context_json.values():
            img_dir = extract_image_directory_from_json(file_json)
            if img_dir:
                context_images.extend(list(img_dir.glob("*.png")))

    # Combine all images
    all_images = file_images + context_images
    if chat_history_images:
        all_images.extend(chat_history_images)

    # Combine all content
    full_content = f"Context: {context_content}\n\nFile: {file_content}\n\nUser: {prompt}"

    try:
        messages = [{'role': 'user', 'content': full_content}]
        
        # Get the list of available models
        available_models = [model['name'] for model in ollama.list()['models']]
        
        # Process images if the model supports it
        if "minicpm-v" in model_name or any(model.endswith('-vision') for model in available_models):
            for img_path in all_images:
                if isinstance(img_path, str):
                    img_content = img_path
                else:
                    img_content = str(img_path)
                messages.append({'role': 'describe', 'content': img_content})

        response = ollama.chat(model=model_name, messages=messages)
        result = response['message']['content']

        # Clear the model's cache after generating the response
        ollama.chat(model=model_name, messages=[{'role': 'system', 'content': '/clear'}])
        
        return result
    except Exception as e:
        print(f"Error in Ollama API call: {str(e)}")
        return f"Error: {str(e)}"

# Example usage
if __name__ == "__main__":
    response = ollama_api(
        prompt="Did you see this before?",
        file_path=r"C:\Users\micah\Downloads\Python Proj\chat_v3\chatbot_v3\context_files\PS304 Practical Assignment Instructions.docx",
        context_dir=None,
        model_name="mannix/llama3.1-8b-abliterated:latest",
        max_tokens=100
    )
    print(response)