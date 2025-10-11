#!/usr/bin/env python3
"""
Script de création des produits Whop pour l'architecture hybride.

Ce script crée automatiquement les produits dans Whop marketplace avec les métadonnées
nécessaires pour l'architecture hybride (crédits, features, etc.).

⚠️  ATTENTION: Ce script utilise l'API Whop qui n'est pas documentée publiquement.
   Les appels API devront être adaptés selon la documentation Whop réelle.

Usage:
    python scripts/create_whop_products.py [--dry-run] [--force]

Options:
    --dry-run: Affiche ce qui serait créé sans rien faire
    --force: Supprime et recrée les produits existants

Le script doit être exécuté APRÈS avoir configuré les variables d'environnement Whop.
"""

import sys
import os
import json
import argparse
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import httpx

from supabase import create_client, Client
from app.core.config import get_settings

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration des plans pour Whop
WHOP_PLANS = [
    {
        'name': 'Starter Plan',
        'description': 'Starter Plan with base features for starting with AI',
        'price_usd': 9.99,
        'trial_days': 7,
        'metadata': {
            'whop_product_id': '',  # Sera rempli après création
            'credits_monthly': '1000',
            'max_ai_calls_per_batch': '3',
            'storage_quota_mb': '10',
            'features': json.dumps({
                'text': True,
                'images': False,
                'audio': False
            }),
            'plan_name': 'Starter',
            'tier': 'starter'
        },
        'whop_data': {
            'name': 'Starter Plan - AI Assistant',
            'description': 'Basic access to our AI assistant with 1000 credits per month',
            'price': 999,  # Prix en cents
            'access_pass': True,  # Type d'accès Whop
            'visibility': 'public',
            'custom_fields': [
                {'name': 'Credits Monthly', 'value': '1000'},
                {'name': 'Features', 'value': 'text'}
            ]
        }
    },
    {
        'name': 'Pro Plan',
        'description': 'Pro Plan with image processing for creatives',
        'price_usd': 29.99,
        'trial_days': 7,
        'metadata': {
            'whop_product_id': '',
            'credits_monthly': '2500',
            'max_ai_calls_per_batch': '5',
            'storage_quota_mb': '20',
            'features': json.dumps({
                'text': True,
                'images': True,
                'audio': False
            }),
            'plan_name': 'Pro',
            'tier': 'pro'
        },
        'whop_data': {
            'name': 'Pro Plan - AI Assistant + Images',
            'description': 'Advanced AI assistant with image processing and 2500 credits per month',
            'price': 2999,
            'access_pass': True,
            'visibility': 'public',
            'custom_fields': [
                {'name': 'Credits Monthly', 'value': '2500'},
                {'name': 'Features', 'value': 'text,images'}
            ]
        }
    },
    {
        'name': 'Plus Plan',
        'description': 'Plus Plan with audio for professionals',
        'price_usd': 49.99,
        'trial_days': 7,
        'metadata': {
            'whop_product_id': '',
            'credits_monthly': '6000',
            'max_ai_calls_per_batch': '8',
            'storage_quota_mb': '40',
            'features': json.dumps({
                'text': True,
                'images': True,
                'audio': True
            }),
            'plan_name': 'Plus',
            'tier': 'plus'
        },
        'whop_data': {
            'name': 'Plus Plan - AI Assistant Complete',
            'description': 'Complete AI assistant with text, images and audio - 6000 credits per month',
            'price': 4999,
            'access_pass': True,
            'visibility': 'public',
            'custom_fields': [
                {'name': 'Credits Monthly', 'value': '6000'},
                {'name': 'Features', 'value': 'text,images,audio'}
            ]
        }
    }
]


def get_whop_client():
    """Obtient le client Whop configuré."""
    try:
        settings = get_settings()

        if not hasattr(settings, 'WHOP_API_KEY') or not settings.WHOP_API_KEY:
            raise ValueError("WHOP_API_KEY non configuré")

        return httpx.AsyncClient(
            base_url="https://api.whop.com/api/v2",
            headers={"Authorization": f"Bearer {settings.WHOP_API_KEY}"},
            timeout=30.0
        )
    except Exception as e:
        logger.error(f"❌ Erreur configuration Whop: {e}")
        sys.exit(1)


def get_db() -> Client:
    """Obtient une connexion à la base de données Supabase."""
    try:
        settings = get_settings()
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        logger.error(f"❌ Erreur connexion Supabase: {e}")
        sys.exit(1)


def find_existing_products_whop(client, db):
    """Trouve les produits existants dans Whop et Supabase."""
    try:
        # Produits dans Supabase (source = whop)
        result = db.table('products').select('id, name, metadata').eq('source', 'whop').execute()
        supabase_products = {p['id']: p for p in result.data}

        # Note: L'API Whop pour lister les produits n'est pas connue
        # Cette fonction devra être adaptée selon la doc Whop
        logger.warning("⚠️  Recherche produits Whop - À adapter selon API Whop")

        return {}, supabase_products  # Placeholder
    except Exception as e:
        logger.error(f"Erreur récupération produits Whop existants: {e}")
        return {}, {}


async def create_whop_product(client, plan: Dict[str, Any], dry_run: bool = False):
    """
    Crée un produit dans Whop.

    ⚠️  CETTE FONCTION EST UN PLACEHOLDER
        Elle devra être adaptée selon la documentation API Whop réelle.
    """
    try:
        logger.info(f"📦 Création produit Whop: {plan['name']}")

        if dry_run:
            logger.info(f"   [DRY-RUN] Produit: {plan['name']}")
            logger.info(f"   [DRY-RUN] Prix: {plan['price_usd']}$")
            logger.info(f"   [DRY-RUN] Crédits: {plan['metadata']['credits_monthly']}")
            return {
                'product': {
                    'id': f'dry-run-whop-{plan["name"].lower().replace(" ", "-")}',
                    'name': plan['name'],
                    'description': plan['description'],
                    'price': int(plan['price_usd'] * 100)
                },
                'dry_run': True
            }

        # ⚠️  PLACEHOLDER - À adapter selon API Whop réelle
        #
        # Exemple d'appel API Whop (à vérifier dans la documentation):
        # response = await client.post("/products", json={
        #     "name": plan['whop_data']['name'],
        #     "description": plan['whop_data']['description'],
        #     "price": plan['whop_data']['price'],
        #     "access_pass": plan['whop_data']['access_pass'],
        #     "visibility": plan['whop_data']['visibility'],
        #     "custom_fields": plan['whop_data']['custom_fields']
        # })
        #
        # whop_product = response.json()

        # Simulation pour le moment
        whop_product = {
            'id': f'whop_{plan["name"].lower().replace(" ", "_")}_{hash(str(plan)) % 10000}',
            'name': plan['whop_data']['name'],
            'price': plan['whop_data']['price'],
            'created_at': '2025-01-10T00:00:00Z'
        }

        logger.warning("⚠️  Création Whop simulée - adapter selon API réelle")
        logger.info(f"✅ Produit Whop simulé: {whop_product['id']}")

        return {'product': whop_product}

    except Exception as e:
        logger.error(f"❌ Erreur création produit Whop {plan['name']}: {e}")
        raise


async def sync_whop_to_supabase(db, whop_data: Dict[str, Any], plan_config: Dict[str, Any], dry_run: bool = False):
    """Synchronise les données Whop vers Supabase."""
    try:
        whop_product = whop_data['product']

        if dry_run:
            logger.info(f"   [DRY-RUN] Sync DB produit Whop: {whop_product['id']}")
            return

        # Sync produit Whop
        db.table('products').upsert({
            'id': whop_product['id'],
            'active': True,  # Whop products are active by default
            'name': whop_product.get('name', plan_config['name']),
            'description': plan_config['description'],
            'image': None,  # Whop peut avoir des images
            'metadata': plan_config['metadata'],
            'source': 'whop'
        }).execute()

        logger.info(f"✅ Sync DB Whop terminée pour {whop_product['id']}")

    except Exception as e:
        logger.error(f"❌ Erreur sync DB Whop pour {whop_product['id']}: {e}")
        raise


async def delete_existing_whop_products(client, db, whop_products, supabase_products, force: bool = False):
    """Supprime les produits Whop existants si force=True."""
    if not force:
        return

    logger.warning("🗑️  Suppression des produits Whop existants (--force activé)")

    try:
        # ⚠️  PLACEHOLDER - À adapter selon API Whop
        # Pour chaque produit Whop, appeler DELETE /products/{id}
        # for prod_id in whop_products:
        #     await client.delete(f"/products/{prod_id}")

        logger.warning("⚠️  Suppression Whop simulée - adapter selon API réelle")

        # Supprimer de Supabase
        for prod_id in supabase_products:
            db.table('products').delete().eq('id', prod_id).execute()

        logger.info("✅ Produits Whop existants supprimés (simulation)")

    except Exception as e:
        logger.error(f"❌ Erreur suppression produits Whop: {e}")
        raise


async def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(description='Créer des produits Whop pour l\'architecture hybride')
    parser.add_argument('--dry-run', action='store_true', help='Affiche les actions sans les exécuter')
    parser.add_argument('--force', action='store_true', help='Supprime et recrée les produits existants')

    args = parser.parse_args()

    logger.info("🚀 Démarrage création produits Whop")
    logger.info(f"   Mode dry-run: {args.dry_run}")
    logger.info(f"   Mode force: {args.force}")
    logger.warning("⚠️  Ce script utilise des appels API Whop simulés - À adapter selon doc API")

    # Initialisation clients
    client = get_whop_client()
    db = get_db()

    try:
        # Vérifier produits existants
        whop_products, supabase_products = find_existing_products_whop(client, db)

        if supabase_products and not args.force:
            logger.warning(f"⚠️  {len(supabase_products)} produits Whop existent déjà dans DB")
            logger.warning("   Utilisez --force pour les supprimer et recréer")
            logger.warning("   Ou --dry-run pour voir ce qui serait créé")
            return

        # Supprimer produits existants si force
        if args.force:
            await delete_existing_whop_products(client, db, whop_products, supabase_products, args.force)

        # Créer les produits
        created_products = []
        for plan in WHOP_PLANS:
            try:
                whop_data = await create_whop_product(client, plan, args.dry_run)
                await sync_whop_to_supabase(db, whop_data, plan, args.dry_run)
                created_products.append(whop_data)

                if not args.dry_run:
                    logger.info(f"✅ {plan['name']} créé avec succès")

            except Exception as e:
                logger.error(f"❌ Échec création {plan['name']}: {e}")
                if not args.force:  # Arrêter si pas en mode force
                    raise

        # Fermer le client HTTP
        await client.aclose()

        # Résumé
        logger.info("\n📊 Résumé:")
        logger.info(f"   Produits créés: {len(created_products)}")
        logger.info(f"   Mode: {'DRY-RUN' if args.dry_run else 'PRODUCTION'}")

        if not args.dry_run:
            logger.warning("⚠️  IMPORTANT: Adapter les appels API selon documentation Whop")
            logger.info("\n🎯 Prochaines étapes:")
            logger.info("   1. Vérifier la documentation API Whop")
            logger.info("   2. Adapter les appels API dans ce script")
            logger.info("   3. Tester les webhooks Whop")
            logger.info("   4. Exécuter le script de migration des données existantes")

    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
        await client.aclose()
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
