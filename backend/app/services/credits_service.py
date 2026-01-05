import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal

from supabase import Client
from fastapi import HTTPException, Depends

from app.db.session import get_db
from app.schemas.subscription import (
    UserSubscription, CreditTransaction, CreditTransactionCreate,
    TransactionType, SubscriptionStatus, InsufficientCreditsError,
    FeatureAccess, CreditsBalance, SubscriptionPlan
)

logger = logging.getLogger(__name__)


class CreditsService:
    """Credits and subscriptions service.

    Adapted for the hybrid Stripe + Supabase architecture.

    Uses tables:
    - user_credits: balances and credit info
    - subscriptions: Stripe/Whop subscriptions
    - products/prices: plan configuration
    """

    def __init__(self, db: Client, redis_client=None, request_cache: Optional[Dict[str, Any]] = None):
        self.db = db
        self.redis = redis_client
        self._request_cache = request_cache if request_cache is not None else {}

    def _get_cached(self, key: str) -> Optional[Any]:
        return self._request_cache.get(key) if self._request_cache is not None else None

    def _set_cached(self, key: str, value: Any) -> None:
        if self._request_cache is not None:
            self._request_cache[key] = value

    # =====================================================
    # Subscriptions (hybrid architecture)
    # =====================================================

    async def get_user_subscription(self, user_id: str) -> Optional[UserSubscription]:
        """
        Retrieve the active subscription for a user.

        Logic:
        - Fetch from user_credits (credit balance)
        - Join with subscriptions (Stripe/Whop subscription info)
        - Build plan from products.metadata
        """
        try:
            cache_key = f"subscription:{user_id}"
            cached_subscription = self._get_cached(cache_key)
            if cached_subscription:
                return cached_subscription

            # 1. Fetch user credits
            credits_result = self.db.table('user_credits').select('*').eq('user_id', user_id).single().execute()

            if not credits_result.data:
                # No credits = no subscription
                return None

            user_credits = credits_result.data

            # 2. If Stripe/Whop subscription exists, fetch details
            subscription_data = None
            plan_data = None

            if user_credits.get('subscription_id'):
                # Fetch subscription with joins
                sub_result = self.db.table('subscriptions').select(
                    '*, price:prices(*, product:products(*))'
                ).eq('id', user_credits['subscription_id']).single().execute()

                if sub_result.data:
                    subscription_data = sub_result.data

                    # Extract plan from product metadata
                    if subscription_data.get('price', {}).get('product', {}):
                        product = subscription_data['price']['product']
                        metadata = product.get('metadata', {})

                        # Convert metadata into a plan object
                        plan_data = self._build_plan_from_product_metadata(product, metadata)

            # 3. Build UserSubscription from hybrid data
            subscription = UserSubscription(
                id=user_credits['id'],
                user_id=user_id,
                plan=plan_data or self._get_default_plan(),
                credits_balance=user_credits['credits_balance'],
                credits_used_this_month=0,  # TODO: compute from transactions
                storage_used_mb=user_credits.get('storage_used_mb', 0),
                subscription_status=self._determine_subscription_status(subscription_data, user_credits),
                stripe_subscription_id=subscription_data.get('id') if subscription_data and subscription_data.get('source') == 'stripe' else None,
                whop_subscription_id=subscription_data.get('id') if subscription_data and subscription_data.get('source') == 'whop' else None,
                current_period_start=subscription_data.get('current_period_start') if subscription_data else None,
                current_period_end=subscription_data.get('current_period_end') if subscription_data else None,
                trial_end=subscription_data.get('trial_end') if subscription_data else None,
                created_at=user_credits['created_at'],
                updated_at=user_credits['updated_at']
            )

            self._set_cached(cache_key, subscription)
            return subscription

        except Exception as e:
            logger.error(f"Error fetching user subscription {user_id}: {e}")
            return None

    def _build_plan_from_product_metadata(self, product: Dict[str, Any], metadata: Dict[str, Any]) -> SubscriptionPlan:
        """Build a SubscriptionPlan from Stripe/Whop product metadata."""
        import json

        # Extract features from metadata
        features_str = metadata.get('features', '{}')
        try:
            features = json.loads(features_str) if isinstance(features_str, str) else features_str
        except:
            features = {"text": True, "images": False, "audio": False}

        return SubscriptionPlan(
            id=product['id'],
            name=product['name'],
            price_eur=0,  # TODO: depuis price
            credits_included=max(1, int(metadata.get('credits_monthly', 1000))),
            max_ai_calls_per_batch=int(metadata.get('max_ai_calls_per_batch', 3)),
            trial_duration_days=max(1, int(metadata.get('trial_duration_days', 7))),
            storage_quota_mb=int(metadata.get('storage_quota_mb', 10)),
            features=features,
            stripe_price_id=None,  # TODO: depuis price relation
            whop_product_id=product['id'] if product.get('source') == 'whop' else None,
            is_active=product.get('active', True),
            is_trial=False,  # TODO: déterminer depuis metadata
            created_at=product.get('created_at'),
            updated_at=product.get('updated_at')
        )

    def _get_default_plan(self) -> SubscriptionPlan:
        """Default plan for users without a subscription."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()

        return SubscriptionPlan(
            id="free_plan",
            name="Free Plan",
            price_eur=0,
            credits_included=100,  # Minimum value to satisfy Pydantic
            max_ai_calls_per_batch=3,
            trial_duration_days=7,  # Minimum value to satisfy Pydantic
            storage_quota_mb=10,
            features={"text": True, "images": False, "audio": False},
            is_active=True,
            is_trial=False,
            created_at=now,
            updated_at=now
        )

    def _determine_subscription_status(self, subscription_data: Optional[Dict], user_credits: Dict) -> SubscriptionStatus:
        """Determine subscription status from hybrid data."""
        if not subscription_data:
            # No active subscription
            return SubscriptionStatus.EXPIRED if user_credits['credits_balance'] == 0 else SubscriptionStatus.ACTIVE

        status_str = subscription_data.get('status', 'active').lower()

        # Map Stripe/Whop status → our enum
        status_mapping = {
            'trialing': SubscriptionStatus.TRIALING,
            'active': SubscriptionStatus.ACTIVE,
            'canceled': SubscriptionStatus.CANCELLED,
            'incomplete': SubscriptionStatus.PAST_DUE,
            'incomplete_expired': SubscriptionStatus.EXPIRED,
            'past_due': SubscriptionStatus.PAST_DUE,
            'unpaid': SubscriptionStatus.PAST_DUE,
            'paused': SubscriptionStatus.CANCELLED
        }

        return status_mapping.get(status_str, SubscriptionStatus.ACTIVE)

    # create_trial_subscription was removed: Stripe handles trials automatically
    # via trial_period_days in prices and customer.subscription.created webhooks

    async def update_subscription_status(self, user_id: str, status: SubscriptionStatus,
                                       stripe_id: Optional[str] = None, whop_id: Optional[str] = None) -> bool:
        """
        Update a subscription status.

        Logic:
        - Update user_credits.subscription_id
        - Update/insert into subscriptions if needed
        - Update the status in subscriptions
        """
        try:
            update_data = {'updated_at': datetime.utcnow().isoformat()}

            subscription_id = None
            source = None

            if stripe_id:
                # Update link to the Stripe subscription
                update_data['subscription_id'] = stripe_id
                subscription_id = stripe_id
                source = 'stripe'

                # Ensure subscriptions entry exists
                await self._ensure_subscription_exists(user_id, stripe_id, 'stripe')

            if whop_id:
                # Update link to the Whop subscription
                update_data['subscription_id'] = whop_id
                subscription_id = whop_id
                source = 'whop'

                # Ensure subscriptions entry exists
                await self._ensure_subscription_exists(user_id, whop_id, 'whop')

            # Update user_credits
            result = self.db.table('user_credits').update(update_data).eq('user_id', user_id).execute()

            # Update status in subscriptions if we have a subscription_id
            if subscription_id:
                # Map SubscriptionStatus to string for DB
                status_str = status.value if isinstance(status, SubscriptionStatus) else str(status)
                
                self.db.table('subscriptions').update({
                    'status': status_str,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', subscription_id).execute()

            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating subscription status for {user_id}: {e}")
            return False

    async def _ensure_subscription_exists(self, user_id: str, subscription_id: str, source: str):
        """Ensure a subscriptions entry exists for this subscription."""
        try:
            # Check whether it already exists
            existing = self.db.table('subscriptions').select('id').eq('id', subscription_id).single().execute()

            if not existing.data:
                # Create a base entry (will be completed by webhooks)
                self.db.table('subscriptions').insert({
                    'id': subscription_id,
                    'user_id': user_id,
                    'status': 'active',
                    'source': source,
                    'metadata': {'created_by': 'credits_service'}
                }).execute()

                logger.info(f"Subscriptions entry created for {source}: {subscription_id}")

        except Exception as e:
            logger.warning(f"Error checking subscription {subscription_id}: {e}")

    # =====================================================
    # Credits management (adapted)
    # =====================================================

    async def check_credits_available(self, user_id: str, required_credits: float) -> bool:
        """
        Check whether the user has enough credits (with Redis cache).

        Logic:
        - Fetch directly from user_credits
        - No need to go through subscription
        """
        try:
            balance = None

            if self.redis:
                cache_key = f"credits:balance:{user_id}"
                cached = await self.redis.get(cache_key)
                if cached:
                    balance = int(cached)

            if balance is None:
                # Fetch from user_credits
                credits_result = self.db.table('user_credits').select('credits_balance').eq('user_id', user_id).single().execute()

                if not credits_result.data:
                    return False

                balance = credits_result.data['credits_balance']

                if self.redis:
                    await self.redis.setex(f"credits:balance:{user_id}", 60, str(balance))

            return balance >= required_credits
        except Exception as e:
            logger.error(f"Error checking credits for {user_id}: {e}")
            return False

    async def get_credits_balance(self, user_id: str) -> CreditsBalance:
        """
        Retrieve detailed credit balance for a user.

        Logic:
        - Use user_credits and compute from transactions
        """
        try:
            # Fetch credit data
            credits_result = self.db.table('user_credits').select('*').eq('user_id', user_id).single().execute()

            if not credits_result.data:
                return CreditsBalance(
                    balance=0,
                    used_this_month=0,
                    plan_limit=0,
                    percentage_used=0
                )

            user_credits = credits_result.data
            balance = user_credits['credits_balance']
            plan_limit = user_credits.get('plan_credits', 0)

            # Calculer crédits utilisés ce mois (depuis transactions)
            start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            transactions_result = self.db.table('credit_transactions').select(
                'credits_amount'
            ).eq('user_id', user_id).eq('transaction_type', 'deduction').gte(
                'created_at', start_of_month.isoformat()
            ).execute()

            used_this_month = sum(abs(t['credits_amount']) for t in transactions_result.data)

            percentage_used = (used_this_month / plan_limit * 100) if plan_limit > 0 else 0

            return CreditsBalance(
                balance=balance,
                used_this_month=used_this_month,
                plan_limit=plan_limit,
                percentage_used=min(percentage_used, 100)
            )

        except Exception as e:
            logger.error(f"Erreur récupération solde crédits {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Erreur récupération solde crédits")

    async def deduct_credits(self, user_id: str, credits_to_deduct: float, reason: str,
                           metadata: Optional[Dict[str, Any]] = None) -> CreditTransaction:
        """
        Déduit des crédits avec vérification atomique.

        NOUVELLE LOGIQUE:
        - Utilise user_credits pour solde
        - Déduction atomique avec transactions
        """
        try:
            # Vérifier solde disponible
            if not await self.check_credits_available(user_id, credits_to_deduct):
                balance_data = await self.get_credits_balance(user_id)
                raise InsufficientCreditsError(
                    required=credits_to_deduct,
                    available=balance_data.balance,
                    message="Crédits insuffisants"
                )

            # Déduction atomique
            balance_after = await self._deduct_credits_atomic(user_id, credits_to_deduct)

            # Créer transaction
            transaction = await self._create_transaction(
                user_id=user_id,
                transaction_type=TransactionType.DEDUCTION,
                credits_amount=-credits_to_deduct,
                credits_balance_after=balance_after,
                reason=reason,
                metadata=metadata or {}
            )

            # Invalider cache
            if self.redis:
                await self.redis.delete(f"credits:balance:{user_id}")

            return transaction

        except InsufficientCreditsError:
            raise
        except Exception as e:
            logger.error(f"Erreur déduction crédits {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Erreur déduction crédits")

    async def add_credits(self, user_id: str, credits_to_add: float, reason: str,
                         transaction_type: TransactionType = TransactionType.PURCHASE,
                         metadata: Optional[Dict[str, Any]] = None) -> CreditTransaction:
        """
        Ajoute des crédits à un utilisateur.

        NOUVELLE LOGIQUE:
        - Met à jour user_credits
        - Crée transaction
        """
        try:
            # Récupérer solde actuel
            current_balance = await self.get_credits_balance(user_id)
            balance_after = current_balance.balance + credits_to_add

            # Mettre à jour user_credits (convertir en int pour la DB)
            self.db.table('user_credits').update({
                'credits_balance': int(balance_after),
                'updated_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).execute()

            # Créer transaction
            transaction = await self._create_transaction(
                user_id=user_id,
                transaction_type=transaction_type,
                credits_amount=credits_to_add,
                credits_balance_after=balance_after,
                reason=reason,
                metadata=metadata or {}
            )

            # Invalider cache
            if self.redis:
                await self.redis.delete(f"credits:balance:{user_id}")

            return transaction

        except Exception as e:
            logger.error(f"Erreur ajout crédits {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Erreur ajout crédits")

    async def get_transaction_history(self, user_id: str, limit: int = 50) -> List[CreditTransaction]:
        """Retrieve the credit transaction history."""
        try:
            result = self.db.table('credit_transactions').select('*').eq('user_id', user_id).order(
                'created_at', desc=True
            ).limit(limit).execute()

            return [CreditTransaction(**transaction) for transaction in result.data]

        except Exception as e:
            logger.error(f"Erreur récupération historique {user_id}: {e}")
            return []

    async def get_feature_access(self, user_id: str) -> FeatureAccess:
        """Determine the features accessible to the user."""
        try:
            cache_key = f"feature_access:{user_id}"
            cached_access = self._get_cached(cache_key)
            if cached_access:
                return cached_access

            subscription = await self.get_user_subscription(user_id)

            if not subscription or not subscription.plan:
                # Plan gratuit par défaut
                feature_access = FeatureAccess(
                    text=True,
                    images=True,
                    audio=False,
                    max_calls_per_batch=3
                )
                self._set_cached(cache_key, feature_access)
                return feature_access

            features = subscription.plan.features or {}
            # La génération d'images est désormais disponible pour tous les plans
            features.setdefault('text', True)
            features['images'] = True
            features.setdefault('audio', False)

            feature_access = FeatureAccess(
                text=features.get('text', True),
                images=features.get('images', False),
                audio=features.get('audio', False),
                max_calls_per_batch=subscription.plan.max_ai_calls_per_batch
            )
            self._set_cached(cache_key, feature_access)
            return feature_access

        except Exception as e:
            logger.error(f"Erreur récupération accès fonctionnalités {user_id}: {e}")
            # Fallback conservateur
            return FeatureAccess(text=True, images=False, audio=False, max_calls_per_batch=3)

    async def can_use_model(self, user_id: str, model_id: str) -> bool:
        """Vérifie si l'utilisateur peut utiliser un modèle spécifique."""
        try:
            logger.info(f"🔍 [CAN_USE_MODEL] Vérification modèle {model_id} pour user {user_id}")
            cache_key = f"ai_model:{model_id}"
            cached_model = self._get_cached(cache_key)
            model = cached_model

            # Récupérer le modèle
            if model is None:
                model_result = self.db.table('ai_models').select('*').eq('openrouter_id', model_id).single().execute()

                if not model_result.data:
                    logger.warning(f"❌ [CAN_USE_MODEL] Modèle {model_id} non trouvé dans ai_models")
                    return False

                model = model_result.data
                self._set_cached(cache_key, model)
            logger.info(f"✅ [CAN_USE_MODEL] Modèle trouvé: {model.get('name', 'N/A')}, supports_images={model.get('supports_images', False)}, supports_audio={model.get('supports_audio', False)}")
            
            feature_access = await self.get_feature_access(user_id)
            logger.info(f"🔍 [CAN_USE_MODEL] Feature access pour {user_id}: text={feature_access.text}, images={feature_access.images}, audio={feature_access.audio}")

            # Vérifier que l'utilisateur a au moins accès au texte
            if not feature_access.text:
                logger.warning(f"❌ [CAN_USE_MODEL] User {user_id} n'a pas accès au texte")
                return False

            # NOTE: Un modèle qui supporte les images/audio peut quand même être utilisé pour du texte uniquement
            # On autorise donc l'utilisation même si l'utilisateur n'a pas accès aux images/audio
            # La vérification se fera au moment de l'envoi du message (si c'est une image/audio, ça échouera)
            # Mais pour du texte, ça fonctionnera
            
            logger.info(f"✅ [CAN_USE_MODEL] Modèle {model_id} autorisé pour user {user_id} (peut être utilisé pour texte même si supporte images/audio)")
            return True

        except Exception as e:
            logger.error(f"❌ [CAN_USE_MODEL] Erreur vérification modèle {model_id} pour {user_id}: {e}", exc_info=True)
            return False

    async def can_use_feature(self, user_id: str, feature: str) -> bool:
        """Vérifie si l'utilisateur peut utiliser une fonctionnalité."""
        try:
            feature_access = await self.get_feature_access(user_id)

            feature_mapping = {
                'images': feature_access.images,
                'audio': feature_access.audio,
                'text': feature_access.text
            }

            return feature_mapping.get(feature, False)

        except Exception as e:
            logger.error(f"Erreur vérification fonctionnalité {feature} pour {user_id}: {e}")
            return False

    # =====================================================
    # Méthodes privées
    # =====================================================

    async def _deduct_credits_atomic(self, user_id: str, amount: float) -> float:
        """Déduit des crédits de manière atomique."""
        # Récupérer solde actuel
        credits_result = self.db.table('user_credits').select('credits_balance').eq('user_id', user_id).single().execute()

        if not credits_result.data:
            raise InsufficientCreditsError(required=amount, available=0, message="Utilisateur sans crédits")

        current_balance = credits_result.data['credits_balance']

        if current_balance < amount:
            raise InsufficientCreditsError(
                required=amount,
                available=current_balance,
                message="Solde insuffisant"
            )

        new_balance = current_balance - amount

        # Mise à jour atomique (convertir en int pour la DB)
        self.db.table('user_credits').update({
            'credits_balance': int(new_balance),
            'updated_at': datetime.utcnow().isoformat()
        }).eq('user_id', user_id).execute()

        return new_balance

    async def _create_transaction(self, user_id: str, transaction_type: TransactionType,
                                credits_amount: float, credits_balance_after: float,
                                reason: str, metadata: Dict[str, Any]) -> CreditTransaction:
        """Crée une transaction de crédits."""
        transaction_data = CreditTransactionCreate(
            user_id=user_id,
            transaction_type=transaction_type,
            credits_amount=credits_amount,
            credits_balance_after=credits_balance_after,
            reason=reason,
            metadata=metadata
        )

        result = self.db.table('credit_transactions').insert(transaction_data.model_dump()).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Erreur création transaction")
        
        transaction_dict = result.data[0] if isinstance(result.data, list) else result.data
        return CreditTransaction(**transaction_dict)

    # =====================================================
    # Compatibility methods (will be removed after migration)
    # =====================================================

    async def reset_monthly_credits(self, user_id: str, credits_monthly: int, reason: str, metadata: Optional[Dict[str, Any]] = None) -> CreditTransaction:
        """
        RESET complet des crédits pour renouvellement mensuel.

        Remplace TOUS les crédits existants par les crédits mensuels du plan.
        """
        try:
            # Récupérer solde actuel
            current_balance = await self.get_credits_balance(user_id)
            credits_difference = credits_monthly - current_balance.balance

            # Mettre à jour user_credits avec reset complet
            now = datetime.now(timezone.utc)
            next_month = now.replace(day=1, month=now.month + 1 if now.month < 12 else 1, year=now.year if now.month < 12 else now.year + 1)

            self.db.table('user_credits').upsert({
                'user_id': user_id,
                'credits_balance': credits_monthly,
                'plan_credits': credits_monthly,
                'subscription_id': metadata.get('subscription_id') if metadata else None,
                'storage_used_mb': current_balance.storage_used_mb,  # Garder stockage
                'next_reset_at': next_month.isoformat()
            }, on_conflict='user_id').execute()

            # Créer transaction de reset
            transaction = await self._create_transaction(
                user_id=user_id,
                transaction_type=TransactionType.MONTHLY_RESET,
                credits_amount=credits_difference,  # Différence (positif si ajout, négatif si retrait)
                credits_balance_after=credits_monthly,  # Nouveau solde = crédits mensuels
                reason=reason,
                metadata=metadata or {}
            )

            # Invalider cache
            if self.redis:
                await self.redis.delete(f"credits:balance:{user_id}")

            logger.info(f"Crédits reset mensuel: {credits_monthly} pour user {user_id} (diff: {credits_difference})")
            return transaction

        except Exception as e:
            logger.error(f"Erreur reset crédits mensuels {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Erreur reset crédits mensuels")

    async def refill_monthly_credits(self) -> int:
        """
        Refill monthly credits (compatibility method).

        DEPRECATED: Sera remplacée par la logique webhook Stripe
        """
        logger.warning("refill_monthly_credits() est DEPRECATED - utiliser webhooks Stripe")
        return 0


# =====================================================
# Dépendances FastAPI
# =====================================================

def get_credits_service(db: Client = Depends(get_db)) -> CreditsService:
    """Dépendance FastAPI pour injecter le service Credits."""
    return CreditsService(db)