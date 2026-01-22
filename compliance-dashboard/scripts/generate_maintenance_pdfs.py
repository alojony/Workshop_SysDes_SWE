"""
Maintenance Work Order PDF Generator
Generates professional maintenance work order PDFs
Reads from maintenance_logs.csv and creates realistic work orders
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
    Spacer
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_maintenance_pdf(maintenance_data, output_path):
    """
    Generate a maintenance work order PDF

    Args:
        maintenance_data: Dictionary with maintenance information
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

    # Header with company logo placeholder
    header_data = [
        ['MAINTENANCE DEPARTMENT', f"Site: {maintenance_data.get('site', 'N/A')}"],
    ]
    header_table = Table(header_data, colWidths=[4*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, 0), 'Helvetica-Bold', 14),
        ('FONT', (1, 0), (1, 0), 'Helvetica', 10),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#1f4788')),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.1*inch))

    # Horizontal line
    line_data = [['  ']]
    line_table = Table(line_data, colWidths=[6.5*inch])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#1f4788')),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 0.2*inch))

    # Title
    title_style = ParagraphStyle(
        'WOTitle',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    story.append(Paragraph("<b>MAINTENANCE WORK ORDER</b>", title_style))
    story.append(Spacer(1, 0.2*inch))

    # Work Order ID and Type
    wo_header_data = [
        [f"Work Order: {maintenance_data.get('event_id', 'N/A')}",
         f"Type: {maintenance_data.get('event_type', 'N/A')}"],
    ]
    wo_header_table = Table(wo_header_data, colWidths=[3.25*inch, 3.25*inch])
    wo_header_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#1f4788')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f0f8')),
        ('FONT', (0, 0), (-1, -1), 'Helvetica-Bold', 12),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(wo_header_table)
    story.append(Spacer(1, 0.3*inch))

    # Equipment Information Section
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.white,
        spaceAfter=0,
        spaceBefore=0,
        leftIndent=10
    )

    # Equipment Info Header
    equip_header_data = [[Paragraph("<b>EQUIPMENT INFORMATION</b>", section_style)]]
    equip_header_table = Table(equip_header_data, colWidths=[6.5*inch])
    equip_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1f4788')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(equip_header_table)

    # Equipment Details
    equip_data = [
        ['Machine ID:', maintenance_data.get('machine_id', 'N/A')],
        ['Description:', maintenance_data.get('machine_description', 'N/A')],
        ['Location:', maintenance_data.get('site', 'N/A')],
    ]

    equip_table = Table(equip_data, colWidths=[1.5*inch, 5*inch])
    equip_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('FONT', (1, 0), (-1, -1), 'Helvetica', 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(equip_table)
    story.append(Spacer(1, 0.25*inch))

    # Work Order Details
    wo_details_header_data = [[Paragraph("<b>WORK ORDER DETAILS</b>", section_style)]]
    wo_details_header_table = Table(wo_details_header_data, colWidths=[6.5*inch])
    wo_details_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1f4788')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(wo_details_header_table)

    wo_details_data = [
        ['Event Date:', maintenance_data.get('event_date', 'N/A')],
        ['Technician:', maintenance_data.get('technician', 'N/A')],
        ['Downtime (hours):', maintenance_data.get('downtime_hours', 'N/A')],
    ]

    wo_details_table = Table(wo_details_data, colWidths=[1.5*inch, 5*inch])
    wo_details_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('FONT', (1, 0), (-1, -1), 'Helvetica', 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(wo_details_table)
    story.append(Spacer(1, 0.25*inch))

    # Work Description
    desc_header_data = [[Paragraph("<b>WORK DESCRIPTION</b>", section_style)]]
    desc_header_table = Table(desc_header_data, colWidths=[6.5*inch])
    desc_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1f4788')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(desc_header_table)

    desc_data = [[maintenance_data.get('description', 'N/A')]]
    desc_table = Table(desc_data, colWidths=[6.5*inch])
    desc_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(desc_table)
    story.append(Spacer(1, 0.25*inch))

    # Parts Replaced
    parts_header_data = [[Paragraph("<b>PARTS REPLACED</b>", section_style)]]
    parts_header_table = Table(parts_header_data, colWidths=[6.5*inch])
    parts_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1f4788')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(parts_header_table)

    parts_replaced = maintenance_data.get('parts_replaced', 'None')
    parts_data = [[parts_replaced if parts_replaced else 'None']]
    parts_table = Table(parts_data, colWidths=[6.5*inch])
    parts_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(parts_table)
    story.append(Spacer(1, 0.25*inch))

    # Notes
    if maintenance_data.get('notes'):
        notes_header_data = [[Paragraph("<b>NOTES</b>", section_style)]]
        notes_header_table = Table(notes_header_data, colWidths=[6.5*inch])
        notes_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1f4788')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(notes_header_table)

        notes_data = [[maintenance_data.get('notes', '')]]
        notes_table = Table(notes_data, colWidths=[6.5*inch])
        notes_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fffacd')),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(notes_table)
        story.append(Spacer(1, 0.3*inch))

    # Completion Status
    event_type = maintenance_data.get('event_type', 'Preventive')
    if event_type == 'Breakdown':
        status_color = colors.red
        status_bg = colors.HexColor('#f8d7da')
    elif event_type == 'Corrective':
        status_color = colors.orange
        status_bg = colors.HexColor('#fff3cd')
    else:  # Preventive
        status_color = colors.green
        status_bg = colors.HexColor('#d4edda')

    status_text = f"<b>Work Order Type: {event_type.upper()}</b>"
    status_para = Paragraph(status_text, ParagraphStyle(
        'StatusStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=status_color,
        alignment=TA_CENTER
    ))

    status_data = [[status_para]]
    status_table = Table(status_data, colWidths=[6.5*inch])
    status_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 2, status_color),
        ('BACKGROUND', (0, 0), (-1, -1), status_bg),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 0.4*inch))

    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Maintenance Department - Quality Management System", footer_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))

    # Build PDF
    doc.build(story)
    print(f"  Created: {output_path.name}")


def main():
    """Generate all Maintenance Work Order PDFs from CSV"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate Maintenance Work Order PDFs')
    parser.add_argument('-i', '--input',
                       default='data/samples/maintenance_logs.csv',
                       help='Input CSV file')
    parser.add_argument('-o', '--output',
                       default='data/raw/pdf/maintenance',
                       help='Output directory for PDFs')

    args = parser.parse_args()

    input_file = Path(args.input)
    output_dir = Path(args.output)

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Maintenance Work Order PDF Generator")
    print("=" * 60)
    print(f"Input: {input_file}")
    print(f"Output: {output_dir}\n")

    # Read CSV
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        maintenance_records = list(reader)

    print(f"Found {len(maintenance_records)} maintenance records\n")

    # Generate PDFs
    for i, maint in enumerate(maintenance_records, 1):
        event_id = maint['event_id']
        output_path = output_dir / f"{event_id}.pdf"

        try:
            generate_maintenance_pdf(maint, output_path)
        except Exception as e:
            print(f"  ERROR generating {event_id}: {e}")

    print("\n" + "=" * 60)
    print(f"Generated {len(maintenance_records)} Maintenance Work Order PDFs")
    print("=" * 60)


if __name__ == '__main__':
    main()
