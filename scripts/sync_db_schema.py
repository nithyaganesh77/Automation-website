import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / "documind.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get existing tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print(f"Existing tables ({len(tables)}):", tables)

# Check organizations columns
cursor.execute("PRAGMA table_info(organizations)")
org_cols = [r[1] for r in cursor.fetchall()]
print("Organizations columns:", org_cols)

new_org_columns = [
    ("legal_name", "VARCHAR(255)"),
    ("gstin", "VARCHAR(15)"),
    ("pan", "VARCHAR(10)"),
    ("address", "TEXT"),
    ("city", "VARCHAR(100)"),
    ("state", "VARCHAR(100)"),
    ("pincode", "VARCHAR(10)"),
    ("phone", "VARCHAR(20)"),
    ("onboarding_completed", "BOOLEAN DEFAULT 0 NOT NULL"),
    ("onboarding_step", "VARCHAR(50) DEFAULT 'PROFILE' NOT NULL")
]

for col_name, col_type in new_org_columns:
    if col_name not in org_cols:
        print(f"Adding column '{col_name}' to organizations...")
        cursor.execute(f"ALTER TABLE organizations ADD COLUMN {col_name} {col_type}")

# Check organization_settings columns
cursor.execute("PRAGMA table_info(organization_settings)")
settings_cols = [r[1] for r in cursor.fetchall()]
print("Organization settings columns:", settings_cols)

new_settings_columns = [
    ("primary_provider", "VARCHAR(50) DEFAULT 'gemini' NOT NULL"),
    ("fallback_provider", "VARCHAR(50) DEFAULT 'groq' NOT NULL"),
    ("gemini_api_key_masked", "VARCHAR(100)"),
    ("groq_api_key_masked", "VARCHAR(100)"),
    ("monthly_budget_usd", "FLOAT DEFAULT 100.0 NOT NULL")
]

for col_name, col_type in new_settings_columns:
    if col_name not in settings_cols:
        print(f"Adding column '{col_name}' to organization_settings...")
        cursor.execute(f"ALTER TABLE organization_settings ADD COLUMN {col_name} {col_type}")

# Check subscriptions table
cursor.execute("PRAGMA table_info(subscriptions)")
sub_cols = [r[1] for r in cursor.fetchall()]
print("Subscriptions columns:", sub_cols)

# Create default subscriptions for existing organizations if missing
cursor.execute("SELECT id FROM organizations")
org_ids = [r[0] for r in cursor.fetchall()]
for oid in org_ids:
    cursor.execute("SELECT id FROM subscriptions WHERE organization_id = ?", (oid,))
    if not cursor.fetchone():
        import uuid
        from datetime import datetime, timezone, timedelta
        sub_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        trial_end = now + timedelta(days=14)
        period_end = now + timedelta(days=30)
        cursor.execute("""
            INSERT INTO subscriptions (
                id, organization_id, plan_tier, status, billing_cycle,
                monthly_document_limit, max_users_limit, current_period_documents_used,
                price_amount, currency, trial_ends_at, current_period_start, current_period_end,
                created_at, updated_at
            ) VALUES (?, ?, 'STARTER', 'TRIAL', 'MONTHLY', 50, 3, 0, 0.0, 'INR', ?, ?, ?, ?, ?)
        """, (sub_id, oid, trial_end, now, period_end, now, now))
        print(f"Created default STARTER subscription for org {oid}")

conn.commit()
conn.close()
print("Database schema synchronization complete!")
