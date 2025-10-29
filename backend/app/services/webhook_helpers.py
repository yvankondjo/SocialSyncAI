import logging
from typing import Optional
from supabase import Client

logger = logging.getLogger(__name__)


async def check_event_processed(
    db: Client,
    stripe_event_id: str = None,
) -> bool:
    """
    Check if a webhook event has already been processed.

    Args:
        db: Client Supabase
        stripe_event_id: ID of the Stripe event (required)

    Returns:
        True if the event has already been processed, False otherwise
    """
    try:
        query = db.table('webhook_events')

        if stripe_event_id:
            result = query.select('id').eq('stripe_event_id', stripe_event_id).execute()
        else:
            logger.warning("No event_id provided for idempotence check")
            return False

        return len(result.data) > 0

    except Exception as e:
        logger.warning(f"Error checking idempotence: {e}")
        return False


async def mark_event_processed(
    db: Client,
    event_id: str,
    event_type: str,
    payload: dict,
    source: str = 'stripe'
) -> None:
    """
    Mark a webhook event as processed.

    Args:
        db: Client Supabase
        event_id: ID of the event
        event_type: Event type (ex: 'customer.subscription.created')
        payload: Complete webhook payload
        source: Source ('stripe' or 'whop')
    """
    try:
        if source != 'stripe':
            raise ValueError(f"Invalid source: {source}")

        event_data = {
            'event_type': event_type,
            'source': source,
            'payload': payload
        }

        event_data['stripe_event_id'] = event_id

        db.table('webhook_events').insert(event_data).execute()

        logger.debug(f"Event {source}:{event_id} marked as processed")

    except Exception as e:
        logger.error(f"Error marking event processed {source}:{event_id}: {e}")


async def get_user_from_subscription(db: Client, subscription_id: str, source: str = 'stripe') -> Optional[str]:
    """
    Retrieve the user_id from a subscription_id.

    Args:
        db: Client Supabase
        subscription_id: ID of the subscription
        source: Source ('stripe' or 'whop')

    Returns:
        user_id or None if not found
    """
    try:
        result = db.table('subscriptions').select('user_id').eq('id', subscription_id).eq('source', source).single().execute()
        return result.data['user_id'] if result.data else None
    except Exception as e:
        logger.warning(f"Error retrieving user for subscription {subscription_id}: {e}")
        return None


async def get_user_from_customer(db: Client, customer_id: str, source: str = 'stripe') -> Optional[str]:
    """
    Retrieve the user_id from a customer_id.

    Args:
        db: Client Supabase
        customer_id: ID of the customer (stripe_customer_id)
        source: Source ('stripe')

    Returns:
        user_id or None if not found
    """
    try:
        if source == 'stripe':
            result = db.table('customers').select('id').eq('stripe_customer_id', customer_id).single().execute()
        else:
            return None

        return result.data['id'] if result.data else None
    except Exception as e:
        logger.warning(f"Error retrieving user for customer {customer_id}: {e}")
        return None


def is_webhook_signature_valid(payload: dict, signature: str, webhook_secret: str, source: str = 'stripe') -> bool:
    """
    Validate the signature of a webhook.

    Args:
        payload: Webhook payload
        signature: Received signature (X-Hub-Signature-256)
        webhook_secret: Secret for validation
        source: Source ('stripe' or 'whop')

    Returns:
        True if the signature is valid
    """
    try:
        if source == 'stripe':
            import stripe
            stripe.Webhook.construct_event(payload, signature, webhook_secret)
            return True

        elif source != 'stripe':
            logger.warning(f"Unknown source for signature validation: {source}")
            return False

    except Exception as e:
        logger.warning(f"Error validating signature {source}: {e}")
        return False


async def log_webhook_error(db: Client, event_id: str, event_type: str, error: str, source: str = 'stripe'):
    """
    Log a webhook processing error.

    Args:
        db: Client Supabase
        event_id: Event ID
        event_type: Event type
        error: Error message
        source: Source ('stripe' or 'whop')
    """
    try:
        logger.error(f"Webhook {source} error - {event_type} ({event_id}): {error}")

    except Exception as e:
        logger.error(f"Error logging webhook error: {e}")


# =====================================================
# Utility functions for tests
# =====================================================

async def cleanup_old_webhook_events(db: Client, days_old: int = 30) -> int:
    """
    Clean up old webhook events.

    Args:
        db: Client Supabase
        days_old: Number of days after which to delete

    Returns:
        Number of events deleted
    """
    try:
        from datetime import datetime, timedelta, timezone

        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_old)).isoformat()

        result = db.table('webhook_events').delete().lt('processed_at', cutoff_date).execute()

        deleted_count = len(result.data) if result.data else 0
        logger.info(f"Cleaned up {deleted_count} old webhook events")

        return deleted_count

    except Exception as e:
        logger.error(f"Error cleaning up webhook events: {e}")
        return 0


async def get_webhook_stats(db: Client, source: str = None, days: int = 7) -> dict:
    """
    Retrieve statistics on processed webhooks.

    Args:
        db: Client Supabase
        source: Filter by source ('stripe', 'whop', or None for all)
        days: Number of days to analyze

    Returns:
        Dictionary of statistics
    """
    try:
        from datetime import datetime, timedelta, timezone

        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        query = db.table('webhook_events').select('event_type, source').gte('processed_at', cutoff_date)

        if source:
            query = query.eq('source', source)

        result = query.execute()

        stats = {
            'total_events': len(result.data),
            'by_type': {},
            'by_source': {},
            'period_days': days
        }

        for event in result.data:
            event_type = event['event_type']
            stats['by_type'][event_type] = stats['by_type'].get(event_type, 0) + 1

            event_source = event['source']
            stats['by_source'][event_source] = stats['by_source'].get(event_source, 0) + 1

        return stats

    except Exception as e:
        logger.error(f"Error retrieving webhook stats: {e}")
        return {'error': str(e)}

