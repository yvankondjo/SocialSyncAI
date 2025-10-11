"""
Schemas Pydantic pour les modèles Stripe.

Ces schemas représentent les objets Stripe dans notre système,
adaptés pour l'architecture hybride.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# =====================================================
# Modèles de base Stripe
# =====================================================

class StripeProductBase(BaseModel):
    """Produit Stripe de base."""
    id: str = Field(..., description="ID Stripe du produit (prod_xxx)")
    active: bool = Field(True, description="Produit actif")
    name: str = Field(..., description="Nom du produit")
    description: Optional[str] = Field(None, description="Description du produit")
    image: Optional[str] = Field(None, description="URL de l'image")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées personnalisées")


class StripeProduct(StripeProductBase):
    """Produit Stripe complet."""
    created_at: Optional[datetime] = Field(None, description="Date de création")
    updated_at: Optional[datetime] = Field(None, description="Date de mise à jour")


class StripePriceBase(BaseModel):
    """Prix Stripe de base."""
    id: str = Field(..., description="ID Stripe du prix (price_xxx)")
    product_id: str = Field(..., description="ID du produit associé")
    active: bool = Field(True, description="Prix actif")
    description: Optional[str] = Field(None, description="Description du prix")
    unit_amount: int = Field(..., description="Montant en centimes")
    currency: str = Field("eur", description="Devise (ISO 4217)")
    type: str = Field(..., description="Type de prix (one_time, recurring)")
    interval: Optional[str] = Field(None, description="Intervalle pour récurrence")
    interval_count: int = Field(1, description="Nombre d'intervalles")
    trial_period_days: Optional[int] = Field(None, description="Période d'essai en jours")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées personnalisées")


class StripePrice(StripePriceBase):
    """Prix Stripe complet."""
    created_at: Optional[datetime] = Field(None, description="Date de création")
    updated_at: Optional[datetime] = Field(None, description="Date de mise à jour")


class StripeSubscriptionBase(BaseModel):
    """Abonnement Stripe de base."""
    id: str = Field(..., description="ID Stripe de l'abonnement (sub_xxx)")
    user_id: str = Field(..., description="ID de l'utilisateur")
    status: str = Field(..., description="Statut de l'abonnement")
    price_id: Optional[str] = Field(None, description="ID du prix actif")
    quantity: int = Field(1, description="Quantité")
    cancel_at_period_end: bool = Field(False, description="Annulé à la fin de période")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées")


class StripeSubscription(StripeSubscriptionBase):
    """Abonnement Stripe complet."""
    current_period_start: Optional[datetime] = Field(None, description="Début période actuelle")
    current_period_end: Optional[datetime] = Field(None, description="Fin période actuelle")
    trial_start: Optional[datetime] = Field(None, description="Début période d'essai")
    trial_end: Optional[datetime] = Field(None, description="Fin période d'essai")
    ended_at: Optional[datetime] = Field(None, description="Date de fin")
    cancel_at: Optional[datetime] = Field(None, description="Date d'annulation programmée")
    canceled_at: Optional[datetime] = Field(None, description="Date d'annulation effective")
    created_at: Optional[datetime] = Field(None, description="Date de création")
    updated_at: Optional[datetime] = Field(None, description="Date de mise à jour")


class StripeCustomerBase(BaseModel):
    """Client Stripe de base."""
    id: str = Field(..., description="ID utilisateur (auth.users)")
    stripe_customer_id: Optional[str] = Field(None, description="ID client Stripe (cus_xxx)")


class StripeCustomer(StripeCustomerBase):
    """Client Stripe complet."""
    created_at: Optional[datetime] = Field(None, description="Date de création")
    updated_at: Optional[datetime] = Field(None, description="Date de mise à jour")


# =====================================================
# Modèles pour les webhooks
# =====================================================

class StripeWebhookEvent(BaseModel):
    """Événement webhook Stripe."""
    id: str = Field(..., description="ID de l'événement")
    type: str = Field(..., description="Type d'événement")
    data: Dict[str, Any] = Field(..., description="Données de l'événement")
    created: int = Field(..., description="Timestamp de création")


class WebhookEventRecord(BaseModel):
    """Enregistrement d'événement webhook dans notre DB."""
    id: str = Field(..., description="ID unique")
    stripe_event_id: Optional[str] = Field(None, description="ID événement Stripe")
    whop_event_id: Optional[str] = Field(None, description="ID événement Whop")
    event_type: str = Field(..., description="Type d'événement")
    source: str = Field(..., description="Source (stripe/whop)")
    processed_at: datetime = Field(..., description="Date de traitement")
    payload: Dict[str, Any] = Field(..., description="Payload complet")


# =====================================================
# Modèles pour les sessions checkout
# =====================================================

class CheckoutSessionRequest(BaseModel):
    """Requête de création de session checkout."""
    price_id: str = Field(..., description="ID du prix Stripe")
    success_url: Optional[str] = Field(None, description="URL de succès")
    cancel_url: Optional[str] = Field(None, description="URL d'annulation")


class CheckoutSessionResponse(BaseModel):
    """Réponse de création de session checkout."""
    success: bool = Field(True, description="Succès de l'opération")
    checkout_url: str = Field(..., description="URL de checkout Stripe")
    session_id: str = Field(..., description="ID de la session")
    price_id: str = Field(..., description="ID du prix")
    customer_id: Optional[str] = Field(None, description="ID du client Stripe")


# =====================================================
# Modèles pour la configuration des plans
# =====================================================

class PlanConfiguration(BaseModel):
    """Configuration d'un plan d'abonnement."""
    name: str = Field(..., description="Nom du plan")
    description: str = Field(..., description="Description marketing")
    price_eur: float = Field(..., gt=0, description="Prix en euros")
    credits_monthly: int = Field(..., gt=0, description="Crédits par mois")
    max_ai_calls_per_batch: int = Field(3, gt=0, description="Appels AI max par batch")
    storage_quota_mb: int = Field(10, gt=0, description="Quota stockage en MB")
    features: Dict[str, bool] = Field(..., description="Fonctionnalités disponibles")
    trial_duration_days: int = Field(7, ge=0, description="Durée essai en jours")


# =====================================================
# Modèles de réponse API
# =====================================================

class StripeConfig(BaseModel):
    """Configuration Stripe pour le frontend."""
    publishable_key: str = Field(..., description="Clé publique Stripe")
    prices: List[StripePrice] = Field(default_factory=list, description="Liste des prix disponibles")


class SubscriptionStatusResponse(BaseModel):
    """Réponse de statut d'abonnement."""
    active: bool = Field(..., description="Abonnement actif")
    status: str = Field(..., description="Statut détaillé")
    current_period_end: Optional[datetime] = Field(None, description="Fin de période actuelle")
    cancel_at_period_end: bool = Field(False, description="Annulé en fin de période")


# =====================================================
# Modèles pour les erreurs
# =====================================================

class StripeError(BaseModel):
    """Erreur Stripe."""
    type: str = Field(..., description="Type d'erreur")
    message: str = Field(..., description="Message d'erreur")
    code: Optional[str] = Field(None, description="Code d'erreur Stripe")


class WebhookError(BaseModel):
    """Erreur de traitement webhook."""
    event_id: str = Field(..., description="ID de l'événement")
    event_type: str = Field(..., description="Type d'événement")
    error: str = Field(..., description="Message d'erreur")
    source: str = Field(..., description="Source (stripe/whop)")


# =====================================================
# Configuration et enums
# =====================================================

class StripeEventType(str):
    """Types d'événements Stripe supportés."""
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"
    PRICE_CREATED = "price.created"
    PRICE_UPDATED = "price.updated"
    PRICE_DELETED = "price.deleted"
    SUBSCRIPTION_CREATED = "customer.subscription.created"
    SUBSCRIPTION_UPDATED = "customer.subscription.updated"
    SUBSCRIPTION_DELETED = "customer.subscription.deleted"
    PAYMENT_SUCCEEDED = "invoice.payment_succeeded"
    PAYMENT_FAILED = "invoice.payment_failed"
    CHECKOUT_COMPLETED = "checkout.session.completed"


class WhopEventType(str):
    """Types d'événements Whop supportés."""
    MEMBERSHIP_CREATED = "membership.created"
    MEMBERSHIP_RENEWED = "membership.renewed"
    MEMBERSHIP_CANCELLED = "membership.cancelled"
    MEMBERSHIP_EXPIRED = "membership.expired"


class SubscriptionStatus(str):
    """Statuts d'abonnement."""
    TRIALING = "trialing"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    PAUSED = "paused"


# =====================================================
# Utilitaires de conversion
# =====================================================

def stripe_product_to_model(stripe_product: Dict[str, Any]) -> StripeProduct:
    """Convertit un objet Stripe Product en modèle Pydantic."""
    return StripeProduct(
        id=stripe_product['id'],
        active=stripe_product.get('active', True),
        name=stripe_product['name'],
        description=stripe_product.get('description'),
        image=stripe_product.get('images', [None])[0] if stripe_product.get('images') else None,
        metadata=stripe_product.get('metadata', {})
    )


def stripe_price_to_model(stripe_price: Dict[str, Any]) -> StripePrice:
    """Convertit un objet Stripe Price en modèle Pydantic."""
    return StripePrice(
        id=stripe_price['id'],
        product_id=stripe_price['product'],
        active=stripe_price.get('active', True),
        unit_amount=stripe_price['unit_amount'],
        currency=stripe_price['currency'],
        type=stripe_price['type'],
        interval=stripe_price.get('recurring', {}).get('interval'),
        interval_count=stripe_price.get('recurring', {}).get('interval_count', 1),
        trial_period_days=stripe_price.get('recurring', {}).get('trial_period_days'),
        metadata=stripe_price.get('metadata', {})
    )


def stripe_subscription_to_model(stripe_subscription: Dict[str, Any], user_id: str) -> StripeSubscription:
    """Convertit un objet Stripe Subscription en modèle Pydantic."""
    from datetime import datetime, timezone

    return StripeSubscription(
        id=stripe_subscription['id'],
        user_id=user_id,
        status=stripe_subscription['status'],
        price_id=stripe_subscription['items']['data'][0]['price']['id'] if stripe_subscription.get('items', {}).get('data') else None,
        quantity=stripe_subscription['items']['data'][0]['quantity'] if stripe_subscription.get('items', {}).get('data') else 1,
        cancel_at_period_end=stripe_subscription.get('cancel_at_period_end', False),
        current_period_start=datetime.fromtimestamp(stripe_subscription['current_period_start'], tz=timezone.utc),
        current_period_end=datetime.fromtimestamp(stripe_subscription['current_period_end'], tz=timezone.utc),
        trial_start=datetime.fromtimestamp(stripe_subscription['trial_start'], tz=timezone.utc) if stripe_subscription.get('trial_start') else None,
        trial_end=datetime.fromtimestamp(stripe_subscription['trial_end'], tz=timezone.utc) if stripe_subscription.get('trial_end') else None,
        ended_at=datetime.fromtimestamp(stripe_subscription['ended_at'], tz=timezone.utc) if stripe_subscription.get('ended_at') else None,
        cancel_at=datetime.fromtimestamp(stripe_subscription['cancel_at'], tz=timezone.utc) if stripe_subscription.get('cancel_at') else None,
        canceled_at=datetime.fromtimestamp(stripe_subscription['canceled_at'], tz=timezone.utc) if stripe_subscription.get('canceled_at') else None,
        metadata=stripe_subscription.get('metadata', {})
    )

