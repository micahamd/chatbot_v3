from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import os
import json
from prep_file import combine_json, extract_text_content,context_directory, batch_directory


api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-large-latest"  # open-mistral-nemo, codestral-latest, mistral-large-latest, open-codestral-mamba 
client = MistralClient(api_key=api_key)


file_path = r"C:\Users\Admin\Python Projects\chatbot\context_files\pdf_test\Amd, 2023_sub_selfesteem.pdf"  # C:\path\to\file
prompt = "Describe what you see poetically"
instructions = "You will receive documents that have been pre-processed into JSON and dumped into a single string. Please refer to the content when responding."
context_dir = r"C:\Users\Admin\Desktop\ANa IQ Paper Review\iq_chatbot"

# Test
file_path = None
context_dir = None

# Process JSON files (can't handle images)
if file_path and context_dir:
   json_file = combine_json(file_path, image_skip=True)
   text_content = extract_text_content(json_file)
   context_json_file = context_directory(context_dir, image_skip=True)
   context_text_content = extract_text_content(context_json_file)
   message_content = "File:[ " + text_content + "], Context files: [" + context_text_content + "]"

elif file_path and not context_dir:
   json_file = combine_json(file_path, image_skip=True)
   text_content = extract_text_content(json_file)
   message_content = "File: [" + text_content + "]"

elif context_dir and not file_path:
    context_json_file = context_directory(context_dir, image_skip=True)
    context_text_content = json.dumps(context_json_file)
    message_content = "Context files: [" + context_text_content + "]"

else:
    message_content = "None."

# Construct message
if file_path or context_dir:
    msg_content = "Prompt: [" + prompt + "], Dumped JSON documents: [" + message_content + "]"
else:
    msg_content = "Prompt: [" + prompt + "]"


# Construct
messages = [
    ChatMessage(role="user", content=msg_content),
]


# Response
chat_response = client.chat(
    model=model, 
    messages=messages,
    temperature=.2,
    safe_prompt=False,
    max_tokens=500)

# Print response
print(chat_response.choices[0].message.content)

