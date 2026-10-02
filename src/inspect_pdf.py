"""
Inspect PDF to determine page content types and characteristics.
Identifies which pages contain selectable text, images, tables, or scanned content.
"""

import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path
from typing import Dict, List, Tuple


class PDFInspector:
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(pdf_path)
        self.pdfplumber_doc = pdfplumber.open(pdf_path)

    def get_page_dimensions(self, page_num: int) -> Tuple[float, float]:
        """Get page width and height in points."""
        page = self.doc[page_num]
        rect = page.rect
        return rect.width, rect.height

    def has_selectable_text(self, page_num: int) -> bool:
        """Check if page has selectable (extractable) text."""
        page = self.doc[page_num]
        text = page.get_text()
        return len(text.strip()) > 0

    def get_text_blocks(self, page_num: int) -> List[Dict]:
        """Extract text blocks with coordinates and font info."""
        page = self.doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        
        text_blocks = []
        for block in blocks:
            if block["type"] == 0:  # Text block
                for line in block["lines"]:
                    for span in line["spans"]:
                        text_blocks.append({
                            "text": span["text"],
                            "bbox": span["bbox"],  # (x0, y0, x1, y1)
                            "font": span["font"],
                            "size": span["size"],
                            "flags": span["flags"],
                        })
        return text_blocks

    def has_images(self, page_num: int) -> bool:
        """Check if page contains images."""
        page = self.doc[page_num]
        image_list = page.get_images()
        return len(image_list) > 0

    def get_image_count(self, page_num: int) -> int:
        """Get number of images on page."""
        page = self.doc[page_num]
        return len(page.get_images())

    def detect_tables(self, page_num: int) -> List[Dict]:
        """Detect tables using pdfplumber."""
        page = self.pdfplumber_doc.pages[page_num]
        tables = page.extract_tables()
        
        if not tables:
            return []
        
        detected = []
        for table in tables:
            # Extract table structure
            detected.append({
                "rows": len(table),
                "cols": len(table[0]) if table else 0,
                "content": table,
            })
        return detected

    def get_table_settings(self, page_num: int) -> Dict:
        """Get table detection settings for a page."""
        page = self.pdfplumber_doc.pages[page_num]
        # Check if table detection is needed
        has_lines = bool(page.lines)
        has_rects = bool(page.rects)
        return {
            "has_lines": has_lines,
            "has_rects": has_rects,
            "line_count": len(page.lines),
            "rect_count": len(page.rects),
        }

    def estimate_text_density(self, page_num: int) -> float:
        """Estimate the density of text on the page (0-1)."""
        page = self.doc[page_num]
        text_area = 0
        
        text_blocks = page.get_text("dict")["blocks"]
        for block in text_blocks:
            if block["type"] == 0:
                bbox = block["bbox"]
                area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                text_area += area
        
        page_area = page.rect.width * page.rect.height
        return min(text_area / page_area, 1.0) if page_area > 0 else 0

    def get_page_summary(self, page_num: int) -> Dict:
        """Get comprehensive summary of page content."""
        return {
            "page": page_num,
            "dimensions": self.get_page_dimensions(page_num),
            "has_text": self.has_selectable_text(page_num),
            "text_blocks": len(self.get_text_blocks(page_num)),
            "text_density": self.estimate_text_density(page_num),
            "has_images": self.has_images(page_num),
            "image_count": self.get_image_count(page_num),
            "tables": len(self.detect_tables(page_num)),
            "table_info": self.get_table_settings(page_num),
        }

    def inspect_all_pages(self) -> List[Dict]:
        """Inspect all pages and return summaries."""
        summaries = []
        for page_num in range(len(self.doc)):
            summaries.append(self.get_page_summary(page_num))
        return summaries

    def close(self):
        """Close the PDF documents."""
        self.doc.close()
        self.pdfplumber_doc.close()


if __name__ == "__main__":
    import json
    
    pdf_path = "input/sample.pdf"
    inspector = PDFInspector(pdf_path)
    
    summaries = inspector.inspect_all_pages()
    
    print(json.dumps(summaries, indent=2))
    inspector.close()
