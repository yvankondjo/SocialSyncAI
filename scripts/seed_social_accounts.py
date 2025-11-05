#!/usr/bin/env python3
"""
SocialSync AI - Social Accounts Seeding Script

Creates test social media accounts for development and testing.
This script creates fake Instagram and WhatsApp accounts with test tokens.

Usage:
    python scripts/seed_social_accounts.py

Environment Variables Required:
    SUPABASE_URL - Your Supabase project URL
    SUPABASE_SERVICE_ROLE_KEY - Your Supabase service role key

Author: SocialSync AI Team
License: AGPL v3.0
"""

import os
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from supabase import create_client, Client

# Test social accounts configuration
TEST_SOCIAL_ACCOUNTS = [
    {
        "platform": "instagram",
        "username": "demo_instagram",
        "display_name": "Demo Instagram Account",
        "access_token": "fake_instagram_token_for_testing_only_12345",
        "platform_user_id": "demo_instagram_user_12345",
        "is_test_account": True,
        "metadata": {
            "is_test_account": True,
            "description": "Test account for development - NOT connected to real Instagram API"
        }
    },
    {
        "platform": "whatsapp",
        "username": "+1234567890",
        "display_name": "Demo WhatsApp Business",
        "access_token": "fake_whatsapp_token_for_testing_only_67890",
        "platform_user_id": "demo_whatsapp_business_67890",
        "phone_number": "+1234567890",
        "is_test_account": True,
        "metadata": {
            "is_test_account": True,
            "description": "Test account for development - NOT connected to real WhatsApp API",
            "phone_number": "+1234567890"
        }
    }
]

def print_header():
    """Print the script header."""
    print("=" * 60)
    print("  SOCIALSYNC AI - SEED SOCIAL ACCOUNTS (Open-Source)")
    print("=" * 60)
    print()

def print_footer():
    """Print the script footer."""
    print()
    print("=" * 60)
    print("  Seeding completed successfully!")
    print("  Use these accounts for testing the platform.")
    print("=" * 60)

def validate_environment() -> bool:
    """Validate required environment variables."""
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY"
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print()
        print("Please set these variables and try again:")
        print("export SUPABASE_URL='https://your-project.supabase.co'")
        print("export SUPABASE_SERVICE_ROLE_KEY='your-service-role-key'")
        return False

    return True

def create_supabase_client() -> Client:
    """Create and return a Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    try:
        return create_client(url, key)
    except Exception as e:
        print(f"❌ Error creating Supabase client: {e}")
        sys.exit(1)

def find_user_by_email(supabase: Client, email: str) -> Optional[str]:
    """Find user by email and return user ID."""
    try:
        response = supabase.auth.admin.list_users()
        users = response.get('users', [])

        for user in users:
            if user.get('email') == email:
                return user.get('id')

        return None
    except Exception as e:
        print(f"❌ Error finding user {email}: {e}")
        return None

def get_user_email() -> str:
    """Get user email from input or use default."""
    print("📧 User email for social accounts (default: demo@socialsync.ai): ", end="")
    email = input().strip()

    if not email:
        email = "demo@socialsync.ai"

    return email

def create_social_account(supabase: Client, user_id: str, account_data: Dict[str, Any]) -> bool:
    """Create a social account for the user."""
    try:
        # Prepare account data
        data = {
            "user_id": user_id,
            "platform": account_data["platform"],
            "username": account_data["username"],
            "display_name": account_data["display_name"],
            "access_token": account_data["access_token"],
            "platform_user_id": account_data["platform_user_id"],
            "is_test_account": account_data.get("is_test_account", False),
            "metadata": account_data.get("metadata", {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Add platform-specific fields
        if account_data["platform"] == "whatsapp":
            data["phone_number"] = account_data.get("phone_number")

        response = supabase.table('social_accounts').insert(data).execute()

        if response.data:
            return True
        else:
            print(f"⚠️ Warning: Account creation returned empty for {account_data['platform']}")
            return False

    except Exception as e:
        print(f"❌ Error creating {account_data['platform']} account: {e}")
        return False

def seed_social_accounts():
    """Main seeding function."""
    print_header()

    # Validate environment
    if not validate_environment():
        sys.exit(1)

    # Create Supabase client
    supabase = create_supabase_client()

    # Get user email
    user_email = get_user_email()

    print(f"🔍 Finding user: {user_email}")

    # Find user
    user_id = find_user_by_email(supabase, user_email)
    if not user_id:
        print(f"❌ Error: User {user_email} not found")
        print("Please create the user first using seed_users.py")
        sys.exit(1)

    print(f"✅ User found (ID: {user_id})")
    print()
    print("Creating test social accounts...")
    print()

    created_accounts = []

    for account_data in TEST_SOCIAL_ACCOUNTS:
        platform = account_data["platform"]
        username = account_data["username"]

        print(f"📱 Creating {platform.upper()} account...")

        # Create account
        success = create_social_account(supabase, user_id, account_data)
        if success:
            print(f"   ✅ {platform.title()} account created (ID: {account_data['platform_user_id']})")
            created_accounts.append(account_data)
        else:
            print(f"   ❌ Failed to create {platform} account")

        print()

    if created_accounts:
        print("📱 Accounts created:")
        print()
        for account in created_accounts:
            platform = account["platform"]
            username = account["username"]
            print(f"  • {platform.upper()}: {username}")
        print()
        print("⚠️  WARNING: These are TEST accounts with fake tokens!")
        print("   They will NOT work with real social media APIs.")
        print("   For production use, connect real accounts via the dashboard.")

    print_footer()

if __name__ == "__main__":
    try:
        seed_social_accounts()
    except KeyboardInterrupt:
        print("\n⚠️ Seeding interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
