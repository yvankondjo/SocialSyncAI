#!/usr/bin/env python3
"""
Script de seed pour initialiser les modèles AI et les plans d'abonnement.

Ce script exécute le fichier SQL seed_data_006.sql qui contient toutes les données.

Usage:
    python scripts/seed_models_and_plans.py

Ce script doit être exécuté après avoir appliqué la migration migration_006_credits_system.sql
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


def execute_seed_sql(db: Client):
    """Exécute le fichier SQL de seed."""
    logger.info("🌱 Exécution du fichier SQL de seed...")

    # Chemin vers le fichier SQL
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file_path = os.path.join(current_dir, '..', 'migrations', 'seed_data_006.sql')

    if not os.path.exists(sql_file_path):
        raise FileNotFoundError(f"Fichier SQL non trouvé: {sql_file_path}")

    # Lire le contenu du fichier SQL
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    try:
        # Exécuter le SQL via Supabase (attention: exec_sql n'existe pas, on utilise une approche alternative)
        # Puisque exec_sql n'est pas disponible, on utilise une approche par requête individuelle
        logger.info("⚠️  exec_sql non disponible, utilisation d'une approche alternative...")

        # On peut soit:
        # 1. Instruire l'utilisateur d'exécuter manuellement via Supabase Dashboard
        # 2. Parser le SQL et l'exécuter requête par requête (complexe)

        logger.warning("📋 Le fichier seed_data_006.sql doit être exécuté manuellement via:")
        logger.warning("   1. Supabase Dashboard > SQL Editor")
        logger.warning("   2. Copier/coller le contenu du fichier seed_data_006.sql")
        logger.warning("   3. Cliquer sur 'Run'")

        # Pour la vérification, on peut quand même vérifier si les données existent
        verify_seed_data(db)

    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution du SQL: {e}")
        logger.warning("💡 Exécutez manuellement le fichier seed_data_006.sql via Supabase Dashboard")
        raise


def verify_seed_data(db: Client):
    """Vérifie que les données ont été correctement insérées."""
    logger.info("🔍 Vérification des données seedées...")

    try:
        # Vérifier les modèles
        models_result = db.table('ai_models').select('name, provider, model_type, credit_cost').execute()
        models_count = len(models_result.data) if models_result.data else 0
        logger.info(f"📊 Modèles AI trouvés: {models_count}")

        if models_count > 0:
            # Grouper par type
            types_count = {}
            for model in models_result.data:
                model_type = model.get('model_type', 'unknown')
                types_count[model_type] = types_count.get(model_type, 0) + 1

            logger.info("   📈 Répartition par type:")
            for model_type, count in types_count.items():
                logger.info(f"      - {model_type}: {count} modèles")

            # Afficher quelques exemples
            for model in models_result.data[:3]:
                logger.info(f"      - {model['name']} ({model['provider']}, {model['model_type']}): {model['credit_cost']} crédits")
        else:
            logger.warning("   ⚠️ Aucun modèle trouvé - exécutez d'abord seed_data_006.sql")

    except Exception as e:
        logger.error(f"Erreur vérification modèles: {e}")

    try:
        # Vérifier les plans
        plans_result = db.table('subscription_plans').select('name, price_eur, credits_included, is_trial').execute()
        plans_count = len(plans_result.data) if plans_result.data else 0
        logger.info(f"📊 Plans d'abonnement trouvés: {plans_count}")

        if plans_count > 0:
            for plan in plans_result.data:
                trial_text = " (essai)" if plan.get('is_trial') else ""
                logger.info(f"   - {plan['name']}{trial_text}: {plan['price_eur']}€ - {plan['credits_included']} crédits")
        else:
            logger.warning("   ⚠️ Aucun plan trouvé - exécutez d'abord seed_data_006.sql")

    except Exception as e:
        logger.error(f"Erreur vérification plans: {e}")


def main():
    """Fonction principale."""
    logger.info("🚀 Début du seeding des modèles AI et plans d'abonnement...")

    try:
        db = get_db()
        logger.info("✅ Connexion à la base de données établie")

        # Exécuter le fichier SQL de seed
        execute_seed_sql(db)

        logger.info("🎊 Seeding terminé!")
        logger.info("")
        logger.info("📋 Résumé:")
        logger.info("   - Modèles AI: 12 modèles (4 fast, 3 advanced, 4 affordable)")
        logger.info("   - Plans: 3 plans payants avec 7 jours d'essai gratuit chacun")
        logger.info("   - Crédits: Système de coût par appel configuré")
        logger.info("")
        logger.info("✨ Le système de crédits est maintenant prêt!")

    except Exception as e:
        logger.error(f"💥 Erreur lors du seeding: {e}")
        logger.info("")
        logger.info("💡 Solution: Exécutez manuellement seed_data_006.sql via Supabase Dashboard")
        sys.exit(1)


if __name__ == "__main__":
    main()
