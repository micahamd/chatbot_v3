from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import os
import json
from prep_file import combine_json, extract_text_content, context_directory

def mistral_api(prompt, file_path=None, context_dir=None, model_name='nemo', max_tokens=500):
    
    # Map short names to full model names
    model_name_mapping = {
        'nemo': 'open-mistral-nemo',
        'large': 'mistral-large-latest'
    }

    # Get the full model name from the mapping
    full_model_name = model_name_mapping.get(model_name, 'open-mistral-nemo')
           
    # Initialize the client
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable not set")
    client = MistralClient(api_key=api_key)

    # Process JSON files (Mistral can't handle images)
    message_content = ""
    if file_path and context_dir:
        json_file = combine_json(file_path, image_skip=True)
        text_content = extract_text_content(json_file)
        context_json_file = context_directory(context_dir, image_skip=True)
        context_text_content = extract_text_content(context_json_file)
        message_content = f"File: [ {text_content} ], Context files: [ {context_text_content} ]"
    elif file_path and not context_dir:
        json_file = combine_json(file_path, image_skip=True)
        text_content = extract_text_content(json_file)
        message_content = f"File: [ {text_content} ]"
    elif context_dir and not file_path:
        context_json_file = context_directory(context_dir, image_skip=True)
        context_text_content = json.dumps(context_json_file)
        message_content = f"Context files: [ {context_text_content} ]"
    else:
        message_content = "No additional files."

    # Construct message
    msg_content = f"Prompt: [ {prompt} ], Dumped JSON documents: [ {message_content} ]"

    # Construct messages
    messages = [
        ChatMessage(role="user", content=msg_content),
    ]

    # Generate response
    chat_response = client.chat(
        model=model_name,
        messages=messages,
        temperature=0.2,
        safe_prompt=False,
        max_tokens=max_tokens
    )

    return chat_response.choices[0].message.content

# Example usage
# response = mistral_api(
#     prompt="Describe what you see poetically",
#     file_path=r"C:\Users\Admin\Desktop\ANa IQ Paper Review\IQ paper manuscript.docx",
#     context_dir=None,
#     model_name="open-mistral-nemo",
#     max_tokens=500
# )
# print(response)
