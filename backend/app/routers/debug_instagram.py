"""
Debug router for Instagram API
Temporary endpoints to troubleshoot Instagram integration
"""
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.db.session import get_authenticated_db
from app.core.security import get_current_user_id
import httpx
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debug/instagram", tags=["Debug Instagram"])


@router.get("/account-info")
async def debug_account_info(
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Debug endpoint: Get raw Instagram account info from Graph API
    Returns the exact response from Instagram including media_count
    """
    try:
        # Get Instagram account
        result = db.table("social_accounts") \
            .select("*") \
            .eq("user_id", current_user_id) \
            .eq("platform", "instagram") \
            .eq("is_active", True) \
            .limit(1) \
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="No Instagram account found")

        account = result.data[0]
        access_token = account.get("access_token")
        account_id = account.get("account_id")

        if not access_token or not account_id:
            raise HTTPException(
                status_code=400,
                detail="Instagram account missing credentials"
            )

        # Call Instagram Graph API
        async with httpx.AsyncClient() as client:
            url = f"https://graph.instagram.com/v23.0/{account_id}"
            params = {
                "fields": "id,username,account_type,media_count,followers_count,follows_count",
                "access_token": access_token
            }

            response = await client.get(url, params=params)
            response.raise_for_status()
            api_data = response.json()

        return {
            "success": True,
            "database_info": {
                "account_id": account.get("account_id"),
                "username": account.get("username"),
                "is_active": account.get("is_active"),
                "token_expires_at": account.get("token_expires_at"),
            },
            "instagram_api_response": api_data,
            "diagnosis": {
                "account_type_compatible": api_data.get("account_type") in ["BUSINESS", "CREATOR"],
                "has_media": api_data.get("media_count", 0) > 0,
                "media_count": api_data.get("media_count", 0),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DEBUG] Error getting Instagram account info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/media-list")
async def debug_media_list(
    limit: int = 10,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Debug endpoint: Get raw media list from Instagram Graph API
    Returns the exact response including all posts
    """
    try:
        # Get Instagram account
        result = db.table("social_accounts") \
            .select("*") \
            .eq("user_id", current_user_id) \
            .eq("platform", "instagram") \
            .eq("is_active", True) \
            .limit(1) \
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="No Instagram account found")

        account = result.data[0]
        access_token = account.get("access_token")
        account_id = account.get("account_id")

        if not access_token or not account_id:
            raise HTTPException(
                status_code=400,
                detail="Instagram account missing credentials"
            )

        # Call Instagram Graph API
        async with httpx.AsyncClient() as client:
            url = f"https://graph.instagram.com/v23.0/{account_id}/media"
            params = {
                "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,comments_count,like_count,username",
                "limit": limit,
                "access_token": access_token
            }

            response = await client.get(url, params=params)
            response.raise_for_status()
            api_data = response.json()

        media_list = api_data.get("data", [])

        return {
            "success": True,
            "endpoint_called": f"/v23.0/{account_id}/media",
            "media_count": len(media_list),
            "instagram_api_response": api_data,
            "diagnosis": {
                "has_posts": len(media_list) > 0,
                "posts_found": len(media_list),
                "has_pagination": "paging" in api_data,
            },
            "posts_preview": [
                {
                    "id": m.get("id"),
                    "type": m.get("media_type"),
                    "caption": m.get("caption", "")[:100],
                    "timestamp": m.get("timestamp"),
                    "comments": m.get("comments_count", 0),
                    "likes": m.get("like_count", 0),
                }
                for m in media_list[:5]
            ] if media_list else []
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DEBUG] Error getting Instagram media list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-permissions")
async def debug_test_permissions(
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Debug endpoint: Test Instagram token permissions
    Tries different API calls to see what works
    """
    try:
        # Get Instagram account
        result = db.table("social_accounts") \
            .select("*") \
            .eq("user_id", current_user_id) \
            .eq("platform", "instagram") \
            .eq("is_active", True) \
            .limit(1) \
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="No Instagram account found")

        account = result.data[0]
        access_token = account.get("access_token")
        account_id = account.get("account_id")

        if not access_token or not account_id:
            raise HTTPException(
                status_code=400,
                detail="Instagram account missing credentials"
            )

        tests = {}

        async with httpx.AsyncClient() as client:
            # Test 1: Basic profile info
            try:
                url = f"https://graph.instagram.com/v23.0/{account_id}"
                params = {
                    "fields": "id,username",
                    "access_token": access_token
                }
                response = await client.get(url, params=params)
                tests["basic_profile"] = {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                }
            except Exception as e:
                tests["basic_profile"] = {"success": False, "error": str(e)}

            # Test 2: Media endpoint
            try:
                url = f"https://graph.instagram.com/v23.0/{account_id}/media"
                params = {
                    "fields": "id",
                    "limit": 1,
                    "access_token": access_token
                }
                response = await client.get(url, params=params)
                tests["media_access"] = {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                }
            except Exception as e:
                tests["media_access"] = {"success": False, "error": str(e)}

            # Test 3: /me endpoint
            try:
                url = "https://graph.instagram.com/v23.0/me"
                params = {
                    "fields": "id,username",
                    "access_token": access_token
                }
                response = await client.get(url, params=params)
                tests["me_endpoint"] = {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                }
            except Exception as e:
                tests["me_endpoint"] = {"success": False, "error": str(e)}

        return {
            "success": True,
            "account_id": account_id,
            "token_valid": all(test.get("success", False) for test in tests.values()),
            "tests": tests,
            "diagnosis": {
                "all_tests_passed": all(test.get("success", False) for test in tests.values()),
                "failed_tests": [name for name, test in tests.items() if not test.get("success", False)],
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DEBUG] Error testing permissions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
