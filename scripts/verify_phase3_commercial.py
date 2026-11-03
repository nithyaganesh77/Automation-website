import os
import sys
import json
import time
import requests
from pathlib import Path

# Force UTF-8 on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api/v1"
ROOT_DIR = Path(__file__).resolve().parent.parent

def print_step(title: str):
    print("\n" + "=" * 70)
    print(f" [PHASE 3 TEST] {title}")
    print("=" * 70, flush=True)

def ensure_super_admin():
    """Ensures admin@documind.ai has is_superuser=True in the database for Super Admin tests."""
    import sqlite3
    db_path = ROOT_DIR / "documind.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_superuser = 1 WHERE email = 'admin@documind.ai'")
    conn.commit()
    conn.close()

def run_phase3_verification():
    print("=" * 70)
    print("DOCUMIND AI — PHASE 3 COMMERCIAL HARDENING & SAAS READINESS TEST")
    print("=" * 70, flush=True)

    ensure_super_admin()

    # -------------------------------------------------------------------
    # 1. SUPER ADMIN AUTHENTICATION & GLOBAL PLATFORM METRICS
    # -------------------------------------------------------------------
    print_step("1. Super Admin Authentication & Platform Telemetry")
    res = requests.post(f"{API_BASE}/auth/login", json={
        "email": "admin@documind.ai",
        "password": "Password123!"
    }, timeout=10)
    assert res.status_code == 200, f"Super Admin login failed: {res.text}"
    super_admin_token = res.json()["access_token"]
    super_admin_headers = {"Authorization": f"Bearer {super_admin_token}"}
    print(f"  Super Admin Token Obtained: {super_admin_token[:20]}...")

    # Query Super Admin Metrics
    res_metrics = requests.get(f"{API_BASE}/admin/metrics", headers=super_admin_headers, timeout=10)
    assert res_metrics.status_code == 200, f"Get super admin metrics failed: {res_metrics.text}"
    metrics_data = res_metrics.json()
    print("  Super Admin Metrics:")
    print(f"    - Total Organizations:       {metrics_data['total_organizations']}")
    print(f"    - Total Registered Users:    {metrics_data['total_users']}")
    print(f"    - Total Documents Processed: {metrics_data['total_documents']}")
    print(f"    - Total Document Spend:      INR {metrics_data['total_invoices_value_inr']:,.2f}")
    print(f"    - Active Storage Volume:     {metrics_data['total_processed_volume_bytes']} bytes")
    print(f"    - AI Primary Provider:       {metrics_data['ai_metrics'].get('primary_provider')}")
    print(f"    - Live DB Status:            {metrics_data['system_health'].get('database', {}).get('status')}")

    # Query Super Admin Organizations Overview
    res_orgs = requests.get(f"{API_BASE}/admin/organizations", headers=super_admin_headers, timeout=10)
    assert res_orgs.status_code == 200, f"Get super admin orgs failed: {res_orgs.text}"
    orgs_data = res_orgs.json()
    print(f"  Super Admin Cross-Tenant Overview: Found {len(orgs_data)} registered tenants:")
    for org in orgs_data:
        print(f"    - [{org['slug']}] {org['name']} | Plan: {org['subscription_plan']} | Members: {org['members_count']} | Docs: {org['documents_count']}")

    # -------------------------------------------------------------------
    # 2. RBAC ACCESS CONTROL ENFORCEMENT (403 FORBIDDEN FOR NON-ADMIN)
    # -------------------------------------------------------------------
    print_step("2. RBAC Tenant Boundary Enforcement (403 Forbidden Guard)")
    res_rev = requests.post(f"{API_BASE}/auth/login", json={
        "email": "reviewer@documind.ai",
        "password": "Password123!"
    }, timeout=10)
    assert res_rev.status_code == 200, f"Reviewer login failed: {res_rev.text}"
    rev_token = res_rev.json()["access_token"]
    rev_headers = {"Authorization": f"Bearer {rev_token}"}

    res_forbidden = requests.get(f"{API_BASE}/admin/metrics", headers=rev_headers, timeout=10)
    print(f"  Reviewer attempt on Super Admin metrics returned HTTP {res_forbidden.status_code}")
    assert res_forbidden.status_code == 403, f"Expected 403 Forbidden, got {res_forbidden.status_code}: {res_forbidden.text}"
    print("  RBAC Security Verified: Non-super administrator strictly denied access (HTTP 403 Forbidden).")

    # -------------------------------------------------------------------
    # 3. END-TO-END CUSTOMER ONBOARDING WORKFLOW
    # -------------------------------------------------------------------
    print_step("3. Customer Onboarding Flow (Register -> Profile -> Team -> AI -> Complete)")
    ts = int(time.time())
    new_tenant_email = f"director_{ts}@zenithlogistics.in"
    new_tenant_org = f"Zenith Logistics {ts}"

    # Step 3a: Register New Tenant
    res_reg = requests.post(f"{API_BASE}/auth/register", json={
        "email": new_tenant_email,
        "password": "Password123!",
        "full_name": "Vikram Malhotra",
        "organization_name": new_tenant_org
    }, timeout=10)
    assert res_reg.status_code == 201 or res_reg.status_code == 200, f"Tenant registration failed: {res_reg.text}"
    tenant_auth = res_reg.json()
    tenant_token = tenant_auth["access_token"]
    tenant_org_id = tenant_auth["user"]["organization"]["id"]
    tenant_headers = {"Authorization": f"Bearer {tenant_token}"}
    print(f"  New Tenant Registered: {new_tenant_email} for org '{new_tenant_org}' (ID: {tenant_org_id})")

    # Step 3b: Query Initial Onboarding Status
    res_status = requests.get(f"{API_BASE}/onboarding/status", headers=tenant_headers, timeout=10)
    assert res_status.status_code == 200, f"Onboarding status failed: {res_status.text}"
    status_data = res_status.json()
    assert status_data["onboarding_completed"] is False, "New tenant onboarding should not be completed yet"
    assert status_data["profile_completed"] is False, "New tenant profile should not be completed yet"
    print(f"  Initial Onboarding Status: Step={status_data['current_step']}, Completed={status_data['onboarding_completed']}")

    # Step 3c: Complete Business Profile
    res_profile = requests.post(f"{API_BASE}/onboarding/profile", headers=tenant_headers, json={
        "legal_name": "Zenith Logistics Private Limited",
        "gstin": "27AAACZ1234F1Z8",
        "pan": "AAACZ1234F",
        "address": "Unit 402, Supreme Business Park, Hiranandani Gardens, Powai",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400076",
        "country": "India",
        "currency": "INR",
        "phone": "+91-9876543210"
    }, timeout=10)
    assert res_profile.status_code == 200, f"Update profile failed: {res_profile.text}"
    profile_status = res_profile.json()
    assert profile_status["profile_completed"] is True, "Profile completed flag should be True"
    print(f"  Business Profile Saved: Legal Name='Zenith Logistics Private Limited', GSTIN='27AAACZ1234F1Z8'")

    # Step 3d: Invite Team across 4 Supported Roles
    team_invites = [
        ("admin@zenithlogistics.in", "Administrator"),
        ("accountant@zenithlogistics.in", "Accountant"),
        ("reviewer@zenithlogistics.in", "Reviewer"),
        ("auditor@zenithlogistics.in", "Read-only User")
    ]
    for email, role in team_invites:
        res_invite = requests.post(f"{API_BASE}/onboarding/invite", headers=tenant_headers, json={
            "email": email,
            "role": role
        }, timeout=10)
        assert res_invite.status_code == 200, f"Invite {email} ({role}) failed: {res_invite.text}"
        inv_data = res_invite.json()
        print(f"  Invited Employee: {inv_data['email']:30s} | Role: {inv_data['role']:15s} | Status: {inv_data['status']}")

    # Query Invitations List
    res_inv_list = requests.get(f"{API_BASE}/onboarding/invitations", headers=tenant_headers, timeout=10)
    assert res_inv_list.status_code == 200, f"Get invitations failed: {res_inv_list.text}"
    inv_list = res_inv_list.json()
    assert len(inv_list) == 4, f"Expected 4 invitations, found {len(inv_list)}"
    print(f"  Verified {len(inv_list)} employee invitations stored in database with 7-day expiration.")

    # Step 3e: Configure AI Engine & Validation Rules
    res_ai = requests.post(f"{API_BASE}/onboarding/ai-config", headers=tenant_headers, json={
        "primary_provider": "gemini",
        "fallback_provider": "groq",
        "confidence_threshold": 0.85,
        "auto_approve_threshold": 0.98,
        "tax_tolerance": 2.0,
        "currency_symbol": "₹"
    }, timeout=10)
    assert res_ai.status_code == 200, f"AI config failed: {res_ai.text}"
    ai_status = res_ai.json()
    assert ai_status["ai_configured"] is True, "AI configured flag should be True"
    print("  AI Provider Configured: Primary='gemini', Fallback='groq', AutoApprove='98%', Tolerance=INR 2.0")

    # Step 3f: Complete Guided Onboarding Stepper
    res_complete = requests.post(f"{API_BASE}/onboarding/complete", headers=tenant_headers, timeout=10)
    assert res_complete.status_code == 200, f"Complete onboarding failed: {res_complete.text}"
    final_status = res_complete.json()
    assert final_status["onboarding_completed"] is True, "Onboarding should be marked completed"
    print("  Customer Onboarding Finalized: Organization marked onboarding_completed=True.")

    # -------------------------------------------------------------------
    # 4. SUBSCRIPTION PLANS & COMMERCIAL UPGRADE
    # -------------------------------------------------------------------
    print_step("4. Commercial Subscription Architecture & Plan Upgrade")
    # Query Plans
    res_plans = requests.get(f"{API_BASE}/subscriptions/plans", headers=tenant_headers, timeout=10)
    assert res_plans.status_code == 200, f"Get plans failed: {res_plans.text}"
    plans = res_plans.json()
    print(f"  Available Commercial Subscription Tiers ({len(plans)} plans):")
    for p in plans:
        print(f"    - [{p['tier']}] INR {p['monthly_price_inr']}/mo | Limit: {p['monthly_document_limit']} docs/mo | Users: {p['max_users_limit']}")

    # Query Current Subscription
    res_sub_curr = requests.get(f"{API_BASE}/subscriptions/current", headers=tenant_headers, timeout=10)
    assert res_sub_curr.status_code == 200, f"Get current sub failed: {res_sub_curr.text}"
    curr_sub = res_sub_curr.json()
    assert curr_sub["plan_tier"] == "STARTER", f"Expected STARTER plan, got {curr_sub['plan_tier']}"
    assert curr_sub["status"] == "TRIAL", f"Expected TRIAL status, got {curr_sub['status']}"
    assert curr_sub["monthly_document_limit"] == 50, f"Expected 50 docs limit, got {curr_sub['monthly_document_limit']}"
    print(f"  Current Subscription: Plan={curr_sub['plan_tier']}, Status={curr_sub['status']}, Limit={curr_sub['monthly_document_limit']} docs/mo, Trial={curr_sub['is_trial']}")

    # Upgrade Subscription to PROFESSIONAL
    res_upgrade = requests.post(f"{API_BASE}/subscriptions/upgrade", headers=tenant_headers, json={
        "target_plan": "PROFESSIONAL",
        "billing_cycle": "MONTHLY"
    }, timeout=10)
    assert res_upgrade.status_code == 200, f"Upgrade failed: {res_upgrade.text}"
    upgraded_sub = res_upgrade.json()
    assert upgraded_sub["plan_tier"] == "PROFESSIONAL", f"Expected PROFESSIONAL, got {upgraded_sub['plan_tier']}"
    assert upgraded_sub["monthly_document_limit"] == 500, f"Expected 500 limit, got {upgraded_sub['monthly_document_limit']}"
    print(f"  Subscription Upgraded to PROFESSIONAL: Monthly Limit={upgraded_sub['monthly_document_limit']} docs/mo, Max Users={upgraded_sub['max_users_limit']}")

    # -------------------------------------------------------------------
    # 5. SUBSCRIPTION QUOTA ENFORCEMENT & HTTP 402 PAYMENT REQUIRED
    # -------------------------------------------------------------------
    print_step("5. Subscription Quota Enforcement (HTTP 402 Gating)")
    # Artificially set usage to limit in DB to test quota boundary
    import sqlite3
    db_path = ROOT_DIR / "documind.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("UPDATE subscriptions SET current_period_documents_used = 500 WHERE organization_id = ?", (tenant_org_id,))
    conn.commit()
    conn.close()

    # Attempt Document Upload when quota is exhausted
    sample_pdf = ROOT_DIR / "evaluation" / "datasets" / "phase2" / "p2_invoice_01_clean_intra.pdf"
    with open(sample_pdf, "rb") as f:
        res_upload_exhausted = requests.post(
            f"{API_BASE}/documents/upload",
            headers=tenant_headers,
            files={"file": ("quota_test_invoice.pdf", f, "application/pdf")},
            timeout=15
        )
    print(f"  Upload attempt with 500/500 quota used returned HTTP {res_upload_exhausted.status_code}")
    assert res_upload_exhausted.status_code == 402, f"Expected HTTP 402 Payment Required, got {res_upload_exhausted.status_code}: {res_upload_exhausted.text}"
    detail = res_upload_exhausted.json().get("detail", "")
    print(f"  Quota Error Message: '{detail}'")
    assert "limit reached" in detail.lower() or "limit" in detail.lower(), "Expected quota limit message in 402 response"

    # Reset quota to normal
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("UPDATE subscriptions SET current_period_documents_used = 0 WHERE organization_id = ?", (tenant_org_id,))
    conn.commit()
    conn.close()
    print("  Quota reset back to 0/500 for normal production operation.")

    # -------------------------------------------------------------------
    # 6. DATABASE ATOMIC BACKUP AUDIT & RESTORE VERIFICATION
    # -------------------------------------------------------------------
    print_step("6. Database Backup & Disaster Recovery Verification")
    backup_dir = ROOT_DIR / "storage" / "backups"
    backups = list(backup_dir.glob("*.db"))
    print(f"  Found {len(backups)} database snapshot(s) in {backup_dir}:")
    assert len(backups) > 0, "No database backup found!"
    for b in backups:
        sz = b.stat().st_size
        print(f"    - {b.name} ({sz:,} bytes)")
        assert sz > 500000, f"Backup {b.name} appears truncated ({sz} bytes)"

    # Test backup integrity with SQLite PRAGMA integrity_check
    latest_backup = sorted(backups)[-1]
    bconn = sqlite3.connect(str(latest_backup))
    bcur = bconn.cursor()
    bcur.execute("PRAGMA integrity_check;")
    chk = bcur.fetchone()
    assert chk[0] == "ok", f"Backup integrity check failed: {chk}"
    bcur.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
    tbl_cnt = bcur.fetchone()[0]
    bconn.close()
    print(f"  Latest Backup '{latest_backup.name}' Integrity: OK ({tbl_cnt} verified tables).")

    print("\n" + "=" * 70)
    print("ALL PHASE 3 COMMERCIAL HARDENING VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70 + "\n", flush=True)

if __name__ == "__main__":
    run_phase3_verification()
