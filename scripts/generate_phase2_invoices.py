import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

OUT_DIR = Path(__file__).resolve().parent.parent / "evaluation" / "datasets" / "phase2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

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
) -> str:
    pdf_path = OUT_DIR / filename
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor('#102A43'), alignment=1)
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 15))

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

    footer_text = "<font size=8 color='#627D98'>This is a computer generated test invoice created for DocuMind AI Phase 2 Verification.</font>"
    story.append(Paragraph(footer_text, styles['Normal']))

    doc.build(story)
    print(f"Generated Phase 2 invoice: {pdf_path}")
    return str(pdf_path)

def generate_phase2_invoices():
    print("Generating Phase 2 Synthetic GST Invoices...")

    # 1. Clean Intra-State GST (CGST 9% + SGST 9%)
    create_invoice_pdf(
        filename="p2_invoice_01_clean_intra.pdf",
        invoice_number="INV-2026-GST-01",
        invoice_date="2026-11-01",
        due_date="2026-12-01",
        supplier_name="Kavitha Infotech Solutions Pvt Ltd",
        supplier_gstin="29AAACK1234F1Z8",
        supplier_address="15 Koramangala Industrial Area, Bengaluru 560034",
        customer_name="DocuMind Enterprise Corp",
        customer_gstin="29XYZAB5678C1Z2",
        customer_address="108 Indiranagar 100ft Road, Bengaluru 560038",
        line_items=[
            {"num": 1, "desc": "Enterprise Software Maintenance", "hsn": "998314", "qty": 1.0, "rate": 25000.0, "tax_rate": 18.0, "total": 25000.0},
            {"num": 2, "desc": "Cloud Database Optimization", "hsn": "998315", "qty": 1.0, "rate": 15000.0, "tax_rate": 18.0, "total": 15000.0}
        ],
        subtotal=40000.0,
        cgst=3600.0,
        sgst=3600.0,
        igst=0.0,
        grand_total=47200.0
    )

    # 2. Clean Inter-State GST (IGST 18%)
    create_invoice_pdf(
        filename="p2_invoice_02_clean_inter.pdf",
        invoice_number="INV-2026-GST-02",
        invoice_date="2026-11-02",
        due_date="2026-12-02",
        supplier_name="Maharashtra Cloud Datacenters LLP",
        supplier_gstin="27AABCM5678D1Z2",
        supplier_address="102 Bandra Kurla Complex, Mumbai 400051",
        customer_name="DocuMind Enterprise Corp",
        customer_gstin="29XYZAB5678C1Z2",
        customer_address="108 Indiranagar 100ft Road, Bengaluru 560038",
        line_items=[
            {"num": 1, "desc": "High-Throughput GPU Cluster Ingress", "hsn": "998316", "qty": 1.0, "rate": 65000.0, "tax_rate": 18.0, "total": 65000.0}
        ],
        subtotal=65000.0,
        cgst=0.0,
        sgst=0.0,
        igst=11700.0,
        grand_total=76700.0
    )

    # 3. Flawed Invoice: Line item sum mismatch vs. Subtotal (₹30k vs ₹35k)
    create_invoice_pdf(
        filename="p2_invoice_03_math_mismatch.pdf",
        invoice_number="INV-2026-ERR-03",
        invoice_date="2026-11-02",
        due_date="2026-12-02",
        supplier_name="Bengaluru Industrial Supplies Co",
        supplier_gstin="29AAACB9012E1Z4",
        supplier_address="50 Peenya 2nd Stage, Bengaluru 560058",
        customer_name="DocuMind Enterprise Corp",
        customer_gstin="29XYZAB5678C1Z2",
        customer_address="108 Indiranagar 100ft Road, Bengaluru 560038",
        line_items=[
            {"num": 1, "desc": "Rack Mount Cooling Fans", "hsn": "8414", "qty": 2.0, "rate": 15000.0, "tax_rate": 18.0, "total": 30000.0}
        ],
        subtotal=35000.0,  # Line item sum is 30,000 but subtotal says 35,000!
        cgst=3150.0,
        sgst=3150.0,
        igst=0.0,
        grand_total=41300.0
    )

    # 4. Anomaly Invoice: Unusual Spend Spike (>3x median)
    create_invoice_pdf(
        filename="p2_invoice_04_spend_anomaly.pdf",
        invoice_number="INV-2026-ANOMALY-04",
        invoice_date="2026-11-03",
        due_date="2026-12-03",
        supplier_name="Kavitha Infotech Solutions Pvt Ltd",
        supplier_gstin="29AAACK1234F1Z8",
        supplier_address="15 Koramangala Industrial Area, Bengaluru 560034",
        customer_name="DocuMind Enterprise Corp",
        customer_gstin="29XYZAB5678C1Z2",
        customer_address="108 Indiranagar 100ft Road, Bengaluru 560038",
        line_items=[
            {"num": 1, "desc": "Turnkey Enterprise Infrastructure Overhaul", "hsn": "998319", "qty": 1.0, "rate": 450000.0, "tax_rate": 18.0, "total": 450000.0}
        ],
        subtotal=450000.0,  # Massive 10x spike vs typical 40k spend
        cgst=40500.0,
        sgst=40500.0,
        igst=0.0,
        grand_total=531000.0
    )

    # 5. Invalid GSTIN Format Invoice
    create_invoice_pdf(
        filename="p2_invoice_05_invalid_gstin.pdf",
        invoice_number="INV-2026-GSTIN-05",
        invoice_date="2026-11-03",
        due_date="2026-12-03",
        supplier_name="QuickPrint Stationery Hub",
        supplier_gstin="INVALID_GSTIN_123",  # Non-compliant format
        supplier_address="8 Brigade Road, Bengaluru 560025",
        customer_name="DocuMind Enterprise Corp",
        customer_gstin="29XYZAB5678C1Z2",
        customer_address="108 Indiranagar 100ft Road, Bengaluru 560038",
        line_items=[
            {"num": 1, "desc": "Custom Legal Document Envelopes", "hsn": "4817", "qty": 500.0, "rate": 20.0, "tax_rate": 12.0, "total": 10000.0}
        ],
        subtotal=10000.0,
        cgst=600.0,
        sgst=600.0,
        igst=0.0,
        grand_total=11200.0
    )

    # 6. Duplicate Invoice: Exact clone of Invoice 1
    create_invoice_pdf(
        filename="p2_invoice_06_duplicate.pdf",
        invoice_number="INV-2026-GST-01",
        invoice_date="2026-11-01",
        due_date="2026-12-01",
        supplier_name="Kavitha Infotech Solutions Pvt Ltd",
        supplier_gstin="29AAACK1234F1Z8",
        supplier_address="15 Koramangala Industrial Area, Bengaluru 560034",
        customer_name="DocuMind Enterprise Corp",
        customer_gstin="29XYZAB5678C1Z2",
        customer_address="108 Indiranagar 100ft Road, Bengaluru 560038",
        line_items=[
            {"num": 1, "desc": "Enterprise Software Maintenance", "hsn": "998314", "qty": 1.0, "rate": 25000.0, "tax_rate": 18.0, "total": 25000.0},
            {"num": 2, "desc": "Cloud Database Optimization", "hsn": "998315", "qty": 1.0, "rate": 15000.0, "tax_rate": 18.0, "total": 15000.0}
        ],
        subtotal=40000.0,
        cgst=3600.0,
        sgst=3600.0,
        igst=0.0,
        grand_total=47200.0
    )

    print("All 6 Phase 2 synthetic test invoices created successfully in evaluation/datasets/phase2/")

if __name__ == "__main__":
    generate_phase2_invoices()

