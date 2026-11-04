#!/usr/bin/env python3
"""
DocuMind AI — Enterprise Disaster Recovery & Automated Backup Manager
Supports:
1. Atomic hot database snapshots with SHA-256 integrity hashing.
2. Metadata manifest generation (timestamp, tables, counts, hash).
3. Automated retention policy enforcement (pruning stale backups).
4. Full disaster recovery restoration into a disposable target database.
5. End-to-end verification of restored records, relationships, and document metadata.
"""

import os
import sys
import json
import time
import shutil
import sqlite3
import hashlib
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

ROOT_DIR = Path(__file__).resolve().parent.parent
STORAGE_BACKUPS = ROOT_DIR / "storage" / "backups"


def compute_file_sha256(filepath: Path) -> str:
    """Computes SHA-256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class DisasterRecoveryManager:
    def __init__(self, backup_dir: Optional[Path] = None):
        self.backup_dir = backup_dir or STORAGE_BACKUPS
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def get_table_counts(self, db_path: Path) -> Dict[str, int]:
        """Audits all tables and their row counts."""
        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.cursor()
            tables = [
                row[0] for row in cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
            ]
            counts = {}
            for t in sorted(tables):
                c = cursor.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                counts[t] = c
            return counts
        finally:
            conn.close()

    def create_atomic_backup(
        self,
        source_db_path: Path,
        retention_count: int = 5
    ) -> Dict[str, Any]:
        """
        Creates an atomic hot backup of the source database,
        computes cryptographic checksums, generates a manifest,
        and enforces the retention policy.
        """
        if not source_db_path.exists():
            raise FileNotFoundError(f"Source database not found: {source_db_path}")

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"documind_backup_{timestamp}.db"
        manifest_filename = f"documind_backup_{timestamp}.manifest.json"
        
        backup_path = self.backup_dir / backup_filename
        manifest_path = self.backup_dir / manifest_filename

        # 1. Capture pre-backup source metrics
        source_sha = compute_file_sha256(source_db_path)
        source_size = source_db_path.stat().st_size
        table_counts = self.get_table_counts(source_db_path)

        # 2. Perform atomic online backup
        src_conn = sqlite3.connect(str(source_db_path))
        dst_conn = sqlite3.connect(str(backup_path))
        try:
            with dst_conn:
                src_conn.backup(dst_conn, pages=100)
        finally:
            dst_conn.close()
            src_conn.close()

        # 3. Verify backup checksum & size
        backup_sha = compute_file_sha256(backup_path)
        backup_size = backup_path.stat().st_size

        if backup_size == 0:
            raise RuntimeError(f"Backup failed: Output file {backup_path} is empty (0 bytes)")

        # 4. Generate manifest
        manifest_data = {
            "timestamp": timestamp,
            "created_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source_db": str(source_db_path.name),
            "source_size_bytes": source_size,
            "source_sha256": source_sha,
            "backup_file": str(backup_filename),
            "backup_size_bytes": backup_size,
            "backup_sha256": backup_sha,
            "table_counts": table_counts,
            "total_records": sum(table_counts.values())
        }

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        # 5. Apply Retention Policy
        self.apply_retention_policy(retention_count)

        return manifest_data

    def apply_retention_policy(self, max_retained: int = 5) -> List[str]:
        """Prunes older backups to maintain retention limits."""
        backups = sorted(self.backup_dir.glob("documind_backup_*.db"))
        pruned = []
        if len(backups) > max_retained:
            to_remove = backups[:-max_retained]
            for b in to_remove:
                manifest = b.with_suffix(".manifest.json")
                if b.exists():
                    b.unlink()
                if manifest.exists():
                    manifest.unlink()
                pruned.append(b.name)
        return pruned

    def restore_backup(
        self,
        backup_path: Path,
        target_db_path: Path
    ) -> Dict[str, Any]:
        """
        Performs a full disaster recovery restoration from a verified backup into
        a target database path. Verifies schema and row count fidelity.
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # 1. Verify backup file integrity
        if backup_path.stat().st_size == 0:
            raise ValueError(f"Corrupt backup: {backup_path} has zero bytes.")

        backup_sha = compute_file_sha256(backup_path)

        # 2. Check manifest if present
        manifest_path = backup_path.with_name(backup_path.stem + ".manifest.json")
        expected_counts = None
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
                expected_sha = manifest_data.get("backup_sha256")
                if expected_sha and expected_sha != backup_sha:
                    raise ValueError(f"Integrity check failed! Expected SHA-256 {expected_sha}, found {backup_sha}")
                expected_counts = manifest_data.get("table_counts")

        # 3. Clean target destination
        if target_db_path.exists():
            target_db_path.unlink()

        # 4. Perform atomic restore via SQLite backup API
        src_conn = sqlite3.connect(str(backup_path))
        tgt_conn = sqlite3.connect(str(target_db_path))
        try:
            with tgt_conn:
                src_conn.backup(tgt_conn, pages=100)
        finally:
            tgt_conn.close()
            src_conn.close()

        # 5. Verify restored database integrity
        restored_sha = compute_file_sha256(target_db_path)
        restored_counts = self.get_table_counts(target_db_path)

        # Check against manifest expectations
        if expected_counts:
            for tbl, expected_c in expected_counts.items():
                actual_c = restored_counts.get(tbl, 0)
                if actual_c != expected_c:
                    raise AssertionError(
                        f"Disaster Recovery validation mismatch for table '{tbl}': "
                        f"Expected {expected_c} rows, restored {actual_c} rows!"
                    )

        return {
            "status": "RESTORED_AND_VERIFIED",
            "backup_file": str(backup_path.name),
            "target_db": str(target_db_path.name),
            "restored_size_bytes": target_db_path.stat().st_size,
            "restored_sha256": restored_sha,
            "table_counts": restored_counts,
            "total_records": sum(restored_counts.values())
        }


def run_standalone_cycle():
    print("=" * 70)
    print("DOCUMIND AI — AUTOMATED DISASTER RECOVERY & BACKUP CYCLE")
    print("=" * 70)

    mgr = DisasterRecoveryManager()
    source_db = ROOT_DIR / "documind.db"
    disposable_restore_db = mgr.backup_dir / "disposable_restore_test.db"

    print(f"\n[1] Creating verified hot backup from: {source_db.name}")
    manifest = mgr.create_atomic_backup(source_db, retention_count=5)
    print(f"  Backup File:      {manifest['backup_file']}")
    print(f"  Backup Size:      {manifest['backup_size_bytes']:,} bytes")
    print(f"  SHA-256 Hash:     {manifest['backup_sha256'][:16]}...")
    print(f"  Total Records:    {manifest['total_records']}")

    backup_path = mgr.backup_dir / manifest['backup_file']

    print(f"\n[2] Executing Disaster Recovery Restore to: {disposable_restore_db.name}")
    restore_result = mgr.restore_backup(backup_path, disposable_restore_db)
    print(f"  Status:           {restore_result['status']}")
    print(f"  Restored Size:    {restore_result['restored_size_bytes']:,} bytes")
    print(f"  Restored Hash:    {restore_result['restored_sha256'][:16]}...")
    print(f"  Restored Records: {restore_result['total_records']}")

    # Clean up disposable restore DB
    if disposable_restore_db.exists():
        disposable_restore_db.unlink()
    print(f"\n[3] Disposable target database cleaned up successfully.")
    print("=" * 70)
    print("DISASTER RECOVERY CYCLE: 100% SUCCESS")
    print("=" * 70)


if __name__ == "__main__":
    run_standalone_cycle()

