"""
Spot-check verification of AI extraction on diverse benchmark invoice categories:
1. Standard intra-state (b01)
2. Trade discount (b21)
3. Complex multi-line (b26)
4. Multi-page carried forward (b31)
5. Scanned / Degraded (b46)
"""
import sys
import json
import time
from pathlib import Path
from decimal import Decimal

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "backend"))

import fitz
from app.core.config import settings
settings.AI_PRIMARY_PROVIDER = "groq"
from app.services.llm import LLMService

BENCHMARK_DIR = root / "evaluation" / "datasets" / "benchmark_50"
GT_FILE = BENCHMARK_DIR / "ground_truth.json"

with open(GT_FILE, "r") as f:
    ground_truth = json.load(f)

test_invoices = [
    ("invoice_b01_INV-2026-B001.pdf", "INV-2026-B001"),
    ("invoice_b21_INV-2026-B021.pdf", "INV-2026-B021"),
    ("invoice_b26_INV-2026-B026.pdf", "INV-2026-B026"),
    ("invoice_b31_INV-2026-B031.pdf", "INV-2026-B031"),
    ("invoice_b46_INV-2026-B046.pdf", "INV-2026-B046"),
]

def numbers_match(val1, val2, tolerance=2.0):
    try:
        return abs(float(val1 or 0) - float(val2 or 0)) <= tolerance
    except Exception:
        return False

def strings_match(s1, s2):
    if not s1 and not s2: return True
    if not s1 or not s2: return False
    c1 = "".join(str(s1).lower().split())
    c2 = "".join(str(s2).lower().split())
    return c1 == c2 or c1 in c2 or c2 in c1

total_fields = 0
correct_fields = 0

print("Running Spot-Check Verification on 5 Diverse Benchmark Categories:")
for filename, inv_num in test_invoices:
    pdf_path = BENCHMARK_DIR / filename
    doc = fitz.open(str(pdf_path))
    raw_text = "\n\n".join([page.get_text() for page in doc])
    gt = ground_truth[inv_num]
    
    t0 = time.time()
    extracted, tokens, cost = LLMService.extract_invoice_data(raw_text)
    latency = time.time() - t0
    
    checks = {
        "invoice_number": strings_match(extracted.get("invoice_number"), gt.get("invoice_number")),
        "supplier_name": strings_match(extracted.get("supplier_name"), gt.get("supplier_name")),
        "supplier_gstin": strings_match(extracted.get("supplier_gstin"), gt.get("supplier_gstin")),
        "taxable_amount": numbers_match(extracted.get("taxable_amount"), gt.get("taxable_amount")),
        "cgst": numbers_match(extracted.get("cgst"), gt.get("cgst")),
        "sgst": numbers_match(extracted.get("sgst"), gt.get("sgst")),
        "igst": numbers_match(extracted.get("igst"), gt.get("igst")),
        "grand_total": numbers_match(extracted.get("grand_total"), gt.get("grand_total")),
    }
    
    doc_correct = sum(1 for v in checks.values() if v)
    total_fields += 8
    correct_fields += doc_correct
    
    print(f"  {inv_num} ({gt['category']}) | Accuracy: {doc_correct}/8 | Latency: {latency:.2f}s | Tokens: {tokens}")
    for f, pass_ in checks.items():
        if not pass_:
            print(f"    FAIL {f}: Extracted={extracted.get(f)}, GT={gt.get(f)}")

print(f"\nSpot Check Result: {correct_fields}/{total_fields} fields correct ({correct_fields/total_fields*100:.1f}%)")

