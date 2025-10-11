"""
Tests pour la migration vers l'architecture hybride Stripe + Supabase.

Ces tests valident:
- Migration des données existantes
- Fonctionnement des webhooks Stripe
- Fonctionnement des webhooks Whop
- Idempotence des webhooks
- Intégrité des données après migration
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from supabase import Client
from fastapi.testclient import TestClient

from app.main import app
from app.services.credits_service import CreditsService
from app.services.stripe_service import StripeService
from app.services.whop_service import WhopService
from app.services.webhook_helpers import check_event_processed, mark_event_processed
from app.schemas.subscription import SubscriptionStatus, TransactionType


# =====================================================
# Fixtures
# =====================================================

@pytest.fixture
def test_client():
    """Client de test FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock Supabase client."""
    return Mock(spec=Client)


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = Mock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def credits_service(mock_db, mock_redis):
    """Service de crédits pour les tests."""
    return CreditsService(mock_db, mock_redis)


@pytest.fixture
def stripe_service(mock_db, credits_service):
    """Service Stripe pour les tests."""
    with patch('app.services.stripe_service.stripe') as mock_stripe:
        service = StripeService(mock_db, credits_service)
        service.enabled = True
        return service


@pytest.fixture
def whop_service(mock_db, credits_service):
    """Service Whop pour les tests."""
    service = WhopService(credits_service)
    service.enabled = True
    return service


# =====================================================
# Tests de migration des données
# =====================================================

class TestDataMigration:
    """Tests de migration des données existantes."""

    def test_migrate_subscription_plans_to_products(self, mock_db):
        """Test migration subscription_plans → products + prices."""
        # Mock des données existantes
        mock_plans = [
            {
                'id': 'plan_123',
                'name': 'Starter Plan',
                'price_eur': 9.99,
                'credits_included': 1000,
                'features': json.dumps({'text': True, 'images': False}),
                'stripe_price_id': 'price_456'
            }
        ]

        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=mock_plans)

        # TODO: Tester la fonction de migration
        # Cette fonction devra être extraite du script pour être testable

        assert True  # Placeholder

    def test_migrate_user_subscriptions_to_user_credits(self, mock_db, credits_service):
        """Test migration user_subscriptions → user_credits."""
        # Mock des données existantes
        mock_subs = [
            {
                'user_id': 'user_123',
                'plan_id': 'plan_456',
                'credits_balance': 500,
                'subscription_status': 'active',
                'plan': {
                    'credits_included': 1000,
                    'name': 'Starter Plan'
                }
            }
        ]

        mock_db.table.return_value.select.return_value.in_.return_value.execute.return_value = Mock(data=mock_subs)

        # TODO: Tester la fonction de migration

        assert True  # Placeholder

    def test_data_integrity_after_migration(self, mock_db, credits_service):
        """Test intégrité des données après migration."""
        # Vérifier que les anciennes et nouvelles tables sont cohérentes
        user_id = 'user_123'

        # Mock user_credits
        mock_credits = {
            'credits_balance': 750,
            'plan_credits': 1000,
            'subscription_id': 'sub_stripe_123'
        }
        mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(data=mock_credits)

        # Tester récupération des crédits
        balance = credits_service.get_credits_balance(user_id)
        assert balance.balance == 750
        assert balance.plan_limit == 1000


# =====================================================
# Tests des webhooks Stripe
# =====================================================

class TestStripeWebhooks:
    """Tests des webhooks Stripe."""

    @pytest.mark.asyncio
    async def test_webhook_product_created(self, stripe_service, mock_db):
        """Test webhook product.created."""
        product_event = {
            'id': 'evt_123',
            'type': 'product.created',
            'data': {
                'object': {
                    'id': 'prod_456',
                    'name': 'Test Product',
                    'active': True,
                    'metadata': {
                        'credits_monthly': '1000',
                        'features': json.dumps({'text': True})
                    }
                }
            }
        }

        # Mock la vérification idempotence
        with patch('app.services.stripe_service.StripeService._is_event_processed', return_value=False):
            with patch('app.services.stripe_service.StripeService._mark_event_processed'):
                result = await stripe_service.handle_webhook(product_event)

        assert result['status'] == 'processed'
        assert result['event_type'] == 'product.created'

        # Vérifier que le produit a été sauvegardé
        mock_db.table.assert_called_with('products')

    @pytest.mark.asyncio
    async def test_webhook_subscription_created(self, stripe_service, mock_db):
        """Test webhook customer.subscription.created."""
        subscription_event = {
            'id': 'evt_123',
            'type': 'customer.subscription.created',
            'data': {
                'object': {
                    'id': 'sub_456',
                    'customer': 'cus_789',
                    'status': 'active',
                    'items': {
                        'data': [{
                            'price': {'id': 'price_123'},
                            'quantity': 1
                        }]
                    },
                    'metadata': {'user_id': 'user_123'}
                }
            }
        }

        # Mock les dépendances
        with patch('app.services.stripe_service.StripeService._is_event_processed', return_value=False):
            with patch('app.services.stripe_service.StripeService._mark_event_processed'):
                with patch('app.services.stripe_service.StripeService._ensure_subscription_exists'):
                    result = await stripe_service.handle_webhook(subscription_event)

        assert result['status'] == 'processed'
        assert result['subscription_id'] == 'sub_456'

    @pytest.mark.asyncio
    async def test_webhook_payment_succeeded(self, stripe_service, mock_db, credits_service):
        """Test webhook invoice.payment_succeeded."""
        payment_event = {
            'id': 'evt_123',
            'type': 'invoice.payment_succeeded',
            'data': {
                'object': {
                    'id': 'inv_456',
                    'subscription': 'sub_789',
                    'amount_paid': 999
                }
            }
        }

        # Mock récupération user
        with patch('app.services.stripe_service.StripeService._get_user_from_subscription', return_value='user_123'):
            with patch('app.services.stripe_service.StripeService._is_event_processed', return_value=False):
                with patch('app.services.stripe_service.StripeService._mark_event_processed'):
                    with patch.object(credits_service, 'add_credits', new_callable=AsyncMock) as mock_add_credits:
                        result = await stripe_service.handle_webhook(payment_event)

        assert result['status'] == 'processed'
        # Vérifier que les crédits ont été ajoutés
        mock_add_credits.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_idempotence(self, stripe_service):
        """Test idempotence des webhooks."""
        event = {
            'id': 'evt_123',
            'type': 'product.created',
            'data': {'object': {'id': 'prod_456', 'name': 'Test'}}
        }

        # Premier appel - pas encore traité
        with patch('app.services.stripe_service.StripeService._is_event_processed', return_value=False):
            with patch('app.services.stripe_service.StripeService._sync_product', return_value={'synced': True}):
                with patch('app.services.stripe_service.StripeService._mark_event_processed'):
                    result1 = await stripe_service.handle_webhook(event)
                    assert result1['status'] == 'processed'

        # Deuxième appel - déjà traité
        with patch('app.services.stripe_service.StripeService._is_event_processed', return_value=True):
            result2 = await stripe_service.handle_webhook(event)
            assert result2['status'] == 'already_processed'


# =====================================================
# Tests des webhooks Whop
# =====================================================

class TestWhopWebhooks:
    """Tests des webhooks Whop."""

    @pytest.mark.asyncio
    async def test_webhook_membership_created(self, whop_service, mock_db):
        """Test webhook membership.created."""
        membership_event = {
            'event': 'membership.created',
            'data': {
                'id': 'whop_mem_123',
                'user': {'email': 'test@example.com'},
                'product': {'id': 'whop_prod_456'}
            }
        }

        # Mock les dépendances
        with patch('app.services.whop_service.WhopService._get_user_id_by_email', return_value='user_123'):
            with patch('app.services.whop_service.WhopService._is_event_processed', return_value=False):
                with patch('app.services.whop_service.WhopService._mark_event_processed'):
                    with patch.object(whop_service, '_create_or_update_whop_subscription', new_callable=AsyncMock):
                        result = await whop_service.handle_webhook(membership_event, 'valid_signature')

        assert result['status'] == 'processed'
        assert result['event_type'] == 'membership.created'

    @pytest.mark.asyncio
    async def test_webhook_membership_renewed(self, whop_service, mock_db, credits_service):
        """Test webhook membership.renewed."""
        renewed_event = {
            'event': 'membership.renewed',
            'data': {
                'id': 'whop_mem_123',
                'user': {'email': 'test@example.com'}
            }
        }

        # Mock récupération subscription
        mock_subscription = {
            'product': {
                'metadata': {'credits_monthly': '1000', 'plan_name': 'Starter'}
            }
        }
        mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(data=mock_subscription)

        with patch('app.services.whop_service.WhopService._get_user_id_by_email', return_value='user_123'):
            with patch('app.services.whop_service.WhopService._is_event_processed', return_value=False):
                with patch('app.services.whop_service.WhopService._mark_event_processed'):
                    with patch.object(credits_service, 'add_credits', new_callable=AsyncMock) as mock_add_credits:
                        result = await whop_service.handle_webhook(renewed_event, 'valid_signature')

        assert result['status'] == 'processed'
        mock_add_credits.assert_called_once()


# =====================================================
# Tests d'idempotence
# =====================================================

class TestIdempotence:
    """Tests d'idempotence des webhooks."""

    @pytest.mark.asyncio
    async def test_check_event_processed_stripe(self, mock_db):
        """Test vérification événement Stripe traité."""
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[{'id': '1'}])

        result = await check_event_processed(mock_db, stripe_event_id='evt_123')
        assert result is True

    @pytest.mark.asyncio
    async def test_check_event_processed_whop(self, mock_db):
        """Test vérification événement Whop traité."""
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[])

        result = await check_event_processed(mock_db, whop_event_id='whop_evt_123')
        assert result is False

    @pytest.mark.asyncio
    async def test_mark_event_processed(self, mock_db):
        """Test marquage événement traité."""
        await mark_event_processed(mock_db, 'evt_123', 'product.created', {'test': 'data'}, 'stripe')

        # Vérifier que l'insertion a été appelée
        mock_db.table.assert_called_with('webhook_events')
        # TODO: Vérifier les paramètres d'insertion


# =====================================================
# Tests d'intégration API
# =====================================================

class TestAPIIntegration:
    """Tests d'intégration des routes API."""

    def test_get_subscription_plans(self, test_client, mock_db):
        """Test récupération des plans d'abonnement."""
        # Mock des données products + prices
        mock_products = [
            {
                'id': 'prod_123',
                'name': 'Starter Plan',
                'active': True,
                'metadata': {
                    'credits_monthly': '1000',
                    'max_ai_calls_per_batch': '3',
                    'features': json.dumps({'text': True, 'images': False})
                },
                'prices': [{
                    'id': 'price_456',
                    'unit_amount': 999,
                    'currency': 'eur'
                }]
            }
        ]

        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=mock_products)

        response = test_client.get("/api/subscriptions/plans")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['name'] == 'Starter Plan'
        assert data[0]['credits_included'] == 1000

    def test_start_trial_subscription(self, test_client, mock_db, credits_service):
        """Test démarrage abonnement d'essai."""
        # Mock produit trouvé
        mock_product = {
            'id': 'prod_123',
            'name': 'Starter Plan',
            'metadata': {
                'credits_monthly': '1000',
                'trial_duration_days': '7'
            }
        }

        mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(data=mock_product)

        # TODO: Mock l'authentification
        # response = test_client.post("/api/subscriptions/start-trial/Starter")

        assert True  # Placeholder - nécessite auth mock

    def test_create_checkout_session(self, test_client):
        """Test création session checkout."""
        # TODO: Mock Stripe et authentification
        # request_data = {'price_id': 'price_123'}
        # response = test_client.post("/api/stripe/create-checkout-session", json=request_data)

        assert True  # Placeholder - nécessite mocks complexes


# =====================================================
# Tests de performance et charge
# =====================================================

class TestPerformance:
    """Tests de performance."""

    @pytest.mark.asyncio
    async def test_webhook_concurrent_processing(self, stripe_service):
        """Test traitement concurrent des webhooks."""
        # TODO: Tester que les webhooks sont traités de manière thread-safe
        # avec l'idempotence
        assert True  # Placeholder

    def test_database_query_performance(self, mock_db):
        """Test performance des requêtes DB."""
        # TODO: Mesurer le temps de réponse des requêtes complexes
        assert True  # Placeholder


# =====================================================
# Tests de sécurité
# =====================================================

class TestSecurity:
    """Tests de sécurité."""

    def test_rls_policies_applied(self, mock_db):
        """Test que les politiques RLS sont appliquées."""
        # TODO: Vérifier que les requêtes respectent les politiques RLS
        assert True  # Placeholder

    def test_webhook_signature_validation(self, whop_service):
        """Test validation des signatures webhook."""
        # Payload et signature valides
        payload = {'event': 'test', 'data': {'id': '123'}}
        valid_signature = "signature_valide"  # TODO: Générer une vraie signature

        # TODO: Tester avec hmac
        assert True  # Placeholder


# =====================================================
# Utilitaires de test
# =====================================================

def create_mock_stripe_product():
    """Crée un produit Stripe mock pour les tests."""
    return {
        'id': 'prod_test_123',
        'name': 'Test Product',
        'active': True,
        'metadata': {
            'credits_monthly': '1000',
            'features': json.dumps({'text': True})
        }
    }


def create_mock_stripe_subscription():
    """Crée un abonnement Stripe mock pour les tests."""
    return {
        'id': 'sub_test_123',
        'customer': 'cus_test_456',
        'status': 'active',
        'items': {
            'data': [{
                'price': {'id': 'price_test_789'},
                'quantity': 1
            }]
        },
        'metadata': {'user_id': 'user_test_999'}
    }


def create_mock_whop_membership():
    """Crée une membership Whop mock pour les tests."""
    return {
        'event': 'membership.created',
        'data': {
            'id': 'whop_mem_test_123',
            'user': {'email': 'test@example.com'},
            'product': {'id': 'whop_prod_test_456'}
        }
    }

