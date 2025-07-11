from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Content, SocialAccount, Analytics, AnalyticsHistory
from app.database import get_db
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
        }
    
    async def sync_content_analytics(self, db: AsyncSession, content_id: str) -> Dict:
        """Synchronise les analytics d'un contenu spécifique"""
        try:
            # Récupérer le contenu et son compte social
            result = await db.execute(
                select(Content, SocialAccount)
                .join(SocialAccount, Content.social_account_id == SocialAccount.id)
                .where(Content.id == content_id)
            )
            content, social_account = result.first()
            
            if not content or not social_account:
                return {"error": "Content or social account not found"}
            
            # Récupérer les stats depuis l'API de la plateforme
            handler = self.platform_handlers.get(social_account.platform)
            if not handler:
                return {"error": f"Platform {social_account.platform} not supported"}
            
            stats = await handler(social_account, content)
            
            # Mettre à jour la table analytics (snapshot actuel)
            await self._update_analytics(db, content_id, social_account.platform, stats)
            
            # Ajouter à l'historique
            await self._add_to_history(db, content_id, social_account.platform, social_account.user_id, stats)
            
            await db.commit()
            return {"success": True, "stats": stats}
            
        except Exception as e:
            logger.error(f"Error syncing analytics for content {content_id}: {e}")
            await db.rollback()
            return {"error": str(e)}
    
    async def sync_user_analytics(self, db: AsyncSession, user_id: str, days: int = 7) -> Dict:
        """Synchronise tous les analytics d'un utilisateur"""
        try:
            # Récupérer tous les contenus publiés récemment
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            result = await db.execute(
                select(Content)
                .join(SocialAccount, Content.social_account_id == SocialAccount.id)
                .where(
                    SocialAccount.user_id == user_id,
                    Content.status == 'published',
                    Content.published_at >= cutoff_date
                )
            )
            contents = result.scalars().all()
            
            results = []
            for content in contents:
                result = await self.sync_content_analytics(db, str(content.id))
                results.append({"content_id": str(content.id), "result": result})
            
            return {"success": True, "synced_count": len(results), "results": results}
            
        except Exception as e:
            logger.error(f"Error syncing user analytics {user_id}: {e}")
            return {"error": str(e)}
    
    async def _update_analytics(self, db: AsyncSession, content_id: str, platform: str, stats: Dict):
        """Met à jour ou crée une entrée dans analytics"""
        result = await db.execute(
            select(Analytics).where(
                Analytics.content_id == content_id,
                Analytics.platform == platform
            )
        )
        analytics = result.scalar_one_or_none()
        
        if analytics:
            # Mettre à jour
            analytics.likes = stats.get('likes', 0)
            analytics.shares = stats.get('shares', 0)
            analytics.comments = stats.get('comments', 0)
            analytics.impressions = stats.get('impressions', 0)
            analytics.reach = stats.get('reach', 0)
            analytics.clicks = stats.get('clicks', 0)
            analytics.conversions = stats.get('conversions', 0)
            analytics.engagement_rate = stats.get('engagement_rate', 0)
            analytics.raw_metrics = stats.get('raw_metrics', {})
            analytics.recorded_at = datetime.utcnow()
        else:
            # Créer nouveau
            analytics = Analytics(
                content_id=content_id,
                platform=platform,
                likes=stats.get('likes', 0),
                shares=stats.get('shares', 0),
                comments=stats.get('comments', 0),
                impressions=stats.get('impressions', 0),
                reach=stats.get('reach', 0),
                clicks=stats.get('clicks', 0),
                conversions=stats.get('conversions', 0),
                engagement_rate=stats.get('engagement_rate', 0),
                raw_metrics=stats.get('raw_metrics', {}),
                recorded_at=datetime.utcnow()
            )
            db.add(analytics)
    
    async def _add_to_history(self, db: AsyncSession, content_id: str, platform: str, user_id: str, stats: Dict):
        """Ajoute une entrée dans analytics_history"""
        history = AnalyticsHistory(
            content_id=content_id,
            platform=platform,
            user_id=user_id,
            likes=stats.get('likes', 0),
            shares=stats.get('shares', 0),
            comments=stats.get('comments', 0),
            impressions=stats.get('impressions', 0),
            reach=stats.get('reach', 0),
            clicks=stats.get('clicks', 0),
            conversions=stats.get('conversions', 0),
            engagement_rate=stats.get('engagement_rate', 0),
            raw_metrics=stats.get('raw_metrics', {}),
            recorded_at=datetime.utcnow()
        )
        db.add(history)
    
    async def _fetch_twitter_stats(self, social_account: SocialAccount, content: Content) -> Dict:
        """Récupère les stats Twitter via API"""
        if not social_account.access_token:
            return {"error": "No access token for Twitter account"}
        
        try:
            # Exemple avec l'API Twitter v2
            headers = {"Authorization": f"Bearer {social_account.access_token}"}
            
            # Supposons que content.account_id contient l'ID du tweet
            tweet_id = content.account_id  # À adapter selon votre structure
            
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
    
    async def _fetch_instagram_stats(self, social_account: SocialAccount, content: Content) -> Dict:
        """Récupère les stats Instagram via API"""
        # Implémentation similaire pour Instagram Graph API
        return {"likes": 0, "shares": 0, "comments": 0}
    
    async def _fetch_facebook_stats(self, social_account: SocialAccount, content: Content) -> Dict:
        """Récupère les stats Facebook via API"""
        # Implémentation similaire pour Facebook Graph API
        return {"likes": 0, "shares": 0, "comments": 0}
    
    async def _fetch_linkedin_stats(self, social_account: SocialAccount, content: Content) -> Dict:
        """Récupère les stats LinkedIn via API"""
        # Implémentation similaire pour LinkedIn API
        return {"likes": 0, "shares": 0, "comments": 0}
    
    async def _fetch_youtube_stats(self, social_account: SocialAccount, content: Content) -> Dict:
        """Récupère les stats YouTube via API"""
        # Implémentation similaire pour YouTube Data API
        return {"likes": 0, "shares": 0, "comments": 0}
    
    async def _fetch_tiktok_stats(self, social_account: SocialAccount, content: Content) -> Dict:
        """Récupère les stats TikTok via API"""
        # Implémentation similaire pour TikTok API
        return {"likes": 0, "shares": 0, "comments": 0}
    
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