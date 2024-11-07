import logging
from google_method import gemini_api
from mistral_method import mistral_api
from openai_method import gpt_api
from claude_method import claude_api
from ollama_method import ollama_api 
from typing import List, Dict, Any, Optional
from read_json_text import extract_json_text
from prep_file import combine_json, context_directory, extract_text_content, ContextCache
import markdown2
import webbrowser
import os
import json
import glob
import tempfile
import base64
from PIL import Image
import io
import requests

class Conversation:
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str, image: Optional[str] = None):
        message = {"role": role, "content": content}
        if image:
            message["image"] = image
        self.messages.append(message)

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
    
    def generate_response(current_prompt: str, chat_history_images: List[Image.Image]) -> str:
        if dev == 'google':
            response = gemini_api(current_prompt, file_path, context_dir, model_name or 'gemini-1.5-flash', max_tokens, chat_history_images)
        elif dev == 'openai':
            response = gpt_api(current_prompt, file_path, context_dir, model_name or 'mini', max_tokens, chat_history_images)
        elif dev == 'mistral':
            response = mistral_api(current_prompt, file_path, context_dir, model_name or 'mistral-large-latest', max_tokens)
        else:
            raise ValueError(f"Invalid dev option: {dev}. Choose 'google', 'openai', or 'mistral'.")
        
        return response.strip()

    chat_history_images = []
    if include_chat_history and conversation.messages:
        full_prompt = f"{conversation.get_full_conversation()}\nUser: {prompt}"
        for message in conversation.messages:
            if 'image' in message:
                if message['image'].startswith('http'):
                    response = requests.get(message['image'])
                    image = Image.open(io.BytesIO(response.content))
                else:
                    image_data = base64.b64decode(message['image'])
                    image = Image.open(io.BytesIO(image_data))
                chat_history_images.append(image)
    else:
        full_prompt = prompt

    try:
        response = generate_response(full_prompt, chat_history_images)
    except Exception as e:
        logging.error(f"Error in model_playground: {e}")
        raise
    
    conversation.add_message("User", prompt)
    conversation.add_message("Assistant", response)

    return {
        "response": response,
        "conversation": conversation
    }

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

    def batch_process(self, directory, prompt, dev, model_name, max_tokens=1000, include_chat_history=True, file_pattern="*.*", image_skip=True):
        results = {}
        for file_path in glob.glob(os.path.join(directory, "**", file_pattern), recursive=True):
            if os.path.isfile(file_path):
                try:
                    combined_json = combine_json(file_path, image_skip=image_skip)
                    file_content = extract_text_content(combined_json)
                    
                    # Minimize prompt construction
                    file_prompt = f"{prompt}\n\nContent: {file_content}"
                    response = self.process_prompt(file_prompt, dev, file_path, model_name, max_tokens, include_chat_history, image_skip)
                    results[file_path] = response
                except Exception as e:
                    results[file_path] = f"Error: {str(e)}"
        return results

    def process_prompt(self, prompt, dev, file_path=None, model_name=None, max_tokens=1000, include_chat_history=True, image_skip=True):
        try:
            context = self.cached_context or self.context_dir
            
            # Handle context as dictionary
            if isinstance(context, dict):
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp:
                    json.dump(context, temp)
                    context_path = temp.name
            else:
                context_path = context
            
            # Extract content efficiently
            content_parts = []
            
            # Add file content if exists
            if file_path:
                json_file = combine_json(file_path, image_skip=image_skip)
                file_content = extract_text_content(json_file)
                if file_content.strip():
                    content_parts.append(file_content)
        
            # Add context content if exists
            if context_path:
                context_json = context_directory(context_path, image_skip=image_skip, use_cache=True)
                context_content = extract_text_content(context_json)
                if context_content.strip():
                    content_parts.append(context_content)
            
            # Optimize content parts assembly
            if prompt.strip():
                content_parts.append(f"User: {prompt}")

            if include_chat_history:
                chat_history = self.conversation.get_full_conversation()
                if chat_history.strip():
                    content_parts.insert(0, chat_history)
            
            # Combine all parts efficiently
            full_content = "\n\n".join(content_parts)
            
            # Process images if needed (only if image_skip is False)
            chat_history_images = []
            if include_chat_history and not image_skip:
                for message in self.conversation.messages:
                    if 'image' in message:
                        if message['image'].startswith('http'):
                            response = requests.get(message['image'])
                            image = Image.open(io.BytesIO(response.content))
                        else:
                            image_data = base64.b64decode(message['image'])
                            image = Image.open(io.BytesIO(image_data))
                        chat_history_images.append(image)
        
            # Handle API calls with proper error handling
            if dev == 'google':
                image_summaries, content_summary = gemini_api(full_content, file_path, context_path, model_name, max_tokens, chat_history_images, image_skip=image_skip)
            elif dev == 'openai':
                image_summaries, content_summary = gpt_api(full_content, file_path, context_path, model_name, max_tokens, chat_history_images, image_skip=image_skip)
            elif dev == 'mistral':
                image_summaries, content_summary = "", mistral_api(full_content, file_path, context_path, model_name, max_tokens)
            elif dev == 'anthropic':
                image_summaries, content_summary = claude_api(full_content, file_path, context_path, model_name, max_tokens, chat_history_images, image_skip=image_skip)
            elif dev == 'ollama':
                image_summaries, content_summary = ollama_api(full_content, file_path, context_path, model_name, max_tokens, chat_history_images, image_skip=image_skip)
            else:
                raise ValueError(f"Invalid dev option: {dev}")

            # Combine results efficiently
            result = content_summary
            if image_summaries and not image_skip:
                result = f"{image_summaries}\n\n{content_summary}"

            self.conversation.add_message("Assistant", result)
            self.save_history()
            
            # Cleanup temp file if created
            if isinstance(context, dict) and 'temp' in locals():
                os.unlink(temp.name)
            
            return result

        except Exception as e:
            logging.error(f"Error in process_prompt: {e}")
            raise

    def update_context(self):
        if self.context_cache and self.context_dir:
            self.cached_context = context_directory(self.context_dir, use_cache=True)
            print("Context updated.")
        else:
            print("No context directory specified or context cache not initialized.")

    def _print_response(self, dev: str, prompt: str, response: str):
        print(f"\n{dev.capitalize()} Response to '{prompt}':")
        print(response)
