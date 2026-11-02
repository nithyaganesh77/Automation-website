import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evaluation", "datasets")
os.makedirs(OUT_DIR, exist_ok=True)


def create_invoice_pdf(
    filename: str,
    invoice_number: str,
    invoice_date: str,
    due_date: str,
    supplier_name: str,
    supplier_gstin: str,
    supplier_address: str,
    customer_name: str,
    customer_gstin: str,
    customer_address: str,
    line_items: list,
    subtotal: float,
    cgst: float,
    sgst: float,
    igst: float,
    grand_total: float,
    title: str = "TAX INVOICE"
):
    pdf_path = os.path.join(OUT_DIR, filename)
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor('#102A43'), alignment=1)
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 15))

    # Header Details
    header_data = [
        [
            Paragraph(f"<b>Supplier:</b><br/>{supplier_name}<br/>{supplier_address}<br/><b>GSTIN:</b> {supplier_gstin}", styles['Normal']),
            Paragraph(f"<b>Invoice #:</b> {invoice_number}<br/><b>Date:</b> {invoice_date}<br/><b>Due Date:</b> {due_date}<br/><b>Currency:</b> INR", styles['Normal'])
        ],
        [
            Paragraph(f"<b>Billed To (Customer):</b><br/>{customer_name}<br/>{customer_address}<br/><b>GSTIN:</b> {customer_gstin}", styles['Normal']),
            Paragraph("<b>Place of Supply:</b> Karnataka (29)<br/><b>Payment Terms:</b> Net 30 Days", styles['Normal'])
        ]
    ]
    header_table = Table(header_data, colWidths=[270, 270])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # Line Items Table
    table_data = [["Item", "Description", "HSN/SAC", "Qty", "Rate", "Tax Rate", "Total"]]
    for item in line_items:
        table_data.append([
            str(item["num"]),
            item["desc"],
            item.get("hsn", "9983"),
            f"{item['qty']:.1f}",
            f"INR {item['rate']:,.2f}",
            f"{item['tax_rate']:.0f}%",
            f"INR {item['total']:,.2f}"
        ])

    table_data.append(["", "", "", "", "", "Subtotal:", f"INR {subtotal:,.2f}"])
    if cgst > 0:
        table_data.append(["", "", "", "", "", "CGST (9%):", f"INR {cgst:,.2f}"])
    if sgst > 0:
        table_data.append(["", "", "", "", "", "SGST (9%):", f"INR {sgst:,.2f}"])
    if igst > 0:
        table_data.append(["", "", "", "", "", "IGST (18%):", f"INR {igst:,.2f}"])
    table_data.append(["", "", "", "", "", "Grand Total:", f"INR {grand_total:,.2f}"])

    item_table = Table(table_data, colWidths=[30, 200, 60, 40, 70, 60, 80])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#102A43')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, len(line_items)), 0.5, colors.HexColor('#CBD5E1')),
        ('FONTNAME', (4, len(line_items) + 1), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (4, len(line_items) + 1), (-1, -1), 1, colors.HexColor('#102A43')),
    ]))
    story.append(item_table)
    story.append(Spacer(1, 20))

    footer_text = "<font size=8 color='#627D98'>This is a computer generated test invoice. Synthetic test data created for DocuMind AI validation.</font>"
    story.append(Paragraph(footer_text, styles['Normal']))

    doc.build(story)
    print(f"Generated synthetic invoice: {pdf_path}")
    return pdf_path


def generate_all_samples():
    # 1. Standard Compliant Invoice 1
    create_invoice_pdf(
        filename="invoice_standard_01.pdf",
        invoice_number="INV-2026-0891",
        invoice_date="2026-10-15",
        due_date="2026-11-15",
        supplier_name="Apex Cloud Technologies Pvt Ltd",
        supplier_gstin="29ABCDE1234F1Z5",
        supplier_address="42 Tech Park, Outer Ring Road, Bengaluru 560103",
        customer_name="DocuMind Enterprise Corp",
        customer_gstin="29XYZAB5678C1Z2",
        customer_address="108 Indiranagar 100ft Road, Bengaluru 560038",
        line_items=[
            {"num": 1, "desc": "Enterprise Cloud Hosting Subscription", "hsn": "998315", "qty": 1.0, "rate": 50000.0, "tax_rate": 18.0, "total": 50000.0},
            {"num": 2, "desc": "Dedicated AI Workload Accelerator", "hsn": "998313", "qty": 2.0, "rate": 25000.0, "tax_rate": 18.0, "total": 50000.0}
        ],
        subtotal=100000.0,
        cgst=9000.0,
        sgst=9000.0,
        igst=0.0,
        grand_total=118000.0
    )

    # 2. Standard Compliant Invoice 2 (Inter-state IGST)
    create_invoice_pdf(
        filename="invoice_standard_02.pdf",
        invoice_number="INV-2026-0942",
        invoice_date="2026-10-20",
        due_date="2026-11-20",
        supplier_name="CyberShield Security Systems Ltd",
        supplier_gstin="27AABCC9988D1Z9",
        supplier_address="88 Nariman Point, Mumbai 400021",
        customer_name="DocuMind Enterprise Corp",
        customer_gstin="29XYZAB5678C1Z2",
        customer_address="108 Indiranagar 100ft Road, Bengaluru 560038",
        line_items=[
            {"num": 1, "desc": "Annual Automated Pen-Testing License", "hsn": "998319", "qty": 1.0, "rate": 75000.0, "tax_rate": 18.0, "total": 75000.0}
        ],
        subtotal=75000.0,
        cgst=0.0,
        sgst=0.0,
        igst=13500.0,
        grand_total=88500.0
    )

    # 3. Invoice with Mathematical Mismatch (Intentionally flawed for Validation Agent)
    create_invoice_pdf(
        filename="invoice_math_error.pdf",
        invoice_number="INV-FLAWED-103",
        invoice_date="2026-10-25",
        due_date="2026-11-25",
        supplier_name="Delta Hardware Supplies LLP",
        supplier_gstin="29DEFGH5678J1Z3",
        supplier_address="12 Peenya Industrial Area, Bengaluru 560058",
        customer_name="DocuMind Enterprise Corp",
        customer_gstin="29XYZAB5678C1Z2",
        customer_address="108 Indiranagar 100ft Road, Bengaluru 560038",
        line_items=[
            {"num": 1, "desc": "Server Rack Mounting Shelves", "hsn": "8471", "qty": 4.0, "rate": 10000.0, "tax_rate": 18.0, "total": 40000.0}
        ],
        subtotal=40000.0,
        cgst=3600.0,
        sgst=3600.0,
        igst=0.0,
        grand_total=55000.0  # Intentional discrepancy: 40000 + 7200 != 55000
    )

    # 4. Duplicate Invoice (Identical to invoice_standard_01 to trigger Duplicate Detection)
    create_invoice_pdf(
        filename="invoice_duplicate.pdf",
        invoice_number="INV-2026-0891",
        invoice_date="2026-10-15",
        due_date="2026-11-15",
        supplier_name="Apex Cloud Technologies Pvt Ltd",
        supplier_gstin="29ABCDE1234F1Z5",
        supplier_address="42 Tech Park, Outer Ring Road, Bengaluru 560103",
        customer_name="DocuMind Enterprise Corp",
        customer_gstin="29XYZAB5678C1Z2",
        customer_address="108 Indiranagar 100ft Road, Bengaluru 560038",
        line_items=[
            {"num": 1, "desc": "Enterprise Cloud Hosting Subscription", "hsn": "998315", "qty": 1.0, "rate": 50000.0, "tax_rate": 18.0, "total": 50000.0},
            {"num": 2, "desc": "Dedicated AI Workload Accelerator", "hsn": "998313", "qty": 2.0, "rate": 25000.0, "tax_rate": 18.0, "total": 50000.0}
        ],
        subtotal=100000.0,
        cgst=9000.0,
        sgst=9000.0,
        igst=0.0,
        grand_total=118000.0
    )

    # 5. Purchase Order (For Classification Agent)
    create_invoice_pdf(
        filename="purchase_order_01.pdf",
        invoice_number="PO-2026-5501",
        invoice_date="2026-10-10",
        due_date="2026-11-10",
        supplier_name="Quantum Chipsets International",
        supplier_gstin="29AAACH8899K1Z4",
        supplier_address="14 Whitefield Main Road, Bengaluru 560066",
        customer_name="DocuMind Enterprise Corp",
        customer_gstin="29XYZAB5678C1Z2",
        customer_address="108 Indiranagar 100ft Road, Bengaluru 560038",
        line_items=[
            {"num": 1, "desc": "Edge AI Inference Processors", "hsn": "8473", "qty": 10.0, "rate": 15000.0, "tax_rate": 18.0, "total": 150000.0}
        ],
        subtotal=150000.0,
        cgst=13500.0,
        sgst=13500.0,
        igst=0.0,
        grand_total=177000.0,
        title="PURCHASE ORDER"
    )

    # 6. Payment Receipt (For Classification Agent)
    create_invoice_pdf(
        filename="receipt_01.pdf",
        invoice_number="RCP-2026-302",
        invoice_date="2026-10-18",
        due_date="2026-10-18",
        supplier_name="Metro Office Spaces & Coworking",
        supplier_gstin="29BBBBB4433P1Z1",
        supplier_address="77 MG Road, Bengaluru 560001",
        customer_name="DocuMind Enterprise Corp",
        customer_gstin="29XYZAB5678C1Z2",
        customer_address="108 Indiranagar 100ft Road, Bengaluru 560038",
        line_items=[
            {"num": 1, "desc": "Conference Room Booking - October", "hsn": "9972", "qty": 1.0, "rate": 8000.0, "tax_rate": 18.0, "total": 8000.0}
        ],
        subtotal=8000.0,
        cgst=720.0,
        sgst=720.0,
        igst=0.0,
        grand_total=9440.0,
        title="PAYMENT RECEIPT"
    )


if __name__ == "__main__":
    generate_all_samples()

