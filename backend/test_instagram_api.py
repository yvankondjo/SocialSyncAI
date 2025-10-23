#!/usr/bin/env python3
"""
Test Instagram Graph API directly
"""
import os
import sys
import asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found")
    sys.exit(1)

# Initialize Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

async def test_instagram_api():
    print("=" * 70)
    print("🔍 Instagram Graph API Tester")
    print("=" * 70)

    # Get Instagram account
    result = supabase.table("social_accounts") \
        .select("*") \
        .eq("platform", "instagram") \
        .eq("is_active", True) \
        .limit(1) \
        .execute()

    if not result.data:
        print("\n❌ No active Instagram account found")
        sys.exit(1)

    account = result.data[0]
    access_token = account.get("access_token")
    account_id = account.get("account_id")

    print(f"\n✅ Using Instagram account:")
    print(f"   Username: {account.get('username')}")
    print(f"   Account ID: {account_id}")
    print(f"   Token expires: {account.get('token_expires_at')}")

    async with httpx.AsyncClient() as client:
        # Test 1: Get account info
        print("\n" + "─" * 70)
        print("📋 Test 1: Get Account Info")
        print("─" * 70)

        url = f"https://graph.instagram.com/v23.0/{account_id}"
        params = {
            "fields": "id,username,account_type,media_count",
            "access_token": access_token
        }

        print(f"GET {url}")
        print(f"Fields: {params['fields']}")

        try:
            response = await client.get(url, params=params)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("\n✅ Account Info:")
                for key, value in data.items():
                    print(f"   {key}: {value}")

                account_type = data.get("account_type")
                media_count = data.get("media_count", 0)

                if account_type not in ["BUSINESS", "CREATOR"]:
                    print(f"\n⚠️  WARNING: Account type is '{account_type}'")
                    print("   The Instagram Graph API only works with BUSINESS or CREATOR accounts!")
                    print("   Convert your account to Business in Instagram settings.")
                else:
                    print(f"\n✅ Account type is '{account_type}' (compatible)")

                print(f"\n📊 Media count reported by Instagram: {media_count}")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {e}")

        # Test 2: Get media list
        print("\n" + "─" * 70)
        print("📋 Test 2: Get Media List")
        print("─" * 70)

        url = f"https://graph.instagram.com/v23.0/{account_id}/media"
        params = {
            "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,comments_count,like_count",
            "limit": 10,
            "access_token": access_token
        }

        print(f"GET {url}")
        print(f"Limit: 10")

        try:
            response = await client.get(url, params=params)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                media_list = data.get("data", [])

                print(f"\n✅ Found {len(media_list)} media items")

                if len(media_list) == 0:
                    print("\n⚠️  No media found!")
                    print("\nPossible reasons:")
                    print("  1. The account has no published posts")
                    print("  2. The account is not a Business/Creator account")
                    print("  3. The access token doesn't have the right permissions")
                    print("  4. Recent posts haven't been indexed yet (wait 5-10 minutes)")
                else:
                    for i, media in enumerate(media_list, 1):
                        print(f"\n  Post #{i}:")
                        print(f"    ID: {media.get('id')}")
                        print(f"    Type: {media.get('media_type')}")
                        print(f"    Caption: {media.get('caption', 'N/A')[:50]}...")
                        print(f"    Timestamp: {media.get('timestamp')}")
                        print(f"    Comments: {media.get('comments_count', 0)}")
                        print(f"    Likes: {media.get('like_count', 0)}")
                        print(f"    URL: {media.get('permalink')}")
            else:
                print(f"❌ Error: {response.text}")

                if response.status_code == 400:
                    print("\n💡 This usually means:")
                    print("   - Account is not a Business/Creator account")
                    print("   - Token permissions are insufficient")
        except Exception as e:
            print(f"❌ Exception: {e}")

        # Test 3: Check token permissions
        print("\n" + "─" * 70)
        print("📋 Test 3: Check Token Permissions")
        print("─" * 70)

        url = "https://graph.instagram.com/v23.0/me"
        params = {
            "fields": "id,username",
            "access_token": access_token
        }

        try:
            response = await client.get(url, params=params)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Token is valid for user: {data.get('username')}")
            else:
                print(f"❌ Token validation failed: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {e}")

    print("\n" + "=" * 70)
    print("💡 Recommendations:")
    print("=" * 70)
    print("\n1. Ensure your Instagram account is converted to Business/Creator")
    print("   Settings → Account → Switch to Professional Account")
    print("\n2. If you just posted, wait 5-10 minutes for Instagram to index it")
    print("\n3. Check that your token has these permissions:")
    print("   - instagram_basic")
    print("   - instagram_manage_comments")
    print("   - instagram_manage_messages")
    print("\n4. Try posting an image or video (not just a story)")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_instagram_api())
