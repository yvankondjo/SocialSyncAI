import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database import get_db
from app.services.analytics_service import analytics_service
from app.models import User, SocialAccount
from sqlalchemy import select

logger = logging.getLogger(__name__)

class AnalyticsScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.setup_jobs()
    
    def setup_jobs(self):
        """Configure les tâches programmées"""
        
        # Sync analytics 3 fois par jour (8h, 14h, 20h)
        self.scheduler.add_job(
            self.sync_all_users_analytics,
            CronTrigger(hour="8,14,20", minute="0"),
            id="sync_analytics_regular",
            name="Sync Analytics - Regular",
            replace_existing=True
        )
        
        # Sync complète une fois par jour à 2h du matin
        self.scheduler.add_job(
            self.sync_all_users_analytics_full,
            CronTrigger(hour="2", minute="0"),
            id="sync_analytics_full",
            name="Sync Analytics - Full",
            replace_existing=True
        )
        
        # Nettoyage des anciennes données d'historique (1 fois par semaine)
        self.scheduler.add_job(
            self.cleanup_old_analytics,
            CronTrigger(day_of_week="sun", hour="3", minute="0"),
            id="cleanup_analytics",
            name="Cleanup Old Analytics",
            replace_existing=True
        )
    
    async def sync_all_users_analytics(self):
        """Synchronise les analytics de tous les utilisateurs actifs (7 derniers jours)"""
        try:
            logger.info("Starting regular analytics sync for all users")
            
            async with get_db() as db:
                # Récupérer tous les utilisateurs actifs
                result = await db.execute(
                    select(User).where(User.is_active == True)
                )
                users = result.scalars().all()
                
                for user in users:
                    try:
                        await analytics_service.sync_user_analytics(db, str(user.id), days=7)
                        logger.info(f"Synced analytics for user {user.id}")
                    except Exception as e:
                        logger.error(f"Error syncing analytics for user {user.id}: {e}")
                
                logger.info(f"Completed regular analytics sync for {len(users)} users")
                
        except Exception as e:
            logger.error(f"Error in regular analytics sync: {e}")
    
    async def sync_all_users_analytics_full(self):
        """Synchronise complète (30 derniers jours)"""
        try:
            logger.info("Starting full analytics sync for all users")
            
            async with get_db() as db:
                result = await db.execute(
                    select(User).where(User.is_active == True)
                )
                users = result.scalars().all()
                
                for user in users:
                    try:
                        await analytics_service.sync_user_analytics(db, str(user.id), days=30)
                        logger.info(f"Full sync completed for user {user.id}")
                    except Exception as e:
                        logger.error(f"Error in full sync for user {user.id}: {e}")
                
                logger.info(f"Completed full analytics sync for {len(users)} users")
                
        except Exception as e:
            logger.error(f"Error in full analytics sync: {e}")
    
    async def cleanup_old_analytics(self):
        """Nettoie les anciennes données d'historique (> 6 mois)"""
        try:
            logger.info("Starting analytics history cleanup")
            
            async with get_db() as db:
                from app.models import AnalyticsHistory
                
                cutoff_date = datetime.utcnow() - timedelta(days=180)  # 6 mois
                
                result = await db.execute(
                    select(AnalyticsHistory).where(
                        AnalyticsHistory.recorded_at < cutoff_date
                    )
                )
                old_records = result.scalars().all()
                
                for record in old_records:
                    await db.delete(record)
                
                await db.commit()
                logger.info(f"Cleaned up {len(old_records)} old analytics records")
                
        except Exception as e:
            logger.error(f"Error in analytics cleanup: {e}")
    
    def start(self):
        """Démarre le scheduler"""
        logger.info("Starting analytics scheduler")
        self.scheduler.start()
    
    def stop(self):
        """Arrête le scheduler"""
        logger.info("Stopping analytics scheduler")
        self.scheduler.shutdown()

# Instance globale
analytics_scheduler = AnalyticsScheduler()

# Fonction pour démarrer le scheduler au lancement de l'app
async def start_scheduler():
    """Démarre le scheduler au lancement de FastAPI"""
    analytics_scheduler.start()
    logger.info("Analytics scheduler started")

# Fonction pour arrêter le scheduler
async def stop_scheduler():
    """Arrête le scheduler à la fermeture de FastAPI"""
    analytics_scheduler.stop()
    logger.info("Analytics scheduler stopped") 