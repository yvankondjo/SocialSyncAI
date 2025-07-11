-- Migration script: Transfer existing analytics data to analytics_history
-- Run this after creating the analytics_history table

INSERT INTO analytics_history (
    content_id,
    platform,
    likes,
    shares,
    comments,
    impressions,
    reach,
    clicks,
    conversions,
    engagement_rate,
    recorded_at,
    user_id,
    raw_metrics,
    created_at
)
SELECT 
    a.content_id,
    a.platform,
    a.likes,
    a.shares,
    a.comments,
    a.impressions,
    a.reach,
    a.clicks,
    a.conversions,
    a.engagement_rate,
    a.recorded_at,
    sa.user_id,
    a.raw_metrics,
    a.created_at
FROM analytics a
JOIN content c ON a.content_id = c.id
JOIN social_accounts sa ON c.social_account_id = sa.id;

-- Verify migration
SELECT 
    'analytics' as table_name, 
    COUNT(*) as record_count 
FROM analytics
UNION ALL
SELECT 
    'analytics_history' as table_name, 
    COUNT(*) as record_count 
FROM analytics_history; 