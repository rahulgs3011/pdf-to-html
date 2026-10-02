"""
Detect and extract table structures from PDF pages.
Converts table cells to HTML tables or positioned elements based on structure confidence.
"""

import pdfplumber
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json


class TableDetector:
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.doc = pdfplumber.open(pdf_path)

    def detect_tables(self, page_num: int) -> List[Dict]:
        """Detect tables on a page using pdfplumber."""
        page = self.doc.pages[page_num]
        tables = page.extract_tables()
        
        if not tables:
            return []
        
        detected = []
        for table_idx, table in enumerate(tables):
            # Get table bounding box
            bbox = self._get_table_bbox(page, table_idx)
            
            detected.append({
                "table_idx": table_idx,
                "rows": len(table),
                "cols": len(table[0]) if table else 0,
                "bbox": bbox,
                "content": table,
                "confidence": self._assess_confidence(page, table),
            })
        
        return detected

    def _get_table_bbox(self, page, table_idx: int) -> Tuple[float, float, float, float]:
        """Get bounding box of a table."""
        # Use table detection settings
        tables = page.find_tables()
        if table_idx < len(tables):
            table_obj = tables[table_idx]
            bbox = table_obj.bbox
            return (bbox[0], bbox[1], bbox[2], bbox[3])
        return (0, 0, page.width, page.height)

    def _assess_confidence(self, page, table: List[List[str]]) -> float:
        """Assess confidence in table structure (0-1)."""
        if not table:
            return 0.0
        
        # Check if table has consistent column count
        col_counts = [len(row) for row in table]
        if not col_counts:
            return 0.0
        
        expected_cols = col_counts[0]
        consistent_cols = all(count == expected_cols for count in col_counts)
        
        # Check if cells have content
        non_empty_cells = sum(1 for row in table for cell in row if cell and cell.strip())
        fill_rate = non_empty_cells / (len(table) * expected_cols) if table else 0
        
        # Combine metrics
        consistency_score = 1.0 if consistent_cols else 0.7
        confidence = consistency_score * (0.5 + 0.5 * fill_rate)
        
        return min(confidence, 1.0)

    def extract_table_html(self, page_num: int, table: Dict) -> str:
        """Convert a detected table to HTML."""
        rows = table["content"]
        cols = table["cols"]
        
        html_lines = ['<table class="extracted-table" style="border-collapse: collapse;">']
        
        for row_idx, row in enumerate(rows):
            html_lines.append("  <tr>")
            for col_idx, cell in enumerate(row):
                cell_text = cell.strip() if cell else ""
                # Escape HTML
                cell_text = (cell_text
                             .replace("&", "&amp;")
                             .replace("<", "&lt;")
                             .replace(">", "&gt;"))
                html_lines.append(f'    <td>{cell_text}</td>')
            html_lines.append("  </tr>")
        
        html_lines.append("</table>")
        return "\n".join(html_lines)

    def extract_positioned_table(self, page_num: int, table: Dict) -> str:
        """Convert table to positioned div elements (for complex layouts)."""
        rows = table["content"]
        bbox = table["bbox"]
        x0, y0, x1, y1 = bbox
        
        width = x1 - x0
        height = y1 - y0
        
        # Calculate cell dimensions
        cell_width = width / table["cols"] if table["cols"] > 0 else width
        cell_height = height / table["rows"] if table["rows"] > 0 else height
        
        html_lines = [
            f'<div class="table-grid" style="position: absolute; left: {x0}px; top: {y0}px; '
            f'width: {width}px; height: {height}px; border: 1px solid #333;">'
        ]
        
        for row_idx, row in enumerate(rows):
            for col_idx, cell in enumerate(row):
                cell_text = cell.strip() if cell else ""
                cell_text = (cell_text
                             .replace("&", "&amp;")
                             .replace("<", "&lt;")
                             .replace(">", "&gt;"))
                
                cell_x = x0 + col_idx * cell_width
                cell_y = y0 + row_idx * cell_height
                
                html_lines.append(
                    f'  <div class="table-cell" style="position: absolute; '
                    f'left: {cell_x}px; top: {cell_y}px; width: {cell_width}px; '
                    f'height: {cell_height}px; border: 1px solid #ccc; '
                    f'padding: 4px; overflow: hidden; font-size: 12px;">{cell_text}</div>'
                )
        
        html_lines.append("</div>")
        return "\n".join(html_lines)

    def get_tables_for_page(self, page_num: int) -> List[Dict]:
        """Get all tables detected on a page with metadata."""
        return self.detect_tables(page_num)

    def extract_all_tables(self) -> List[Dict]:
        """Extract tables from all pages."""
        all_tables = []
        for page_num in range(len(self.doc.pages)):
            tables = self.detect_tables(page_num)
            if tables:
                all_tables.append({
                    "page": page_num,
                    "tables": tables,
                })
        return all_tables

    def close(self):
        """Close the PDF document."""
        self.doc.close()


if __name__ == "__main__":
    detector = TableDetector("input/sample.pdf")
    all_tables = detector.extract_all_tables()
    
    with open("output/detected_tables.json", "w") as f:
        json.dump(all_tables, f, indent=2)
    
    print("Table detection complete.")
    detector.close()
