import fitz  # PyMuPDF
import tempfile
from pathlib import Path
import os
import easyocr
from dotenv import load_dotenv

# Load environment variables (still here if you want to keep Vision API option)
load_dotenv()

# Initialize EasyOCR reader (English by default, add more langs if needed)
easyocr_reader = easyocr.Reader(['en'])

def extract_text_from_pdf(file):
    """
    Extract text from a PDF.
    - Uses PyMuPDF for native text.
    - Falls back to EasyOCR for scanned or low-quality PDFs.
    """
    doc = fitz.open(stream=file.read(), filetype="pdf")
    all_text = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text().strip()

        # Mark text as junk if very short or looks like a scan
        is_junk = len(text) < 30 or "camscanner" in text.lower()

        if text and not is_junk:
            # Use normal text extraction
            all_text.append(text)
        else:
            # Convert page to high-res image
            pix = page.get_pixmap(dpi=300)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
                img_path = Path(tmp_img.name)
                pix.save(img_path)

            # OCR fallback using EasyOCR
            ocr_text = easyocr_ocr(str(img_path))
            if ocr_text.strip():
                all_text.append(ocr_text)
            else:
                all_text.append(f"[Page {page_num}] Unable to extract text.")

            # Clean up temp image
            if img_path.exists():
                img_path.unlink()

    return "\n".join(all_text)


def easyocr_ocr(image_path):
    """
    Extract text from an image using EasyOCR.
    """
    try:
        results = easyocr_reader.readtext(image_path, detail=0, paragraph=True)
        return "\n".join(results).strip()
    except Exception as e:
        print(f"EasyOCR error on {image_path}: {e}")
        return ""


def chunk_text(text, max_tokens=500):
    """
    Break large text into smaller chunks suitable for summarization.
    Approximation: ~4 chars = 1 token.
    """
    max_chars = max_tokens * 4
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start = end
    return chunks
