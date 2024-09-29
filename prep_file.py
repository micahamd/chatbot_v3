from read_json_text import extract_json_text  # Import function to extract JSON text from a file
from read_image_url import extract_images  # Import function to extract images from a file
import json  # Import JSON module for handling JSON data
import base64
import os  # Import OS module for interacting with the operating system
import glob  # Import glob module for file pattern matching
import hashlib  # Import hashlib module for hashing functions
import zlib
from pathlib import Path # Import Path class for handling file paths
from urllib.parse import urlparse # Import urlparse function for parsing URLs


def combine_json(file_path, image_skip=False):
    # Extract text JSON from the file
    text_JSON = extract_json_text(file_path)
    
    if not image_skip:
        # If image_skip is False, extract images JSON from the file
        image_JSON = extract_images(file_path)
    else:
        # If image_skip is True, skip image extraction and set a default message
        image_JSON = {"message": "No images were processed"}
    
    # Combine text JSON and image JSON into a single dictionary
    combined_result = {
        "text_JSON": text_JSON,
        "image_JSON": image_JSON
    }
    
    # Return the combined result
    return combined_result

# Text extraction method
def extract_text_content(json_file):
    print(f"Extracting text content from: {type(json_file)}")
    if isinstance(json_file, dict):
        if 'text_JSON' in json_file:
            content = json_file['text_JSON'].get('content', {})
            paragraphs = content.get('paragraphs', {})
            headings = content.get('headings', {})
            tables = content.get('tables', [])
            pages = content.get('pages', [])
            
            # Combine structural elements
            structural_content = []
            
            # Process pages if available
            if pages:
                for page in pages:
                    page_type = page.get('type', 'page')
                    page_number = page.get('page_number', '')
                    structural_content.append(f"{page_type.capitalize()} {page_number}:")
                    
                    for heading_hash in page.get('headings', []):
                        heading_text = headings.get(heading_hash, '')
                        if heading_text:
                            structural_content.append(f"Heading: {heading_text}")
                    
                    for para_hash in page.get('paragraphs', []):
                        if para_hash.startswith("TABLE_"):
                            table_index = int(para_hash.split('_')[1])
                            if table_index < len(tables):
                                structural_content.append("Table:")
                                for row in tables[table_index]:
                                    structural_content.append(" | ".join(str(cell) for cell in row))
                        else:
                            para_text = paragraphs.get(para_hash, '')
                            if para_text:
                                structural_content.append(para_text)
            else:
                # If no pages, process headings and paragraphs directly
                for heading in headings.values():
                    structural_content.append(f"Heading: {heading}")
                for para in paragraphs.values():
                    structural_content.append(para)
                
                # Process tables if available
                if tables:
                    for table in tables:
                        structural_content.append("Table:")
                        for row in table:
                            structural_content.append(" | ".join(str(cell) for cell in row))
            
            combined_content = "\n\n".join(structural_content)
            print(f"Extracted structured content length: {len(combined_content)}")
            return combined_content
        else:
            # If it's a dictionary of files, concatenate all text content
            texts = [extract_text_content(file_json) for file_json in json_file.values()]
            combined_text = '\n\n'.join(texts)
            print(f"Combined text content length: {len(combined_text)}")
            return combined_text
    print("No text content extracted")
    return ''

# For iterating over images in a directory
def extract_image_directory_from_json(json_file):
    images = json_file.get('image_JSON', {}).get('images', [])
    image_urls = [image.get('url', '') for image in images]
    
    if not image_urls:
        return None
    
    # Parse the first URL to get the path
    parsed_url = urlparse(image_urls[0])
    image_path = Path(parsed_url.path.lstrip('/'))  # Remove leading slash
    
    # Return the directory containing the images
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


def context_directory(directory_path, image_skip=False, use_cache=True):
    print(f"context_directory called with path: {directory_path}")
    print(f"image_skip: {image_skip}")
    
    if use_cache:
        cache = ContextCache(directory_path)
        cached_context = cache.get_cached_context()
        if cached_context:
            print("Returning cached context")
            return cached_context

    print(f"Processing files in directory: {directory_path}")
    combined_results = {}
    for file_path in glob.glob(os.path.join(directory_path, '*')):
        if os.path.isfile(file_path):
            print(f"Processing file: {file_path}")
            file_name = os.path.basename(file_path)
            result = combine_json(file_path, image_skip=image_skip)
            combined_results[file_name] = result
            print(f"File {file_name} processed. Image JSON: {result.get('image_JSON', {}).get('images', [])}")

    if use_cache:
        print("Saving context to cache")
        cache.save_cache(combined_results)

    print(f"Processed {len(combined_results)} files")
    return combined_results

# Updated batch_directory function
def batch_directory(directory_path, image_skip=False):
    results = []
    for file_path in os.path.join(directory_path, '*'):
        if os.path.isfile(file_path):
            file_name = os.path.basename(file_path)
            result = combine_json(file_path, image_skip)
            results.append({
                "file_name": file_name,
                "result": result
            })
    return results

# Utility functions for compression (optional, can be used if needed)
def compress_context(context_json):
    return zlib.compress(json.dumps(context_json).encode())

def decompress_context(compressed_context):
    return json.loads(zlib.decompress(compressed_context).decode())

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
