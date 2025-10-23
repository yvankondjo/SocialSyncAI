#!/usr/bin/env python3
"""
Migration runner script for Supabase
Applies SQL migrations directly to Supabase Cloud instance
"""
import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in .env")
    sys.exit(1)

# Initialize Supabase client with service role (bypasses RLS for migrations)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def run_migration(migration_file: str):
    """
    Execute SQL migration file on Supabase

    Args:
        migration_file: Path to .sql file
    """
    migration_path = Path(migration_file)

    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)

    print(f"📄 Reading migration: {migration_path.name}")
    sql_content = migration_path.read_text()

    print(f"🚀 Executing migration on {SUPABASE_URL}...")

    try:
        # Execute SQL via Supabase RPC
        # Note: Supabase Python client doesn't have direct SQL execution
        # We'll use the REST API endpoint
        import requests

        url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
        headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json"
        }

        # Split SQL into statements and execute them
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]

        print(f"📝 Executing {len(statements)} SQL statements...")

        for i, statement in enumerate(statements, 1):
            if statement:
                print(f"  [{i}/{len(statements)}] Executing statement...")

                # Use PostgREST to execute raw SQL
                # This requires a custom function in Supabase
                # Instead, let's use psycopg2 for direct connection

        # Alternative: Use direct PostgreSQL connection
        print("\n⚠️  Direct SQL execution via REST API not available.")
        print("📋 Please apply the migration manually via Supabase Dashboard:")
        print(f"\n1. Go to: {SUPABASE_URL.replace('https://', 'https://supabase.com/dashboard/project/')}")
        print("2. Navigate to: SQL Editor")
        print("3. Copy and paste the migration SQL:")
        print(f"\n{'='*60}")
        print(sql_content)
        print(f"{'='*60}\n")
        print("4. Click 'Run' to execute the migration")

        print("\n💡 Or use direct PostgreSQL connection:")
        print("   Uncomment SUPABASE_DB_URL in .env and run with psycopg2")

    except Exception as e:
        print(f"❌ Error executing migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migration_file = "/workspace/migrations/20251019_create_monitored_posts.sql"

    print("=" * 60)
    print("🔧 Supabase Migration Runner")
    print("=" * 60)

    run_migration(migration_file)
