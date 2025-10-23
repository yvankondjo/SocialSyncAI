"""
Celery Workers for Topic Modeling (BERTopic)

Tasks:
- Daily fit + merge: Fit on last 24h messages + merge with yesterday's model (3 AM daily)
  - Generates embeddings on-the-fly (not stored)
  - Saves top 10 topics (overwrites old ones)
"""
import logging
import asyncio
from typing import Dict, Any
from datetime import datetime, timezone

from app.workers.celery_app import celery
from app.db.session import get_db
from app.services.topic_modeling_service import TopicModelingService

logger = logging.getLogger(__name__)


@celery.task(name="app.workers.topics.run_daily_fit_and_merge")
def run_daily_fit_and_merge() -> Dict[str, Any]:
    """
    Daily task: Fit + Merge BERTopic models
    Runs at 3:00 AM UTC every day

    Workflow per user:
    1. Fetch last 24h inbound messages
    2. Generate embeddings on-the-fly
    3. Fit new model on these messages
    4. Merge with yesterday's model (if exists)
    5. Save top 10 topics (overwrite old ones)

    Returns:
        Dict with processing results per user
    """
    started_at = datetime.now(timezone.utc)

    try:
        logger.info("=" * 80)
        logger.info("[TOPIC DAILY] Starting daily fit+merge")
        logger.info("=" * 80)

        db = get_db()

        users_result = db.table("users").select("id").execute()
        user_ids = [str(user["id"]) for user in users_result.data]

        total_users = len(user_ids)
        logger.info(f"[TOPIC DAILY] Found {total_users} users")

        results = {
            "total_users": total_users,
            "processed_users": 0,
            "skipped_users": 0,
            "failed_users": 0,
            "user_details": [],
            "estimated_time_per_user_seconds": 0
        }

        if total_users == 0:
            logger.info("[TOPIC DAILY] No users found, skipping")
            return results

        user_start = datetime.now(timezone.utc)

        for user_id in user_ids:
            user_task_start = datetime.now(timezone.utc)

            try:
                logger.info(f"[TOPIC DAILY] Processing user: {user_id}")

                service = TopicModelingService(user_id)

                new_version = asyncio.run(
                    service.merge_and_update_model(min_documents=10)
                )

                user_task_duration = (datetime.now(timezone.utc) - user_task_start).total_seconds()

                if new_version:
                    results["processed_users"] += 1
                    results["user_details"].append({
                        "user_id": user_id,
                        "status": "success",
                        "new_version": new_version,
                        "duration_seconds": user_task_duration
                    })

                    logger.info(
                        f"[TOPIC DAILY] User {user_id}: "
                        f"Created model {new_version} in {user_task_duration:.2f}s"
                    )
                else:
                    results["skipped_users"] += 1
                    results["user_details"].append({
                        "user_id": user_id,
                        "status": "skipped",
                        "reason": "Not enough new messages (< 10)",
                        "duration_seconds": user_task_duration
                    })

                    logger.info(f"[TOPIC DAILY] User {user_id}: Skipped (not enough messages)")

            except Exception as e:
                logger.error(f"[TOPIC DAILY] Error processing user {user_id}: {e}", exc_info=True)
                results["failed_users"] += 1
                results["user_details"].append({
                    "user_id": user_id,
                    "status": "failed",
                    "error": str(e)
                })
                continue

        if results["processed_users"] > 0:
            total_processing_time = (datetime.now(timezone.utc) - user_start).total_seconds()
            results["estimated_time_per_user_seconds"] = total_processing_time / results["processed_users"]

        finished_at = datetime.now(timezone.utc)
        duration_seconds = (finished_at - started_at).total_seconds()

        logger.info("=" * 80)
        logger.info(
            f"[TOPIC DAILY] Daily fit+merge complete: "
            f"{results['processed_users']} processed, "
            f"{results['skipped_users']} skipped, "
            f"{results['failed_users']} failed, "
            f"Duration: {duration_seconds:.2f}s, "
            f"Avg time/user: {results['estimated_time_per_user_seconds']:.2f}s"
        )
        logger.info("=" * 80)

        results["started_at"] = started_at.isoformat()
        results["finished_at"] = finished_at.isoformat()
        results["duration_seconds"] = duration_seconds

        return results

    except Exception as e:
        logger.error(f"[TOPIC DAILY] Fatal error in daily fit+merge: {e}", exc_info=True)
        return {
            "error": str(e),
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat()
        }


@celery.task(name="app.workers.topics.fit_initial_model_for_user")
def fit_initial_model_for_user(user_id: str) -> Dict[str, Any]:
    """
    One-time task: Fit initial BERTopic model for a user
    Called manually or automatically when user has no active model

    Fits on last 24h messages with on-the-fly embedding generation

    Args:
        user_id: User ID to fit model for

    Returns:
        Dict with fit result
    """
    started_at = datetime.now(timezone.utc)

    try:
        logger.info(f"[TOPIC INIT] Fitting initial model for user: {user_id}")

        service = TopicModelingService(user_id)

        version = asyncio.run(
            service.fit_initial_model(min_documents=10)
        )

        if version:
            finished_at = datetime.now(timezone.utc)
            duration_seconds = (finished_at - started_at).total_seconds()

            logger.info(
                f"[TOPIC INIT] Initial model fit complete for user {user_id}: "
                f"version {version}, Duration: {duration_seconds:.2f}s"
            )

            return {
                "success": True,
                "user_id": user_id,
                "version": version,
                "started_at": started_at.isoformat(),
                "finished_at": finished_at.isoformat(),
                "duration_seconds": duration_seconds
            }
        else:
            logger.warning(
                f"[TOPIC INIT] Not enough messages for user {user_id} "
                f"(minimum 10 required in last 24h)"
            )

            return {
                "success": False,
                "user_id": user_id,
                "reason": "Not enough messages in last 24h (minimum 10 required)",
                "started_at": started_at.isoformat(),
                "finished_at": datetime.now(timezone.utc).isoformat()
            }

    except Exception as e:
        logger.error(f"[TOPIC INIT] Error fitting initial model for user {user_id}: {e}", exc_info=True)

        return {
            "success": False,
            "user_id": user_id,
            "error": str(e),
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat()
        }
