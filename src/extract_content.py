"""
Extract text and images from PDF pages while preserving coordinates and metadata.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from PIL import Image
import io


class ContentExtractor:
    def __init__(self, pdf_path: str, output_dir: str = None):
        self.pdf_path = Path(pdf_path)
        
        # If no output dir specified, create one based on PDF filename
        if output_dir is None:
            pdf_name = Path(pdf_path).stem
            output_dir = f"output-{pdf_name}"
        
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.doc = fitz.open(pdf_path)
        self.image_counter = 0

    def extract_text_with_coords(self, page_num: int) -> List[Dict]:
        """Extract text with precise coordinates, size, and font information."""
        page = self.doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        
        text_elements = []
        for block in blocks:
            if block["type"] == 0:  # Text block
                for line in block["lines"]:
                    for span in line["spans"]:
                        x0, y0, x1, y1 = span["bbox"]
                        text_elements.append({
                            "text": span["text"],
                            "x": x0,
                            "y": y0,
                            "width": x1 - x0,
                            "height": y1 - y0,
                            "font": span["font"],
                            "size": span["size"],
                            "color": span["color"],  # RGB color value
                            "flags": span["flags"],  # Bold, italic, etc.
                            "is_bold": span["flags"] & 2**0,
                            "is_italic": span["flags"] & 2**1,
                        })
        
        return text_elements

    def extract_images(self, page_num: int) -> List[Dict]:
        """Extract images from a page and save them to disk."""
        page = self.doc[page_num]
        image_list = page.get_images()
        
        extracted_images = []
        for img_index, img_xref in enumerate(image_list):
            try:
                # Get image as pixmap
                pix = fitz.Pixmap(self.doc, img_xref[0])
                
                # Convert CMYK to RGB if needed
                if pix.n - pix.alpha > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                
                # Get image rectangle on page
                rects = page.get_image_rects(img_xref[0])
                if not rects:
                    continue
                
                rect = rects[0]
                
                # Save image
                filename = f"page_{page_num}_img_{self.image_counter}.png"
                filepath = self.images_dir / filename
                pix.save(str(filepath))
                
                extracted_images.append({
                    "filename": filename,
                    "x": rect.x0,
                    "y": rect.y0,
                    "width": rect.width,
                    "height": rect.height,
                    "page": page_num,
                })
                
                self.image_counter += 1
                pix = None  # Free memory
                
            except Exception as e:
                print(f"Error extracting image {img_index} from page {page_num}: {e}")
        
        return extracted_images

    def get_page_content(self, page_num: int) -> Dict:
        """Extract all content from a page."""
        page = self.doc[page_num]
        rect = page.rect
        
        return {
            "page": page_num,
            "width": rect.width,
            "height": rect.height,
            "text_elements": self.extract_text_with_coords(page_num),
            "images": self.extract_images(page_num),
        }

    def extract_all_pages(self) -> List[Dict]:
        """Extract content from all pages."""
        all_content = []
        for page_num in range(len(self.doc)):
            print(f"Extracting content from page {page_num}...")
            all_content.append(self.get_page_content(page_num))
        return all_content

    def close(self):
        """Close the PDF document."""
        self.doc.close()


if __name__ == "__main__":
    import json
    
    extractor = ContentExtractor("input/sample.pdf")
    content = extractor.extract_all_pages()
    
    # Save content to JSON for later use
    with open("output/extracted_content.json", "w") as f:
        json.dump(content, f, indent=2)
    
    print("Content extraction complete.")
    extractor.close()
