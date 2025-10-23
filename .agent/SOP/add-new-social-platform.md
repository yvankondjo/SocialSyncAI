# SOP: Adding a New Social Media Platform

**Time Estimate:** 4-6 hours
**Difficulty:** Intermediate
**Prerequisites:** Python, FastAPI, OAuth 2.0 knowledge

---

## Overview

This guide walks you through adding a new social media platform to the comment monitoring system. We'll use **Twitter/X** as an example.

---

## Checklist

- [ ] **Step 1:** Create platform API service
- [ ] **Step 2:** Create platform connector
- [ ] **Step 3:** Add OAuth integration
- [ ] **Step 4:** Update database migrations
- [ ] **Step 5:** Update worker polling logic
- [ ] **Step 6:** Add frontend UI components
- [ ] **Step 7:** Write tests
- [ ] **Step 8:** Update documentation

---

## Step 1: Create Platform API Service

### File: `backend/app/services/twitter_service.py`

```python
"""
Twitter/X API v2 Service
Handles authentication and API calls to Twitter
"""
import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class TwitterService:
    """Twitter API v2 client for comments and replies"""

    def __init__(self, bearer_token: str, user_id: str):
        self.bearer_token = bearer_token
        self.user_id = user_id
        self.base_url = "https://api.twitter.com/2"

    async def get_tweet_replies(
        self,
        tweet_id: str,
        max_results: int = 100,
        pagination_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get replies to a specific tweet

        API Reference:
        https://developer.twitter.com/en/docs/twitter-api/tweets/search/api-reference/get-tweets-search-recent
        """
        # Use search query to find replies
        query = f"conversation_id:{tweet_id}"

        url = f"{self.base_url}/tweets/search/recent"
        params = {
            'query': query,
            'max_results': max_results,
            'tweet.fields': 'author_id,created_at,conversation_id,in_reply_to_user_id,public_metrics',
            'user.fields': 'username,name,profile_image_url',
            'expansions': 'author_id'
        }

        if pagination_token:
            params['pagination_token'] = pagination_token

        headers = {
            'Authorization': f'Bearer {self.bearer_token}'
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()

    async def reply_to_tweet(
        self,
        tweet_id: str,
        reply_text: str
    ) -> Dict[str, Any]:
        """
        Reply to a tweet

        API Reference:
        https://developer.twitter.com/en/docs/twitter-api/tweets/manage-tweets/api-reference/post-tweets
        """
        url = f"{self.base_url}/tweets"
        payload = {
            'text': reply_text,
            'reply': {
                'in_reply_to_tweet_id': tweet_id
            }
        }

        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                logger.error(f"Failed to reply to tweet {tweet_id}: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }

    async def get_user_tweets(
        self,
        user_id: str,
        max_results: int = 10,
        pagination_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user's recent tweets

        API Reference:
        https://developer.twitter.com/en/docs/twitter-api/tweets/timelines/api-reference/get-users-id-tweets
        """
        url = f"{self.base_url}/users/{user_id}/tweets"
        params = {
            'max_results': max_results,
            'tweet.fields': 'created_at,public_metrics,attachments',
            'media.fields': 'url,preview_image_url',
            'expansions': 'attachments.media_keys'
        }

        if pagination_token:
            params['pagination_token'] = pagination_token

        headers = {
            'Authorization': f'Bearer {self.bearer_token}'
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
```

---

## Step 2: Create Platform Connector

### File: `backend/app/services/twitter_connector.py`

```python
"""
Twitter Connector - Implements unified comment interface
"""
from typing import List, Dict, Tuple, Optional, Any
from .twitter_service import TwitterService
from .base_connector import BasePlatformConnector
import logging

logger = logging.getLogger(__name__)


class TwitterConnector(BasePlatformConnector):
    """Twitter connector for comment monitoring"""

    def __init__(self, bearer_token: str, user_id: str):
        self.service = TwitterService(bearer_token, user_id)

    async def list_new_comments(
        self,
        post_id: str,
        since_cursor: Optional[str] = None
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        Fetch replies (comments) for a tweet

        Args:
            post_id: Tweet ID
            since_cursor: Pagination token

        Returns:
            (normalized_comments, next_cursor)
        """
        try:
            response = await self.service.get_tweet_replies(
                tweet_id=post_id,
                pagination_token=since_cursor
            )

            # Extract tweets (replies) and users
            tweets = response.get('data', [])
            users_dict = {}

            # Build user lookup dictionary
            includes = response.get('includes', {})
            users = includes.get('users', [])
            for user in users:
                users_dict[user['id']] = user

            # Normalize comments
            comments = []
            for tweet in tweets:
                author_id = tweet.get('author_id')
                author_data = users_dict.get(author_id, {})

                normalized = self.normalize_comment(tweet, author_data)
                comments.append(normalized)

            # Get next cursor
            meta = response.get('meta', {})
            next_token = meta.get('next_token')

            logger.info(f"[TwitterConnector] Fetched {len(comments)} replies for tweet {post_id}")

            return comments, next_token

        except Exception as e:
            logger.error(f"[TwitterConnector] Error fetching replies for {post_id}: {e}")
            return [], None

    async def reply_to_comment(
        self,
        comment_id: str,
        reply_text: str
    ) -> Dict[str, Any]:
        """
        Reply to a tweet (comment)

        Args:
            comment_id: Tweet ID to reply to
            reply_text: Reply content

        Returns:
            {"success": bool, "reply_id": str, "error": str}
        """
        try:
            result = await self.service.reply_to_tweet(comment_id, reply_text)

            if result.get('success'):
                tweet_data = result['data'].get('data', {})
                return {
                    "success": True,
                    "reply_id": tweet_data.get('id'),
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "reply_id": None,
                    "error": result.get('error', 'Unknown error')
                }

        except Exception as e:
            logger.error(f"[TwitterConnector] Error replying to {comment_id}: {e}")
            return {
                "success": False,
                "reply_id": None,
                "error": str(e)
            }

    def normalize_comment(
        self,
        raw_tweet: Dict,
        author_data: Dict
    ) -> Dict:
        """
        Normalize Twitter reply to unified comment format

        Args:
            raw_tweet: Raw tweet data from API
            author_data: Author/user data

        Returns:
            Unified comment dict
        """
        # Extract metrics
        metrics = raw_tweet.get('public_metrics', {})

        return {
            'id': raw_tweet['id'],
            'author_name': author_data.get('username', 'Unknown'),
            'author_id': raw_tweet.get('author_id'),
            'author_avatar_url': author_data.get('profile_image_url'),
            'text': raw_tweet.get('text', ''),
            'created_at': raw_tweet.get('created_at'),
            'parent_id': raw_tweet.get('in_reply_to_user_id'),  # Thread support
            'like_count': metrics.get('like_count', 0),
            'retweet_count': metrics.get('retweet_count', 0),  # Platform-specific
            'reply_count': metrics.get('reply_count', 0)  # Platform-specific
        }
```

---

## Step 3: Add OAuth Integration

### File: `backend/app/routers/oauth.py` (add to existing file)

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
import httpx
import os

TWITTER_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
TWITTER_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")
TWITTER_REDIRECT_URI = os.getenv("TWITTER_REDIRECT_URI", "http://localhost:3000/auth/twitter/callback")

router = APIRouter(prefix="/oauth/twitter", tags=["oauth"])


@router.get("/connect")
async def twitter_connect():
    """
    Initiate Twitter OAuth 2.0 flow

    Docs: https://developer.twitter.com/en/docs/authentication/oauth-2-0/authorization-code
    """
    auth_url = (
        f"https://twitter.com/i/oauth2/authorize?"
        f"response_type=code&"
        f"client_id={TWITTER_CLIENT_ID}&"
        f"redirect_uri={TWITTER_REDIRECT_URI}&"
        f"scope=tweet.read tweet.write users.read offline.access&"
        f"state=random_state_string&"
        f"code_challenge=challenge&"
        f"code_challenge_method=plain"
    )
    return RedirectResponse(auth_url)


@router.get("/callback")
async def twitter_callback(
    code: str,
    state: str,
    current_user = Depends(get_current_user),
    db: Supabase = Depends(get_db)
):
    """
    Handle Twitter OAuth callback

    1. Exchange code for access_token
    2. Get user info
    3. Save to social_accounts table
    """
    # Exchange authorization code for access token
    token_url = "https://api.twitter.com/2/oauth2/token"
    token_data = {
        'code': code,
        'grant_type': 'authorization_code',
        'client_id': TWITTER_CLIENT_ID,
        'redirect_uri': TWITTER_REDIRECT_URI,
        'code_verifier': 'challenge'
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data=token_data,
            auth=(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET)
        )

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token")

        tokens = response.json()
        access_token = tokens['access_token']
        refresh_token = tokens.get('refresh_token')

    # Get user profile
    user_url = "https://api.twitter.com/2/users/me"
    headers = {'Authorization': f'Bearer {access_token}'}

    async with httpx.AsyncClient() as client:
        response = await client.get(user_url, headers=headers)
        response.raise_for_status()
        user_data = response.json()['data']

    # Save to database
    social_account = {
        'user_id': current_user['id'],
        'platform': 'twitter',
        'account_id': user_data['id'],
        'username': user_data['username'],
        'access_token': access_token,
        'refresh_token': refresh_token,
        'is_active': True,
        'metadata': {
            'name': user_data.get('name'),
            'profile_image_url': user_data.get('profile_image_url')
        }
    }

    db.table('social_accounts').upsert(social_account).execute()

    return RedirectResponse(url="/dashboard/settings/accounts?success=twitter")
```

---

## Step 4: Update Database Migration

### File: `backend/supabase/migrations/20251020_add_twitter_support.sql`

```sql
-- Add Twitter platform to enum if using platform enum
-- Otherwise, the VARCHAR(50) field supports any platform

-- Add Twitter-specific metadata columns (optional)
ALTER TABLE monitored_posts
ADD COLUMN IF NOT EXISTS tweet_metrics JSONB;

COMMENT ON COLUMN monitored_posts.tweet_metrics IS
'Twitter-specific metrics: retweet_count, quote_count, impression_count';

-- Add Twitter comment metadata
ALTER TABLE comments
ADD COLUMN IF NOT EXISTS retweet_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS quote_count INTEGER DEFAULT 0;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Twitter platform support added successfully';
END $$;
```

---

## Step 5: Update Worker Polling Logic

### File: `backend/app/workers/comments.py` (modify existing)

```python
def _get_connector(post: Dict[str, Any]) -> Optional[BasePlatformConnector]:
    """Get platform connector for a post"""
    platform = post.get("platform")

    if platform == "instagram":
        # ... existing Instagram code
        return InstagramConnector(access_token, page_id)

    elif platform == "facebook":
        # ... existing Facebook code
        return FacebookConnector(access_token, page_id)

    elif platform == "twitter":
        social_accounts = post.get("social_accounts")
        if not social_accounts:
            logger.error(f"[POLL] No social_accounts data for Twitter post {post.get('id')}")
            return None

        bearer_token = social_accounts.get("access_token")
        user_id = social_accounts.get("account_id")

        if not bearer_token or not user_id:
            logger.error(
                f"[POLL] Missing credentials for Twitter post {post.get('id')}: "
                f"has_token={bool(bearer_token)}, has_user_id={bool(user_id)}"
            )
            return None

        return TwitterConnector(bearer_token, user_id)

    else:
        logger.warning(f"[POLL] Unsupported platform: {platform}")
        return None
```

---

## Step 6: Add Frontend UI Components

### File: `frontend/components/platforms/TwitterAccountCard.tsx`

```tsx
"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Twitter } from "lucide-react"

interface TwitterAccountCardProps {
  account: {
    id: string
    username: string
    metadata: {
      name: string
      profile_image_url: string
    }
  }
  onDisconnect: (id: string) => void
}

export function TwitterAccountCard({ account, onDisconnect }: TwitterAccountCardProps) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between p-4">
        <div className="flex items-center gap-3">
          <Twitter className="w-6 h-6 text-blue-400" />
          <img
            src={account.metadata.profile_image_url}
            alt={account.username}
            className="w-10 h-10 rounded-full"
          />
          <div>
            <p className="font-medium">{account.metadata.name}</p>
            <p className="text-sm text-muted-foreground">@{account.username}</p>
          </div>
        </div>
        <Button
          variant="destructive"
          size="sm"
          onClick={() => onDisconnect(account.id)}
        >
          Disconnect
        </Button>
      </CardContent>
    </Card>
  )
}
```

### File: `frontend/app/dashboard/settings/accounts/page.tsx` (add button)

```tsx
<Button onClick={() => window.location.href = '/api/oauth/twitter/connect'}>
  <Twitter className="w-4 h-4 mr-2" />
  Connect Twitter
</Button>
```

---

## Step 7: Write Tests

### File: `backend/test_twitter_integration.py`

```python
import asyncio
import pytest
from app.services.twitter_connector import TwitterConnector

@pytest.mark.asyncio
async def test_twitter_fetch_comments():
    """Test fetching replies from Twitter"""
    connector = TwitterConnector(
        bearer_token="YOUR_TEST_TOKEN",
        user_id="YOUR_TEST_USER_ID"
    )

    # Fetch comments for a test tweet
    comments, cursor = await connector.list_new_comments("1234567890123456789")

    assert isinstance(comments, list)
    assert cursor is None or isinstance(cursor, str)

    if comments:
        comment = comments[0]
        assert 'id' in comment
        assert 'author_name' in comment
        assert 'text' in comment


@pytest.mark.asyncio
async def test_twitter_reply():
    """Test replying to a tweet"""
    connector = TwitterConnector(
        bearer_token="YOUR_TEST_TOKEN",
        user_id="YOUR_TEST_USER_ID"
    )

    result = await connector.reply_to_comment(
        "1234567890123456789",
        "Test reply from automated system"
    )

    assert result['success'] is True
    assert 'reply_id' in result


if __name__ == "__main__":
    asyncio.run(test_twitter_fetch_comments())
    asyncio.run(test_twitter_reply())
```

---

## Step 8: Update Documentation

### Update: `.agent/System/comment-monitoring-unified-api.md`

Add Twitter to platform comparison table:

```markdown
| Platform   | Comments API | Reply API | Media Support | OAuth Scope |
|------------|--------------|-----------|---------------|-------------|
| Twitter    | ✅ API v2    | ✅        | ✅ Images+GIFs | `tweet.read`, `tweet.write` |
```

---

## Environment Variables

Add to `.env`:

```bash
# Twitter/X API Credentials
TWITTER_CLIENT_ID=your_client_id_here
TWITTER_CLIENT_SECRET=your_client_secret_here
TWITTER_REDIRECT_URI=http://localhost:3000/auth/twitter/callback
TWITTER_BEARER_TOKEN=your_bearer_token_here  # For app-only auth
```

---

## Testing Checklist

- [ ] OAuth flow connects successfully
- [ ] Access token is saved to `social_accounts` table
- [ ] Worker can fetch comments from Twitter
- [ ] Worker can reply to comments
- [ ] Comments appear in frontend UI
- [ ] AI processing works with Twitter comments
- [ ] Conversation detection works correctly
- [ ] Rate limits are handled gracefully

---

## Common Issues

### Issue 1: "403 Forbidden" on API calls

**Cause:** Missing OAuth scopes

**Solution:** Ensure your Twitter app has the following scopes:
- `tweet.read`
- `tweet.write`
- `users.read`
- `offline.access` (for refresh tokens)

### Issue 2: Rate limit exceeded

**Cause:** Twitter has strict rate limits (300 requests per 15 min window)

**Solution:** Implement rate limiting in worker:

```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=300, period=900)  # 300 calls per 15 min
async def fetch_with_rate_limit(url, headers):
    async with httpx.AsyncClient() as client:
        return await client.get(url, headers=headers)
```

### Issue 3: Pagination not working

**Cause:** Twitter uses `next_token` not `after` cursor

**Solution:** Check API response structure and extract correct pagination field.

---

## Platform-Specific Notes

### Twitter/X Specifics

1. **Thread Structure:**
   - Twitter uses `conversation_id` not `parent_id`
   - Need to search by conversation_id to get all replies

2. **Media Handling:**
   - Images are in `attachments.media_keys`
   - Need to expand media to get URLs
   - Videos require separate API call

3. **Rate Limits:**
   - User context: 300 requests / 15 min
   - App context: 450 requests / 15 min
   - Use app context when possible

---

## Deployment

1. **Update environment variables** in production
2. **Run database migration**
3. **Restart Celery workers** to load new connectors
4. **Test with real account** before public launch

---

## Support

For platform-specific API issues, refer to:
- **Twitter Docs:** https://developer.twitter.com/en/docs
- **Facebook Docs:** https://developers.facebook.com/docs
- **TikTok Docs:** https://developers.tiktok.com/doc

---

**Estimated Time:** 4-6 hours per platform
**Next Platforms:** Facebook, TikTok, LinkedIn
