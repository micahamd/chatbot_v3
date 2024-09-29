import os
import json
import io
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
from docx import Document
from pptx import Presentation
import csv
import openpyxl
import hashlib

def extract_json_text(file_path):
    # Get the file extension and convert it to lowercase
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    # Initialize the result dictionary with metadata and content structure
    result = {
        "metadata": {
            "file_name": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path),
            "file_type": ext,
            "instructions": {
                "text": "Main text content",
                "paragraphs": "A dictionary where keys are MD5 hashes of paragraph content and values are the paragraph text.",
                "headings": "A dictionary where keys are MD5 hashes of heading content and values are the heading text.",
                "tables": "A list of tables extracted from the document. Each table is represented as a list of rows, where each row is a list of cell values.",
                "pages": "A list of dictionaries, each representing a page or slide. Each dictionary contains the page/slide number, text content, and lists of paragraph and heading hashes."
            }
        },
        "content": {
            "paragraphs": {},
            "headings": {},
            "tables": [],
            "pages": []
        }
    }

    # Function to apply OCR on an image and return the text
    def apply_ocr(image):
        try:
            return pytesseract.image_to_string(image)
        except pytesseract.TesseractNotFoundError:
            return "[OCR Text: Tesseract not installed]"

    # Function to hash content using MD5
    def hash_content(content):
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    # Dictionaries to keep track of seen paragraphs and headings to avoid duplicates
    seen_paragraphs = {}
    seen_headings = {}

    try:
        # Process image files
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            with Image.open(file_path) as img:
                ocr_text = apply_ocr(img)
                para_hash = hash_content(ocr_text)
                result["content"]["paragraphs"][para_hash] = ocr_text
                result["content"]["pages"].append({
                    "page_number": 1,
                    "paragraphs": [para_hash]
                })

        # Process PDF files
        elif ext == '.pdf':
            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc):
                page_text = page.get_text("text")
                page_paragraphs = page_text.split('\n\n')
                page_content = {
                    "page_number": page_num + 1,
                    "paragraphs": [],
                    "headings": []
                }
                
                for para in page_paragraphs:
                    para_hash = hash_content(para)
                    if para_hash not in result["content"]["paragraphs"]:
                        result["content"]["paragraphs"][para_hash] = para
                    page_content["paragraphs"].append(para_hash)

                for block in page.get_text("dict")["blocks"]:
                    if block["type"] == 0:  # Text block
                        for line in block["lines"]:
                            for span in line["spans"]:
                                if span["font"].startswith("Heading"):
                                    heading_hash = hash_content(span["text"])
                                    if heading_hash not in result["content"]["headings"]:
                                        result["content"]["headings"][heading_hash] = span["text"]
                                    page_content["headings"].append(heading_hash)

                result["content"]["pages"].append(page_content)

        # Process Word documents
        elif ext in ['.docx', '.doc']:
            doc = Document(file_path)
            current_page = {"type": "docx_page", "page_number": 1, "paragraphs": [], "headings": []}
            page_count = 0
        
            def add_page(page):
                nonlocal page_count
                page_count += 1
                page["page_number"] = page_count
                result["content"]["pages"].append(page)
        
            for element in doc.element.body:
                if element.tag.endswith('p'):  # Paragraph
                    para = doc.paragraphs[len(current_page["paragraphs"]) + len(current_page["headings"])]
                    para_text = para.text.strip()
                    if para_text:
                        para_hash = hash_content(para_text)
                        if para.style.name.startswith('Heading'):
                            result["content"]["headings"][para_hash] = para_text
                            current_page["headings"].append(para_hash)
                        else:
                            result["content"]["paragraphs"][para_hash] = para_text
                            current_page["paragraphs"].append(para_hash)
                elif element.tag.endswith('tbl'):  # Table
                    table_data = []
                    for row in element.findall('.//w:tr', namespaces=element.nsmap):
                        row_data = [cell.text.strip() for cell in row.findall('.//w:t', namespaces=element.nsmap)]
                        table_data.append(row_data)
                    result["content"]["tables"].append(table_data)
                    table_hash = hash_content(str(table_data))
                    current_page["paragraphs"].append(f"TABLE_{table_hash}")
                elif element.tag.endswith('sectPr'):  # Section break (new page)
                    if current_page["paragraphs"] or current_page["headings"]:
                        add_page(current_page)
                        current_page = {"type": "docx_page", "paragraphs": [], "headings": []}
        
            # Add the last page if it has content
            if current_page["paragraphs"] or current_page["headings"]:
                add_page(current_page)
        
            # Extract images and apply OCR
            for rel in doc.part.rels.values():
                if "image" in rel.target_ref:
                    image = Image.open(io.BytesIO(rel.target_part.blob))
                    ocr_text = apply_ocr(image)
                    if ocr_text.strip():
                        para_hash = hash_content(ocr_text)
                        result["content"]["paragraphs"][para_hash] = ocr_text
                        add_page({
                            "type": "docx_image",
                            "paragraphs": [para_hash]
                        })
        
            # Add document properties
            doc_props = doc.core_properties
            result["metadata"]["title"] = doc_props.title or ""
            result["metadata"]["author"] = doc_props.author or ""
            result["metadata"]["created"] = str(doc_props.created) if doc_props.created else ""
            result["metadata"]["modified"] = str(doc_props.modified) if doc_props.modified else ""

        # Process PowerPoint presentations
        elif ext in ['.pptx', '.ppt']:
            prs = Presentation(file_path)
            for slide_num, slide in enumerate(prs.slides):
                slide_paragraphs = []
                for shape in slide.shapes:
                    if hasattr(shape, 'text'):
                        shape_text = shape.text.strip()
                        if shape_text:
                            para_hash = hash_content(shape_text)
                            if para_hash not in result["content"]["paragraphs"]:
                                result["content"]["paragraphs"][para_hash] = shape_text
                            slide_paragraphs.append(para_hash)
                    if hasattr(shape, "image"):
                        image = Image.open(io.BytesIO(shape.image.blob))
                        ocr_text = apply_ocr(image)
                        para_hash = hash_content(ocr_text)
                        if para_hash not in result["content"]["paragraphs"]:
                            result["content"]["paragraphs"][para_hash] = ocr_text
                        slide_paragraphs.append(para_hash)
                result["content"]["pages"].append({
                    "slide_number": slide_num + 1,
                    "paragraphs": slide_paragraphs
                })

        # Process Excel files
        elif ext in ['.xlsx', '.xls']:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            for sheet in wb.worksheets:
                sheet_data = []
                for row in sheet.iter_rows():
                    row_data = [cell.value for cell in row]
                    sheet_data.append(row_data)
                result["content"]["tables"].append({"sheet": sheet.title, "data": sheet_data})

        # Process CSV files
        elif ext == '.csv':
            table_data = []
            with open(file_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    table_data.append(row)
            result["content"]["tables"].append(table_data)

        # Process text-based files
        elif ext in ['.md', '.markdown', '.mdown', '.html', '.htm', '.py', '.js', '.java', '.cpp', '.txt', '.rtf', '.odt', '.epub', '.tex', '.json', '.yaml', '.yml', '.log', '.xml', '.ini']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
                paragraphs = text.split('\n\n')
                page_paragraphs = []
                for para in paragraphs:
                    para = para.strip()
                    if para:
                        para_hash = hash_content(para)
                        if para_hash not in result["content"]["paragraphs"]:
                            result["content"]["paragraphs"][para_hash] = para
                        page_paragraphs.append(para_hash)
                result["content"]["pages"].append({
                    "page_number": 1,
                    "paragraphs": page_paragraphs
                })

        # Default processing for other file types
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
                paragraphs = text.split('\n\n')
                page_paragraphs = []
                for para in paragraphs:
                    para = para.strip()
                    if para:
                        para_hash = hash_content(para)
                        if para_hash not in result["content"]["paragraphs"]:
                            result["content"]["paragraphs"][para_hash] = para
                        page_paragraphs.append(para_hash)
                result["content"]["pages"].append({
                    "page_number": 1,
                    "paragraphs": page_paragraphs
                })

    except Exception as e:
        result["content"]["paragraphs"][hash_content(str(e))] = f"Error processing file: {str(e)}"

    return result

## Example usage
#if __name__ == "__main__":
#    file_path = r"C:\Users\Admin\OneDrive - The University of the South Pacific\Documents\fig2_heat.png"  # C:\your\document-file\path
#    output = extract_json_text(file_path)
#    print(json.dumps(output, indent=4))  # This will print the JSON string