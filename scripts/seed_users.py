#!/usr/bin/env python3
"""
SocialSync AI - User Seeding Script

Creates test users with unlimited credits for development and testing.
This script creates demo accounts that can be used to explore the platform.

Usage:
    python scripts/seed_users.py

Environment Variables Required:
    SUPABASE_URL - Your Supabase project URL
    SUPABASE_SERVICE_ROLE_KEY - Your Supabase service role key

Author: SocialSync AI Team
License: AGPL v3.0
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from supabase import create_client, Client

# Test users configuration
TEST_USERS = [
    {
        "email": "demo@socialsync.ai",
        "password": "Demo123456!",
        "full_name": "Demo User",
        "username": "demo_user",
    },
    {
        "email": "test@socialsync.ai",
        "password": "Test123456!",
        "full_name": "Test User",
        "username": "test_user",
    },
    {
        "email": "admin@socialsync.ai",
        "password": "Admin123456!",
        "full_name": "Admin User",
        "username": "admin_user",
    },
]

UNLIMITED_CREDITS = 999999


def print_header():
    """Print the script header."""
    print("=" * 60)
    print("  SOCIALSYNC AI - SEED USERS (Open-Source)")
    print("=" * 60)
    print()


def print_footer():
    """Print the script footer."""
    print()
    print("=" * 60)
    print("  Seeding completed successfully!")
    print("  Use the credentials above to log into the platform.")
    print("=" * 60)


def validate_environment() -> bool:
    """Validate required environment variables."""
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]

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


def user_exists(supabase: Client, email: str) -> bool:
    """Check if user already exists."""
    try:
        response = supabase.auth.admin.list_users()
        users = response.get("users", [])

        for user in users:
            if user.get("email") == email:
                return True

        return False
    except Exception as e:
        print(f"⚠️ Warning: Could not check if user exists: {e}")
        return False


def create_user(supabase: Client, user_data: Dict[str, str]) -> str:
    """Create a user with Supabase Auth."""
    try:
        # Create user in auth.users
        response = supabase.auth.admin.create_user(
            {
                "email": user_data["email"],
                "password": user_data["password"],
                "email_confirm": True,  # Auto-confirm email
                "user_metadata": {
                    "full_name": user_data["full_name"],
                    "username": user_data["username"],
                },
            }
        )

        user = response.user
        if not user:
            raise Exception("Failed to create user")

        return user.id

    except Exception as e:
        print(f"❌ Error creating user {user_data['email']}: {e}")
        return None


def create_user_credits(supabase: Client, user_id: str, credits: int) -> bool:
    """Create unlimited credits for user."""
    try:
        # Insert into user_credits table
        data = {
            "user_id": user_id,
            "credits_remaining": credits,
            "plan_type": "unlimited",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        response = supabase.table("user_credits").insert(data).execute()

        if response.data:
            return True
        else:
            print(f"⚠️ Warning: Credits creation returned empty for user {user_id}")
            return False

    except Exception as e:
        print(f"❌ Error creating credits for user {user_id}: {e}")
        return False


def seed_users():
    """Main seeding function."""
    print_header()

    # Validate environment
    if not validate_environment():
        sys.exit(1)

    # Create Supabase client
    supabase = create_supabase_client()

    print("🔧 Starting user seeding process...")
    print()

    created_users = []

    for user_data in TEST_USERS:
        email = user_data["email"]
        password = user_data["password"]

        print(f"📧 Processing user: {email}")

        # Check if user exists
        if user_exists(supabase, email):
            print(f"   ⚠️ User {email} already exists - skipping")
            continue

        # Create user
        user_id = create_user(supabase, user_data)
        if not user_id:
            continue

        # Create credits
        credits_created = create_user_credits(supabase, user_id, UNLIMITED_CREDITS)
        if not credits_created:
            print(f"   ⚠️ User created but credits setup failed")
            continue

        print(f"   ✅ User created (ID: {user_id})")
        print(f"   ✅ Credits created ({UNLIMITED_CREDITS} unlimited)")

        created_users.append({"email": email, "password": password, "user_id": user_id})

        print()

    if created_users:
        print("📝 Login credentials:")
        print()
        for user in created_users:
            print(f"  • Email: {user['email']}")
            print(f"    Password: {user['password']}")
            print(f"    User ID: {user['user_id']}")
            print()

    print_footer()


if __name__ == "__main__":
    try:
        seed_users()
    except KeyboardInterrupt:
        print("\n⚠️ Seeding interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
