import os
import fitz  # PyMuPDF
from docx import Document
from pptx import Presentation
import csv
import openpyxl

def extract_json_text(file_path):
    def add_content(content, content_type, page_content):
        if not content or not content.strip():
            return None
        
        if content_type == "paragraphs":
            page_content["paragraphs"].append(content)
        elif content_type == "headings":
            page_content["headings"].append(content)

    def process_pdf(file_path):
        doc = fitz.open(file_path)
        for page_num, page in enumerate(doc):
            page_content = {"page_number": page_num + 1, "paragraphs": [], "headings": []}
            # Only extract text, no OCR
            text = page.get_text().strip()
            if text:
                add_content(text, "paragraphs", page_content)
                result["content"]["pages"].append(page_content)

    def process_word(file_path):
        doc = Document(file_path)
        page_content = {"page_number": 1, "paragraphs": [], "headings": []}
        
        # Only process text content
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                content_type = "headings" if para.style.name.startswith('Heading') else "paragraphs"
                add_content(text, content_type, page_content)
        
        if page_content["paragraphs"] or page_content["headings"]:
            result["content"]["pages"].append(page_content)

    def process_ppt(file_path):
        prs = Presentation(file_path)
        for slide_num, slide in enumerate(prs.slides):
            slide_content = {"slide_number": slide_num + 1, "paragraphs": [], "headings": []}
            
            # Only process text content
            for shape in slide.shapes:
                if hasattr(shape, 'text'):
                    text = shape.text.strip()
                    if text:
                        add_content(text, "paragraphs", slide_content)
            
            if slide_content["paragraphs"] or slide_content["headings"]:
                result["content"]["pages"].append(slide_content)

    def process_excel(file_path):
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        for sheet in wb.worksheets:
            sheet_data = []
            for row in sheet.iter_rows():
                cleaned_row = []
                for cell in row:
                    value = str(cell.value) if cell.value is not None else ""
                    if value.strip():
                        cleaned_row.append(value)
                    else:
                        cleaned_row.append("")
                if any(cell for cell in cleaned_row):
                    sheet_data.append(cleaned_row)
            if sheet_data:
                result["content"]["tables"].append({"sheet": sheet.title, "data": sheet_data})

    def process_csv(file_path):
        with open(file_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
            data = []
            for row in csv.reader(csvfile):
                cleaned_row = [cell.strip() for cell in row]
                if any(cleaned_row):
                    data.append(cleaned_row)
            if data:
                result["content"]["tables"].append(data)

    def process_text(file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            text = file.read().strip()
            if text:
                page_content = {"page_number": 1, "paragraphs": [], "headings": []}
                paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                for para in paragraphs:
                    add_content(para, "paragraphs", page_content)
                if page_content["paragraphs"]:
                    result["content"]["pages"].append(page_content)

    result = {
        "metadata": {
            "file_name": os.path.basename(file_path),
            "file_type": os.path.splitext(file_path)[1].lower()
        },
        "content": {
            "tables": [],
            "pages": []
        }
    }

    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            # Skip image files entirely - they'll be handled by read_image_url
            pass
        elif ext == '.pdf':
            process_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            process_word(file_path)
        elif ext in ['.pptx', '.ppt']:
            process_ppt(file_path)
        elif ext in ['.xlsx', '.xls']:
            process_excel(file_path)
        elif ext in ['.csv']:
            process_csv(file_path)
        else:
            process_text(file_path)
    except Exception as e:
        result["content"]["pages"].append({
            "page_number": 1,
            "paragraphs": [f"Error processing file: {str(e)}"],
            "headings": []
        })

    return result
