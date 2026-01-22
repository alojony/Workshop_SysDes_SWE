"""
Inspection Certificate PDF Generator
Generates professional inspection report PDFs
Reads from inspection_logs.csv and creates realistic inspection certificates
"""
import csv
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


def generate_inspection_pdf(inspection_data, output_path):
    """
    Generate an inspection certificate PDF

    Args:
        inspection_data: Dictionary with inspection information
        output_path: Output PDF file path
    """
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    story = []
    styles = getSampleStyleSheet()

    # Company Header
    header_style = ParagraphStyle(
        'CompanyHeader',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_RIGHT
    )
    story.append(Paragraph("Quality Inspection Division", header_style))
    story.append(Paragraph(f"{inspection_data.get('site', 'N/A')}", header_style))
    story.append(Spacer(1, 0.3*inch))

    # Title
    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=6,
        alignment=TA_CENTER
    )
    story.append(Paragraph("<b>INSPECTION CERTIFICATE</b>", title_style))

    subtitle_style = ParagraphStyle(
        'CertSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER
    )
    story.append(Paragraph("Quality Control Report", subtitle_style))
    story.append(Spacer(1, 0.4*inch))

    # Inspection ID box
    id_data = [[f"Inspection ID: {inspection_data.get('inspection_id', 'N/A')}"]]
    id_table = Table(id_data, colWidths=[6*inch])
    id_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#1f4788')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f0f8')),
        ('FONT', (0, 0), (-1, -1), 'Helvetica-Bold', 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(id_table)
    story.append(Spacer(1, 0.3*inch))

    # Part Information Section
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=10,
        spaceBefore=10
    )
    story.append(Paragraph("<b>PART INFORMATION</b>", section_style))

    part_data = [
        ['Part Number:', inspection_data.get('part_number', 'N/A')],
        ['Description:', inspection_data.get('part_description', 'N/A')],
        ['Supplier:', inspection_data.get('supplier', 'N/A')],
        ['Production Line:', inspection_data.get('production_line', 'N/A')],
    ]

    part_table = Table(part_data, colWidths=[1.5*inch, 4.5*inch])
    part_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('FONT', (1, 0), (-1, -1), 'Helvetica', 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(part_table)
    story.append(Spacer(1, 0.25*inch))

    # Inspection Details
    story.append(Paragraph("<b>INSPECTION DETAILS</b>", section_style))

    inspection_details_data = [
        ['Inspection Date:', inspection_data.get('inspection_date', 'N/A')],
        ['Inspector:', inspection_data.get('inspector', 'N/A')],
        ['Site Location:', inspection_data.get('site', 'N/A')],
    ]

    details_table = Table(inspection_details_data, colWidths=[1.5*inch, 4.5*inch])
    details_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('FONT', (1, 0), (-1, -1), 'Helvetica', 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 0.25*inch))

    # Measurement Results
    story.append(Paragraph("<b>MEASUREMENT RESULTS</b>", section_style))

    # Result color based on pass/fail
    result = inspection_data.get('result', 'FAIL')
    if result == 'PASS':
        result_color = colors.green
        result_bg = colors.HexColor('#d4edda')
    elif result == 'FAIL':
        result_color = colors.red
        result_bg = colors.HexColor('#f8d7da')
    else:  # CONDITIONAL
        result_color = colors.orange
        result_bg = colors.HexColor('#fff3cd')

    measurement_data = [
        ['Parameter', 'Measured Value', 'Unit', 'Spec Min', 'Spec Max', 'Result'],
        ['Dimension',
         inspection_data.get('measurement_value', 'N/A'),
         inspection_data.get('measurement_unit', ''),
         inspection_data.get('spec_min', 'N/A'),
         inspection_data.get('spec_max', 'N/A'),
         result]
    ]

    measurement_table = Table(measurement_data,
                             colWidths=[1.5*inch, 1*inch, 0.6*inch, 0.9*inch, 0.9*inch, 1.1*inch])
    measurement_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8')),
        ('BACKGROUND', (-1, 1), (-1, -1), result_bg),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
        ('FONT', (-1, 1), (-1, -1), 'Helvetica-Bold', 10),
        ('TEXTCOLOR', (-1, 1), (-1, -1), result_color),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(measurement_table)
    story.append(Spacer(1, 0.3*inch))

    # Notes
    if inspection_data.get('notes'):
        story.append(Paragraph("<b>NOTES</b>", section_style))
        notes_data = [[inspection_data.get('notes', '')]]
        notes_table = Table(notes_data, colWidths=[6*inch])
        notes_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(notes_table)
        story.append(Spacer(1, 0.3*inch))

    # Final Result Box
    result_text = f"<b>INSPECTION RESULT: {result}</b>"
    result_para = Paragraph(result_text, ParagraphStyle(
        'ResultStyle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=result_color,
        alignment=TA_CENTER
    ))

    result_box_data = [[result_para]]
    result_box = Table(result_box_data, colWidths=[6*inch])
    result_box.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 3, result_color),
        ('BACKGROUND', (0, 0), (-1, -1), result_bg),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(result_box)
    story.append(Spacer(1, 0.4*inch))

    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("This certificate is issued electronically and is valid without signature.", footer_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))

    # Build PDF
    doc.build(story)
    print(f"  Created: {output_path.name}")


def main():
    """Generate all Inspection Certificate PDFs from CSV"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate Inspection Certificate PDFs')
    parser.add_argument('-i', '--input',
                       default='data/samples/inspection_logs.csv',
                       help='Input CSV file')
    parser.add_argument('-o', '--output',
                       default='data/raw/pdf/inspections',
                       help='Output directory for PDFs')

    args = parser.parse_args()

    input_file = Path(args.input)
    output_dir = Path(args.output)

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Inspection Certificate PDF Generator")
    print("=" * 60)
    print(f"Input: {input_file}")
    print(f"Output: {output_dir}\n")

    # Read CSV
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        inspection_records = list(reader)

    print(f"Found {len(inspection_records)} inspection records\n")

    # Generate PDFs
    for i, inspection in enumerate(inspection_records, 1):
        inspection_id = inspection['inspection_id']
        output_path = output_dir / f"{inspection_id}.pdf"

        try:
            generate_inspection_pdf(inspection, output_path)
        except Exception as e:
            print(f"  ERROR generating {inspection_id}: {e}")

    print("\n" + "=" * 60)
    print(f"Generated {len(inspection_records)} Inspection Certificate PDFs")
    print("=" * 60)


if __name__ == '__main__':
    main()
