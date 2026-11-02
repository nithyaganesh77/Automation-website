import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
os.environ["PYTHONPATH"] = str(backend_dir)

from app.core.config import settings
from app.services.llm import LLMService

def test_api_keys():
    print("=" * 60)
    print("DOCUMIND AI — API PROVIDER LIVE VERIFICATION")
    print("=" * 60)

    print(f"Primary Provider:   {settings.AI_PRIMARY_PROVIDER}")
    print(f"Fallback Provider:  {settings.AI_FALLBACK_PROVIDER}")
    print(f"Gemini Model:       {settings.GEMINI_MODEL}")
    print(f"Groq Model:         {settings.GROQ_MODEL}")
    print(f"Gemini Key set:     {bool(settings.GEMINI_API_KEY)} (Masked: {settings.GEMINI_API_KEY[:4]}...{settings.GEMINI_API_KEY[-4:] if settings.GEMINI_API_KEY else ''})")
    print(f"Groq Key set:       {bool(settings.GROQ_API_KEY)} (Masked: {settings.GROQ_API_KEY[:4]}...{settings.GROQ_API_KEY[-4:] if settings.GROQ_API_KEY else ''})")
    print("-" * 60)

    # 1. Test Gemini Connection
    print("\n[1] Testing Google Gemini API connection...")
    success_gemini, msg_gemini = LLMService.test_provider_connection("gemini", settings.GEMINI_API_KEY)
    print(f"    Status:  {'SUCCESS' if success_gemini else 'FAILED'}")
    print(f"    Message: {msg_gemini}")

    # 2. Test Groq Connection
    print("\n[2] Testing Groq API connection...")
    success_groq, msg_groq = LLMService.test_provider_connection("groq", settings.GROQ_API_KEY)
    print(f"    Status:  {'SUCCESS' if success_groq else 'FAILED'}")
    print(f"    Message: {msg_groq}")

    # 3. Test Structured JSON Classification
    print("\n[3] Testing Document Classification with Failover Engine...")
    sample_text = """
    TAX INVOICE
    Invoice Number: INV-2026-9021
    Date: 02/11/2026
    Supplier: TechCorp Systems Pvt Ltd
    GSTIN: 27AABCT1234F1Z8
    Subtotal: INR 20,000.00
    CGST (9%): INR 1,800.00
    SGST (9%): INR 1,800.00
    Grand Total: INR 23,600.00
    """
    doc_type, confidence, metadata = LLMService.classify_document(sample_text)
    print(f"    Classified Type: {doc_type}")
    print(f"    Confidence:      {confidence}")
    print(f"    Metadata:        {metadata}")

    # 4. Test Extraction
    print("\n[4] Testing Structured Invoice Field Extraction...")
    data, tokens, cost = LLMService.extract_invoice_data(sample_text)
    print(f"    Invoice Number:   {data.get('invoice_number')}")
    print(f"    Supplier Name:    {data.get('supplier_name')}")
    print(f"    Supplier GSTIN:   {data.get('supplier_gstin')}")
    print(f"    Subtotal:         {data.get('subtotal')}")
    print(f"    Grand Total:      {data.get('grand_total')}")
    print(f"    Line Items Count: {len(data.get('line_items', []))}")
    print(f"    Tokens Used:      {tokens}")
    print(f"    Estimated Cost:   ${cost}")

    # 5. Telemetry
    print("\n[5] AI Telemetry & Usage Stats:")
    telemetry = LLMService.get_telemetry()
    for k, v in telemetry.items():
        print(f"    {k}: {v}")

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_api_keys()
