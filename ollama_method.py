import ollama
from typing import Optional, List
from prep_file import combine_json, context_directory, extract_text_content, extract_image_directory_from_json
from pathlib import Path
import base64

def ollama_api(prompt: str, file_path: Optional[str] = None, context_dir: Optional[str] = None, model_name: str = 'mannix/llama3.1-8b-abliterated:latest', max_tokens: int = 1000, chat_history_images: Optional[List] = None) -> str:
    print(f"Ollama API called with prompt: {prompt[:100]}...")
    print(f"File path: {file_path}")
    print(f"Context directory: {context_dir}")
    print(f"Model name: {model_name}")

    def process_image(img_path):
        try:
            with open(img_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            print(f"Error processing image {img_path}: {str(e)}")
            return None

    # Process file content
    file_content = ""
    file_images = []
    if file_path:
        try:
            json_file = combine_json(file_path, image_skip=False)
            file_content = extract_text_content(json_file)
            print(f"Extracted file content (first 500 chars): {file_content[:500]}")
            img_dir = extract_image_directory_from_json(json_file)
            if img_dir:
                file_images = list(img_dir.glob("*.png"))
                print(f"Found {len(file_images)} images in the file")
            else:
                print("No image directory found in the file")
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")

    # Process context directory
    context_content = ""
    context_images = []
    if context_dir:
        try:
            context_json = context_directory(context_dir, image_skip=False)
            context_content = extract_text_content(context_json)
            print(f"Extracted context content (first 500 chars): {context_content[:500]}")
            for file_json in context_json.values():
                img_dir = extract_image_directory_from_json(file_json)
                if img_dir:
                    context_images.extend(list(img_dir.glob("*.png")))
            print(f"Found {len(context_images)} images in the context directory")
        except Exception as e:
            print(f"Error processing context directory {context_dir}: {str(e)}")

    # Combine all images
    all_images = file_images + context_images
    if chat_history_images:
        all_images.extend(chat_history_images)
    print(f"Total images to process: {len(all_images)}")

    # Process images with minicpm-v:latest and collect responses
    image_descriptions = []
    for img_path in all_images:
        try:
            img_data = process_image(img_path)
            if img_data:
                img_response = ollama.chat(model='minicpm-v:latest', messages=[
                    {'role': 'user', 'content': "Describe this image in detail:", 'images': [img_data]}
                ])
                description = f"Image {img_path.name}: {img_response['message']['content']}"
                image_descriptions.append(description)
                print(description)  # Output each image description as it's generated
            else:
                print(f"Skipping image {img_path} due to processing error")
        except Exception as e:
            error_msg = f"Error processing image {img_path}: {str(e)}"
            print(error_msg)
            image_descriptions.append(error_msg)

    # Combine all content
    full_content = f"Context: {context_content}\n\nFile: {file_content}\n\n"
    if image_descriptions:
        full_content += "Image Descriptions:\n" + "\n".join(image_descriptions) + "\n\n"
    full_content += f"User: {prompt}"

    print(f"Full content to be sent to the model (first 1000 chars): {full_content[:1000]}")

    try:
        response = ollama.chat(model=model_name, messages=[
            {'role': 'user', 'content': full_content}
        ])
        result = response['message']['content']
        print(f"Final response: {result}")  # Output the final response
        return result
    except Exception as e:
        error_msg = f"Error in Ollama API call: {str(e)}"
        print(error_msg)
        return error_msg

# Example usage
if __name__ == "__main__":
    response = ollama_api(
        prompt="Summarise this for a 5-year old",
        file_path=r"C:\Users\micah\Downloads\fpsyg-10-00457.pdf",
        context_dir=None,
        model_name="mannix/llama3.1-8b-abliterated:latest",
        max_tokens=100
    )
    print(response)