#!/usr/bin/env python3
"""
Test script for comment monitoring system
Tests the complete flow: polling → triage → response
"""
import os
import sys
import asyncio
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

print("=" * 70)
print("🧪 Comment Monitoring System Test")
print("=" * 70)

# Test 1: Check monitored posts
print("\n📋 Test 1: Check Monitored Posts")
print("─" * 70)

result = supabase.table("monitored_posts") \
    .select("*, social_accounts(username, platform)") \
    .eq("monitoring_enabled", True) \
    .execute()

posts = result.data or []
print(f"✅ Found {len(posts)} monitored posts")

if len(posts) == 0:
    print("\n⚠️  No posts are being monitored!")
    print("   You need to:")
    print("   1. Sync Instagram posts via /api/monitoring/sync")
    print("   2. Or manually enable monitoring on posts")
    sys.exit(0)

for i, post in enumerate(posts[:5], 1):
    print(f"\n  Post #{i}:")
    print(f"    Platform: {post['platform']}")
    print(f"    Caption: {post.get('caption', 'N/A')[:50]}...")
    print(f"    Platform Post ID: {post.get('platform_post_id')}")
    print(f"    Last check: {post.get('last_check_at', 'Never')}")
    print(f"    Next check: {post.get('next_check_at', 'Not scheduled')}")
    print(f"    Monitoring ends: {post.get('monitoring_ends_at', 'N/A')}")

# Test 2: Check comments
print("\n\n📋 Test 2: Check Comments")
print("─" * 70)

comments_result = supabase.table("comments") \
    .select("*, monitored_posts(caption, platform)") \
    .limit(10) \
    .execute()

comments = comments_result.data or []
print(f"✅ Found {len(comments)} comments in database")

if len(comments) > 0:
    print("\nRecent comments:")
    for i, comment in enumerate(comments[:5], 1):
        print(f"\n  Comment #{i}:")
        print(f"    Author: {comment.get('author_name', 'Unknown')}")
        print(f"    Text: {comment.get('text', '')[:60]}...")
        print(f"    Triage: {comment.get('triage', 'Not processed yet')}")
        print(f"    Posted: {comment.get('created_at')}")
        if comment.get('parent_id'):
            print(f"    ↳ Reply to: {comment['parent_id']}")
        if comment.get('replied_at'):
            print(f"    ✅ Replied at: {comment['replied_at']}")

# Test 3: Test Instagram connector
print("\n\n📋 Test 3: Test Instagram API Connection")
print("─" * 70)

try:
    # Get first monitored post with credentials
    first_post = posts[0] if posts else None

    if first_post:
        # Get social account
        account_result = supabase.table("social_accounts") \
            .select("*") \
            .eq("id", first_post["social_account_id"]) \
            .single() \
            .execute()

        account = account_result.data

        if account:
            print(f"Testing with account: @{account.get('username')}")
            print(f"Account ID: {account.get('account_id')}")
            print(f"Has token: {bool(account.get('access_token'))}")

            # Try to fetch comments
            from app.services.instagram_connector import InstagramConnector

            access_token = account.get("access_token")
            page_id = account.get("account_id")
            platform_post_id = first_post.get("platform_post_id")

            if access_token and page_id and platform_post_id:
                connector = InstagramConnector(access_token, page_id)

                print(f"\n🔄 Fetching comments for post {platform_post_id}...")

                new_comments, next_cursor = asyncio.run(
                    connector.list_new_comments(platform_post_id)
                )

                print(f"✅ Found {len(new_comments)} comments from Instagram API")

                if len(new_comments) > 0:
                    print("\nSample comments:")
                    for i, comment in enumerate(new_comments[:3], 1):
                        print(f"\n  Comment #{i}:")
                        print(f"    Author: {comment.get('author_name')}")
                        print(f"    Text: {comment.get('text', '')[:60]}...")
                        print(f"    Has parent_id: {bool(comment.get('parent_id'))}")
                        print(f"    Like count: {comment.get('like_count', 0)}")
            else:
                print("⚠️  Missing credentials to test API")

except Exception as e:
    print(f"❌ Error testing Instagram connector: {e}")

# Test 4: Check Celery workers
print("\n\n📋 Test 4: Celery Worker Status")
print("─" * 70)

try:
    from app.workers.celery_app import celery

    # Inspect active workers
    inspect = celery.control.inspect()

    print("Checking for active Celery workers...")
    active = inspect.active()

    if active:
        print(f"✅ Found {len(active)} active workers")
        for worker_name, tasks in active.items():
            print(f"\n  Worker: {worker_name}")
            print(f"  Active tasks: {len(tasks)}")
    else:
        print("⚠️  No active Celery workers found")
        print("   Start workers with:")
        print("   celery -A app.workers.celery_app worker --beat --loglevel=info -Q comments")

except Exception as e:
    print(f"⚠️  Could not connect to Celery: {e}")

# Summary
print("\n\n" + "=" * 70)
print("📊 Summary")
print("=" * 70)
print(f"""
Monitored Posts:     {len(posts)}
Total Comments:      {len(comments)}
Unprocessed:         {len([c for c in comments if not c.get('triage')])}
Responded:           {len([c for c in comments if c.get('replied_at')])}
Escalated:           {len([c for c in comments if c.get('triage') == 'escalate'])}

Next steps:
1. Ensure Celery workers are running (see above)
2. Test force polling: POST /api/debug/comments/force-poll
3. Monitor logs: celery worker output will show polling activity
4. Check comments appear in UI: /dashboard/activity/comments
""")
print("=" * 70)
