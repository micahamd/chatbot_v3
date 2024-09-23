from google_method import gemini_api
from mistral_method import mistral_api
from openai_method import gpt_api
from typing import List, Dict, Any, Optional
from read_json_text import extract_json_text
from prep_file import combine_json, context_directory, ContextCache  # Added ContextCache import
import markdown2
import webbrowser
import os
import json
import glob
import tempfile


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
            /* ... existing styles ... */
            .file-result { margin-bottom: 20px; border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
            .file-name { font-weight: bold; margin-bottom: 10px; }
            .collapsible { background-color: #eee; color: #444; cursor: pointer; padding: 18px; width: 100%; border: none; text-align: left; outline: none; font-size: 15px; }
            .active, .collapsible:hover { background-color: #ccc; }
            .content { padding: 0 18px; display: none; overflow: hidden; background-color: #f1f1f1; }
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h1>Conversations</h1>
            <ul>
    """

    for dev in conversations.keys():
        html_content += f"<li><a href='#{dev}'>{dev.capitalize()}</a></li>"

    html_content += """
            </ul>
        </div>
        <div class="main-content">
    """

    for dev, conversation in conversations.items():
        html_content += f"""
        <div id="{dev}" class="conversation">
            <h2>{dev.capitalize()} Conversation</h2>
            <div class="messages">
        """
        user_prompt = ""
        for message in conversation.messages:
            role_class = message['role'].lower()
            content = markdown2.markdown(message['content'])
            if role_class == 'user':
                user_prompt = content
            else:
                if 'File:' in content:
                    file_name = content.split('File:')[1].split('\n')[0].strip()
                    response = content.split('Response:')[1].strip()
                    html_content += f"""
                    <div class="file-result">
                        <button class="collapsible">{file_name}</button>
                        <div class="content">
                            <div class="{role_class}">
                                <strong>{message['role']}:</strong>
                                {response}
                            </div>
                        </div>
                    </div>
                    """
                else:
                    html_content += f"""
                    <div class="message">
                        <div class="{role_class}">
                            <strong>{message['role']}:</strong>
                            {content}
                        </div>
                    </div>
                    """
        html_content += "</div></div>"

    html_content += """
        </div>
        <script>
            var coll = document.getElementsByClassName("collapsible");
            var i;

            for (i = 0; i < coll.length; i++) {
                coll[i].addEventListener("click", function() {
                    this.classList.toggle("active");
                    var content = this.nextElementSibling;
                    if (content.style.display === "block") {
                        content.style.display = "none";
                    } else {
                        content.style.display = "block";
                    }
                });
            }
        </script>
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
        self.context_cache = ContextCache(context_dir) if context_dir else None
        self.conversation = Conversation()
        self.history_file = history_file
        self.batch_dir = False
        self.load_history()
        self.cached_context = self._load_cached_context()

    def _load_cached_context(self):
        if self.context_cache:
            cached_context = self.context_cache.get_cached_context()
            if cached_context:
                return cached_context
        return None

    def load_history(self):
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.conversation.messages = json.load(f)
        except FileNotFoundError:
            print("No history file found, starting with an empty conversation.")
        except json.JSONDecodeError as e:
            print(f"Error loading history: {e}")

    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation.messages, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Error saving history: {e}")

    def clear_history(self):
        self.conversation = Conversation()
        self.save_history()
        print("Conversation history cleared.")

    def batch_process(self, directory, prompt, dev, model_name, max_tokens=1000, include_chat_history=True, file_pattern="*.*"):
        results = {}
        for file_path in glob.glob(os.path.join(directory, "**", file_pattern), recursive=True):
            if os.path.isfile(file_path):
                file_content = extract_json_text(file_path)["content"]["text"]
                file_prompt = f"{prompt}\n\nFile: {os.path.basename(file_path)}\nContent: {file_content}\n\nResponse:"
                response = self.process_prompt(file_prompt, dev, file_path, model_name, max_tokens, include_chat_history)
                results[file_path] = response
        return results

    def process_prompt(self, prompt: str, dev: str, file_path: str = None, model_name: str = None, max_tokens: int = 1000, include_chat_history: bool = True):
        print(f"Processing prompt with context_dir: {self.context_dir}")
        print(f"Cached context available: {self.cached_context is not None}")
        
        context = self.cached_context or self.context_dir
        
        # Ensure context is a string path
        if isinstance(context, dict):
            print("Cached context is a dictionary. Writing to temporary file.")
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp:
                json.dump(context, temp)
                context_path = temp.name
            print(f"Temporary context file created at: {context_path}")
        else:
            context_path = context
        
        print(f"Using context path: {context_path}")
        
        result = model_playground(
            prompt, 
            dev=dev, 
            file_path=file_path,
            context_dir=context_path,
            model_name=model_name,
            max_tokens=max_tokens,
            conversation=self.conversation,
            include_chat_history=include_chat_history
        )
        self._print_response(dev, prompt, result["response"])
        self.save_history()
        
        # Clean up temporary file if it was created
        if isinstance(context, dict) and 'temp' in locals():
            import os
            os.unlink(temp.name)
            print(f"Temporary context file removed: {temp.name}")
        
        return result["response"]

    def update_context(self):
        if self.context_cache and self.context_dir:
            new_context = context_directory(self.context_dir, use_cache=True)
            self.cached_context = new_context
            print("Context updated.")
        else:
            print("No context directory specified or context cache not initialized.")

    def _print_response(self, dev: str, prompt: str, response: str):
        print(f"\n{dev.capitalize()} Response to '{prompt}':")
        print(response)

    def display_results(self):
        conversations = {'combined': self.conversation}
        display_conversations_in_browser(conversations)


## Example usage
#if __name__ == "__main__":
#    playground = AIPlayground(context_dir=None)
#
#    # Process individual prompts
#    playground.process_prompt("Tell me a funny story about Mary", dev='google')
#    playground.process_prompt("Continue Mary's humorous adventures", dev='openai')
#    playground.process_prompt("End Mary's story with a dark twist", dev='openai')
#    playground.process_prompt("How would Mary describe her day?", dev='google')
#
#    # Batch process files in a directory
#    batch_results = playground.batch_process(
#        directory=r"C:\Users\micah\Downloads\WA1_Assignments",
#        prompt="Summarize the content of this file",
#        dev='google',
#        file_pattern="*.json",
#        model_name='gemini-1.5-flash',
#        max_tokens=300,
#        include_chat_history=False
#    )
#    for file_path, summary in batch_results.items():
#        print(f"\nSummary for {file_path}:")
#        print(summary)
#
#    # Display the results in the browser
#    playground.display_results()

    # Clear the conversation history (uncomment to use)
    # playground.clear_history()