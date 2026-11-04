import os
import sys
import json
import shutil
import sqlite3
import pytest
from pathlib import Path
from decimal import Decimal

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.disaster_recovery_manager import DisasterRecoveryManager, compute_file_sha256
from app.models.all_models import Organization, Document, Invoice, InvoiceLineItem
from tests.conftest import TestingSessionLocal


@pytest.fixture
def dr_temp_env(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Create disposable test database
    source_db = tmp_path / "disposable_source.db"
    conn = sqlite3.connect(str(source_db))
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE organizations (id TEXT PRIMARY KEY, name TEXT, slug TEXT)")
    cursor.execute("CREATE TABLE documents (id TEXT PRIMARY KEY, org_id TEXT, file_name TEXT, tokens INT)")
    cursor.execute("CREATE TABLE invoices (id TEXT PRIMARY KEY, doc_id TEXT, invoice_number TEXT, total NUMERIC)")

    cursor.execute("INSERT INTO organizations VALUES ('org-1', 'Alpha Corp', 'alpha-corp')")
    cursor.execute("INSERT INTO documents VALUES ('doc-1', 'org-1', 'tax_invoice.pdf', 0)")
    cursor.execute("INSERT INTO invoices VALUES ('inv-1', 'doc-1', 'INV-2026-001', 50000.00)")
    conn.commit()
    conn.close()

    mgr = DisasterRecoveryManager(backup_dir=backup_dir)
    return {
        "mgr": mgr,
        "backup_dir": backup_dir,
        "source_db": source_db,
        "tmp_path": tmp_path
    }


def test_atomic_backup_creation_and_manifest(dr_temp_env):
    mgr = dr_temp_env["mgr"]
    source_db = dr_temp_env["source_db"]

    manifest = mgr.create_atomic_backup(source_db, retention_count=3)
    assert manifest["source_db"] == "disposable_source.db"
    assert manifest["total_records"] == 3
    assert manifest["table_counts"]["organizations"] == 1
    assert manifest["table_counts"]["documents"] == 1
    assert manifest["table_counts"]["invoices"] == 1

    backup_path = mgr.backup_dir / manifest["backup_file"]
    assert backup_path.exists()
    assert backup_path.stat().st_size > 0
    assert manifest["backup_sha256"] == compute_file_sha256(backup_path)


def test_disaster_recovery_restore_cycle(dr_temp_env):
    mgr = dr_temp_env["mgr"]
    source_db = dr_temp_env["source_db"]
    target_restore_db = dr_temp_env["tmp_path"] / "disposable_target.db"

    # 1. Create backup
    manifest = mgr.create_atomic_backup(source_db)
    backup_file = mgr.backup_dir / manifest["backup_file"]

    # 2. Perform restore onto fresh target
    restore_meta = mgr.restore_backup(backup_file, target_restore_db)
    assert restore_meta["status"] == "RESTORED_AND_VERIFIED"
    assert restore_meta["total_records"] == 3
    assert target_restore_db.exists()

    # 3. Verify actual records and data fidelity
    conn = sqlite3.connect(str(target_restore_db))
    cursor = conn.cursor()
    org_name = cursor.execute("SELECT name FROM organizations WHERE id='org-1'").fetchone()[0]
    inv_num = cursor.execute("SELECT invoice_number FROM invoices WHERE id='inv-1'").fetchone()[0]
    conn.close()

    assert org_name == "Alpha Corp"
    assert inv_num == "INV-2026-001"


def test_corrupt_backup_detection_and_rejection(dr_temp_env):
    mgr = dr_temp_env["mgr"]
    source_db = dr_temp_env["source_db"]
    target_restore_db = dr_temp_env["tmp_path"] / "corrupt_target.db"

    manifest = mgr.create_atomic_backup(source_db)
    backup_file = mgr.backup_dir / manifest["backup_file"]

    # Tamper with backup file
    with open(backup_file, "ab") as f:
        f.write(b"CORRUPTED_BYTES")

    # Restoration should be rejected due to hash mismatch
    with pytest.raises(ValueError, match="Integrity check failed"):
        mgr.restore_backup(backup_file, target_restore_db)


def test_retention_policy_pruning(dr_temp_env):
    mgr = dr_temp_env["mgr"]
    source_db = dr_temp_env["source_db"]

    # Create 5 backups with retention set to 2
    for _ in range(5):
        mgr.create_atomic_backup(source_db, retention_count=2)
        # Sleep slightly so timestamps increment
        import time
        time.sleep(1.05)

    remaining_backups = list(mgr.backup_dir.glob("documind_backup_*.db"))
    assert len(remaining_backups) == 2
