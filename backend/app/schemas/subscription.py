from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Any
from datetime import datetime
from enum import Enum


class TransactionType(str, Enum):
    DEDUCTION = "deduction"
    REFUND = "refund"
    PURCHASE = "purchase"
    MONTHLY_RESET = "monthly_reset"
    TRIAL_GRANT = "trial_grant"
    BONUS = "bonus"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"
    TRIALING = "trialing"



class AIModelBase(BaseModel):
    name: str = Field(..., description="Nom d'affichage du modèle")
    provider: str = Field(..., description="Provider du modèle (openai, anthropic, etc.)")
    openrouter_id: str = Field(..., description="ID exact du modèle dans OpenRouter")
    logo_key: Optional[str] = Field(None, description="Nom du fichier logo (ex: openai-logo.svg)")
    description: Optional[str] = Field(None, description="Description marketing du modèle")
    credit_cost: float = Field(..., gt=0, description="Coût en crédits par appel")
    model_type: str = Field("fast", description="Type de modèle: fast, advanced, affordable")
    supports_text: bool = Field(True, description="Support du texte")
    supports_images: bool = Field(False, description="Support des images")
    supports_audio: bool = Field(False, description="Support de l'audio")
    max_context_tokens: Optional[int] = Field(None, description="Tokens maximum de contexte")
    is_active: bool = Field(True, description="Modèle actif")


class AIModelCreate(AIModelBase):
    pass


class AIModelUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    openrouter_id: Optional[str] = None
    logo_key: Optional[str] = None
    description: Optional[str] = None
    credit_cost: Optional[float] = Field(None, gt=0)
    supports_text: Optional[bool] = None
    supports_images: Optional[bool] = None
    supports_audio: Optional[bool] = None
    max_context_tokens: Optional[int] = None
    is_active: Optional[bool] = None


class AIModel(AIModelBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# Schémas pour les plans d'abonnement
# =====================================================

class SubscriptionPlanBase(BaseModel):
    name: str = Field(..., description="Nom du plan")
    price_eur: float = Field(..., ge=0, description="Prix en euros")
    credits_included: int = Field(..., gt=0, description="Crédits inclus par période")
    max_ai_calls_per_batch: int = Field(3, gt=0, description="Nombre maximum d'appels AI par batch")
    trial_duration_days: Optional[int] = Field(None, gt=0, description="Durée de l'essai en jours")
    storage_quota_mb: int = Field(10, gt=0, description="Quota de stockage en MB")
    features: Dict[str, bool] = Field(
        default_factory=lambda: {"text": True, "images": False, "audio": False},
        description="Fonctionnalités disponibles"
    )
    stripe_price_id: Optional[str] = Field(None, description="ID du prix Stripe")
    whop_product_id: Optional[str] = Field(None, description="ID du produit Whop")
    is_active: bool = Field(True, description="Plan actif")
    is_trial: bool = Field(False, description="Plan d'essai gratuit")


class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass


class SubscriptionPlanUpdate(BaseModel):
    name: Optional[str] = None
    price_eur: Optional[float] = Field(None, ge=0)
    credits_included: Optional[int] = Field(None, gt=0)
    max_ai_calls_per_batch: Optional[int] = Field(None, gt=0)
    trial_duration_days: Optional[int] = Field(None, gt=0)
    features: Optional[Dict[str, bool]] = None
    stripe_price_id: Optional[str] = None
    whop_product_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_trial: Optional[bool] = None


class SubscriptionPlan(SubscriptionPlanBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# Schémas pour les abonnements utilisateur
# =====================================================

class UserSubscriptionBase(BaseModel):
    plan_id: Optional[str] = Field(None, description="ID du plan d'abonnement (deprecated)")
    credits_balance: int = Field(0, ge=0, description="Solde actuel de crédits")
    credits_used_this_month: int = Field(0, ge=0, description="Crédits utilisés ce mois")
    storage_used_mb: float = Field(0, ge=0, description="Stockage utilisé en MB")
    subscription_status: SubscriptionStatus = Field(SubscriptionStatus.ACTIVE, description="Statut de l'abonnement")
    stripe_subscription_id: Optional[str] = Field(None, description="ID abonnement Stripe")
    whop_subscription_id: Optional[str] = Field(None, description="ID abonnement Whop")
    current_period_start: Optional[datetime] = Field(None, description="Début période actuelle")
    current_period_end: Optional[datetime] = Field(None, description="Fin période actuelle")
    trial_end: Optional[datetime] = Field(None, description="Fin période d'essai")


class UserSubscriptionCreate(UserSubscriptionBase):
    user_id: str = Field(..., description="ID de l'utilisateur")


class UserSubscriptionUpdate(BaseModel):
    plan_id: Optional[str] = None
    credits_balance: Optional[int] = Field(None, ge=0)
    credits_used_this_month: Optional[int] = Field(None, ge=0)
    storage_used_mb: Optional[float] = Field(None, ge=0)
    subscription_status: Optional[SubscriptionStatus] = None
    stripe_subscription_id: Optional[str] = None
    whop_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    trial_end: Optional[datetime] = None


class UserSubscription(UserSubscriptionBase):
    id: str
    user_id: str
    plan: SubscriptionPlan
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# Schémas pour les transactions de crédits
# =====================================================

class CreditTransactionBase(BaseModel):
    transaction_type: TransactionType
    credits_amount: int = Field(..., description="Montant des crédits (+ pour ajout, - pour déduction)")
    credits_balance_after: int = Field(..., ge=0, description="Solde après transaction")
    reason: str = Field(..., description="Raison de la transaction")
    metadata: Dict = Field(default_factory=dict, description="Métadonnées supplémentaires")


class CreditTransactionCreate(CreditTransactionBase):
    user_id: str = Field(..., description="ID de l'utilisateur")


class CreditTransaction(CreditTransactionBase):
    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# Schémas de réponse API
# =====================================================

class CreditsBalance(BaseModel):
    balance: int = Field(..., description="Solde actuel de crédits")
    used_this_month: int = Field(..., description="Crédits utilisés ce mois")
    plan_limit: int = Field(..., description="Limite du plan actuel")
    percentage_used: float = Field(..., ge=0, le=100, description="Pourcentage utilisé")


class SubscriptionWithPlan(BaseModel):
    subscription: UserSubscription
    can_upgrade: bool = Field(True, description="Peut passer à un plan supérieur")
    days_until_renewal: Optional[int] = Field(None, description="Jours avant renouvellement")
    trial_days_remaining: Optional[int] = Field(None, description="Jours restants d'essai")


class FeatureAccess(BaseModel):
    text: bool = Field(True, description="Accès au traitement texte")
    images: bool = Field(False, description="Accès au traitement images")
    audio: bool = Field(False, description="Accès au traitement audio")
    max_calls_per_batch: int = Field(3, description="Nombre maximum d'appels par batch")




class InsufficientCreditsError(BaseModel):
    error: str = "insufficient_credits"
    required: int = Field(..., description="Crédits requis")
    available: int = Field(..., description="Crédits disponibles")
    message: str = Field(..., description="Message d'erreur")


class FeatureNotAllowedError(BaseModel):
    error: str = "feature_not_allowed"
    feature: str = Field(..., description="Fonctionnalité demandée")
    current_plan: str = Field(..., description="Plan actuel")
    message: str = Field(..., description="Message d'erreur")


class SubscriptionRequiredError(BaseModel):
    error: str = "subscription_required"
    message: str = Field("Un abonnement actif est requis pour utiliser cette fonctionnalité", description="Message d'erreur")



class StorageUsage(BaseModel):
    used_mb: float = Field(..., description="Stockage utilisé en MB")
    quota_mb: int = Field(..., description="Quota total en MB")
    available_mb: float = Field(..., description="Espace disponible en MB")
    percentage_used: float = Field(..., ge=0, le=100, description="Pourcentage utilisé")
    is_full: bool = Field(..., description="Quota atteint")


class StorageQuotaExceededError(BaseModel):
    error: str = "storage_quota_exceeded"
    message: str = Field(..., description="Message d'erreur")
    used_mb: float = Field(..., description="Stockage utilisé en MB")
    quota_mb: int = Field(..., description="Quota total en MB")
    required_mb: float = Field(..., description="Taille requise en MB")


class PriceMetadata(BaseModel):
    plan_name: Optional[str] = None
    credits_monthly: Optional[int] = None
    max_ai_calls_per_batch: Optional[int] = None
    storage_quota_mb: Optional[int] = None
    features: Dict[str, bool] = Field(default_factory=dict)
    is_trial_eligible: Optional[bool] = None
    # Champs additionnels pour compatibilité
    fallback: Optional[bool] = None
    migrated_from: Optional[str] = None
    trial_days: Optional[str] = None


class ProductMetadata(BaseModel):
    plan_name: Optional[str] = None
    credits_monthly: Optional[int] = None
    max_ai_calls_per_batch: Optional[int] = None
    storage_quota_mb: Optional[int] = None
    features: Dict[str, bool] = Field(default_factory=dict)
    is_trial_eligible: Optional[bool] = None
    supports_images: Optional[bool] = None
    supports_audio: Optional[bool] = None
    tier: Optional[str] = None


class Price(BaseModel):
    id: str
    product_id: str
    active: bool
    description: Optional[str] = None
    unit_amount: int
    currency: str
    type: str
    interval: Optional[str] = None
    interval_count: Optional[int] = None
    trial_period_days: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Product(BaseModel):
    id: str
    active: bool
    name: str
    description: Optional[str] = None
    image: Optional[str] = None
    metadata: Dict[str, Optional[str]] = Field(default_factory=dict)
    source: str
    prices: List[Price] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubscriptionPlanExpanded(SubscriptionPlan):
    product: Optional[Product] = None
    prices: List[Price] = Field(default_factory=list)


class PublicPlan(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price: float
    currency: str
    interval: str
    interval_count: int
    features: Dict[str, bool]
    credits_monthly: int
    max_ai_calls_per_batch: int
    storage_quota_mb: int
    trial_duration_days: Optional[int] = None
    source: str
    stripe_price_id: Optional[str] = None
    whop_product_id: Optional[str] = None


class SubscriptionListResponse(BaseModel):
    plans: List[SubscriptionPlanExpanded]
    last_updated: datetime


class PublicPricingResponse(BaseModel):
    plans: List[PublicPlan]
    stripe_enabled: bool = False
    whop_enabled: bool = False
    currency: str = "eur"
    updated_at: datetime
