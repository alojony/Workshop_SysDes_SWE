"""
CSV to PDF Converter
Helper script to create PDF versions of CSV files for testing

This creates simple PDF representations of CSV data
Useful for Session 3+ when testing document ingestion
"""
import csv
import sys
from pathlib import Path
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not installed. Install with: pip install reportlab")


def csv_to_pdf(csv_path: Path, pdf_path: Path, title: str = None):
    """
    Convert CSV file to PDF

    Args:
        csv_path: Path to CSV file
        pdf_path: Path for output PDF
        title: Document title (defaults to filename)
    """
    if not REPORTLAB_AVAILABLE:
        print("Error: reportlab library required. Install with: pip install reportlab")
        sys.exit(1)

    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)

    # Read CSV data
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        data = list(reader)

    if not data:
        print(f"Error: CSV file is empty: {csv_path}")
        sys.exit(1)

    # Create PDF
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Container for elements
    elements = []
    styles = getSampleStyleSheet()

    # Add title
    if title is None:
        title = csv_path.stem.replace('_', ' ').title()

    title_para = Paragraph(f"<b>{title}</b>", styles['Title'])
    elements.append(title_para)
    elements.append(Spacer(1, 0.2*inch))

    # Add metadata
    meta_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>Source: {csv_path.name}"
    meta_para = Paragraph(meta_text, styles['Normal'])
    elements.append(meta_para)
    elements.append(Spacer(1, 0.3*inch))

    # Calculate column widths
    # Use available width divided by number of columns
    available_width = letter[0] - (1.0 * inch)  # Page width minus margins
    num_cols = len(data[0])
    col_width = available_width / num_cols

    # Adjust column widths if too narrow
    if col_width < 0.5*inch:
        col_width = 0.5*inch

    col_widths = [col_width] * num_cols

    # Create table
    table = Table(data, colWidths=col_widths, repeatRows=1)

    # Style the table
    table_style = TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

        # Data rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),

        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ])

    table.setStyle(table_style)
    elements.append(table)

    # Build PDF
    doc.build(elements)
    print(f"Created PDF: {pdf_path}")


def batch_convert(input_folder: Path, output_folder: Path):
    """
    Convert all CSV files in a folder to PDFs

    Args:
        input_folder: Folder containing CSV files
        output_folder: Folder for output PDFs
    """
    if not input_folder.exists():
        print(f"Error: Input folder not found: {input_folder}")
        sys.exit(1)

    output_folder.mkdir(parents=True, exist_ok=True)

    csv_files = list(input_folder.glob('*.csv'))

    if not csv_files:
        print(f"No CSV files found in {input_folder}")
        return

    print(f"Found {len(csv_files)} CSV files")
    print(f"Output folder: {output_folder}\n")

    for csv_file in csv_files:
        pdf_file = output_folder / f"{csv_file.stem}.pdf"
        try:
            csv_to_pdf(csv_file, pdf_file)
        except Exception as e:
            print(f"Error converting {csv_file.name}: {e}")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert CSV files to PDF format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single file
  python csv_to_pdf.py -i data/samples/inspections.csv -o data/samples/inspections.pdf

  # Convert all CSVs in a folder
  python csv_to_pdf.py -i data/samples/ -o data/samples/pdf/
        """
    )

    parser.add_argument('-i', '--input', required=True,
                        help='Input CSV file or folder')
    parser.add_argument('-o', '--output', required=True,
                        help='Output PDF file or folder')
    parser.add_argument('-t', '--title',
                        help='Document title (for single file conversion)')

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.is_file():
        # Single file conversion
        csv_to_pdf(input_path, output_path, args.title)
    elif input_path.is_dir():
        # Batch conversion
        if output_path.suffix:
            print("Error: When converting a folder, output must be a folder path")
            sys.exit(1)
        batch_convert(input_path, output_path)
    else:
        print(f"Error: Input not found: {input_path}")
        sys.exit(1)


if __name__ == '__main__':
    main()
