import os
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
    def apply_ocr(image):
        try:
            return pytesseract.image_to_string(image)
        except pytesseract.TesseractNotFoundError:
            return "[OCR Text: Tesseract not installed]"

    def hash_content(content):
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def add_paragraphs(paragraphs, page_content):
        for para in paragraphs:
            para_hash = hash_content(para)
            result["content"]["paragraphs"][para_hash] = para
            page_content["paragraphs"].append(para_hash)

    def process_image(file_path):
        with Image.open(file_path) as img:
            ocr_text = apply_ocr(img)
            add_paragraphs([ocr_text], {"page_number": 1, "paragraphs": []})

    def process_pdf(file_path):
        doc = fitz.open(file_path)
        for page_num, page in enumerate(doc):
            page_content = {"page_number": page_num + 1, "paragraphs": [], "headings": []}
            # Apply OCR to the entire page image
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))
            ocr_text = apply_ocr(img)
            if ocr_text.strip():
                add_paragraphs([ocr_text], page_content)
            # Extract text from the PDF
            page_text = page.get_text().strip()
            if page_text:
                text_hash = hash_content(page_text)
                result["content"]["paragraphs"][text_hash] = page_text
                page_content["paragraphs"].append(text_hash)
            result["content"]["pages"].append(page_content)

    def process_word(file_path):
        doc = Document(file_path)
        page_content = {"page_number": 1, "paragraphs": [], "headings": []}
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                para_hash = hash_content(text)
                if para.style.name.startswith('Heading'):
                    result["content"]["headings"][para_hash] = text
                    page_content["headings"].append(para_hash)
                else:
                    result["content"]["paragraphs"][para_hash] = text
                    page_content["paragraphs"].append(para_hash)
        result["content"]["pages"].append(page_content)
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                image = Image.open(io.BytesIO(rel.target_part.blob))
                ocr_text = apply_ocr(image)
                add_paragraphs([ocr_text], {"page_number": 1, "paragraphs": []})

    def process_ppt(file_path):
        prs = Presentation(file_path)
        for slide_num, slide in enumerate(prs.slides):
            slide_content = {"slide_number": slide_num + 1, "paragraphs": []}
            for shape in slide.shapes:
                if hasattr(shape, 'text'):
                    text = shape.text.strip()
                    if text:
                        para_hash = hash_content(text)
                        result["content"]["paragraphs"][para_hash] = text
                        slide_content["paragraphs"].append(para_hash)
                if hasattr(shape, "image"):
                    image = Image.open(io.BytesIO(shape.image.blob))
                    ocr_text = apply_ocr(image)
                    add_paragraphs([ocr_text], slide_content)
            result["content"]["pages"].append(slide_content)

    def process_excel(file_path):
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        for sheet in wb.worksheets:
            sheet_data = [[cell.value for cell in row] for row in sheet.iter_rows()]
            result["content"]["tables"].append({"sheet": sheet.title, "data": sheet_data})

    def process_csv(file_path):
        with open(file_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
            result["content"]["tables"].append([row for row in csv.reader(csvfile)])

    def process_text(file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            paragraphs = [p.strip() for p in file.read().split('\n\n') if p.strip()]
            add_paragraphs(paragraphs, {"page_number": 1, "paragraphs": []})

    result = {
        "metadata": {
            "file_name": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path),
            "file_type": os.path.splitext(file_path)[1].lower(),
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

    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            process_image(file_path)
        elif ext == '.pdf':
            process_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            process_word(file_path)
        elif ext in ['.pptx', '.ppt']:
            process_ppt(file_path)
        elif ext in ['.xlsx', '.xls']:
            process_excel(file_path)
        elif ext == '.csv':
            process_csv(file_path)
        else:
            process_text(file_path)
    except Exception as e:
        result["content"]["paragraphs"][hash_content(str(e))] = f"Error processing file: {str(e)}"

    return result