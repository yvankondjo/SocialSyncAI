"""
Helpers pour la gestion des webhooks avec idempotence.

Ce module fournit des utilitaires pour éviter le traitement dupliqué
des webhooks Stripe et Whop en utilisant la table webhook_events.
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
    Vérifie si un événement webhook a déjà été traité.

    Args:
        db: Client Supabase
        stripe_event_id: ID d'événement Stripe (requis)

    Returns:
        True si l'événement a déjà été traité, False sinon
    """
    try:
        query = db.table('webhook_events')

        if stripe_event_id:
            result = query.select('id').eq('stripe_event_id', stripe_event_id).execute()
        else:
            logger.warning("Aucun event_id fourni pour vérification idempotence")
            return False

        return len(result.data) > 0

    except Exception as e:
        logger.warning(f"Erreur vérification idempotence: {e}")
        # En cas d'erreur, on considère que l'événement n'a pas été traité
        # pour éviter de perdre des événements importants
        return False


async def mark_event_processed(
    db: Client,
    event_id: str,
    event_type: str,
    payload: dict,
    source: str = 'stripe'
) -> None:
    """
    Marque un événement webhook comme traité.

    Args:
        db: Client Supabase
        event_id: ID de l'événement
        event_type: Type d'événement (ex: 'customer.subscription.created')
        payload: Payload complet du webhook
        source: Source ('stripe' ou 'whop')
    """
    try:
        # Valider les paramètres
        if source != 'stripe':
            raise ValueError(f"Source invalide: {source}")

        event_data = {
            'event_type': event_type,
            'source': source,
            'payload': payload
        }

        # Ajouter l'ID selon la source
        event_data['stripe_event_id'] = event_id

        # Insérer dans la table
        db.table('webhook_events').insert(event_data).execute()

        logger.debug(f"Événement {source}:{event_id} marqué comme traité")

    except Exception as e:
        logger.error(f"Erreur marquage événement traité {source}:{event_id}: {e}")
        # Ne pas lever d'exception pour ne pas casser le traitement du webhook
        # Le webhook sera retraité mais c'est acceptable


async def get_user_from_subscription(db: Client, subscription_id: str, source: str = 'stripe') -> Optional[str]:
    """
    Récupère l'user_id depuis un subscription_id.

    Args:
        db: Client Supabase
        subscription_id: ID de l'abonnement
        source: Source ('stripe' ou 'whop')

    Returns:
        user_id ou None si non trouvé
    """
    try:
        result = db.table('subscriptions').select('user_id').eq('id', subscription_id).eq('source', source).single().execute()
        return result.data['user_id'] if result.data else None
    except Exception as e:
        logger.warning(f"Erreur récupération user pour subscription {subscription_id}: {e}")
        return None


async def get_user_from_customer(db: Client, customer_id: str, source: str = 'stripe') -> Optional[str]:
    """
    Récupère l'user_id depuis un customer_id.

    Args:
        db: Client Supabase
        customer_id: ID du customer (stripe_customer_id)
        source: Source ('stripe')

    Returns:
        user_id ou None si non trouvé
    """
    try:
        if source == 'stripe':
            result = db.table('customers').select('id').eq('stripe_customer_id', customer_id).single().execute()
        else:
            return None

        return result.data['id'] if result.data else None
    except Exception as e:
        logger.warning(f"Erreur récupération user pour customer {customer_id}: {e}")
        return None


def is_webhook_signature_valid(payload: dict, signature: str, webhook_secret: str, source: str = 'stripe') -> bool:
    """
    Valide la signature d'un webhook.

    Args:
        payload: Payload du webhook
        signature: Signature reçue
        webhook_secret: Secret pour validation
        source: Source ('stripe' ou 'whop')

    Returns:
        True si la signature est valide
    """
    try:
        if source == 'stripe':
            # Validation Stripe
            import stripe
            stripe.Webhook.construct_event(payload, signature, webhook_secret)
            return True

        elif source != 'stripe':
            logger.warning(f"Source inconnue pour validation signature: {source}")
            return False

    except Exception as e:
        logger.warning(f"Erreur validation signature {source}: {e}")
        return False


async def log_webhook_error(db: Client, event_id: str, event_type: str, error: str, source: str = 'stripe'):
    """
    Log une erreur de traitement webhook.

    Args:
        db: Client Supabase
        event_id: ID de l'événement
        event_type: Type d'événement
        error: Message d'erreur
        source: Source ('stripe' ou 'whop')
    """
    try:
        # Pour l'instant, on log juste. Plus tard, on pourrait créer une table dédiée
        logger.error(f"Webhook {source} error - {event_type} ({event_id}): {error}")

        # Optionnellement, marquer quand même comme traité pour éviter les retraits
        # Cela dépend de la stratégie de gestion d'erreur souhaitée

    except Exception as e:
        logger.error(f"Erreur logging webhook error: {e}")


# =====================================================
# Fonctions utilitaires pour les tests
# =====================================================

async def cleanup_old_webhook_events(db: Client, days_old: int = 30) -> int:
    """
    Nettoie les anciens événements webhook traités.

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
        logger.info(f"Nettoyé {deleted_count} anciens événements webhook")

        return deleted_count

    except Exception as e:
        logger.error(f"Erreur nettoyage webhook events: {e}")
        return 0


async def get_webhook_stats(db: Client, source: str = None, days: int = 7) -> dict:
    """
    Récupère des statistiques sur les webhooks traités.

    Args:
        db: Client Supabase
        source: Filtrer par source ('stripe', 'whop', ou None pour tous)
        days: Nombre de jours à analyser

    Returns:
        Dictionnaire de statistiques
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

