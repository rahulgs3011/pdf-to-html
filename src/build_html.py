"""
Build a single scrollable HTML document from extracted PDF content.
All pages are stacked vertically in order. Images are referenced from the images/ folder.
Text and elements are positioned to match the PDF layout.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from html import escape


class HTMLBuilder:
    def __init__(self, output_dir: str = None):
        if output_dir is None:
            output_dir = "output"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_html_document(
        self,
        content: List[Dict],
        tables: Optional[List[Dict]] = None,
        title: str = "PDF to HTML",
    ) -> str:
        """Build complete HTML document from extracted content."""
        html_parts = []
        
        # HTML Header
        html_parts.append(self._build_header(title))
        
        # Body
        html_parts.append("<body>")
        html_parts.append('<div class="document-container">')
        
        # Pages
        tables_by_page = self._index_tables_by_page(tables) if tables else {}
        
        for page_data in content:
            page_num = page_data["page"]
            page_tables = tables_by_page.get(page_num, [])
            html_parts.append(self._build_page(page_data, page_tables))
        
        html_parts.append("</div>")
        html_parts.append("</body>")
        html_parts.append("</html>")
        
        return "\n".join(html_parts)

    def _build_header(self, title: str) -> str:
        """Build HTML header with styles."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)}</title>
    <link rel="stylesheet" href="styles.css">
</head>"""

    def _build_page(self, page_data: Dict, page_tables: List[Dict] = None) -> str:
        """Build HTML for a single page."""
        page_num = page_data["page"]
        width = page_data["width"]
        height = page_data["height"]
        text_elements = page_data.get("text_elements", [])
        images = page_data.get("images", [])
        page_tables = page_tables or []
        
        lines = [
            f'<section class="pdf-page" id="page-{page_num}" '
            f'style="width: {width}px; height: {height}px; position: relative; '
            f'border: 1px solid #ddd; margin: 20px auto; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">'
        ]
        
        # Add page number
        lines.append(
            f'<div class="page-number" style="position: absolute; bottom: 10px; right: 10px; '
            f'font-size: 12px; color: #999;">Page {page_num + 1}</div>'
        )
        
        # Add images
        for img_data in images:
            lines.append(self._build_image_element(img_data))
        
        # Add text elements
        for text_elem in text_elements:
            lines.append(self._build_text_element(text_elem))
        
        # Add tables (if any detected on this page)
        for table_data in page_tables:
            lines.append(self._build_table_element(table_data))
        
        lines.append("</section>")
        
        return "\n".join(lines)

    def _build_text_element(self, text_elem: Dict) -> str:
        """Build positioned text element with color preservation."""
        text = escape(text_elem.get("text", ""))
        x = text_elem.get("x", 0)
        y = text_elem.get("y", 0)
        width = text_elem.get("width", 100)
        height = text_elem.get("height", 20)
        size = text_elem.get("size", 12)
        is_bold = text_elem.get("is_bold", False)
        is_italic = text_elem.get("is_italic", False)
        color = text_elem.get("color")  # RGB color value from PDF
        
        # Build style
        style_parts = [
            f"position: absolute",
            f"left: {x}px",
            f"top: {y}px",
            f"width: {width}px",
            f"height: {height}px",
            f"font-size: {size}px",
            f"line-height: 1.2",
            f"white-space: pre-wrap",
            f"word-wrap: break-word",
            f"overflow: hidden",
        ]
        
        if is_bold:
            style_parts.append("font-weight: bold")
        if is_italic:
            style_parts.append("font-style: italic")
        
        # Preserve text color from PDF
        if color is not None:
            # Convert RGB color value to hex
            hex_color = self._convert_color_to_hex(color)
            if hex_color:
                style_parts.append(f"color: {hex_color}")
        
        style = "; ".join(style_parts) + ";"
        
        return f'<div class="text-element" style="{style}">{text}</div>'
    
    def _convert_color_to_hex(self, color: int) -> str:
        """Convert RGB color value from PDF to hex color string."""
        if color is None or color == 0:
            return None
        
        # Extract RGB components
        # PyMuPDF returns color as: (R<<16) | (G<<8) | B
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        
        # Skip if color is black (default, no preservation needed)
        if r == 0 and g == 0 and b == 0:
            return None
        
        return f"#{r:02x}{g:02x}{b:02x}"

    def _build_image_element(self, img_data: Dict) -> str:
        """Build positioned image element."""
        filename = img_data.get("filename", "")
        x = img_data.get("x", 0)
        y = img_data.get("y", 0)
        width = img_data.get("width", 100)
        height = img_data.get("height", 100)
        
        return (
            f'<img class="pdf-image" src="images/{filename}" '
            f'style="position: absolute; left: {x}px; top: {y}px; '
            f'width: {width}px; height: {height}px; object-fit: contain;" '
            f'alt="Page image" />'
        )

    def _build_table_element(self, table_data: Dict) -> str:
        """Build table element."""
        rows = table_data.get("content", [])
        bbox = table_data.get("bbox", (0, 0, 200, 200))
        x0, y0, x1, y1 = bbox
        width = x1 - x0
        height = y1 - y0
        
        lines = [
            f'<table class="extracted-table" style="position: absolute; '
            f'left: {x0}px; top: {y0}px; width: {width}px; '
            f'border-collapse: collapse; border: 1px solid #333;">'
        ]
        
        for row in rows:
            lines.append("<tr>")
            for cell in row:
                cell_text = escape(cell.strip() if cell else "")
                lines.append(f'<td style="border: 1px solid #ccc; padding: 4px;">{cell_text}</td>')
            lines.append("</tr>")
        
        lines.append("</table>")
        
        return "\n".join(lines)

    def _index_tables_by_page(self, tables: List[Dict]) -> Dict[int, List]:
        """Index tables by page number."""
        index = {}
        for page_entry in tables:
            page_num = page_entry.get("page")
            page_tables = page_entry.get("tables", [])
            index[page_num] = page_tables
        return index

    def generate_css(self) -> str:
        """Generate CSS stylesheet."""
        return """/* PDF to HTML Stylesheet */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: #f5f5f5;
    color: #333;
    line-height: 1.6;
}

.document-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
}

/* PDF Pages */
.pdf-page {
    background: white;
    margin: 20px auto;
    page-break-after: avoid;
    position: relative;
    overflow: hidden;
}

.page-number {
    color: #999;
    font-size: 12px;
}

/* Text Elements */
.text-element {
    font-family: inherit;
}

/* Images */
.pdf-image {
    max-width: 100%;
    height: auto;
}

/* Tables */
.extracted-table {
    font-size: 12px;
}

.extracted-table td {
    padding: 8px;
    vertical-align: top;
    background: white;
}

.extracted-table tr:nth-child(even) td {
    background: #f9f9f9;
}

.extracted-table tr:hover td {
    background: #f0f0f0;
}

.table-grid {
    border: 1px solid #333;
}

.table-cell {
    border: 1px solid #ccc;
    padding: 4px;
    font-size: 12px;
    vertical-align: top;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Print Styles */
@media print {
    body {
        background: white;
    }
    
    .toc {
        page-break-after: always;
    }
    
    .pdf-page {
        page-break-after: always;
        page-break-inside: avoid;
        margin: 0;
        box-shadow: none;
    }
}

/* Responsive */
@media (max-width: 768px) {
    .document-container {
        padding: 10px;
    }
    
    .pdf-page {
        margin: 10px auto;
    }
    
    .toc {
        font-size: 14px;
    }
}
"""

    def save_html(self, html: str, filename: str = "index.html"):
        """Save HTML to file."""
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML saved to {filepath}")

    def save_css(self, css: str, filename: str = "styles.css"):
        """Save CSS to file."""
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(css)
        print(f"CSS saved to {filepath}")


if __name__ == "__main__":
    # Load extracted content
    with open("output/extracted_content.json", "r") as f:
        content = json.load(f)
    
    # Load tables (optional)
    tables = None
    try:
        with open("output/detected_tables.json", "r") as f:
            tables = json.load(f)
    except FileNotFoundError:
        pass
    
    # Build HTML
    builder = HTMLBuilder("output")
    html = builder.build_html_document(content, tables, title="PDF to HTML")
    css = builder.generate_css()
    
    # Save files
    builder.save_html(html)
    builder.save_css(css)
    
    print("HTML document generation complete.")
