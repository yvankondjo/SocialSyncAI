"""Webhook helpers with idempotency.

Utilities to avoid duplicate processing of Stripe/Whop webhooks using
the webhook_events table.
"""

import logging
from typing import Optional
from supabase import Client

logger = logging.getLogger(__name__)


async def check_event_processed(
    db: Client,
    stripe_event_id: str = None,
) -> bool:
    """
    Check whether a webhook event has already been processed.

    Args:
        db: Supabase client
        stripe_event_id: Stripe event ID (required)

    Returns:
        True if the event was already processed, False otherwise.
    """
    try:
        query = db.table('webhook_events')

        if stripe_event_id:
            result = query.select('id').eq('stripe_event_id', stripe_event_id).execute()
        else:
            logger.warning("No event_id provided for idempotency check")
            return False

        return len(result.data) > 0

    except Exception as e:
        logger.warning(f"Idempotency check error: {e}")
        # On error, assume the event was not processed to avoid losing important events.
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
        db: Supabase client
        event_id: Event ID
        event_type: Event type (e.g. 'customer.subscription.created')
        payload: Full webhook payload
        source: Source ('stripe')
    """
    try:
        # Validate parameters
        if source != 'stripe':
            raise ValueError(f"Source invalide: {source}")

        event_data = {
            'event_type': event_type,
            'source': source,
            'payload': payload
        }

        # Add ID based on source
        event_data['stripe_event_id'] = event_id

        # Insert into table
        db.table('webhook_events').insert(event_data).execute()

        logger.debug(f"Event {source}:{event_id} marked as processed")

    except Exception as e:
        logger.error(f"Error marking event processed {source}:{event_id}: {e}")
        # Do not raise to avoid breaking webhook handling. The webhook may be retried.


async def get_user_from_subscription(db: Client, subscription_id: str, source: str = 'stripe') -> Optional[str]:
    """
    Get user_id from a subscription_id.

    Args:
        db: Supabase client
        subscription_id: Subscription ID
        source: Source ('stripe' or 'whop')

    Returns:
        user_id, or None if not found
    """
    try:
        result = db.table('subscriptions').select('user_id').eq('id', subscription_id).eq('source', source).single().execute()
        return result.data['user_id'] if result.data else None
    except Exception as e:
        logger.warning(f"Error getting user for subscription {subscription_id}: {e}")
        return None


async def get_user_from_customer(db: Client, customer_id: str, source: str = 'stripe') -> Optional[str]:
    """
    Get user_id from a customer_id.

    Args:
        db: Supabase client
        customer_id: Customer ID (stripe_customer_id)
        source: Source ('stripe')

    Returns:
        user_id, or None if not found
    """
    try:
        if source == 'stripe':
            result = db.table('customers').select('id').eq('stripe_customer_id', customer_id).single().execute()
        else:
            return None

        return result.data['id'] if result.data else None
    except Exception as e:
        logger.warning(f"Error getting user for customer {customer_id}: {e}")
        return None


def is_webhook_signature_valid(payload: dict, signature: str, webhook_secret: str, source: str = 'stripe') -> bool:
    """
    Validate a webhook signature.

    Args:
        payload: Webhook payload
        signature: Received signature
        webhook_secret: Validation secret
        source: Source ('stripe' or 'whop')

    Returns:
        True if the signature is valid
    """
    try:
        if source == 'stripe':
            # Validation Stripe
            import stripe
            stripe.Webhook.construct_event(payload, signature, webhook_secret)
            return True

        elif source != 'stripe':
            logger.warning(f"Unknown source for signature validation: {source}")
            return False

    except Exception as e:
        logger.warning(f"Signature validation error ({source}): {e}")
        return False


async def log_webhook_error(db: Client, event_id: str, event_type: str, error: str, source: str = 'stripe'):
    """
    Log a webhook processing error.

    Args:
        db: Client Supabase
        event_id: ID de l'événement
        event_type: Type d'événement
        error: Message d'erreur
        source: Source ('stripe' ou 'whop')
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
    Cleanup old processed webhook events.

    Args:
        db: Client Supabase
        days_old: Nombre de jours après lesquels supprimer

    Returns:
        Nombre d'événements supprimés
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
    Get stats about processed webhooks.

    Args:
        db: Client Supabase
        source: Filter by source ('stripe', 'whop', or None for all)
        days: Number of days to analyze

    Returns:
        Stats dictionary
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
            # Par type d'événement
            event_type = event['event_type']
            stats['by_type'][event_type] = stats['by_type'].get(event_type, 0) + 1

            # Par source
            event_source = event['source']
            stats['by_source'][event_source] = stats['by_source'].get(event_source, 0) + 1

        return stats

    except Exception as e:
        logger.error(f"Erreur récupération stats webhooks: {e}")
        return {'error': str(e)}

