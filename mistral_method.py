from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import os
import json
from prep_file import combine_json, extract_text_content, context_directory

def mistral_api(prompt, file_path=None, context_dir=None, model_name='nemo', max_tokens=500):
    print(f"Mistral API called with prompt: {prompt[:100]}...")
    print(f"File path: {file_path}")
    print(f"Context directory: {context_dir}")
    
    # Model configuration
    model_name_mapping = {
        'nemo': 'open-mistral-nemo',
        'large': 'mistral-large-latest',
        'codestral': 'codestral-latest',
        'mamba': 'open-codestral-mamba'
    }
    full_model_name = model_name_mapping.get(model_name, 'open-mistral-nemo')
    
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable not set")
    client = MistralClient(api_key=api_key)

    # Process context directory
    context_content = ""
    if context_dir:
        print("Processing context_dir")
        context_json_file = context_directory(context_dir, image_skip=True, use_cache=True)
        print(f"Context JSON file keys: {list(context_json_file.keys())}")
        context_content = extract_text_content(context_json_file)

    # Process file path
    file_content = ""
    if file_path:
        json_file = combine_json(file_path, image_skip=True)
        file_content = extract_text_content(json_file)

    # Combine content
    message_content = f"Context: {context_content}\nFile: {file_content}".strip()
    print(f"Final message_content: {message_content[:500]}...")

    # Construct message and generate response
    msg_content = f"Prompt: [ {prompt} ], Content: [ {message_content} ]"
    messages = [ChatMessage(role="user", content=msg_content)]
    
    chat_response = client.chat(
        model=full_model_name,
        messages=messages,
        temperature=0.3,
        safe_prompt=False,
        max_tokens=max_tokens
    )

    return chat_response.choices[0].message.content

