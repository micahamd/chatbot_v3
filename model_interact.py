from google_method import gemini_api
from mistral_method import mistral_api
from openai_method import gpt_api
from typing import List, Dict, Any, Optional
from prep_file import combine_json
import webbrowser
import os
import json
import glob

class Conversation:
    def __init__(self):
        self.messages: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def get_full_conversation(self) -> str:
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.messages])

def model_playground(
    prompt: str,
    dev: str,
    file_path: str = None,
    context_dir: str = None,
    model_name: str = None,
    max_tokens: int = 500,
    conversation: Optional[Conversation] = None,
    include_chat_history: bool = True
) -> Dict[str, Any]:
    if conversation is None:
        conversation = Conversation()
    
    def generate_response(current_prompt: str) -> str:
        if dev == 'google':
            response = gemini_api(current_prompt, file_path, context_dir, model_name or 'gemini-1.5-flash', max_tokens)
        elif dev == 'openai':
            response = gpt_api(current_prompt, file_path, context_dir, model_name or 'mini', max_tokens)
        elif dev == 'mistral':
            response = mistral_api(current_prompt, file_path, context_dir, model_name or 'mistral-large-latest', max_tokens)
        else:
            raise ValueError(f"Invalid dev option: {dev}. Choose 'google', 'openai', or 'mistral'.")
        
        return response

    if include_chat_history and conversation.messages:
        full_prompt = f"{conversation.get_full_conversation()}\nUser: {prompt}"
    else:
        full_prompt = prompt

    response = generate_response(full_prompt)
    
    conversation.add_message("User", prompt)
    conversation.add_message("Assistant", response)

    result = {
        "response": response,
        "conversation": conversation
    }

    return result

def generate_html(conversations: Dict[str, Conversation]) -> str:
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Model Conversations</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }
            h1, h2 { color: #333; }
            .conversation { background-color: #f4f4f4; padding: 10px; margin-bottom: 20px; border-radius: 5px; }
            .message { margin-bottom: 10px; }
            .user { color: #0066cc; }
            .assistant { color: #009933; }
        </style>
    </head>
    <body>
        <h1>AI Model Conversations</h1>
    """

    for dev, conversation in conversations.items():
        html_content += f"""
        <div class="conversation">
            <h2>{dev.capitalize()} Conversation</h2>
        """
        for message in conversation.messages:
            html_content += f"""
            <div class="message">
                <span class="{message['role'].lower()}"><strong>{message['role']}:</strong></span> {message['content']}
            </div>
            """
        html_content += "</div>"

    html_content += """
    </body>
    </html>
    """

    return html_content

def display_conversations_in_browser(conversations: Dict[str, Conversation]):
    html_content = generate_html(conversations)
    with open("ai_conversations.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    webbrowser.open('file://' + os.path.realpath("ai_conversations.html"))

class AIPlayground:
    def __init__(self, context_dir: str = None, history_file: str = "conversation_history.json"):
        self.context_dir = context_dir
        self.conversation = Conversation()
        self.history_file = history_file
        self.load_history()

    def process_prompt(self, prompt: str, dev: str, file_path: str = None, model_name: str = None, max_tokens: int = 500, include_chat_history: bool = True):
        result = model_playground(
            prompt, 
            dev=dev, 
            file_path=file_path,
            context_dir=self.context_dir, 
            model_name=model_name,
            max_tokens=max_tokens,
            conversation=self.conversation,
            include_chat_history=include_chat_history
        )
        print(f"\n{dev.capitalize()} Response to '{prompt}':")
        print(result["response"])

        self.save_history()
        return result["response"]

    def batch_process(self, directory: str, prompt: str, dev: str, file_pattern: str = "*", context_dir: str = None, model_name: str = None, max_tokens: int = 500, include_chat_history: bool = True):
        results = {}
        for file_path in glob.glob(os.path.join(directory, file_pattern)):
            with open(file_path, 'r') as file:
                file_content = self.combine_json(file_path)
            
            file_prompt = f"{prompt}\n\nFile content:\n{file_content}"
            result = self.process_prompt(
                file_prompt,
                dev=dev,
                file_path=file_path,
                model_name=model_name,
                max_tokens=max_tokens,
                include_chat_history=include_chat_history
            )
            results[file_path] = result
        
        return results

    def display_results(self):
        conversations = {
            'combined': self.conversation
        }
        display_conversations_in_browser(conversations)

    def save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.conversation.messages, f)

    def load_history(self):
        try:
            with open(self.history_file, 'r') as f:
                self.conversation.messages = json.load(f)
        except FileNotFoundError:
            pass  # No history file found, start with an empty conversation

    def clear_history(self):
        self.conversation = Conversation()
        self.save_history()
        print("Conversation history cleared.")

# Example usage
if __name__ == "__main__":
    playground = AIPlayground(context_dir=None)

    # Process individual prompts
    playground.process_prompt("Tell me a funny story about Mary", dev='google')
    playground.process_prompt("Continue Mary's humorous adventures", dev='openai')
    playground.process_prompt("End Mary's story with a dark twist", dev='openai')
    playground.process_prompt("How would Mary describe her day?", dev='google')

    # Batch process files in a directory
    batch_results = playground.batch_process(
        directory=r"C:\Users\Admin\Python Projects\chatbot\output_files",
        prompt="Summarize the content of this file",
        dev='google',
        file_pattern="*.txt",
        model_name='gemini-1.5-flash',
        max_tokens=300,
        include_chat_history=False
    )
    for file_path, summary in batch_results.items():
        print(f"\nSummary for {file_path}:")
        print(summary)

    # Display the results in the browser
    playground.display_results()

    # Clear the conversation history (uncomment to use)
    # playground.clear_history()