import os
import csv
import json
import uuid
from decimal import Decimal
from typing import List, Dict, Any, Tuple
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from app.core.config import settings


class ExportEngine:
    @classmethod
    def generate_excel_report(cls, records: List[Dict[str, Any]], export_type: str, organization_id: str) -> Tuple[str, int]:
        """
        Builds a styled, production-grade Excel report with formatted headers and auto-sized columns.
        Returns: (file_path, record_count)
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = export_type[:31]

        # Theme styling (Dark Navy header)
        header_fill = PatternFill(start_color="102A43", end_color="102A43", fill_type="solid")
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        data_font = Font(name="Segoe UI", size=10)
        thin_border = Border(
            left=Side(style='thin', color="E2E8F0"),
            right=Side(style='thin', color="E2E8F0"),
            top=Side(style='thin', color="E2E8F0"),
            bottom=Side(style='thin', color="E2E8F0")
        )

        if not records:
            ws.append(["No records found matching criteria."])
            os.makedirs(os.path.join(settings.UPLOAD_DIR, "exports"), exist_ok=True)
            filename = f"export_{export_type.lower()}_{uuid.uuid4().hex[:8]}.xlsx"
            out_path = os.path.join(settings.UPLOAD_DIR, "exports", filename)
            wb.save(out_path)
            return out_path, 0

        # Extract headers from first record
        headers = list(records[0].keys())
        ws.append([h.replace("_", " ").title() for h in headers])

        # Style header row
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        ws.row_dimensions[1].height = 28

        # Write data rows
        for row_idx, rec in enumerate(records, start=2):
            row_data = [rec.get(h) for h in headers]
            ws.append(row_data)
            ws.row_dimensions[row_idx].height = 20
            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.font = data_font
                cell.border = thin_border
                if isinstance(cell.value, (int, float, Decimal)):
                    cell.number_format = '#,##0.00'
                    cell.alignment = Alignment(horizontal="right")

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or '')
                if len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        os.makedirs(os.path.join(settings.UPLOAD_DIR, "exports"), exist_ok=True)
        filename = f"export_{export_type.lower()}_{uuid.uuid4().hex[:8]}.xlsx"
        out_path = os.path.join(settings.UPLOAD_DIR, "exports", filename)
        wb.save(out_path)
        return out_path, len(records)

    @classmethod
    def generate_csv_report(cls, records: List[Dict[str, Any]], export_type: str, organization_id: str) -> Tuple[str, int]:
        os.makedirs(os.path.join(settings.UPLOAD_DIR, "exports"), exist_ok=True)
        filename = f"export_{export_type.lower()}_{uuid.uuid4().hex[:8]}.csv"
        out_path = os.path.join(settings.UPLOAD_DIR, "exports", filename)

        if not records:
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                f.write("No records found\n")
            return out_path, 0

        headers = list(records[0].keys())
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for r in records:
                writer.writerow(r)

        return out_path, len(records)
