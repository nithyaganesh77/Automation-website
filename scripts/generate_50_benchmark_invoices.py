import json
import random
from pathlib import Path
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

OUT_DIR = Path(__file__).resolve().parent.parent / "evaluation" / "datasets" / "benchmark_50"
OUT_DIR.mkdir(parents=True, exist_ok=True)

INDIAN_STATES = [
    ("Karnataka", "29", "Bengaluru"),
    ("Maharashtra", "27", "Mumbai"),
    ("Tamil Nadu", "33", "Chennai"),
    ("Delhi", "07", "New Delhi"),
    ("Telangana", "36", "Hyderabad"),
    ("Gujarat", "24", "Ahmedabad"),
    ("Uttar Pradesh", "09", "Noida"),
    ("West Bengal", "19", "Kolkata"),
    ("Kerala", "32", "Kochi"),
    ("Rajasthan", "08", "Jaipur")
]

SUPPLIER_NAMES = [
    "Nexus Cloud Technologies Pvt Ltd",
    "Apex Logistics & Warehousing LLP",
    "Vanguard Heavy Engineering Works",
    "Sunrise Packaging Solutions Co",
    "Bharat Petroleum Instruments Corp",
    "Kaveri Silk & Textiles Ltd",
    "Zenith Office Automations Pvt Ltd",
    "Indus Polymer Polymers Pvt Ltd",
    "Deccan Precision Tooling Ltd",
    "Matrix Electrical Components LLP"
]

def make_gstin(state_code: str, pan: str, entity_num="1", z="Z", checksum="5"):
    return f"{state_code}{pan}{entity_num}{z}{checksum}"

def generate_50_invoices():
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1E3A8A"),
        alignment=1
    )
    bold_style = ParagraphStyle("Bold", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=12)
    normal_style = ParagraphStyle("NormalText", parent=styles["Normal"], fontName="Helvetica", fontSize=8, leading=11)
    right_bold = ParagraphStyle("RightBold", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=12, alignment=2)
    right_normal = ParagraphStyle("RightNorm", parent=styles["Normal"], fontName="Helvetica", fontSize=8, leading=11, alignment=2)

    ground_truth = {}

    print(f"Generating 50 synthetic benchmark invoice variations in: {OUT_DIR}")

    for idx in range(1, 51):
        inv_num = f"INV-2026-B{idx:03d}"
        inv_date = f"2026-{random.randint(1, 10):02d}-{random.randint(1, 28):02d}"
        due_date = f"2026-{random.randint(11, 12):02d}-{random.randint(1, 28):02d}"
        
        state_name, state_code, city = INDIAN_STATES[(idx - 1) % len(INDIAN_STATES)]
        supp_name = SUPPLIER_NAMES[(idx - 1) % len(SUPPLIER_NAMES)]
        pan = f"AAAC{idx:02d}491F"
        supp_gstin = make_gstin(state_code, pan)
        
        # Decide Intra vs Inter-state
        # Odd numbers: Intra-state (CGST+SGST), Even numbers: Inter-state (IGST)
        is_intra = (idx % 2 != 0)
        
        # Category specific logic
        is_multi_page = (31 <= idx <= 35)
        is_flawed = (41 <= idx <= 45)
        has_discount = (21 <= idx <= 25)
        is_complex = (26 <= idx <= 30)
        is_scanned = (46 <= idx <= 50)
        has_missing_fields = (36 <= idx <= 40)

        # Build items
        num_items = 8 if is_complex else (6 if is_multi_page else random.randint(2, 4))
        items_data = []
        subtotal = Decimal("0.00")
        
        for item_idx in range(1, num_items + 1):
            qty = Decimal(str(random.randint(2, 20)))
            unit_price = Decimal(str(random.randint(50, 500) * 10))
            line_tot = qty * unit_price
            subtotal += line_tot
            items_data.append([
                Paragraph(str(item_idx), normal_style),
                Paragraph(f"Commercial Supply Item #{item_idx} - Grade {chr(64 + item_idx)}", normal_style),
                Paragraph(f"{8400 + item_idx}", normal_style),
                Paragraph(f"{qty:.1f} Nos", normal_style),
                Paragraph(f"INR {unit_price:,.2f}", right_normal),
                Paragraph(f"INR {line_tot:,.2f}", right_normal)
            ])

        discount = Decimal("0.00")
        if has_discount:
            discount = Decimal("2500.00")

        taxable_amount = max(subtotal - discount, Decimal("0.00"))

        if is_intra:
            tax_rate = Decimal("18.0")
            cgst = (taxable_amount * Decimal("0.09")).quantize(Decimal("0.01"))
            sgst = (taxable_amount * Decimal("0.09")).quantize(Decimal("0.01"))
            igst = Decimal("0.00")
        else:
            tax_rate = Decimal("18.0")
            cgst = Decimal("0.00")
            sgst = Decimal("0.00")
            igst = (taxable_amount * Decimal("0.18")).quantize(Decimal("0.01"))

        total_tax = cgst + sgst + igst
        grand_total = taxable_amount + total_tax

        # Introduce intentional flaws for 41-45
        if is_flawed:
            if idx == 41:
                # Math mismatch: subtotal manipulated
                subtotal += Decimal("5000.00")
            elif idx == 42:
                # Invalid GSTIN
                supp_gstin = "INVALID_99X_GSTIN"
            elif idx == 43:
                # Grand total mismatch
                grand_total += Decimal("10000.00")
            elif idx == 44:
                # High spend spike
                grand_total = grand_total * Decimal("10")
                taxable_amount = taxable_amount * Decimal("10")

        # Save ground truth
        ground_truth[inv_num] = {
            "invoice_number": inv_num,
            "invoice_date": inv_date,
            "supplier_name": supp_name,
            "supplier_gstin": supp_gstin,
            "taxable_amount": float(taxable_amount),
            "cgst": float(cgst),
            "sgst": float(sgst),
            "igst": float(igst),
            "grand_total": float(grand_total),
            "is_intra": is_intra,
            "is_flawed": is_flawed,
            "category": (
                "flawed" if is_flawed else
                "multi_page" if is_multi_page else
                "discount" if has_discount else
                "complex" if is_complex else
                "scanned" if is_scanned else
                "missing_fields" if has_missing_fields else
                "standard"
            )
        }

        # Build PDF with ReportLab
        pdf_path = OUT_DIR / f"invoice_b{idx:02d}_{inv_num}.pdf"
        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        story = []

        # Header Title
        title_text = "TAX INVOICE"
        if is_scanned:
            title_text = "TAX INVOICE [OFFICIAL DIGITIZED COPY]"
        story.append(Paragraph(title_text, title_style))
        story.append(Spacer(1, 10))

        # Metadata Table
        buyer_gstin = "29AAACD9981F1Z8" if not has_missing_fields else ""
        buyer_po = f"PO-2026-{idx:04d}" if not has_missing_fields else ""
        meta_table_data = [
            [
                Paragraph(f"<b>Supplier:</b><br/>{supp_name}<br/>Plot {idx*4}, Industrial Area, {city}<br/>{state_name} - State Code: {state_code}<br/><b>GSTIN:</b> {supp_gstin}", normal_style),
                Paragraph(f"<b>Invoice No:</b> {inv_num}<br/><b>Date:</b> {inv_date}<br/><b>Due Date:</b> {due_date}<br/><b>Place of Supply:</b> {state_name}<br/><b>PO Reference:</b> {buyer_po}", normal_style)
            ],
            [
                Paragraph(f"<b>Billed To (Customer):</b><br/>DocuMind Enterprise Corp India<br/>Embassy Tech Village, Outer Ring Road<br/>Bengaluru, Karnataka - 560103<br/><b>GSTIN:</b> {buyer_gstin}", normal_style),
                Paragraph(f"<b>Payment Terms:</b> Net 30 Days<br/><b>Currency:</b> INR (Indian Rupee)<br/><b>Reverse Charge:</b> No<br/><b>E-Way Bill:</b> EWB-{idx:08d}", normal_style)
            ]
        ]
        meta_table = Table(meta_table_data, colWidths=[270, 270])
        meta_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 12))

        # Items Table
        item_headers = [
            Paragraph("#", bold_style),
            Paragraph("Item Description", bold_style),
            Paragraph("HSN/SAC", bold_style),
            Paragraph("Qty", bold_style),
            Paragraph("Unit Price", right_bold),
            Paragraph("Amount", right_bold)
        ]
        
        table_rows = [item_headers]
        if is_multi_page:
            # First 3 items on page 1, page break, then next 3 on page 2
            table_rows.extend(items_data[:3])
            t1 = Table(table_rows, colWidths=[30, 210, 60, 60, 90, 90])
            t1.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(t1)
            story.append(Spacer(1, 15))
            story.append(Paragraph(f"<i>Subtotal carried forward to Page 2...</i>", normal_style))
            story.append(PageBreak())
            story.append(Paragraph(f"<b>TAX INVOICE — {inv_num} (Page 2 of 2)</b>", bold_style))
            story.append(Spacer(1, 10))
            
            table_rows_p2 = [item_headers] + items_data[3:]
            t2 = Table(table_rows_p2, colWidths=[30, 210, 60, 60, 90, 90])
            t2.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(t2)
        else:
            table_rows.extend(items_data)
            t_main = Table(table_rows, colWidths=[30, 210, 60, 60, 90, 90])
            t_main.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(t_main)

        story.append(Spacer(1, 10))

        # Totals Table
        totals_data = [
            [Paragraph("Subtotal:", right_normal), Paragraph(f"INR {subtotal:,.2f}", right_normal)],
            [Paragraph("Discount / Trade Rebate:", right_normal), Paragraph(f"INR {discount:,.2f}", right_normal)],
            [Paragraph("Taxable Value:", right_bold), Paragraph(f"INR {taxable_amount:,.2f}", right_bold)],
        ]
        if is_intra:
            totals_data.append([Paragraph("CGST (9.0%):", right_normal), Paragraph(f"INR {cgst:,.2f}", right_normal)])
            totals_data.append([Paragraph("SGST (9.0%):", right_normal), Paragraph(f"INR {sgst:,.2f}", right_normal)])
        else:
            totals_data.append([Paragraph("IGST (18.0%):", right_normal), Paragraph(f"INR {igst:,.2f}", right_normal)])

        totals_data.append([Paragraph("<b>Grand Total:</b>", right_bold), Paragraph(f"<b>INR {grand_total:,.2f}</b>", right_bold)])

        tot_table = Table(totals_data, colWidths=[400, 140])
        tot_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#FEF3C7")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(tot_table)

        # Footer notes
        story.append(Spacer(1, 15))
        story.append(Paragraph("Declaration: We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct.", normal_style))
        story.append(Spacer(1, 5))
        story.append(Paragraph(f"Authorized Signatory for <b>{supp_name}</b>", normal_style))

        doc.build(story)

    # Save Ground Truth JSON
    gt_path = OUT_DIR / "ground_truth.json"
    with open(gt_path, "w") as f:
        json.dump(ground_truth, f, indent=2)

    print(f"\nGenerated 50 benchmark PDFs and ground_truth.json in: {OUT_DIR}")

if __name__ == "__main__":
    generate_50_invoices()

