import logging
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException

from supabase import Client
from app.db.session import get_db, get_authenticated_db
from app.core.security import get_current_user_id
from app.services.credits_service import CreditsService, get_credits_service
from app.services.storage_service import get_storage_service
from app.schemas.subscription import (
    SubscriptionPlan, SubscriptionPlanExpanded, UserSubscription, CreditTransaction,
    CreditsBalance, FeatureAccess, SubscriptionWithPlan, StorageUsage,
    PublicPricingResponse, PublicPlan
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/subscriptions",
    tags=["subscriptions"]
)


def _parse_metadata(raw_metadata) -> dict:
    if not raw_metadata:
        return {}
    if isinstance(raw_metadata, dict):
        return raw_metadata
    try:
        return json.loads(raw_metadata)
    except Exception:
        return {}


def _select_primary_price(prices: List[dict]) -> Optional[dict]:
    if not prices:
        return None
    recurring_prices = [p for p in prices if (p.get('type') or '').lower() == 'recurring']
    monthly_prices = [p for p in recurring_prices if (p.get('interval') or '').lower() == 'month']
    if monthly_prices:
        return monthly_prices[0]
    if recurring_prices:
        return recurring_prices[0]
    return prices[0]


def _safe_int(value, default: Optional[int] = None) -> Optional[int]:
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _build_subscription_plan(product: dict, price: dict) -> SubscriptionPlan:
    metadata = _parse_metadata(product.get('metadata'))
    price_metadata = _parse_metadata(price.get('metadata'))

    features = metadata.get('features') or price_metadata.get('features') or {
        "text": True,
        "images": False,
        "audio": False,
    }
    if isinstance(features, str):
        try:
            features = json.loads(features)
        except Exception:
            features = {"text": True, "images": False, "audio": False}

    trial_days = metadata.get('trial_duration_days') or price_metadata.get('trial_period_days') or price.get('trial_period_days')

    return SubscriptionPlan(
        id=product['id'],
        name=product.get('name', 'Plan'),
        price_eur=(price.get('unit_amount') or 0) / 100,
        credits_included=_safe_int(metadata.get('credits_monthly') or price_metadata.get('credits_monthly'), 0),
        max_ai_calls_per_batch=_safe_int(metadata.get('max_ai_calls_per_batch') or price_metadata.get('max_ai_calls_per_batch'), 3),
        trial_duration_days=_safe_int(trial_days),
        storage_quota_mb=_safe_int(metadata.get('storage_quota_mb') or price_metadata.get('storage_quota_mb'), 10),
        features=features,
        stripe_price_id=price['id'] if product.get('source') == 'stripe' else None,
        whop_product_id=product['id'] if product.get('source') == 'whop' else None,
        is_active=product.get('active', True),
        is_trial=str(metadata.get('is_trial_eligible', 'false')).lower() == 'true',
        created_at=product.get('created_at'),
        updated_at=product.get('updated_at')
    )


# =====================================================
# Endpoints pour les plans d'abonnement
# =====================================================

@router.get("/plans", response_model=List[SubscriptionPlanExpanded])
async def get_subscription_plans(db: Client = Depends(get_db)):
    """Récupère la liste complète des plans (produit + prix)."""
    try:
        result = db.table('products').select('*, prices(*)').eq('active', True).execute()

        plans: List[SubscriptionPlanExpanded] = []
        for product in result.data:
            prices = product.get('prices') or []
            primary_price = _select_primary_price(prices)

            if not primary_price:
                continue

            plan_base = _build_subscription_plan(product, primary_price)

            price_schemas: List[dict] = []
            for raw_price in prices:
                price_schemas.append(
                    {
                        "id": raw_price.get('id'),
                        "product_id": raw_price.get('product_id'),
                        "active": raw_price.get('active', True),
                        "description": raw_price.get('description'),
                        "unit_amount": raw_price.get('unit_amount'),
                        "currency": raw_price.get('currency', 'eur'),
                        "type": raw_price.get('type', 'recurring'),
                        "interval": raw_price.get('interval'),
                        "interval_count": raw_price.get('interval_count'),
                        "trial_period_days": raw_price.get('trial_period_days'),
                        "metadata": _parse_metadata(raw_price.get('metadata')),
                        "created_at": raw_price.get('created_at'),
                        "updated_at": raw_price.get('updated_at')
                    }
                )

            plan_product = {
                "id": product.get('id'),
                "active": product.get('active', True),
                "name": product.get('name'),
                "description": product.get('description'),
                "image": product.get('image'),
                "metadata": _parse_metadata(product.get('metadata')),
                "source": product.get('source', 'stripe'),
                "prices": price_schemas,
                "created_at": product.get('created_at'),
                "updated_at": product.get('updated_at')
            }

            plans.append(
                SubscriptionPlanExpanded(
                    **plan_base.dict(),
                    product=plan_product,
                    prices=price_schemas
                )
            )

        plans.sort(key=lambda p: p.price_eur)

        return plans

    except Exception as e:
        logger.error(f"Erreur récupération plans: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération plans d'abonnement")


@router.get("/plans/{plan_id}", response_model=SubscriptionPlanExpanded)
async def get_subscription_plan(plan_id: str, db: Client = Depends(get_db)):
    """
    Récupère les détails d'un plan spécifique.

    NOUVELLE LOGIQUE:
    - Cherche dans products + prices
    - plan_id peut être un product_id (Stripe/Whop)
    """
    try:
        # Chercher le produit par ID
        result = db.table('products').select(
            '*, prices(*)'
        ).eq('id', plan_id).eq('active', True).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Plan non trouvé")

        product = result.data
        prices = product.get('prices') or []
        primary_price = _select_primary_price(prices)

        if not primary_price:
            raise HTTPException(status_code=404, detail="Prix non trouvé pour ce plan")

        plan_base = _build_subscription_plan(product, primary_price)

        price_schemas: List[dict] = []
        for raw_price in prices:
            price_schemas.append(
                {
                    "id": raw_price.get('id'),
                    "product_id": raw_price.get('product_id'),
                    "active": raw_price.get('active', True),
                    "description": raw_price.get('description'),
                    "unit_amount": raw_price.get('unit_amount'),
                    "currency": raw_price.get('currency', 'eur'),
                    "type": raw_price.get('type', 'recurring'),
                    "interval": raw_price.get('interval'),
                    "interval_count": raw_price.get('interval_count'),
                    "trial_period_days": raw_price.get('trial_period_days'),
                    "metadata": _parse_metadata(raw_price.get('metadata')),
                    "created_at": raw_price.get('created_at'),
                    "updated_at": raw_price.get('updated_at')
                }
            )

        plan_product = {
            "id": product.get('id'),
            "active": product.get('active', True),
            "name": product.get('name'),
            "description": product.get('description'),
            "image": product.get('image'),
            "metadata": _parse_metadata(product.get('metadata')),
            "source": product.get('source', 'stripe'),
            "prices": price_schemas,
            "created_at": product.get('created_at'),
            "updated_at": product.get('updated_at')
        }

        return SubscriptionPlanExpanded(
            **plan_base.dict(),
            product=plan_product,
            prices=price_schemas
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération plan")


# =====================================================
# Endpoints pour l'abonnement utilisateur
# =====================================================

@router.get("/me", response_model=SubscriptionWithPlan)
async def get_my_subscription(
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id),
    credits_service: CreditsService = Depends(get_credits_service)
):
    """Récupère l'abonnement actuel de l'utilisateur connecté."""
    try:
        subscription = await credits_service.get_user_subscription(current_user_id)

        if not subscription:
            # Aucun abonnement trouvé - l'utilisateur doit en créer un
            raise HTTPException(status_code=404, detail="Aucun abonnement actif trouvé - veuillez choisir un plan d'abonnement")

        now = datetime.now(timezone.utc)

        days_until_renewal = None
        if subscription.current_period_end:
            current_period_end = subscription.current_period_end
            if isinstance(current_period_end, str):
                current_period_end = datetime.fromisoformat(current_period_end)
            time_diff = current_period_end - now
            days_until_renewal = max(0, time_diff.days)

        trial_days_remaining = None
        if subscription.trial_end and subscription.subscription_status.value == 'trialing':
            trial_end = subscription.trial_end
            if isinstance(trial_end, str):
                trial_end = datetime.fromisoformat(trial_end)
            time_diff = trial_end - now
            trial_days_remaining = max(0, time_diff.days)

        # Vérifier si upgrade possible (plans payants disponibles)
        available_products = db.table('products').select('*, prices(*)').eq('active', True).execute()
        current_price = subscription.plan.price_eur if subscription.plan else 0

        can_upgrade = False
        for product in available_products.data:
            primary_price = _select_primary_price(product.get('prices') or [])
            if not primary_price or primary_price.get('unit_amount') is None:
                continue
            plan_price = (primary_price.get('unit_amount') or 0) / 100
            if plan_price > current_price:
                can_upgrade = True
                break

        return SubscriptionWithPlan(
            subscription=subscription,
            can_upgrade=can_upgrade,
            days_until_renewal=days_until_renewal,
            trial_days_remaining=trial_days_remaining
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération abonnement {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération abonnement")


# =====================================================
# Endpoints pour les crédits
# =====================================================

@router.get("/credits/balance", response_model=CreditsBalance)
async def get_credits_balance(
    credits_service: CreditsService = Depends(get_credits_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Récupère le solde de crédits actuel de l'utilisateur."""
    try:
        return await credits_service.get_credits_balance(current_user_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération solde crédits {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération solde crédits")


@router.get("/credits/history", response_model=List[CreditTransaction])
async def get_credits_history(
    limit: int = 50,
    credits_service: CreditsService = Depends(get_credits_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Récupère l'historique des transactions de crédits."""
    try:
        if limit < 1 or limit > 100:
            limit = 50  # Valeur par défaut raisonnable

        return await credits_service.get_transaction_history(current_user_id, limit)

    except Exception as e:
        logger.error(f"Erreur récupération historique crédits {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération historique")


# =====================================================
# Endpoints pour les fonctionnalités
# =====================================================

@router.get("/features/access", response_model=FeatureAccess)
async def get_feature_access(
    credits_service: CreditsService = Depends(get_credits_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Vérifie quelles fonctionnalités sont accessibles pour l'utilisateur."""
    try:
        return await credits_service.get_feature_access(current_user_id)

    except Exception as e:
        logger.error(f"Erreur récupération accès fonctionnalités {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération accès fonctionnalités")


# =====================================================
# Endpoint public pricing (accès non authentifié)
# =====================================================

@router.get("/public/pricing", response_model=PublicPricingResponse)
async def get_public_pricing(db: Client = Depends(get_db)):
    try:
        result = db.table('products').select('*, prices(*)').eq('active', True).execute()

        plans: List[PublicPlan] = []
        stripe_enabled = False
        whop_enabled = False
        default_currency = 'eur'

        for product in result.data:
            prices = product.get('prices') or []
            primary_price = _select_primary_price(prices)

            if not primary_price:
                continue

            metadata = _parse_metadata(product.get('metadata'))
            price_metadata = _parse_metadata(primary_price.get('metadata'))

            unit_amount = primary_price.get('unit_amount') or 0
            currency = primary_price.get('currency') or default_currency
            interval = primary_price.get('interval') or 'month'
            interval_count = primary_price.get('interval_count') or 1

            features = metadata.get('features') or price_metadata.get('features') or {
                "text": True,
                "images": False,
                "audio": False,
            }
            if isinstance(features, str):
                try:
                    features = json.loads(features)
                except Exception:
                    features = {"text": True, "images": False, "audio": False}

            credits_monthly = metadata.get('credits_monthly') or price_metadata.get('credits_monthly') or 0
            max_calls = metadata.get('max_ai_calls_per_batch') or price_metadata.get('max_ai_calls_per_batch') or 3
            storage_quota = metadata.get('storage_quota_mb') or price_metadata.get('storage_quota_mb') or 10
            trial_days = metadata.get('trial_duration_days') or price_metadata.get('trial_period_days') or primary_price.get('trial_period_days')

            # Utiliser product_id directement comme id (plus simple et stable)
            plans.append(
                PublicPlan(
                    id=product.get('id'),
                    name=product.get('name'),
                    description=product.get('description'),
                    price=unit_amount / 100,
                    currency=currency,
                    interval=interval,
                    interval_count=interval_count,
                    features=features,
                    credits_monthly=_safe_int(credits_monthly, 0) or 0,
                    max_ai_calls_per_batch=_safe_int(max_calls, 3) or 3,
                    storage_quota_mb=_safe_int(storage_quota, 10) or 10,
                    trial_duration_days=_safe_int(trial_days),
                    source=product.get('source', 'stripe'),
                    stripe_price_id=primary_price.get('id') if product.get('source') == 'stripe' else None,
                    whop_product_id=product.get('id') if product.get('source') == 'whop' else None
                )
            )

            if product.get('source') == 'stripe':
                stripe_enabled = True
            if product.get('source') == 'whop':
                whop_enabled = True

        plans.sort(key=lambda p: p.price)

        currency = plans[0].currency if plans else default_currency

        return PublicPricingResponse(
            plans=plans,
            stripe_enabled=stripe_enabled,
            whop_enabled=whop_enabled,
            currency=currency,
            updated_at=datetime.now(timezone.utc)
        )

    except Exception as e:
        logger.error(f"Erreur récupération pricing public: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération pricing")


# =====================================================
# Endpoints pour les modèles AI
# =====================================================

@router.get("/models")
async def get_available_models(db: Client = Depends(get_db)):
    """Récupère la liste des modèles AI disponibles avec leurs coûts."""
    try:
        result = db.table('ai_models').select('*').eq('is_active', True).order('name').execute()
        return result.data
    except Exception as e:
        logger.error(f"Erreur récupération modèles: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération modèles AI")


@router.get("/models/{model_id}/can-use")
async def check_model_access(
    model_id: str,
    credits_service: CreditsService = Depends(get_credits_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Vérifie si l'utilisateur peut utiliser un modèle spécifique."""
    try:
        can_use = await credits_service.can_use_model(current_user_id, model_id)

        return {
            "model_id": model_id,
            "can_use": can_use,
            "reason": "Modèle autorisé" if can_use else "Modèle non compatible avec votre plan"
        }

    except Exception as e:
        logger.error(f"Erreur vérification accès modèle {model_id} pour {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur vérification accès modèle")


# Route start-trial supprimée - Stripe gère automatiquement les périodes d'essai
# via trial_period_days dans les prix et les webhooks


# =====================================================
# Endpoints pour le stockage
# =====================================================

@router.get("/storage/usage", response_model=StorageUsage)
async def get_storage_usage(
    storage_service = Depends(get_storage_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Récupère l'usage de stockage de l'utilisateur."""
    try:
        return await storage_service.get_storage_usage(current_user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération usage stockage pour {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération usage stockage")


# =====================================================
# Endpoints administratifs (protégés)
# =====================================================

@router.post("/admin/refill-monthly", response_model=dict)
async def admin_refill_monthly_credits(
    credits_service: CreditsService = Depends(get_credits_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Endpoint admin pour déclencher le refill mensuel des crédits.
    À sécuriser avec des permissions admin appropriées.
    """
    try:
        # TODO: Ajouter vérification des permissions admin
        refilled_count = await credits_service.refill_monthly_credits()

        return {
            "success": True,
            "message": f"Reset mensuel effectué pour {refilled_count} abonnements",
            "refilled_count": refilled_count
        }

    except Exception as e:
        logger.error(f"Erreur reset mensuel par {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur reset mensuel")
