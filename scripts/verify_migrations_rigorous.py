"""
Rigorously verify Alembic migrations:
1. Fresh database migration from base -> c706 -> d417 -> cf29 (upgrade head)
2. Downgrade from head -> d417 -> c706 -> base
3. Re-upgrade to head
4. Disposable copy of documind.db migration & data integrity check (ensures zero data loss)
5. Model vs Schema consistency check
"""
import os
import shutil
import sqlite3
import sys
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(BACKEND_DIR))

from app.models.all_models import Base

def test_fresh_migration_lifecycle():
    print("\n--- 1. Testing Fresh Database Migration Lifecycle ---")
    temp_db_path = REPO_ROOT / "temp_fresh_migration.db"
    if temp_db_path.exists():
        temp_db_path.unlink()

    sqlite_url = f"sqlite:///{temp_db_path.as_posix()}"
    alembic_ini_path = BACKEND_DIR / "alembic.ini"

    cfg = Config(str(alembic_ini_path))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", sqlite_url)

    # 1. Upgrade to head
    print("Executing 'alembic upgrade head' on fresh DB...")
    command.upgrade(cfg, "head")

    engine = create_engine(sqlite_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Fresh DB upgrade succeeded! Created {len(tables)} tables: {sorted(tables)}")
    assert "alembic_version" in tables
    assert "organizations" in tables
    assert "data_rights_requests" in tables
    assert "subscriptions" in tables
    assert "organization_invitations" in tables

    # Check version
    with engine.connect() as conn:
        ver = conn.exec_driver_sql("SELECT version_num FROM alembic_version").scalar()
        print(f"Current migration head: {ver}")
        assert ver == "cf29860092de"

    # 2. Downgrade to d417279d3854
    print("Downgrading to d417279d3854...")
    command.downgrade(cfg, "d417279d3854")
    with engine.connect() as conn:
        ver = conn.exec_driver_sql("SELECT version_num FROM alembic_version").scalar()
        assert ver == "d417279d3854"
    tables = inspect(engine).get_table_names()
    assert "data_rights_requests" not in tables
    assert "subscriptions" in tables
    print("Downgrade to d417279d3854 verified.")

    # 3. Downgrade to c706f8d0d5b0
    print("Downgrading to c706f8d0d5b0...")
    command.downgrade(cfg, "c706f8d0d5b0")
    with engine.connect() as conn:
        ver = conn.exec_driver_sql("SELECT version_num FROM alembic_version").scalar()
        assert ver == "c706f8d0d5b0"
    tables = inspect(engine).get_table_names()
    assert "subscriptions" not in tables
    assert "organization_invitations" not in tables
    assert "organizations" in tables
    print("Downgrade to c706f8d0d5b0 verified.")

    # 4. Downgrade to base
    print("Downgrading to base...")
    command.downgrade(cfg, "base")
    tables = [t for t in inspect(engine).get_table_names() if t != "alembic_version"]
    assert len(tables) == 0, f"Expected 0 tables after downgrade to base, got {tables}"
    print("Downgrade to base verified (all domain tables dropped).")

    # 5. Re-upgrade to head
    print("Re-upgrading to head...")
    command.upgrade(cfg, "head")
    with engine.connect() as conn:
        ver = conn.exec_driver_sql("SELECT version_num FROM alembic_version").scalar()
        assert ver == "cf29860092de"
    tables = inspect(engine).get_table_names()
    print(f"Re-upgrade verified: {len(tables)} tables restored.")

    engine.dispose()
    if temp_db_path.exists():
        temp_db_path.unlink()
    print("Fresh migration lifecycle: PASSED 100%")

def test_disposable_documind_copy_migration():
    print("\n--- 2. Testing Existing DB Migration on Disposable Copy ---")
    orig_db = REPO_ROOT / "documind.db"
    assert orig_db.exists(), "Original documind.db not found!"

    disposable_db = REPO_ROOT / "temp_disposable_documind.db"
    if disposable_db.exists():
        disposable_db.unlink()
    shutil.copyfile(orig_db, disposable_db)

    conn_raw = sqlite3.connect(disposable_db)
    cursor = conn_raw.cursor()

    # Read user and document counts
    user_count_before = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    org_count_before = cursor.execute("SELECT COUNT(*) FROM organizations").fetchone()[0]
    doc_count_before = cursor.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    conn_raw.close()

    print(f"Disposable DB initial counts: Users={user_count_before}, Orgs={org_count_before}, Docs={doc_count_before}")

    sqlite_url = f"sqlite:///{disposable_db.as_posix()}"
    alembic_ini_path = BACKEND_DIR / "alembic.ini"
    cfg = Config(str(alembic_ini_path))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", sqlite_url)

    print("Running 'alembic upgrade head' on disposable DB...")
    command.upgrade(cfg, "head")

    conn_raw = sqlite3.connect(disposable_db)
    cursor = conn_raw.cursor()
    user_count_after = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    org_count_after = cursor.execute("SELECT COUNT(*) FROM organizations").fetchone()[0]
    doc_count_after = cursor.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    version_after = cursor.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    conn_raw.close()

    print(f"Disposable DB after migration: Version={version_after}, Users={user_count_after}, Orgs={org_count_after}, Docs={doc_count_after}")
    assert user_count_after == user_count_before, "User count changed!"
    assert org_count_after == org_count_before, "Organization count changed!"
    assert doc_count_after == doc_count_before, "Document count changed!"
    assert version_after == "cf29860092de", "Did not reach head!"

    if disposable_db.exists():
        disposable_db.unlink()
    print("Disposable DB migration and data preservation: PASSED 100%")

def test_model_vs_schema_consistency():
    print("\n--- 3. Testing Model vs Schema Consistency ---")
    temp_db_path = REPO_ROOT / "temp_schema_check.db"
    if temp_db_path.exists():
        temp_db_path.unlink()

    sqlite_url = f"sqlite:///{temp_db_path.as_posix()}"
    alembic_ini_path = BACKEND_DIR / "alembic.ini"
    cfg = Config(str(alembic_ini_path))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", sqlite_url)

    command.upgrade(cfg, "head")
    engine = create_engine(sqlite_url)
    inspector = inspect(engine)
    migrated_tables = set(inspector.get_table_names()) - {"alembic_version"}

    model_tables = set(Base.metadata.tables.keys())

    print(f"Migrated tables count: {len(migrated_tables)}")
    print(f"Model tables count:    {len(model_tables)}")

    diff_migrated_not_model = migrated_tables - model_tables
    diff_model_not_migrated = model_tables - migrated_tables

    print(f"Tables in migration but not in models: {diff_migrated_not_model}")
    print(f"Tables in models but not in migration: {diff_model_not_migrated}")

    assert len(diff_model_not_migrated) == 0, f"Unmigrated model tables: {diff_model_not_migrated}"
    print("Model and migration schema consistency: PASSED 100%")

    engine.dispose()
    if temp_db_path.exists():
        temp_db_path.unlink()

if __name__ == "__main__":
    test_fresh_migration_lifecycle()
    test_disposable_documind_copy_migration()
    test_model_vs_schema_consistency()
    print("\n=======================================================")
    print("ALL MIGRATION VERIFICATION CHECKS COMPLETED SUCCESSFULLY")
    print("=======================================================")

