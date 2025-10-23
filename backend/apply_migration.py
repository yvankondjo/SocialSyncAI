#!/usr/bin/env python3
"""
Direct PostgreSQL migration runner for Supabase
Executes SQL migrations using direct database connection
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
project_ref = SUPABASE_URL.replace("https://", "").split(".")[0] if SUPABASE_URL else ""

# Construct direct PostgreSQL connection URL
# Format: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
DB_PASSWORD = "SocialSyncAI@YVANK"  # From commented SUPABASE_DB_URL
DB_URL = f"postgresql://postgres:{DB_PASSWORD}@db.{project_ref}.supabase.co:5432/postgres"

print("=" * 70)
print("🔧 Supabase Migration - Apply to Database")
print("=" * 70)

migration_file = Path("/workspace/migrations/20251019_create_monitored_posts.sql")

if not migration_file.exists():
    print(f"❌ Migration file not found: {migration_file}")
    sys.exit(1)

print(f"\n📄 Migration file: {migration_file.name}")
print(f"🎯 Target database: {project_ref}.supabase.co")

sql_content = migration_file.read_text()
print(f"📝 SQL statements: {len([s for s in sql_content.split(';') if s.strip()])} statements")

print("\n" + "=" * 70)
print("OPTION 1: Apply via Supabase Dashboard (Recommended)")
print("=" * 70)
print(f"\n1. Go to: https://supabase.com/dashboard/project/{project_ref}/editor")
print("2. Click on 'SQL Editor' in the left sidebar")
print("3. Click 'New Query'")
print("4. Copy and paste the SQL below:")
print("\n" + "─" * 70)
print(sql_content)
print("─" * 70)
print("\n5. Click 'Run' (or press Ctrl+Enter)")
print("\n✅ The migration will create:")
print("   - Table: monitored_posts (with RLS policies)")
print("   - Table: monitoring_rules (with RLS policies)")
print("   - Column: comments.monitored_post_id")
print("   - Indexes and triggers")

print("\n" + "=" * 70)
print("OPTION 2: Apply via psql command line")
print("=" * 70)
print("\nRun this command in your terminal:\n")
print(f'psql "{DB_URL}" -f {migration_file}')

print("\n" + "=" * 70)
print("OPTION 3: Apply via Python script with psycopg2")
print("=" * 70)
print("\nInstall psycopg2 and run:\n")
print("pip install psycopg2-binary")
print("python3 << 'EOF'")
print(f"""import psycopg2
conn = psycopg2.connect("{DB_URL}")
cursor = conn.cursor()
with open("{migration_file}", "r") as f:
    cursor.execute(f.read())
conn.commit()
cursor.close()
conn.close()
print("✅ Migration applied successfully!")
EOF
""")

print("\n💡 After applying, restart your backend to clear Supabase cache:")
print("   - Stop the backend (Ctrl+C)")
print("   - Start it again: python3 -m uvicorn app.main:app --reload")

print("\n" + "=" * 70)
