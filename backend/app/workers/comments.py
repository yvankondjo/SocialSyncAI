"""
Celery Workers for Comment Polling System

Workers:
- poll_post_comments: Periodic task (every 5 min) to fetch new comments from platforms
- process_comment: Process a single comment with AI guardrails and auto-reply

Features:
- Adaptive polling intervals (5min → 15min → 30min based on post age)
- OpenAI Moderation integration
- Email escalation for flagged content
- RAG-based auto-replies
- Retry logic with exponential backoff
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from app.workers.celery_app import celery
from app.db.session import get_db
from app.services.instagram_connector import InstagramConnector
from app.services.ai_decision_service import AIDecisionService
from app.services.email_service import EmailService
from app.services.rag_agent import RAGAgent
from app.services.comment_triage import CommentTriageService, get_owner_username
from app.schemas.ai_rules import AIDecision

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _calculate_poll_interval(post: Dict[str, Any]) -> timedelta:
    """
    Calculate adaptive polling interval based on post age

    Strategy:
    - J+0 to J+2: Every 5 minutes (high engagement period)
    - J+2 to J+5: Every 15 minutes (medium engagement)
    - J+5 to J+7: Every 30 minutes (low engagement)
    - J+7+: Stop polling (monitoring_ends_at exceeded)

    Args:
        post: Dict with 'posted_at' key (from monitored_posts)

    Returns:
        timedelta for next polling interval
    """
    posted_at_str = post.get("posted_at")
    if not posted_at_str:
        return timedelta(minutes=5)  # Default

    try:
        if isinstance(posted_at_str, str):
            # Parse ISO format timestamp
            posted_at = datetime.fromisoformat(posted_at_str.replace('Z', '+00:00'))
        else:
            posted_at = posted_at_str

        age = datetime.now(posted_at.tzinfo) - posted_at

        if age < timedelta(days=2):
            return timedelta(minutes=5)  # J+0 to J+2
        elif age < timedelta(days=5):
            return timedelta(minutes=15)  # J+2 to J+5
        else:
            return timedelta(minutes=30)  # J+5 to J+7

    except Exception as e:
        logger.error(f"Error calculating poll interval: {e}")
        return timedelta(minutes=5)  # Safe default


def _get_connector(post: Dict[str, Any]) -> Optional[InstagramConnector]:
    """
    Get platform connector for a post

    Args:
        post: Dict with 'platform' and social_accounts data

    Returns:
        PlatformConnector instance or None
    """
    platform = post.get("platform")

    if platform == "instagram":
        social_accounts = post.get("social_accounts")
        if not social_accounts:
            logger.error(f"[POLL] No social_accounts data for post {post.get('id')}")
            return None

        access_token = social_accounts.get("access_token")
        page_id = social_accounts.get("account_id")  # Fixed: was platform_page_id

        if not access_token or not page_id:
            logger.error(
                f"[POLL] Missing credentials for Instagram post {post.get('id')}: "
                f"has_token={bool(access_token)}, has_page_id={bool(page_id)}"
            )
            return None

        return InstagramConnector(access_token, page_id)

    else:
        logger.warning(f"[POLL] Unsupported platform: {platform}")
        return None


def _get_checkpoint(db, post_id: str) -> Dict[str, Any]:
    """
    Get checkpoint for post (pagination state)

    Args:
        db: Supabase client
        post_id: Post UUID

    Returns:
        Dict with last_cursor and last_seen_ts
    """
    try:
        result = db.table("comment_checkpoint") \
            .select("*") \
            .eq("monitored_post_id", post_id) \
            .maybe_single() \
            .execute()

        return result.data or {}

    except Exception as e:
        logger.error(f"[POLL] Error fetching checkpoint for {post_id}: {e}")
        return {}


def _update_checkpoint(
    db,
    post_id: str,
    last_cursor: Optional[str],
    last_seen_ts: Optional[datetime] = None
):
    """
    Update checkpoint with new cursor and timestamp

    Args:
        db: Supabase client
        post_id: Monitored post UUID
        last_cursor: Pagination cursor from API
        last_seen_ts: Timestamp of most recent comment
    """
    try:
        data = {
            "monitored_post_id": post_id,
            "last_cursor": last_cursor,
            "last_seen_ts": last_seen_ts.isoformat() if last_seen_ts else None
        }

        db.table("comment_checkpoint").upsert(data).execute()

        logger.debug(f"[POLL] Updated checkpoint for {post_id}: cursor={'exists' if last_cursor else 'none'}")

    except Exception as e:
        logger.error(f"[POLL] Error updating checkpoint for {post_id}: {e}")


def _save_comment(db, post_id: str, comment_data: Dict[str, Any]) -> Optional[str]:
    """
    Save comment to database

    Args:
        db: Supabase client
        post_id: Monitored post UUID
        comment_data: Comment data from connector

    Returns:
        Comment UUID or None if failed
    """
    try:
        data = {
            "monitored_post_id": post_id,  # FK to monitored_posts
            "platform_comment_id": comment_data["id"],
            "author_name": comment_data.get("author_name"),
            "author_id": comment_data.get("author_id"),
            "text": comment_data["text"],
            "created_at": comment_data["created_at"],
            "parent_id": comment_data.get("parent_id"),  # Instagram parent comment ID (TEXT)
            "like_count": comment_data.get("like_count", 0)
        }

        # Upsert to handle duplicates (idempotence)
        result = db.table("comments").upsert(data, on_conflict="monitored_post_id,platform_comment_id").execute()

        if result.data and len(result.data) > 0:
            comment_id = result.data[0]["id"]
            logger.debug(f"[POLL] Saved comment {comment_id} from {comment_data.get('author_name')}")
            return comment_id
        else:
            logger.warning(f"[POLL] Failed to save comment: no data returned")
            return None

    except Exception as e:
        logger.error(f"[POLL] Error saving comment: {e}")
        return None


def _get_user_email(db, user_id: str) -> Optional[str]:
    """
    Get user email for escalation notifications

    Args:
        db: Supabase client
        user_id: User UUID

    Returns:
        Email address or None
    """
    try:
        result = db.table("users") \
            .select("email") \
            .eq("id", user_id) \
            .single() \
            .execute()

        return result.data.get("email") if result.data else None

    except Exception as e:
        logger.error(f"[PROCESS] Error fetching user email for {user_id}: {e}")
        return None


# ============================================================================
# CELERY TASKS
# ============================================================================

@celery.task(name="app.workers.comments.poll_post_comments")
def poll_post_comments():
    """
    Periodic task to poll published posts for new comments

    Schedule: Every 5 minutes (Celery Beat)

    Logic:
    1. Query posts with active polling (status='published' AND stop_at > NOW())
    2. For each post:
       - Check if next_check_at <= NOW() (skip if not due yet)
       - Calculate adaptive interval
       - Fetch new comments via PlatformConnector
       - Save comments to DB
       - Enqueue process_comment tasks
       - Update checkpoint and next_check_at
    3. Log metrics

    Returns:
        Dict with metrics: {posts_checked, comments_found, errors}
    """
    db = get_db()

    try:
        # Query monitored_posts with active polling
        result = db.table("monitored_posts") \
            .select("*, social_accounts!inner(platform, access_token, account_id)") \
            .eq("monitoring_enabled", True) \
            .lte("next_check_at", datetime.utcnow().isoformat()) \
            .gt("monitoring_ends_at", datetime.utcnow().isoformat()) \
            .execute()

        posts = result.data or []

        logger.info(f"[POLL] Checking {len(posts)} monitored posts for new comments")

        metrics = {
            "posts_checked": 0,
            "comments_found": 0,
            "errors": 0
        }

        for post in posts:
            try:
                post_id = post["id"]

                # Check if due for polling
                next_check_str = post.get("next_check_at")
                if next_check_str:
                    next_check = datetime.fromisoformat(next_check_str.replace('Z', '+00:00'))
                    if next_check > datetime.now(next_check.tzinfo):
                        logger.debug(f"[POLL] Post {post_id} not due yet, skipping")
                        continue

                # Get connector
                connector = _get_connector(post)
                if not connector:
                    metrics["errors"] += 1
                    continue

                # Get checkpoint
                checkpoint = _get_checkpoint(db, post_id)
                last_cursor = checkpoint.get("last_cursor")

                # Fetch new comments
                platform_post_id = post.get("platform_post_id")
                if not platform_post_id:
                    logger.error(f"[POLL] Post {post_id} has no platform_post_id")
                    metrics["errors"] += 1
                    continue

                logger.info(
                    f"[POLL] Fetching comments for post {post_id} "
                    f"(platform_post_id={platform_post_id})"
                )

                # Fetch comments using asyncio.run() since connector methods are async
                new_comments, next_cursor = asyncio.run(
                    connector.list_new_comments(
                        platform_post_id,
                        since_cursor=last_cursor
                    )
                )

                # Save comments and enqueue processing
                for comment in new_comments:
                    comment_id = _save_comment(db, post_id, comment)
                    if comment_id:
                        # Enqueue processing task
                        process_comment.delay(comment_id)
                        metrics["comments_found"] += 1

                # Update checkpoint
                if new_comments:
                    latest_ts = max(
                        datetime.fromisoformat(c["created_at"].replace('Z', '+00:00'))
                        for c in new_comments
                    )
                    _update_checkpoint(db, post_id, next_cursor, latest_ts)
                elif next_cursor:
                    # Cursor changed but no new comments
                    _update_checkpoint(db, post_id, next_cursor)

                # Calculate next polling interval
                interval = _calculate_poll_interval(post)
                next_check_at = datetime.utcnow() + interval

                # Update monitored_post
                db.table("monitored_posts") \
                    .update({
                        "last_check_at": datetime.utcnow().isoformat(),
                        "next_check_at": next_check_at.isoformat()
                    }) \
                    .eq("id", post_id) \
                    .execute()

                metrics["posts_checked"] += 1

                logger.info(
                    f"[POLL] Post {post_id}: found {len(new_comments)} new comments, "
                    f"next check in {interval.total_seconds() / 60:.0f} minutes"
                )

            except Exception as e:
                logger.error(f"[POLL] Error polling post {post.get('id')}: {e}")
                metrics["errors"] += 1

        logger.info(
            f"[POLL] Completed: {metrics['posts_checked']} posts checked, "
            f"{metrics['comments_found']} comments found, "
            f"{metrics['errors']} errors"
        )

        return metrics

    except Exception as e:
        logger.error(f"[POLL] Fatal error in poll_post_comments: {e}")
        return {"error": str(e)}


@celery.task(
    name="app.workers.comments.process_comment",
    bind=True,
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def process_comment(self, comment_id: str):
    """
    Process a single comment with AI guardrails and auto-reply

    Args:
        comment_id: Comment UUID to process

    Flow:
    1. Fetch comment + post + user data
    2. AIDecisionService.check_message(text, context_type="comment")
    3. Log decision
    4. Take action based on decision:
       - ESCALATE → Send email to user
       - RESPOND → Generate RAG response and reply via connector
       - IGNORE → No action
    5. Update comment triage + ai_decision_id

    Retry: 3 attempts with 5 min backoff on API errors
    """
    db = get_db()

    try:
        # 1. Fetch comment with related data from monitored_posts
        result = db.table("comments") \
            .select("""
                *,
                monitored_posts!inner(
                    id,
                    user_id,
                    platform,
                    platform_post_id,
                    caption,
                    media_url,
                    posted_at,
                    social_accounts!inner(id, access_token, account_id, username)
                )
            """) \
            .eq("id", comment_id) \
            .single() \
            .execute()

        if not result.data:
            logger.error(f"[PROCESS] Comment {comment_id} not found")
            return

        comment = result.data
        post = comment["monitored_posts"]
        user_id = post["user_id"]
        platform = post["platform"]
        social_account_id = post["social_accounts"]["id"] if "social_accounts" in post else None

        logger.info(
            f"[PROCESS] Processing comment {comment_id} from "
            f"{comment.get('author_name')} on {platform} post"
        )

        # 1.5. Check if AI is enabled for comments
        # Query monitoring_rules to check ai_enabled_for_comments flag
        try:
            # First, try account-specific rules
            rules_result = db.table("monitoring_rules") \
                .select("ai_enabled_for_comments") \
                .eq("user_id", user_id) \
                .eq("social_account_id", social_account_id) \
                .maybe_single() \
                .execute()

            # If no account-specific rules, fall back to user-level rules
            if not rules_result.data:
                rules_result = db.table("monitoring_rules") \
                    .select("ai_enabled_for_comments") \
                    .eq("user_id", user_id) \
                    .is_("social_account_id", "null") \
                    .maybe_single() \
                    .execute()

            # Check if AI is disabled for comments
            if rules_result.data:
                ai_enabled = rules_result.data.get("ai_enabled_for_comments", True)

                if not ai_enabled:
                    logger.info(
                        f"[PROCESS] AI disabled for comments (user_id={user_id}, "
                        f"account_id={social_account_id}). Skipping AI processing for comment {comment_id}"
                    )

                    # Mark comment as ignored (AI disabled by user)
                    db.table("comments") \
                        .update({"triage": "ignore"}) \
                        .eq("id", comment_id) \
                        .execute()

                    return

        except Exception as e:
            # If monitoring_rules query fails, log warning but continue processing
            # (fail-open strategy - don't block comment processing on config errors)
            logger.warning(
                f"[PROCESS] Failed to check ai_enabled_for_comments flag for comment {comment_id}: {e}. "
                f"Continuing with AI processing as fallback."
            )

        # 1.6. Check if AI should respond (conversation detection)
        # Get owner username for triage
        owner_username = post["social_accounts"].get("username", "") if "social_accounts" in post else ""

        if not owner_username and social_account_id:
            owner_username = get_owner_username(db, social_account_id)

        if owner_username:
            # Get all comments on this post for thread reconstruction
            all_comments_result = db.table("comments") \
                .select("*") \
                .eq("monitored_post_id", post["id"]) \
                .execute()

            all_comments = all_comments_result.data or []

            # Check if AI should respond
            triage_service = CommentTriageService(user_id, owner_username)
            should_respond, triage_reason = triage_service.should_ai_respond(
                comment, post, all_comments
            )

            if not should_respond:
                # Mark as user_conversation or ignore
                logger.info(
                    f"[PROCESS] Skipping AI processing: {triage_reason} - "
                    f"Comment from {comment.get('author_name')}: {comment['text'][:50]}..."
                )

                db.table("comments") \
                    .update({"triage": triage_reason}) \
                    .eq("id", comment_id) \
                    .execute()

                return

        # 2. AI Decision with context_type="comment"
        decision_service = AIDecisionService(user_id, db)
        decision, confidence, reason, rule = decision_service.check_message(
            comment["text"],
            context_type="comment"  # <-- IMPORTANT: Granular scope control
        )

        logger.info(
            f"[PROCESS] Comment {comment_id} → Decision: {decision.value}, "
            f"confidence: {confidence:.2f}, reason: {reason}"
        )

        # 3. Log decision
        decision_record = decision_service.log_decision(
            message_id=comment_id,
            message_text=comment["text"],
            decision=decision,
            confidence=confidence,
            reason=reason,
            matched_rule=rule
        )

        decision_id = decision_record["id"] if decision_record else None

        # 4. Take action based on decision
        if decision == AIDecision.ESCALATE:
            # Send escalation email
            logger.info(f"[PROCESS] ESCALATE: Sending email for comment {comment_id}")

            # TODO: Fix email escalation - EmailEscalationService removed
            # For now, just log the escalation
            logger.warning(f"[ESCALATE] Email sending temporarily disabled - comment {comment_id} needs manual review")
            logger.warning(f"[ESCALATE] Reason: {reason}")

            # Commented out until EmailEscalationService is properly implemented
            # email_service = EmailService()
            # email_data = await email_service.send_escalation_email(
            #     to_email="support@example.com",
            #     escalation_data={
            #         "message_text": comment["text"],
            #         "reason": reason,
            #         "context": {
            #             "platform": platform,
            #             "author": comment.get("author_name", "Unknown"),
            #             "post_id": post["id"],
            #             "comment_id": comment_id,
            #             "platform_post_id": post.get("platform_post_id")
            #         }
            #     },
            #     conversation_link="https://example.com/conversations"
            # )
            # logger.info(f"[PROCESS] Escalation email sent")
            # Commented out until EmailEscalationService is fixed

        elif decision == AIDecision.RESPOND:
            # Generate auto-reply via RAG
            logger.info(f"[PROCESS] RESPOND: Generating auto-reply for comment {comment_id}")

            # Build enriched context for Vision AI
            context_parts = []

            # 1. Add post image if available (Vision AI)
            media_url = post.get("media_url")
            if media_url:
                context_parts.append({
                    "type": "image_url",
                    "image_url": {"url": media_url}
                })
                logger.info(f"[PROCESS] Added post image to context: {media_url[:50]}...")

            # 2. Add post caption
            caption = post.get("caption")
            context_text = ""
            if caption:
                context_text += f"📸 Post Caption: {caption}\n\n"

            # 3. Add music title if available (Instagram posts can have music)
            # Note: Music metadata would need to be fetched from Instagram API
            # For now, we'll check if it's in the post metadata
            music_title = post.get("music_title")  # To be fetched from API
            if music_title:
                context_text += f"🎵 Music: {music_title}\n\n"

            # 4. Add comment thread (all comments on this post for context)
            thread_comments = all_comments if all_comments else []
            if thread_comments and len(thread_comments) > 1:
                context_text += "💬 Comment Thread:\n"
                for c in thread_comments[:10]:  # Limit to 10 most recent
                    author = c.get("author_name", "Unknown")
                    text = c.get("text", "")
                    context_text += f"  - @{author}: {text}\n"
                context_text += "\n"

            # 5. Add the current comment being responded to
            context_text += f"❓ New Comment from @{comment.get('author_name')}: {comment['text']}"

            # Add text context
            context_parts.append({
                "type": "text",
                "text": context_text
            })

            # Generate response with RAG agent using enriched context
            from langchain_core.messages import HumanMessage
            enriched_message = HumanMessage(content=context_parts)

            agent = RAGAgent(user_id=user_id)
            response_data = asyncio.run(agent.graph.ainvoke(
                {"messages": [enriched_message]},
                config={"configurable": {"thread_id": f"comment:{comment_id}"}}
            ))

            # Extract response from agent output
            if response_data and "messages" in response_data:
                ai_messages = [m for m in response_data["messages"] if hasattr(m, 'type') and m.type == 'ai']
                if ai_messages:
                    response_text = ai_messages[-1].content
                else:
                    logger.error(f"[PROCESS] No AI message in response")
                    raise Exception("No AI response generated")
            else:
                logger.error(f"[PROCESS] Invalid response format from RAG agent")
                raise Exception("Invalid RAG response format")

            if not response_text:
                logger.error(f"[PROCESS] RAG agent returned empty response")
                raise Exception("Empty RAG response")

            # Get connector and reply
            connector = _get_connector(post)
            if not connector:
                raise Exception("Failed to get platform connector")

            # Reply using asyncio.run() since connector method is async
            result = asyncio.run(
                connector.reply_to_comment(
                    comment["platform_comment_id"],
                    response_text
                )
            )

            if result.get("success"):
                # Update replied_at timestamp
                db.table("comments") \
                    .update({"replied_at": datetime.utcnow().isoformat()}) \
                    .eq("id", comment_id) \
                    .execute()

                logger.info(
                    f"[PROCESS] Successfully replied to comment {comment_id}: "
                    f"{response_text[:50]}..."
                )
            else:
                raise Exception(f"Failed to send reply: {result.get('error')}")

        else:  # IGNORE
            logger.info(f"[PROCESS] IGNORE: No action for comment {comment_id}")

        # 5. Update triage
        db.table("comments") \
            .update({
                "triage": decision.value,
                "ai_decision_id": decision_id
            }) \
            .eq("id", comment_id) \
            .execute()

        logger.info(f"[PROCESS] Completed processing comment {comment_id}")

    except Exception as e:
        logger.error(f"[PROCESS] Error processing comment {comment_id}: {e}")

        # Retry on transient errors
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(
                f"[PROCESS] Max retries exceeded for comment {comment_id}, "
                f"marking as failed"
            )

            # Update comment with error
            try:
                db.table("comments") \
                    .update({
                        "triage": AIDecision.IGNORE.value,
                        "ai_decision_id": None
                    }) \
                    .eq("id", comment_id) \
                    .execute()
            except:
                pass
