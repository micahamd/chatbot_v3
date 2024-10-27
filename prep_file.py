from read_json_text import extract_json_text
from read_image_url import extract_images
import json
import base64
import os
import glob
import hashlib
import zlib
from pathlib import Path
from urllib.parse import urlparse

def combine_json(file_path, image_skip=True):
    # Always get text content first
    text_JSON = extract_json_text(file_path)
    
    # Only get image content if image_skip is False
    if not image_skip:
        image_JSON = extract_images(file_path)
    else:
        image_JSON = {"message": "No images were processed"}
    
    return {
        "text_JSON": text_JSON,
        "image_JSON": image_JSON
    }

def extract_text_content(json_file):
    if isinstance(json_file, dict):
        if 'text_JSON' in json_file:
            content = json_file['text_JSON'].get('content', {})
            
            structural_content = []
            
            # Process pages
            for page in content.get('pages', []):
                # Add headings first
                headings = page.get('headings', [])
                if headings:
                    structural_content.extend(headings)
                
                # Add paragraphs
                paragraphs = page.get('paragraphs', [])
                if paragraphs:
                    structural_content.extend(paragraphs)
            
            # Process tables
            for table in content.get('tables', []):
                if isinstance(table, dict):  # Excel sheet
                    for row in table.get('data', []):
                        if any(cell.strip() for cell in row):
                            structural_content.append(" | ".join(cell for cell in row if cell.strip()))
                else:  # CSV data
                    for row in table:
                        if any(cell.strip() for cell in row):
                            structural_content.append(" | ".join(cell for cell in row if cell.strip()))
            
            # Join with single newlines to minimize tokens
            combined_content = "\n".join(filter(None, structural_content))
            print(f"Extracted structured content length: {len(combined_content)}")
            return combined_content
        else:
            # Process multiple files
            texts = []
            for file_json in json_file.values():
                text = extract_text_content(file_json)
                if text.strip():
                    texts.append(text)
            combined_text = "\n\n".join(texts)
            print(f"Combined text content length: {len(combined_text)}")
            return combined_text
    
    return ''

def extract_image_directory_from_json(json_file):
    images = json_file.get('image_JSON', {}).get('images', [])
    image_urls = [image.get('url', '') for image in images]
    
    if not image_urls:
        return None
    
    parsed_url = urlparse(image_urls[0])
    image_path = Path(parsed_url.path.lstrip('/'))
    return image_path.parent

class ContextCache:
    def __init__(self, context_dir, cache_file="context_cache.json"):
        self.context_dir = context_dir
        self.cache_file = cache_file

    def get_dir_hash(self):
        hash_md5 = hashlib.md5()
        if not isinstance(self.context_dir, (str, bytes, os.PathLike)):
            raise TypeError(f"Expected str, bytes or os.PathLike object, got {type(self.context_dir)}")
        for root, _, files in os.walk(self.context_dir):
            for file in files:
                hash_md5.update(f"{file}{os.path.getmtime(os.path.join(root, file))}".encode())
        return hash_md5.hexdigest()

    def is_cache_valid(self):
        if not os.path.exists(self.cache_file):
            return False
        with open(self.cache_file, 'r') as f:
            cache = json.load(f)
        return cache.get('dir_hash') == self.get_dir_hash()

    def get_cached_context(self):
        if self.is_cache_valid():
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
                compressed_data = base64.b64decode(cache['context'])
                return json.loads(zlib.decompress(compressed_data).decode())
        return None

    def save_cache(self, context):
        compressed_data = zlib.compress(json.dumps(context).encode())
        cache = {
            'dir_hash': self.get_dir_hash(),
            'context': base64.b64encode(compressed_data).decode()
        }
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f)

def context_directory(directory_path, image_skip=True, use_cache=True):
    if use_cache:
        cache = ContextCache(directory_path)
        cached_context = cache.get_cached_context()
        if cached_context:
            return cached_context

    combined_results = {}
    for root, _, files in os.walk(directory_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            try:
                result = combine_json(file_path, image_skip=image_skip)
                combined_results[file_path] = result
            except Exception as e:
                print(f"Error processing file {file_path}: {str(e)}")

    if use_cache:
        cache.save_cache(combined_results)

    return combined_results

def compress_context(context_json):
    return zlib.compress(json.dumps(context_json).encode())

def decompress_context(compressed_context):
    return json.loads(zlib.decompress(compressed_context).decode())

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
