"""
Analytics API Router
Analytics for conversations, AI metrics, and topics
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timedelta
from typing import Optional

from app.db.session import get_authenticated_db
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
async def get_analytics_overview(
    date_range: str = Query("30d", regex="^(7d|30d|90d)$"),
    db=Depends(get_authenticated_db)
):
    """
    Get analytics overview (KPIs)
    Returns: total conversations, messages, AI metrics, moderation stats
    """
    user_id = db.auth.get_user().user.id

    days = int(date_range.replace("d", ""))
    start_date = datetime.utcnow() - timedelta(days=days)

    conversations_result = db.table("conversations").select("id", count="exact").eq("user_id", user_id).gte("created_at", start_date.isoformat()).execute()
    total_conversations = conversations_result.count or 0

    messages_result = db.table("messages").select("id", count="exact").eq("user_id", user_id).gte("created_at", start_date.isoformat()).execute()
    total_messages = messages_result.count or 0

    decisions_result = db.table("ai_decisions").select("decision, confidence").eq("user_id", user_id).gte("created_at", start_date.isoformat()).execute()

    ai_stats = {"respond": 0, "ignore": 0, "escalate": 0, "avg_confidence": 0.0}
    if decisions_result.data:
        total_confidence = 0
        for decision in decisions_result.data:
            decision_type = decision.get("decision", "respond")
            if decision_type in ai_stats:
                ai_stats[decision_type] += 1
            total_confidence += decision.get("confidence", 0.0)

        ai_stats["avg_confidence"] = round(total_confidence / len(decisions_result.data), 2) if decisions_result.data else 0.0

    escalations_result = db.table("escalation_emails").select("id", count="exact").eq("user_id", user_id).gte("created_at", start_date.isoformat()).execute()
    total_escalations = escalations_result.count or 0

    moderation_flags = db.table("ai_decisions").select("id", count="exact").eq("user_id", user_id).like("matched_rule", "openai_moderation%").gte("created_at", start_date.isoformat()).execute().count or 0

    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "ai_stats": ai_stats,
        "total_escalations": total_escalations,
        "moderation_flags": moderation_flags,
        "date_range": date_range,
        "start_date": start_date.isoformat(),
        "end_date": datetime.utcnow().isoformat()
    }


@router.get("/conversations-timeline")
async def get_conversations_timeline(
    date_range: str = Query("30d", regex="^(7d|30d|90d)$"),
    db=Depends(get_authenticated_db)
):
    """
    Get conversations timeline (day by day)
    Returns: array of {date, conversations, messages}
    """
    user_id = db.auth.get_user().user.id
    days = int(date_range.replace("d", ""))
    start_date = datetime.utcnow() - timedelta(days=days)

    conversations = db.table("conversations").select("created_at").eq("user_id", user_id).gte("created_at", start_date.isoformat()).execute().data

    timeline = {}
    for conv in conversations:
        date_str = conv["created_at"][:10] 
        if date_str not in timeline:
            timeline[date_str] = {"date": date_str, "conversations": 0, "messages": 0}
        timeline[date_str]["conversations"] += 1

    messages = db.table("messages").select("created_at").eq("user_id", user_id).gte("created_at", start_date.isoformat()).execute().data
    for msg in messages:
        date_str = msg["created_at"][:10]
        if date_str in timeline:
            timeline[date_str]["messages"] += 1

    result = sorted(timeline.values(), key=lambda x: x["date"])

    return result


@router.get("/ai-metrics")
async def get_ai_metrics(
    date_range: str = Query("30d", regex="^(7d|30d|90d)$"),
    db=Depends(get_authenticated_db)
):
    """
    Get AI performance metrics
    Returns: decision distribution, confidence over time, top matched rules
    """
    user_id = db.auth.get_user().user.id
    days = int(date_range.replace("d", ""))
    start_date = datetime.utcnow() - timedelta(days=days)

    decisions = db.table("ai_decisions").select("*").eq("user_id", user_id).gte("created_at", start_date.isoformat()).order("created_at", desc=False).execute().data

    distribution = {"respond": 0, "ignore": 0, "escalate": 0}
    for decision in decisions:
        decision_type = decision.get("decision", "respond")
        if decision_type in distribution:
            distribution[decision_type] += 1

    confidence_timeline = {}
    for decision in decisions:
        date_str = decision["created_at"][:10]
        if date_str not in confidence_timeline:
            confidence_timeline[date_str] = {"date": date_str, "confidences": []}
        confidence_timeline[date_str]["confidences"].append(decision.get("confidence", 0.0))

    confidence_over_time = []
    for date_str, data in sorted(confidence_timeline.items()):
        avg_conf = sum(data["confidences"]) / len(data["confidences"]) if data["confidences"] else 0.0
        confidence_over_time.append({
            "date": date_str,
            "avg_confidence": round(avg_conf, 2),
            "count": len(data["confidences"])
        })

    rules_count = {}
    for decision in decisions:
        rule = decision.get("matched_rule", "unknown")
        rules_count[rule] = rules_count.get(rule, 0) + 1

    top_rules = sorted(
        [{"rule": rule, "count": count} for rule, count in rules_count.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:10]

    return {
        "distribution": distribution,
        "confidence_over_time": confidence_over_time,
        "top_rules": top_rules
    }


@router.get("/topics")
async def get_topics(
    date_range: str = Query("30d", regex="^(7d|30d|90d)$"),
    db=Depends(get_authenticated_db)
):
    """
    Get top topics from BERTopic analysis
    Returns: array of {topic_id, topic_label, keywords, message_count, samples}

    Note: This requires BERTopic analysis to be run daily (Celery task)
    If no data available, returns empty array
    """
    user_id = db.auth.get_user().user.id
    days = int(date_range.replace("d", ""))
    start_date = datetime.utcnow() - timedelta(days=days)

    topics = db.table("topic_analysis").select("*").eq("user_id", user_id).gte("analysis_date", start_date.date().isoformat()).execute().data

    topic_aggregates = {}
    for topic in topics:
        topic_id = topic["topic_id"]
        if topic_id not in topic_aggregates:
            topic_aggregates[topic_id] = {
                "topic_id": topic_id,
                "topic_label": topic["topic_label"],
                "topic_keywords": topic["topic_keywords"],
                "message_count": 0,
                "sample_messages": []
            }

        topic_aggregates[topic_id]["message_count"] += topic["message_count"]
        topic_aggregates[topic_id]["sample_messages"].extend(topic.get("sample_messages", [])[:3])

    top_topics = sorted(
        topic_aggregates.values(),
        key=lambda x: x["message_count"],
        reverse=True
    )[:10]

    return top_topics


@router.get("/posts-comments-timeline")
async def get_posts_comments_timeline(
    date_range: str = Query("30d", regex="^(7d|30d|90d)$"),
    db=Depends(get_authenticated_db)
):
    """
    Get posts and comments timeline
    Returns: array of {date, posts, comments, dms}
    """
    user_id = db.auth.get_user().user.id
    days = int(date_range.replace("d", ""))
    start_date = datetime.utcnow() - timedelta(days=days)

    posts = db.table("scheduled_posts").select("scheduled_for").eq("user_id", user_id).gte("scheduled_for", start_date.isoformat()).execute().data

    comments = db.table("comments").select("created_at").eq("user_id", user_id).gte("created_at", start_date.isoformat()).execute().data

    dms = db.table("messages").select("created_at").eq("user_id", user_id).gte("created_at", start_date.isoformat()).execute().data

    timeline = {}

    for post in posts:
        date_str = post["scheduled_for"][:10]
        if date_str not in timeline:
            timeline[date_str] = {"date": date_str, "posts": 0, "comments": 0, "dms": 0}
        timeline[date_str]["posts"] += 1

    for comment in comments:
        date_str = comment["created_at"][:10]
        if date_str not in timeline:
            timeline[date_str] = {"date": date_str, "posts": 0, "comments": 0, "dms": 0}
        timeline[date_str]["comments"] += 1

    for dm in dms:
        date_str = dm["created_at"][:10]
        if date_str not in timeline:
            timeline[date_str] = {"date": date_str, "posts": 0, "comments": 0, "dms": 0}
        timeline[date_str]["dms"] += 1

    result = sorted(timeline.values(), key=lambda x: x["date"])

    return result
