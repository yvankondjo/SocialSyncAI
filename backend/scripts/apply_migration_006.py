#!/usr/bin/env python3
"""
Script pour appliquer la migration 006 du système de crédits.

Usage:
    python scripts/apply_migration_006.py

Ce script applique la migration SQL via le client Supabase.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from supabase import create_client, Client

from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db() -> Client:
    """Obtient une connexion à la base de données Supabase."""
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def apply_migration(db: Client):
    """Applique la migration via des requêtes individuelles."""
    logger.info("🔧 Application de la migration via requêtes individuelles...")

    try:
        # 1. Créer la table ai_models
        logger.info("📋 Création de la table ai_models...")
        db.table('ai_models').select('*').limit(1).execute()  # Test si elle existe
        logger.info("✅ Table ai_models existe déjà")
    except Exception:
        # Table n'existe pas, la créer via un insert test
        logger.info("⚠️ Table ai_models n'existe pas - migration nécessaire manuellement")
        logger.info("💡 Veuillez exécuter le fichier migration_006_credits_system.sql manuellement")
        logger.info("   ou via l'interface Supabase SQL Editor")
        return False

    try:
        # 2. Créer la table subscription_plans
        logger.info("📋 Vérification de la table subscription_plans...")
        db.table('subscription_plans').select('*').limit(1).execute()
        logger.info("✅ Table subscription_plans existe déjà")
    except Exception:
        logger.info("⚠️ Table subscription_plans n'existe pas - migration nécessaire manuellement")
        return False

    try:
        # 3. Créer la table user_subscriptions
        logger.info("📋 Vérification de la table user_subscriptions...")
        db.table('user_subscriptions').select('*').limit(1).execute()
        logger.info("✅ Table user_subscriptions existe déjà")
    except Exception:
        logger.info("⚠️ Table user_subscriptions n'existe pas - migration nécessaire manuellement")
        return False

    try:
        # 4. Créer la table credit_transactions
        logger.info("📋 Vérification de la table credit_transactions...")
        db.table('credit_transactions').select('*').limit(1).execute()
        logger.info("✅ Table credit_transactions existe déjà")
        return True
    except Exception:
        logger.info("⚠️ Table credit_transactions n'existe pas - migration nécessaire manuellement")
        return False


def verify_migration(db: Client):
    """Vérifie que la migration a été appliquée correctement."""
    logger.info("🔍 Vérification de la migration...")

    tables_to_check = [
        'ai_models',
        'subscription_plans',
        'user_subscriptions',
        'credit_transactions'
    ]

    for table in tables_to_check:
        try:
            # Essayer de compter les lignes dans chaque table
            result = db.table(table).select('*', count='exact').limit(1).execute()
            logger.info(f"✅ Table '{table}' existe ({result.count} enregistrements)")
        except Exception as e:
            logger.error(f"❌ Table '{table}' non trouvée ou inaccessible: {e}")
            return False

    # Vérifier les données seedées
    try:
        models_result = db.table('ai_models').select('name', count='exact').execute()
        plans_result = db.table('subscription_plans').select('name', count='exact').execute()

        logger.info(f"📊 {models_result.count} modèles AI seedés")
        logger.info(f"📊 {plans_result.count} plans d'abonnement seedés")

        if models_result.count == 0:
            logger.warning("⚠️ Aucun modèle AI trouvé - lancer le script de seed")
        if plans_result.count == 0:
            logger.warning("⚠️ Aucun plan d'abonnement trouvé - lancer le script de seed")

    except Exception as e:
        logger.error(f"Erreur vérification données seedées: {e}")

    logger.info("✅ Vérification terminée")
    return True


def main():
    """Fonction principale."""
    logger.info("🚀 Vérification de la migration 006 - Système de Crédits...")

    try:
        db = get_db()
        logger.info("✅ Connexion à la base de données établie")

        # Vérifier si la migration est déjà appliquée
        migration_applied = apply_migration(db)

        if migration_applied:
            logger.info("")
            logger.info("🎊 Migration 006 déjà appliquée!")
            logger.info("")
            logger.info("📋 Prochaines étapes:")
            logger.info("   1. Lancer le script de seed: python scripts/seed_models_and_plans.py")
            logger.info("   2. Tester l'API: GET /api/subscriptions/plans")
            logger.info("   3. Vérifier les configurations Redis/Stripe/Whop dans .env")
        else:
            logger.info("")
            logger.info("⚠️ Migration 006 non appliquée")
            logger.info("")
            logger.info("📋 Instructions manuelles:")
            logger.info("   1. Ouvrir Supabase Dashboard > SQL Editor")
            logger.info("   2. Copier le contenu de: backend/migrations/migration_006_credits_system.sql")
            logger.info("   3. Exécuter le script SQL")
            logger.info("   4. Relancer ce script pour vérifier")
            logger.info("")
            logger.info("💡 Alternative: Utiliser psql directement si accès DB")
            sys.exit(1)

    except Exception as e:
        logger.error(f"💥 Erreur lors de la vérification: {e}")
        logger.info("")
        logger.info("📋 Instructions manuelles:")
        logger.info("   1. Ouvrir Supabase Dashboard > SQL Editor")
        logger.info("   2. Copier le contenu de: backend/migrations/migration_006_credits_system.sql")
        logger.info("   3. Exécuter le script SQL")
        sys.exit(1)


if __name__ == "__main__":
    main()
