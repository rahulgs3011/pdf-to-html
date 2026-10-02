"""
Main orchestration script for PDF to HTML conversion.
Runs the full processing pipeline: inspect → extract → detect tables → OCR → build HTML → compare.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional

# Import processing modules
from inspect_pdf import PDFInspector
from extract_content import ContentExtractor
from detect_tables import TableDetector
from run_ocr import OCRProcessor
from build_html import HTMLBuilder
from compare_render import RenderComparison


class PDFToHTMLPipeline:
    def __init__(self, pdf_path: str, output_dir: str = None):
        self.pdf_path = Path(pdf_path)
        
        # If no output dir specified, create one based on PDF filename
        if output_dir is None:
            pdf_name = self.pdf_path.stem  # Filename without extension
            output_dir = f"output-{pdf_name}"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_full_pipeline(
        self,
        skip_ocr: bool = False,
        skip_comparison: bool = False,
        ocr_lang: str = "eng",
    ) -> dict:
        """Run the complete PDF to HTML conversion pipeline."""
        
        results = {
            "pdf_path": str(self.pdf_path),
            "output_dir": str(self.output_dir),
            "steps": {},
        }
        
        # Step 1: Inspect PDF
        print("\n" + "="*60)
        print("STEP 1: Inspecting PDF...")
        print("="*60)
        try:
            inspector = PDFInspector(str(self.pdf_path))
            page_summaries = inspector.inspect_all_pages()
            inspector.close()
            
            with open(self.output_dir / "pdf_inspection.json", "w") as f:
                json.dump(page_summaries, f, indent=2)
            
            results["steps"]["inspect"] = {
                "status": "success",
                "pages": len(page_summaries),
                "file": "pdf_inspection.json",
            }
            
            # Print summary
            for summary in page_summaries:
                print(f"  Page {summary['page']}: "
                      f"text={summary['has_text']}, "
                      f"images={summary['image_count']}, "
                      f"tables={summary['tables']}")
        
        except Exception as e:
            print(f"ERROR in inspection: {e}")
            results["steps"]["inspect"] = {"status": "error", "error": str(e)}
            return results
        
        # Step 2: Extract Content
        print("\n" + "="*60)
        print("STEP 2: Extracting content...")
        print("="*60)
        try:
            extractor = ContentExtractor(str(self.pdf_path), str(self.output_dir))
            content = extractor.extract_all_pages()
            extractor.close()
            
            with open(self.output_dir / "extracted_content.json", "w") as f:
                json.dump(content, f, indent=2)
            
            total_text_elements = sum(len(p.get("text_elements", [])) for p in content)
            total_images = sum(len(p.get("images", [])) for p in content)
            
            results["steps"]["extract"] = {
                "status": "success",
                "text_elements": total_text_elements,
                "images_extracted": total_images,
                "file": "extracted_content.json",
            }
            
            print(f"  Extracted {total_text_elements} text elements")
            print(f"  Extracted {total_images} images")
        
        except Exception as e:
            print(f"ERROR in extraction: {e}")
            results["steps"]["extract"] = {"status": "error", "error": str(e)}
            return results
        
        # Step 3: Detect Tables
        print("\n" + "="*60)
        print("STEP 3: Detecting tables...")
        print("="*60)
        try:
            detector = TableDetector(str(self.pdf_path))
            tables = detector.extract_all_tables()
            detector.close()
            
            with open(self.output_dir / "detected_tables.json", "w") as f:
                json.dump(tables, f, indent=2)
            
            total_tables = sum(len(p.get("tables", [])) for p in tables)
            
            results["steps"]["detect_tables"] = {
                "status": "success",
                "tables_detected": total_tables,
                "file": "detected_tables.json",
            }
            
            print(f"  Detected {total_tables} tables")
        
        except Exception as e:
            print(f"WARNING in table detection: {e}")
            results["steps"]["detect_tables"] = {"status": "warning", "error": str(e)}
            tables = None
        
        # Step 4: Run OCR (if not skipped)
        if not skip_ocr:
            print("\n" + "="*60)
            print("STEP 4: Running OCR...")
            print("="*60)
            try:
                processor = OCRProcessor(str(self.pdf_path), str(self.output_dir))
                
                if not processor.check_tesseract_installed():
                    print("  WARNING: Tesseract not installed. Skipping OCR.")
                    print("  Install from: https://github.com/UB-Mannheim/tesseract/wiki")
                    results["steps"]["ocr"] = {
                        "status": "skipped",
                        "reason": "Tesseract not installed",
                    }
                else:
                    ocr_results = processor.ocr_all_pages(lang=ocr_lang)
                    processor.close()
                    
                    with open(self.output_dir / "ocr_results.json", "w") as f:
                        json.dump(ocr_results, f, indent=2)
                    
                    successful_ocr = sum(1 for r in ocr_results if r.get("success"))
                    
                    results["steps"]["ocr"] = {
                        "status": "success",
                        "pages_processed": len(ocr_results),
                        "pages_successful": successful_ocr,
                        "file": "ocr_results.json",
                    }
                    
                    print(f"  Processed {len(ocr_results)} pages with OCR")
                    print(f"  Successful: {successful_ocr}/{len(ocr_results)}")
            
            except Exception as e:
                print(f"WARNING in OCR: {e}")
                results["steps"]["ocr"] = {"status": "error", "error": str(e)}
        else:
            print("\n" + "="*60)
            print("STEP 4: Skipping OCR (as requested)")
            print("="*60)
            results["steps"]["ocr"] = {"status": "skipped"}
        
        # Step 5: Build HTML
        print("\n" + "="*60)
        print("STEP 5: Building HTML document...")
        print("="*60)
        try:
            builder = HTMLBuilder(str(self.output_dir))
            html = builder.build_html_document(content, tables, title="PDF to HTML Conversion")
            css = builder.generate_css()
            
            builder.save_html(html, "index.html")
            builder.save_css(css, "styles.css")
            
            results["steps"]["build_html"] = {
                "status": "success",
                "html_file": "index.html",
                "css_file": "styles.css",
            }
            
            print(f"  HTML: output/index.html")
            print(f"  CSS: output/styles.css")
        
        except Exception as e:
            print(f"ERROR in HTML building: {e}")
            results["steps"]["build_html"] = {"status": "error", "error": str(e)}
            return results
        
        # Step 6: Compare Renderings (if not skipped)
        if not skip_comparison:
            print("\n" + "="*60)
            print("STEP 6: Creating comparison images...")
            print("="*60)
            try:
                comparator = RenderComparison(str(self.pdf_path), str(self.output_dir))
                comparison_report = comparator.compare_all_pages()
                comparator.close()
                
                with open(self.output_dir / "comparison_report.json", "w") as f:
                    json.dump(comparison_report, f, indent=2)
                
                results["steps"]["compare"] = {
                    "status": "success",
                    "pages_compared": comparison_report["total_pages"],
                    "comparison_dir": "comparison",
                }
                
                print(f"  Compared {comparison_report['total_pages']} pages")
                print(f"  Images saved to: output/comparison/")
            
            except Exception as e:
                print(f"WARNING in comparison: {e}")
                results["steps"]["compare"] = {"status": "warning", "error": str(e)}
        else:
            print("\n" + "="*60)
            print("STEP 6: Skipping comparison (as requested)")
            print("="*60)
            results["steps"]["compare"] = {"status": "skipped"}
        
        # Final summary
        print("\n" + "="*60)
        print("PIPELINE COMPLETE")
        print("="*60)
        
        results["status"] = "success"
        
        # Save pipeline results
        with open(self.output_dir / "pipeline_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\nOpen output/index.html in a browser to view the result.")
        print(f"Pipeline results saved to: output/pipeline_results.json")
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF to scrollable HTML document"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the PDF file to convert",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: output-<pdf-filename>)",
    )
    parser.add_argument(
        "--skip-ocr",
        action="store_true",
        help="Skip OCR processing",
    )
    parser.add_argument(
        "--skip-comparison",
        action="store_true",
        help="Skip rendering comparison",
    )
    parser.add_argument(
        "--ocr-lang",
        default="eng",
        help="OCR language (default: eng)",
    )
    
    args = parser.parse_args()
    
    # Validate PDF path
    if not Path(args.pdf_path).exists():
        print(f"ERROR: PDF file not found: {args.pdf_path}")
        sys.exit(1)
    
    # Run pipeline
    pipeline = PDFToHTMLPipeline(args.pdf_path, args.output_dir)
    results = pipeline.run_full_pipeline(
        skip_ocr=args.skip_ocr,
        skip_comparison=args.skip_comparison,
        ocr_lang=args.ocr_lang,
    )
    
    # Exit with appropriate code
    if results["status"] == "success":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
