import os
import io
import re
from PIL import Image
import pytesseract
import fitz
from docx import Document
from pptx import Presentation
import csv
import openpyxl
import hashlib
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import pdfplumber

class DocumentStructure:
    def __init__(self):
        self.content_map = {}
        self.structure = {"metadata": {}, "content": {"text": {}, "tables": [], "pages": []}}
    
    def add_table(self, table_data: List[List[str]], page_num: int) -> str:
        table_hash = hashlib.md5(str(table_data).encode()).hexdigest()[:8]
        self.structure["content"]["tables"].append({
            "hash": table_hash,
            "page": page_num,
            "data": table_data
        })
        return table_hash

def extract_json_text(file_path):
    doc_structure = DocumentStructure()
    
    def apply_ocr(image):
        try:
            return pytesseract.image_to_string(image)
        except pytesseract.TesseractNotFoundError:
            return ""

    def hash_content(content):
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:8]  # Shortened hash

    def add_content(content, check_similar=True):
        if len(content.strip()) < 5:
            return None
            
        content_hash = hash_content(content)
        
        # Check for similar existing content
        if check_similar:
            for existing_hash, existing_content in unique_contents.items():
                pass  # Replace with actual code
                    
        if content_hash not in unique_contents:
            unique_contents[content_hash] = content
        return content_hash

    def extract_tables_from_pdf(page, page_num):
        tables = []
        try:
            with pdfplumber.open(file_path) as pdf:
                pass  # Replace with actual code
        except ImportError:
            pass
        return tables

    def extract_tables_from_docx(doc):
        tables = []
        for table in doc.tables:
            table_data = []
            for row in table.rows:
                cell_data = [cell.text for cell in row.cells]
                table_data.append(cell_data)
            tables.append(table_data)
        return tables

    unique_contents = {}

    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            image = Image.open(file_path)
            ocr_text = apply_ocr(image)
            if ocr_text.strip():
                content_hash = add_content(ocr_text.strip())
                if content_hash:
                    doc_structure.structure["content"]["pages"].append({"n": 1, "h": [content_hash]})

        elif ext == '.pdf':
            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc, start=1):
                # Extract text
                page_text = page.get_text().strip()
                content_hash = add_content(page_text) if page_text else None
                
                # Extract tables
                tables = extract_tables_from_pdf(page, page_num)
                table_hashes = [doc_structure.add_table(table, page_num) for table in tables]
                
                if content_hash or table_hashes:
                    doc_structure.structure["content"]["pages"].append({
                        "n": page_num,
                        "h": [content_hash] if content_hash else [],
                        "t": table_hashes
                    })

        elif ext in ['.docx', '.doc']:
            doc = Document(file_path)
            
            # Extract metadata
            doc_structure.structure["metadata"] = {
                "title": doc.core_properties.title,
                "author": doc.core_properties.author,
                "created": str(doc.core_properties.created)
            }
            
            # Extract content with structure
            page_content = []
            current_heading = None
            
            for element in doc.element.body:
                if element.tag.endswith('p'):
                    if element.style and element.style.type == 'heading':
                        current_heading = element.text
                    content_hash = add_content(element.text.strip())
                    if content_hash:
                        page_content.append({
                            "hash": content_hash,
                            "type": "heading" if current_heading else "paragraph"
                        })
                
                elif element.tag.endswith('tbl'):
                    table_data = extract_tables_from_docx([element])
                    for table in table_data:
                        table_hash = doc_structure.add_table(table, 1)
                        page_content.append({"hash": table_hash, "type": "table"})
            
            if page_content:
                doc_structure.structure["content"]["pages"].append({
                    "n": 1,
                    "elements": page_content
                })

        elif ext in ['.pptx', '.ppt']:
            prs = Presentation(file_path)
            for slide_num, slide in enumerate(prs.slides, start=1):
                slide_content = []
                for shape in slide.shapes:
                    if hasattr(shape, 'text') and shape.text.strip():
                        content_hash = add_content(shape.text.strip())
                        if content_hash:
                            slide_content.append(content_hash)
                if slide_content:
                    doc_structure.structure["content"]["pages"].append({"n": slide_num, "h": slide_content})

        elif ext in ['.xlsx', '.xls']:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            for sheet in wb.worksheets:
                sheet_content = []
                for row in sheet.iter_rows():
                    row_text = ' '.join(str(cell.value).strip() for cell in row if cell.value)
                    if row_text:
                        content_hash = add_content(row_text)
                        if content_hash:
                            sheet_content.append(content_hash)
                if sheet_content:
                    doc_structure.structure["content"]["pages"].append({"s": sheet.title, "h": sheet_content})

        elif ext == '.csv':
            with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                page_content = []
                for row in reader:
                    row_text = ' '.join(cell.strip() for cell in row if cell.strip())
                    if row_text:
                        content_hash = add_content(row_text)
                        if content_hash:
                            page_content.append(content_hash)
                if page_content:
                    doc_structure.structure["content"]["pages"].append({"n": 1, "h": page_content})

        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read().strip()
                if text:
                    content_hash = add_content(text)
                    if content_hash:
                        doc_structure.structure["content"]["pages"].append({"n": 1, "h": [content_hash]})

    except Exception:
        pass  # Removed error messages

    doc_structure.structure["content"]["text"] = unique_contents
    return doc_structure.structure