#!/usr/bin/env python3
"""
Script de test pour vérifier le système de quota de stockage.
Teste les endpoints, les calculs et l'intégrité des données.
"""

import os
import sys
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import get_db
from app.services.credits_service import get_credits_service
from app.services.storage_service import get_storage_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_storage_quota_system():
    """Test complet du système de quota de stockage."""

    logger.info("🚀 Début des tests du système de quota de stockage")

    try:
        # 1. Test des schémas de base de données
        logger.info("📋 Test 1: Vérification des colonnes de base de données")
        db = get_db()

        # Vérifier les colonnes dans subscription_plans
        plans_columns = db.table('subscription_plans').select('*').limit(1).execute()
        if plans_columns.data:
            plan = plans_columns.data[0]
            assert 'storage_quota_mb' in plan, "Colonne storage_quota_mb manquante dans subscription_plans"
            logger.info("✅ Colonne storage_quota_mb présente dans subscription_plans")

        # Vérifier les colonnes dans user_subscriptions
        subs_columns = db.table('user_subscriptions').select('*').limit(1).execute()
        if subs_columns.data:
            sub = subs_columns.data[0]
            assert 'storage_used_mb' in sub, "Colonne storage_used_mb manquante dans user_subscriptions"
            logger.info("✅ Colonne storage_used_mb présente dans user_subscriptions")

        # Vérifier les colonnes dans knowledge_documents
        docs_columns = db.table('knowledge_documents').select('*').limit(1).execute()
        if docs_columns.data:
            doc = docs_columns.data[0]
            assert 'file_size_bytes' in doc, "Colonne file_size_bytes manquante dans knowledge_documents"
            logger.info("✅ Colonne file_size_bytes présente dans knowledge_documents")

        # Vérifier les colonnes dans faq_qa
        faq_columns = db.table('faq_qa').select('*').limit(1).execute()
        if faq_columns.data:
            faq = faq_columns.data[0]
            assert 'text_size_bytes' in faq, "Colonne text_size_bytes manquante dans faq_qa"
            logger.info("✅ Colonne text_size_bytes présente dans faq_qa")

        # 2. Test des données de seed
        logger.info("📋 Test 2: Vérification des données de seed")
        plans = db.table('subscription_plans').select('name, storage_quota_mb').execute()

        quota_by_plan = {plan['name']: plan['storage_quota_mb'] for plan in plans.data}

        # Vérifier les quotas
        assert quota_by_plan.get('Starter') == 10, f"Quota Starter incorrect: {quota_by_plan.get('Starter')}"
        assert quota_by_plan.get('Pro') == 40, f"Quota Pro incorrect: {quota_by_plan.get('Pro')}"
        assert quota_by_plan.get('Plus') == 40, f"Quota Plus incorrect: {quota_by_plan.get('Plus')}"
        assert quota_by_plan.get('Team') == 40, f"Quota Team incorrect: {quota_by_plan.get('Team')}"

        logger.info("✅ Données de seed correctes")

        # 3. Test du StorageService
        logger.info("📋 Test 3: Test du StorageService")

        # Obtenir un utilisateur test
        users = db.table('user_subscriptions').select('user_id').limit(1).execute()
        if users.data:
            test_user_id = users.data[0]['user_id']

            storage_service = await get_storage_service(db)

            # Test get_storage_usage
            usage = await storage_service.get_storage_usage(test_user_id)
            assert 'used_mb' in usage, "Champ used_mb manquant dans StorageUsage"
            assert 'quota_mb' in usage, "Champ quota_mb manquant dans StorageUsage"
            assert 'available_mb' in usage, "Champ available_mb manquant dans StorageUsage"
            assert 'percentage_used' in usage, "Champ percentage_used manquant dans StorageUsage"
            assert 'is_full' in usage, "Champ is_full manquant dans StorageUsage"

            logger.info(f"✅ StorageService fonctionne - Usage: {usage.used_mb:.2f}MB / {usage.quota_mb}MB")

        # 4. Test des triggers (simulation)
        logger.info("📋 Test 4: Test des triggers de stockage")

        # Vérifier que les triggers existent
        triggers = db.rpc('sql', {
            'query': """
            SELECT trigger_name, event_manipulation, event_object_table
            FROM information_schema.triggers
            WHERE trigger_name LIKE 'storage_%';
            """
        }).execute()

        trigger_names = [t['trigger_name'] for t in triggers.data]
        expected_triggers = [
            'storage_increment_knowledge_documents',
            'storage_decrement_knowledge_documents',
            'storage_increment_faq_qa',
            'storage_decrement_faq_qa'
        ]

        for trigger in expected_triggers:
            assert trigger in trigger_names, f"Trigger {trigger} manquant"
            logger.info(f"✅ Trigger {trigger} présent")

        logger.info("🎉 Tous les tests sont passés avec succès!")

        return True

    except Exception as e:
        logger.error(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_storage_quota_system())
    sys.exit(0 if success else 1)


