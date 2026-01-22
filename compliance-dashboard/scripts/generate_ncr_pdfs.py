"""
NCR Report PDF Generator
Generates professional Non-Conformance Report PDFs matching the workshop layout
Reads from ncr_detailed.csv and creates 50 realistic PDF reports
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
    Spacer, PageBreak, Frame, PageTemplate
)
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


def create_header_footer(canvas_obj, doc):
    """Add header and footer to each page"""
    canvas_obj.saveState()

    # Header - NCR reference
    canvas_obj.setFont('Helvetica', 10)
    canvas_obj.drawString(0.5*inch, letter[1] - 0.5*inch,
                         f"NCR reference: {doc.ncr_ref}")

    # Footer - Page number
    canvas_obj.setFont('Helvetica', 9)
    page_num = canvas_obj.getPageNumber()
    text = f"Page {page_num} | 4"
    canvas_obj.drawString(letter[0]/2 - 0.5*inch, 0.5*inch, text)

    canvas_obj.restoreState()


def create_section_header(title, width):
    """Create a section header"""
    style = ParagraphStyle(
        'SectionHeader',
        parent=getSampleStyleSheet()['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=6,
        spaceBefore=6
    )
    return Paragraph(f"<b>{title}</b>", style)


def create_field_table(data, col_widths=None):
    """Create a table for form fields"""
    if col_widths is None:
        col_widths = [2*inch, 4.5*inch]

    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8e8e8')),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
        ('FONT', (1, 0), (-1, -1), 'Helvetica', 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return table


def format_date(date_str):
    """Format date string for display"""
    if not date_str or date_str == '':
        return 'N/A'
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%Y-%m-%d')
    except:
        return date_str


def generate_ncr_pdf(ncr_data, output_path):
    """
    Generate a complete NCR PDF report

    Args:
        ncr_data: Dictionary with NCR information
        output_path: Output PDF file path
    """
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Store NCR reference for header
    doc.ncr_ref = ncr_data['ncr_id']

    story = []
    styles = getSampleStyleSheet()

    # =========================================================================
    # PAGE 1: Basic Information
    # =========================================================================

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=24,
        alignment=TA_CENTER
    )
    story.append(Paragraph("<b>Non-Conformance Report</b>", title_style))
    story.append(Spacer(1, 0.3*inch))

    # NCR Identification
    story.append(create_section_header("NCR Identification", letter[0] - inch))
    ncr_id_data = [
        ['Title:', ncr_data.get('title', 'N/A')],
        ['Reference:', ncr_data.get('reference', 'N/A')],
        ['Status:', ncr_data.get('status', 'N/A')],
        ['Revision:', ncr_data.get('revision', 'N/A')],
    ]
    story.append(create_field_table(ncr_id_data))
    story.append(Spacer(1, 0.2*inch))

    # NCR File History
    story.append(create_section_header("NCR File History", letter[0] - inch))
    history_data = [
        ['Creator:', ncr_data.get('creator', 'N/A')],
        ['Department Creator:', ncr_data.get('department_creator', 'N/A')],
        ['Updated By:', ncr_data.get('updated_by', 'N/A')],
        ['Updated:', format_date(ncr_data.get('updated_date', ''))],
    ]
    story.append(create_field_table(history_data))
    story.append(Spacer(1, 0.2*inch))

    # Responsible
    story.append(create_section_header("Responsible", letter[0] - inch))
    responsible_data = [
        ['Person Responsible:', ncr_data.get('person_responsible', 'N/A')],
        ['Department Responsible:', ncr_data.get('department_responsible', 'N/A')],
    ]
    story.append(create_field_table(responsible_data))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: Non-conformance Details
    # =========================================================================

    story.append(create_section_header("Non-conformance Details", letter[0] - inch))

    details_data = [
        ['Location:', ncr_data.get('location', 'N/A')],
        ['Description:', ncr_data.get('description', 'N/A')],
        ['Initial analysis of the cause\nfor Non-Conformance:',
         ncr_data.get('initial_analysis', 'N/A')],
        ['Data Significant:', ncr_data.get('data_significant', 'N/A')],
        ['Date of Occurrence:', format_date(ncr_data.get('date_occurrence', ''))],
    ]
    story.append(create_field_table(details_data))
    story.append(Spacer(1, 0.3*inch))

    # NCR Close-out
    story.append(create_section_header("NCR Close-out", letter[0] - inch))

    closeout_data = [
        ['Cause of NCR:', ncr_data.get('cause_of_ncr', 'N/A')],
        ['Close-out Date:', format_date(ncr_data.get('close_out_date', ''))],
        ['Reason for Closure:', ncr_data.get('reason_closure', 'N/A')],
        ['Reference:', ncr_data.get('reference', 'N/A')],
        ['Latest Disposition:', ncr_data.get('disposition', 'N/A')],
    ]
    story.append(create_field_table(closeout_data))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: Review Board Details
    # =========================================================================

    story.append(create_section_header("Non-Conformance Review Board Details",
                                      letter[0] - inch))
    story.append(Spacer(1, 0.1*inch))

    # NRB Participants
    nrb_header = Paragraph("<b>NRB Participants:</b>", styles['Normal'])
    story.append(nrb_header)
    story.append(Spacer(1, 0.05*inch))

    participant_table_data = [
        ['Email', 'Name', 'Type'],
        [ncr_data.get('nrb_participant_email', 'N/A'),
         ncr_data.get('nrb_participant_name', 'N/A'),
         ncr_data.get('nrb_participant_type', 'N/A')]
    ]
    participant_table = Table(participant_table_data,
                             colWidths=[2.5*inch, 2*inch, 2*inch])
    participant_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8')),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(participant_table)
    story.append(Spacer(1, 0.2*inch))

    # Details of Decision
    story.append(Paragraph("<b>Details of Decision:</b>", styles['Normal']))
    story.append(Spacer(1, 0.05*inch))

    decision_data = [
        ['Date:', format_date(ncr_data.get('decision_date', ''))],
        ['Type:', ncr_data.get('decision_type', 'N/A')],
        ['Description:', ncr_data.get('description', 'N/A')[:100] + '...'],
    ]
    story.append(create_field_table(decision_data))
    story.append(Spacer(1, 0.1*inch))

    classification_data = [
        ['Classification Initiator:', ncr_data.get('classification_initiator', 'N/A')],
        ['Classification Confirmer:', ncr_data.get('classification_confirmer', 'N/A')],
        ['Classification Prima:', ncr_data.get('classification_prima', 'N/A')],
    ]
    story.append(create_field_table(classification_data))
    story.append(Spacer(1, 0.1*inch))

    disposition_data = [
        ['Disposition:', ncr_data.get('disposition', 'N/A')],
        ['NPW:', 'N/A'],
    ]
    story.append(create_field_table(disposition_data))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: Actions and Attachments
    # =========================================================================

    story.append(create_section_header("Actions", letter[0] - inch))

    actions_table_data = [
        ['Title', 'Reference', 'Actions', 'Date Created', 'Due Date', 'Status'],
        ['Corrective Action', ncr_data.get('reference', 'N/A'),
         ncr_data.get('reason_closure', 'N/A')[:50],
         format_date(ncr_data.get('opened_at', '')),
         format_date(ncr_data.get('close_out_date', '')),
         ncr_data.get('status', 'N/A')]
    ]
    actions_table = Table(actions_table_data,
                         colWidths=[1*inch, 1*inch, 1.8*inch, 1*inch, 1*inch, 0.7*inch])
    actions_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8')),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 7),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(actions_table)
    story.append(Spacer(1, 0.3*inch))

    # NCR and sub attachments
    story.append(create_section_header("NCR and sub attachments", letter[0] - inch))

    attachments_table_data = [
        ['File Name', 'Description', 'Attached By', 'Date Attached'],
        [f"{ncr_data.get('ncr_id', 'NCR')}_inspection.pdf",
         'Linked inspection report',
         ncr_data.get('creator', 'N/A'),
         format_date(ncr_data.get('opened_at', ''))],
        [f"{ncr_data.get('ncr_id', 'NCR')}_photos.zip",
         'Supporting photographs',
         ncr_data.get('creator', 'N/A'),
         format_date(ncr_data.get('opened_at', ''))],
    ]
    attachments_table = Table(attachments_table_data,
                             colWidths=[2*inch, 2.5*inch, 1.5*inch, 1.5*inch])
    attachments_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8')),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(attachments_table)
    story.append(Spacer(1, 0.3*inch))

    # NCR Related Items
    story.append(create_section_header("NCR Related Items", letter[0] - inch))

    related_table_data = [
        ['Item Name', 'Reference', 'Title'],
        ['Inspection Report',
         ncr_data.get('linked_inspection_id', 'N/A'),
         f"Inspection - {ncr_data.get('part_number', 'N/A')}"],
    ]
    related_table = Table(related_table_data,
                         colWidths=[2*inch, 2*inch, 2.5*inch])
    related_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8')),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(related_table)

    # Build PDF with custom header/footer
    doc.build(story, onFirstPage=create_header_footer,
              onLaterPages=create_header_footer)

    print(f"  Created: {output_path.name}")


def main():
    """Generate all NCR PDFs from CSV"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate NCR Report PDFs')
    parser.add_argument('-i', '--input',
                       default='data/samples/ncr_detailed.csv',
                       help='Input CSV file')
    parser.add_argument('-o', '--output',
                       default='data/raw/pdf/ncr',
                       help='Output directory for PDFs')

    args = parser.parse_args()

    input_file = Path(args.input)
    output_dir = Path(args.output)

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("NCR Report PDF Generator")
    print("=" * 60)
    print(f"Input: {input_file}")
    print(f"Output: {output_dir}\n")

    # Read CSV
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        ncr_records = list(reader)

    print(f"Found {len(ncr_records)} NCR records\n")

    # Generate PDFs
    for i, ncr in enumerate(ncr_records, 1):
        ncr_id = ncr['ncr_id']
        output_path = output_dir / f"{ncr_id}.pdf"

        try:
            generate_ncr_pdf(ncr, output_path)
        except Exception as e:
            print(f"  ERROR generating {ncr_id}: {e}")

    print("\n" + "=" * 60)
    print(f"Generated {len(ncr_records)} NCR PDFs")
    print("=" * 60)


if __name__ == '__main__':
    main()
