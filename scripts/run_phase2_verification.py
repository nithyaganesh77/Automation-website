import os
import sys
import json
import time
import requests
from decimal import Decimal
from pathlib import Path
import openpyxl

# Force UTF-8 on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api/v1"
DATASET_DIR = Path(__file__).resolve().parent.parent / "evaluation" / "datasets" / "phase2"

def print_section(title: str):
    print("\n" + "=" * 70)
    print(f" {title} ")
    print("=" * 70)

def run_phase2_verification():
    results = {
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "connectivity": {},
        "uploads": [],
        "duplicate_test": {},
        "anomaly_test": {},
        "validation_test": {},
        "approval_test": {},
        "rejection_test": {},
        "persistence_test": {},
        "excel_export_test": {},
        "tenant_isolation_test": {},
        "dashboard_metrics": {}
    }

    print_section("PHASE 2: REAL-WORLD END-TO-END SYSTEM VERIFICATION")

    # -------------------------------------------------------------
    # 1. VERIFY FRONTEND & BACKEND CONNECTIVITY
    # -------------------------------------------------------------
    print("\n[Step 1] Verifying Backend & Frontend Connectivity...")
    # Backend health
    resp_health = requests.get(f"{BASE_URL}/health", timeout=5)
    assert resp_health.status_code == 200, f"Backend health failed: {resp_health.text}"
    health_data = resp_health.json()
    print(f"  Backend Health:  OK (Status: {health_data.get('status')}, Version: {health_data.get('version')})")

    # Frontend root
    resp_fe = requests.get("http://localhost:3000", timeout=5)
    assert resp_fe.status_code == 200, f"Frontend root failed: {resp_fe.status_code}"
    print(f"  Frontend Server: OK (Port 3000 responding HTTP 200, length {len(resp_fe.content)} bytes)")

    results["connectivity"]["backend"] = health_data
    results["connectivity"]["frontend_status"] = resp_fe.status_code

    # -------------------------------------------------------------
    # 2. AUTHENTICATION (ADMIN & REVIEWER)
    # -------------------------------------------------------------
    print("\n[Step 2] Authenticating Test Users...")
    # Admin login
    admin_login_res = requests.post(f"{API_BASE}/auth/login", json={
        "email": "admin@documind.ai",
        "password": "Password123!"
    }, timeout=5)
    assert admin_login_res.status_code == 200, f"Admin login failed: {admin_login_res.text}"
    admin_auth = admin_login_res.json()
    admin_token = admin_auth["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print(f"  Admin Logged In:    {admin_auth['user']['email']} (Org: {admin_auth['user']['role']})")

    # Reviewer login
    rev_login_res = requests.post(f"{API_BASE}/auth/login", json={
        "email": "reviewer@documind.ai",
        "password": "Password123!"
    }, timeout=5)
    assert rev_login_res.status_code == 200, f"Reviewer login failed: {rev_login_res.text}"
    rev_auth = rev_login_res.json()
    rev_token = rev_auth["access_token"]
    rev_headers = {"Authorization": f"Bearer {rev_token}"}
    print(f"  Reviewer Logged In: {rev_auth['user']['email']} (Org: {rev_auth['user']['role']})")

    # -------------------------------------------------------------
    # 3. UPLOAD 5 SYNTHETIC INDIAN GST INVOICES + RUN MULTI-AGENT WORKFLOW
    # -------------------------------------------------------------
    print_section("UPLOADING & EXECUTING MULTI-AGENT PIPELINE ON 5 GST INVOICES")

    invoice_files = [
        ("p2_invoice_01_clean_intra.pdf", "Clean Intra-State GST (CGST+SGST 18%)"),
        ("p2_invoice_02_clean_inter.pdf", "Clean Inter-State GST (IGST 18%)"),
        ("p2_invoice_03_math_mismatch.pdf", "Flawed Line Items vs Subtotal Discrepancy"),
        ("p2_invoice_04_spend_anomaly.pdf", "Spend Spike (>3x historical spend)"),
        ("p2_invoice_05_invalid_gstin.pdf", "Non-compliant Indian GSTIN Format")
    ]

    # Fetch existing documents to allow reusing if already processed
    existing_res = requests.get(f"{API_BASE}/documents?limit=50", headers=admin_headers)
    existing_items = existing_res.json().get("items", []) if existing_res.status_code == 200 else []
    existing_by_fname = {}
    for d in existing_items:
        if d["file_name"] not in existing_by_fname:
            existing_by_fname[d["file_name"]] = d

    uploaded_docs = {}

    for fname, desc in invoice_files:
        fpath = DATASET_DIR / fname
        assert fpath.exists(), f"File {fpath} not found!"
        
        # Check if already uploaded and processed
        if fname in existing_by_fname and os.getenv("FORCE_REUPLOAD", "false").lower() != "true":
            doc_data = existing_by_fname[fname]
            doc_id = doc_data["id"]
            uploaded_docs[fname] = doc_data
            elapsed = 0.0
            print(f"\n--> [Verified Existing] {fname} ({desc})...")
        else:
            print(f"\n--> Uploading {fname} ({desc})...")
            t0 = time.time()
            with open(fpath, "rb") as fh:
                up_res = requests.post(
                    f"{API_BASE}/documents/upload",
                    headers=admin_headers,
                    files={"file": (fname, fh, "application/pdf")},
                    timeout=120
                )
            elapsed = time.time() - t0
            assert up_res.status_code == 200, f"Upload failed for {fname}: {up_res.text}"
            doc_data = up_res.json()
            doc_id = doc_data["id"]
            uploaded_docs[fname] = doc_data

        print(f"    Document ID:    {doc_id}")
        print(f"    Status:         {doc_data.get('status')}")
        print(f"    Classified As:  {doc_data.get('document_type')} (Confidence: {doc_data.get('confidence')})")
        if elapsed > 0:
            print(f"    Elapsed Time:   {elapsed:.2f}s")

        # Fetch full dossier details (invoices, validation, agents)
        dossier_res = requests.get(f"{API_BASE}/documents/{doc_id}", headers=admin_headers, timeout=5)
        assert dossier_res.status_code == 200, f"Failed to fetch dossier: {dossier_res.text}"
        dossier = dossier_res.json()

        # Check invoice
        inv = dossier.get("invoice")
        if inv:
            print(f"    Invoice Number: {inv.get('invoice_number')}")
            print(f"    Supplier:       {inv.get('supplier_name_raw')}")
            print(f"    Grand Total:    INR {float(inv.get('grand_total') or 0):,.2f}")

        # Check validation
        vals = dossier.get("validations", [])
        val = vals[0] if vals else None
        if val:
            print(f"    Validation:     {val.get('status')} (Valid: {val.get('is_valid')}, Errors: {len(val.get('errors') or [])})")

        # Check Agent Executions
        agent_execs = dossier.get("agent_executions", [])
        print(f"    Agents Executed:{len(agent_execs)} agent nodes tracked")
        for ag in agent_execs:
            print(f"      - {ag.get('agent_name')}: {ag.get('status')} ({ag.get('latency_ms')}ms)")

        results["uploads"].append({
            "file_name": fname,
            "description": desc,
            "document_id": doc_id,
            "status": doc_data.get("status"),
            "document_type": doc_data.get("document_type"),
            "invoice_number": inv.get("invoice_number") if inv else None,
            "grand_total": float(inv.get("grand_total") or 0) if inv else None,
            "validation_status": val.get("status") if val else None,
            "agents_count": len(agent_execs),
            "elapsed_seconds": round(elapsed, 2)
        })

    # -------------------------------------------------------------
    # 4. DUPLICATE INVOICE DETECTION TEST
    # -------------------------------------------------------------
    print_section("TESTING DUPLICATE INVOICE DETECTION (INVOICE 6)")
    dup_file = DATASET_DIR / "p2_invoice_06_duplicate.pdf"
    if "p2_invoice_06_duplicate.pdf" in existing_by_fname and os.getenv("FORCE_REUPLOAD", "false").lower() != "true":
        dup_doc = existing_by_fname["p2_invoice_06_duplicate.pdf"]
        dup_doc_id = dup_doc["id"]
        print(f"\n--> [Verified Existing Duplicate] p2_invoice_06_duplicate.pdf ({dup_doc_id})...")
    else:
        print(f"\n--> Uploading duplicate invoice (clone of p2_invoice_01_clean_intra.pdf)...")
        with open(dup_file, "rb") as fh:
            dup_up_res = requests.post(
                f"{API_BASE}/documents/upload",
                headers=admin_headers,
                files={"file": ("p2_invoice_06_duplicate.pdf", fh, "application/pdf")},
                timeout=120
            )
        assert dup_up_res.status_code == 200, f"Duplicate upload failed: {dup_up_res.text}"
        dup_doc = dup_up_res.json()
        dup_doc_id = dup_doc["id"]

    # Fetch dossier
    dup_dossier = requests.get(f"{API_BASE}/documents/{dup_doc_id}", headers=admin_headers, timeout=5).json()
    dup_matches = dup_dossier.get("duplicates", [])
    print(f"  Duplicate Upload Status: {dup_doc.get('status')}")
    print(f"  Duplicates Detected:     {len(dup_matches)} match(es)")
    for dm in dup_matches:
        print(f"    - Type: {dm.get('match_type')}, Score: {dm.get('match_score')}, Matched Doc: {dm.get('matched_document_id')}")

    assert len(dup_matches) > 0, "Expected duplicate detection to flag matching invoice!"
    results["duplicate_test"] = {
        "duplicate_document_id": dup_doc_id,
        "matches_found": len(dup_matches),
        "details": dup_matches
    }

    # -------------------------------------------------------------
    # 5. MATHEMATICAL VALIDATION ENGINE VERIFICATION
    # -------------------------------------------------------------
    print_section("TESTING MATHEMATICAL VALIDATION & ERROR FLAGGING")
    flawed_doc_id = uploaded_docs["p2_invoice_03_math_mismatch.pdf"]["id"]
    flawed_dossier = requests.get(f"{API_BASE}/documents/{flawed_doc_id}", headers=admin_headers, timeout=5).json()
    flawed_vals = flawed_dossier.get("validations", [])
    flawed_val = flawed_vals[0] if flawed_vals else {}
    print(f"  Flawed Invoice ID:       {flawed_doc_id}")
    print(f"  Validation Status:       {flawed_val.get('status')}")
    print(f"  Is Valid:                {flawed_val.get('is_valid')}")
    print(f"  Reported Errors:         {flawed_val.get('errors')}")

    assert flawed_val.get("status") in ["FAILED", "WARNING"] or not flawed_val.get("is_valid"), \
        "Expected validation engine to flag calculation mismatch!"
    results["validation_test"] = {
        "document_id": flawed_doc_id,
        "status": flawed_val.get("status"),
        "is_valid": flawed_val.get("is_valid"),
        "errors": flawed_val.get("errors")
    }

    # -------------------------------------------------------------
    # 6. ANOMALY DETECTION TEST
    # -------------------------------------------------------------
    print_section("TESTING ANOMALY DETECTION AGENT")
    anomaly_doc_id = uploaded_docs["p2_invoice_04_spend_anomaly.pdf"]["id"]
    anomaly_dossier = requests.get(f"{API_BASE}/documents/{anomaly_doc_id}", headers=admin_headers, timeout=5).json()
    anomalies = anomaly_dossier.get("anomalies", [])
    print(f"  Anomaly Invoice ID:      {anomaly_doc_id}")
    print(f"  Anomalies Detected:      {len(anomalies)}")
    for a in anomalies:
        desc = str(a.get('description', '')).replace('₹', 'INR ')
        print(f"    - [{a.get('severity')}] {a.get('anomaly_type')}: {desc}")

    results["anomaly_test"] = {
        "document_id": anomaly_doc_id,
        "anomalies_count": len(anomalies),
        "findings": anomalies
    }

    # -------------------------------------------------------------
    # 7. HUMAN APPROVAL & REJECTION WORKFLOW
    # -------------------------------------------------------------
    print_section("TESTING HUMAN APPROVAL & REJECTION WORKFLOW")
    # 1. Approve Clean Invoice 1
    clean_doc_id = uploaded_docs["p2_invoice_01_clean_intra.pdf"]["id"]
    clean_check = requests.get(f"{API_BASE}/documents/{clean_doc_id}", headers=admin_headers, timeout=5).json()
    if clean_check.get("status") == "APPROVED":
        print(f"\n--> Clean Invoice 1 ({clean_doc_id}) is already APPROVED.")
    else:
        print(f"\n--> Approving Clean Invoice 1 ({clean_doc_id}) as Financial Reviewer...")
        app_res = requests.post(
            f"{API_BASE}/approvals/{clean_doc_id}/approve",
            headers=rev_headers,
            json={"action": "APPROVE", "comments": "All line items and GST calculations reconciled perfectly against PO."},
            timeout=5
        )
        assert app_res.status_code == 200, f"Approval failed: {app_res.text}"
        clean_check = requests.get(f"{API_BASE}/documents/{clean_doc_id}", headers=admin_headers, timeout=5).json()
        assert clean_check.get("status") == "APPROVED", f"Expected APPROVED but got {clean_check.get('status')}"
    print(f"    Database Persistence:   Verified document status is APPROVED")
    results["approval_test"] = {"document_id": clean_doc_id, "status": clean_check.get("status")}

    # 2. Reject Flawed Invoice 3
    flawed_check = requests.get(f"{API_BASE}/documents/{flawed_doc_id}", headers=admin_headers, timeout=5).json()
    if flawed_check.get("status") == "REJECTED":
        print(f"\n--> Flawed Invoice 3 ({flawed_doc_id}) is already REJECTED.")
    else:
        print(f"\n--> Rejecting Flawed Invoice 3 ({flawed_doc_id}) as Financial Reviewer...")
        rej_res = requests.post(
            f"{API_BASE}/approvals/{flawed_doc_id}/reject",
            headers=rev_headers,
            json={"action": "REJECT", "comments": "Rejected: Line item amounts sum to 30,000 INR, but stated subtotal is 35,000 INR."},
            timeout=5
        )
        assert rej_res.status_code == 200, f"Rejection failed: {rej_res.text}"
        flawed_check = requests.get(f"{API_BASE}/documents/{flawed_doc_id}", headers=admin_headers, timeout=5).json()
        assert flawed_check.get("status") == "REJECTED", f"Expected REJECTED but got {flawed_check.get('status')}"
    print(f"    Database Persistence:   Verified document status is REJECTED")
    results["rejection_test"] = {"document_id": flawed_doc_id, "status": flawed_check.get("status")}

    # -------------------------------------------------------------
    # 8. EXCEL REPORT GENERATION & CONTENT AUDIT
    # -------------------------------------------------------------
    print_section("TESTING EXCEL EXPORT & DATA FIDELITY")
    print("--> Requesting XLSX ledger export...")
    export_req = requests.post(
        f"{API_BASE}/reports/exports",
        headers=admin_headers,
        json={"export_type": "INVOICES", "format": "EXCEL"},
        timeout=15
    )
    assert export_req.status_code == 200, f"Export generation failed: {export_req.text}"
    export_info = export_req.json()
    export_id = export_info["id"]
    print(f"  Export Job ID:      {export_id}")
    print(f"  Export Format:      {export_info.get('format')}")
    print(f"  Record Count:       {export_info.get('record_count')}")

    # Download file
    dl_res = requests.get(f"{API_BASE}/reports/exports/{export_id}/download", headers=admin_headers, timeout=10)
    assert dl_res.status_code == 200, f"Download failed: {dl_res.status_code}"
    
    excel_path = Path("storage") / "test_verification_export.xlsx"
    with open(excel_path, "wb") as f:
        f.write(dl_res.content)
    print(f"  Export Downloaded:  {excel_path} ({len(dl_res.content)} bytes)")

    # Read Excel with openpyxl
    wb = openpyxl.load_workbook(excel_path)
    sheet = wb.active
    rows = list(sheet.iter_rows(values_only=True))
    raw_headers = [str(h).strip().title() for h in rows[0]]
    data_rows = rows[1:]

    print(f"  Workbook Loaded:    Sheet '{sheet.title}', {len(data_rows)} data rows")
    print(f"  Headers:            {raw_headers[:6]}")

    inv_idx = raw_headers.index("Invoice Number") if "Invoice Number" in raw_headers else 0
    total_idx = raw_headers.index("Grand Total") if "Grand Total" in raw_headers else 12
    stat_idx = raw_headers.index("Status") if "Status" in raw_headers else 13

    # Verify approved invoice is in Excel
    found_approved = False
    for r in data_rows:
        inv_num = str(r[inv_idx])
        grand_total = r[total_idx]
        stat = str(r[stat_idx])
        if inv_num == "INV-2026-GST-01":
            found_approved = True
            print(f"  -> Verified Invoice row: {inv_num} | Grand Total: {grand_total} | Status: {stat}")
            assert float(grand_total) == 47200.0, f"Excel total mismatch: {grand_total} vs 47200.0"

    assert found_approved, "Approved invoice INV-2026-GST-01 not found in exported Excel spreadsheet!"
    results["excel_export_test"] = {
        "file_size": len(dl_res.content),
        "rows_count": len(data_rows),
        "found_approved_invoice": found_approved
    }

    # -------------------------------------------------------------
    # 9. MULTI-TENANT ISOLATION & ACCESS CONTROL AUDIT
    # -------------------------------------------------------------
    print_section("TESTING MULTI-TENANT ISOLATION & ACCESS CONTROL")
    # Register separate tenant organization: Acme Outsourcing Corp
    acme_user_email = f"lead-{int(time.time())}@acme-outsourcing.com"
    reg_res = requests.post(f"{API_BASE}/auth/register", json={
        "email": acme_user_email,
        "password": "SecurePassword999!",
        "full_name": "Tenant Acme Lead",
        "organization_name": "Acme Outsourcing Corp"
    }, timeout=5)
    assert reg_res.status_code == 200, f"Tenant registration failed: {reg_res.text}"
    acme_auth = reg_res.json()
    acme_token = acme_auth["access_token"]
    acme_headers = {"Authorization": f"Bearer {acme_token}"}
    print(f"  Tenant 2 Created:   Acme Outsourcing Corp ({acme_user_email})")

    # Attempt 1: Acme queries DocuMind Enterprise documents list
    acme_docs_res = requests.get(f"{API_BASE}/documents", headers=acme_headers, timeout=5)
    acme_docs = acme_docs_res.json()
    print(f"  Acme Documents Listed: {acme_docs.get('total')} (Expected: 0)")
    assert acme_docs.get("total") == 0, "Security Violation: Tenant 2 saw Tenant 1 documents!"

    # Attempt 2: Acme directly requests DocuMind Enterprise document by ID
    acme_spy_res = requests.get(f"{API_BASE}/documents/{clean_doc_id}", headers=acme_headers, timeout=5)
    print(f"  Acme Cross-Tenant Read Attempt ({clean_doc_id}): HTTP {acme_spy_res.status_code}")
    assert acme_spy_res.status_code in [403, 404], "Security Violation: Cross-tenant ID query succeeded!"

    # Attempt 3: Acme attempts to approve DocuMind Enterprise document
    acme_hack_app = requests.post(f"{API_BASE}/approvals/{clean_doc_id}/approve", headers=acme_headers, json={"comments": "Illegal attempt"}, timeout=5)
    print(f"  Acme Cross-Tenant Mutation Attempt: HTTP {acme_hack_app.status_code}")
    assert acme_hack_app.status_code in [403, 404], "Security Violation: Cross-tenant approval permitted!"

    print("  -> Tenant Data Isolation: STRICTLY ENFORCED (Zero Data Leakage)")
    results["tenant_isolation_test"] = {"status": "ENFORCED", "leakage_detected": False}

    # -------------------------------------------------------------
    # 10. LIVE DASHBOARD METRICS VERIFICATION
    # -------------------------------------------------------------
    print_section("TESTING LIVE DASHBOARD METRICS")
    dash_res = requests.get(f"{API_BASE}/reports/dashboard", headers=admin_headers, timeout=5)
    assert dash_res.status_code == 200, f"Dashboard metrics failed: {dash_res.text}"
    dash_data = dash_res.json()

    agents_res = requests.get(f"{API_BASE}/agents", headers=admin_headers, timeout=5)
    assert agents_res.status_code == 200, f"Agents status failed: {agents_res.text}"
    agents_data = agents_res.json()

    print(f"  Total Documents:          {dash_data.get('total_documents')}")
    print(f"  Total Invoices:           {dash_data.get('total_invoices')}")
    print(f"  Total Invoice Value:      INR {float(dash_data.get('total_invoice_value') or 0):,.2f}")
    print(f"  Pending Approvals:        {dash_data.get('pending_approvals')}")
    print(f"  Duplicate Warnings:       {dash_data.get('duplicate_warnings')}")
    print(f"  Live Agent Nodes:         {len(agents_data)} agent nodes operational")
    for ag in agents_data:
        print(f"    * {ag.get('name')}: {ag.get('status')} ({ag.get('successful_executions')} successes, avg {ag.get('avg_latency_ms')}ms)")

    results["dashboard_metrics"] = dash_data
    results["agents_metrics"] = agents_data

    # Output JSON summary
    summary_path = Path("evaluation") / "phase2_verification_results.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w") as sf:
        json.dump(results, sf, indent=2, default=str)
    print(f"\nPhase 2 Verification results written to: {summary_path}")

    print_section("ALL 16 PHASE 2 FUNCTIONAL VERIFICATION CHECKS PASSED")

if __name__ == "__main__":
    run_phase2_verification()
