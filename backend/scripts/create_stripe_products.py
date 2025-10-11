#!/usr/bin/env python3
"""
Script de création des produits Stripe pour l'architecture hybride.

Ce script crée automatiquement les produits et prix dans Stripe avec les métadonnées
nécessaires pour l'architecture hybride (crédits, features, etc.).

Usage:
    python scripts/create_stripe_products.py [--dry-run] [--force]

Options:
    --dry-run: Affiche ce qui serait créé sans rien faire
    --force: Supprime et recrée les produits existants

Le script doit être exécuté APRÈS avoir configuré les variables d'environnement Stripe.
"""

import sys
import os
import json
import argparse
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from supabase import create_client, Client

from app.core.config import get_settings

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration des plans
PLANS = [
    {
        'name': 'Starter Plan',
        'description': 'Starter Plan with base features for starting with AI',
        'price_eur': 9.99,
        'trial_days': 7,
        'metadata': {
            'credits_monthly': '1000',
            'max_ai_calls_per_batch': '3',
            'storage_quota_mb': '10',
            'features': json.dumps({
                'text': True,
                'images': False,
                'audio': False
            }),
            'plan_name': 'Starter',
            'tier': 'starter',
            'trial_duration_days': '7'
        }
    },
    {
        'name': 'Pro Plan',
        'description': 'Pro Plan with image processing for creatives',
        'price_eur': 29.99,
        'trial_days': 7,
        'metadata': {
            'credits_monthly': '2500',
            'max_ai_calls_per_batch': '5',
            'storage_quota_mb': '20',
            'features': json.dumps({
                'text': True,
                'images': True,
                'audio': False
            }),
            'plan_name': 'Pro',
            'tier': 'pro',
            'trial_duration_days': '7'
        }
    },
    {
        'name': 'Plus Plan',
        'description': 'Plus Plan with audio for professionals',
        'price_eur': 49.99,
        'trial_days': 7,
        'metadata': {
            'credits_monthly': '6000',
            'max_ai_calls_per_batch': '8',
            'storage_quota_mb': '40',
            'features': json.dumps({
                'text': True,
                'images': True,
                'audio': True
            }),
            'plan_name': 'Plus',
            'tier': 'plus',
            'trial_duration_days': '7'
        }
    }
]


def get_stripe_client():
    """Obtient le client Stripe configuré."""
    try:
        import stripe
        settings = get_settings()

        if not hasattr(settings, 'STRIPE_SECRET_KEY') or not settings.STRIPE_SECRET_KEY:
            raise ValueError("STRIPE_SECRET_KEY non configuré")

        stripe.api_key = settings.STRIPE_SECRET_KEY
        return stripe
    except ImportError:
        logger.error("❌ Stripe non installé. Installez avec: pip install stripe")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erreur configuration Stripe: {e}")
        sys.exit(1)


def get_db() -> Client:
    """Obtient une connexion à la base de données Supabase."""
    try:
        settings = get_settings()
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        logger.error(f"❌ Erreur connexion Supabase: {e}")
        sys.exit(1)


def find_existing_products(stripe, db):
    """Trouve les produits existants dans Stripe et Supabase."""
    try:
        # Produits dans Stripe
        stripe_products = stripe.Product.list(limit=100)
        stripe_product_ids = {p['id']: p for p in stripe_products['data']}

        # Produits dans Supabase
        result = db.table('products').select('id, name, source').eq('source', 'stripe').execute()
        supabase_products = {p['id']: p for p in result.data}

        return stripe_product_ids, supabase_products
    except Exception as e:
        logger.error(f"Erreur récupération produits existants: {e}")
        return {}, {}


def create_stripe_product(stripe, plan: Dict[str, Any], dry_run: bool = False):
    """Crée un produit et un prix dans Stripe."""
    try:
        logger.info(f"📦 Création produit Stripe: {plan['name']}")

        if dry_run:
            logger.info(f"   [DRY-RUN] Produit: {plan['name']}")
            logger.info(f"   [DRY-RUN] Prix: {plan['price_eur']}€/mois")
            logger.info(f"   [DRY-RUN] Crédits: {plan['metadata']['credits_monthly']}")
            return {
                'product': {
                    'id': f'dry-run-prod-{plan["name"].lower().replace(" ", "-")}',
                    'name': plan['name'],
                    'description': plan['description'],
                    'active': True,
                    'metadata': plan['metadata'],
                    'images': []
                },
                'price': {
                    'id': f'dry-run-price-{plan["name"].lower().replace(" ", "-")}',
                    'unit_amount': int(plan['price_eur'] * 100),
                    'currency': 'eur',
                    'type': 'recurring',
                    'active': True,
                    'recurring': {'interval': 'month', 'interval_count': 1, 'trial_period_days': plan.get('trial_days', 0)},
                    'metadata': {'plan_name': plan['name']}
                },
                'dry_run': True
            }

        # Créer le produit
        product = stripe.Product.create(
            name=plan['name'],
            description=plan['description'],
            metadata=plan['metadata']
        )

        # Créer le prix récurrent
        price = stripe.Price.create(
            product=product.id,
            unit_amount=int(plan['price_eur'] * 100),  # Convertir en centimes
            currency='eur',
            recurring={'interval': 'month'},
            metadata={'plan_name': plan['name'], 'trial_days': str(plan['trial_days'])}
        )

        logger.info(f"✅ Produit créé: {product.id}")
        logger.info(f"✅ Prix créé: {price.id} ({plan['price_eur']}€/mois)")

        return {'product': product, 'price': price}

    except Exception as e:
        logger.error(f"❌ Erreur création produit {plan['name']}: {e}")
        raise


def sync_to_supabase(db, stripe_data: Dict[str, Any], dry_run: bool = False):
    """Synchronise les données Stripe vers Supabase."""
    try:
        product = stripe_data['product']
        price = stripe_data['price']

        if dry_run:
            logger.info(f"   [DRY-RUN] Sync DB produit: {product['id']}")
            return

        # Sync produit
        product_payload = {
            'id': product['id'],
            'active': product.get('active', True),
            'name': product.get('name'),
            'description': product.get('description'),
            'image': (product.get('images') or [None])[0],
            'metadata': product.get('metadata', {}),
            'source': 'stripe'
        }

        product_result = db.table('products').upsert(product_payload).execute()
        product_error = getattr(product_result, 'error', None)
        if product_error:
            raise RuntimeError(f"Supabase upsert produit {product['id']} a échoué: {product_error}")

        if getattr(product_result, 'data', None) is None:
            logger.warning(f"Upsert produit {product['id']} n'a pas retourné de données (peut-être déjà présent)")

        # Sync prix
        price_recurring = price.get('recurring') or {}
        price_payload = {
            'id': price['id'],
            'product_id': product['id'],
            'active': price.get('active', True),
            'description': price.get('metadata', {}).get('plan_name'),
            'unit_amount': price['unit_amount'],
            'currency': price['currency'],
            'type': price.get('type', 'recurring'),
            'interval': price_recurring.get('interval'),
            'interval_count': price_recurring.get('interval_count', 1),
            'trial_period_days': price_recurring.get('trial_period_days'),
            'metadata': price.get('metadata', {})
        }

        price_result = db.table('prices').upsert(price_payload).execute()
        price_error = getattr(price_result, 'error', None)
        if price_error:
            raise RuntimeError(f"Supabase upsert prix {price['id']} a échoué: {price_error}")

        if getattr(price_result, 'data', None) is None:
            logger.warning(f"Upsert prix {price['id']} n'a pas retourné de données (peut-être déjà présent)")

        logger.info(f"✅ Sync DB terminée pour {product['id']}")

    except Exception as e:
        logger.error(f"❌ Erreur sync DB pour {product['id']}: {e}")
        raise


def delete_existing_products(stripe, db, stripe_products, supabase_products, force: bool = False):
    """Supprime les produits existants si force=True."""
    if not force:
        return

    logger.warning("🗑️  Suppression des produits existants (--force activé)")

    try:
        # Supprimer les prix d'abord
        for prod_id, product in stripe_products.items():
            prices = stripe.Price.list(product=prod_id, limit=10)
            for price in prices['data']:
                if not price.get('deleted', False):
                    logger.info(f"   Suppression prix: {price['id']}")
                    stripe.Price.modify(price['id'], active=False)

            # Supprimer le produit
            logger.info(f"   Suppression produit: {prod_id}")
            stripe.Product.modify(prod_id, active=False)

        # Supprimer de Supabase
        for prod_id in supabase_products:
            db.table('products').delete().eq('id', prod_id).execute()
            db.table('prices').delete().eq('product_id', prod_id).execute()

        logger.info("✅ Produits existants supprimés")

    except Exception as e:
        logger.error(f"❌ Erreur suppression produits: {e}")
        raise


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(description='Créer des produits Stripe pour l\'architecture hybride')
    parser.add_argument('--dry-run', action='store_true', help='Affiche les actions sans les exécuter')
    parser.add_argument('--force', action='store_true', help='Supprime et recrée les produits existants')

    args = parser.parse_args()

    logger.info("🚀 Démarrage création produits Stripe")
    logger.info(f"   Mode dry-run: {args.dry_run}")
    logger.info(f"   Mode force: {args.force}")

    # Initialisation clients
    stripe = get_stripe_client()
    db = get_db()

    try:
        # Vérifier produits existants
        stripe_products, supabase_products = find_existing_products(stripe, db)

        if stripe_products and not args.force:
            logger.warning(f"⚠️  {len(stripe_products)} produits existent déjà dans Stripe")
            logger.warning("   Utilisez --force pour les supprimer et recréer")
            logger.warning("   Ou --dry-run pour voir ce qui serait créé")
            return

        # Supprimer produits existants si force
        if args.force:
            delete_existing_products(stripe, db, stripe_products, supabase_products, args.force)

        # Créer les produits
        created_products = []
        for plan in PLANS:
            try:
                stripe_data = create_stripe_product(stripe, plan, args.dry_run)
                sync_to_supabase(db, stripe_data, args.dry_run)
                created_products.append(stripe_data)

                if not args.dry_run:
                    logger.info(f"✅ {plan['name']} créé avec succès")

            except Exception as e:
                logger.error(f"❌ Échec création {plan['name']}: {e}")
                if not args.force:  # Arrêter si pas en mode force
                    raise

        # Résumé
        logger.info("\n📊 Résumé:")
        logger.info(f"   Produits créés: {len(created_products)}")
        logger.info(f"   Mode: {'DRY-RUN' if args.dry_run else 'PRODUCTION'}")

        if not args.dry_run:
            logger.info("\n🎯 Prochaines étapes:")
            logger.info("   1. Configurer les webhooks Stripe dans le dashboard")
            logger.info("   2. Tester les webhooks avec des événements de test")
            logger.info("   3. Exécuter le script de migration des données existantes")

    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
