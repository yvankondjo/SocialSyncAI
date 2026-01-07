#!/usr/bin/env python3
"""
Script to subscribe all existing Instagram accounts to webhooks.

This script should be run once to fix accounts that were created before
the webhook subscription was implemented in the OAuth callback.

Usage:
    python scripts/subscribe_instagram_webhooks.py

Environment variables required:
    - SUPABASE_URL
    - SUPABASE_SERVICE_ROLE_KEY
    - META_GRAPH_VERSION (optional, defaults to v24.0)
"""

import os
import sys
import asyncio
import httpx
from dotenv import load_dotenv

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
META_GRAPH_VERSION = os.getenv('META_GRAPH_VERSION', 'v24.0')


async def subscribe_instagram_webhooks(access_token: str, ig_user_id: str) -> dict:
    """Subscribe an Instagram account to webhooks."""
    url = f'https://graph.instagram.com/{META_GRAPH_VERSION}/{ig_user_id}/subscribed_apps'
    params = {'subscribed_fields': 'messages,comments'}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                params=params,
                headers={'Authorization': f'Bearer {access_token}'}
            )
            response.raise_for_status()
            return {'success': True, 'data': response.json()}
        except httpx.HTTPStatusError as e:
            return {'success': False, 'error': e.response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}


async def get_instagram_accounts():
    """Fetch all Instagram accounts from the database."""
    from supabase import create_client
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")
        sys.exit(1)
    
    db = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    
    result = db.table('social_accounts').select('*').eq('platform', 'instagram').execute()
    return result.data


async def main():
    print("🔍 Fetching existing Instagram accounts...")
    accounts = await get_instagram_accounts()
    
    if not accounts:
        print("ℹ️ No Instagram accounts found in the database.")
        return
    
    print(f"📋 Found {len(accounts)} Instagram account(s)")
    
    success_count = 0
    error_count = 0
    
    for account in accounts:
        account_id = account.get('account_id')
        access_token = account.get('access_token')
        username = account.get('username', 'Unknown')
        user_id = account.get('user_id')
        
        if not account_id or not access_token:
            print(f"  ⚠️ Skipping account {username}: missing account_id or access_token")
            error_count += 1
            continue
        
        print(f"  📡 Subscribing {username} (ID: {account_id}, User: {user_id})...")
        
        result = await subscribe_instagram_webhooks(access_token, account_id)
        
        if result['success']:
            print(f"     ✅ Success: {result['data']}")
            success_count += 1
        else:
            print(f"     ❌ Failed: {result['error']}")
            error_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {error_count}")
    print(f"   📦 Total: {len(accounts)}")


if __name__ == '__main__':
    asyncio.run(main())
