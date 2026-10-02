"""
Render PDF and HTML for visual comparison to refine layout and styling.
Helps identify mismatches in positioning, fonts, spacing, and table borders.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, Optional
import json
from PIL import Image, ImageDraw, ImageFont


class RenderComparison:
    def __init__(self, pdf_path: str, output_dir: str = None):
        self.pdf_path = Path(pdf_path)
        
        # If no output dir specified, create one based on PDF filename
        if output_dir is None:
            pdf_name = Path(pdf_path).stem
            output_dir = f"output-{pdf_name}"
        
        self.output_dir = Path(output_dir)
        self.comparison_dir = self.output_dir / "comparison"
        self.comparison_dir.mkdir(parents=True, exist_ok=True)
        self.doc = fitz.open(pdf_path)

    def render_pdf_page(self, page_num: int, dpi: int = 150) -> Image.Image:
        """Render a PDF page to PIL Image."""
        page = self.doc[page_num]
        
        # Increase zoom for higher DPI
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # Convert pixmap to PIL Image
        img_data = pix.tobytes("ppm")
        image = Image.open(fitz.io.BytesIO(img_data))
        
        return image

    def render_html_page_screenshot(self, page_num: int) -> Optional[Image.Image]:
        """
        Render HTML page screenshot using Playwright or similar.
        This is a placeholder - actual implementation would use a headless browser.
        """
        # This would require Playwright or Selenium
        # For now, return None - user would need to screenshot manually
        print(f"Note: HTML screenshots require a headless browser. Please manually screenshot page {page_num}")
        return None

    def create_comparison_image(
        self,
        page_num: int,
        pdf_image: Image.Image,
        html_image: Optional[Image.Image] = None,
    ) -> Image.Image:
        """Create side-by-side comparison image."""
        pdf_width, pdf_height = pdf_image.size
        
        if html_image is None:
            # Just show PDF page with labels
            comparison = Image.new("RGB", (pdf_width + 20, pdf_height + 40), color="white")
            comparison.paste(pdf_image, (10, 30))
            
            # Add labels
            draw = ImageDraw.Draw(comparison)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
            except:
                font = ImageFont.load_default()
            
            draw.text((10, 5), f"PDF Page {page_num + 1}", fill="black", font=font)
            
            return comparison
        
        # Side-by-side comparison
        html_width, html_height = html_image.size
        
        # Create new image with both sides
        comparison_width = pdf_width + html_width + 30
        comparison_height = max(pdf_height, html_height) + 40
        
        comparison = Image.new("RGB", (comparison_width, comparison_height), color="white")
        
        # Paste images
        comparison.paste(pdf_image, (10, 30))
        comparison.paste(html_image, (pdf_width + 20, 30))
        
        # Add labels
        draw = ImageDraw.Draw(comparison)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 5), f"PDF", fill="black", font=font)
        draw.text((pdf_width + 20, 5), f"HTML", fill="black", font=font)
        
        # Draw dividing line
        draw.line([(pdf_width + 15, 0), (pdf_width + 15, comparison_height)], fill="gray", width=2)
        
        return comparison

    def save_comparison(self, image: Image.Image, page_num: int, filename: str = None):
        """Save comparison image."""
        if filename is None:
            filename = f"comparison_page_{page_num}.png"
        
        filepath = self.comparison_dir / filename
        image.save(filepath)
        print(f"Comparison saved to {filepath}")

    def compare_all_pages(self, html_images: Dict[int, Image.Image] = None) -> Dict:
        """Compare all pages."""
        html_images = html_images or {}
        comparison_report = []
        
        for page_num in range(len(self.doc)):
            print(f"Comparing page {page_num}...")
            
            pdf_image = self.render_pdf_page(page_num)
            html_image = html_images.get(page_num)
            
            comparison = self.create_comparison_image(page_num, pdf_image, html_image)
            self.save_comparison(comparison, page_num)
            
            comparison_report.append({
                "page": page_num,
                "pdf_size": pdf_image.size,
                "html_size": html_image.size if html_image else None,
                "comparison_saved": True,
            })
        
        return {
            "total_pages": len(self.doc),
            "comparisons": comparison_report,
        }

    def extract_text_from_pdf_page(self, page_num: int) -> str:
        """Extract text from PDF page for comparison."""
        page = self.doc[page_num]
        return page.get_text()

    def analyze_layout_differences(
        self,
        page_num: int,
        extracted_content: Dict,
    ) -> Dict:
        """Analyze differences between extracted layout and rendered PDF."""
        analysis = {
            "page": page_num,
            "observations": [],
            "recommendations": [],
        }
        
        page_data = extracted_content.get("page_data", {})
        width = page_data.get("width", 0)
        height = page_data.get("height", 0)
        text_elements = page_data.get("text_elements", [])
        images = page_data.get("images", [])
        
        # Check page dimensions
        if width < 100 or height < 100:
            analysis["observations"].append("Unusual page dimensions detected")
            analysis["recommendations"].append("Verify page extraction")
        
        # Check text coverage
        if len(text_elements) == 0:
            analysis["observations"].append("No text elements extracted")
            analysis["recommendations"].append("Consider running OCR")
        
        # Check image placement
        for img in images:
            if img.get("width", 0) < 10 or img.get("height", 0) < 10:
                analysis["observations"].append(f"Very small image detected: {img['filename']}")
                analysis["recommendations"].append("Verify image extraction")
        
        return analysis

    def generate_comparison_report(self, analyses: list) -> str:
        """Generate comparison report."""
        lines = [
            "# PDF to HTML Comparison Report",
            "",
            f"## Summary",
            f"Total pages analyzed: {len(analyses)}",
            "",
        ]
        
        for analysis in analyses:
            page_num = analysis["page"]
            lines.append(f"### Page {page_num + 1}")
            
            if analysis["observations"]:
                lines.append("**Observations:**")
                for obs in analysis["observations"]:
                    lines.append(f"- {obs}")
            
            if analysis["recommendations"]:
                lines.append("**Recommendations:**")
                for rec in analysis["recommendations"]:
                    lines.append(f"- {rec}")
            
            lines.append("")
        
        return "\n".join(lines)

    def close(self):
        """Close the PDF document."""
        self.doc.close()


if __name__ == "__main__":
    # Load extracted content
    try:
        with open("output/extracted_content.json", "r") as f:
            content = json.load(f)
    except FileNotFoundError:
        print("extracted_content.json not found. Run extract_content.py first.")
        exit(1)
    
    # Create comparison
    comparator = RenderComparison("input/sample.pdf")
    report = comparator.compare_all_pages()
    
    # Save report
    with open("output/comparison_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("Comparison complete. Check output/comparison/ for images.")
    comparator.close()
