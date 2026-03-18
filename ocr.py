import pytesseract
from PIL import Image
import pdfplumber

def extract_text(file_obj, filename: str) -> str:
    """
    Unified function to extract text from an uploaded file object.
    Supports both images (via pytesseract) and PDFs (via pdfplumber).
    """
    ext = filename.split('.')[-1].lower()
    text = ""
    try:
        if ext == 'pdf':
            with pdfplumber.open(file_obj) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        elif ext in ['jpg', 'jpeg', 'png', 'bmp', 'tiff']:
            image = Image.open(file_obj)
            text = pytesseract.image_to_string(image)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
            
        if not text.strip():
            raise ValueError("No text could be extracted from the file.")
            
        return text.strip()
    except Exception as e:
        raise Exception(f"OCR Error: {str(e)}")
