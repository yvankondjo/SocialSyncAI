#!/usr/bin/env python3
"""
Debug script to check Instagram account data
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment
env_path = Path(__file__).parent / "backend" / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found")
    sys.exit(1)

# Initialize Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

print("=" * 70)
print("🔍 Instagram Account Debugger")
print("=" * 70)

# Get all Instagram accounts
result = supabase.table("social_accounts") \
    .select("*") \
    .eq("platform", "instagram") \
    .execute()

if not result.data:
    print("\n❌ No Instagram accounts found in database")
    sys.exit(0)

print(f"\n✅ Found {len(result.data)} Instagram account(s)\n")

for i, account in enumerate(result.data, 1):
    print(f"Account #{i}:")
    print(f"  ID: {account.get('id')}")
    print(f"  User ID: {account.get('user_id')}")
    print(f"  Platform: {account.get('platform')}")
    print(f"  Is Active: {account.get('is_active')}")
    print(f"  Username: {account.get('username', 'N/A')}")

    # Check critical fields
    access_token = account.get('access_token')
    account_id = account.get('account_id')

    print(f"\n  ✓ Critical fields:")
    print(f"    access_token: {'✅ Present' if access_token else '❌ MISSING'}")
    if access_token:
        print(f"      Length: {len(access_token)} chars")
        print(f"      Preview: {access_token[:20]}...{access_token[-10:]}")

    print(f"    account_id: {'✅ Present' if account_id else '❌ MISSING'}")
    if account_id:
        print(f"      Value: {account_id}")

    # Check alternative field names
    print(f"\n  📋 All available fields:")
    for key in sorted(account.keys()):
        value = account[key]
        if key in ['access_token', 'refresh_token']:
            if value:
                print(f"    {key}: {value[:15]}...{value[-10:] if len(str(value)) > 25 else ''}")
            else:
                print(f"    {key}: None")
        elif isinstance(value, str) and len(value) > 50:
            print(f"    {key}: {value[:50]}...")
        else:
            print(f"    {key}: {value}")

    print("\n" + "─" * 70 + "\n")

print("\n💡 Expected fields for Instagram:")
print("  - access_token: Long-lived Instagram token")
print("  - account_id: Instagram Business Account ID (numeric)")
print("  - platform: 'instagram'")
print("  - is_active: True")

print("\n📝 If fields are missing, you need to reconnect your Instagram account.")
print("=" * 70)
