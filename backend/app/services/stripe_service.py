import os
import stripe
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from fastapi import HTTPException, Depends

from supabase import Client
from dotenv import load_dotenv

from app.services.credits_service import CreditsService, TransactionType, get_credits_service
from app.services.email_service import EmailService, get_email_service
from app.db.session import get_db
from app.schemas.subscription import SubscriptionStatus

load_dotenv()
logger = logging.getLogger(__name__)

CURRENCY = 'EUR'


class StripeService:
    """
    Service Stripe pour l'architecture hybride.

    Gère:
    - Sync automatique products/prices depuis Stripe
    - Gestion des abonnements et renouvellements
    - Webhooks Stripe standard avec idempotence
    - Création sessions checkout
    """

    def __init__(self, db: Client, credits_service: CreditsService, email_service: Optional[EmailService] = None):
        self.db = db
        self.credits_service = credits_service
        self.email_service = email_service
        self.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        if not self.api_key:
            logger.warning("STRIPE_SECRET_KEY non configuré - service Stripe désactivé")
            self.enabled = False
        else:
            self.enabled = True
            stripe.api_key = self.api_key

    # =====================================================
    # Gestion des clients (Customers)
    # =====================================================

    async def get_or_create_customer(self, user_id: str) -> Dict[str, Any]:
        """
        Récupère ou crée un customer Stripe pour l'utilisateur.

        Returns: {'stripe_customer_id': str, 'is_new': bool}
        """
        if not self.enabled:
            raise HTTPException(status_code=503, detail="Service Stripe non configuré")

        try:
            # Vérifier si customer existe déjà
            customer_result = self.db.table('customers').select('stripe_customer_id').eq('id', user_id).execute()

            if customer_result.data and len(customer_result.data) > 0 and customer_result.data[0].get('stripe_customer_id'):
                return {
                    'stripe_customer_id': customer_result.data[0]['stripe_customer_id'],
                    'is_new': False
                }

            # Récupérer info utilisateur
            user_result = self.db.table('users').select('email, full_name').eq('id', user_id).single().execute()

            if not user_result.data:
                raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

            user_data = user_result.data

            # Créer customer dans Stripe
            customer = stripe.Customer.create(
                email=user_data.get('email'),
                name=user_data.get('full_name'),
                metadata={'user_id': user_id}
            )

            # Sauvegarder dans notre DB
            self.db.table('customers').upsert({
                'id': user_id,
                'stripe_customer_id': customer.id
            }).execute()

            logger.info(f"Customer Stripe créé: {customer.id} pour user {user_id}")

            return {
                'stripe_customer_id': customer.id,
                'is_new': True
            }

        except Exception as e:
            logger.error(f"Erreur création/récupération customer {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Erreur gestion client Stripe")

    # =====================================================
    # Sessions de checkout
    # =====================================================

    async def create_checkout_session(self, user_id: str, price_id: str,
                                    success_url: Optional[str] = None,
                                    cancel_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Crée une session de checkout Stripe pour un abonnement.

        Args:
            user_id: ID de l'utilisateur
            price_id: ID du prix Stripe (price_xxx)
            success_url/cancel_url: URLs de redirection
        """
        if not self.enabled:
            raise HTTPException(status_code=503, detail="Service Stripe non configuré")

        try:
            # Récupérer ou créer customer
            customer_data = await self.get_or_create_customer(user_id)

            # Récupérer info du prix pour metadata
            price_result = self.db.table('prices').select('*, product:products(*)').eq('id', price_id).single().execute()

            if not price_result.data:
                raise HTTPException(status_code=404, detail="Prix non trouvé")

            price_data = price_result.data
            product_data = price_data.get('product') or {}
            product_metadata = product_data.get('metadata') or {}
            if isinstance(product_metadata, str):
                try:
                    product_metadata = json.loads(product_metadata)
                except Exception:
                    product_metadata = {}

            # Récupérer trial_days depuis metadata
            trial_days = product_metadata.get('trial_duration_days')
            try:
                trial_days = int(trial_days) if trial_days is not None else 0
            except (ValueError, TypeError):
                trial_days = 0

            # URLs par défaut
            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
            default_success_url = f"{frontend_url}/dashboard?payment=success"
            default_cancel_url = f"{frontend_url}/dashboard?payment=cancelled"

            # Construire subscription_data proprement
            subscription_data = {
                'metadata': {
                    'user_id': user_id,
                    'plan_name': product_metadata.get('plan_name', 'Unknown')
                }
            }
            if trial_days and trial_days > 0:
                subscription_data['trial_period_days'] = trial_days

            session = stripe.checkout.Session.create(
                customer=customer_data['stripe_customer_id'],
                mode='subscription',
                line_items=[{'price': price_id, 'quantity': 1}],
                # Stripe recommande automatic_payment_methods
                automatic_payment_methods={'enabled': True},
                success_url=success_url or default_success_url,
                cancel_url=cancel_url or default_cancel_url,
                subscription_data=subscription_data,
                metadata={
                    'user_id': user_id,
                    'price_id': price_id,
                    'plan_name': product_metadata.get('plan_name', 'Unknown')
                }
            )

            logger.info(f"Session checkout créée: {session.id} pour user {user_id}")
            
            return {
                'success': True,
                'checkout_url': session.url,
                'session_id': session.id,
                'price_id': price_id,
                'customer_id': customer_data['stripe_customer_id']
            }
            
        except Exception as e:
            logger.error(f"Erreur Stripe checkout: {e}")
            raise HTTPException(status_code=400, detail=f"Erreur Stripe: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur création session checkout {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Erreur création session de paiement")

    # =====================================================
    # Sync automatique depuis Stripe (Webhooks)
    # =====================================================
    
    async def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Traite un webhook Stripe en vérifiant la signature et en parsant le payload.
        """
        if not self.enabled:
            return {'status': 'disabled', 'message': 'Stripe service disabled'}

        try:
            # Vérifier et parser le webhook Stripe
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )

            # Traiter l'événement avec idempotence
            return await self._process_webhook_event(event)

        except Exception as e:
            logger.error(f"Signature webhook invalide: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        except Exception as e:
            logger.error(f"Erreur traitement webhook: {e}")
            raise

    async def _process_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite un webhook Stripe avec idempotence.

        Gestion des événements standard:
        - product.* : Sync produits
        - price.* : Sync prix
        - customer.subscription.* : Sync abonnements
        - invoice.* : Gestion paiements/renouvellements
        """
        if not self.enabled:
            return {'status': 'disabled', 'message': 'Stripe service disabled'}

        try:
            event_type = event.get('type')
            event_id = event.get('id')
            event_data = event.get('data', {}).get('object', {})

            # Try-insert (unique) pour idempotence. Si conflit => déjà traité.
            try:
                self.db.table('webhook_events').insert({
                    'stripe_event_id': event_id,
                    'event_type': event_type,
                    'source': 'stripe',
                    'payload': event,            # tu peux tronquer si trop gros
                    'processed_at': datetime.now(timezone.utc).isoformat()
                }).execute()
            except Exception as e:
                # Si erreur de contrainte unique -> déjà traité
                logger.info(f"Événement déjà traité (unique conflict): {event_id}")
                return {'status': 'already_processed', 'event_id': event_id}

            logger.info(f"Webhook Stripe: {event_type} ({event_id})")

            # Router selon type d'événement
            handlers = {
                # Produits
                'product.created': self._sync_product,
                'product.updated': self._sync_product,
                'product.deleted': self._archive_product,

                # Prix
                'price.created': self._sync_price,
                'price.updated': self._sync_price,
                'price.deleted': self._archive_price,

                # Abonnements
                'customer.subscription.created': self._handle_subscription_created,
                'customer.subscription.updated': self._handle_subscription_updated,
                'customer.subscription.deleted': self._handle_subscription_deleted,

                # Paiements
                'invoice.payment_succeeded': self._handle_payment_succeeded,
                'invoice.payment_failed': self._handle_payment_failed,

                # Sessions
                'checkout.session.completed': self._handle_checkout_completed,
            }

            handler = handlers.get(event_type)
            if handler:
                result = await handler(event_data)

                return {
                    'status': 'processed',
                    'event_type': event_type,
                    'event_id': event_id,
                    'result': result
                }
            else:
                # Événement non géré
                return {
                    'status': 'ignored',
                    'event_type': event_type,
                    'reason': 'Handler not implemented'
                }

        except Exception as e:
            logger.error(f"Erreur traitement webhook Stripe: {e}")
            raise HTTPException(status_code=500, detail="Erreur traitement webhook")

    # =====================================================
    # Handlers de sync automatique
    # =====================================================

    async def _sync_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Sync un produit depuis Stripe."""
        try:
            self.db.table('products').upsert({
                'id': product['id'],
                'active': product.get('active', True),
                'name': product['name'],
                'description': product.get('description'),
                'image': product.get('images', [None])[0] if product.get('images') else None,
                'metadata': product.get('metadata', {}),
                'source': 'stripe'
            }).execute()

            logger.info(f"Produit sync: {product['id']} - {product['name']}")
            return {'synced': True, 'product_id': product['id']}

        except Exception as e:
            logger.error(f"Erreur sync produit {product['id']}: {e}")
            raise

    async def _archive_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Archive un produit supprimé."""
        try:
            self.db.table('products').update({
                'active': False,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', product['id']).execute()

            logger.info(f"Produit archivé: {product['id']}")
            return {'archived': True, 'product_id': product['id']}
                
        except Exception as e:
            logger.error(f"Erreur archivage produit {product['id']}: {e}")
            raise
    
    async def _sync_price(self, price: Dict[str, Any]) -> Dict[str, Any]:
        """Sync un prix depuis Stripe."""
        try:
            self.db.table('prices').upsert({
                'id': price['id'],
                'product_id': price['product'],
                'active': price.get('active', True),
                'description': price.get('metadata', {}).get('plan_name'),
                'unit_amount': price['unit_amount'],
                'currency': price['currency'],
                'type': price['type'],
                'interval': price.get('recurring', {}).get('interval'),
                'interval_count': price.get('recurring', {}).get('interval_count', 1),
                'trial_period_days': price.get('recurring', {}).get('trial_period_days', 0),
                'metadata': price.get('metadata', {})
            }).execute()

            logger.info(f"Prix sync: {price['id']} - {price['unit_amount']/100}€")
            return {'synced': True, 'price_id': price['id']}

        except Exception as e:
            logger.error(f"Erreur sync prix {price['id']}: {e}")
            raise

    async def _archive_price(self, price: Dict[str, Any]) -> Dict[str, Any]:
        """Archive un prix supprimé."""
        try:
            self.db.table('prices').update({
                'active': False,
                    'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', price['id']).execute()

            logger.info(f"Prix archivé: {price['id']}")
            return {'archived': True, 'price_id': price['id']}

        except Exception as e:
            logger.error(f"Erreur archivage prix {price['id']}: {e}")
            raise

    async def _handle_subscription_created(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Traite la création d'un abonnement avec gestion crédits d'essai."""
        try:
            user_id = subscription.get('metadata', {}).get('user_id')

            if not user_id:
                # Essayer de trouver via customer
                customer_id = subscription.get('customer')
                customer_result = self.db.table('customers').select('id').eq('stripe_customer_id', customer_id).execute()
                if customer_result.data and len(customer_result.data) > 0:
                    user_id = customer_result.data[0]['id']

            if not user_id:
                logger.warning(f"User ID non trouvé pour subscription {subscription['id']}")
                return {'error': 'user_not_found'}

            # Créer entrée subscription
            self.db.table('subscriptions').upsert({
                'id': subscription['id'],
                'user_id': user_id,
                'status': subscription['status'],
                'price_id': subscription['items']['data'][0]['price']['id'] if subscription.get('items', {}).get('data') else None,
                'quantity': subscription['items']['data'][0]['quantity'] if subscription.get('items', {}).get('data') else 1,
                'cancel_at_period_end': subscription.get('cancel_at_period_end', False),
                'created_at': datetime.fromtimestamp(subscription['created'], tz=timezone.utc).isoformat(),
                'current_period_start': datetime.fromtimestamp(subscription['current_period_start'], tz=timezone.utc).isoformat(),
                'current_period_end': datetime.fromtimestamp(subscription['current_period_end'], tz=timezone.utc).isoformat(),
                'trial_end': datetime.fromtimestamp(subscription['trial_end'], tz=timezone.utc).isoformat() if subscription.get('trial_end') else None,
                'metadata': subscription.get('metadata', {}),
                'source': 'stripe'
            }).execute()

            # GESTION CRÉDITS SELON STATUT
            if subscription['status'] == 'trialing':
                # APPLIQUER CRÉDITS D'ESSAI (100 crédits)
                await self._apply_trial_credits(user_id, subscription['id'])
            elif subscription['status'] == 'active':
                # ABONNEMENT ACTIF DIRECT (pas d'essai) - appliquer crédits du plan
                await self._apply_initial_plan_credits(user_id, subscription['id'])

            # Envoyer email de bienvenue
            await self._send_subscription_welcome_email(user_id, subscription)

            logger.info(f"Abonnement créé: {subscription['id']} pour user {user_id} - statut: {subscription['status']}")
            return {
                'subscription_id': subscription['id'],
                'user_id': user_id,
                'status': subscription['status']
            }

        except Exception as e:
            logger.error(f"Erreur création abonnement {subscription['id']}: {e}")
            raise
    
    async def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Traite la mise à jour d'un abonnement avec gestion crédits."""
        try:
            user_id = await self._get_user_from_subscription(subscription['id'])
            if not user_id:
                logger.warning(f"User non trouvé pour subscription {subscription['id']}")
                return {'error': 'user_not_found'}

            # Mettre à jour subscription
            update_data = {
                'status': subscription['status'],
                'cancel_at_period_end': subscription.get('cancel_at_period_end', False),
                'current_period_start': datetime.fromtimestamp(subscription['current_period_start'], tz=timezone.utc).isoformat(),
                'current_period_end': datetime.fromtimestamp(subscription['current_period_end'], tz=timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

            # Ajouter trial_end si présent (important pour détecter les essais)
            if subscription.get('trial_end'):
                update_data['trial_end'] = datetime.fromtimestamp(subscription['trial_end'], tz=timezone.utc).isoformat()

            # Ajouter trial_start si présent
            if subscription.get('trial_start'):
                update_data['trial_start'] = datetime.fromtimestamp(subscription['trial_start'], tz=timezone.utc).isoformat()

            self.db.table('subscriptions').update(update_data).eq('id', subscription['id']).execute()

            # GESTION CRÉDITS SIMPLIFIÉE selon la documentation
            if subscription['status'] in ['canceled', 'incomplete_expired']:
                # Selon documentation : purge immédiate à l'annulation effective
                # Plus de logique complexe - purge systématique
                await self._zero_credits_on_cancel(subscription['id'])

                # Créer transaction pour audit
                await self.credits_service._create_transaction(
                    user_id=user_id,
                    transaction_type=TransactionType.CANCEL,
                    credits_amount=0,
                    credits_balance_after=0,
                    reason=f"Annulation abonnement - {subscription['status']}",
                    metadata={'subscription_id': subscription['id']}
                )

                logger.info(f"Annulation abonnement {subscription['id']} - crédits purgés immédiatement")

            elif subscription['status'] == 'trialing':
                # Abonnement en essai - crédits d'essai déjà appliqués à la création
                logger.info(f"Essai actif {subscription['id']} - crédits d'essai maintenus")

            elif subscription['status'] == 'active':
                # Passage en actif (fin d'essai réussi) - crédits restent jusqu'au prochain paiement
                logger.info(f"Abonnement devenu actif {subscription['id']} - crédits préservés")

                # Gestion changement de plan (sans toucher aux crédits)
                await self._handle_plan_change(user_id, subscription)

            logger.info(f"Abonnement mis à jour: {subscription['id']} - {subscription['status']}")
            return {
                'subscription_id': subscription['id'],
                'status': subscription['status'],
                'user_id': user_id
            }

        except Exception as e:
            logger.error(f"Erreur mise à jour abonnement {subscription['id']}: {e}")
            raise

    async def _handle_subscription_deleted(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Traite la suppression d'un abonnement - PURGE IMMÉDIATE des crédits."""
        try:
            # Récupérer user_id avant suppression
            user_id = await self._get_user_from_subscription(subscription['id'])

            # Marquer comme supprimé (ne pas supprimer la ligne)
            self.db.table('subscriptions').update({
                'status': 'canceled',
                'ended_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', subscription['id']).execute()

            # PURGE IMMÉDIATE des crédits selon la documentation
            await self._zero_credits_on_cancel(subscription['id'])

            # Créer transaction pour audit si user trouvé
            if user_id:
                await self.credits_service._create_transaction(
                    user_id=user_id,
                    transaction_type=TransactionType.CANCEL,
                    credits_amount=0,  # Purge complète
                    credits_balance_after=0,
                    reason="Annulation abonnement - Purge crédits",
                    metadata={'subscription_id': subscription['id']}
                )

                # Envoyer email d'annulation
                await self._send_subscription_cancelled_email(user_id, subscription)

            logger.info(f"Abonnement supprimé et crédits purgés: {subscription['id']}")
            return {'subscription_id': subscription['id'], 'action': 'deleted_and_credits_zeroed'}

        except Exception as e:
            logger.error(f"Erreur suppression abonnement {subscription['id']}: {e}")
            raise

    async def _handle_payment_succeeded(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Traite un paiement réussi (renouvellement mensuel - RESET crédits)."""
        try:
            subscription_id = invoice.get('subscription')
            if not subscription_id:
                return {'ignored': True, 'reason': 'no_subscription'}

            user_id = await self._get_user_from_subscription(subscription_id)
            if not user_id:
                logger.warning(f"User non trouvé pour invoice {invoice['id']}")
                return {'error': 'user_not_found'}

            # Récupérer la date de fin de période depuis l'invoice
            period_end = None
            if invoice.get('lines', {}).get('data'):
                period_end_ts = invoice['lines']['data'][0].get('period', {}).get('end')
                if period_end_ts:
                    period_end = datetime.fromtimestamp(period_end_ts, tz=timezone.utc).isoformat()

            if not period_end:
                logger.warning(f"Pas de period_end dans invoice {invoice['id']}")
                return {'error': 'no_period_end'}

            # RESET DUR des crédits avec fonction SQL atomique
            plan_credits = await self._resolve_plan_credits(subscription_id)
            await self._reset_cycle_credits(subscription_id, period_end)

            # Lire nouveau solde
            uc = self.db.table('user_credits').select('user_id, credits_balance').eq('subscription_id', subscription_id).single().execute()
            new_balance = (uc.data or {}).get('credits_balance')

            await self.credits_service._create_transaction(
                user_id=user_id,
                transaction_type=TransactionType.MONTHLY_RESET,
                credits_amount=int(plan_credits),
                credits_balance_after=new_balance,
                reason=f"Renouvellement Stripe - Invoice {invoice['id']}",
                metadata={
                    'stripe_invoice_id': invoice['id'],
                    'subscription_id': subscription_id,
                    'amount_paid': invoice.get('amount_paid', 0),
                    'period_end': period_end
                }
            )

            logger.info(f"Crédits reset pour abonnement {subscription_id} - période jusqu'à {period_end}")
            return {
                'subscription_id': subscription_id,
                'invoice_id': invoice['id'],
                'period_end': period_end,
                'action': 'credits_reset'
            }

        except Exception as e:
            logger.error(f"Erreur paiement réussi {invoice['id']}: {e}")
            raise

    async def cancel_subscription(self, user_id: str) -> Dict[str, Any]:
        """Annule l'abonnement actif de l'utilisateur (fin de période)."""
        try:
            if not self.enabled:
                raise HTTPException(status_code=503, detail="Stripe service disabled")

            # Trouver customer
            customer_data = await self.get_or_create_customer(user_id)

            # Trouver abonnement actif
            subscriptions = stripe.Subscription.list(
                customer=customer_data['stripe_customer_id'],
                status='active',
                limit=1
            )

            if not subscriptions.data:
                raise HTTPException(status_code=404, detail="No active subscription found")

            subscription = subscriptions.data[0]

            # Annuler à la fin de la période (cancel_at_period_end=True)
            stripe.Subscription.modify(
                subscription.id,
                cancel_at_period_end=True
            )

            logger.info(f"Abonnement annulé (fin période): {subscription.id} pour user {user_id}")
            return {
                'subscription_id': subscription.id,
                'cancel_at': datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc).isoformat(),
                'current_period_end': datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc).isoformat(),
                'status': 'canceled_at_period_end'
            }

        except Exception as e:
            logger.error(f"Erreur annulation abonnement pour {user_id}: {e}")
            raise

    # =====================================================
    # Nouvelles méthodes helper utilisant fonctions SQL atomiques
    # =====================================================

    async def _apply_trial_credits(self, user_id: str, subscription_id: str) -> None:
        """Applique crédits d'essai résolus depuis metadata."""
        try:
            # lire trial_end
            sub_row = self.db.table('subscriptions').select('price_id, trial_end').eq('id', subscription_id).single().execute()
            if not sub_row.data or not sub_row.data.get('trial_end'):
                logger.warning(f"Pas de trial_end pour subscription {subscription_id}")
                return

            price_id = sub_row.data.get('price_id')
            trial_end = sub_row.data['trial_end']

            # résoudre trial_credits depuis price -> product (fallback 100)
            pr = self.db.table('prices').select('metadata, product:products(metadata)').eq('id', price_id).single().execute()
            price_md = (pr.data or {}).get('metadata') or {}
            product_md = (pr.data or {}).get('product', {}).get('metadata') or {}
            if isinstance(price_md, str):
                try: price_md = json.loads(price_md)
                except: price_md = {}
            if isinstance(product_md, str):
                try: product_md = json.loads(product_md)
                except: product_md = {}

            trial_credits = (price_md.get('trial_credits')
                             or product_md.get('trial_credits')
                             or 100)

            # RPC atomique
            self.db.rpc('apply_trial_credits', {
                'p_user_id': user_id,
                'p_subscription_id': subscription_id,
                'p_trial_credits': int(trial_credits),
                'p_trial_end': trial_end
            }).execute()

            # log: lire le solde après
            uc = self.db.table('user_credits').select('credits_balance').eq('user_id', user_id).single().execute()
            new_balance = (uc.data or {}).get('credits_balance', int(trial_credits))

            await self.credits_service._create_transaction(
                user_id=user_id,
                transaction_type=TransactionType.TRIAL_GRANT,
                credits_amount=int(trial_credits),
                credits_balance_after=new_balance,
                reason="Attribution crédits d'essai",
                metadata={'subscription_id': subscription_id, 'trial_end': trial_end}
            )

            logger.info(f"Crédits d'essai appliqués: {trial_credits} pour user {user_id} - fin essai: {trial_end}")

        except Exception as e:
            logger.error(f"Erreur application crédits essai {user_id}: {e}")
            raise

    async def _apply_initial_plan_credits(self, user_id: str, subscription_id: str) -> None:
        """Applique les crédits initiaux du plan pour abonnement actif direct."""
        try:
            # Récupérer period_end
            subscription_data = self.db.table('subscriptions').select('current_period_end').eq('id', subscription_id).single().execute()
            period_end = subscription_data.data['current_period_end'] if subscription_data.data else None

            if not period_end:
                logger.warning(f"Pas de current_period_end pour subscription {subscription_id}")
                return

            # RESET DUR avec fonction SQL atomique
            await self._reset_cycle_credits(subscription_id, period_end)

            logger.info(f"Crédits plan initiaux appliqués pour user {user_id}")

        except Exception as e:
            logger.error(f"Erreur application crédits plan initiaux {user_id}: {e}")
            raise

    async def _reset_cycle_credits(self, subscription_id: str, period_end: str) -> None:
        """Reset dur des crédits pour nouveau cycle payant."""
        try:
            # Résoudre les crédits du plan d'abord
            plan_credits = await self._resolve_plan_credits(subscription_id)

            # Utiliser fonction SQL atomique
            result = self.db.rpc('reset_cycle_credits', {
                'p_subscription_id': subscription_id,
                'p_plan_credits': plan_credits,
                'p_period_end': period_end
            }).execute()

            logger.info(f"Reset cycle crédits: {plan_credits} pour subscription {subscription_id}")

        except Exception as e:
            logger.error(f"Erreur reset cycle crédits {subscription_id}: {e}")
            raise

    async def _resolve_plan_credits(self, subscription_id: str) -> int:
        """Résout le nombre de crédits du plan depuis les métadonnées."""
        # Pour l'instant, utiliser uniquement le fallback Python car la fonction RPC n'est pas encore créée
        # TODO: utiliser la fonction RPC une fois créée dans Supabase
        try:
            # Récupérer les données subscription + price + product
            subscription_data = self.db.table('subscriptions').select(
                '*, price:prices(*, product:products(*))'
            ).eq('id', subscription_id).single().execute()

            if not subscription_data.data:
                logger.warning(f"Subscription {subscription_id} non trouvée")
                return 1000

            product_metadata = subscription_data.data.get('price', {}).get('product', {}).get('metadata', {})

            # Convertir metadata string si nécessaire
            if isinstance(product_metadata, str):
                import json
                try:
                    product_metadata = json.loads(product_metadata)
                except:
                    product_metadata = {}

            # Résoudre dans l'ordre: price.metadata -> product.metadata
            credits_per_cycle = (
                product_metadata.get('credits_per_cycle') or
                product_metadata.get('credits_monthly') or
                1000  # Valeur par défaut
            )

            return int(credits_per_cycle)

        except Exception as e:
            logger.error(f"Erreur résolution crédits plan {subscription_id}: {e}")
            return 1000  # Valeur par défaut

    async def _zero_credits_on_cancel(self, subscription_id: str) -> None:
        """Met à zéro les crédits et détache l'abonnement."""
        try:
            # Utiliser fonction SQL atomique
            result = self.db.rpc('zero_credits_on_cancel', {
                'p_subscription_id': subscription_id
            }).execute()

            logger.info(f"Crédits mis à zéro pour abonnement annulé: {subscription_id}")

        except Exception as e:
            logger.error(f"Erreur mise à zéro crédits {subscription_id}: {e}")
            raise

    async def _handle_plan_change(self, user_id: str, subscription: Dict[str, Any]) -> None:
        """Gère les changements de plan (upgrades/downgrades).

        SELON LA DOCUMENTATION : Pas de prorata de crédits.
        Le reset des crédits intervient UNIQUEMENT au prochain BILLING_SUCCEEDED.
        """
        try:
            # Récupérer ancien abonnement en DB
            db_subscription = self.db.table('subscriptions').select('price_id').eq('id', subscription['id']).single().execute()

            if not db_subscription.data:
                return

            old_price_id = db_subscription.data.get('price_id')
            new_price_id = subscription.get('items', {}).get('data', [{}])[0].get('price', {}).get('id')

            if old_price_id != new_price_id:
                # Changement de plan détecté - LOG UNIQUEMENT
                logger.info(f"Changement de plan détecté: {old_price_id} -> {new_price_id} pour user {user_id}")

                # PAS D'ACTION SUR LES CRÉDITS ICI
                # Le prochain paiement (invoice.payment_succeeded) réglera les crédits selon le nouveau plan
                # C'est la politique "toujours remplacer, jamais additionner"

        except Exception as e:
            logger.error(f"Erreur gestion changement plan {subscription['id']}: {e}")

    async def _send_subscription_welcome_email(self, user_id: str, subscription: Dict[str, Any]) -> None:
        """Envoie un email de bienvenue lors de la souscription."""
        try:
            # Récupérer info utilisateur
            user_result = self.db.table('users').select('email, full_name').eq('id', user_id).single().execute()
            if not user_result.data:
                logger.warning(f"User {user_id} non trouvé pour email bienvenue")
                return

            user_data = user_result.data

            # Récupérer info plan depuis metadata
            price_id = subscription.get('items', {}).get('data', [{}])[0].get('price', {}).get('id')
            if price_id:
                price_result = self.db.table('prices').select('*, product:products(*)').eq('id', price_id).single().execute()
                if price_result.data:
                    product = price_result.data.get('product', {})
                    plan_name = product.get('name', 'Premium Plan')
                    trial_days = price_result.data.get('trial_period_days')

                    # Envoyer email si service configuré
                    if self.email_service:
                        success = await self.email_service.send_subscription_welcome_email(
                            to_email=user_data['email'],
                            user_name=user_data.get('full_name'),
                            plan_name=plan_name,
                            trial_days=trial_days if trial_days and trial_days > 0 else None
                        )
                        if success:
                            logger.info(f"📧 Email bienvenue envoyé à {user_data['email']} pour {plan_name}")
                        else:
                            logger.error(f"📧 Échec envoi email bienvenue à {user_data['email']}")
                    else:
                        logger.warning("📧 Service email non configuré - email bienvenue ignoré")

        except Exception as e:
            logger.error(f"Erreur envoi email bienvenue {user_id}: {e}")

    async def _send_subscription_cancelled_email(self, user_id: str, subscription: Dict[str, Any]) -> None:
        """Envoie un email de confirmation d'annulation."""
        try:
            # Récupérer info utilisateur
            user_result = self.db.table('users').select('email, full_name').eq('id', user_id).single().execute()
            if not user_result.data:
                logger.warning(f"User {user_id} non trouvé pour email annulation")
                return

            user_data = user_result.data

            # Récupérer info plan depuis metadata
            price_id = subscription.get('items', {}).get('data', [{}])[0].get('price', {}).get('id')
            plan_name = 'Premium Plan'  # Default
            end_date = None

            if price_id:
                price_result = self.db.table('prices').select('*, product:products(*)').eq('id', price_id).single().execute()
                if price_result.data:
                    product = price_result.data.get('product', {})
                    plan_name = product.get('name', 'Premium Plan')

            # Formater la date de fin
            if subscription.get('current_period_end'):
                end_date = datetime.fromtimestamp(subscription['current_period_end'], tz=timezone.utc).strftime('%B %d, %Y')

            # Envoyer email si service configuré
            if self.email_service:
                success = await self.email_service.send_subscription_cancelled_email(
                    to_email=user_data['email'],
                    user_name=user_data.get('full_name'),
                    plan_name=plan_name,
                    end_date=end_date
                )
                if success:
                    logger.info(f"📧 Email annulation envoyé à {user_data['email']} pour {plan_name}")
                else:
                    logger.error(f"📧 Échec envoi email annulation à {user_data['email']}")
            else:
                logger.warning("📧 Service email non configuré - email annulation ignoré")

        except Exception as e:
            logger.error(f"Erreur envoi email annulation {user_id}: {e}")


    async def _handle_payment_failed(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Traite un paiement échoué."""
        try:
            subscription_id = invoice.get('subscription')
            if subscription_id:
                # Marquer abonnement en souffrance
                self.db.table('subscriptions').update({
                    'status': 'past_due',
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).eq('id', subscription_id).execute()

                logger.warning(f"Paiement échoué pour abonnement {subscription_id}")
            
            return {
                'invoice_id': invoice['id'],
                'subscription_id': subscription_id,
                'action': 'marked_past_due'
            }

        except Exception as e:
            logger.error(f"Erreur paiement échoué {invoice['id']}: {e}")
            raise

    async def _handle_checkout_completed(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Traite la completion d'une session checkout."""
        try:
            user_id = session.get('metadata', {}).get('user_id')
            subscription_id = session.get('subscription')

            if user_id and subscription_id:
                logger.info(f"Checkout complété: user {user_id}, subscription {subscription_id}")
                return {
                    'user_id': user_id,
                    'subscription_id': subscription_id,
                    'action': 'checkout_completed'
                }
            else:
                return {'ignored': True, 'reason': 'missing_metadata'}
            
        except Exception as e:
            logger.error(f"Erreur checkout complété {session['id']}: {e}")
            raise

    # =====================================================
    # Utilitaires
    # =====================================================

    async def _is_event_processed(self, event_id: str) -> bool:
        """Vérifie si un événement a déjà été traité."""
        try:
            result = self.db.table('webhook_events').select('id').eq('stripe_event_id', event_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.warning(f"Erreur vérification idempotence {event_id}: {e}")
            return False

    async def _mark_event_processed(self, event_id: str, event_type: str, payload: Dict[str, Any]):
        """Marque un événement comme traité."""
        try:
            self.db.table('webhook_events').insert({
                'stripe_event_id': event_id,
                'event_type': event_type,
                'source': 'stripe',
                'payload': payload
            }).execute()
        except Exception as e:
            logger.error(f"Erreur marquage événement traité {event_id}: {e}")

    async def _get_user_from_subscription(self, subscription_id: str) -> Optional[str]:
        """Récupère l'user_id depuis un subscription_id."""
        try:
            result = self.db.table('subscriptions').select('user_id').eq('id', subscription_id).single().execute()
            return result.data['user_id'] if result.data else None
        except Exception:
            return None

    def _calculate_next_reset(self) -> str:
        """Calcule la date du prochain reset mensuel (début du mois suivant)."""
        from datetime import datetime, timezone
        from dateutil.relativedelta import relativedelta
        
        now = datetime.now(timezone.utc)
        next_month = now + relativedelta(months=1)
        # Premier jour du mois suivant
        next_reset = next_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return next_reset.isoformat()

# Factory function
def get_stripe_service(
    db: Client = Depends(get_db),
    credits_service: CreditsService = Depends(get_credits_service),
    email_service: EmailService = Depends(get_email_service)
) -> StripeService:
    return StripeService(db, credits_service, email_service)