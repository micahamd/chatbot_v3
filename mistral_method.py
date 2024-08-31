from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import os
import json
from prep_file import combine_json, context_directory, batch_directory


api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-large-latest"  # open-mistral-nemo, codestral-latest, mistral-large-latest, open-codestral-mamba 
client = MistralClient(api_key=api_key)


file_path = r"C:\Users\Admin\Python Projects\chatbot\context_files\pdf_test\Amd, 2023_sub_selfesteem.pdf"  # C:\path\to\file
prompt = "Describe what you see poetically"
instructions = "You will receive documents that have been pre-processed into JSON and dumped into a single string. Please refer to the content when responding."
context_dir = r"C:\Users\Admin\Desktop\ANa IQ Paper Review\iq_chatbot"

# Test
# file_path = None
# context_dir = None

# Text extraction method
def extract_text_content(json_file):
    return json_file.get('text_JSON', {}).get('content', {}).get('text', '')

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

















#def mistral_api(prompt, instructions, file_path=None, context_dir=None, model_name='mistral-large-latest', token_count=500):
#    # Initialize the Mistral API key
#    api_key = os.getenv("MISTRAL_API_KEY")
#    if not api_key:
#        print("WARNING: MISTRAL_API_KEY environment variable not set. Mistral API will not be available.")
#        return None
#
#    # Create a MistralClient instance
#    client = MistralClient(api_key=api_key)
#
#    messages = []
#
#    # Prepare JSON file if file_path is provided
#    json_file = {}
#    if file_path:
#        with open(file_path, 'r') as f:
#            json_file = json.load(f)
#        dumped_json = json.dumps(json_file)
#        messages.append({"role": "system", "content": dumped_json})
#
#    # Prepare context JSON if context_dir is provided
#    context_json = {}
#    if context_dir:
#        context_files = [f for f in os.listdir(context_dir) if os.path.isfile(os.path.join(context_dir, f))]
#        for file in context_files:
#            with open(os.path.join(context_dir, file), 'r') as f:
#                context_json[file] = json.load(f)
#        dumped_context_json = json.dumps(context_json)
#        messages.append({"role": "system", "content": dumped_context_json})
#
#    # Add the prompt and instructions as the final user message
#    messages.append({"role": "user", "content": f"{prompt}\n\n{instructions}"})
#
#    # Send the chat completion request
#    response = client.chat(
#        model=model_name,
#        messages=messages,
#        max_tokens=token_count,
#    )
#
#    # Return the response
#    return response.choices[0].message.content
#
#mistral_api(prompt, instructions, context_dir=context_dir)