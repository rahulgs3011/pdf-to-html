# PDF to HTML Converter

Convert PDF documents into a single scrollable HTML document with extracted text, images, and tables. All pages are stacked vertically, with content positioned to match the original PDF layout.

## Features

- **Single HTML Document**: All PDF pages in one scrollable file
- **Coordinate-Based Layout**: Text and images positioned to match PDF geometry
- **Image Extraction**: Embedded images saved to `images/` folder
- **Table Detection**: Automatic table detection and HTML conversion
- **OCR Support**: Extract text from scanned pages using Tesseract
- **Visual Comparison**: Compare PDF vs. HTML renderings for quality assurance
- **Selectable Text**: All extracted text remains selectable in the browser
- **Print-Friendly**: CSS includes print styles for accurate document output

## Architecture

```
pdf-to-html/
├── venv/                        # Python virtual environment
├── input/                       # Place PDF files here
│   └── sample.pdf
├── output-sample/               # Output for each PDF (auto-created)
│   ├── index.html
│   ├── styles.css
│   ├── images/
│   ├── extracted_content.json
│   ├── detected_tables.json
│   ├── pdf_inspection.json
│   ├── ocr_results.json
│   ├── comparison_report.json
│   ├── pipeline_results.json
│   └── comparison/
├── output-report/               # Another PDF's output
│   ├── index.html
│   └── ...
├── src/
│   ├── main.py
│   ├── inspect_pdf.py
│   ├── extract_content.py
│   ├── detect_tables.py
│   ├── run_ocr.py
│   ├── build_html.py
│   └── compare_render.py
├── .gitignore                   # Git ignore file
├── requirements.txt
└── README.md
```

**Key Changes:**
- Each PDF creates its own `output-<pdf-filename>` folder
- All intermediate files and images stay organized per PDF
- `.gitignore` excludes output folders and venv
- `venv/` folder included for virtual environment

## Installation

### Prerequisites

- Python 3.8+
- Tesseract (for OCR support)

### Setup Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

### Install Tesseract

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Quick Start

```bash
# Run complete pipeline on a PDF
# Output goes to: output-<pdf-filename>/
python src/main.py input/sample.pdf
# Creates: output-sample/index.html
```

### Output Folder Structure

Each PDF creates its own output folder automatically:

```bash
python src/main.py input/research_paper.pdf
# Creates: output-research_paper/
#   ├── index.html
#   ├── styles.css
#   ├── images/
#   └── *.json files

python src/main.py input/scanned_doc.pdf
# Creates: output-scanned_doc/
#   ├── index.html
#   ├── styles.css
#   └── images/
```

### Advanced Options

```bash
# Skip OCR (faster processing)
python src/main.py input/sample.pdf --skip-ocr

# Skip comparison images
python src/main.py input/sample.pdf --skip-comparison

# Use different OCR language
python src/main.py input/sample.pdf --ocr-lang spa

# Custom output directory (optional, overrides auto-naming)
python src/main.py input/sample.pdf --output-dir custom_output
```

### Run Individual Steps

#### 1. Inspect PDF

```python
from src.inspect_pdf import PDFInspector

inspector = PDFInspector("input/sample.pdf")
summaries = inspector.inspect_all_pages()
inspector.close()

# Output: Shows page content types, text density, image count, etc.
```

#### 2. Extract Content

```python
from src.extract_content import ContentExtractor

extractor = ContentExtractor("input/sample.pdf")
content = extractor.extract_all_pages()
extractor.close()

# Output: Text elements with coordinates, extracted images
```

#### 3. Detect Tables

```python
from src.detect_tables import TableDetector

detector = TableDetector("input/sample.pdf")
tables = detector.extract_all_tables()
detector.close()

# Output: Table structures and content
```

#### 4. Run OCR

```python
from src.run_ocr import OCRProcessor

processor = OCRProcessor("input/sample.pdf")
results = processor.ocr_all_pages()
processor.close()

# Output: Text and coordinates from scanned pages
```

#### 5. Build HTML

```python
from src.build_html import HTMLBuilder
import json

# Load extracted content
with open("output/extracted_content.json") as f:
    content = json.load(f)

# Build and save
builder = HTMLBuilder("output")
html = builder.build_html_document(content, title="My PDF")
builder.save_html(html)
builder.save_css(builder.generate_css())
```

#### 6. Compare Renderings

```python
from src.compare_render import RenderComparison

comparator = RenderComparison("input/sample.pdf")
report = comparator.compare_all_pages()
comparator.close()

# Output: Side-by-side comparison images in output/comparison/
```

## Processing Pipeline

### Overview

```
1. Inspect PDF
   └─ Determine content types per page
   └─ Identify text, images, tables, scanned content

2. Extract Content
   └─ Extract text with coordinates and font info
   └─ Save images to output/images/
   └─ Preserve page dimensions

3. Detect Tables
   └─ Identify table structures
   └─ Extract cell content
   └─ Assess layout confidence

4. Run OCR
   └─ Process scanned pages
   └─ Extract text with coordinates
   └─ Recognize low-confidence regions

5. Build HTML
   └─ Create single scrollable document
   └─ Position elements with CSS
   └─ Apply styling from PDF

6. Compare Renderings
   └─ Render PDF pages
   └─ Generate comparison images
   └─ Identify layout mismatches
```

## Output Files

### HTML & CSS
- **index.html**: Main output document with all pages
- **styles.css**: Stylesheet with page layout and print styles

### Images
- **images/**: Extracted images from PDF
  - Named: `page_X_img_Y.png`

### Metadata JSON
- **extracted_content.json**: Text elements and images with coordinates
- **detected_tables.json**: Table structures and content
- **pdf_inspection.json**: Page analysis results
- **ocr_results.json**: OCR text recognition results
- **pipeline_results.json**: Full pipeline execution report
- **comparison_report.json**: Visual comparison results

### Comparison Images
- **comparison/comparison_page_X.png**: PDF vs. HTML side-by-side

## Customization

### Modify CSS

Edit `output/styles.css` to adjust:
- Font families and sizes
- Page margins and spacing
- Table styling
- Print appearance
- Responsive breakpoints

### Adjust Content Positioning

The HTML uses absolute positioning for text elements. To refine alignment:

1. Open `output/extracted_content.json`
2. Adjust `x`, `y`, `width`, `height` values for text elements
3. Regenerate HTML or manually edit `index.html`

### Filter Content

Modify `build_html.py` to:
- Skip certain text elements
- Exclude small images
- Simplify table rendering
- Remove OCR low-confidence text

## Troubleshooting

### Images Not Appearing

- Check `output/images/` folder exists
- Verify image paths in HTML are relative: `images/page_0_img_0.png`
- Check image file permissions

### Text Misaligned

- Inspect coordinates in `extracted_content.json`
- Compare PDF page dimensions with HTML page dimensions
- Adjust font sizes and positions in CSS

### OCR Not Working

```bash
# Check Tesseract installation
tesseract --version

# If not found, install it
brew install tesseract  # macOS
sudo apt-get install tesseract-ocr  # Linux
```

### Tables Look Incorrect

- Some PDFs use visual tables (borders/positioning) instead of semantic tables
- Check `detected_tables.json` for confidence scores
- High confidence (>0.8) = semantic table
- Low confidence = use positioned divs instead

### Slow Processing

- Use `--skip-ocr` for faster processing without OCR
- Use `--skip-comparison` to skip image rendering
- Process smaller PDFs first to test

## Performance Tips

1. **Batch Processing**: Process multiple PDFs with a loop
2. **Skip Unnecessary Steps**: Use flags to skip OCR/comparison if not needed
3. **OCR Languages**: Specify language for faster recognition
4. **Image Quality**: Output images are high-quality by default; reduce DPI if space is an issue

## Limitations & Tradeoffs

### What Works Well
- Text-heavy PDFs with clear structure
- PDFs with embedded images
- Documents with table content
- Scanned documents (with OCR)

### Challenges
- Complex multi-column layouts may need CSS refinement
- Overlapping elements might not render correctly
- Handwritten text OCR accuracy is lower
- Very large PDFs (1000+ pages) may be memory-intensive

### Design Choice: Visual Fidelity vs. Semantic HTML

This tool prioritizes **visual fidelity** (matching PDF appearance) over semantic HTML structure. This means:

✅ **Advantages:**
- Documents look exactly like the PDF
- Text remains selectable
- Images are embedded and positioned correctly
- Easy to verify output matches original

❌ **Tradeoffs:**
- HTML is heavily styled with positioned elements
- Limited semantic structure for accessibility
- Not ideal for screen readers
- Difficult to modify content later

To improve accessibility, you could post-process the HTML to add ARIA labels and semantic restructuring.

## Examples

### Convert a Research Paper

```bash
python src/main.py input/research_paper.pdf --output-dir output/research
```

### Convert a Scanned Document

```bash
python src/main.py input/scanned_doc.pdf --ocr-lang fra
# For French OCR
```

### Quick Test (Skip OCR & Comparison)

```bash
python src/main.py input/test.pdf --skip-ocr --skip-comparison
```

## Contributing

To improve the conversion process:

1. Test with different PDF types
2. Report issues with specific PDFs
3. Improve CSS for better rendering
4. Enhance table detection
5. Optimize OCR accuracy

## License

MIT License - Feel free to use and modify.

## Requirements Summary

| Tool | Purpose | Install |
|------|---------|---------|
| PyMuPDF | PDF inspection and extraction | `pip install PyMuPDF` |
| pdfplumber | Table detection | `pip install pdfplumber` |
| pytesseract | OCR text recognition | `pip install pytesseract` |
| Tesseract | OCR engine (system) | `brew install tesseract` |
| Pillow | Image processing | `pip install Pillow` |
| pdf2image | PDF to image rendering | `pip install pdf2image` |

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the JSON output files for insights
3. Compare PDF vs. HTML in `output/comparison/`
4. Test with `--skip-ocr` to isolate issues
