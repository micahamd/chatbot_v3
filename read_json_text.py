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
                "text": "The 'text' field contains the concatenated text content of the file.",
                "paragraphs": "The 'paragraphs' field is a dictionary where keys are MD5 hashes of paragraph content and values are the paragraph text. This helps in deduplication.",
                "headings": "The 'headings' field is a dictionary where keys are MD5 hashes of heading content and values are the heading text.",
                "tables": "The 'tables' field is a list of tables extracted from the document. Each table is represented as a list of rows, where each row is a list of cell values.",
                "pages": "The 'pages' field is a list of dictionaries, each representing a page or slide. Each dictionary contains the page/slide number, text content, and lists of paragraph and heading hashes."
            }
        },
        "content": {
            "text": "",
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
                result["content"]["text"] = ocr_text
                para_hash = hash_content(ocr_text)
                seen_paragraphs[para_hash] = ocr_text

        # Process PDF files
        elif ext == '.pdf':
            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc):
                page_text = page.get_text("text")
                page_paragraphs = page_text.split('\n\n')
                page_headings = []
                for block in page.get_text("dict")["blocks"]:
                    if block["type"] == 0:  # Text block
                        for line in block["lines"]:
                            for span in line["spans"]:
                                if span["font"].startswith("Heading"):
                                    page_headings.append(span["text"])

                # Deduplicate paragraphs and headings
                unique_paragraphs = {}
                unique_headings = {}
                for para in page_paragraphs:
                    para_hash = hash_content(para)
                    if para_hash not in seen_paragraphs:
                        unique_paragraphs[para_hash] = para
                        seen_paragraphs[para_hash] = para

                for heading in page_headings:
                    heading_hash = hash_content(heading)
                    if heading_hash not in seen_headings:
                        unique_headings[heading_hash] = heading
                        seen_headings[heading_hash] = heading

                result["content"]["text"] += page_text
                result["content"]["paragraphs"].update(unique_paragraphs)
                result["content"]["headings"].update(unique_headings)
                result["content"]["pages"].append({
                    "page_number": page_num + 1,
                    "text": page_text,
                    "paragraphs": list(unique_paragraphs.keys()),
                    "headings": list(unique_headings.keys())
                })

        # Process Word documents
        elif ext in ['.docx', '.doc']:
            doc = Document(file_path)
            for para in doc.paragraphs:
                para_text = para.text
                para_hash = hash_content(para_text)
                if para_hash not in seen_paragraphs:
                    result["content"]["text"] += para_text + "\n"
                    seen_paragraphs[para_hash] = para_text
                    result["content"]["paragraphs"][para_hash] = para_text
                if para.style.name.startswith('Heading') and para_hash not in seen_headings:
                    seen_headings[para_hash] = para_text
                    result["content"]["headings"][para_hash] = para_text
            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    row_data = [cell.text for cell in row.cells]
                    table_data.append(row_data)
                result["content"]["tables"].append(table_data)
            
            # Extract images and apply OCR
            for rel in doc.part.rels.values():
                if "image" in rel.target_ref:
                    image = Image.open(io.BytesIO(rel.target_part.blob))
                    ocr_text = apply_ocr(image)
                    result["content"]["text"] += ocr_text + "\n"
                    para_hash = hash_content(ocr_text)
                    if para_hash not in seen_paragraphs:
                        seen_paragraphs[para_hash] = ocr_text
                        result["content"]["paragraphs"][para_hash] = ocr_text

        # Process PowerPoint presentations
        elif ext in ['.pptx', '.ppt']:
            prs = Presentation(file_path)
            for slide_num, slide in enumerate(prs.slides):
                slide_text = ""
                slide_paragraphs = []
                for shape in slide.shapes:
                    if hasattr(shape, 'text'):
                        shape_text = shape.text
                        slide_text += shape_text + "\n"
                        para_hash = hash_content(shape_text)
                        if para_hash not in seen_paragraphs:
                            slide_paragraphs.append(para_hash)
                            seen_paragraphs[para_hash] = shape_text
                            result["content"]["paragraphs"][para_hash] = shape_text
                    if hasattr(shape, "image"):
                        image = Image.open(io.BytesIO(shape.image.blob))
                        ocr_text = apply_ocr(image)
                        slide_text += ocr_text + "\n"
                        para_hash = hash_content(ocr_text)
                        if para_hash not in seen_paragraphs:
                            slide_paragraphs.append(para_hash)
                            seen_paragraphs[para_hash] = ocr_text
                            result["content"]["paragraphs"][para_hash] = ocr_text
                result["content"]["text"] += slide_text
                result["content"]["pages"].append({
                    "slide_number": slide_num + 1,
                    "text": slide_text,
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
                unique_paragraphs = {}
                for para in paragraphs:
                    para_hash = hash_content(para)
                    if para_hash not in seen_paragraphs:
                        unique_paragraphs[para_hash] = para
                        seen_paragraphs[para_hash] = para
                result["content"]["text"] = text
                result["content"]["paragraphs"].update(unique_paragraphs)

        # Default processing for other file types
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
                paragraphs = text.split('\n\n')
                unique_paragraphs = {}
                for para in paragraphs:
                    para_hash = hash_content(para)
                    if para_hash not in seen_paragraphs:
                        unique_paragraphs[para_hash] = para
                        seen_paragraphs[para_hash] = para
                result["content"]["text"] = text
                result["content"]["paragraphs"].update(unique_paragraphs)

    except Exception as e:
        # Handle any exceptions that occur during file processing
        result["content"]["text"] = f"Error processing file: {str(e)}"

    return result

## Example usage
#if __name__ == "__main__":
#    file_path = r"C:\Users\Admin\OneDrive - The University of the South Pacific\Documents\fig2_heat.png"  # C:\your\document-file\path
#    output = extract_json_text(file_path)
#    print(json.dumps(output, indent=4))  # This will print the JSON string