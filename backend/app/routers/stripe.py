import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from supabase import Client
from app.services.stripe_service import StripeService, get_stripe_service
from app.db.session import get_db
from app.services.credits_service import CreditsService, get_credits_service
from app.core.security import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/stripe",
    tags=["stripe"]
)




# =====================================================
# Endpoints pour les sessions de checkout
# =====================================================

@router.post("/create-checkout-session", response_model=None)
async def create_checkout_session(
    request: Dict[str, Any],  # Accepter le body JSON
    stripe_service: StripeService = Depends(get_stripe_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Crée une session de checkout Stripe pour un abonnement.

    NOUVELLE LOGIQUE:
    - Utilise price_id directement (au lieu de plan_id)
    - price_id pointe vers un prix Stripe existant

    Args:
        price_id: ID du prix Stripe (price_xxx)
        success_url: URL de redirection en cas de succès (optionnel)
        cancel_url: URL de redirection en cas d'annulation (optionnel)

    Returns:
        Dictionnaire contenant l'URL de checkout Stripe
    """
    try:
        # Extraire les paramètres du body JSON
        price_id = request.get('price_id')
        success_url = request.get('success_url')
        cancel_url = request.get('cancel_url')

        if not price_id:
            raise HTTPException(status_code=422, detail="price_id is required")

        session_data = await stripe_service.create_checkout_session(
            user_id=current_user_id,
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url
        )

        return {
            'success': True,
            'checkout_url': session_data['checkout_url'],
            'session_id': session_data['session_id'],
            'price_id': price_id,
            'customer_id': session_data.get('customer_id')
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur création session checkout pour {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur création session de paiement")


# =====================================================
# Endpoint pour les webhooks Stripe
# =====================================================

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    stripe_service: StripeService = Depends(get_stripe_service),
    credits_service: CreditsService = Depends(get_credits_service)
):
    """
    Endpoint pour recevoir les webhooks Stripe.

    Ce endpoint doit être configuré dans le dashboard Stripe avec l'URL complète:
    https://votredomaine.com/api/stripe/webhook

    Les événements gérés:
    - checkout.session.completed: Paiement réussi pour nouvel abonnement
    - invoice.payment_succeeded: Paiement récurrent réussi
    - invoice.payment_failed: Paiement échoué
    - customer.subscription.updated: Changement de statut d'abonnement
    - customer.subscription.deleted: Annulation d'abonnement
    """
    try:
        # Lire le payload brut
        payload = await request.body()

        # Traiter le webhook
        result = await stripe_service.handle_webhook(payload, stripe_signature)

        # Log du traitement réussi
        logger.info(f"Webhook traité avec succès: {result.get('event_type')} - {result.get('event_id')}")

        # Stripe attend un status code 200 pour confirmer la réception
        return {"received": True, "processed": result.get('processed', False)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur traitement webhook: {e}")
        # Ne pas lever d'exception pour éviter que Stripe retry le webhook
        return {"received": True, "error": str(e)}


# =====================================================
# Endpoints de gestion d'abonnement
# =====================================================

@router.post("/cancel-subscription", response_model=None)
async def cancel_subscription(
    stripe_service: StripeService = Depends(get_stripe_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Annule l'abonnement actif de l'utilisateur.

    L'annulation prendra effet à la fin de la période de facturation en cours.
    """
    try:
        result = await stripe_service.cancel_subscription(current_user_id)

        return {
            'success': True,
            'message': 'Abonnement annulé avec succès',
            'cancel_at': result['cancel_at'],
            'current_period_end': result['current_period_end'],
            'subscription_id': result['subscription_id']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur annulation abonnement pour {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur annulation abonnement")


# =====================================================
# Endpoints d'information (pour le frontend)
# =====================================================

@router.get("/config", response_model=Dict[str, str])
async def get_stripe_config():
    """
    Retourne la configuration publique Stripe pour le frontend.

    Le publishable key peut être exposé au frontend pour créer des éléments Stripe.
    """
    from app.core.config import get_settings
    settings = get_settings()

    # Ne retourner que les clés publiques
    return {
        'publishable_key': settings.STRIPE_PUBLISHABLE_KEY or '',
        'enabled': bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET)
    }




# =====================================================
# Endpoints pour les sessions de checkout
# =====================================================
