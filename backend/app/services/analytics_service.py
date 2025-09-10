from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import asyncio
import logging
from supabase import Client
import httpx

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.platform_handlers = {
            'twitter': self._fetch_twitter_stats,
            'instagram': self._fetch_instagram_stats,
            'facebook': self._fetch_facebook_stats,
            'linkedin': self._fetch_linkedin_stats,
            'youtube': self._fetch_youtube_stats,
            'tiktok': self._fetch_tiktok_stats,
            'whatsapp': self._fetch_whatsapp_stats,
        }
    
    async def sync_content_analytics(self, db: Client, content_id: str) -> dict:
        """Synchronise les analytics d'un contenu spécifique."""
        try:
            content_res = db.table("content").select("*, social_accounts(*)").eq("id", content_id).single().execute()
            if not content_res.data:
                return {"error": "Content not found"}
            
            content = content_res.data
            social_account = content.get("social_accounts")

            if not social_account:
                return {"error": "Social account not found for this content"}

            handler = self.platform_handlers.get(social_account["platform"])
            if not handler:
                return {"error": f"Platform {social_account['platform']} not supported"}

            stats = await handler(social_account, content)
            
            # Mettre à jour ou insérer les analytics
            db.table("analytics").upsert({
                "content_id": content_id,
                "platform": social_account["platform"],
                **self._format_stats(stats)
            }).execute()
            
            # Ajouter à l'historique
            db.table("analytics_history").insert({
                "content_id": content_id,
                "platform": social_account["platform"],
                "user_id": social_account["user_id"],
                **self._format_stats(stats)
            }).execute()

            return {"success": True, "stats": stats}
        except Exception as e:
            logger.error(f"Error syncing analytics for content {content_id}: {e}")
            return {"error": str(e)}
    
    async def sync_user_analytics(self, db: Client, user_id: str, days: int = 7) -> Dict:
        """Synchronise tous les analytics d'un utilisateur"""
        try:
            # Récupérer tous les contenus publiés récemment
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            result = db.table("content").select("*").eq("social_account_id", user_id).eq("status", "published").gte("published_at", cutoff_date).execute()  # TODO: vérifier si user_id devrait être social_account_id
            contents = result.data
            
            results = []
            for content in contents:
                result = await self.sync_content_analytics(db, str(content["id"]))
                results.append({"content_id": str(content["id"]), "result": result})
            
            return {"success": True, "synced_count": len(results), "results": results}
            
        except Exception as e:
            logger.error(f"Error syncing user analytics {user_id}: {e}")
            return {"error": str(e)}
    
    def _format_stats(self, stats: dict) -> dict:
        """Helper to format stats for DB insertion."""
        return {
            "likes": stats.get('likes', 0),
            "shares": stats.get('shares', 0),
            "comments": stats.get('comments', 0),
            "impressions": stats.get('impressions', 0),
            "reach": stats.get('reach', 0),
            "clicks": stats.get('clicks', 0),
            "conversions": stats.get('conversions', 0),
            "engagement_rate": stats.get('engagement_rate', 0),
            "raw_metrics": stats.get('raw_metrics', {}),
            "recorded_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def _fetch_twitter_stats(self, social_account: Dict, content: Dict) -> Dict:
        """Récupère les stats Twitter via API"""
        if not social_account.get("access_token"):
            return {"error": "No access token for Twitter account"}
        
        try:
            # Exemple avec l'API Twitter v2
            headers = {"Authorization": f"Bearer {social_account['access_token']}"}
            
            # Supposons que content.account_id contient l'ID du tweet
            tweet_id = content.get("account_id")  # À adapter selon votre structure
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.twitter.com/2/tweets/{tweet_id}",
                    headers=headers,
                    params={
                        "tweet.fields": "public_metrics,created_at",
                        "expansions": "author_id"
                    }
                )
                
                if response.status_code != 200:
                    return {"error": f"Twitter API error: {response.status_code}"}
                
                data = response.json()
                metrics = data.get('data', {}).get('public_metrics', {})
                
                return {
                    "likes": metrics.get('like_count', 0),
                    "shares": metrics.get('retweet_count', 0),
                    "comments": metrics.get('reply_count', 0),
                    "impressions": metrics.get('impression_count', 0),
                    "engagement_rate": self._calculate_engagement_rate(metrics),
                    "raw_metrics": metrics
                }
                
        except Exception as e:
            logger.error(f"Error fetching Twitter stats: {e}")
            return {"error": str(e)}
    
    async def _fetch_instagram_stats(self, social_account: Dict, content: Dict) -> Dict:
        """Récupère les stats Instagram via API"""
        # Implémentation similaire pour Instagram Graph API
        return {"likes": 0, "shares": 0, "comments": 0}
    
    async def _fetch_facebook_stats(self, social_account: Dict, content: Dict) -> Dict:
        """Récupère les stats Facebook via API"""
        # Implémentation similaire pour Facebook Graph API
        return {"likes": 0, "shares": 0, "comments": 0}
    
    async def _fetch_linkedin_stats(self, social_account: Dict, content: Dict) -> Dict:
        """Récupère les stats LinkedIn via API"""
        # Implémentation similaire pour LinkedIn API
        return {"likes": 0, "shares": 0, "comments": 0}
    
    async def _fetch_youtube_stats(self, social_account: Dict, content: Dict) -> Dict:
        """Récupère les stats YouTube via API"""
        # Implémentation similaire pour YouTube Data API
        return {"likes": 0, "shares": 0, "comments": 0}
    
    async def _fetch_tiktok_stats(self, social_account: Dict, content: Dict) -> Dict:
        """Récupère les stats TikTok via API"""
        # Implémentation similaire pour TikTok API
        return {"likes": 0, "shares": 0, "comments": 0}

    async def _fetch_whatsapp_stats(self, social_account: Dict, content: Dict) -> Dict:
        """Récupère les stats WhatsApp via API"""
        # Implémentation similaire pour WhatsApp Business API
        # (ex: messages envoyés, lus, etc.)
        return {"messages_sent": 0, "messages_delivered": 0, "messages_read": 0}
    
    def _calculate_engagement_rate(self, metrics: Dict) -> float:
        """Calcule le taux d'engagement"""
        total_engagements = (
            metrics.get('like_count', 0) +
            metrics.get('retweet_count', 0) +
            metrics.get('reply_count', 0)
        )
        impressions = metrics.get('impression_count', 0)
        
        if impressions > 0:
            return round((total_engagements / impressions) * 100, 2)
        return 0.0

# Instance globale
analytics_service = AnalyticsService() 