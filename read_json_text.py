import os
import io
import re
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
from docx import Document
from pptx import Presentation
import csv
import openpyxl
import hashlib

def extract_json_text(file_path):
    def apply_ocr(image):
        try:
            return pytesseract.image_to_string(image)
        except pytesseract.TesseractNotFoundError:
            return ""

    def normalize_text(text):
        # Remove punctuation, digits, and normalize whitespace and case
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        text = re.sub(r'\d+', '', text)      # Remove digits
        return ' '.join(text.split()).lower()

    def hash_content(content):
        normalized_content = normalize_text(content)
        return hashlib.md5(normalized_content.encode('utf-8')).hexdigest()

    def add_content(content):
        normalized_content = normalize_text(content)
        if len(normalized_content) < 5:  # Skip very short content
            return None
        content_hash = hash_content(content)
        if content_hash not in unique_contents:
            unique_contents[content_hash] = normalized_content
        return content_hash  # Return content_hash to reference in pages

    def is_repeated_line(line, line_counts, threshold=3):
        normalized_line = normalize_text(line)
        if not normalized_line:
            return True
        line_counts[normalized_line] = line_counts.get(normalized_line, 0) + 1
        return line_counts[normalized_line] > threshold

    # Initialize data structures
    result = {
        "metadata": {
            "file_name": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path),
            "file_type": os.path.splitext(file_path)[1].lower(),
            "instructions": {
                "text": "Unique normalized text content with hashes as keys.",
                "pages": "List of pages with references to content hashes."
            }
        },
        "content": {
            "text": {},
            "pages": []
        }
    }

    unique_contents = {}
    line_counts = {}

    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            # Process image files
            image = Image.open(file_path)
            ocr_text = apply_ocr(image)
            if ocr_text.strip():
                content_hash = add_content(ocr_text.strip())
                if content_hash:
                    page_content = {"page_number": 1, "content_hashes": [content_hash]}
                    result["content"]["pages"].append(page_content)
        elif ext == '.pdf':
            # Process PDF files
            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc, start=1):
                page_content = {"page_number": page_num, "content_hashes": []}
                page_text = page.get_text()
                lines = page_text.split('\n')
                filtered_lines = []
                for line in lines:
                    if not is_repeated_line(line, line_counts):
                        filtered_lines.append(line)
                filtered_text = '\n'.join(filtered_lines).strip()
                if filtered_text:
                    content_hash = add_content(filtered_text)
                    if content_hash:
                        page_content["content_hashes"].append(content_hash)
                else:
                    # Apply OCR if no text is extracted
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    ocr_text = apply_ocr(img)
                    if ocr_text.strip():
                        content_hash = add_content(ocr_text.strip())
                        if content_hash:
                            page_content["content_hashes"].append(content_hash)
                if page_content["content_hashes"]:
                    result["content"]["pages"].append(page_content)
        elif ext in ['.docx', '.doc']:
            # Process Word documents
            doc = Document(file_path)
            page_content = {"page_number": 1, "content_hashes": []}
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    content_hash = add_content(text)
                    if content_hash:
                        page_content["content_hashes"].append(content_hash)
            if page_content["content_hashes"]:
                result["content"]["pages"].append(page_content)
            # Optional OCR on images - skip to prevent duplication
        elif ext in ['.pptx', '.ppt']:
            # Process PowerPoint presentations
            prs = Presentation(file_path)
            for slide_num, slide in enumerate(prs.slides, start=1):
                page_content = {"page_number": slide_num, "content_hashes": []}
                for shape in slide.shapes:
                    if hasattr(shape, 'text'):
                        text = shape.text.strip()
                        if text:
                            content_hash = add_content(text)
                            if content_hash:
                                page_content["content_hashes"].append(content_hash)
                    # Skip OCR on images to prevent duplication
                if page_content["content_hashes"]:
                    result["content"]["pages"].append(page_content)
        elif ext in ['.xlsx', '.xls']:
            # Process Excel files
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            for sheet in wb.worksheets:
                page_content = {"sheet": sheet.title, "content_hashes": []}
                for row in sheet.iter_rows():
                    row_values = [str(cell.value).strip() for cell in row if cell.value]
                    if row_values:
                        text = ' '.join(row_values)
                        content_hash = add_content(text)
                        if content_hash:
                            page_content["content_hashes"].append(content_hash)
                if page_content["content_hashes"]:
                    result["content"]["pages"].append(page_content)
        elif ext == '.csv':
            # Process CSV files
            with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                page_content = {"page_number": 1, "content_hashes": []}
                for row in reader:
                    row_values = [cell.strip() for cell in row if cell.strip()]
                    if row_values:
                        text = ' '.join(row_values)
                        content_hash = add_content(text)
                        if content_hash:
                            page_content["content_hashes"].append(content_hash)
                if page_content["content_hashes"]:
                    result["content"]["pages"].append(page_content)
        else:
            # Process other text files
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read().strip()
                if text:
                    content_hash = add_content(text)
                    if content_hash:
                        page_content = {"page_number": 1, "content_hashes": [content_hash]}
                        result["content"]["pages"].append(page_content)
    except Exception as e:
        # Handle exceptions
        error_message = f"Error processing file: {str(e)}"
        content_hash = add_content(error_message)
        if content_hash:
            page_content = {"page_number": 1, "content_hashes": [content_hash]}
            result["content"]["pages"].append(page_content)

    # Assign unique contents to result
    result["content"]["text"] = unique_contents

    return result