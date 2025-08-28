import pytesseract
from PIL import Image
import fitz  # PyMuPDF for PDFs

def extract_text(file_path: str) -> str:
    if file_path.endswith(".pdf"):
        text = ""
        pdf = fitz.open(file_path)
        for page in pdf:
            text += page.get_text()
        return text if text.strip() else pytesseract.image_to_string(Image.open(file_path))
    else:
        return pytesseract.image_to_string(Image.open(file_path))
