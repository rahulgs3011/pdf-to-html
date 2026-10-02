"""
Run OCR on scanned pages or image-only regions to extract text and coordinates.
Uses Tesseract via pytesseract.
"""

import pytesseract
import fitz  # PyMuPDF
from pdf2image import convert_from_path
from pathlib import Path
from typing import Dict, List, Optional
import json


class OCRProcessor:
    def __init__(self, pdf_path: str, output_dir: str = None):
        self.pdf_path = Path(pdf_path)
        
        # If no output dir specified, create one based on PDF filename
        if output_dir is None:
            pdf_name = Path(pdf_path).stem
            output_dir = f"output-{pdf_name}"
        
        self.output_dir = Path(output_dir)
        self.doc = fitz.open(pdf_path)

    def check_tesseract_installed(self) -> bool:
        """Check if Tesseract is installed."""
        try:
            pytesseract.get_tesseract_version()
            return True
        except pytesseract.TesseractNotFoundError:
            return False

    def render_page_to_image(self, page_num: int, dpi: int = 150) -> Optional[object]:
        """Render a PDF page to an image (PIL Image)."""
        try:
            images = convert_from_path(
                str(self.pdf_path),
                first_page=page_num + 1,
                last_page=page_num + 1,
                dpi=dpi,
            )
            return images[0] if images else None
        except Exception as e:
            print(f"Error rendering page {page_num}: {e}")
            return None

    def ocr_image(self, image, lang: str = "eng") -> Dict:
        """Run OCR on an image using Tesseract."""
        try:
            # Get data with coordinates
            data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
            
            text_elements = []
            for i in range(len(data["text"])):
                if data["text"][i].strip():  # Skip empty strings
                    text_elements.append({
                        "text": data["text"][i],
                        "x": int(data["left"][i]),
                        "y": int(data["top"][i]),
                        "width": int(data["width"][i]),
                        "height": int(data["height"][i]),
                        "confidence": int(data["conf"][i]),
                        "level": int(data["level"][i]),
                    })
            
            return {
                "success": True,
                "text_elements": text_elements,
                "full_text": pytesseract.image_to_string(image, lang=lang),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text_elements": [],
                "full_text": "",
            }

    def ocr_page(self, page_num: int, lang: str = "eng", dpi: int = 150) -> Dict:
        """Run OCR on a PDF page."""
        print(f"Running OCR on page {page_num}...")
        
        # Render page to image
        image = self.render_page_to_image(page_num, dpi=dpi)
        if image is None:
            return {
                "page": page_num,
                "success": False,
                "error": "Failed to render page to image",
            }
        
        # Run OCR
        ocr_result = self.ocr_image(image, lang=lang)
        
        # Get page dimensions
        page = self.doc[page_num]
        rect = page.rect
        
        return {
            "page": page_num,
            "page_width": rect.width,
            "page_height": rect.height,
            "success": ocr_result["success"],
            "error": ocr_result.get("error"),
            "text_elements": ocr_result["text_elements"],
            "full_text": ocr_result["full_text"],
        }

    def ocr_all_pages(self, lang: str = "eng", dpi: int = 150) -> List[Dict]:
        """Run OCR on all pages."""
        if not self.check_tesseract_installed():
            print("WARNING: Tesseract is not installed. OCR will not work.")
            print("Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")
            return []
        
        results = []
        for page_num in range(len(self.doc)):
            result = self.ocr_page(page_num, lang=lang, dpi=dpi)
            results.append(result)
        
        return results

    def ocr_page_region(
        self, 
        page_num: int, 
        x0: float, 
        y0: float, 
        x1: float, 
        y1: float, 
        lang: str = "eng",
    ) -> Dict:
        """Run OCR on a specific region of a page."""
        page = self.doc[page_num]
        
        # Clip to region
        clip_rect = fitz.Rect(x0, y0, x1, y1)
        
        # Render clipped region
        pix = page.get_pixmap(clip=clip_rect, alpha=False)
        from PIL import Image
        import io
        
        # Convert pixmap to PIL Image
        img_data = pix.tobytes("ppm")
        image = Image.open(io.BytesIO(img_data))
        
        # Run OCR
        ocr_result = self.ocr_image(image, lang=lang)
        
        # Adjust coordinates back to page space
        adjusted_elements = []
        for elem in ocr_result["text_elements"]:
            adjusted_elements.append({
                "text": elem["text"],
                "x": elem["x"] + x0,
                "y": elem["y"] + y0,
                "width": elem["width"],
                "height": elem["height"],
                "confidence": elem["confidence"],
            })
        
        return {
            "page": page_num,
            "region": (x0, y0, x1, y1),
            "success": ocr_result["success"],
            "text_elements": adjusted_elements,
            "full_text": ocr_result["full_text"],
        }

    def close(self):
        """Close the PDF document."""
        self.doc.close()


if __name__ == "__main__":
    processor = OCRProcessor("input/sample.pdf")
    
    if processor.check_tesseract_installed():
        results = processor.ocr_all_pages()
        
        with open("output/ocr_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print("OCR processing complete.")
    else:
        print("Tesseract is not installed. Cannot run OCR.")
    
    processor.close()
